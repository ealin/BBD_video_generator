import os
from moviepy import *
from moviepy.video import *
from moviepy.audio import *
from moviepy.audio.AudioClip import AudioClip

import random
#from moviepy.video import VideoFileClip, concatenate_videoclips

from PIL import Image


def resize_image(input_file, output_file, resolution):
    """
    将指定的图像文件转换为指定解析度。

    :param input_file: str, 输入图像文件路径
    :param output_file: str, 输出图像文件路径
    :param resolution: tuple, 目标分辨率 (宽度, 高度)
    """
    try:
        # 打开输入图像文件
        with Image.open(input_file) as img:
            # 调整图像大小
            resized_img = img.resize(resolution, Image.LANCZOS)
            # 保存为输出文件
            resized_img.save(output_file)
            print(f"图像已成功转换为解析度 {resolution} 并保存为 {output_file}")
    except Exception as e:
        print(f"处理图像时出错: {e}")

def convert_webp_to_jpeg_with_resolution(input_file, resolution):
    """
    将指定的 .webp 文件转换为指定解析度，并保存为同名的 .jpeg 文件。

    :param input_file: str, 输入 .webp 文件路径
    :param resolution: tuple, 目标分辨率 (宽度, 高度)
    """
    try:
        # 获取输出文件名，将扩展名改为 .jpeg
        output_file = input_file.rsplit('.', 1)[0] + ".jpeg"

        # 打开 .webp 文件
        with Image.open(input_file) as img:
            # 调整图像大小
            resized_img = img.resize(resolution, Image.LANCZOS)
            # 转换为 RGB 模式（JPEG 不支持透明度）
            rgb_img = resized_img.convert("RGB")
            # 保存为 .jpeg 文件
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
    

