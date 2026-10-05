#!/usr/bin/env python3
"""
build_broll_background_video.py
===============================
自動下載約 30 個與《AI未來已來》主題相符的高清動態短影片 (B-Roll Footage)，
涵蓋：伺服器機房、神經網絡、人形機器人、處理器晶片、代碼數據流、未來城市、全息交互等。
自動標準化為 1080P (1920x1080 @ 24fps) 無聲格式，並串接成單一宏偉的背景大片。
"""

import os
import sys
import re
import time
import urllib.request
import subprocess
import functools

print = functools.partial(print, flush=True)

# Ensure workspace site-packages is on sys.path
_repo_root = os.path.dirname(os.path.abspath(__file__))
_site_packages = os.path.join(_repo_root, "site-packages")
if os.path.exists(_site_packages) and _site_packages not in sys.path:
    sys.path.insert(0, _site_packages)

import imageio_ffmpeg

TEMP_DIR = os.path.join(_repo_root, "data", "temp_stock_clips")
NORMALIZED_DIR = os.path.join(_repo_root, "data", "temp_normalized_clips")
OUTPUT_VIDEO = os.path.join(_repo_root, "data", "背景影片", "AI未來已來.mp4")

# 精選 32 個主題相符的高清短影片（目標成功抓取並串接 30 個）
CURATED_CLIPS = [
    # 1. 算力中心與伺服器機房 (Compute Engines & Server Infrastructure)
    {"id": "23282", "title": "藍光伺服器機房長廊", "cat": "算力中心"},
    {"id": "23281", "title": "工程師於機房操作筆電", "cat": "算力中心"},
    {"id": "47050", "title": "伺服器光纖與機櫃特寫", "cat": "算力中心"},
    {"id": "23215", "title": "伺服器機架陣列指示燈", "cat": "算力中心"},
    
    # 2. 神經網絡與數字大腦 (Neural Networks & AI Intelligence)
    {"id": "31510", "title": "3D 旋轉神經網絡光點與連線", "cat": "神經網絡"},
    {"id": "31771", "title": "三維數字大腦數據球體", "cat": "神經網絡"},
    {"id": "12748", "title": "全球數字化互聯網絡地圖", "cat": "神經網絡"},
    {"id": "31497", "title": "穿梭於多維黑色立方體數據空間", "cat": "神經網絡"},
    
    # 3. 人形機器人與精密自動化 (Robotics & Embodied AI)
    {"id": "47257", "title": "高科技工廠機械手臂自動化流水線", "cat": "機器人"},
    {"id": "47258", "title": "電子元件生產基地機器人作業", "cat": "機器人"},
    {"id": "20970", "title": "現代工業機械手臂精密作業", "cat": "機器人"},
    {"id": "45220", "title": "仿生人形機器人步態特寫", "cat": "機器人"},
    {"id": "20961", "title": "智能仿生機器人面部與眼部運動", "cat": "機器人"},
    {"id": "49042", "title": "高靈活性人形機器人動態演示", "cat": "機器人"},
    
    # 4. 微處理器、晶圓與晶片 (Compute Hardware & Microchips)
    {"id": "47051", "title": "高科技晶片處理器電路板特寫", "cat": "晶片硬體"},
    {"id": "47048", "title": "微型電子電路微觀世界", "cat": "晶片硬體"},
    {"id": "47266", "title": "自動化機械高速貼片晶片", "cat": "晶片硬體"},
    {"id": "47267", "title": "微處理器核心線路板俯瞰", "cat": "晶片硬體"},
    
    # 5. 代碼流、軟體自動生成與矩陣 (Code Generation & Cyber Matrix)
    {"id": "46635", "title": "新技術代碼自動編程與運行", "cat": "代碼生成"},
    {"id": "50748", "title": "螢幕綠色字符矩陣數據瀑布", "cat": "代碼生成"},
    {"id": "9757",  "title": "電腦螢幕上的動態程式碼流", "cat": "代碼生成"},
    {"id": "46634", "title": "高難度軟體工程編寫特寫", "cat": "代碼生成"},
    
    # 6. 未來科技界面、全息與虛擬設備 (Holographic HUD & Future Devices)
    {"id": "99786", "title": "未來科技設備全息運動動畫", "cat": "全息科技"},
    {"id": "51214", "title": "操作未來全息 VR 科技界面", "cat": "全息科技"},
    {"id": "41180", "title": "專注審視未來平板數據界面", "cat": "全息科技"},
    {"id": "221",   "title": "眼鏡上倒映的高速數據螢幕", "cat": "全息科技"},
    
    # 7. 人機協同與未來工作者 (Human-AI Collaboration & Workforce)
    {"id": "29991", "title": "工程師於現代科技工坊專注研發", "cat": "人機協同"},
    {"id": "41638", "title": "多終端協同作業與移動智能辦公", "cat": "人機協同"},
    {"id": "43527", "title": "雙手在高性能電腦前高速操作", "cat": "人機協同"},
    {"id": "41183", "title": "專業工程師在高效能工作站工作", "cat": "人機協同"},
    
    # 8. 智慧城市與未來科技生活 (Smart City & Cyberpunk Future)
    {"id": "242",   "title": "商務人士高效敲擊現代鍵盤", "cat": "未來商業"},
    {"id": "47263", "title": "全自動化無人農場精密培育", "cat": "未來商業"}
]

