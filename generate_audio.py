import os
import re
import subprocess
import argparse

# 設定 BOOK_ID 與動態目錄尋找 (保留此處供手動修改與回溯相容)
BOOK_ID = "144"

# TTS 聲音設定 (Edge-TTS)
VOICE_MALE_HOST = "zh-TW-YunJheNeural"      # 男主持：年輕活潑
VOICE_FEMALE_HOST = "zh-TW-HsiaoChenNeural"   # 女主持：親切明亮
VOICE_GUEST = "zh-CN-YunyangNeural"         # 受訪專家 (預設男性)：沉穩知性

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
    for i, segment in enumerate(segments):
        segment_id = i + 1
        
        # 判斷說話角色 (檢查開頭的 。 數量)
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
            
        if engine == "edge-tts":
            print(f"[{segment_id:04d}] 角色 (Edge-TTS): {current_voice}")
        else:
            print(f"[{segment_id:04d}] 角色 (Index-TTS): {role_name} (Ref: {os.path.basename(current_ref)})")
        
        txt_filename = f"B{book_id}_{segment_id:04d}.txt"
        txt_path = os.path.join(TXT_DIR, txt_filename)
        mp3_filename = f"B{book_id}_{segment_id:04d}.mp3"
        mp3_path = os.path.join(VOICE_DIR, mp3_filename)

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
            continue

        # 1. 產生文字檔 (保留所有控制符號)
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(segment)
            
        # 2. 產生語音檔
        tts_text = clean_text_for_tts(segment)
        
        if engine == "edge-tts":
            # 如果是純轉場符號(空字串)，傳送一個空格給引擎以產生極短 of 靜音檔
            final_tts_text = tts_text if tts_text else " "
            
            # 使用 python3 -m edge_tts 呼叫引擎
            cmd = [
                "python3", "-m", "edge_tts",
                "--voice", current_voice,
                "--text", final_tts_text,
                "--write-media", mp3_path
            ]
            
            # 女主持人加快語速至 +15%
            if current_voice == VOICE_FEMALE_HOST:
                cmd.extend(["--rate", "+15%"])
                
            success = False
            for attempt in range(1, 4):
                try:
                    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
                continue
                
            # 繁簡轉換 (IndexTTS 的 BPE 字彙表以簡體中文為主，直接輸入繁體會引發 unknown token 發音異常)
            simplified_text = zhconv.convert(tts_text, 'zh-hans')
            
            # 過濾特定不支援的字元（例如斜線 '/' 或 & 等常見標點符號，轉換為空白或口語）
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
