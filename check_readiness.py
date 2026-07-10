import os
import csv
import re

def find_book_dir(book_id):
    for item in os.listdir('.'):
        if os.path.isdir(item) and (item.startswith(f"{book_id}_") or item.startswith(f"B{book_id}_") or item.startswith(f"1{book_id}_") or item.startswith(f"{book_id}-") or item.startswith(f"B{book_id}-") or item.startswith(f"1{book_id}-")):
            return item
    raise FileNotFoundError(f"Cannot find book directory starting with {book_id}_")

def expected_script_segments(script_path):
    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()

    raw_segments = content.split('\n\n')
    segments = []
    for s in raw_segments:
        s = s.strip()
        if not s:
            continue

        lines = s.split('\n')
        current_part = []
        for line in lines:
            if line.startswith('>>>>') or line.startswith('@@@@'):
                if current_part:
                    segments.append('\n'.join(current_part))
                    current_part = []
                segments.append(line)
            else:
                current_part.append(line)
        if current_part:
            segments.append('\n'.join(current_part))

    return len(segments)

def numbered_files(directory, book_id, ext):
    pattern = re.compile(rf"^B{re.escape(book_id)}_(\d{{4}})\.{re.escape(ext)}$")
    found = {}
    if not os.path.exists(directory):
        return found
    for filename in os.listdir(directory):
        match = pattern.match(filename)
        if match:
            found[int(match.group(1))] = filename
    return found

