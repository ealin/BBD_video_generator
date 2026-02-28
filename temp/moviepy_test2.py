from moviepy import *
from moviepy.video import *
from moviepy.audio import *
import os

def starts_with_arrows(string):
    """
    判斷字串是否以 '>>>>>' 開頭。

    :param string: str, 要檢查的字串
    :return: bool, 若以 '>>>>>' 開頭則傳回 True，否則傳回 False
    """
    return string.startswith(">>>>>")


def generate_video_from_text_and_audio(text_file, output_file):
    # 讀取文字檔內容
    with open(text_file, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    
    clips = []
    background_color = (0, 255, 0)  # 綠色背景
    

    for i, line in enumerate(lines):

        # 對應的 mp3 檔案名稱
        if i < 9 :
            audio_file = f'./voice/B66-2-000{i + 1}.mp3'
        else :
            audio_file = f'./voice/B66-2-00{i + 1}.mp3'

        if not os.path.exists(audio_file):
            print(f"音檔 {audio_file} 不存在，跳過該行！")
            continue
        else :
            print(f'process {audio_file} ')
        
        # 讀取音訊檔
        audio_clip = AudioFileClip(audio_file)
        duration = audio_clip.duration

        line = line.replace('\XD','\n')
        
        # 創建字幕的文字片段 (需分別一般段落或title 判斷：>>>>> )
        text_clip = TextClip(
            #text = '\n' + line + '\nABVDEDFFFF' + '\n我是大黑狗',                    # + '\n 換行有作用
            text=line,
            font_size=60,
            color='red',                    # can use RGB as a color
            bg_color=(0, 255, 0),           # (0, 255, 0),
            stroke_color='blue',
            stroke_width=1,
            #margin=(50,500),               # 控制字串的左上角位置
            method='label',                 # 不會自動換行！
            text_align='right',      #'left',   
            interline=30,                   # 行距
            transparent = True,
            font='Annotated.ttf')


        #if i==0:
        #    TextClip.list('color')
        #    TextClip.list('font')
        
        #if generate_video_from_text_and_audio(line) :
        #    text_clip = text_clip.with_position('center').with_duration(duration)
        #else :
        #    text_clip = text_clip.with_position('center').with_duration(duration)
        
        # 創建背景顏色
        bg_clip = ColorClip(size=(1920, 1080), color=background_color, duration=duration)
        #bg_clip = ColorClip(size=(1920, 1080), is_mask=True, color=0, duration=duration)
        
        # 合成字幕與背景
        # video_clip = bg_clip.with_layer(text_clip).with_audio(audio_clip)
        video_clip = CompositeVideoClip([bg_clip, text_clip]).with_duration(duration).with_audio(audio_clip)
        #video_clip = text_clip.with_duration(duration).with_audio(audio_clip)

        clips.append(video_clip)

    print('text clip process done. Start to generate MP4 file')
    

    
    # 合併所有片段
    #final_clip =  CompositeVideoClip(clips)   
    final_clip = concatenate_videoclips(clips, method="compose")
    final_clip.write_videofile(output_file, fps=24, codec='libx264', audio_codec='aac')

# 使用範例
generate_video_from_text_and_audio("sub.txt", "output.mp4")
