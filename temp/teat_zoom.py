import os
from moviepy import *
from moviepy.video import *
from moviepy.audio import *
from moviepy.audio.AudioClip import AudioClip
from moviepy.video.VideoClip import VideoClip
from moviepy.video.fx import FadeIn, FadeOut, CrossFadeIn, CrossFadeOut, Scroll
from moviepy.video.fx import MaskColor
from moviepy.audio.fx import AudioFadeIn, AudioFadeOut, AudioNormalize
from PIL import Image
import numpy as np

import random

def create_zoom_in_slideshow(image_dir, output_file="output.mp4", duration_per_image=3, resolution=(1920, 1080), zoom_scale=1.1):
    """
    製作 zoom-in 動畫的圖片幻燈片影片，使用 moviepy 2.0 相容寫法。
    """
    image_files = sorted([f for f in os.listdir(image_dir) if f.lower().endswith(".jpg")])
    clips = []

    for filename in image_files:
        path = os.path.join(image_dir, filename)

        # 載入圖片並轉為 np.array
        img = Image.open(path).convert("RGB")
        img = img.resize(resolution, Image.LANCZOS)
        img_np = np.array(img)

        def make_frame(t, img_np=img_np):
            # t 從 0 到 duration，放大倍率從 1.0 到 zoom_scale
            scale = 1.0 + (zoom_scale - 1.0) * (t / duration_per_image)
            h, w = img_np.shape[:2]
            center_x, center_y = w // 2, h // 2

            # 計算縮放後的裁切範圍
            crop_w, crop_h = int(w / scale), int(h / scale)
            x1 = max(center_x - crop_w // 2, 0)
            y1 = max(center_y - crop_h // 2, 0)
            x2 = x1 + crop_w
            y2 = y1 + crop_h

            cropped = img_np[y1:y2, x1:x2]
            zoomed = np.array(Image.fromarray(cropped).resize(resolution, Image.LANCZOS))
            return zoomed

        clip = VideoClip(make_frame=make_frame, duration=duration_per_image)
        clips.append(clip)

    final = concatenate_videoclips(clips, method="compose")
    final.write_videofile(output_file, fps=24)


# ✅ 使用範例
if __name__ == "__main__":
    create_zoom_in_slideshow(
        image_dir="./主題圖片/紫金山彗星",          # 圖片資料夾路徑
        output_file="slideshow.mp4",   # 輸出檔名
        duration_per_image=3,          # 每張圖片顯示秒數
        resolution=(1920, 1080),       # 輸出解析度
        zoom_scale=1.1                 # 總放大倍率（例如 1.1 = 放大10%）
    )