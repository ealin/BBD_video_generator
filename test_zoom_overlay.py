import os
import numpy as np
from PIL import Image
from moviepy import *

# 配置參數
ZOOM_STOPS_AT = 10  # 10 秒完成縮放 (加快 1.5 倍)
TARGET_IMAGE_SIZE = 540  # 縮小為原本 720 的 3/4

def make_crop_zoom_clip(img_path, duration, target_size, zoom_stops_at):
    # 載入原始圖片並轉為 RGBA
    pil_img = Image.open(img_path).convert("RGBA")
    
    # 1. 先將原始圖片裁切為正方形 (取中心部分)
    w, h = pil_img.size
    min_side = min(w, h)
    left = (w - min_side) / 2
    top = (h - min_side) / 2
    right = (w + min_side) / 2
    bottom = (h + min_side) / 2
    square_img = pil_img.crop((left, top, right, bottom))

    def make_frame(t):
        # 計算當前的縮放比例 (從 1.2x 漸變到 1.0x)
        if t <= zoom_stops_at:
            scale = 1.2 - (1.2 - 1.0) * (t / zoom_stops_at)
        else:
            scale = 1.0
            
        # 計算當前放大後的尺寸
        cur_size = int(target_size * scale)
        resized_img = square_img.resize((cur_size, cur_size), Image.Resampling.LANCZOS)
        
        # 從放大後的圖片中，裁切出中央固定大小 (target_size x target_size) 的區域
        c_left = (cur_size - target_size) / 2
        c_top = (cur_size - target_size) / 2
        c_right = c_left + target_size
        c_bottom = c_top + target_size
        
        cropped_img = resized_img.crop((c_left, c_top, c_right, c_bottom))
        return np.array(cropped_img)

    return VideoClip(make_frame, duration=duration)

def test_render():
    OUTPUT_FILE = "test_zoom_sub.mp4"
    BACKGROUND_COLOR = (0, 255, 0)
    DURATION = 30  # 測試 30 秒
    
    # 建立純綠色背景
    bg_clip = ColorClip(size=(1920, 1080), color=BACKGROUND_COLOR, duration=DURATION)
    
    # 尋找第一張背景圖片
    img_path = None
    for ext in ['.jpeg', '.jpg', '.png']:
        p = os.path.join("bg_image/bg129", f"0{ext}")
        if os.path.exists(p):
            img_path = p
            break
            
    overlay_clips = []
    if img_path:
        print(f"找到圖片: {img_path}，開始設定 Ken Burns 縮放動畫...")
        # 產生固定外框大小的 Ken Burns 縮放影片片段
        img_clip = make_crop_zoom_clip(img_path, DURATION, TARGET_IMAGE_SIZE, ZOOM_STOPS_AT)
        
        # 由於外框大小始終固定為 TARGET_IMAGE_SIZE (540)，
        # 位置也可以直接固定在右半部中央：
        pos_x = 1440 - TARGET_IMAGE_SIZE // 2  # 1440 - 270 = 1170
        pos_y = 540 - TARGET_IMAGE_SIZE // 2   # 540 - 270 = 270
        
        img_clip = img_clip.with_position((pos_x, pos_y))
        img_clip = img_clip.with_start(0)
        overlay_clips.append(img_clip)
    else:
        print("找不到測試用的背景圖片！")
        return

    # 建立測試字幕 (靠左對齊)
    text_content = (
        "這是一段測試字幕...\n"
        "1. 圖畫佔據畫面的外框大小 (540x540) 始終不變。\n"
        "2. 剛開始只顯示內部 zoomed-in 畫面。\n"
        "3. 隨著時間 (10秒內) 漸漸 reveal 顯示出完整大圖。\n"
        "4. 在 10 秒後停下來並持續顯示完整大圖。"
    )
    
    text_clip = TextClip(
        text=text_content,
        font_size=48,
        color=(255, 255, 255),
        stroke_color='black',
        stroke_width=2,
        font='TaipeiSansTCBeta-Regular.ttf',
        method='label',
        text_align='left',
        interline=15
    ).with_position((50, 500)).with_duration(DURATION)
    
    # 合成並渲染
    final_video = CompositeVideoClip([bg_clip] + overlay_clips + [text_clip])
    
    print(f"開始渲染輸出: {OUTPUT_FILE}...")
    final_video.write_videofile(OUTPUT_FILE, fps=24, codec="libx264")
    print("渲染完成！")

if __name__ == "__main__":
    test_render()
