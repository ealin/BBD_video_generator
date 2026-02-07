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


def convert_webp_to_jpg_with_resolution(input_file, resolution):
    """
    将指定的 .webp 文件转换为指定解析度，并保存为同名的 .jpg 文件。

    :param input_file: str, 输入 .webp 文件路径
    :param resolution: tuple, 目标分辨率 (宽度, 高度)
    """
    try:
        # 获取输出文件名，将扩展名改为 .jpg
        output_file = input_file.rsplit('.', 1)[0] + "-2.jpg"

        # 打开 .webp 文件
        with Image.open(input_file) as img:
            # 调整图像大小
            resized_img = img.resize(resolution, Image.LANCZOS)
            # 转换为 RGB 模式（JPG 不支持透明度）
            rgb_img = resized_img.convert("RGB")
            # 保存为 .jpg 文件
            rgb_img.save(output_file, "JPEG")
            print(f"图像已成功转换为解析度 {resolution} 并保存为 {output_file}")
    except Exception as e:
        print(f"处理图像时出错: {e}")


def convert_png_to_jpg_with_resolution(input_file, resolution):
    """
    将指定的 .png 文件转换为指定解析度，并保存为同名的 .jpg 文件。

    :param input_file: str, 输入 .png 文件路径
    :param resolution: tuple, 目标分辨率 (宽度, 高度)
    """
    try:
        # 获取输出文件名，将扩展名改为 .jpg
        output_file = input_file.rsplit('.', 1)[0] + ".jpg"

        # 打开 .png 文件
        with Image.open(input_file) as img:
            # 调整图像大小
            resized_img = img.resize(resolution, Image.LANCZOS)
            # 转换为 RGB 模式（JPG 不支持透明度）
            rgb_img = resized_img.convert("RGB")
            # 保存为 .jpg 文件
            rgb_img.save(output_file, "JPEG")
            print(f"图像已成功转换为解析度 {resolution} 并保存为 {output_file}")
    except Exception as e:
        print(f"处理图像时出错: {e}")


class Topic:
    """
    定义一个包含 line, second, time 属性的数据结构。
    """
    def __init__(self, line, second, time):
        self.line = line  # 字符串属性
        self.second = second  # 浮点数属性
        self.time = time  # 字符串属性

    def __repr__(self):
        # 定义如何打印 Topic 对象
        #return f"Topic(line='{self.line}', second={self.second}, time='{self.time}')"
        return f"Topic( '{self.time}' '{self.line}')"


def starts_with_pattern(line, pattern):
    """
    判断字符串是否以指定的子字符串开头。

    :param line: str, 要检查的字符串
    :param pattern: str, 指定的子字符串
    :return: bool, 如果字符串以子字符串开头返回 True，否则返回 False
    """
    return line.startswith(pattern)


def format_seconds_to_hms(seconds):
    """
    将秒数转换为时:分:秒格式的字符串。

    :param seconds: int, 输入的秒数
    :return: str, 转换后的时:分:秒格式字符串
    """
    seconds = int(seconds)  # 确保输入是整数

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    #return f"{hours:02}:{minutes:02}:{secs:02}"
    return f"{minutes:02}:{secs:02}"

        # 创建静音音频生成器
def make_silence(t):
    return 0.0  # 静音信号，返回 0 振幅
    

