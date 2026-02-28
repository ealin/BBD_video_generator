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

from PIL import Image
import re
from typing import List


def sort_filenames(names: List[str], case_sensitive: bool = False) -> List[str]:
    """
    以「自然排序」排序檔名清單（把字串中的連續數字視為整數比較）。
    例：["10.jpg", "2.jpg", "1.jpg"] -> ["1.jpg", "2.jpg", "10.jpg"]

    :param names: 檔名字串的串列
    :param case_sensitive: 是否區分大小寫（預設不區分）
    :return: 排序後的新串列
    """
    def natural_key(s: str):
        s_cmp = s if case_sensitive else s.lower()
        # 將字串切成「非數字」與「數字」片段；數字片段轉成 int 以數值比較
        return [int(part) if part.isdigit() else part
                for part in re.split(r"(\d+)", s_cmp)]
    return sorted(names, key=natural_key)



def resize_image(input_path, output_path):
    """
    处理输入图像：
    - 如果是竖直的（高 > 宽）：高度缩放至 1080，宽度按比例缩放，绿色填充空白，生成 1920x1080 图像。
    - 如果是横向的（宽 > 高）：宽度缩放至 1920，高度按比例缩放至 1080，无需填充。

    :param input_path: str, 输入图像的文件路径 (.jpg)
    :param output_path: str, 输出处理后的图像路径 (.jpg)
    """
    # 打开原始图像
    img = Image.open(input_path)
    original_width, original_height = img.size

    # 目标分辨率
    target_width = 1080
    target_height = 1920

    #print(" 一般寬图像处理")
    resized_img = img.resize((target_width,target_height), Image.LANCZOS)
    resized_img.save(output_path)

    print(f"Resize 处理完成，已保存至: {output_path}")




