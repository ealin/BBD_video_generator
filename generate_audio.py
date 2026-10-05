import os
import re
import subprocess
import argparse

# 設定 BOOK_ID 與動態目錄尋找 (保留此處供手動修改與回溯相容)
BOOK_ID = "152"

# TTS 聲音設定 (Edge-TTS)
VOICE_MALE_HOST = "zh-CN-YunyangNeural"      # 男主持：沉穩知性
VOICE_FEMALE_HOST = "zh-CN-XiaoxiaoNeural"   # 女主持：親切自然 (zh-CN-XiaoxiaoNeural)
VOICE_GUEST = "zh-TW-YunJheNeural"         # 受訪專家 (李開復)(台灣)：青年/沉穩，速度+5%
RATE_GUEST = "+5%"
RATE_FEMALE_HOST = "+0%"

# IndexTTS 模型全局變數
_tts_model = None

def get_index_tts():
    """延遲載入 (Lazy Load) IndexTTS 模型"""
    global _tts_model
    if _tts_model is None:
        import sys
        import torch
        # macOS Intel 相容性補丁
        if not hasattr(torch, "get_default_device"):
            torch.get_default_device = lambda: torch.device("cpu")
            
        repo_path = '/Users/mac/00prj/2026PRJ/index-tts'
        sys.path.append(repo_path)
        from indextts.infer_v2 import IndexTTS2
        
        print("Initializing IndexTTS2 model (CPU)...")
        _tts_model = IndexTTS2(
            cfg_path=os.path.join(repo_path, "checkpoints/config.yaml"),
            model_dir=os.path.join(repo_path, "checkpoints"),
            device="cpu"
        )
    return _tts_model

def find_book_dir(book_id):
    for item in os.listdir('.'):
        # 兼容 "139_" 或 "B139_" 開頭的目錄
        if os.path.isdir(item) and (item.startswith(f"{book_id}_") or item.startswith(f"B{book_id}_") or item.startswith(f"1{book_id}_") or item.startswith(f"{book_id}-") or item.startswith(f"B{book_id}-") or item.startswith(f"1{book_id}-")):
            return item
    raise FileNotFoundError(f"Cannot find book directory starting with {book_id}_")

def clean_text_for_tts(text):
    """過濾掉所有控制符號，產生乾淨的 TTS 語音字串"""
    # 移除 > @ < 等符號
    text = text.replace(">", "").replace("@", "").replace("<", "")
    # 移除段落開頭的 。 控制符號 (保留句尾正常的句號)
    text = re.sub(r'^。+', '', text)
    # 將換行替換為空白，讓語音連貫
    text = text.replace('\n', ' ')
    return text.strip()

