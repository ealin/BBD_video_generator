import os
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, CompositeAudioClip, concatenate_videoclips
from moviepy.video.fx.all import mask_color
import moviepy.audio.fx.all as afx

def make_transparent(clip, color=[0, 255, 0], thr=100, s=5):
    """
    將指定的顏色 (綠色) 變成透明
    """
    return mask_color(clip, color=color, thr=thr, s=s)

def composite_final_video(av_dir, book_id, output_path, intro_video_path, outro_video_path, num_clips=4):
    """
    將所有分段的 _img, _head, _sub 疊加，混合背景音樂，並加上片頭片尾
    """
    print("開始最終合成...")
    
    main_clips = []
    
    for i in range(1, num_clips + 1):
        img_path = os.path.join(av_dir, f"output{i}_img.mp4")
        sub_path = os.path.join(av_dir, f"output{i}_sub.mp4")
        head_path = os.path.join(av_dir, f"output{i}_head.mp4")
        
        if not os.path.exists(img_path) or not os.path.exists(sub_path):
            print(f"警告：找不到第 {i} 段的素材，跳過...")
            continue
            
        print(f"正在載入並處理第 {i} 段影片素材...")
        
        clip_img = VideoFileClip(img_path)
        clip_sub = VideoFileClip(sub_path)
        
        # 套用綠幕去背
        clip_sub_transparent = make_transparent(clip_sub)
        
        layers = [clip_img]
        
        if os.path.exists(head_path):
            clip_head = VideoFileClip(head_path)
            clip_head_transparent = make_transparent(clip_head)
            layers.append(clip_head_transparent)
            
        layers.append(clip_sub_transparent)
        
        # 疊加成單一段落
        composed_clip = CompositeVideoClip(layers, size=(1920, 1080)).set_duration(clip_img.duration)
        
        # 音訊處理：保留 _sub 的 TTS 聲音
        composed_clip = composed_clip.set_audio(clip_sub.audio)
        main_clips.append(composed_clip)

    if not main_clips:
        print("沒有可用的主要影片片段，合成失敗！")
        return False
        
    print("合併所有段落...")
    full_main_video = concatenate_videoclips(main_clips, method="compose")
    
    # 載入並混音背景音樂
    bgm_path = os.path.join(av_dir, f"output{book_id}.mp3")
    if os.path.exists(bgm_path):
        print("正在混合背景音樂...")
        bg_audio = AudioFileClip(bgm_path).fx(afx.volumex, 0.2) # 將 BGM 音量調低為 20%
        # 如果 BGM 比較長，截斷至主影片長度
        bg_audio = bg_audio.set_duration(full_main_video.duration)
        
        final_audio = CompositeAudioClip([full_main_video.audio, bg_audio])
        full_main_video = full_main_video.set_audio(final_audio)
    
    # 加入片頭片尾
    final_sequence = []
    
    if intro_video_path and os.path.exists(intro_video_path):
        intro_clip = VideoFileClip(intro_video_path).resize((1920, 1080))
        final_sequence.append(intro_clip)
        
    final_sequence.append(full_main_video)
    
    if outro_video_path and os.path.exists(outro_video_path):
        outro_clip = VideoFileClip(outro_video_path).resize((1920, 1080))
        final_sequence.append(outro_clip)
        
    print("產生最終影片序列...")
    final_video = concatenate_videoclips(final_sequence, method="compose")
    
    print(f"開始輸出最終影片至 {output_path} (這可能需要一段時間)...")
    final_video.write_videofile(
        output_path, 
        fps=24, 
        codec='libx264', 
        audio_codec='aac',
        preset='fast',
        threads=4
    )
    
    print("輸出完成！")
    return True

if __name__ == "__main__":
    book_id = "128"
    av_dir = f"128_20260322_量子与生活/auto_output/AV"
    out_file = f"128_20260322_量子与生活/auto_output/Final_Video_{book_id}.mp4"
    intro = "128_20260322_量子与生活/AV/訪談START.mp4"
    outro = "128_20260322_量子与生活/AV/訪談STOP.mp4"
    
    # 測試執行 (請確保 AV 目錄下已有素材)
    # composite_final_video(av_dir, book_id, out_file, intro, outro)
