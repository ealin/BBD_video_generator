import os
from moviepy import *
from moviepy.video import *
from moviepy.audio import *


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


def generate_videos_from_txt_and_mp3(txt_dir, voice_dir, output_file, start_second):
    """
    从指定目录中的 .txt 文件和对应的 .mp3 文件生成视频。
    视频背景为全绿，字幕为 .txt 文件内容，音频为 .mp3 文件内容。

    :param txt_dir: str, .txt 文件所在目录
    :param voice_dir: str, .mp3 文件所在目录
    :param output_file: str, 输出视频檔案
    """
    # 确保输出目录存在
    #os.makedirs(output_dir, exist_ok=True)

    #--------------------------------------------------
    # configuration
    background_color = (0, 255, 0)  # 綠色背景
    font_ttf = 'TaipeiSansTCBeta-Regular.ttf'  #'BpmfGenSenRounded-R.ttf'  #'Annotated.ttf' (<- 注音)
    font_color= (255,255,153) #香檳黃 #'white' #yellow'
    font_strok_color='black'
    font_strok_width=2
    txt_font_size = 52
    topic_font_color='white'
    topic_font_strok_color='black'
    topic_font_strok_width=2
    topic_txt_font_size = 40
    topic_font_background_color = (222, 49,99) #櫻桃紅  #(255,128,153)  #浅鲑红  #'red'
    topic_font_ttf = 'TaipeiSansTCBeta-Bold.ttf'  #'Annotated.ttf'  #'BpmfGenSenRounded-EL.ttf'  
    max_line = 0    # 0 means no limited

    pattern_ending = ">>>>結論"
   
    pattern_new_line = '<'
    pattern_topic = '>>>>'
    pattern_no_show = '!!!!' 

    # configuration
    #--------------------------------------------------
 
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
                    text="隱形",
                    font_size=txt_font_size,color=background_color, bg_color=background_color,stroke_color=background_color,stroke_width=1,
                    margin=(20,500), method='caption', size=(1900,None),text_align='center', interline=30, font=font_ttf)
            
            else:               
                # 創建字幕的文字片段 (需分別一般段落或title 判斷：>>>>> )
                text_clip = TextClip(
                    text=subtitle_text,
                    font_size=txt_font_size,
                    color=font_color,                    # can use RGB as a color
                    bg_color=background_color,           # (0, 255, 0),
                    stroke_color=font_strok_color,
                    stroke_width=font_strok_width,
                    margin=(20,500),               # 控制字串的左上角位置
                    method='caption',
                    size=(1900,None),
                    text_align='center',      #'left',   
                    interline=30,                   # 行距
                    #horizontal_align='left',
                    font=font_ttf)

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


            # 創建背景顏色
            bg_clip = ColorClip(size=(1920, 1080), color=background_color, duration=duration)
            #bg_clip = ColorClip(size=(1920, 1080), is_mask=True, color=0, duration=duration) 

            # '!!!!' 不產生字幕
            if starts_with_pattern(subtitle_text, pattern_no_show):  # topic
                # 合成背景、字幕和音频
                video_clip = CompositeVideoClip([bg_clip]).with_duration(duration).with_audio(audio_clip)
            else:
                if with_topic_flag == True:
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


# 使用示例
#generate_videos_from_txt_and_mp3("./txt67", "./voice67", "./video")
#generate_videos_from_txt_and_mp3("./txt67-1", "./voice67-1", "./output1.mp4",0)  #final parameter: start time (in second)
generate_videos_from_txt_and_mp3("./txt67-2", "./voice67-2", "./output2.mp4",420)
