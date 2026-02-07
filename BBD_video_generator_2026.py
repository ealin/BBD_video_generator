import os
import random
import numpy as np
from PIL import Image

# MoviePy 相關模組導入
from moviepy import *
from moviepy.video import *
from moviepy.audio import *
from moviepy.audio.AudioClip import AudioClip
from moviepy.video.VideoClip import VideoClip
# 導入特效
from moviepy.video.fx import FadeIn, FadeOut, CrossFadeIn, CrossFadeOut, Scroll, MaskColor
from moviepy.audio.fx import AudioFadeIn, AudioFadeOut, AudioNormalize

def convert_webp_to_jpg_with_resolution(input_file, resolution):
    """
    功能：將 .webp 圖片轉換為指定解析度的 .jpg。
    """
    try:
        output_file = input_file.rsplit('.', 1)[0] + "-2.jpg"
        with Image.open(input_file) as img:
            resized_img = img.resize(resolution, Image.LANCZOS)
            rgb_img = resized_img.convert("RGB") # JPG 不支援透明度，需轉 RGB
            rgb_img.save(output_file, "JPEG")
            print(f"圖像已成功轉換為解析度 {resolution} 並保存為 {output_file}")
    except Exception as e:
        print(f"處理圖像時出错: {e}")


def convert_png_to_jpg_with_resolution(input_file, resolution):
    """
    功能：將 .png 圖片轉換為指定解析度的 .jpg。
    """
    try:
        output_file = input_file.rsplit('.', 1)[0] + ".jpg"
        with Image.open(input_file) as img:
            resized_img = img.resize(resolution, Image.LANCZOS)
            rgb_img = resized_img.convert("RGB")
            rgb_img.save(output_file, "JPEG")
            print(f"圖像已成功轉換為解析度 {resolution} 並保存為 {output_file}")
    except Exception as e:
        print(f"處理圖像時出错: {e}")


class Topic:
    """
    資料結構：用於儲存每個主題段落的資訊。
    """
    def __init__(self, line, second, time):
        self.line = line      # 字幕內容 (字串)
        self.second = second  # 開始秒數 (浮點數)
        self.time = time      # 格式化的時間字串 (HH:MM:SS 或 MM:SS)

    def __repr__(self):
        return f"Topic( '{self.time}' '{self.line}')"


def starts_with_pattern(line, pattern):
    """
    功能：封裝字串開頭檢查，判斷 line 是否以 pattern 開頭。
    """
    return line.startswith(pattern)


def format_seconds_to_hms(seconds):
    """
    功能：將秒數轉換為 分:秒 (MM:SS) 格式。
    """
    seconds = int(seconds)
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{minutes:02}:{secs:02}"


def make_silence(t):
    """
    功能：產生靜音訊號（振幅為 0）。
    """
    return 0.0


