import os
import sys

# 將工作目錄加入 sys.path 以便 import
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 引入原有的腳本中的函式
from BBD_video_generator_2026 import generate_videos_from_txt_img_mp3, create_audio_from_mp3s
import BBD_video_generator_2026

def render_core_clips(txt_base_dir, voice_base_dir, bg_img_dir, output_dir, book_ID, clip_number=4, bg_type=1, default_bg_video_path='bg_image/turntable_playing.mp4'):
    """
    呼叫 BBD_video_generator_2026 中的核心函式來產生 _img, _sub, _head 影片與背景音樂
    """
    print("開始進行基礎影片渲染...")
    os.makedirs(output_dir, exist_ok=True)
    
    # 修改全域變數設定
    BBD_video_generator_2026.string_align = 'left'
    BBD_video_generator_2026.default_bg_video = default_bg_video_path

    start_bg_img_ID = 0
    video_length = 0
    topic_num = 0

    for i in range(1, clip_number + 1):
        txt_dir = os.path.join(txt_base_dir, f"txt{book_ID}-{i}")
        voice_dir = os.path.join(voice_base_dir, f"voice{book_ID}-{i}")
        
        # 確認該段落的目錄存在且有檔案
        if not os.path.exists(txt_dir) or len(os.listdir(txt_dir)) == 0:
            print(f"找不到段落 {i} 的資料 ({txt_dir})，提早結束渲染迴圈。")
            break
            
        output_file = os.path.join(output_dir, f"output{i}.mp4")
        
        print(f"正在渲染第 {i} 段影片...")
        topic_num, video_length, start_bg_img_ID = generate_videos_from_txt_img_mp3(
            txt_dir,
            voice_dir,
            bg_img_dir,
            output_file,
            video_length,
            topic_num,
            start_bg_img_ID,
            bg_type=bg_type
        )
        print(f"第 {i} 段影片渲染完成，目前總長度: {video_length} 秒")

    # 生成總背景音樂
    bg_mp3_dir = "./bg_mp3" # 預設背景音樂來源目錄
    output_bg_mp3 = os.path.join(output_dir, f"output{book_ID}.mp3")
    print("正在生成全長背景音樂...")
    create_audio_from_mp3s(None, bg_mp3_dir, video_length, output_bg_mp3)
    
    print("所有基礎素材渲染完成！")
    return True

if __name__ == "__main__":
    # 測試執行
    book_id = "128"
    base = f"128_20260322_量子与生活/auto_output"
    
    # 假設前兩個步驟已經在 base 產生了 txt128-X 和 voice128-X
    # 這裡只做參數示範
    render_core_clips(
        txt_base_dir=base,
        voice_base_dir=base,
        bg_img_dir="bg_image/bg" + book_id,
        output_dir=os.path.join(base, "AV"),
        book_ID=book_id,
        clip_number=4
    )
