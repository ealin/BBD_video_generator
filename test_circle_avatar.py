import os
import numpy as np
from PIL import Image, ImageDraw, ImageChops
from moviepy import *

def make_circle_avatar(img_path, target_width):
    try:
        # 開啟圖片並轉為 RGBA
        avatar = Image.open(img_path).convert("RGBA")
        
        # 裁切成正方形 (取中間部分)
        min_side = min(avatar.size)
        left = (avatar.width - min_side) / 2
        top = (avatar.height - min_side) / 2
        right = (avatar.width + min_side) / 2
        bottom = (avatar.height + min_side) / 2
        avatar = avatar.crop((left, top, right, bottom))
        
        # 縮放至目標大小
        avatar = avatar.resize((target_width, target_width), Image.Resampling.LANCZOS)
        
        # 建立圓形遮罩
        mask = Image.new('L', (target_width, target_width), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, target_width, target_width), fill=255)
        
        # 若原圖有透明度，將原本的 alpha 通道與圓形遮罩做交集 (darker)
        _, _, _, alpha = avatar.split()
        new_alpha = ImageChops.darker(alpha, mask)
        avatar.putalpha(new_alpha)
        
        return avatar
    except Exception as e:
        print(f"處理圖片 {img_path} 失敗: {e}")
        return None

def test_circle_avatar():
    OUTPUT_FILE = "test_head_circle.mp4"
    BACKGROUND_COLOR = (0, 255, 0)
    HEAD_WIDTH = 200  # 設定較大的尺寸方便觀察
    DURATION = 10     # 總長度 10 秒
    FPS = 24
    
    avatars = ["AA.png", "BB.png", "CC.png"]
    
    # 預先處理三個頭像為圓形
    processed_avatars = {}
    for av in avatars:
        if os.path.exists(av):
            processed_avatars[av] = make_circle_avatar(av, HEAD_WIDTH)
        else:
            print(f"找不到圖片: {av}")
            
    # 每秒產生一張 frame (MoviePy 建議寫法：使用 make_frame)
    # 我們每 3.33 秒切換一個頭像
    def make_frame(t):
        # 決定當前頭像
        idx = int((t / DURATION) * len(avatars))
        if idx >= len(avatars):
            idx = len(avatars) - 1
            
        current_av_name = avatars[idx]
        current_avatar = processed_avatars.get(current_av_name)
        
        # 建立全綠底
        base_img = Image.new("RGB", (1920, 1080), BACKGROUND_COLOR)
        
        if current_avatar:
            # 貼在畫面中央偏左，模擬實際場景
            x = 860
            y = 440
            base_img.paste(current_avatar, (x, y), current_avatar)
            
        return np.array(base_img)
        
    # 建立 VideoClip
    print("開始生成圓形頭像測試影片...")
    video = VideoClip(make_frame, duration=DURATION)
    video.write_videofile(OUTPUT_FILE, fps=FPS, codec="libx264", audio=False)
    print(f"測試影片已生成: {OUTPUT_FILE}")

if __name__ == "__main__":
    test_circle_avatar()
