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
    #image_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.png')]
    image_files = [os.path.join(directory, f) for f in os.listdir(directory) if (f.endswith('.png') or f.endswith('.jpeg') or f.endswith('.jpg')) ]
 
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
        first_frame_duration = 1.5
        if frame_num == 0 :
            open_frame_clip = ImageClip(resized_files[0]).with_duration(first_frame_duration)
            clips.append(open_frame_clip)

        # create chinese-text clip
        txt_font_size = 64
        font_strok_color='black'
        font_strok_width=2
        string_left = 40
        string_top = 500+120
        string_method='label'
        string_size=(None,None)
        string_text_align = 'left'
        font_ttf = 'TaipeiSansTCBeta-Regular.ttf'

        font_color_Lavender = (230,230,250) #薰衣草紫
        font_color_LightSkyBlue = (135,206,250)
        font_color_White = 'white'
        font_color_default= (255,255,153) #香檳黃

        text_clip = TextClip(
            text=chn_strings[frame_num],
            font_size=txt_font_size+8,
            color=font_color_Lavender,                    # can use RGB as a color
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
            color= font_color_default ,     
            bg_color=(0, 255, 0),           # (0, 255, 0),
            stroke_color=font_strok_color,
            stroke_width=font_strok_width,
            margin=(string_left,string_top+450),               # 控制字串的左上角位置
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
A_roll_IMG_dir = "b113_short_bg014"
A_roll_MP3_dir = "./bg_mp3/short/50S"
JPG_number = 7                      # 1.jpg, 2.jpg ... 6.jpg (png OK also)
zoom_scale = 1.4

Each_JPG_Length = 7               # sec. 

chn_strings1 = [ \
"拒絕的權力 \n《《《 自由的價格", \
"他靜靜望著湖面，\n思考自由的形狀。", \
"他撿起一顆石子，\n開始為自己儲備底氣。", \
"那隻小皮袋鼓起時，\n他心裡變得踏實。", \
"風起時，別的翅膀亂了方向，\n他仍選擇不動。", \
"他緊咬皮袋，\n對風說出了第一個『不』。", \
"風停了，湖面重歸平靜，\n他知道自己再也不怕了。", \
]

eng_strings1 = [ \
"The Power to Say No \n《《《 The Price of Freedom", \
"He quietly gazed at the lake,\ncontemplating the shape of freedom.", \
"He picked up a pebble,\nstarting to prepare his \nown confidence.", \
"As the little pouch swelled,\nhis heart grew steady.", \
"When the wind rose, \nothers lost direction,\nhe chose stillness.", \
"He clenched the pouch \nand finally said 'no' \nto the storm.", \
"The wind calmed,\nthe lake was still,\nand fear was gone.", \
]

chn_strings2 = [ \
"小港口的節流者 \n《《《 高儲蓄率的槓桿力", \
"他靜靜望著潮退的海灘，\n思考那些被浪帶走\n又留下的東西。", \
"他彎身撿起第一枚貝殼，\n自由的旅程開始了。", \
"他每天多撿一點，\n慢慢堆出了安穩的形狀。", \
"暴風來襲，他緊緊守著那\n一小堆屬於自己的安穩。", \
"他檢視留下的貝殼，\n發現每一枚都閃著堅持的光。", \
"他笑了，因為省下的，\n不只是貝殼，\n而是選擇的自由。", \
]

eng_strings2 = [ \
"The Saver of the Small Harbor \n《《《 The Power of High Savings", \
"He quietly watched the receding tide, \npondering what the waves\ntook and left behind.", \
"He bent down to pick up the \nfirst shell, and the journey to \nfreedom began.", \
"Each day he gathered a little more, \nslowly shaping hisstability.", \
"When the storm came, he held tightly \nto his small mound of peace.", \
"He examined the remaining shells,\neach glowing with persistence.", \
"He smiled, for what he had saved\nwas not just shells but choices.", \
]
 
chn_strings3 = [ \
"靜水的投資者 \n《《《 指數投資", \
"他坐在霧中的河邊，\n讓光與靜默告訴他何處開始。", \
"他投下第一顆石子，\n讓時間起波紋。", \
"他每天重複相同的動作，\n讓時間築起他的堤岸。", \
"雨勢再大，他也不離開，\n相信洪水終會退去。", \
"陽光再映水面，他微笑，\n因為一切依然存在。", \
"多年以後，\n他坐在自己築起的壩上，\n看著時間的金光閃爍。", \
]

eng_strings3 = [ \
"The Patient Investor \n《《《 Index Investing", \
"He sat by the foggy river,\nletting light and silence show\nhim where to begin.", \
"He dropped the first pebble,\nletting time ripple outward.", \
"Each day he repeated the sameact, \nletting time build his quiet dam.", \
"No matter how hard the rain fell,\nhe stayed, \nbelieving the floodwould pass.", \
"When sunlight returned, \nhe smiled, \neverything still stood.", \
"Years later, \nhe sat on the dam he built, \nwatching time shimmer in gold.", \
]

chn_strings4 = [ \
"雪原下的紀律 \n《《《 下跌時的冷靜紀律", \
"他嗅到暴風的氣味，\n卻依然平靜。", \
"雪落得越急，\n他越能看清自己的方向。", \
"在最白的風裡，\n他聽見自己心跳的節奏。", \
"他選擇不動，\n因為有時等待就是行動。", \
"黎明的光刺進雪裡，\n他重新上路。", \
"風停了，\n他昂首看見前方依然是路。", \
]

eng_strings4 = [ \
"Discipline Beneath the Snow \n 《《《Calm Discipline in a Downturn", \
"He sensed the storm’s scent,\nyet stayed calm.", \
"The harder the snow fell, \nthe clearer his direction became.", \
"In the whitest storm, he heard\nthe rhythm of his heartbeat.", \
"He chose stillness, \nfor sometimes waiting is \nthe truest action.", \
"The light of dawn pierced the snow, \nand he walked again.", \
"The wind ceased, \nhe lifted his head \n— the road still ahead.", \
]

chn_strings5 = [ \
"自轉的羊駝 \n《《《 自動化理財系統", \
"他望著溪水，\n明白力量不必來自自己。", \
"每一根木頭與石塊，\n都是未來的齒輪。", \
"水輪動了，\n他的世界也跟著動了。", \
"當機械自轉時，\n他終於能靜靜地閱讀。", \
"他微笑著，\n看著自然與自己一起運轉。", \
"星光下，輪仍在轉，\n他知道明天也會如此。", \
]

eng_strings5 = [ \
"The Self-Running Alpaca \n《《《 Automated Finance System", \
"He watched the stream and\nrealized power need not come\nfrom himself.", \
"Each plank and stone was a\ngear he placed for the future.", \
"The wheel turned, and with it\nhis world began to move.", \
"As the machine turned on itsown,\nhe could finally read \nin peace.", \
"He smiled, \nwatching nature move\nin harmony with him.", \
"Beneath the starlight, \nthe wheel kept turning \n— and tomorrow would too.", \
]

chn_strings6 = [ \
"卸下石袋的黑鼻羊 \n《《《 債務的枷鎖與解放", \
"他背著滿袋石頭跋涉多年，\n每一步都沉重。", \
"他放下一顆，又一顆，\n腳步漸輕。", \
"最後一顆滾落谷底，\n他抬頭看著遠山。", \
"自由不是抵達山頂，\n而是能輕盈地走回自己。", \
"陽光灑在他身上，\n風輕撫他的毛，\n那是解放的氣息。", \
"他終於懂了，\n自由的重量，\n其實是放下的輕。", \
]

eng_strings6 = [ \
"The Sheep Who Laid Down Its Stones \n《《《 Debt and Liberation", \
"He carried a sack of stones for years, \neach step heavy with burden.", \
"He set one down, \nthen another,\nhis pace grew lighter.", \
"When the last stone fell \ninto the valley, \nhe looked up at the distant peaks.", \
"Freedom wasn’t reaching the summit,\n but walking lightly back to himself.", \
"Sunlight warmed his wool, \nthe wind brushed softly \n— release at last.", \
"He understood — \nthe weight of freedom is \nthe lightness of\nletting go.", \
]


chn_strings9 = [ \
"竹林的紀律 \n《《《 簡化與紀律投資", \
"清晨霧起，\n小熊貓靜坐在竹林深處。", \
"他曾試著擁有更多竹子，\n卻發現越多越亂。", \
"他決定只取所需，\n每天固定時間採集。", \
"風雨來時，\n別的動物逃散，他仍穩坐。", \
"季節更替，\n他的竹林愈加茂盛。", \
"他明白，真正的富足，\n來自堅持與簡化。", \
]

eng_strings9 = [ \
"Discipline in the Bamboo Forest \n《《《 Simplicity and Discipline\n《《《 in Investing", \
"At dawn, the red panda sat \nquietly within the bamboo forest.", \
"He once tried to gather more bamboo, \nbut the more he had, \nthe more chaotic it became.", \
"He decided to take only\n what he needed, \ngathering at the same hour each day.", \
"When the storm came, others ran — \nhe stayed still.", \
"As seasons changed, \nhis bamboo grove flourished.", \
"He realized true wealth comes from \ndiscipline and simplicity.", \
]

chn_strings = [ \
"雪野的自由 \n《《《 自由與心的平衡", \
"黎明時分，\n白狐在雪原上奔跑，\n追逐風的方向。", \
"他跑了很久，\n直到氣息在寒氣中化成霧。", \
"他停下腳步，\n聽見雪的聲音。", \
"那一刻，\n他懂得自由不是奔跑。", \
"他躺下，\n任風穿過他的毛尖。", \
"陽光升起，\n雪光閃爍，牠微笑了。", \
]

eng_strings = [ \
"Freedom of the Snowfields \n《《《 Freedom and Balance", \
"At dawn, the white fox \nran across the snowfield, \nchasing the direction of the wind.", \
"He ran for so long that his breath \nturned to mist in the cold air.", \
"He stopped and heard the sound \nof snow beneath his paws.", \
"In that moment, he understood — \nfreedom wasn’t in running.", \
"He lay down, \nletting the wind pass through his fur.", \
"The sun rose, \nthe snow shimmered — he smiled.", \
]



#"冥想練習讓我們更清醒與仁慈".  // <== 中文一行長度參考
#"Breath quality drives your energy."  // <==. 英文一行長度參考




create_video_from_images_with_ZOOMING("./bg_image/"+A_roll_IMG_dir, zoom_scale, Each_JPG_Length, Each_JPG_Length*JPG_number, \
                                      chn_strings, eng_strings, \
                                      A_roll_MP3_dir, \
                                      A_roll_IMG_dir+".mp4")