def download_clip(clip_info):
    vid = clip_info["id"]
    out_file = os.path.join(TEMP_DIR, f"{vid}.mp4")
    if os.path.exists(out_file) and os.path.getsize(out_file) > 100000:
        return out_file
        
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # 嘗試 1080p，若無則降至 720p
    for res in ["1080", "720"]:
        url = f"https://assets.mixkit.co/videos/{vid}/{vid}-{res}.mp4"
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=20) as resp, open(out_file, "wb") as fp:
                fp.write(resp.read())
            if os.path.exists(out_file) and os.path.getsize(out_file) > 100000:
                print(f"  ✓ 下載成功 [{res}p]: {clip_info['cat']} - {clip_info['title']} ({os.path.getsize(out_file)/1024/1024:.2f} MB)")
                return out_file
        except Exception as e:
            pass
            
    print(f"  ✗ 下載失敗: {vid} ({clip_info['title']})")
    return None

def normalize_clip(raw_mp4, output_mp4, ffmpeg_exe, target_duration=14.0):
    """
    將短片標準化為 1920x1080, 24fps, 無音軌, 裁切前 target_duration 秒
    並在首尾加入微淡入淡出（0.5秒），使拼接時自然流暢。
    """
    cmd = [
        ffmpeg_exe, "-y",
        "-i", raw_mp4,
        "-t", str(target_duration),
        "-vf", (
            "scale=1920:1080:force_original_aspect_ratio=increase,"
            "crop=1920:1080,"
            "fps=24,"
            f"fade=t=in:st=0:d=0.5,fade=t=out:st={target_duration-0.5}:d=0.5"
        ),
        "-an",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        output_mp4
    ]
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return res.returncode == 0 and os.path.exists(output_mp4) and os.path.getsize(output_mp4) > 10000

def main():
    print("=" * 65)
    print("🚀 啟動《AI未來已來》專屬 B-Roll 背景影片下載與合成工程")
    print("   目標：串接約 30 個精選 AI 科技短片（機房/大腦/機器人/晶片/代碼/城市）")
    print("=" * 65)
    
    os.makedirs(TEMP_DIR, exist_ok=True)
    os.makedirs(NORMALIZED_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(OUTPUT_VIDEO), exist_ok=True)
    
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    
    # 1. 批次下載素材
    print("\n[第一階段] 批次下載高品質免版權短片素材...")
    valid_clips = []
    
    for idx, clip in enumerate(CURATED_CLIPS, 1):
        print(f"[{idx:02d}/{len(CURATED_CLIPS)}] 獲取素材: {clip['cat']} - {clip['title']} ...")
        raw_file = download_clip(clip)
        if raw_file:
            valid_clips.append((clip, raw_file))
        if len(valid_clips) >= 30:
            print(f"\n✓ 已成功獲取 30 個頂級素材！開始進入後製...")
            break
            
    print(f"\n總共成功獲取 {len(valid_clips)} 個可用短影片。")
    if len(valid_clips) < 15:
        print("錯誤：可用影片數量過少，無法完成合成！")
        return

    # 2. 影片標準化處理 (1080P, 24fps, 無聲, 淡入淡出)
    print("\n[第二階段] 標準化影片格式 (1920x1080 @ 24fps, 無聲, 平滑淡入淡出)...")
    normalized_list = []
    
    for idx, (clip_info, raw_path) in enumerate(valid_clips, 1):
        norm_path = os.path.join(NORMALIZED_DIR, f"norm_{idx:02d}_{clip_info['id']}.mp4")
        print(f"[{idx:02d}/{len(valid_clips)}] 標準化: {clip_info['cat']} - {clip_info['title']} ...")
        # 每段維持 12~14 秒
        dur = 14.0
        ok = normalize_clip(raw_path, norm_path, ffmpeg_exe, target_duration=dur)
        if ok:
            normalized_list.append(norm_path)
            print(f"  ✓ 完成: {os.path.getsize(norm_path)/1024/1024:.2f} MB")
        else:
            print(f"  ✗ 轉碼失敗: {clip_info['id']}")
            
    print(f"\n總共標準化完成 {len(normalized_list)} 個片段。")
    
    # 3. 拼接所有片段為單一背景大片
    print("\n[第三階段] 拼接所有片段為單一背景影片...")
    concat_list_file = os.path.join(NORMALIZED_DIR, "concat_list.txt")
    with open(concat_list_file, "w", encoding="utf-8") as f:
        for p in normalized_list:
            f.write(f"file '{os.path.abspath(p)}'\n")
            
    # 使用 ffmpeg concat demuxer 高速無損拼接
    cmd_concat = [
        ffmpeg_exe, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_list_file,
        "-c", "copy",
        OUTPUT_VIDEO
    ]
    
    print(f"執行無損拼接 -> {OUTPUT_VIDEO} ...")
    subprocess.run(cmd_concat, check=True)
    
    # 4. 驗證最終輸出
    if os.path.exists(OUTPUT_VIDEO) and os.path.getsize(OUTPUT_VIDEO) > 100000:
        sz = os.path.getsize(OUTPUT_VIDEO) / 1024 / 1024
        # Probe duration
        probe_cmd = [ffmpeg_exe, "-i", OUTPUT_VIDEO]
        p = subprocess.run(probe_cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        dur_str = "未知"
        for line in p.stderr.split("\n"):
            if "Duration:" in line:
                dur_str = line.split("Duration:")[1].split(",")[0].strip()
                break
                
        print("\n" + "=" * 65)
        print("🎉《AI未來已來》專屬 B-Roll 背景影片合成完成！")
        print(f"  • 輸出位置: {OUTPUT_VIDEO}")
        print(f"  • 片段總數: {len(normalized_list)} 個主題片段")
        print(f"  • 影片時長: {dur_str}")
        print(f"  • 檔案大小: {sz:.2f} MB")
        print(f"  • 規格參數: 1920x1080 (16:9, 1080P), 24fps, 無音軌")
        print("=" * 65)
    else:
        print("錯誤：最終輸出影片失敗！")

if __name__ == "__main__":
    main()
