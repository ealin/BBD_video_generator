from __future__ import annotations

import math
from pathlib import Path
from typing import Optional

import numpy as np

def extract_musical_segment(
    mp3_path: str | Path,
    segment_seconds: float = 20.0,
    out_path: Optional[str | Path] = None,
    target_bitrate: str = "192k",
    fade_in_ms: int = 200,
    fade_out_ms: int = 300,
) -> str:
    """
    讀入一首 .mp3（音樂），分析節拍與旋律（chroma），擷取一段「可獨立成段」的音樂片段並輸出 mp3。
    演算法（簡述）：
      1) 以 librosa 載入音訊，做 HPSS 分離（harmonic 作為旋律分析、percussive 作為節拍）。
      2) 以 percussive 訊號計算 onset envelope 及 beat tracking（得到節拍時間軸）。
      3) 以 harmonic 訊號計算 chroma，對齊節拍（beat-synchronous），建立自相似矩陣 S。
      4) 在節拍網格上以長度 ~= segment_seconds 的窗口滑動，為每個窗口計分：
           分數 = 0.7*段內平均「與全曲的相似度」 + 0.3*段內平均能量  - 0.2*邊界瞬時能量
         取分數最高的窗口當作片段（避免在強瞬變處切割）。
      5) 用 pydub 依時間（毫秒）擷取片段，加上淡入淡出，輸出為 mp3。
    參數：
      mp3_path        : 輸入 mp3 檔案路徑
      segment_seconds : 目標片段秒數（預設 20.0）
      out_path        : 輸出檔（預設為 <原檔名>_short.mp3）
      target_bitrate  : 匯出 mp3 位元率（預設 192k）
      fade_in_ms      : 片頭淡入毫秒（預設 200ms）
      fade_out_ms     : 片尾淡出毫秒（預設 300ms）
    回傳：
      實際輸出的 mp3 路徑（字串）

    需求：
      pip install librosa pydub soundfile numpy
      系統可呼叫 ffmpeg（pydub 需用到）
    """
    # ---- 延遲匯入並給出更清楚的錯誤訊息 ----
    try:
        import librosa
    except ModuleNotFoundError:
        raise RuntimeError("需要安裝 librosa：pip install librosa")
    try:
        from pydub import AudioSegment
    except ModuleNotFoundError:
        raise RuntimeError("需要安裝 pydub：pip install pydub（並確認 ffmpeg 已安裝且在 PATH）")

    in_path = Path(mp3_path)
    if not in_path.exists():
        raise FileNotFoundError(f"找不到 mp3 檔案：{in_path}")

    if out_path is None:
        out_path = in_path.with_name(f"{in_path.stem}_short.mp3")
    out_path = Path(out_path)

    # ---- 讀檔（mono）並做 HPSS 分離 ----
    # sr 採 librosa 預設（~22050），足以做結構/旋律分析
    y, sr = librosa.load(str(in_path), mono=True)
    if y.size == 0:
        raise RuntimeError("音檔解碼失敗或為空。請確認 mp3 可播放、ffmpeg 是否已安裝。")

    duration = y.shape[0] / sr
    if duration <= 1.0:
        raise RuntimeError("音檔過短，無法分析。")

    if segment_seconds >= duration:
        # 目標長度大於整首，就取整首（仍加淡入淡出）
        start_t, end_t = 0.0, duration
    else:
        # HPSS：harmonic(旋律) / percussive(節拍)
        y_harm, y_perc = librosa.effects.hpss(y)

        # ---- 節拍軸（使用 percussive 訊號）----
        hop = 512
        oenv = librosa.onset.onset_strength(y=y_perc, sr=sr, hop_length=hop)
        tempo, beats = librosa.beat.beat_track(
            y=None, sr=sr, onset_envelope=oenv, hop_length=hop, units="frames"
        )
        if beats.size < 2:
            # 後備：每 0.5 秒一拍
            beats_times = np.arange(0.0, duration, 0.5)
            beats_frames = librosa.time_to_frames(beats_times, sr=sr, hop_length=hop)
        else:
            beats_frames = beats
            beats_times = librosa.frames_to_time(beats_frames, sr=sr, hop_length=hop)

        # 估算目標節拍長度（至少 4 拍）
        if tempo is None or not np.isfinite(tempo) or tempo <= 0:
            tempo = 120.0  # 穩健預設
        target_beats = max(4, int(round(segment_seconds * float(tempo) / 60.0)))
        if target_beats >= len(beats_times):
            # 拍數不足，就把片段設為中間對齊的 segment_seconds
            mid = duration / 2.0
            start_t = max(0.0, mid - segment_seconds / 2.0)
            end_t = min(duration, start_t + segment_seconds)
        else:
            # ---- 旋律（harmonic） -> chroma，並同步到節拍 ----
            chroma = librosa.feature.chroma_cqt(y=y_harm, sr=sr, hop_length=hop)
            # 同步到節拍（把每個拍內的特徵聚合成一個值）
            C_sync = librosa.util.sync(chroma, beats_frames, aggregate=np.median)  # (12, n_beats)

            # ---- 自相似矩陣（節拍級）----
            # 以 cosine 類似度（經 L2 正規化）衡量
            Cn = C_sync / (np.linalg.norm(C_sync, axis=0, keepdims=True) + 1e-9)
            S = np.clip(Cn.T @ Cn, 0.0, 1.0)  # (n_beats, n_beats)

            # ---- 能量（onset envelope）同步到節拍，用於加權 ----
            o_sync = librosa.util.sync(oenv[np.newaxis, :], beats_frames, aggregate=np.mean).ravel()
            # 正規化到 0~1
            if o_sync.max() > 0:
                o_sync = o_sync / float(o_sync.max())

            # ---- 在節拍網格上滑窗，計分並挑選窗口 ----
            n_beats = len(beats_times)
            best_s, best_score = 0, -np.inf
            for s in range(0, n_beats - target_beats + 1):
                e = s + target_beats
                # 「與全曲相似度」：窗口內每拍對全曲的平均相似度
                rep = S[s:e, :].mean()

                # 窗口能量（避免太平淡片段），同時避免超爆音
                energy = float(o_sync[s:e].mean()) if o_sync.size >= e else 0.0

                # 邊界懲罰：在強瞬變處切割的代價（希望切在較平順處）
                boundary_penalty = 0.0
                if s < o_sync.size and e-1 < o_sync.size:
                    boundary_penalty = 0.5 * (o_sync[s] + o_sync[e-1])

                # 綜合分數（可依口味調整權重）
                score = 0.7 * rep + 0.3 * energy - 0.2 * boundary_penalty

                if score > best_score:
                    best_score = score
                    best_s = s

            start_t = float(beats_times[best_s])
            # 盡量靠近目標長度；若節拍格不夠細，尾端用秒數補齊
            end_t = start_t + segment_seconds
            # 但不超出歌曲
            if end_t > duration:
                end_t = duration
                start_t = max(0.0, end_t - segment_seconds)

    # ---- 用 pydub 擷取並輸出 mp3（加淡入淡出）----
    # 注意：pydub 的時間以毫秒為單位
    from pydub import AudioSegment

    seg = AudioSegment.from_file(str(in_path))  # 需要 ffmpeg 存取 mp3
    start_ms = int(round(start_t * 1000.0))
    end_ms = int(round(end_t * 1000.0))
    if end_ms <= start_ms:
        # 萬一上面的計算失敗，就取中間一段
        mid = int(round((len(seg) / 2)))
        half = int(round(segment_seconds * 1000 / 2))
        start_ms = max(0, mid - half)
        end_ms = min(len(seg), start_ms + int(round(segment_seconds * 1000)))

    out = seg[start_ms:end_ms].fade_in(fade_in_ms).fade_out(fade_out_ms)
    out.export(str(out_path), format="mp3", bitrate=target_bitrate)

    return str(out_path)



out_file = extract_musical_segment("./bg_mp3/EchoesInTheDrizzle.mp3", segment_seconds=20.0)
print("已輸出：", out_file)