def create_video_from_images_with_ZOOMING(directory, zoom_scale, t1, t2, chn_strings, eng_strings,  A_roll_MP3_dir, output_file):
    """
    将指定目录中的 .jpg 文件以随机顺序生成一个总时长为 t2 的 MP4 视频。
    每张图片的显示时间为 t1，所有图片解析度调整为 1920x1080。

    :param directory: str, 包含 .jpg 文件的目录路径
    :param t1: int, 每张图片的显示时间（秒）
    :param t2: int, 输出视频的总时长（秒）
    :param output_file: str, 输出视频文件路径

    chn_strings, eng_strings:  顯示在圖上的字串
    """

    # 获取目录中的所有 .jpg 文件
    image_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.png')]

    if not image_files:
            print(f"目录 {directory} 中没有找到任何 .png 文件！")
            return

    # 创建临时目录存放调整解析度后的图片
    temp_dir = os.path.join(directory, "temp_resized")
    os.makedirs(temp_dir, exist_ok=True)

    resized_files = []
    for img_file in image_files:
            resized_path = os.path.join(temp_dir, os.path.basename(img_file))
            print(img_file)
            resize_image(img_file, resized_path)
            resized_files.append(resized_path)

    # 图片文件 - 依據檔名排序
    resized_files = sort_filenames(resized_files)
    print("Sorting")
    print( resized_files)

    # 计算需要的图片数量
    num_images = t2 // t1
    if num_images > len(resized_files):
            print("警告：可用图片不足，将循环使用图片以填满时长！")
            resized_files = (resized_files * (num_images // len(resized_files) + 1))[:num_images]
    else:
            resized_files = resized_files[:num_images]

    clips = []
    frame_num = 0
    for filename in resized_files:

        print("!!!! processing :" + resized_files[frame_num])

        # 載入圖片並轉為 np.array
        img = Image.open(resized_files[frame_num]).convert("RGB")
        #img = img.resize((1920,1080)), Image.LANCZOS)
        img_np = np.array(img)

        def make_frame(t, img_np=img_np):
            # t 從 0 到 duration，放大倍率從 1.0 到 zoom_scale
            scale = 1.0 + (zoom_scale - 1.0) * (t / t1)
            h, w = img_np.shape[:2]
            center_x, center_y = w // 2, h // 2

            # 計算縮放後的裁切範圍
            crop_w, crop_h = int(w / scale), int(h / scale)
            x1 = max(center_x - crop_w // 2, 0)
            y1 = max(center_y - crop_h // 2, 0)
            x2 = x1 + crop_w
            y2 = y1 + crop_h

            cropped = img_np[y1:y2, x1:x2]
            zoomed = np.array(Image.fromarray(cropped).resize(((1080,1920)), Image.LANCZOS))
            return zoomed

        video_clip = VideoClip(make_frame=make_frame, duration=t1)

        # 一開始插入一張沒有字幕的圖
        if frame_num == 0 :
            open_frame_clip = ImageClip(resized_files[0]).with_duration(0.5)
            clips.append(open_frame_clip)

        # create chinese-text clip
        txt_font_size = 64
        font_color= (255,255,153) #香檳黃
        font_strok_color='black'
        font_strok_width=2
        string_left = 30
        string_top = 500+100
        string_method='label'
        string_size=(None,None)
        string_text_align = 'left'
        font_ttf = 'TaipeiSansTCBeta-Regular.ttf'

        text_clip = TextClip(
            text=chn_strings[frame_num],
            font_size=txt_font_size+16,
            color=font_color,                    # can use RGB as a color
            bg_color=(0, 255, 0),           # (0, 255, 0),
            stroke_color=font_strok_color,
            stroke_width=font_strok_width,
            margin=(string_left,string_top),               # 控制字串的左上角位置
            method=string_method,
            size=string_size,
            text_align=string_text_align,   
            interline=30,                   # 行距
            font=font_ttf,
            transparent=True)
        text_clip = MaskColor(color=(0,255,1),threshold=20, stiffness=3).apply(text_clip) 


        text_clip2 = TextClip(
            text=eng_strings[frame_num],
            font_size=txt_font_size-8,
            color='white',  #font_color,                    # can use RGB as a color
            bg_color=(0, 255, 0),           # (0, 255, 0),
            stroke_color=font_strok_color,
            stroke_width=font_strok_width,
            margin=(string_left,string_top+500),               # 控制字串的左上角位置
            method=string_method,
            size=string_size,
            text_align=string_text_align,   
            interline=30,                   # 行距
            font=font_ttf,
            transparent=True)
        text_clip2 = MaskColor(color=(0,255,1),threshold=20, stiffness=3).apply(text_clip2) 


        frame_num = frame_num + 1
        clip = CompositeVideoClip([video_clip, text_clip, text_clip2],use_bgclip=True).with_duration(t1) #.with_audio(audio_clip)
  
        clips.append(clip)
        
 
    # create audio clip
    audio_files = [os.path.join(A_roll_MP3_dir, f) for f in os.listdir(A_roll_MP3_dir) if (f.endswith('.m4a') or f.endswith('.mp3')) ]
    if not audio_files:
        print(f"目录 {directory} 中没有找到任何 .mp3 or m4a 文件！")
        return

    # 打乱音频文件的顺序
    random.shuffle(audio_files)
    print("Selected Audio file:" + audio_files[0])

    a_clip = AudioFileClip(audio_files[0])
    #a_clip.with_duration(t1) 

    video_final_clip = concatenate_videoclips(clips, method="compose")
    video_final_clip = video_final_clip.with_audio(a_clip)

    video_final_clip.write_videofile(output_file, fps=24)
    a_clip.close()




# parameters
#
A_roll_IMG_dir = "b110_short_bg006"
A_roll_MP3_dir = "./bg_mp3/short/45S"
JPG_number = 9                      # 1.jpg, 2.jpg ... 6.jpg (png OK also)
zoom_scale = 1.3

Each_JPG_Length = 5               # sec. 


chn_strings = [ \
	"[書摘]：\n常見症狀的呼吸工具箱", \
	"鼻塞先用溫熱與濕度，\n緩解黏膜充血。", \
	"咳嗽夜間採半坐臥，\n減少氣道刺激。", \
	"空調過冷過乾都要調整。", \
	"若出現喘鳴或久咳，\n及早就醫評估。", \
	"運動時分段與休息，\n避免過度換氣。", \
	"善用鼻吸口吐與節奏，\n可降低不適。", \
	"配合醫囑用藥，\n不逞強。", \
	"除了身體，\n把日常環境也一起調整。" \
]
eng_strings = [ \
	"[Topic]: \nBreathing Toolbox for \nCommon Symptoms.", \
	"For congestion,use warmth and \nhumidity to ease mucosal swelling.", \
	"For cough,sleep semi-upright to \nreduce airway irritation.", \
	"Tune AC that’s too cold or \ntoo dry.", \
	"If wheeze or long cough appears,\nseek early medical evaluation.", \
	"During exercise,\nbreak into segments and \nrest to avoid overbreathing.", \
	"Use nose-in,\nmouth-out and cadence to \nreduce discomfort.", \
	"Follow prescribed meds—\ndon’t tough it out.", \
	"Adjust the daily environment too." \
]
	#"二氧化碳是人體穩態守門員".  // <== 中文一行長度參考
    #"Breath quality drives your energy."  // <==. 英文一行長度參考




create_video_from_images_with_ZOOMING("./bg_image/"+A_roll_IMG_dir, zoom_scale, Each_JPG_Length, Each_JPG_Length*JPG_number, \
                                      chn_strings, eng_strings, \
                                      A_roll_MP3_dir, \
                                      A_roll_IMG_dir+".mp4")