def generate_videos_from_txt_and_mp3(txt_dir, voice_dir, bg_img_dir, output_file, start_second, topic_index, bg_type = 0):
    """
    从指定目录中的 .txt 文件和对应的 .mp3 文件生成视频。
    视频背景为全绿，字幕为 .txt 文件内容，音频为 .mp3 文件内容。

    :param txt_dir: str, .txt 文件所在目录
    :param voice_dir: str, .mp3 文件所在目录
    :param output_file: str, 输出视频檔案
    topic_index = 0         開始處理的是第幾個topic  (根據此變數決定要抓哪張圖), start from 0.jpg

    bg_type -  0: 背景是靜態圖片 (bg_image/0.png, 1.png....)
               1: 背景是短影片 (bg_image/0.mp4, 1.mp4....)
                
    """
    # 确保输出目录存在
    #os.makedirs(output_dir, exist_ok=True)

    #--------------------------------------------------
    #--------------------------------------------------
    #--------------------------------------------------
    # configuration
    background_color = (0, 255, 0)  # 綠色背景
    font_ttf = 'TaipeiSansTCBeta-Regular.ttf'  #'BpmfGenSenRounded-R.ttf'  #'Annotated.ttf' (<- 注音)
    font_color= (255,255,153) #香檳黃 #'white' #yellow'
    font_strok_color='black'
    font_strok_width=2
    txt_font_size = 56
    topic_font_color='white'
    topic_font_strok_color='black'
    topic_font_strok_width=2
    topic_txt_font_size = 46
    topic_font_background_color = (0, 49,83) #普魯士藍  #(255,128,153)  #浅鲑红  #'red'
    topic_font_ttf = 'TaipeiSansTCBeta-Bold.ttf'  #'Annotated.ttf'  #'BpmfGenSenRounded-EL.ttf'  
    max_line = 0    # 0 means no limited   (for test usage)

    pattern_ending = ">>>>結論"
   
    pattern_new_line = '<'
    pattern_topic = '>>>>'
    pattern_no_show = '!!!!' 

    # top image 會延續幾個 page?
    topic_image_page_no = 5

    pending_duration=2
    pending_color=(0,0,0)  #black

    # configuration
    #--------------------------------------------------
    #--------------------------------------------------

    # 為 topic 加入幾個page的插圖
    topic_image_index = -1   # 自topic開始會連續顯示幾頁的image，此變數紀錄目前顯示到第幾頁 (-1 means no need BG image)

    clips = []
    acc_second = start_second

    # 创建一个 Topic 数组
    topic_array = []

    # 遍历 .txt 文件目录
    all_txt_files = os.listdir(txt_dir)
    all_txt_files.sort()

    with_topic_flag = False
    topic_text = ""


    for txt_file in all_txt_files:

        if max_line != 0:
            max_line = max_line - 1
            if max_line == 0 :
                break

        if txt_file.endswith(".txt"):
            # 获取文件名（无扩展名）
            base_name = os.path.splitext(txt_file)[0]
            txt_path = os.path.join(txt_dir, txt_file)
            mp3_path = os.path.join(voice_dir, f"{base_name}.mp3")

            # 检查对应的 .mp3 文件是否存在
            if not os.path.exists(mp3_path):
                print(f"音频文件 {mp3_path} 不存在，跳过 {txt_file}")
                continue

            # 读取 .txt 文件内容作为字幕
            with open(txt_path, "r", encoding="utf-8") as f:
                subtitle_text = f.read().strip()

            # 加载音频
            if subtitle_text == ">>>>" :
                # 创建静音 AudioClip
                audio_clip = AudioClip(make_silence, duration=1, fps=44100)
                duration = 1
            elif starts_with_pattern(subtitle_text, "@@@@"):
                duration = pending_duration
            else:
                audio_clip = AudioFileClip(mp3_path)
                duration = audio_clip.duration  #單位 (second)
           
            # 创建字幕

            # 換行符號
            subtitle_text = subtitle_text.replace(pattern_new_line,'\n')

            # topic - 不同位置與字體
            if starts_with_pattern(subtitle_text, pattern_topic):  # topic
                topic_text = subtitle_text
                with_topic_flag=True
                
                print("*****  topic string:" + subtitle_text + "start time = " + format_seconds_to_hms(acc_second) )
                topic_array.append(Topic(subtitle_text, acc_second, format_seconds_to_hms(acc_second)))
                text_clip = TextClip(       # 全綠, i.e. 只為了產生此物件，畫面上看不到字
                    text="隱形", font=font_ttf,
                    font_size=txt_font_size,color=background_color, bg_color=background_color,stroke_color=background_color,stroke_width=1,
                     method='caption', size=(2,None),text_align='center', interline=30)
                
                topic_image_index =  0  # 自topic開始會連續顯示幾頁的image，此變數紀錄目前顯示到第幾頁
                topic_index = topic_index + 1         # 目前處理的是第幾個topic  (根據此變數決定要抓哪張圖, start from 1)
           
            else:    

                    # 創建字幕的文字片段 (需分別一般段落或title 判斷：>>>>)
                if string_align == 'center':   # 中間靠右
                        string_left = 200
                        string_top = 450
                        string_text_align = 'center'
                        string_method='caption'
                        string_size=(1920,None)
                else :                  # 對齊左邊邊框
                        string_left = 30
                        string_top = 500
                        string_text_align = 'left'
                        string_method='label'
                        string_size=(None,None)
                 

                if topic_image_index != -1 and topic_image_index < topic_image_page_no :
                    

                    #txt_clip = TextClip(text=subtitle_text, font_size=txt_font_size, color=font_color, font=font_ttf, bg_color=None)
    

                    text_clip = TextClip(
                                text= subtitle_text,   #'\n'+subtitle_text+'\n',
                                font_size=txt_font_size,  # 字体大小
                                color=font_color,                    # can use RGB as a color
                                bg_color= (0,255,0), 
                                #bg_color=None,
                                stroke_color=font_strok_color,
                                stroke_width=font_strok_width,
                                margin=(string_left,string_top),               # 控制字串的左上角位置
                                text_align= string_text_align, 
                                font=font_ttf,
                                interline=15, 
                            ).with_position(string_text_align) #.with_duration(duration)

                    
                    text_clip = MaskColor(color=(0,255,1),threshold=20, stiffness=3).apply(text_clip)   

                else:

                    text_clip = TextClip(
                        text=subtitle_text,
                        font_size=txt_font_size,
                        color=font_color,                    # can use RGB as a color
                        bg_color=background_color,           # (0, 255, 0),
                        stroke_color=font_strok_color,
                        stroke_width=font_strok_width,
                        margin=(string_left,string_top),               # 控制字串的左上角位置
                        method=string_method,
                        size=string_size,
                        text_align=string_text_align,   
                        interline=30,                   # 行距
                        #horizontal_align='left',
                        font=font_ttf,
                        transparent=True)
                    
            if with_topic_flag == True:
                topic_clip = TextClip(
                text=topic_text,
                font_size=topic_txt_font_size,
                color=topic_font_color,                    # can use RGB as a color
                bg_color=topic_font_background_color,         
                stroke_color=topic_font_strok_color,
                stroke_width=topic_font_strok_width,
                margin=(10,10),               # 控制字串的左上角位置
                method='label',                 # 不會自動換行！
                text_align='left',      #'left',   
                interline=30,                   # 行距
                font=topic_font_ttf)

                #print("with_topic_flag == True")


            # 創建背景 單色或圖片
            if topic_image_index != -1 and topic_image_index < topic_image_page_no :

                try:
                    if bg_type == 1:
                        video_filename = os.path.join(bg_img_dir, f"{topic_index-1}.mp4")
                        print(video_filename)
                        bg_clip = VideoFileClip(video_filename).resized( (1920,1080), Image.LANCZOS)
                        topic_image_index = -1  # 下個page後就不需要顯示背景圖了

                        if duration <= 9:
                            duration = duration + 1

                        # <======================================
                        #todo: 函數加參數 - done
                        #todo: 謝謝收看的影片
                        #todo: 去浮水印 - using 剪映 https://www.youtube.com/watch?v=y86gUFle7WM  - done
                    else :                    
                        image_filename = os.path.join(bg_img_dir, f"{topic_index-1}.jpg")
                        print(image_filename)

                        resize_image2(image_filename, 'temp.jpg')
                        bg_clip = ImageClip('temp.jpg')   #image_filename) #.resized(width=1920, height=1080)

                        topic_image_index = topic_image_index + 1
                        if topic_image_index == topic_image_page_no :
                            topic_image_index = -1  # 下個page後就不需要顯示背景圖了
                    
                except Exception as e:
                    bg_clip = ColorClip(size=(1920, 1080), color=background_color, duration=duration)
                    topic_image_index = -1
            else :        
                bg_clip = ColorClip(size=(1920, 1080), color=background_color, duration=duration)
                #bg_clip = ColorClip(size=(1920, 1080), is_mask=True, color=0, duration=duration) 

            # '!!!!' 不產生字幕
            if starts_with_pattern(subtitle_text, pattern_no_show):  # topic
                # 合成背景、字幕和音频
                video_clip = CompositeVideoClip([bg_clip]).with_duration(duration).with_audio(audio_clip,)
            elif starts_with_pattern(subtitle_text, '@@@@'): #subtitle_text == '@@@@' :
                # 黑屏延續一段時間 / 換場
                video_clip = ColorClip(size=(1920, 1080), color=pending_color, duration=pending_duration)
            else:
                if with_topic_flag == True and topic_text != '>>>>' :
                     # 合成背景、字幕、topic和音频
                    video_clip = CompositeVideoClip([bg_clip, text_clip, topic_clip],use_bgclip=True).with_duration(duration).with_audio(audio_clip)
                else:
                    # 合成背景、字幕和音频
                    video_clip = CompositeVideoClip([bg_clip, text_clip],use_bgclip=True).with_duration(duration).with_audio(audio_clip)
            
            acc_second = acc_second + duration

            # 输出视频
            #video_clip.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")
            #print(f"生成视频：{output_path}")
            clips.append(video_clip)
 
            if starts_with_pattern(subtitle_text, pattern_ending): 
                with_topic_flag = False

    print("打印 Topic 数组中的所有元素:")
    topic_num = 0
    for topic in topic_array:
        print(f"{topic.time} {topic.line}")
        topic_num = topic_num + 1


    print("輸出視頻長度：")
    print(acc_second)

    # 合併所有片段
    final_clip = concatenate_videoclips(clips, method="compose")
    final_clip.write_videofile(output_file, fps=24, codec='libx264', audio_codec='aac')

    return topic_num, int(acc_second)+1


