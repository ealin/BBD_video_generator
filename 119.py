import asyncio
import edge_tts
import os

# 設置輸出的語音文字、聲線、檔案名稱
TEXT = "大家好，這是一段由 edge-tts 生成的中文語音，語音非常流暢自然。"
VOICE = "zh-TW-HsiaoChenNeural" # 台灣女聲 (建議選擇)
OUTPUT_FILE = "output.mp3"

async def _main() -> None:
    print("正在生成語音...")
    communicate = edge_tts.Communicate(TEXT, VOICE)
    await communicate.save(OUTPUT_FILE)
    print(f"語音已保存為: {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(_main())
    
    # 自動播放 (僅限 Windows/macOS/Linux 環境下安裝了對應播放器)
    if os.name == 'nt': # Windows
        os.system(f"start {OUTPUT_FILE}")
    elif os.name == 'posix': # macOS/Linux
        os.system(f"open {OUTPUT_FILE}" if os.uname().sysname == 'Darwin' else f"xdg-open {OUTPUT_FILE}")