def generate_videos_from_txt_img_mp3(txt_dir, voice_dir, bg_img_dir, output_file, start_second, topic_index, bg_img_ID, bg_type=0):
    """
    核心功能：從指定目錄讀取 .txt 和 .mp3，生成三個同步影片：
    1. 背景影片 (_img)
    2. 綠幕字幕影片 (_sub)
    3. 綠幕頭像影片 (_head) - 採用 PIL 直接合成 + 縮放功能
    """
    
    # --- 參數配置區 ---
    background_color = (0, 255, 0)  # 綠幕背景 (用於去背)
    font_ttf = 'TaipeiSansTCBeta-Regular.ttf' # 字幕字體
    font_color = (255, 255, 153) # 香檳黃
    font_strok_color = 'black'
    font_strok_width = 2
    txt_font_size = 56
    
    # Topic (標題) 字幕設定
    topic_font_color = 'white'
    topic_font_strok_color = 'black'
    topic_font_strok_width = 2
    topic_txt_font_size = 46
    topic_font_background_color = (0, 49, 83) # 普魯士藍
    topic_font_ttf = 'TaipeiSansTCBeta-Bold.ttf'
    
    max_line = 0    # 0 代表無限制
    
    pattern_new_line = '<'    # 換行符號
    pattern_topic = '>>>>'    # 標題符號
    pattern_no_show = '!!!!'  # 不顯示字幕符號
    
    pending_duration = 2
    pending_color = (0, 0, 0) # 過場黑畫面顏色

    # --- 頭像影片配置參數 ---
    AA_IMG_PATH = "AA.png"
    BB_IMG_PATH = "BB.png"
    CC_IMG_PATH = "CC.png"

    # 新增：設定頭像目標寬度 (Pixel)
    head_width = 150  # 可自行修改為想要的數值，例如 50, 100, 300 等

    # 定義頭像座標 (左上角 X, Y)
    # 注意：這是圖片貼上的左上角座標，若縮小了圖片，位置可能需要微調
    head_pos_x = 70
    head_pos_y = 50     # (head_pos_x, head_pos_y) : 第一張頭像，距畫面左下角的長與寬
    AA_X, AA_Y = head_pos_x, (1080-head_pos_y-head_width)
    BB_X, BB_Y = head_pos_x*2 + head_width, (1080-head_pos_y-head_width)
    CC_X, CC_Y = head_pos_x*3 + head_width*2, (1080-head_pos_y-head_width)

    # 初始化頭像狀態變數
    current_avatar_img = None
    current_avatar_pos = (0, 0)
    # ---------------------------

    # --- 配置結束 ---

    img_clips = []
    sub_clips = []
    head_clips = [] 
    
    acc_second = start_second
    topic_array = [] 

    all_txt_files = os.listdir(txt_dir)
    all_txt_files.sort()

    topic_text = ""
    pattern_bg_img = '_bg'
    
    image_filename = os.path.join(bg_img_dir, f"{bg_img_ID}.jpg")
    print("Initial BG Image: " + image_filename)
    
    resize_image2(image_filename, 'temp.jpg')

    for txt_file in all_txt_files:
        if max_line != 0:
            max_line = max_line - 1
            if max_line == 0:
                break

        if txt_file.endswith(".txt"):
            base_name = os.path.splitext(txt_file)[0]
            txt_path = os.path.join(txt_dir, txt_file)
            mp3_path = os.path.join(voice_dir, f"{base_name}.mp3")

            if not os.path.exists(mp3_path):
                print(f"音訊檔案 {mp3_path} 不存在，跳過 {txt_file}")
                continue

            with open(txt_path, "r", encoding="utf-8") as f:
                subtitle_text = f.read().strip()

            if subtitle_text == pattern_bg_img:
                image_filename = os.path.join(bg_img_dir, f"{bg_img_ID}.jpg")
                bg_img_ID = bg_img_ID + 1
                print("===================> 切換背景圖: " + image_filename)
                resize_image2(image_filename, 'temp.jpg') 
                continue

            # --- 解析字幕以更新頭像狀態 ---
            if subtitle_text.startswith("。。。"):
                current_avatar_img = CC_IMG_PATH
                current_avatar_pos = (CC_X, CC_Y)
            elif subtitle_text.startswith("。。"):
                current_avatar_img = BB_IMG_PATH
                current_avatar_pos = (BB_X, BB_Y)
            elif subtitle_text.startswith("。"):
                current_avatar_img = AA_IMG_PATH
                current_avatar_pos = (AA_X, AA_Y)
            elif subtitle_text.startswith("@@@@") or subtitle_text.startswith("<<<<"):
                current_avatar_img = None
            # ---------------------------------

            if subtitle_text == ">>>>":
                audio_clip = AudioClip(make_silence, duration=1, fps=44100)
                duration = 1
            elif starts_with_pattern(subtitle_text, "@@@@"):
                duration = pending_duration
                audio_clip = AudioClip(make_silence, duration=duration, fps=44100)
            else:
                audio_clip = AudioFileClip(mp3_path)
                duration = audio_clip.duration
           
            subtitle_text = subtitle_text.replace(pattern_new_line, '\n')
            
            # --- Sub影片 (字幕) 製作 ---
            sub_elements = []
            green_bg = ColorClip(size=(1920, 1080), color=background_color, duration=duration)
            sub_elements.append(green_bg)

            if starts_with_pattern(subtitle_text, pattern_topic):
                topic_text = subtitle_text.replace(pattern_topic, "")
                print("***** Topic 發現: " + subtitle_text + " 開始時間 = " + format_seconds_to_hms(acc_second))
                topic_array.append(Topic(topic_text, acc_second, format_seconds_to_hms(acc_second)))
            else:    
                if string_align == 'center':
                    string_left = 200
                    string_top = 450
                    string_text_align = 'center'
                else:
                    string_left = 30
                    string_top = 500
                    string_text_align = 'left'

                text_clip = TextClip(
                    text=subtitle_text,
                    font_size=txt_font_size,
                    color=font_color,
                    bg_color=background_color,
                    stroke_color=font_strok_color,
                    stroke_width=font_strok_width,
                    margin=(string_left, string_top),
                    text_align=string_text_align,
                    font=font_ttf,
                    interline=15,
                ).with_position(string_text_align).with_duration(duration)
                
                if not starts_with_pattern(subtitle_text, pattern_no_show) and not starts_with_pattern(subtitle_text, '@@@@'):
                    sub_elements.append(text_clip)

            if topic_text and not starts_with_pattern(subtitle_text, '@@@@'):
                topic_clip = TextClip(
                    text=topic_text,
                    font_size=topic_txt_font_size,
                    color=topic_font_color,
                    bg_color=topic_font_background_color,         
                    stroke_color=topic_font_strok_color,
                    stroke_width=topic_font_strok_width,
                    margin=(10, 10),
                    method='label',
                    text_align='left',   
                    interline=30,
                    font=topic_font_ttf
                ).with_duration(duration)
                sub_elements.append(topic_clip)

            sub_video_clip = CompositeVideoClip(sub_elements, size=(1920, 1080)).with_duration(duration).with_audio(audio_clip)
            sub_clips.append(sub_video_clip)


            # --- Img影片 (背景) 製作 ---
            if starts_with_pattern(subtitle_text, '@@@@'):
                img_video_clip = ColorClip(size=(1920, 1080), color=pending_color, duration=duration)
            else:
                bg_clip = ImageClip('temp.jpg').with_duration(duration)
                img_video_clip = CompositeVideoClip([bg_clip], size=(1920, 1080)).with_duration(duration)

            img_clips.append(img_video_clip)


            # --- 頭像影片 (Head) 製作 (PIL 合成 + 縮放) ---
            
            # 1. 建立一張全綠色的畫布
            base_img = Image.new("RGB", (1920, 1080), background_color)
            
            # 2. 判斷是否需要貼頭像
            if current_avatar_img is not None:
                try:
                    # 載入頭像，轉為 RGBA
                    avatar_pil = Image.open(current_avatar_img).convert("RGBA")
                    
                    # === 新增：解析度調整邏輯 ===
                    # 取得原始尺寸
                    original_w, original_h = avatar_pil.size
                    
                    # 計算縮放比例與新高度 (等比例縮放)
                    scale_factor = head_width / float(original_w)
                    new_height = int(float(original_h) * float(scale_factor))
                    
                    # 執行縮放 (使用 LANCZOS 濾鏡獲得較好品質)
                    avatar_pil = avatar_pil.resize((head_width, new_height), Image.LANCZOS)
                    # ===========================
                    
                    # 貼上圖片 (使用 Alpha 通道作為 Mask)
                    base_img.paste(avatar_pil, current_avatar_pos, avatar_pil)
                    
                except Exception as e:
                    print(f"警告：無法載入或處理頭像圖片 {current_avatar_img}: {e}")
            
            # 3. 轉為 MoviePy ImageClip
            final_head_frame = np.array(base_img)
            head_video_clip = ImageClip(final_head_frame).with_duration(duration)

            head_clips.append(head_video_clip)
            # ---------------------------------
            
            acc_second = acc_second + duration

    print("打印 Topic 數組中的所有元素:")
    topic_num = 0
    for topic in topic_array:
        print(f"{topic.time} {topic.line}")
        topic_num = topic_num + 1

    print("輸出視頻長度：", acc_second)

    base_filename, ext = os.path.splitext(output_file)
    output_file_img = f"{base_filename}_img{ext}"
    output_file_sub = f"{base_filename}_sub{ext}"
    output_file_head = f"{base_filename}_head{ext}"

    final_head_clip = concatenate_videoclips(head_clips, method="compose")
    final_head_clip.write_videofile(output_file_head, fps=24, codec='libx264', audio=False)
    print(f"已生成頭像影片: {output_file_head}")

    final_sub_clip = concatenate_videoclips(sub_clips, method="compose")
    final_sub_clip.write_videofile(output_file_sub, fps=24, codec='libx264', audio_codec='aac')
    print(f"已生成字幕影片: {output_file_sub}")

    final_img_clip = concatenate_videoclips(img_clips, method="compose")
    final_img_clip.write_videofile(output_file_img, fps=24, codec='libx264', audio=False)
    print(f"已生成背景影片: {output_file_img}")

 
    return topic_num, int(acc_second) + 1, bg_img_ID