def generate_videos_from_txt_and_mp3(txt_dir, voice_dir, bg_img_dir, output_file, start_second, topic_index):
    """
    从指定目录中的 .txt 文件和对应的 .mp3 文件生成视频。
    视频背景为全绿，字幕为 .txt 文件内容，音频为 .mp3 文件内容。

    :param txt_dir: str, .txt 文件所在目录
    :param voice_dir: str, .mp3 文件所在目录
    :param output_file: str, 输出视频檔案
    topic_index = 0         開始處理的是第幾個topic  (根據此變數決定要抓哪張圖), start from 0.jpg

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
    topic_image_page_no = 3

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
                if topic_image_index != -1 and topic_image_index < topic_image_page_no :
                    
                    text_clip = TextClip(
                                text= subtitle_text,   #'\n'+subtitle_text+'\n',
                                font_size=txt_font_size,  # 字体大小
                                color=font_color,                    # can use RGB as a color
                                bg_color=(0,71,125),  #水水藍
                                stroke_color=font_strok_color,
                                stroke_width=font_strok_width,
                                text_align='center', 
                                font=font_ttf,
                                interline=15, 
                            ).with_position("center") #.with_duration(duration)
                    

                    im_width, im_height = text_clip.size
                    color_clip_ = ColorClip(size=(int(im_width*1.1), int(im_height*1.1)),color=(0,71,125))  #水手藍
                    #color_clip_ = color_clip_.with_opacity(.6)    
                    text_clip = CompositeVideoClip([color_clip_, text_clip]).with_position('center')

                    #text_clip.save_frame("out.png")

                else:

                    # 創建字幕的文字片段 (需分別一般段落或title 判斷：>>>>)
                    text_clip = TextClip(
                        text=subtitle_text,
                        font_size=txt_font_size,
                        color=font_color,                    # can use RGB as a color
                        bg_color=background_color,           # (0, 255, 0),
                        stroke_color=font_strok_color,
                        stroke_width=font_strok_width,
                        margin=(200,450),               # 控制字串的左上角位置
                        method='caption',
                        size=(1920,None),
                        text_align='center',      #'left',   
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
                image_filename = os.path.join(bg_img_dir, f"{topic_index-1}.jpeg")

                print(image_filename)
                try:
                    bg_clip = ImageClip(image_filename) #.resized(width=1920, height=1080)

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
                video_clip = CompositeVideoClip([bg_clip]).with_duration(duration).with_audio(audio_clip)
            elif starts_with_pattern(subtitle_text, '@@@@'): #subtitle_text == '@@@@' :
                # 黑屏延續一段時間 / 換場
                video_clip = ColorClip(size=(1920, 1080), color=pending_color, duration=pending_duration)
            else:
                if with_topic_flag == True and topic_text != '>>>>' :
                     # 合成背景、字幕、topic和音频
                    video_clip = CompositeVideoClip([bg_clip, text_clip, topic_clip]).with_duration(duration).with_audio(audio_clip)
                else:
                    # 合成背景、字幕和音频
                    video_clip = CompositeVideoClip([bg_clip, text_clip]).with_duration(duration).with_audio(audio_clip)
            
            acc_second = acc_second + duration

            # 输出视频
            #video_clip.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")
            #print(f"生成视频：{output_path}")
            clips.append(video_clip)
 
            if starts_with_pattern(subtitle_text, pattern_ending): 
                with_topic_flag = False

    print("打印 Topic 数组中的所有元素:")
    for topic in topic_array:
        print(f"{topic.time} {topic.line}")
    print("輸出視頻長度：")
    print(acc_second)

    # 合併所有片段
    final_clip = concatenate_videoclips(clips, method="compose")
    final_clip.write_videofile(output_file, fps=24, codec='libx264', audio_codec='aac')


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

def create_video_from_images(directory, t1, t2, output_file):
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
            resize_image(img_file, resized_path)
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

        # 创建图像剪辑列表
        clips = [ImageClip(img).with_duration(t1) for img in resized_files]

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

def create_audio_from_mp3s(directory, t2, output_file):
    """
    从指定目录中的 .mp3 文件以随机顺序连接成一个总时长为 t2 的 .mp3 文件。

    :param directory: str, 包含 .mp3 文件的目录路径
    :param t2: int, 输出音频的总时长（秒）
    :param output_file: str, 输出音频文件路径
    """
    try:
        # 获取目录中的所有 .mp3 文件
        audio_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.mp3')]

        if not audio_files:
            print(f"目录 {directory} 中没有找到任何 .mp3 文件！")
            return

        # 打乱音频文件的顺序
        random.shuffle(audio_files)

        # 加载音频剪辑并计算总时长
        clips = []
        total_duration = 0

        while total_duration < t2:
            for audio_file in audio_files:
                clip = AudioFileClip(audio_file)
                clip_duration = clip.duration

                print("Add audio file: " + audio_file)

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

        # 输出最终音频
        final_audio.write_audiofile(output_file, codec="libmp3lame")
        print(f"音频已成功生成：{output_file}")

    except Exception as e:
        print(f"处理音频时出错: {e}")



#--------------------------------------------------------------------------------------------------

# 製作長背景音樂 (from .mp3)
#create_audio_from_mp3s("./bg_mp3", 20*60, "2030.mp3")


# 製作長背景影片 (from .mp4)
create_random_video_from_directory("./主題影片/2030預言", 60*20, "2030.mp4")

# 製作長背景影片 (from .jpeg)
#create_video_from_images("./主題圖片/紫金山彗星", 2, 60, "output.mp4")


# step1:  背景圖轉檔
'''
for i in range(0,13):   # range(1:10) <== 1~9
    image_filename = os.path.join('./bg_image/B72', f"{i}.webp")
    convert_webp_to_jpeg_with_resolution(image_filename,(1920, 1080))
'''


# 使用示例
#generate_videos_from_txt_and_mp3("./腳本/txt", "./腳本/voice",  "./bg_image/B69","./output.mp4",0,0)

# step2: 產生影片-1
#generate_videos_from_txt_and_mp3("./腳本/txt72-1", "./腳本/voice72-1", "./bg_image/B72","./output1.mp4",0,0)  #4th parameter: start time (in second)

# step3: 產生影片-2
#generate_videos_from_txt_and_mp3("./腳本/txt72-2", "./腳本/voice72-2", "./bg_image/B72", "./output2.mp4",495,5) # 最後一個參數：從第幾個topic開始, start from 0.jpg

# step4: 產生影片-3
#generate_videos_from_txt_and_mp3("./腳本/txt72-3", "./腳本/voice72-3", "./bg_image/B72", "./output3.mp4",971,10) # 最後一個參數：從第幾個topic開始, start from 0.jpg