def run_checks():
    print("==================================================")
    print("       YouTube 書摘要影片 Pipeline 就緒度檢查       ")
    print("==================================================")
    
    # 1. 檢查 info.txt
    print("\n[項目 1] 檢查 info.txt...")
    book_id = "146"
    book_dir = find_book_dir(book_id)

    info_path = f"{book_dir}/raw/info.txt"
    if os.path.exists(info_path):
        print(f"  ✓ 找到 info.txt: {info_path}")
        with open(info_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_fields = ["影片主標題", "縮圖標題", "SEO 標籤", "影片說明欄"]
        missing_fields = []
        for field in required_fields:
            if field not in content:
                missing_fields.append(field)
        
        if not missing_fields:
            print("  ✓ info.txt 包含所有必要欄位（影片主標題、縮圖標題、SEO 標籤、影片說明欄）")
        else:
            print(f"  ✗ info.txt 缺漏欄位: {missing_fields}")
    else:
        print(f"  ✗ 找不到 info.txt (預期路徑: {info_path})")
        
    # 1.1 檢查發音人清單.csv
    print("  - 檢查發音人清單...")
    spk_csv_path = f"{book_dir}/raw/發音人清單.csv"
    if os.path.exists(spk_csv_path):
        print(f"  ✓ 找到發音人清單: {spk_csv_path}")
    else:
        print(f"  ✗ 找不到發音人清單 (預期路徑: {spk_csv_path})")
        
    # 2. 檢查 youtube_thumbnail.png
    print("\n[項目 2] 檢查縮圖檔案...")
    photo_dir = f"{book_dir}/photo"
    thumbnail_found = False
    if os.path.exists(photo_dir):
        for f in os.listdir(photo_dir):
            if f.startswith("youtube_thumbnail") and not f.startswith('.'):
                print(f"  ✓ 找到縮圖檔案: {f}")
                thumbnail_found = True
                break
        if not thumbnail_found:
            print("  ✗ 找不到名稱為 'youtube_thumbnail' 的圖檔")
    else:
        print(f"  ✗ 找不到 photo 目錄: {photo_dir}")
        
    # 3. 檢查腳本與語音數量一致性
    print("\n[項目 3] 檢查腳本與語音數量一致性...")
    txt_dir = f"{book_dir}/raw/txt{book_id}"
    voice_dir = f"{book_dir}/raw/voice{book_id}"
    
    txt_files = sorted([f for f in os.listdir(txt_dir) if f.endswith(".txt") and not f.startswith('.')]) if os.path.exists(txt_dir) else []
    voice_files = sorted([f for f in os.listdir(voice_dir) if f.endswith(".mp3") and not f.startswith('.')]) if os.path.exists(voice_dir) else []
    script_path = os.path.join(book_dir, "raw", "腳本-step4.txt")
    expected_segments = expected_script_segments(script_path) if os.path.exists(script_path) else 0
    
    print(f"  - 文字檔 (.txt) 數量: {len(txt_files)}")
    print(f"  - 語音檔 (.mp3) 數量: {len(voice_files)}")
    print(f"  - 腳本實際切段預期數量: {expected_segments}")
    
    if len(txt_files) == len(voice_files) and len(txt_files) > 0:
        print("  ✓ 腳本與語音檔案數量一致！")
        # 檢查檔名對應
        mismatch = []
        for t_file in txt_files:
            base = os.path.splitext(t_file)[0]
            expected_mp3 = f"{base}.mp3"
            if expected_mp3 not in voice_files:
                mismatch.append(t_file)
        if not mismatch:
            print("  ✓ 所有檔名皆完美一對一對應！")
        else:
            print(f"  ✗ 檔名不匹配的檔案: {mismatch[:5]}...")
    else:
        print("  ✗ 檔案數量不一致或目錄為空！")

    if expected_segments > 0:
        txt_numbered = numbered_files(txt_dir, book_id, "txt")
        voice_numbered = numbered_files(voice_dir, book_id, "mp3")
        expected_numbers = set(range(1, expected_segments + 1))
        missing_txt = sorted(expected_numbers - set(txt_numbered))
        missing_voice = sorted(expected_numbers - set(voice_numbered))
        extra_txt = sorted(set(txt_numbered) - expected_numbers)
        extra_voice = sorted(set(voice_numbered) - expected_numbers)
        zero_voice = sorted(
            name for name in voice_files
            if os.path.exists(os.path.join(voice_dir, name)) and os.path.getsize(os.path.join(voice_dir, name)) == 0
        )

        if not missing_txt and not extra_txt and len(txt_numbered) == expected_segments:
            print("  ✓ 文字檔編號與腳本預期段數完全一致")
        else:
            print(f"  ✗ 文字檔段數/編號異常：缺少 {missing_txt[:10]}，多出 {extra_txt[:10]}")

        if not missing_voice and not extra_voice and len(voice_numbered) == expected_segments:
            print("  ✓ 語音檔編號與腳本預期段數完全一致")
        else:
            print(f"  ✗ 語音檔段數/編號異常：缺少 {missing_voice[:10]}，多出 {extra_voice[:10]}")

        if not zero_voice:
            print("  ✓ 沒有 0-byte 語音檔")
        else:
            print(f"  ✗ 發現 0-byte 語音檔: {zero_voice[:10]}")

    # 4. 檢查各項圖檔、影片檔是否存在
    print("\n[項目 4] 檢查其他媒體素材...")
    
    # 4.1 頭像 (自書籍目錄下的 photo/ 載入)
    avatars = ["AA.png", "BB.png", "CC.png"]
    for av in avatars:
        av_path = os.path.join(photo_dir, av)
        if os.path.exists(av_path):
            print(f"  ✓ 找到頭像: {av_path}")
        else:
            print(f"  ✗ 找不到頭像: {av_path}")
            
    # 4.2 訪談影片
    av_dir = f"{book_dir}/AV"
    
    # 同時相容 '訪談開始.mp4' 與 '訪談START.mp4'
    start_v = os.path.join(av_dir, "訪談開始.mp4")
    start_v_alt = os.path.join(av_dir, "訪談START.mp4")
    end_v = os.path.join(av_dir, "訪談結束.mp4")
    end_v_alt = os.path.join(av_dir, "訪談END.mp4")
    
    if os.path.exists(start_v):
        print(f"  ✓ 找到開場影片: {start_v}")
    elif os.path.exists(start_v_alt):
        print(f"  ✓ 找到開場影片: {start_v_alt}")
    else:
        print(f"  ✗ 找不到開場影片 (預期: 訪談開始.mp4 或 訪談START.mp4)")
        
    if os.path.exists(end_v):
        print(f"  ✓ 找到結束影片: {end_v}")
    elif os.path.exists(end_v_alt):
        print(f"  ✓ 找到結束影片: {end_v_alt}")
    else:
        print(f"  ✗ 找不到結束影片 (預期: 訪談結束.mp4 或 訪談END.mp4)")
        
    # 4.3 中文與原文封面
    cn_cover = False
    en_cover = False
    if os.path.exists(photo_dir):
        for f in os.listdir(photo_dir):
            if f.startswith('.'):
                continue
            if "中文封面" in f:
                print(f"  ✓ 找到中文封面: {f}")
                cn_cover = True
            if "原文封面" in f:
                print(f"  ✓ 找到原文封面: {f}")
                en_cover = True
        if not cn_cover and not en_cover:
            print("  ✗ 找不到任何封面圖檔（中文封面或原文封面）")
        elif not cn_cover:
            print("  ✓ 找到原文封面，使用原文封面作為主封面")
            
    # 4.4 背景圖數量與分段生圖腳本 CSV 的段落數比較
    print(f"\n[項目 5] 檢查 {book_dir}/photo/bg{book_id} 與生圖腳本段落數...")
    bg_dir = f"{book_dir}/photo/bg{book_id}"
    csv_path = f"{book_dir}/raw/分段生圖腳本.csv"
    
    # 取得 CSV 分段數
    csv_segments = 0
    if os.path.exists(csv_path):
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            header = next(reader)
            for row in reader:
                if row:
                    csv_segments += 1
        print(f"  - 分段生圖腳本記錄的段落數量: {csv_segments}")
    else:
        print(f"  ✗ 找不到分段生圖腳本 CSV: {csv_path}")
        
    # 取得 bg_image/bg{book_id} 檔案數量 (排除重複類型，計算唯一數字編號)
    bg_numbers = set()
    if os.path.exists(bg_dir):
        for f in os.listdir(bg_dir):
            if f.startswith('.'):
                continue
            name, ext = os.path.splitext(f)
            if name.isdigit() and ext.lower() in ['.jpg', '.jpeg', '.png']:
                bg_numbers.add(int(name))
        
        bg_files = sorted(list(bg_numbers))
        print(f"  - bg{book_id} 中唯一的順序編號圖檔數量: {len(bg_files)}")
        if len(bg_files) > 0:
            print(f"  - 命名區間: {bg_files[0]} 至 {bg_files[-1]}")
            
        # 檢查是否連續且多於 CSV 分段數
        is_sequential = all(bg_files[i] == i for i in range(len(bg_files)))
        if is_sequential:
            print("  ✓ 圖檔命名依序連續 (0, 1, 2...)")
        else:
            print("  ✗ 圖檔命名不連續！請檢查檔名")
            
        if len(bg_files) >= csv_segments:
            print(f"  ✓ 圖檔數量 ({len(bg_files)}) 大於或等於分段數 ({csv_segments})")
        else:
            print(f"  ✗ 圖檔數量 ({len(bg_files)}) 少於分段數 ({csv_segments})！")
    else:
        print(f"  ✗ 找不到背景圖目錄: {bg_dir}")

if __name__ == "__main__":
    run_checks()