def create_random_video_from_directory(directory, target_duration, output_file):
    """
    功能：從目錄隨機選取 .mp4，拼接成指定長度的影片。
    """
    try:
        video_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.mp4')]

        if not video_files:
            print(f"目錄 {directory} 中沒有找到任何 .mp4 文件！")
            return

        clips = []
        total_duration = 0
        loop_count = 0

        while total_duration < target_duration:
            print(f"loop count: {loop_count}")
            loop_count = loop_count + 1
            random.shuffle(video_files)

            for video_file in video_files:
                print("processing:" + video_file)
                clip = VideoFileClip(video_file).resized((1920, 1080), Image.LANCZOS)
                clip_duration = clip.duration

                clip = CrossFadeIn(1).apply(clip)
                clip = CrossFadeOut(1).apply(clip)

                clips.append(clip)
                total_duration += clip_duration
                print(f"total_duration: {total_duration}, target_duration: {target_duration}")

                if total_duration >= target_duration:
                    print("time is enough!")
                    break
        
        final_video = concatenate_videoclips(clips, method="compose")
        final_video.write_videofile(output_file, fps=24, codec="libx264", audio_codec="aac")
        print(f"視頻已成功生成：{output_file}")

    except Exception as e:
        print(f"處理視頻時出错: {e}")