def create_random_video_from_directory(directory, target_duration, output_file):
    """
    从指定目录中随机选择 .mp4 文件并连接成一个指定时长的视频。

    :param directory: str, 包含 .mp4 文件的目录路径
    :param target_duration: int, 目标视频总时长（秒）
    :param output_file: str, 输出视频文件路径
    """
    try:
        # 获取目录中的所有 .mp4 文件
        video_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.mp4')]

        if not video_files:
            print(f"目录 {directory} 中没有找到任何 .mp4 文件！")
            return

        # 加载视频剪辑并计算总时长
        clips = []
        total_duration = 0
        loop_count = 0

        while total_duration < target_duration :
            print(f"loop count:  {loop_count}")
            loop_count = loop_count + 1

            # 打乱视频文件的顺序
            random.shuffle(video_files)

            for video_file in video_files:

                print("processing:" + video_file)
                clip = VideoFileClip(video_file).resized( (1920,1080), Image.LANCZOS)
                clip_duration = clip.duration

                clip = CrossFadeIn(1).apply(clip)
                clip = CrossFadeOut(1).apply(clip)

                # 如果当前片段加入后总时长超过目标，裁剪至剩余时间
                if total_duration + clip_duration > target_duration:
                    #clip = clip.subclip(0, target_duration - total_duration)
                    clips.append(clip)
                    total_duration += clip_duration
                    break

                clips.append(clip)
                total_duration += clip_duration

                print(f"total_duration:  {total_duration},target_duration:  {target_duration}   ")

                # 如果已达到目标时长，停止选择
                if total_duration >= target_duration:
                    print("time is enough!")
                    break
        
        
        # 合并所有剪辑
        final_video = concatenate_videoclips(clips, method="compose")

        # 输出最终视频
        final_video.write_videofile(output_file, fps=24, codec="libx264", audio_codec="aac")
        print(f"视频已成功生成：{output_file}")

    except Exception as e:
        print(f"处理视频时出错: {e}")