def process_segments(book_id=BOOK_ID, engine="edge-tts"):
    book_dir = find_book_dir(book_id)
    TXT_DIR = os.path.join(book_dir, "raw", f"txt{book_id}")
    VOICE_DIR = os.path.join(book_dir, "raw", f"voice{book_id}")
    os.makedirs(TXT_DIR, exist_ok=True)
    os.makedirs(VOICE_DIR, exist_ok=True)

    # 取得參考音訊路徑 (若使用 IndexTTS)
    ref_dir = os.path.join(book_dir, "raw", "voice_refs")
    ref_aa = os.path.join(ref_dir, "AA_ref.wav")
    ref_bb = os.path.join(ref_dir, "BB_ref.wav")
    ref_cc = os.path.join(ref_dir, "CC_ref.wav")

    if engine == "index-tts":
        # 檢查 voice_refs 目錄與檔案是否存在
        if not os.path.exists(ref_dir):
            raise FileNotFoundError(f"IndexTTS 啟用失敗：找不到參考音檔目錄 {ref_dir}，請確認已放入 AA_ref.wav, BB_ref.wav, CC_ref.wav")
        for ref_file in [ref_aa, ref_bb, ref_cc]:
            if not os.path.exists(ref_file):
                raise FileNotFoundError(f"IndexTTS 啟用失敗：找不到參考音檔 {ref_file}")
        
        # 載入 zhconv (繁簡轉換) 與 torch
        global zhconv, torch, torchaudio
        import zhconv
        import torch
        import torchaudio

    script_path = os.path.join(book_dir, "raw", "腳本-step4.txt")
    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # 以空白行切分大段落，但要確保 >>>> 和 @@@@ 獨立成段
    raw_segments = content.split('\n\n')
    segments = []
    for s in raw_segments:
        s = s.strip()
        if not s: continue
        
        # 逐行檢查，若有控制符號行則拆分為獨立段落
        lines = s.split('\n')
        current_part = []
        for line in lines:
            if line.startswith('>>>>') or line.startswith('@@@@'):
                if current_part:
                    segments.append('\n'.join(current_part))
                    current_part = []
                segments.append(line)
            else:
                current_part.append(line)
        if current_part:
            segments.append('\n'.join(current_part))

    print(f"預期段落總數: {len(segments)}")
    print(f"使用的語音引擎: {engine}")
            
    # 初始化角色狀態 (預設是 AA 男主持)
    # Edge-TTS 的角色狀態
    current_voice = VOICE_MALE_HOST
    # IndexTTS 的角色狀態
    current_ref = ref_aa
    role_name = "AA (Male Host)"
    
    # 處理所有段落
    # 1. 預先依序解析所有段落的說話者狀態 (避免並行化後狀態遺失導致角色判定錯誤)
    resolved_speakers = []
    current_voice = VOICE_MALE_HOST
    current_ref = ref_aa
    role_name = "AA (Male Host)"
    
    for segment in segments:
        if book_id == "150":
            if segment.startswith("。。。"):
                current_voice = "zh-CN-XiaoxiaoNeural"
                current_ref = ref_cc
                role_name = "CC (Daughter Rachel)"
            elif segment.startswith("。。"):
                current_voice = "zh-TW-YunJheNeural"
                current_ref = ref_bb
                role_name = "BB (Father Dave)"
            elif segment.startswith("。") or segment.startswith(">>>>"):
                current_voice = "zh-TW-HsiaoChenNeural"
                current_ref = ref_aa
                role_name = "AA (Female Host)"
        elif book_id == "151":
            if segment.startswith("。。"):
                current_voice = "zh-CN-XiaoxiaoNeural"
                current_ref = ref_bb
                role_name = "BB (Author Natasha)"
            elif segment.startswith("。") or segment.startswith(">>>>"):
                current_voice = "zh-TW-HsiaoChenNeural"
                current_ref = ref_aa
                role_name = "AA (Female Host)"
        elif book_id == "152":
            if segment.startswith("。。。"):
                current_voice = "zh-TW-YunJheNeural"
                current_ref = ref_cc
                role_name = "CC (Author Kai-Fu Lee)"
            elif segment.startswith("。。") or segment.startswith(">>>>"):
                current_voice = "zh-CN-XiaoxiaoNeural"
                current_ref = ref_bb
                role_name = "BB (Female Host)"
        else:
            if segment.startswith("。。。"):
                current_voice = VOICE_GUEST
                current_ref = ref_cc
                role_name = "CC (Guest)"
            elif segment.startswith("。。"):
                current_voice = VOICE_FEMALE_HOST
                current_ref = ref_bb
                role_name = "BB (Female Host)"
            elif segment.startswith("。"):
                current_voice = VOICE_MALE_HOST
                current_ref = ref_aa
                role_name = "AA (Male Host)"
            
        resolved_speakers.append((current_voice, current_ref, role_name))

    # 2. 處理所有段落的並行函數
    from concurrent.futures import ThreadPoolExecutor
    
    def process_single(item):
        i, segment = item
        segment_id = i + 1
        current_voice, current_ref, role_name = resolved_speakers[i]
            
        txt_filename = f"B{book_id}_{segment_id:04d}.txt"
        txt_path = os.path.join(TXT_DIR, txt_filename)
        mp3_filename = f"B{book_id}_{segment_id:04d}.mp3"
        mp3_path = os.path.join(VOICE_DIR, mp3_filename)

        # 紀錄發音者資訊
        role_marker = ""
        if segment.startswith("。。。"):
            role_marker = "。。。"
        elif segment.startswith("。。"):
            role_marker = "。。"
        elif segment.startswith("。"):
            role_marker = "。"
        elif segment.startswith(">>>>"):
            role_marker = ">>>> (章節標頭)"
        elif segment.startswith("@@@@"):
            role_marker = "@@@@ (轉場空秒)"
        else:
            role_marker = "未標記"

        speaker_info = {
            "檔名": mp3_filename,
            "角色標記": role_marker,
            "角色名稱": role_name if not (segment.startswith(">>>>") or segment.startswith("@@@@")) else "系統符號",
            "TTS語音": current_voice if engine == "edge-tts" else f"Index-TTS ({role_name})",
            "文字內容": segment.replace('\n', ' ')[:50]
        }

        # 智慧比對：若已有相同文字檔且音檔大小大於 0，則直接跳過生成
        is_identical = False
        if os.path.exists(txt_path) and os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 0:
            try:
                with open(txt_path, 'r', encoding='utf-8') as f_old:
                    old_content = f_old.read()
                if old_content.strip() == segment.strip():
                    is_identical = True
            except Exception:
                pass

        if is_identical:
            print(f"  -> 段落 {segment_id:04d} 已存在且文字相同，跳過生成。")
            return speaker_info

        # 1. 產生文字檔 (保留所有控制符號)
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(segment)
            
        # 2. 產生語音檔
        tts_text = clean_text_for_tts(segment)
        
        if engine == "edge-tts":
            if not tts_text:
                # 轉場/空秒：寫入一個 0.5 秒的靜音檔 (使用 wav 格式儲存為 .mp3 副檔名，ffmpeg 可自動識別並載入)
                import wave
                import struct
                try:
                    with wave.open(mp3_path, 'wb') as wav_file:
                        wav_file.setnchannels(1)
                        wav_file.setsampwidth(2)
                        wav_file.setframerate(24000)
                        num_frames = int(0.5 * 24000)
                        data = struct.pack('<' + 'h' * num_frames, *([0] * num_frames))
                        wav_file.writeframes(data)
                    print(f"  -> 已為轉場段落生成 0.5s 靜音檔: {mp3_filename}")
                    return speaker_info
                except Exception as e:
                    print(f"  -> 生成靜音檔失敗: {e}")
                    
            final_tts_text = tts_text
            
            # 使用 python3 -m edge_tts 呼叫引擎
            cmd = [
                "python3", "-m", "edge_tts",
                "--voice", current_voice,
                "--text", final_tts_text,
                "--write-media", mp3_path
            ]
            
            # 語速設定
            if book_id == "152":
                if current_voice == "zh-TW-YunJheNeural":
                    cmd.extend(["--rate", "+5%"])
                # 女聲 zh-CN-XiaoxiaoNeural 保持預設速度 (+0%)
            elif current_voice == VOICE_FEMALE_HOST:
                cmd.extend(["--rate", "+15%"])
                
            # 建立包含 workspace site-packages 的環境變數
            env = os.environ.copy()
            site_packages_dir = os.path.abspath("site-packages")
            env["PYTHONPATH"] = site_packages_dir + (":" + env["PYTHONPATH"] if "PYTHONPATH" in env else "")

            success = False
            for attempt in range(1, 4):
                try:
                    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
                    print(f"  -> Edge-TTS 已生成: {txt_filename} & {mp3_filename}")
                    success = True
                    break
                except subprocess.CalledProcessError as e:
                    import time
                    print(f"  -> Edge-TTS 生成 {mp3_filename} 失敗 (第 {attempt} 次嘗試): {e}")
                    if attempt < 3:
                        time.sleep(2)
            if not success:
                print(f"  -> ❌ Edge-TTS 生成 {mp3_filename} 最終失敗！")
                
        elif engine == "index-tts":
            if not tts_text:
                # 轉場/空秒：直接生成 0.2 秒靜音 Tensor 以維持 pipeline 相容性
                print("  -> 空文字/轉場，直接生成 0.2 秒靜音音軌...")
                silence_tensor = torch.zeros(1, 4410)  # 22050Hz * 0.2s = 4410 samples
                torchaudio.save(mp3_path, silence_tensor, 22050)
                print(f"  -> Index-TTS 已生成靜音檔: {mp3_filename}")
                return speaker_info
                
            # 繁簡轉換
            simplified_text = zhconv.convert(tts_text, 'zh-hans')
            simplified_text = simplified_text.replace('/', ' ').replace('&', ' 和 ')
            
            tts_model = get_index_tts()
            success = False
            for attempt in range(1, 4):
                try:
                    tts_model.infer(
                        spk_audio_prompt=current_ref,
                        text=simplified_text,
                        output_path=mp3_path,
                        verbose=False
                    )
                    print(f"  -> Index-TTS 已生成: {txt_filename} & {mp3_filename}")
                    success = True
                    break
                except Exception as e:
                    import time
                    print(f"  -> Index-TTS 生成 {mp3_filename} 失敗 (第 {attempt} 次嘗試): {e}")
                    if attempt < 3:
                        time.sleep(2)
            if not success:
                print(f"  -> ❌ Index-TTS 生成 {mp3_filename} 最終失敗！")
                
        return speaker_info

    print("開始並行語音生成（線程數 16）...")
    with ThreadPoolExecutor(max_workers=16) as executor:
        speaker_list = list(executor.map(process_single, enumerate(segments)))

    # 寫入發音人清單 CSV 檔
    csv_file = os.path.join(book_dir, "raw", "發音人清單.csv")
    import csv
    with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f_csv:
        writer = csv.writer(f_csv)
        writer.writerow(["檔名", "角色標記", "角色名稱", "TTS語音", "文字內容"])
        for item in speaker_list:
            if item:
                writer.writerow([item["檔名"], item["角色標記"], item["角色名稱"], item["TTS語音"], item["文字內容"]])
    print(f"\n✓ 發音人清單已成功輸出至: {csv_file}")

    # 完整性驗證：避免中途停止時誤以為 txt/mp3 數量相等就是完成
    missing_txt = []
    missing_mp3 = []
    zero_mp3 = []
    for idx in range(1, len(segments) + 1):
        base = f"B{book_id}_{idx:04d}"
        txt_path = os.path.join(TXT_DIR, base + ".txt")
        mp3_path = os.path.join(VOICE_DIR, base + ".mp3")
        if not os.path.exists(txt_path):
            missing_txt.append(base + ".txt")
        if not os.path.exists(mp3_path):
            missing_mp3.append(base + ".mp3")
        elif os.path.getsize(mp3_path) == 0:
            zero_mp3.append(base + ".mp3")
            
    print(f"\n完整性驗證: expected={len(segments)}, missing_txt={len(missing_txt)}, missing_mp3={len(missing_mp3)}, zero_mp3={len(zero_mp3)}")
    if missing_txt:
        print("缺少文字檔:", missing_txt[:20])
    if missing_mp3:
        print("缺少語音檔:", missing_mp3[:20])
    if zero_mp3:
        print("0-byte 語音檔:", zero_mp3[:20])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BBD 語音批量合成工具 (Edge-TTS / IndexTTS)")
    parser.add_argument("--book-id", type=str, default=BOOK_ID, help="書籍 ID (預設為 144)")
    parser.add_argument("--engine", type=str, choices=["edge-tts", "index-tts"], default="edge-tts", help="TTS 語音合成引擎 (預設為 edge-tts)")
    args = parser.parse_args()
    
    process_segments(book_id=args.book_id, engine=args.engine)
    print("\n所有段落處理完成！")
