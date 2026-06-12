import os
import re
import subprocess

# 設定 BOOK_ID 與動態目錄尋找
BOOK_ID = "141"

def find_book_dir(book_id):
    for item in os.listdir('.'):
        # 兼容 "139_" 或 "B139_" 開頭的目錄
        if os.path.isdir(item) and (item.startswith(f"{book_id}_") or item.startswith(f"B{book_id}_") or item.startswith(f"1{book_id}_")):
            return item
    raise FileNotFoundError(f"Cannot find book directory starting with {book_id}_")

book_dir = find_book_dir(BOOK_ID)
TXT_DIR = os.path.join(book_dir, "raw", f"txt{BOOK_ID}")
VOICE_DIR = os.path.join(book_dir, "raw", f"voice{BOOK_ID}")
os.makedirs(TXT_DIR, exist_ok=True)
os.makedirs(VOICE_DIR, exist_ok=True)

# TTS 聲音設定 (可根據專家性別調整)
VOICE_MALE_HOST = "zh-TW-YunJheNeural"      # 男主持：年輕活潑
VOICE_FEMALE_HOST = "zh-TW-HsiaoChenNeural"   # 女主持：親切明亮
VOICE_GUEST = "zh-CN-YunyangNeural"         # 受訪專家 (預設男性)：沉穩知性

"""
Edge-TTS 可選中文聲音清單說明：

台灣 (zh-TW):
- zh-TW-YunJheNeural (男): 年輕、活潑、陽光，適合作為主持人。
- zh-TW-HsiaoChenNeural (女): 甜美、親切、明亮，適合作為主持人或助理。
- zh-TW-HsiaoYuNeural (女): 溫柔、自然，適合知性主題。

中國大陸 (zh-CN) - 推薦作為「專家」使用以產生腔調區隔:
- zh-CN-YunyangNeural (男): 專業、沉穩、可靠 (新聞播報風格)，極力推薦作為男性專家。
- zh-CN-XiaoxiaoNeural (女): 溫暖、感性、知性 (新聞/故事風格)，推薦作為女性專家。
- zh-CN-YunxiNeural (男): 活潑、陽光，適合年輕男性角色。
- zh-CN-YunjianNeural (男): 充滿激情、體育解說風格。
- zh-CN-XiaoyiNeural (女): 俏皮、可愛，適合卡通或趣味內容。
- zh-CN-YunxiaNeural (男): 軟萌、可愛，少年音。
"""

def clean_text_for_tts(text):
    """過濾掉所有控制符號，產生乾淨的 TTS 語音字串"""
    # 移除 > @ < 等符號
    text = text.replace(">", "").replace("@", "").replace("<", "")
    # 移除段落開頭的 。 控制符號 (保留句尾正常的句號)
    text = re.sub(r'^。+', '', text)
    # 將換行替換為空白，讓語音連貫
    text = text.replace('\n', ' ')
    return text.strip()

def process_segments():
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
            
    current_voice = VOICE_MALE_HOST # 預設由男主持開場
    
    # 處理所有段落
    for i, segment in enumerate(segments):
        segment_id = i + 1
        
        # 判斷說話角色 (檢查開頭的 。 數量)
        if segment.startswith("。。。"):
            current_voice = VOICE_GUEST
        elif segment.startswith("。。"):
            current_voice = VOICE_FEMALE_HOST
        elif segment.startswith("。"):
            current_voice = VOICE_MALE_HOST
            
        print(f"[{segment_id:04d}] 角色: {current_voice}")
        
        txt_filename = f"B{BOOK_ID}_{segment_id:04d}.txt"
        txt_path = os.path.join(TXT_DIR, txt_filename)
        mp3_filename = f"B{BOOK_ID}_{segment_id:04d}.mp3"
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
            # 確保保留說話角色狀態
            continue

        # 1. 產生文字檔 (保留所有控制符號)
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(segment)
            
        # 2. 產生語音檔
        # 準備語音
        tts_text = clean_text_for_tts(segment)
        
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
                print(f"  -> 已生成: {txt_filename} & {mp3_filename}")
                success = True
                break
            except subprocess.CalledProcessError as e:
                import time
                print(f"  -> 生成 {mp3_filename} 失敗 (第 {attempt} 次嘗試): {e}")
                if attempt < 3:
                    time.sleep(2)
        if not success:
            print(f"  -> ❌ 生成 {mp3_filename} 最終失敗！")

    # 完整性驗證：避免中途停止時誤以為 txt/mp3 數量相等就是完成
    missing_txt = []
    missing_mp3 = []
    zero_mp3 = []
    for idx in range(1, len(segments) + 1):
        base = f"B{BOOK_ID}_{idx:04d}"
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
    process_segments()
    print("\n所有段落處理完成！")