def resize_image(input_path, output_path, resolution=(1920, 1080)):
    """
    调整图像到指定解析度。

    :param input_path: str, 输入图像文件路径
    :param output_path: str, 输出图像文件路径
    :param resolution: tuple, 目标解析度 (宽度, 高度)
    """
    with Image.open(input_path) as img:
        resized_img = img.resize(resolution, Image.LANCZOS)
        resized_img.save(output_path)


def resize_image2(input_path, output_path, resolution=(1920, 1080)):
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
    target_width = 1920
    target_height = 1080

    if original_height >= original_width:
        print(" 竖直图像处理XXXS")
        new_height = target_height - 10 # 高度调整为 1080
        new_width = int(original_width * (target_height / original_height))  # 等比例缩放宽度

        print(f"new height: {new_height},   new width: {new_width}" ) 
        #print(output_path)

        # 调整图像尺寸
        img_resized = img.resize((new_width, new_height), Image.LANCZOS)
        #print(img_resized)

        # 创建 1920x1080 绿色背景
        canvas = Image.new("RGB", (target_width, target_height),  (0,49,83))  #(0, 255, 0))  # 绿色背景
        #print(canvas)

        # 计算居中位置（水平居中）
        x_offset = (target_width - new_width) - 100
        print(f"x_offset = {x_offset}")
        canvas.paste(img_resized, (x_offset, 0))

        # 保存图像
        try:
            canvas.save(output_path, "JPEG")
            print("OKOK")
        except Exception as e:
            print(e)

    else:
        print(" 一般寬图像处理")
        resized_img = img.resize(resolution, Image.LANCZOS)
        resized_img.save(output_path)

    print(f"处理完成，已保存至: {output_path}")



