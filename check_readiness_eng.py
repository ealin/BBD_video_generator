import os
import csv

def run_english_readiness_checks():
    print("==================================================")
    print("    B134 English Video Production Readiness Check ")
    print("==================================================")
    
    project_dir = "134_20260527_你的生命是一場喜樂的量子遊戲"
    
    # 1. Check info_E.txt
    print("\n[Item 1] Checking info_E.txt...")
    info_path = os.path.join(project_dir, "raw/info_E.txt")
    if os.path.exists(info_path):
        print(f"  ✓ Found info_E.txt: {info_path}")
        with open(info_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_fields = ["【Video Title】", "【Thumbnail Title】", "【SEO Tags】", "【Video Description】"]
        missing_fields = []
        for field in required_fields:
            if field not in content:
                missing_fields.append(field)
        
        if not missing_fields:
            print("  ✓ info_E.txt contains all required sections (Video Title, Thumbnail Title, SEO Tags, Description)")
        else:
            print(f"  ✗ info_E.txt is missing sections: {missing_fields}")
    else:
        print(f"  ✗ Cannot find info_E.txt at: {info_path}")
        
    # 2. Check youtube_thumbnail_E.png
    print("\n[Item 2] Checking YouTube Thumbnail...")
    photo_dir = os.path.join(project_dir, "photo")
    thumbnail_path = os.path.join(photo_dir, "youtube_thumbnail_E.png")
    if os.path.exists(thumbnail_path):
        print(f"  ✓ Found English thumbnail: {thumbnail_path} (Size: {os.path.getsize(thumbnail_path):,} bytes)")
    else:
        print(f"  ✗ Cannot find English thumbnail: {thumbnail_path}")
        
    # 3. Check text & voice file matching in txt134_E and voice_E
    print("\n[Item 3] Checking script & voice matching...")
    txt_dir = os.path.join(project_dir, "raw/txt134_E")
    voice_dir = os.path.join(project_dir, "raw/voice134_E")
    
    txt_files = sorted([f for f in os.listdir(txt_dir) if f.endswith(".txt") and not f.startswith('.')]) if os.path.exists(txt_dir) else []
    voice_files = sorted([f for f in os.listdir(voice_dir) if f.endswith(".mp3") and not f.startswith('.')]) if os.path.exists(voice_dir) else []
    
    print(f"  - English Script files (.txt) count: {len(txt_files)}")
    print(f"  - English Voice files (.mp3) count: {len(voice_files)}")
    
    if len(txt_files) == 246 and len(voice_files) == 246:
        print("  ✓ Perfect count! Exactly 246 text and 246 audio files.")
    else:
        print(f"  ✗ Count discrepancy! Expected 246 of each, got {len(txt_files)} scripts and {len(voice_files)} audios.")
        
    if len(txt_files) > 0 and len(voice_files) > 0:
        mismatch = []
        for t_file in txt_files:
            base = os.path.splitext(t_file)[0]
            expected_mp3 = f"{base}.mp3"
            if expected_mp3 not in voice_files:
                mismatch.append(t_file)
        if not mismatch:
            print("  ✓ All files match 1-to-1 perfectly!")
        else:
            print(f"  ✗ Mismatched/missing audio for: {mismatch[:5]}...")
            
    # 4. Check Avatars and cover candidates
    print("\n[Item 4] Checking image resources...")
    avatars = ["AA.png", "BB.png", "CC.png"]
    for av in avatars:
        av_path = os.path.join(photo_dir, av)
        if os.path.exists(av_path):
            print(f"  ✓ Found avatar: {av_path}")
        else:
            print(f"  ✗ Missing avatar: {av_path}")
            
    cover_path = os.path.join(photo_dir, "中文封面.jpg")
    if os.path.exists(cover_path):
        print(f"  ✓ Found fallback book cover: {cover_path}")
    else:
        print(f"  ✗ Missing fallback cover: {cover_path}")
        
    # 5. Check background images
    print("\n[Item 5] Checking background images...")
    bg_dir = os.path.join(project_dir, "photo/bg134")
    bg_files = sorted([f for f in os.listdir(bg_dir) if f.endswith(".png") and f.replace(".png","").isdigit() and not f.startswith('.')], key=lambda x: int(os.path.splitext(x)[0])) if os.path.exists(bg_dir) else []
    print(f"  - Background images (.png) count: {len(bg_files)}")
    if len(bg_files) == 41:
        print("  ✓ Background images count is correct (exactly 41 files, 0.png to 40.png)")
        is_sequential = all(int(os.path.splitext(f)[0]) == idx for idx, f in enumerate(bg_files))
        if is_sequential:
            print("  ✓ Background images are named sequentially (0.png to 40.png)")
        else:
            print("  ✗ Background images are not named sequentially!")
    else:
        print(f"  ✗ Expected 41 background images (0.png to 40.png), got {len(bg_files)}")

    # 6. Check font files
    print("\n[Item 6] Checking English fonts...")
    fonts = ["Montserrat-Bold.ttf", "Montserrat-SemiBold.ttf", "Montserrat-Regular.ttf"]
    all_fonts_ok = True
    for f in fonts:
        if os.path.exists(f):
            print(f"  ✓ Found font: {f}")
        else:
            print(f"  ✗ Missing font: {f}")
            all_fonts_ok = False
            
    if all_fonts_ok:
        print("  ✓ All Montserrat premium fonts are present and ready!")

if __name__ == "__main__":
    run_english_readiness_checks()
