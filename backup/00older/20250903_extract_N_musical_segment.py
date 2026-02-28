from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple
import numpy as np

def extract_musical_segments(
    mp3_path: str | Path,
    segment_seconds: float = 20.0,
    num_segments: int = 3,
    out_dir: Optional[str | Path] = None,
    target_bitrate: str = "192k",
    fade_in_ms: int = 200,
    fade_out_ms: int = 300,
) -> List[str]:
    """
    讀入一首 .mp3（音樂），以節拍 + 旋律(chroma)分析，選出「可自成段落」的 num_segments 段，
    每段長度約 segment_seconds，輸出多個 mp3：
      <原檔名>_short_1.mp3, <原檔名>_short_2.mp3, ...

    演算法（摘要）：
      1) 以 librosa 載入音訊，HPSS 分離 -> harmonic(旋律)/percussive(節拍)。
      2) 以 percussive 訊號做 onset/beat tracking，取得節拍時間軸。
      3) 以 harmonic 計算 chroma，beat-synchronous 對齊，建立自相似矩陣 S。
      4) 以與全曲的相似度 + 段內能量 - 邊界懲罰 計分，挑選最佳窗口（節拍對齊）。
      5) 用 pydub 擷取音訊，套淡入/淡出後輸出為 mp3。

    注意：
      - 若歌太短或節拍偵測不足，將退回以時間均勻分佈的簡化策略。
      - 若可用的非重疊窗口少於 num_segments，將輸出可取得的數量。

    參數：
      mp3_path        : 輸入 mp3 檔
      segment_seconds : 目標片段秒數
      num_segments    : 需要輸出的段數（從 1 開始編號）
      out_dir         : 輸出資料夾（預設為原檔目錄）
      target_bitrate  : 匯出 mp3 位元率
      fade_in_ms      : 片頭淡入（毫秒）
      fade_out_ms     : 片尾淡出（毫秒）

    需求：
      pip install librosa pydub soundfile numpy
      並安裝 ffmpeg（pydub 需用到）
    """
    # 延遲匯入，給出清楚錯誤訊息
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

    out_dir = Path(out_dir) if out_dir is not None else in_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    # 讀檔（mono）並 HPSS
    y, sr = librosa.load(str(in_path), mono=True)
    if y.size == 0:
        raise RuntimeError("音檔解碼失敗或為空。請確認檔案可播放、ffmpeg 是否可用。")
    duration = y.shape[0] / sr
    if duration <= 1.0:
        raise RuntimeError("音檔過短，無法分析。")
    if segment_seconds <= 0:
        raise ValueError("segment_seconds 必須 > 0")
    if num_segments <= 0:
        raise ValueError("num_segments 必須 > 0")

    # 若歌曲很短，就只輸出 1 段（整首或目標長度）
    max_nonoverlap = int(duration // max(1e-6, segment_seconds))
    target_n = min(num_segments, max(1, max_nonoverlap)) if max_nonoverlap > 0 else 1

    y_harm, y_perc = librosa.effects.hpss(y)

    # 節拍與 onset
    hop = 512
    oenv = librosa.onset.onset_strength(y=y_perc, sr=sr, hop_length=hop)
    tempo, beats = librosa.beat.beat_track(
        y=None, sr=sr, onset_envelope=oenv, hop_length=hop, units="frames"
    )
    if beats.size < 2:
        beats_times = np.arange(0.0, duration, 0.5)  # 後備：每 0.5s 一拍
        beats_frames = librosa.time_to_frames(beats_times, sr=sr, hop_length=hop)
    else:
        beats_frames = beats
        beats_times = librosa.frames_to_time(beats_frames, sr=sr, hop_length=hop)

    # 旋律特徵（chroma），對齊節拍
    chroma = librosa.feature.chroma_cqt(y=y_harm, sr=sr, hop_length=hop)
    if len(beats_frames) < 2 or chroma.shape[1] < 2:
        # 節拍/特徵不足，退回均勻取樣策略
        return _export_uniform_segments(
            in_path, duration, segment_seconds, target_n, out_dir, target_bitrate, fade_in_ms, fade_out_ms
        )

    C_sync = librosa.util.sync(chroma, beats_frames, aggregate=np.median)  # (12, n_beats)
    # 自相似矩陣（節拍級）
    Cn = C_sync / (np.linalg.norm(C_sync, axis=0, keepdims=True) + 1e-9)
    S = np.clip(Cn.T @ Cn, 0.0, 1.0)  # (n_beats, n_beats)

    # 能量（同步到節拍）
    o_sync = librosa.util.sync(oenv[np.newaxis, :], beats_frames, aggregate=np.mean).ravel()
    if o_sync.max() > 0:
        o_sync = o_sync / float(o_sync.max())

    # 估算目標窗口的節拍長度
    if tempo is None or not np.isfinite(tempo) or tempo <= 0:
        tempo = 120.0
    target_beats = max(4, int(round(segment_seconds * float(tempo) / 60.0)))
    n_beats = len(beats_times)
    if target_beats >= n_beats:
        # 太短，退回均勻策略
        return _export_uniform_segments(
            in_path, duration, segment_seconds, target_n, out_dir, target_bitrate, fade_in_ms, fade_out_ms
        )

    # 為每個可能起點計分
    candidates: List[Tuple[float, int]] = []
    for s in range(0, n_beats - target_beats + 1):
        e = s + target_beats
        rep = S[s:e, :].mean()  # 與全曲之相似度
        energy = float(o_sync[s:e].mean()) if o_sync.size >= e else 0.0
        boundary_penalty = 0.0
        if s < o_sync.size and e-1 < o_sync.size:
            boundary_penalty = 0.5 * (o_sync[s] + o_sync[e-1])
        score = 0.7 * rep + 0.3 * energy - 0.2 * boundary_penalty
        candidates.append((score, s))

    # 依分數由高到低挑選「不重疊」窗口
    candidates.sort(key=lambda x: x[0], reverse=True)
    chosen: List[int] = []
    def overlap(a_start: int, b_start: int) -> bool:
        a_end, b_end = a_start + target_beats, b_start + target_beats
        return not (a_end <= b_start or b_end <= a_start)

    for _, s in candidates:
        if len(chosen) >= target_n:
            break
        if all(not overlap(s, c) for c in chosen):
            chosen.append(s)

    # 若挑不足，就退回均勻策略補齊
    if len(chosen) == 0:
        return _export_uniform_segments(
            in_path, duration, segment_seconds, target_n, out_dir, target_bitrate, fade_in_ms, fade_out_ms
        )

    chosen.sort()
    # 匯出
    from pydub import AudioSegment
    full = AudioSegment.from_file(str(in_path))
    out_files: List[str] = []

    for idx, s in enumerate(chosen, 1):
        start_t = float(beats_times[s])
        end_t = min(duration, start_t + segment_seconds)
        # 若最後一段靠近尾巴，維持固定長度（盡量）：
        if end_t - start_t < segment_seconds and end_t == duration:
            start_t = max(0.0, end_t - segment_seconds)

        start_ms = int(round(start_t * 1000.0))
        end_ms = int(round(end_t * 1000.0))
        seg = full[start_ms:end_ms]
        # 避免淡入/淡出長於片段
        fi = min(fade_in_ms, max(0, len(seg) // 3))
        fo = min(fade_out_ms, max(0, len(seg) // 3))
        seg = seg.fade_in(fi).fade_out(fo)

        out_path = out_dir / f"{in_path.stem}_short_{idx}.mp3"
        seg.export(str(out_path), format="mp3", bitrate=target_bitrate)
        out_files.append(str(out_path))

    return out_files


def _export_uniform_segments(
    in_path: Path,
    duration: float,
    segment_seconds: float,
    target_n: int,
    out_dir: Path,
    target_bitrate: str,
    fade_in_ms: int,
    fade_out_ms: int,
) -> List[str]:
    """備援：無法可靠節拍/旋律時，均勻取不重疊片段。"""
    from pydub import AudioSegment
    full = AudioSegment.from_file(str(in_path))
    out_files: List[str] = []

    # 最多可不重疊數量
    max_n = int(duration // max(1e-6, segment_seconds))
    n = min(target_n, max(1, max_n)) if max_n > 0 else 1

    if n == 1:
        # 取中間一段
        mid = duration / 2.0
        start_t = max(0.0, mid - segment_seconds / 2.0)
        end_t = min(duration, start_t + segment_seconds)
        _export_slice(full, start_t, end_t, out_dir / f"{in_path.stem}_short_1.mp3",
                      target_bitrate, fade_in_ms, fade_out_ms)
        return [str(out_dir / f"{in_path.stem}_short_1.mp3")]

    # 將 [0, duration - segment] 平均切成 n 等分的起點
    span = (duration - segment_seconds)
    starts = np.linspace(0.0, max(0.0, span), num=n)
    for i, st in enumerate(starts, 1):
        et = min(duration, float(st) + segment_seconds)
        _export_slice(full, float(st), float(et),
                      out_dir / f"{in_path.stem}_short_{i}.mp3",
                      target_bitrate, fade_in_ms, fade_out_ms)
    return [str(out_dir / f"{in_path.stem}_short_{i}.mp3") for i in range(1, n+1)]


def _export_slice(full, start_t: float, end_t: float, out_path: Path,
                  bitrate: str, fade_in_ms: int, fade_out_ms: int) -> None:
    from pydub import AudioSegment
    start_ms = int(round(start_t * 1000.0))
    end_ms = int(round(end_t * 1000.0))
    seg = full[start_ms:end_ms]
    fi = min(fade_in_ms, max(0, len(seg) // 3))
    fo = min(fade_out_ms, max(0, len(seg) // 3))
    seg = seg.fade_in(fi).fade_out(fo)
    seg.export(str(out_path), format="mp3", bitrate=bitrate)



# 產生 3 段、每段 20 秒的短版 mp3
outs = extract_musical_segments(
    "./bg_mp3/SnowflakesDanceFreeTonight.mp3",    # CeremonialLibrary-AsherFulero.mp3",
    segment_seconds=45.0,
    num_segments=5
)
print("輸出檔案：", outs)