def resize_image(input_path, output_path, resolution=(1920, 1080)):
    """
    功能：單純調整圖像到指定解析度 (可能會變形)。
    """
    with Image.open(input_path) as img:
        resized_img = img.resize(resolution, Image.LANCZOS)
        resized_img.save(output_path)


def resize_image2(input_path, output_path, resolution=(1920, 1080)):
    """
    功能：智慧調整圖片大小。
    """
    img = Image.open(input_path)
    original_width, original_height = img.size

    target_width = 1920
    target_height = 1080

    if original_height >= original_width:
        print(" 豎直圖像處理")
        new_height = target_height - 10 
        new_width = int(original_width * (target_height / original_height))

        print(f"new height: {new_height}, new width: {new_width}")
        img_resized = img.resize((new_width, new_height), Image.LANCZOS)

        canvas = Image.new("RGB", (target_width, target_height), (0, 49, 83)) 
        
        x_offset = (target_width - new_width) - 100 
        print(f"x_offset = {x_offset}")
        canvas.paste(img_resized, (x_offset, 0))

        try:
            canvas.save(output_path, "JPEG")
            print("OKOK")
        except Exception as e:
            print(e)
    else:
        print(" 一般寬圖像處理")
        resized_img = img.resize(resolution, Image.LANCZOS)
        resized_img.save(output_path)

    print(f"處理完成，已保存至: {output_path}")


