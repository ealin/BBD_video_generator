import os
import argparse
import time

# 引入自訂模組
from book_to_script import generate_script_and_seo
from script_parser import parse_and_generate_audio
from image_generator import generate_avatars, generate_backgrounds, create_youtube_thumbnail
from core_renderer import render_core_clips
from final_render import composite_final_video

def main():
    parser = argparse.ArgumentParser(description='BBD YouTube 影片全自動化生成工具')
    parser.add_argument('--input_txt', type=str, required=True, help='原始書籍文字檔路徑 (例如: 128_20260322_量子与生活/raw/book.txt)')
    parser.add_argument('--book_id', type=str, default="128", help='書籍編號 (預設: 128)')
    parser.add_argument('--output_dir', type=str, required=True, help='自動化輸出目錄')
    parser.add_argument('--intro', type=str, default="", help='開場影片路徑')
    parser.add_argument('--outro', type=str, default="", help='結尾影片路徑')
    
    args = parser.parse_args()
    
    print(f"========== 啟動 BBD 自動化影片生成流程 ==========")
    print(f"輸入檔案: {args.input_txt}")
    print(f"書籍編號: {args.book_id}")
    print(f"輸出目錄: {args.output_dir}")
    
    os.makedirs(args.output_dir, exist_ok=True)
    
    # 預備路徑
    script_path = os.path.join(args.output_dir, "book_abstract_auto.txt")
    seo_path = os.path.join(args.output_dir, "seo_info.json")
    visuals_dir = os.path.join(args.output_dir, "visuals")
    av_dir = os.path.join(args.output_dir, "AV")
    bg_img_dir = os.path.join(visuals_dir, "bg_image")
    final_video_path = os.path.join(args.output_dir, f"Final_Video_{args.book_id}.mp4")
    
    start_time = time.time()
    
    # === 階段 1: 產生腳本與 SEO ===
    print("\n>>> 階段 1: 正在呼叫 LLM 產生對話腳本與 SEO 資訊...")
    if not os.path.exists(script_path):
        success = generate_script_and_seo(args.input_txt, script_path, seo_path)
        if not success:
            print("腳本產生失敗，流程終止。")
            return
    else:
        print("已存在生成的腳本，跳過階段 1。")
        
    # === 階段 2: 劇本解析與語音合成 ===
    print("\n>>> 階段 2: 正在解析腳本、切分段落並合成語音 (TTS)...")
    success = parse_and_generate_audio(script_path, args.output_dir, book_id=args.book_id, num_clips=4)
    if not success:
        print("語音產生失敗，流程終止。")
        return
        
    # === 階段 3: 生成視覺素材 (頭像、背景、縮圖) ===
    print("\n>>> 階段 3: 正在產生視覺素材...")
    os.makedirs(bg_img_dir, exist_ok=True)
    generate_avatars(visuals_dir)
    generate_backgrounds(script_path, bg_img_dir)
    
    # 生成縮圖 (背景圖使用生成的第一張 0.jpg)
    create_youtube_thumbnail(seo_path, os.path.join(bg_img_dir, "0.jpg"), None, os.path.join(visuals_dir, "thumbnail.jpg"))
    
    # === 階段 4: 基礎影片渲染 ===
    print("\n>>> 階段 4: 正在渲染核心影片素材 (_img, _sub, _head)...")
    success = render_core_clips(
        txt_base_dir=args.output_dir,
        voice_base_dir=args.output_dir,
        bg_img_dir=bg_img_dir,
        output_dir=av_dir,
        book_ID=args.book_id,
        clip_number=4
    )
    if not success:
        print("基礎渲染失敗，流程終止。")
        return
        
    # === 階段 5: 最終成片合成 ===
    print("\n>>> 階段 5: 正在疊加所有軌道並輸出最終影片...")
    success = composite_final_video(
        av_dir=av_dir,
        book_id=args.book_id,
        output_path=final_video_path,
        intro_video_path=args.intro,
        outro_video_path=args.outro,
        num_clips=4
    )
    
    if success:
        elapsed = time.time() - start_time
        print(f"\n========== 恭喜！全自動化流程完成 ==========")
        print(f"總耗時: {elapsed/60:.2f} 分鐘")
        print(f"最終影片: {final_video_path}")
        print(f"YouTube 縮圖: {os.path.join(visuals_dir, 'thumbnail.jpg')}")
        print(f"SEO 資訊: {seo_path}")
    else:
        print("\n========== 流程結束，但最終成片合成失敗 ==========")

if __name__ == "__main__":
    main()
