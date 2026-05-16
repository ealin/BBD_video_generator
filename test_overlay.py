import os
import math
from moviepy import *

# 配置參數
TXT_DIR = "腳本/txt129"
VOICE_DIR = "腳本/voice129"
BG_IMG_DIR = "bg_image/bg129"
OUTPUT_FILE = "output1_sub.mp4"
FONT_TTF = 'TaipeiSansTCBeta-Regular.ttf'
BACKGROUND_COLOR = (0, 255, 0)
BLOCKS_PER_SEGMENT = 7
IMAGE_DISPLAY_DURATION = 20
ZOOM_STOPS_AT = 15
TARGET_IMAGE_SIZE = 720

def make_silence(t):
    return 0.0

def scale_func(t):
    start_scale = 1.2
    end_scale = 1.0
    if t <= ZOOM_STOPS_AT:
        return start_scale - (start_scale - end_scale) * (t / ZOOM_STOPS_AT)
    else:
        return end_scale

def test_render():
    bg_audio_clips = []
    overlay_clips = []
    text_clips = []
    acc_second = 0
    
    font_color_AA = (135, 206, 250)
    font_color_BB = (255, 179, 230)
    font_color_CC = (255, 255, 153)
    
    # 讀取前 10 個段落 (快速驗證)
    all_files = sorted([f for f in os.listdir(TXT_DIR) if f.endswith(".txt")])
    test_files = all_files[:10]
    
    print(f"開始處理 {len(test_files)} 個段落...")
    
    for i, txt_file in enumerate(test_files):
        block_id = i + 1
        txt_path = os.path.join(TXT_DIR, txt_file)
        base_name = os.path.splitext(txt_file)[0]
        mp3_path = os.path.join(VOICE_DIR, f"{base_name}.mp3")
        
        with open(txt_path, "r", encoding="utf-8") as f:
            raw_text = f.read().strip()
            
        subtitle_text = raw_text
        current_font_color = font_color_AA
        if subtitle_text.startswith("。。。"):
            current_font_color = font_color_CC
            subtitle_text = subtitle_text[3:]
        elif subtitle_text.startswith("。。"):
            current_font_color = font_color_BB
            subtitle_text = subtitle_text[2:]
        elif subtitle_text.startswith("。"):
            current_font_color = font_color_AA
            subtitle_text = subtitle_text[1:]
            
        if subtitle_text.startswith(">>>>"):
            duration = 1.0
            audio_clip = AudioClip(make_silence, duration=duration, fps=44100)
        elif subtitle_text.startswith("@@@@"):
            duration = 2.0
            audio_clip = AudioClip(make_silence, duration=duration, fps=44100)
        else:
            if os.path.exists(mp3_path):
                audio_clip = AudioFileClip(mp3_path)
                duration = audio_clip.duration
            else:
                duration = 1.0
                audio_clip = AudioClip(make_silence, duration=duration, fps=44100)
        
        # 插圖處理
        if (block_id - 1) % BLOCKS_PER_SEGMENT == 0:
            seg_id = (block_id - 1) // BLOCKS_PER_SEGMENT
            img_path = None
            for ext in ['.jpeg', '.jpg', '.png']:
                p = os.path.join(BG_IMG_DIR, f"{seg_id}{ext}")
                if os.path.exists(p):
                    img_path = p
                    break
                
            if img_path:
                img_clip = ImageClip(img_path).with_duration(IMAGE_DISPLAY_DURATION)
                img_clip = img_clip.resized(height=TARGET_IMAGE_SIZE)
                img_clip = img_clip.resized(scale_func)
                img_clip = img_clip.with_position(lambda t: (
                    1440 - (TARGET_IMAGE_SIZE * scale_func(t)) / 2,
                    540 - (TARGET_IMAGE_SIZE * scale_func(t)) / 2
                ))
                img_clip = img_clip.with_start(acc_second)
                overlay_clips.append(img_clip)

        # 背景層 (純綠色 + 該段落音訊)
        bg_clip = ColorClip(size=(1920, 1080), color=BACKGROUND_COLOR, duration=duration).with_audio(audio_clip)
        bg_audio_clips.append(bg_clip)

        # 字幕層 (獨立於背景，確保在最上層)
        clean_subtitle = subtitle_text.replace('<', '\n')
        if not any(subtitle_text.startswith(p) for p in ["!!!!", "@@@@", ">>>>"]):
            text_clip = TextClip(
                text=clean_subtitle,
                font_size=48,
                color=current_font_color,
                stroke_color='black',
                stroke_width=2,
                font=FONT_TTF,
                method='label',   # 改用 label 模式以獲得更精確的靠左對齊
                text_align='left' # 強制靠左
            ).with_position((30, 600)).with_duration(duration).with_start(acc_second)
            text_clips.append(text_clip)
        
        acc_second += duration

    print("正在串接背景音軌層...")
    final_bg_video = concatenate_videoclips(bg_audio_clips)
    
    print("正在疊加各圖層 (底層:綠幕 -> 中層:插圖 -> 頂層:字幕)...")
    # 這裡的順序決定了層級：後面的蓋在前面的上面
    final_video = CompositeVideoClip([final_bg_video] + overlay_clips + text_clips)
    
    print(f"開始渲染輸出: {OUTPUT_FILE}...")
    final_video.write_videofile(OUTPUT_FILE, fps=24, codec="libx264")
    print("渲染完成！")

if __name__ == "__main__":
    test_render()