def create_video_from_images_with_ZOOMING(directory, zoom_scale, t1, t2, output_file):
    """
    功能：Ken Burns 效果，隨機播放圖片並帶有放大 (Zoom) 特效。
    """
    image_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.jpg')]

    if not image_files:
        print(f"目錄 {directory} 中沒有找到任何 .jpg 文件！")
        return

    temp_dir = os.path.join(directory, "temp_resized")
    os.makedirs(temp_dir, exist_ok=True)

    resized_files = []
    for img_file in image_files:
        resized_path = os.path.join(temp_dir, os.path.basename(img_file))
        print(img_file)
        resize_image2(img_file, resized_path)
        resized_files.append(resized_path)

    random.shuffle(resized_files)

    num_images = t2 // t1
    if num_images > len(resized_files):
        print("警告：可用圖片不足，將循環使用！")
        resized_files = (resized_files * (num_images // len(resized_files) + 1))[:num_images]
    else:
        resized_files = resized_files[:num_images]

    clips = []
    for filename in resized_files:
        img = Image.open(filename).convert("RGB")
        img_np = np.array(img)

        def make_frame(t, img_np=img_np):
            scale = 1.0 + (zoom_scale - 1.0) * (t / t1)
            h, w = img_np.shape[:2]
            center_x, center_y = w // 2, h // 2

            crop_w, crop_h = int(w / scale), int(h / scale)
            x1 = max(center_x - crop_w // 2, 0)
            y1 = max(center_y - crop_h // 2, 0)
            x2 = x1 + crop_w
            y2 = y1 + crop_h

            cropped = img_np[y1:y2, x1:x2]
            zoomed = np.array(Image.fromarray(cropped).resize(((1920, 1080)), Image.LANCZOS))
            return zoomed

        clip = VideoClip(make_frame=make_frame, duration=t1)
        clips.append(clip)

    final = concatenate_videoclips(clips, method="compose")
    final.write_videofile(output_file, fps=24)


def create_video_from_images(mix_mode, directory, t1, t2, output_file):
    """
    功能：隨機播放圖片影片 (幻燈片模式)。
    """
    try:
        image_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.jpg')]

        if not image_files:
            print(f"目錄 {directory} 中沒有找到任何 .jpg 文件！")
            return

        temp_dir = os.path.join(directory, "temp_resized")
        os.makedirs(temp_dir, exist_ok=True)

        resized_files = []
        for img_file in image_files:
            resized_path = os.path.join(temp_dir, os.path.basename(img_file))
            print(img_file)
            resize_image2(img_file, resized_path)
            resized_files.append(resized_path)

        random.shuffle(resized_files)

        num_images = t2 // t1
        if num_images > len(resized_files):
            print("警告：可用圖片不足，將循環使用！")
            resized_files = (resized_files * (num_images // len(resized_files) + 1))[:num_images]
        else:
            resized_files = resized_files[:num_images]
      
        clips = []
        for img in resized_files:
            clip = ImageClip(img).with_duration(t1)
            if mix_mode != True:
                clip = CrossFadeIn(1).apply(clip)
                clip = CrossFadeOut(1).apply(clip)            
            clips.append(clip)

        final_video = concatenate_videoclips(clips, method="compose")
        final_video.write_videofile(output_file, fps=24, codec="libx264")
        print(f"視頻已成功生成：{output_file}")

        for temp_file in resized_files:
            os.remove(temp_file)
        os.rmdir(temp_dir)

    except Exception as e:
        print(f"處理圖片時出错: {e}")


def create_audio_from_mp3s(first_audio, directory, t2, output_file):
    """
    功能：隨機串接 MP3/M4A 檔案，生成指定長度的背景音樂。
    """
    try:
        audio_files = [os.path.join(directory, f) for f in os.listdir(directory) if (f.endswith('.m4a') or f.endswith('.mp3'))]
     
        if not audio_files:
            print(f"目錄 {directory} 中沒有找到任何 .mp3 或 m4a 文件！")
            return

        random.shuffle(audio_files)
        if first_audio is not None:
            audio_files.insert(0, first_audio)

        clips = []
        total_duration = 0

        while total_duration < t2:
            for audio_file in audio_files:
                clip = AudioFileClip(audio_file)
                clip_duration = clip.duration

                clip = AudioFadeOut(5).apply(clip)
                clip = AudioFadeIn(2).apply(clip)

                print(format_seconds_to_hms(total_duration) + " " + os.path.basename(audio_file.strip()))

                if total_duration + clip_duration > t2:
                    total_duration += clip_duration
                    clips.append(clip)
                    break

                clips.append(clip)
                total_duration += clip_duration

                if total_duration >= t2:
                    break

        final_audio = concatenate_audioclips(clips)
        final_audio = AudioNormalize().apply(final_audio)

        final_audio.write_audiofile(output_file, codec="libmp3lame")
        print(f"音頻已成功生成：{output_file}")

    except Exception as e:
        print(f"處理音頻時出错: {e}")


def create_countdown_video(minutes, seconds, font, fontsize, color, position, output_file="countdown.mp4"):
    """
    功能：產生倒數計時影片，綠底 (00:00 時會閃爍)。
    """
    total_seconds = minutes * 60 + seconds
    resolution = (300, 100)
    bg_color = (0, 255, 0)  # 綠底

    flash_counter = 300

    background = ColorClip(size=resolution, color=bg_color, duration=total_seconds + flash_counter)

    def make_frame(t):
        if t < total_seconds:
            remaining = int(total_seconds - t)
            mm = remaining // 60
            ss = remaining % 60
            time_text = f"{mm:02}:{ss:02}"
        else:
            flash_on = int(t) % 2 == 0
            time_text = "00:00" if flash_on else ""

        txt_clip = TextClip(
            text=time_text,
            font_size=fontsize,
            font=font,
            bg_color=bg_color,
            color=color,
            margin=position
        ).with_duration(1)
        return txt_clip.get_frame(0)

    countdown = VideoClip(make_frame, duration=total_seconds + flash_counter)
    final = CompositeVideoClip([background, countdown])
    final.write_videofile(output_file, fps=24, codec="libx264", audio=False)


# --------------------------------------------------------------------------------------------------
# 主程式執行區
# --------------------------------------------------------------------------------------------------

# Configuration
book_ID = '124'
clip_number = 3         # 總共分為幾段 (B77-1, B77-2, B77-3)
string_align = 'left'   # 'center': 靠中偏右; 'left': 對齊左邊邊框

# 產生第 1 段影片
topic_num1, video_length1, start_bg_img_ID = \
    generate_videos_from_txt_img_mp3(
        "./腳本/txt"+book_ID+"-1", 
        "./腳本/voice"+book_ID+"-1", 
        "./bg_image/bg"+book_ID,
        "./output1.mp4",
        0, 0, 0, bg_type=0
    )

# 產生第 2 段影片
topic_num2, video_length2, start_bg_img_ID = \
        generate_videos_from_txt_img_mp3(
            "./腳本/txt"+book_ID+"-2", 
            "./腳本/voice"+book_ID+"-2", 
            "./bg_image/bg"+book_ID, 
            "./output2.mp4", 
            video_length1, topic_num1, start_bg_img_ID, bg_type=1
        )

# 產生第 3 段影片
video_length3 = video_length2
if clip_number >= 3:
    topic_num3, video_length3, start_bg_img_ID = \
            generate_videos_from_txt_img_mp3(
                "./腳本/txt"+book_ID+"-3",
                "./腳本/voice"+book_ID+"-3", 
                "./bg_image/bg"+book_ID, 
                "./output3.mp4", 
                video_length2, topic_num1+topic_num2, start_bg_img_ID, bg_type=1
            ) 

# 產生第 4 段影片
video_length4 = video_length3
if clip_number >= 4:
    topic_num4, video_length4, start_bg_img_ID = \
            generate_videos_from_txt_img_mp3(
                "./腳本/txt"+book_ID+"-4",
                "./腳本/voice"+book_ID+"-4", 
                "./bg_image/bg"+book_ID, 
                "./output4.mp4", 
                video_length3, topic_num1+topic_num2+topic_num3, start_bg_img_ID, bg_type=1
            ) 

# 生成總背景音樂
create_audio_from_mp3s(None, "./bg_mp3", video_length4, "output" + book_ID + ".mp3")