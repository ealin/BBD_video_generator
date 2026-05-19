import os
import re
import subprocess

# 設定目錄
TXT_DIR = "腳本/txt130"
VOICE_DIR = "腳本/voice130"
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
    script_path = "130_20260518_台灣半導體如何成為世界的心臟/raw/腳本-step4.txt"
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
        
        # 1. 產生文字檔 (保留所有控制符號)
        txt_filename = f"B130_{segment_id:04d}.txt"
        with open(os.path.join(TXT_DIR, txt_filename), 'w', encoding='utf-8') as f:
            f.write(segment)
            
        # 2. 產生語音檔
        # 準備語音
        tts_text = clean_text_for_tts(segment)
        mp3_filename = f"B130_{segment_id:04d}.mp3"
        mp3_path = os.path.join(VOICE_DIR, mp3_filename)
        
        # 如果是純轉場符號(空字串)，傳送一個空格給引擎以產生極短的靜音檔
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
            
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"  -> 已生成: {txt_filename} & {mp3_filename}")
        except subprocess.CalledProcessError as e:
            print(f"  -> 生成 {mp3_filename} 失敗: {e}")

if __name__ == "__main__":
    process_segments()
    print("\n所有段落處理完成！")
