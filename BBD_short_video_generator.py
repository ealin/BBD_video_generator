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

# uploaded to gitHub  


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

        # 一開始插入一張沒有字幕的圖. (前面五秒和動畫重疊)
        first_frame_duration = 5
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
            font_size=txt_font_size, #+4,
            color=font_color_Lavender,                    # can use RGB as a color
            bg_color=(0, 255, 0),           # (0, 255, 0),
            stroke_color=font_strok_color,
            stroke_width=font_strok_width,
            margin=(string_left,40), #string_top),               # 控制字串的左上角位置
            method=string_method,
            size=string_size,
            text_align=string_text_align,   
            interline=30,                   # 行距
            font=font_ttf,
            transparent=True)
        text_clip = MaskColor(color=(0,255,1),threshold=20, stiffness=3).apply(text_clip) 


        text_clip2 = TextClip(
            text=eng_strings[frame_num],
            font_size=txt_font_size-12,
            color= font_color_default ,     
            bg_color=(0, 255, 0),           # (0, 255, 0),
            stroke_color=font_strok_color,
            stroke_width=font_strok_width,
            margin=(string_left,string_top+600),               # 控制字串的左上角位置
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
A_roll_IMG_dir = "b115_short_bg001"
A_roll_MP3_dir = "./bg_mp3/short/50S"
JPG_number = 7                      # 1.jpg, 2.jpg ... 6.jpg (png OK also)
zoom_scale = 1.4

Each_JPG_Length = 6               # sec. 

chn_strings = [ \
"讓耳朵清楚聽見自己的願望清單\n《《《 思想變現與小行動", \
"耳廓狐阿晞在熙攘的\n共享辦公室裡，被各種『成功學』\n聲音吵得心煩。", \
"他決定只選一個願望，\n在筆記本上寫下那句 :「一年後，\n我想換到更適合自己的工作」。", \
"每晚，他把耳朵從外界雜音\n收回，只聽見自己寫下的\n那一行小行動。", \
"那天，他更新履歷；\n隔天，研究感興趣的產業；\n第三天，練習自我介紹。", \
"因為主動幫忙解決\n一個簡單的電腦問題，\n他被隔壁桌的人注意到。", \
"那一刻他發現，願望不是突然\n掉下來的，而是每天小小的行動，\n悄悄換掉了他的現實。", \
]

eng_strings = [ \
"The Wish List Heard by Ears\n《《《 Turning thoughts into action", \
"In the crowded co-working space,\nAshi the fennec fox was overwhelmed by\n all the noisy 'success' voices around him.", \
"Ashi decided to choose just one wish,\nand wrote in his notebook that a year\n from now he wanted a job that truly\n fit him.", \
"Each night,he drew his ears back from\n the outside noise and listened only to\n that single line of small action\n he had written.", \
"That day he updated his résumé,\nthe next he researched the industries\n he liked,and on the third day he practiced\n introducing himself.", \
"By stepping in to fix a simple computer\n problemn, he caught the attention of\n the person at the next table.", \
"In that moment Ashi realized that wishes\n don’t just fall from the sky,\nthose tiny daily answers had quietly\n rewritten his reality.", \
]


chn_strings2 = [ \
"龍貓的願景房間\n《《《 從幻想退回現實", \
"森林精靈龍貓住進城市邊緣的\n一間小套房，\n牆上貼滿五顏六色的願景板。", \
"他每天點著香氛蠟燭，\n對著圖像輕聲說：\n『宇宙，請實現我的許願。』", \
"帳單堆在門口，\n冰箱裡只剩下一顆皺巴巴的蘋果，\n現實與牆上的夢越拉越遠。", \
"某天，下雨漏水，\n牆上一角的願景板\n被泡得捲起來。", \
"龍貓終於拿下那張紙，\n走出門去找屋頂修繕公司。", \
"他留下少數最重要的願望，\n其餘的改成『本月行動清單』，\n房間變空了，心卻踏實了。", \
]

eng_strings2 = [ \
"The Dream Room of the Forest Spirit\n《《《 Stepping back from fantasy", \
"The forest creature moved into a tiny\n apartment on the edge of the city,\ncovering the walls with\n colorful vision boards.", \
"Every day he lit scented candles,\nwhispering to the images, asking\n the universe to make them real.", \
"Bills piled up by the door,\nand only a shriveled apple remained\n in the fridge,while reality drifted\n farther from the dreams on the wall.", \
"One rainy day the ceiling started\n to leak, soaking a corner of the\n vision board until it curled and sagged.", \
"At last he tore the poster from\n the wall,and stepped out the door to\n look for someone to fix the roof.", \
"He kept only a few important dreams,\nturned the rest into a monthly action\n list,and though the room grew emptier,\nhis heart felt steadier.", \
]


chn_strings3 = [ \
"海獺與便利商店的巧合\n《《《 小願望與自我預言", \
"海獺小湊每天經過\n港口旁的便利商店，\n都會順手買一本雜誌。", \
"某晚，他在未來日記裡寫下：\n『幾年後，我出版了一本\n關於海邊生活的小書。』", \
"於是，他開始在社群分享\n自己每天撿到的貝殼故事。", \
"幾個月後，他發現，\n便利商店的雜誌區多了\n一本主題徵稿的小冊子。", \
"於是他投稿了自己的故事，\n被收錄在專欄裡。", \
"那天，他站在便利商店前，\n看到自己的名字印在雜誌一角\n，心想： 原來所謂『巧合』是\n行動後才會長出來的花。", \
]

eng_strings3 = [ \
"Otter and the Convenient Coincidences\n《《《 \nSmall wishes & self-fulfilling prophecy", \
"Every day Kotsu the sea otter passed\n the harbor convenience store,\nand casually picked up a magazine.", \
"One night he wrote in his future diary,\nthat years from now he would publish a\n little book about life by the sea.", \
"So he began sharing the stories of\n the shells he picked up every day\non social media.", \
"Months later he noticed a new themed\n booklet in the store’s magazine section,\nquietly calling for stories.", \
"In the end he submitted his own story,\nand it was chosen for a\n special feature.", \
"That day, standing in front of the\n convenience store,he saw his own name\n on the cover and thought that\n coincidence is a flower that\n blooms only after we act.", \
]


chn_strings4 = [ \
"無尾熊的共享樹屋計畫\n《《《 從佔有到共好", \
"無尾熊露亞一直羨慕山頭上\n那棵最高的樹，心想：\n要是整棵都是我的就好了。", \
"她在日記裡寫著\n「我要成為森林裡最有錢的\n無尾熊」，卻只覺得越寫越焦躁。", \
"她看見一群小動物在\n矮矮的樹下淋雨，\n沒有地方躲，心裡一震。", \
"她開始研究木工，\n詢問鳥兒如何設計樹枝動線，\n請海狸教她加固樹幹。", \
"過程很累，\n但看見朋友們在樹屋裡忙進忙出，\n她的心反而越來越飽滿。", \
"小動物們自發地把水果、\n葉子堆在她門口，\n感謝她的付出。", \
]

eng_string4 = [ \
"The Koala’s Shared Treehouse Plan\n《《《 From owning to growing together", \
"Lua the koala always envied the\n tallest tree on the hill,\nthinking that if only the whole\n thing could belong to her.", \
"She filled her diary with the idea of\n being the richest koala in the forest,\nyet the more she wrote,\nthe more anxious she felt.", \
"She saw a group of little animals huddling\n under a low tree in the rain,\nwith nowhere to hide,\nand her heart jolted.", \
"She began studying carpentry,asking\n the birds about branch routes\nand learning from the beaver how to\n reinforce the trunk.", \
"The work was exhausting,\n yet watching her friends bustling\n around inside the treehouse made her\n heart feel fuller and fuller.", \
"The small animals spontaneously piled\n fruits and leaves at her doorway,\nquietly thanking her for all\n she had done.", \
]


chn_strings5 = [ \
"樹懶的一分鐘階梯\n《《《 微習慣與小改變", \
"樹懶阿嵐最愛躺在吊床上刷影片，\n常看到別人『一年就瘦十公斤』\n『三個月學會三種語言』。", \
"他也曾寫過宏偉的清單，\n但堅持不到三天就放棄。", \
"某天，他在一本書上看到\n『微習慣』的概念，\n決定只做一件荒謬地小的事。", \
"一開始，他仍然很懶，\n只是順手多走幾階，\n多翻一頁。", \
"幾週後，\n他發現自己喘得比較少了，\n故事也越看越有趣。", \
"朋友問他祕訣，他笑著說：\n『我沒有變勤勞，\n只是每天偷懶得比昨天少一點點。』", \
]

eng_strings5 = [ \
"The Sloth’s One-Minute Staircase\n《《《 Micro-habits and gentle change", \
"Alan the sloth loved scrolling videos\n in his hammock,always seeing people \nwho lost weight in a year or\n mastered languages in months.", \
"He had written grand improvement lists\n before,but always gave up before\n even three days had passed.", \
"One day he read about the idea of\n micro-habits,and decided to do\n something ridiculously small each day.", \
"At first he was still lazy,\nmerely taking a few extra steps on\n the stairs and reading just\n one more page.", \
"A few weeks later he noticed he was\n breathing less heavily,and the stories\n were becoming more and more\n interesting.", \
"When his friends asked for his secret,\nhe smiled and said that he hadn’t become\n hardworking, he had just been a tiny bit\n less lazy than yesterday, every day.", \
]


chn_strings6 = [ \
"狐獴的股市瞭望台\n《《《 信念與理性平衡", \
"狐獴墨墨最近迷上吸引力法則，\n在房間貼滿上漲的股價曲線，\n對著圖像冥想一夜致富。", \
"有天，他在網路論壇看到有人\n大喊這檔股票『一定飆』，\n差點把所有積蓄都押上去。", \
"他走到陽台，\n像平常警戒天敵那樣站得高高的，\n深呼吸，看著城市的燈光。", \
"他一邊保留對未來變好的想像，\n一邊打開財報、查公司資訊，\n只拿出一小部分資金試水溫。", \
"那檔股票先漲後跌，\n他雖沒暴富，\n卻也沒有傾家蕩產。", \
"他在這段時間為自己建了一座\n真正看得見風向的 - \n『瞭望台』。", \
]

eng_strings6 = [ \
"The Meerkat’s Market Watchtower\n《《《 Balancing belief and rational risk", \
"Lately the meerkat was obsessed with\n the law of attraction,filling his room\n with rising stock charts and\n meditating on getting rich overnight.", \
"One day he saw people on an online\n forum shouting that a certain stock\n would definitely skyrocket,and he\n almost threw in all his savings.", \
"He walked out onto the balcony,\nstanding tall like he would when watching\n for predators,breathing deeply as he\n looked over the city lights.", \
"So he kept his hope for a better future,\nbut opened the reports,checked the\n company,and used only a small portion\n of his money to test the waters.", \
"The stock first shot up and then\n dropped again,he didn’t become rich,\nbut he also hadn’t lost\n everything.", \
"During this time he built himself a real\n watchtower,from which he could see\n which way the market wind was blowing.", \
]

#"冥想練習讓我們更清醒與仁慈".  // <== 中文一行長度參考
#"Breath quality drives your energy."  // <==. 英文一行長度參考




create_video_from_images_with_ZOOMING("./bg_image/"+A_roll_IMG_dir, zoom_scale, Each_JPG_Length, Each_JPG_Length*JPG_number, \
                                      chn_strings, eng_strings, \
                                      A_roll_MP3_dir, \
                                      A_roll_IMG_dir+".mp4")