def create_video_from_images_with_ZOOMING(directory, zoom_scale, t1, t2, output_file):
    """
    将指定目录中的 .jpg 文件以随机顺序生成一个总时长为 t2 的 MP4 视频。
    每张图片的显示时间为 t1，所有图片解析度调整为 1920x1080。

    :param directory: str, 包含 .jpg 文件的目录路径
    :param t1: int, 每张图片的显示时间（秒）
    :param t2: int, 输出视频的总时长（秒）
    :param output_file: str, 输出视频文件路径
    """

    # 获取目录中的所有 .jpg 文件
    image_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.jpg')]

    if not image_files:
            print(f"目录 {directory} 中没有找到任何 .jpg 文件！")
            return

    # 创建临时目录存放调整解析度后的图片
    temp_dir = os.path.join(directory, "temp_resized")
    os.makedirs(temp_dir, exist_ok=True)

    resized_files = []
    for img_file in image_files:
            resized_path = os.path.join(temp_dir, os.path.basename(img_file))
            print(img_file)
            resize_image2(img_file, resized_path)
            resized_files.append(resized_path)

    # 打乱图片文件的顺序
    random.shuffle(resized_files)

    # 计算需要的图片数量
    num_images = t2 // t1
    if num_images > len(resized_files):
            print("警告：可用图片不足，将循环使用图片以填满时长！")
            resized_files = (resized_files * (num_images // len(resized_files) + 1))[:num_images]
    else:
            resized_files = resized_files[:num_images]

    clips = []
    for filename in resized_files:

        # 載入圖片並轉為 np.array
        img = Image.open(filename).convert("RGB")
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
            zoomed = np.array(Image.fromarray(cropped).resize(((1920,1080)), Image.LANCZOS))
            return zoomed

        clip = VideoClip(make_frame=make_frame, duration=t1)
        clips.append(clip)

    final = concatenate_videoclips(clips, method="compose")
    final.write_videofile(output_file, fps=24)
    







def create_video_from_images(mix_mode, directory, t1, t2, output_file):
    """
    将指定目录中的 .jpg 文件以随机顺序生成一个总时长为 t2 的 MP4 视频。
    每张图片的显示时间为 t1，所有图片解析度调整为 1920x1080。

    :param directory: str, 包含 .jpg 文件的目录路径
    :param t1: int, 每张图片的显示时间（秒）
    :param t2: int, 输出视频的总时长（秒）
    :param output_file: str, 输出视频文件路径
    """
    try:

        # 获取目录中的所有 .jpg 文件
        image_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.jpg')]

        if not image_files:
            print(f"目录 {directory} 中没有找到任何 .jpg 文件！")
            return

        # 创建临时目录存放调整解析度后的图片
        temp_dir = os.path.join(directory, "temp_resized")
        os.makedirs(temp_dir, exist_ok=True)

        resized_files = []
        for img_file in image_files:
            resized_path = os.path.join(temp_dir, os.path.basename(img_file))
            print(img_file)
            resize_image2(img_file, resized_path)
            resized_files.append(resized_path)


        # 打乱图片文件的顺序
        random.shuffle(resized_files)

        # 计算需要的图片数量
        num_images = t2 // t1
        if num_images > len(resized_files):
            print("警告：可用图片不足，将循环使用图片以填满时长！")
            resized_files = (resized_files * (num_images // len(resized_files) + 1))[:num_images]
        else:
            resized_files = resized_files[:num_images]
      
        clips = []
        for img in resized_files:

            clip = ImageClip(img).with_duration(t1)
            if mix_mode != True :
                clip = CrossFadeIn(1).apply(clip)
                clip = CrossFadeOut(1).apply(clip)            
            clips.append(clip)

        # 创建图像剪辑列表
        #clips = [ImageClip(img).with_duration(t1) for img in resized_files]

        # 合并所有剪辑
        final_video = concatenate_videoclips(clips, method="compose")
        

        # 输出最终视频
        final_video.write_videofile(output_file, fps=24, codec="libx264")
        print(f"视频已成功生成：{output_file}")

        # 清理临时文件
        for temp_file in resized_files:
            os.remove(temp_file)
        os.rmdir(temp_dir)

    except Exception as e:
        print(f"处理图片时出错: {e}")

def create_audio_from_mp3s(first_audio, directory, t2, output_file):
    """
    从指定目录中的 .mp3 文件以随机顺序连接成一个总时长为 t2 的 .mp3 文件。

    :param directory: str, 包含 .mp3 文件的目录路径
    :param t2: int, 输出音频的总时长（秒）
    :param output_file: str, 输出音频文件路径
    """
    try:
        # 获取目录中的所有 .mp3 文件
        #audio_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.mp3')]
        audio_files = [os.path.join(directory, f) for f in os.listdir(directory) if (f.endswith('.m4a') or f.endswith('.mp3')) ]
     
        if not audio_files:
            print(f"目录 {directory} 中没有找到任何 .mp3 or m4a 文件！")
            return

        # 打乱音频文件的顺序
        random.shuffle(audio_files)
        if first_audio != None:
            audio_files.insert(0,first_audio)

        # 加载音频剪辑并计算总时长
        clips = []
        total_duration = 0

        while total_duration < t2:
            for audio_file in audio_files:
                clip = AudioFileClip(audio_file)
                clip_duration = clip.duration

                clip = AudioFadeOut(5).apply(clip)  # fade out
                clip = AudioFadeIn(2).apply(clip)  # fade out

                print(format_seconds_to_hms(total_duration) + " " + os.path.basename(audio_file.strip()) )

                # 如果当前片段加入后总时长超过目标，裁剪至剩余时间
                if total_duration + clip_duration > t2:
                    total_duration += clip_duration
                    clips.append(clip)
                    break

                clips.append(clip)
                total_duration += clip_duration

                # 如果已达到目标时长，停止选择
                if total_duration >= t2:
                    break

        # 合并所有音频剪辑
        final_audio = concatenate_audioclips(clips)
        final_audio = AudioNormalize().apply(final_audio)

        # 输出最终音频
        final_audio.write_audiofile(output_file, codec="libmp3lame")
        print(f"音频已成功生成：{output_file}")

    except Exception as e:
        print(f"处理音频时出错: {e}")


#-------------產生倒數計時影片，影片背景為綠色，倒數結束時 00:00 閃爍。----------------------------------------------
def create_countdown_video(minutes, seconds,font,fontsize, color, position, output_file="countdown.mp4"):
    """
    產生倒數計時影片，影片背景為綠色，倒數結束時 00:00 閃爍。
    """
    total_seconds = minutes * 60 + seconds
    resolution = (300, 100)
    bg_color = (0, 255, 0)  # 綠底

    flash_counter = 300

    # 背景 clip
    background = ColorClip(size=resolution, color=bg_color, duration=total_seconds + flash_counter)

    # 每秒更新倒數時間的 TextClip
    def make_frame(t):
        if t < total_seconds:
            remaining = int(total_seconds - t)
            mm = remaining // 60
            ss = remaining % 60
            time_text = f"{mm:02}:{ss:02}"
        else:
            # 倒數結束後閃爍 (每秒出現/消失)
            flash_on = int(t) % 2 == 0
            time_text = "00:00" if flash_on else ""

        #time_text = time_text + ' 請保持專注！'
        txt_clip = TextClip(
            text=time_text,
            font_size=fontsize,
            font= font,
            bg_color=bg_color,
            color=color,
            margin=position
        ).with_duration(1) #.with_position(position)
        return txt_clip.get_frame(0)

    # 建立 VideoClip 物件
    countdown = VideoClip(make_frame, duration=total_seconds + flash_counter)

    # 合成背景與倒數計時
    final = CompositeVideoClip([background, countdown])

    # 輸出影片
    final.write_videofile(output_file, fps=24, codec="libx264", audio=False)



#--------------------------------------------------------------------------------------------------

#configuration -------------------


# function = 1 製作長背景音樂 (from .mp3)
BGM_length = 12         # 背景音樂長度 / 單位：分鐘
BGM_output_filename = "emotion.mp3"

# function = 2 製作長背景影片 (from .mp4)
A_roll_MP4_length = 12    # A-roll (由MP4組成) 長度 / 單位：分鐘
A_roll_MP4_dir = "Money"   # mp4目錄名稱

# function = 3 製作長背景影片 (from .jpg)
A_roll_JPG_length = 2         # A-roll (由JPG組成) 長度 / 單位：分鐘
Each_JPG_Length = 30          # 每張JPG顯示多久時間   / 單位：秒
zoom_scale = 1.8
A_roll_JPG_dir = "法醫"       # .jpg 目錄名稱
mix_mode = False                 # mix-mode = True : 橫圖/豎圖交雜，則不能做fade in/out



# function = 4  背景圖轉檔 (.webp --> .jpg)
total_webp_photo_no = 0     # 共有幾張圖(.webp)   e.g. 10 means 0-9
total_png_photo_no = 30   # 共有幾張圖(.png)   e.g. 10 means 0-9
#photo_dir = "./bg_image/bg113"    #"./主題圖片/trump" #"./bg_image/bg89" 



# function 5 generate_videos_from_txt_and_mp3   : test sample

# function 6, generate_videos_from_txt_and_mp3 , 產生影片 5+ 1+2 ( or +3)
book_ID = '112'
clip_number = 2    # 總共分為幾段 （e.g. clip_number=3 => B77-1, B77-2, B77-3)
string_align = 'left'  # default 'center': 靠中偏右;    'left': 對齊左邊邊框


#configuration -------------------
function = 4


# function = 1 製作長背景音樂 (from .mp3)
if function == 1:
    create_audio_from_mp3s(None ,"./bg_mp3", BGM_length*60, BGM_output_filename)

# function = 2 製作長背景影片 (from .mp4)
if function == 2:
    create_random_video_from_directory("./主題影片/"+A_roll_MP4_dir, 60*A_roll_MP4_length, A_roll_MP4_dir+".mp4")

# function = 3 製作長背景影片 (from .jpg)
if function == 3:
    zoom_scale = 1.5
    create_video_from_images_with_ZOOMING("./主題圖片/"+A_roll_JPG_dir, zoom_scale, Each_JPG_Length, 60*A_roll_JPG_length, A_roll_JPG_dir+"2.mp4")
    #create_video_from_images(mix_mode, "./主題圖片/"+A_roll_JPG_dir, Each_JPG_Length, 60*A_roll_JPG_length, A_roll_JPG_dir+"2.mp4")

# function = 4  背景圖轉檔
if function == 4:
    total_png_photo_no = 70   # 共有幾張圖(.png)   e.g. 10 means 0-9
    photo_dir = "./bg_image/bg124"    #"./主題圖片/trump" #"./bg_image/bg89" 

    for i in range(0,total_webp_photo_no):   # range(0:10) <== 0~9
        image_filename = os.path.join(photo_dir, f"{i}.webp")
        convert_webp_to_jpg_with_resolution(image_filename,(1920, 1080))

    for i in range(0,total_png_photo_no):   # range(0:10) <== 0~9
        image_filename = os.path.join(photo_dir, f"{i}.png")
        convert_png_to_jpg_with_resolution(image_filename,(1920, 1080))

# function = 5 使用示例
if function == 5:
    generate_videos_from_txt_and_mp3("./腳本/txt95-1", "./腳本/voice95-1",  "./bg_image/bg95","./output.mp4",0,0)

# function = 6  產生含字幕影片 5 + 1+2 (+3)
if function == 6:

    book_ID = '115'
    clip_number = 2    # 總共分為幾段 （e.g. clip_number=3 => B77-1, B77-2, B77-3)
    string_align = 'left'  # default 'center': 靠中偏右;    'left': 對齊左邊邊框

    Each_JPG_Length = 14            #30 # 每張JPG顯示多久時間   / 單位：秒
    A_roll_JPG_dir = "running"       # .jpg 目錄名稱
    zoom_scale = 1.3                #1.5
    #mix_mode = True                 # mix-mode = True : 橫圖/豎圖交雜，則不能做fade in/out


    A_roll_MP4_dir = 'Money'

    
    topic_num1, video_length1 = \
        generate_videos_from_txt_and_mp3("./腳本/txt"+book_ID+"-1", "./腳本/voice"+book_ID+"-1", "./bg_image/bg"+book_ID,"./output1.mp4",0,0, \
                                         bg_type=1)        #4th parameter: start time (in sec.);   bg_type=0 topic背景靜態照片 (==1, topic是動畫)

    topic_num2, video_length2 = \
        generate_videos_from_txt_and_mp3("./腳本/txt"+book_ID+"-2", "./腳本/voice"+book_ID+"-2", "./bg_image/bg"+book_ID, "./output2.mp4", \
                                    video_length1,topic_num1, bg_type=1)
    video_length3=video_length2
    if clip_number == 3:
        topic_num3, video_length3 = \
            generate_videos_from_txt_and_mp3("./腳本/txt"+book_ID+"-3", "./腳本/voice"+book_ID+"-3", "./bg_image/bg"+book_ID, "./output3.mp4", \
                                    video_length2,topic_num1+topic_num2,bg_type=1) 

    create_audio_from_mp3s(None, "./bg_mp3", video_length3, "output" + book_ID + ".mp3")

    # 設定 - A_roll_MP4_dir (function-2)
    create_random_video_from_directory("./主題影片/"+A_roll_MP4_dir, video_length3, A_roll_MP4_dir+".mp4")
    

    create_video_from_images_with_ZOOMING("./主題圖片/"+A_roll_JPG_dir, zoom_scale, Each_JPG_Length, video_length3, A_roll_JPG_dir+"2.mp4")
    #create_video_from_images(mix_mode, "./主題圖片/"+A_roll_JPG_dir, Each_JPG_Length, video_length3, A_roll_JPG_dir+"2.mp4")
    
    
    

# function = 7  產生音樂影片 1+2 (+3)
if function == 7:
    First_audio_filename = "./bg_mp3/原始音量/Echoes In The Drizzle.mp3"
    music_program_length = 30  # unit : minutes
    A_roll_JPG_dir = "黑膠播放"
    A_roll_MP4_dir = "cafe"
    Each_JPG_Length = 20

    # function-1 : music clip generation
    create_audio_from_mp3s(First_audio_filename,"./bg_mp3/原始音量", music_program_length*60, "output.mp3")

    # 設定 - A_roll_MP4_dir (function-2)
    create_random_video_from_directory("./主題影片/"+A_roll_MP4_dir, music_program_length*60, A_roll_MP4_dir+".mp4")

    # function-3
    #create_video_from_images(mix_mode, "./主題圖片/"+A_roll_JPG_dir, Each_JPG_Length, music_program_length*60, A_roll_JPG_dir+"2.mp4")

    '''
    create_countdown_video(
        minutes=music_program_length*2,
        seconds=0,
        font='TaipeiSansTCBeta-Bold.ttf',
        fontsize=100,
        color= (216,191,216), #蓟紫 #(255, 77,64), #  柿子橙
        #(255,191,0),琥珀色,   #(139,0,255),#紫羅蘭  #(0,71,125), #水手藍  #(222,49,99),  #樱桃红  #(250,128,114),    #(46, 139,87) , #"yellow",
        position=(10, 10),
        output_file="countdown.mp4"
    )
    '''
    
    




    

    

