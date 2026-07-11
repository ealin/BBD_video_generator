import os
import random
import numpy as np
from PIL import Image, ImageDraw, ImageChops, ImageFont

# MoviePy 相關模組導入
from moviepy import *
from moviepy.video import *
from moviepy.audio import *
from moviepy.audio.AudioClip import AudioClip
from moviepy.video.VideoClip import VideoClip
# 導入特效
from moviepy.video.fx import FadeIn, FadeOut, CrossFadeIn, CrossFadeOut, Scroll, MaskColor, Loop
from moviepy.audio.fx import AudioFadeIn, AudioFadeOut, AudioNormalize
import time
from proglog import ProgressBarLogger

class TimeTrackingLogger(ProgressBarLogger):
    def __init__(self, task_name):
        super().__init__()
        self.task_name = task_name
        self.start_time = time.time()
        self.last_print_time = 0

    def callback(self, **kwargs):
        pass  # 禁用預設的日誌輸出

    def bars_callback(self, bar, attr, value, old_value=None):
        super().bars_callback(bar, attr, value, old_value)
        current_time = time.time()
        # 限制更新頻率為每 0.5 秒一次
        if current_time - self.last_print_time >= 0.5:
            elapsed = int(current_time - self.start_time)
            total = self.bars[bar].get('total', 0)
            progress = (value / total * 100) if total > 0 else 0
            print(f"\r[{self.task_name}] 進度: {progress:.1f}% | 已耗時: {elapsed} 秒", end="", flush=True)
            self.last_print_time = current_time

# [Claude Comment] : 此程式為 BBD 書籍討論影片自動生成系統。
# [Claude Comment] : 輸入：逐句腳本 (.txt) + 對應 TTS 配音 (.mp3)；
# [Claude Comment] : 輸出：三條可後製合成的綠幕素材影片：背景(_img)、字幕(_sub)、頭像(_head)。

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


def get_text_width(text, font):
    dummy = Image.new('RGBA', (1, 1))
    dd = ImageDraw.Draw(dummy)
    bbox = dd.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]

def wrap_text_by_width(text, font, max_width=1650):
    original_lines = text.split('\n')
    final_lines = []
    for line in original_lines:
        if get_text_width(line, font) <= max_width:
            final_lines.append(line)
            continue
        words = line.split(' ')
        current_line = []
        for word in words:
            test_line = ' '.join(current_line + [word])
            if get_text_width(test_line, font) <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    final_lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    final_lines.append(word)
                    current_line = []
        if current_line:
            final_lines.append(' '.join(current_line))
    return '\n'.join(final_lines)

def make_pil_subtitle_clip(text, font_path, font_size, color, stroke_color,
                            stroke_width, extra_spacing, duration):
    """
    使用 PIL 繪製多行字幕（RGBA 透明背景），支援自訂行距。
    """
    try:
        font = ImageFont.truetype(font_path, font_size)
    except Exception:
        font = ImageFont.load_default()

    # Apply auto-wrapping to prevent text cut-off on edges
    text = wrap_text_by_width(text, font, max_width=1650)

    lines = text.split('\n') if '\n' in text else [text]

    # 測量每行尺寸
    dummy  = Image.new('RGBA', (1, 1))
    dd     = ImageDraw.Draw(dummy)
    bboxes      = [dd.textbbox((0, 0), ln or ' ', font=font) for ln in lines]
    line_widths  = [b[2] - b[0] for b in bboxes]
    line_heights = [b[3] - b[1] for b in bboxes]
    line_offsets = [b[1]        for b in bboxes]   # 字型基線偏移量

    margin  = stroke_width + 4
    img_w   = max(line_widths) + margin * 2 + 10
    img_h   = (sum(line_heights)
               + extra_spacing * max(len(lines) - 1, 0)
               + margin * 2 + 10)

    img  = Image.new('RGBA', (img_w, img_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    y = margin
    for ln, lh, lo in zip(lines, line_heights, line_offsets):
        # 描邊（向各方向偏移 stroke_width 個像素）
        for dx in range(-stroke_width, stroke_width + 1):
            for dy in range(-stroke_width, stroke_width + 1):
                if dx * dx + dy * dy <= stroke_width ** 2:
                    draw.text((margin + dx, y - lo + dy), ln or ' ',
                               font=font, fill=stroke_color)
        # 主體文字
        draw.text((margin, y - lo), ln or ' ', font=font, fill=color)
        y += lh + extra_spacing

    arr = np.array(img)
    return ImageClip(arr, is_mask=False).with_duration(duration)


def make_pil_topic_clip(text, font_path, font_size, color, bg_color,
                         stroke_color, stroke_width, duration):
    """使用 PIL 繪製章節標題（含背景色塊，支援多行自適應換行）。"""
    try:
        font = ImageFont.truetype(font_path, font_size)
    except Exception:
        font = ImageFont.load_default()

    # Apply auto-wrapping to prevent title cut-off
    text = wrap_text_by_width(text, font, max_width=1700)
    lines = text.split('\n') if '\n' in text else [text]
    
    dummy = Image.new('RGBA', (1, 1))
    dd = ImageDraw.Draw(dummy)
    bboxes = [dd.textbbox((0, 0), ln or ' ', font=font) for ln in lines]
    line_widths = [b[2] - b[0] for b in bboxes]
    line_heights = [b[3] - b[1] for b in bboxes]
    line_offsets = [b[1] for b in bboxes]
    
    tw = max(line_widths)
    pad = 16
    th = sum(line_heights) + 12 * max(len(lines) - 1, 0)

    if isinstance(bg_color, tuple) and len(bg_color) == 3:
        bg_fill = bg_color + (230,)
    else:
        bg_fill = bg_color

    img = Image.new('RGBA', (tw + pad * 2, th + pad * 2), bg_fill)
    draw = ImageDraw.Draw(img)

    y = pad
    for ln, lh, lo in zip(lines, line_heights, line_offsets):
        # Left align each line on the background card
        x_offset = pad
        
        for dx in range(-stroke_width, stroke_width + 1):
            for dy in range(-stroke_width, stroke_width + 1):
                if dx * dx + dy * dy <= stroke_width ** 2:
                    draw.text((x_offset + dx, y - lo + dy), ln or ' ', font=font, fill=stroke_color)
        draw.text((x_offset, y - lo), ln or ' ', font=font, fill=color)
        y += lh + 12

    return ImageClip(np.array(img)).with_duration(duration)


def make_crop_zoom_clip(img_path, duration, target_size, zoom_stops_at, radius=48):
    """
    功能：產生固定外框大小的 Ken Burns 縮放影片片段 (支持高雅圓弧角)
    """
    # 載入原始圖片並轉為 RGBA
    pil_img = Image.open(img_path).convert("RGBA")
    
    # 1. 先將原始圖片裁切為正方形 (取中心部分)
    w, h = pil_img.size
    min_side = min(w, h)
    left = (w - min_side) / 2
    top = (h - min_side) / 2
    right = (w + min_side) / 2
    bottom = (h + min_side) / 2
    square_img = pil_img.crop((left, top, right, bottom))

    # 預先繪製圓角遮罩 (黑白二值遮罩)
    mask_im = Image.new("L", (target_size, target_size), 0)
    draw = ImageDraw.Draw(mask_im)
    draw.rounded_rectangle((0, 0, target_size, target_size), radius=radius, fill=255)

    def make_rgba_frame(t):
        # 計算當前的縮放比例 (從 1.3x 漸變到 1.0x)
        if t <= zoom_stops_at:
            scale = 1.3 - (1.3 - 1.0) * (t / zoom_stops_at)
        else:
            scale = 1.0
            
        # 計算當前放大後的尺寸
        cur_size = int(target_size * scale)
        resized_img = square_img.resize((cur_size, cur_size), Image.Resampling.BILINEAR)
        
        # 從放大後的圖片中，裁切出中央固定大小 (target_size x target_size) 的區域
        c_left = (cur_size - target_size) / 2
        c_top = (cur_size - target_size) / 2
        c_right = c_left + target_size
        c_bottom = c_top + target_size
        
        cropped_img = resized_img.crop((c_left, c_top, c_right, c_bottom))
        cropped_img.putalpha(mask_im)
        return np.array(cropped_img)

    # 分離出 RGB 畫面與 Alpha 通道，MoviePy 能完美去背融合
    def rgb_frame(t):
        rgba = make_rgba_frame(t)
        return rgba[:, :, :3]
        
    def mask_frame(t):
        rgba = make_rgba_frame(t)
        return rgba[:, :, 3] / 255.0

    clip = VideoClip(rgb_frame, duration=duration)
    mask_clip = VideoClip(mask_frame, is_mask=True, duration=duration)
    return clip.with_mask(mask_clip)


def generate_videos_from_txt_img_mp3(txt_dir, voice_dir, bg_img_dir, output_file, start_second, topic_index, bg_img_ID, bg_type=0, mode="all", head_type="static_head"):
    """
    核心功能：從指定目錄讀取 .txt 和 .mp3，生成三個同步影片：
    1. 背景影片 (_img)
    2. 綠幕字幕影片 (_sub)
    3. 綠幕頭像影片 (_head) - 採用 PIL 直接合成 + 縮放功能 + 動態座標
    4. "all" : 生成全部影片 (Sub, Head, Img)
    """

    # --- 參數配置區 ---
    background_color = (0, 255, 0)  # 綠幕背景 (用於去背)
    
    import sys
    is_eng = "--eng" in sys.argv
    if is_eng:
        font_ttf = 'Montserrat-Bold.ttf' # 字幕字體 (英文 Montserrat)
    else:
        font_ttf = 'TaipeiSansTCBeta-Regular.ttf' # 字幕字體

    # 1. 定義三種用於顯示字幕的顏色，格式為RGB
    font_color_AA = (162, 242, 202) # 優雅亮薄荷綠
    font_color_BB = (255, 179, 230) # 浅珍珠红
    font_color_CC = (255, 255, 153) # 香檳黃    ``

    font_strok_color = 'black'
    font_strok_width = 2
    txt_font_size = 40 if is_eng else 64     # 配合 2026 字幕字體，中文 64 點，英文 40 點
    extra_line_spacing = 22 # 行與行之間的距離加大 22點

    # Topic (標題) 字幕設定
    topic_font_color = 'white'
    topic_font_strok_color = 'black'
    topic_font_strok_width = 2
    topic_txt_font_size = 56
    topic_font_background_color = (0, 49, 83) # 普魯士藍
    if is_eng:
        topic_font_ttf = 'Montserrat-Bold.ttf'
        topic_txt_font_size = 36  # Set English title size to 36 pixels
    else:
        topic_font_ttf = 'TaipeiSansTCBeta-Bold.ttf'

    max_line = 0    # 0 代表無限制

    # [Claude Comment] : 腳本特殊前綴符號定義：
    # [Claude Comment] :   '<'    → 強制換行 (替換成 \n)
    # [Claude Comment] :   '>>>>' → 宣告新章節標題，不顯示一般字幕
    # [Claude Comment] :   '!!!!' → 跳過字幕顯示 (靜音音效仍播放)
    pattern_new_line = '<'    # 換行符號
    pattern_topic = '>>>>'    # 標題符號
    pattern_no_show = '!!!!'  # 不顯示字幕符號

    pending_duration = 2
    pending_color = (0, 0, 0) # 過場黑畫面顏色

    # 預先定義字幕的位置，起始高度再下降 100 pixels (共下降 200 pixels)
    global string_align
    if string_align == 'center':
        base_string_left = 200
        base_string_top = 650  # 原 550 + 100
        base_string_text_align = 'center'
    else:
        base_string_left = 30
        base_string_top = 700  # 原 600 + 100
        base_string_text_align = 'left'

    # --- 頭像影片配置參數 ---
    # 尋找特定 book_ID 的書籍目錄，以載入頭像
    book_dir = None
    try:
        import re
        # 1. 嘗試從路徑字串中直接比對現有書籍目錄的前綴，例如 "136_20260528_人生只有兩件事"
        for item in os.listdir("."):
            if os.path.isdir(item) and "_" in item:
                prefix = item.split("_")[0]
                if prefix.isdigit() and (prefix in txt_dir or prefix in voice_dir or (bg_img_dir and prefix in bg_img_dir) or (output_file and prefix in output_file)):
                    book_dir = item
                    break
        
        if not book_dir:
            # 2. 正則比對 txt136 / voice136 等數字 ID
            for path_str in [txt_dir, voice_dir, bg_img_dir, output_file]:
                if path_str:
                    match = re.search(r"(\d+)", path_str)
                    if match:
                        tid = match.group(1)
                        for item in os.listdir("."):
                            if os.path.isdir(item) and item.startswith(f"{tid}_"):
                                book_dir = item
                                break
                        if book_dir:
                            break
                            
        if not book_dir and book_ID:
            # 3. 備用方案：比對全域 book_ID
            for item in os.listdir("."):
                if os.path.isdir(item) and item.startswith(f"{book_ID}_"):
                    book_dir = item
                    break
    except Exception as e_find:
        print(f"尋找書籍目錄時出錯: {e_find}")

    photo_dir = os.path.join(book_dir, "photo") if book_dir else None
    stickman_dir = os.path.join(book_dir, "raw", "stickman_green") if book_dir else None

    # 用於安全載入頭像的輔助函式，支援多層級備用
    def resolve_avatar_path(avatar_name, p_dir):
        if p_dir:
            # 1. 優先：專屬書籍目錄下的 photo 資料夾
            p = os.path.join(p_dir, avatar_name)
            if os.path.exists(p):
                return p
        
        # 2. 備用：根目錄 (如果有的話)
        if os.path.exists(avatar_name):
            return avatar_name
            
        # 3. 備用：其他書籍目錄下的 photo 資料夾 (例如 135_... / 133_...)
        for item in os.listdir("."):
            if os.path.isdir(item) and "_" in item:
                candidate = os.path.join(item, "photo", avatar_name)
                if os.path.exists(candidate):
                    return candidate
                    
        # 4. 備用：模板目錄下
        template_p = os.path.join("00_new_poject_template", "photo", avatar_name)
        if os.path.exists(template_p):
            return template_p
            
        return None

    AA_IMG_PATH = resolve_avatar_path("AA.png", photo_dir)
    BB_IMG_PATH = resolve_avatar_path("BB.png", photo_dir)
    CC_IMG_PATH = resolve_avatar_path("CC.png", photo_dir)

    print(f"✓ 頭像載入路徑完成解析：")
    print(f"  - 書籍目錄：{book_dir if book_dir else '未對接'}")
    print(f"  - AA: {AA_IMG_PATH}")
    print(f"  - BB: {BB_IMG_PATH}")
    print(f"  - CC: {CC_IMG_PATH}")

    # 設定頭像目標寬度 (Pixel) - 放大 1.5 倍 (原 150 -> 225)
    head_width = 225

    # 預先計算好的 X 座標 - 無論哪個角色均與字幕左邊對齊
    AA_X = base_string_left
    BB_X = base_string_left
    CC_X = base_string_left

    # 頭像底部和字幕頂部的間距 (pixel)
    Avatar_Sub_offset = 20

    # 初始化頭像狀態變數
    current_avatar_img = None
    current_avatar_x = 0  # 紀錄 X 座標

    # 2A. 預設的字串顏色為：font_color_AA
    current_font_color = font_color_AA
    # ---------------------------

    # --- 配置結束 ---

    # [Claude Comment] : 三條影片軌道的 clip 累積清單，最後再各自 concatenate 輸出
    img_clips = []
    sub_clips = []
    head_clips = []

    # [Claude Comment] : acc_second 追蹤整支影片的累計時間軸，用於計算章節標題的絕對時間戳
    acc_second = start_second
    topic_array = []
    
    # --- 智慧對接：加載「分段生圖腳本.csv」做精確語意插圖匹配 ---
    csv_paragraphs = []
    cleaned_csv_paragraphs = []
    already_triggered_illustrations = set()
    
    if book_dir:
        csv_candidates = [
            os.path.join(book_dir, "raw", "分段生圖腳本.csv"),
            os.path.join(book_dir, "分段生圖腳本.csv")
        ]
        csv_path = None
        for candidate in csv_candidates:
            if os.path.exists(candidate):
                csv_path = candidate
                break
                
        if csv_path:
            import csv
            try:
                with open(csv_path, 'r', encoding='utf-8') as f_csv:
                    reader = csv.reader(f_csv)
                    header = next(reader)
                    for row in reader:
                        if row and len(row) > 1:
                            csv_paragraphs.append(row[1].strip())
                
                # 預先清理 CSV 段落以便做包含性匹配
                def clean_temp_str(s):
                    s = s.replace("。", "").replace("。。", "").replace("。。。", "")
                    s = s.replace(">>>>", "").replace("@@@@", "").replace("<<<<", "")
                    s = s.replace("<", "").replace("\n", "").replace(" ", "").strip()
                    return s
                cleaned_csv_paragraphs = [clean_temp_str(p) for p in csv_paragraphs]
                print(f"✓ 成功讀取插圖設計 CSV: {csv_path}，載入 {len(csv_paragraphs)} 段插圖定位")
            except Exception as e_csv:
                print(f"⚠️ 讀取插圖 CSV 時發生錯誤: {e_csv}")

    # --- 新增：插圖疊加與字幕層配置 ---
    overlay_clips = []
    text_layer_clips = []
    block_count = 0
    BLOCKS_PER_SEGMENT = 10
    IMAGE_DISPLAY_DURATION = 25  # 改為 30 秒
    ZOOM_STOPS_AT = 18           # 18秒內漸漸顯示完整大圖
    TARGET_IMAGE_SIZE = 960       # 從 1024 稍微縮小為 960，右側預留約 20 點空間
    RIGHT_PADDING = 20            # 右側留出 20 點空間
    # -----------------------------

    all_txt_files = [f for f in os.listdir(txt_dir) if not f.startswith('.')]
    all_txt_files.sort()

    topic_text = ""
    # [Claude Comment] : 腳本內容等於 '_bg' 時，表示切換到下一張背景圖片
    pattern_bg_img = '_bg'

    if bg_type == 0:
        # convert bg-image-files from png to jpg
        for i in range(0,100):   # range(0:10) <== 0~9
            image_filename_png = os.path.join(bg_img_dir, f"{i}.png")
            if os.path.exists(image_filename_png):
                convert_png_to_jpg_with_resolution(image_filename_png,(1920, 1080))

        image_filename = os.path.join(bg_img_dir, f"{bg_img_ID}.jpg")
        if not os.path.exists(image_filename):
            image_filename = os.path.join(bg_img_dir, f"{bg_img_ID}.jpeg")

        print("Initial BG Image: " + image_filename)
        resize_image2(image_filename, 'temp.jpg')

    for txt_file in all_txt_files:
        if max_line != 0:
            max_line = max_line - 1
            if max_line == 0:
                break

        if txt_file.endswith(".txt") and not txt_file.startswith("._") and not txt_file.startswith("."):
            base_name = os.path.splitext(txt_file)[0]
            txt_path = os.path.join(txt_dir, txt_file)
            # [Claude Comment] : TTS 音訊檔與腳本 .txt 同名，僅副檔名不同
            mp3_path = os.path.join(voice_dir, f"{base_name}.mp3")

            if not os.path.exists(mp3_path):
                print(f"音訊檔案 {mp3_path} 不存在，跳過 {txt_file}")
                continue

            try:
                with open(txt_path, "r", encoding="utf-8") as f:
                    subtitle_text = f.read().strip()
            except UnicodeDecodeError:
                with open(txt_path, "r", encoding="cp950", errors="ignore") as f:
                    subtitle_text = f.read().strip()

            if subtitle_text == pattern_bg_img:
                if bg_type == 0:
                    image_filename = os.path.join(bg_img_dir, f"{bg_img_ID}.jpg")
                    if not os.path.exists(image_filename):
                        image_filename = os.path.join(bg_img_dir, f"{bg_img_ID}.jpeg")
                    bg_img_ID = bg_img_ID + 1
                    print("===================> 切換背景圖: " + image_filename)
                    resize_image2(image_filename, 'temp.jpg')
                continue

            # --- 解析字幕以更新頭像狀態與字幕顏色 ---
            # [Claude Comment] : 以句首全形句號數量判斷目前說話角色：
            # [Claude Comment] :   '。'   → 角色 AA (天藍色字幕)
            # [Claude Comment] :   '。。' → 角色 BB (珍珠紅字幕)
            # [Claude Comment] :   '。。。'→ 角色 CC (香檳黃字幕)
            # [Claude Comment] :   '@@@@' 或 '<<<< → 隱藏頭像 (過場/特殊段落)
            if subtitle_text.startswith("。。。"):
                current_avatar_img = CC_IMG_PATH
                current_avatar_x = CC_X # 只更新 X 座標
                current_font_color = font_color_CC
                subtitle_text = subtitle_text[3:]
            elif subtitle_text.startswith("。。"):
                current_avatar_img = BB_IMG_PATH
                current_avatar_x = BB_X # 只更新 X 座標
                current_font_color = font_color_BB
                subtitle_text = subtitle_text[2:]
            elif subtitle_text.startswith("。"):
                current_avatar_img = AA_IMG_PATH
                current_avatar_x = AA_X # 只更新 X 座標
                current_font_color = font_color_AA
                subtitle_text = subtitle_text[1:]
            elif subtitle_text.startswith("@@@@") or subtitle_text.startswith("<<<<"):
                current_avatar_img = None
            # ---------------------------------

            # [Claude Comment] : 決定本句 clip 的持續時間與音訊來源：
            # [Claude Comment] :   '>>>>' 章節標題 → 1 秒靜音 (章節標題本身不配音)
            # [Claude Comment] :   '@@@@' 黑幕過場 → pending_duration 秒靜音
            # [Claude Comment] :   其他   → 載入對應 .mp3，以音訊實際長度為準
            if subtitle_text == ">>>>":
                audio_clip = AudioClip(make_silence, duration=1, fps=44100)
                duration = 1
            elif starts_with_pattern(subtitle_text, "@@@@"):
                duration = pending_duration
                audio_clip = AudioClip(make_silence, duration=duration, fps=44100)
            else:
                if not os.path.exists(mp3_path) or os.path.getsize(mp3_path) == 0:
                    print(f"⚠️ 偵測到音訊檔案 {mp3_path} 為空檔或不存在，自動以 1.0 秒靜音替代")
                    duration = 1.0
                    audio_clip = AudioClip(make_silence, duration=duration, fps=44100)
                else:
                    audio_clip = AudioFileClip(mp3_path)
                    duration = audio_clip.duration

            subtitle_text = subtitle_text.replace(pattern_new_line, '\n')

            # --- 2026 新增：插圖分段偵測與疊加 (僅針對字幕影片，支援優化語意匹配) ---
            block_count += 1
            
            should_overlay = False
            seg_id = -1
            
            # 從 CSV 中精確查找當前句子屬於哪一個原始插圖段落
            if csv_paragraphs:
                # 清理當前字串
                def clean_temp_str(s):
                    s = s.replace("。", "").replace("。。", "").replace("。。。", "")
                    s = s.replace(">>>>", "").replace("@@@@", "").replace("<<<<", "")
                    s = s.replace("<", "").replace("\n", "").replace(" ", "").strip()
                    return s
                
                cleaned_current = clean_temp_str(subtitle_text)
                if cleaned_current:
                    for idx, cp in enumerate(cleaned_csv_paragraphs):
                        if cleaned_current in cp:
                            # 找到了對應的原始段落
                            seg_id = idx
                            # 當前段落是這個原始段落的第一句時，才觸發貼圖，避免重複貼圖
                            if seg_id not in already_triggered_illustrations:
                                should_overlay = True
                                already_triggered_illustrations.add(seg_id)
                            break
            
            # 備用方案：若無 CSV 或匹配失敗，則退回到原本的算術每 10 段貼圖模式
            if seg_id == -1:
                if block_count == 4:
                    should_overlay = True
                    seg_id = 0
                elif block_count >= 14 and (block_count - 14) % BLOCKS_PER_SEGMENT == 0:
                    should_overlay = True
                    seg_id = 1 + (block_count - 14) // BLOCKS_PER_SEGMENT
                
            if should_overlay and seg_id >= 0:
                img_path = None
                # 參考 bg_image/bg{ID} 目錄下的圖檔，支援多種格式
                for ext in ['.jpeg', '.jpg', '.png']:
                    p = os.path.join(bg_img_dir, f"{seg_id}{ext}")
                    if os.path.exists(p):
                        img_path = p
                        break
                
                if img_path:
                    print(f"段落 {block_count}: 語意對應插圖成功！疊加圖片 {img_path} (套用 Ken Burns 1.3x -> 1.0x 縮放動畫)")
                    # 導入優化：套用 48 點圓角遮罩與 20px 右側留空，尺寸稍微縮小至 960x960
                    ov_clip = make_crop_zoom_clip(img_path, IMAGE_DISPLAY_DURATION, TARGET_IMAGE_SIZE, ZOOM_STOPS_AT, radius=48)
                    pos_x = 1920 - RIGHT_PADDING - TARGET_IMAGE_SIZE  # 1920 - 20 - 960 = 940
                    pos_y = 540 - TARGET_IMAGE_SIZE // 2            # 60
                    ov_clip = ov_clip.with_position((pos_x, pos_y))
                    ov_clip = ov_clip.with_start(acc_second)
                    overlay_clips.append(ov_clip)
            # -----------------------------------------------

            # --- Sub影片 (字幕) 製作 ---
            # [Claude Comment] : 2026 重構：分離背景與文字層，確保字幕在最頂層
            
            # 1. 綠幕背景與音軌 (用於串接)
            green_bg = ColorClip(size=(1920, 1080), color=background_color, duration=duration).with_audio(audio_clip)
            sub_clips.append(green_bg)

            # 2. 獨立字幕層 (text_layer_clips)
            if starts_with_pattern(subtitle_text, pattern_topic):
                topic_text = subtitle_text.replace(pattern_topic, "")
                print("***** Topic 發現: " + subtitle_text + " 開始時間 = " + format_seconds_to_hms(acc_second))
                topic_array.append(Topic(topic_text, acc_second, format_seconds_to_hms(acc_second)))
            else:
                string_left = base_string_left
                string_top = base_string_top
                string_text_align = base_string_text_align

                if not starts_with_pattern(subtitle_text, pattern_no_show) and not starts_with_pattern(subtitle_text, '@@@@'):
                    t_clip = make_pil_subtitle_clip(
                        text             = subtitle_text,
                        font_path        = font_ttf,
                        font_size        = txt_font_size,
                        color            = current_font_color,
                        stroke_color     = font_strok_color,
                        stroke_width     = font_strok_width,
                        extra_spacing    = extra_line_spacing,
                        duration         = duration,
                    ).with_position((string_left, string_top)) \
                     .with_start(acc_second)
                    text_layer_clips.append(t_clip)

            # 3. 獨立標題層
            if topic_text and not starts_with_pattern(subtitle_text, '@@@@'):
                top_clip = make_pil_topic_clip(
                    text         = topic_text,
                    font_path    = topic_font_ttf,
                    font_size    = topic_txt_font_size,
                    color        = topic_font_color,
                    bg_color     = topic_font_background_color,
                    stroke_color = topic_font_strok_color,
                    stroke_width = topic_font_strok_width,
                    duration     = duration,
                ).with_start(acc_second)
                if is_eng:
                    top_clip = top_clip.with_position((0, 0))
                text_layer_clips.append(top_clip)


            # --- Img影片 (背景) 製作 ---
            if bg_type == 0:
                if starts_with_pattern(subtitle_text, '@@@@'):
                    # [Claude Comment] : 過場段落使用純黑畫面，避免背景圖跳切造成視覺不連貫
                    img_video_clip = ColorClip(size=(1920, 1080), color=pending_color, duration=duration)
                else:
                    # [Claude Comment] : 從 temp.jpg 讀取當前背景圖，temp.jpg 會在遇到 '_bg' 指令時更新
                    bg_clip = ImageClip('temp.jpg').with_duration(duration)
                    img_video_clip = CompositeVideoClip([bg_clip], size=(1920, 1080)).with_duration(duration)

                img_clips.append(img_video_clip)


            # --- 頭像影片 (Head) 製作 (PIL 合成 + 縮放 或 動態綠幕) ---

            if head_type == "dynamic_body":
                if subtitle_text == ">>>>" or starts_with_pattern(subtitle_text, "@@@@"):
                    # 系統符號或轉場過場：使用純綠幕
                    head_video_clip = ColorClip(size=(1920, 1080), color=background_color, duration=duration)
                else:
                    stickman_mp4_path = None
                    if stickman_dir:
                        stickman_mp4_path = os.path.join(stickman_dir, f"{base_name}.mp4")
                    
                    if stickman_mp4_path and os.path.exists(stickman_mp4_path):
                        clip = VideoFileClip(stickman_mp4_path)
                        if clip.h != 1080:
                            clip = clip.resized(height=1080)
                        
                        if clip.duration >= duration:
                            clip_processed = clip.subclipped(0, duration)
                        else:
                            clip_processed = clip.with_effects([Loop(duration=duration)])
                        
                        # 建立 1920x1080 的綠幕畫布並將影片置中放置，以確保解析度完全一致，防止畫面錯位
                        green_canvas = ColorClip(size=(1920, 1080), color=background_color, duration=duration)
                        pos_x = (1920 - clip_processed.w) // 2
                        positioned_clip = clip_processed.with_position((pos_x, 0))
                        head_video_clip = CompositeVideoClip([green_canvas, positioned_clip], size=(1920, 1080))
                    else:
                        print(f"⚠️ 找不到動態綠幕影片 {stickman_mp4_path if stickman_mp4_path else ''}，使用綠幕背景替代")
                        head_video_clip = ColorClip(size=(1920, 1080), color=background_color, duration=duration)
            else:
                # [Claude Comment] : 以純綠底 PIL Image 作為頭像軌道畫布，後製時可色鍵去背
                base_img = Image.new("RGB", (1920, 1080), background_color)

                if current_avatar_img is not None:
                    try:
                        avatar_pil = Image.open(current_avatar_img).convert("RGBA")

                        # 裁切成正方形 (取中間部分)
                        min_side = min(avatar_pil.size)
                        left = (avatar_pil.width - min_side) / 2
                        top = (avatar_pil.height - min_side) / 2
                        right = (avatar_pil.width + min_side) / 2
                        bottom = (avatar_pil.height + min_side) / 2
                        avatar_pil = avatar_pil.crop((left, top, right, bottom))

                        # [Claude Comment] : 縮放至目標大小 (正方形)
                        avatar_pil = avatar_pil.resize((head_width, head_width), Image.Resampling.LANCZOS)
                        new_height = head_width
                        
                        # 建立圓形遮罩
                        mask = Image.new('L', (head_width, head_width), 0)
                        draw = ImageDraw.Draw(mask)
                        draw.ellipse((0, 0, head_width, head_width), fill=255)
                        
                        # 若原圖有透明度，將原本的 alpha 通道與圓形遮罩做交集 (darker)
                        _, _, _, alpha = avatar_pil.split()
                        new_alpha = ImageChops.darker(alpha, mask)
                        avatar_pil.putalpha(new_alpha)

                        # [20260306 update] 動態計算頭像 Y 座標：確保所有頭像的「左下角」對齊
                        # 因為 base_string_top 現在是絕對固定的，所以這裡算出來的底部 Y 座標也會絕對固定
                        # 公式：字幕第一行 Y 座標 (base_string_top) - 頭像縮放後高度 (new_height) - 10 pixels 距離
                        avatar_y = base_string_top - new_height - Avatar_Sub_offset
                        current_avatar_pos = (current_avatar_x, avatar_y)

                        # [Claude Comment] : 使用 RGBA 的 alpha 通道作為遮罩，正確貼合帶透明度的 PNG 頭像
                        base_img.paste(avatar_pil, current_avatar_pos, avatar_pil)

                    except Exception as e:
                        print(f"警告：無法載入或處理頭像圖片 {current_avatar_img}: {e}")

                # [Claude Comment] : 將 PIL Image 轉為 numpy array 後建立 MoviePy ImageClip
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

    # [Claude Comment] : 頭像影片不含音訊 (audio=False)，後製合成時才與字幕軌道混音
    if mode in ["all", "head"]:
        final_head_clip = concatenate_videoclips(head_clips, method="chain")
        logger_head = TimeTrackingLogger(os.path.basename(output_file_head))
        final_head_clip.write_videofile(output_file_head, fps=24, codec='libx264', audio=False, threads=8, logger=logger_head)
        elapsed = int(time.time() - logger_head.start_time)
        print(f"\n已生成頭像影片: {output_file_head}，總共耗時: {elapsed} 秒")

    # [Claude Comment] : 2026 更新：使用 CompositeVideoClip 組合綠幕、插圖與字幕層
    if mode in ["all", "sub"]:
        final_sub_bg = concatenate_videoclips(sub_clips, method="chain")
        final_sub_clip = CompositeVideoClip([final_sub_bg] + overlay_clips + text_layer_clips)
        logger_sub = TimeTrackingLogger(os.path.basename(output_file_sub))
        final_sub_clip.write_videofile(output_file_sub, fps=24, codec='libx264', audio_codec='aac', threads=8, logger=logger_sub)
        elapsed = int(time.time() - logger_sub.start_time)
        print(f"\n已生成字幕影片: {output_file_sub}，總共耗時: {elapsed} 秒")

    if mode in ["all", "img"]:
        if bg_type == 0:
            final_img_clip = concatenate_videoclips(img_clips, method="chain")
        else:
            # [Claude Comment] : bg_type=1 時，將 default_bg_video 重複循環至與內容等長，作為背景影片
            global default_bg_video
            total_duration = acc_second - start_second
            bg_video = VideoFileClip(default_bg_video).resized((1920, 1080), Image.LANCZOS)
            loops = int(total_duration / bg_video.duration) + 1
            final_img_clip = concatenate_videoclips([bg_video] * loops).with_duration(total_duration)
            final_img_clip = final_img_clip.without_audio()

        logger_img = TimeTrackingLogger(os.path.basename(output_file_img))
        final_img_clip.write_videofile(output_file_img, fps=24, codec='libx264', audio=False, threads=8, logger=logger_img)
        elapsed = int(time.time() - logger_img.start_time)
        print(f"\n已生成背景影片: {output_file_img}，總共耗時: {elapsed} 秒")


    # [Claude Comment] : 回傳章節數、目前累計秒數(+1 防止下一段 start_second 重疊)、背景圖 ID 游標
    return topic_num, int(acc_second) + 1, bg_img_ID


def create_random_video_from_directory(directory, target_duration, output_file):
    """
    功能：從目錄隨機選取 .mp4，拼接成指定長度的影片。
    """
    try:
        video_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.mp4') and not f.startswith('.')]

        if not video_files:
            print(f"目錄 {directory} 中沒有找到任何 .mp4 文件！")
            return

        clips = []
        total_duration = 0
        loop_count = 0

        # [Claude Comment] : 外層 while 循環保證影片總長超過 target_duration；
        # [Claude Comment] : 每輪重新洗牌，避免重複順序。
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
        # [Claude Comment] : 直向（豎版）圖：等比縮放至接近 1080px 高，不強制拉伸
        print(" 豎直圖像處理")
        new_height = target_height - 10
        new_width = int(original_width * (target_height / original_height))

        print(f"new height: {new_height}, new width: {new_width}")
        img_resized = img.resize((new_width, new_height), Image.LANCZOS)

        # [Claude Comment] : 底色使用普魯士藍 (0, 49, 83)，與字幕標題背景色一致，視覺風格統一
        canvas = Image.new("RGB", (target_width, target_height), (0, 49, 83))

        # [Claude Comment] : -100 讓圖片稍微往左偏移，為右側字幕留出更多空間
        x_offset = (target_width - new_width) - 100
        print(f"x_offset = {x_offset}")
        canvas.paste(img_resized, (x_offset, 0))

        try:
            canvas.save(output_path, "JPEG")
            print("OKOK")
        except Exception as e:
            print(e)
    else:
        # [Claude Comment] : 橫向寬圖：直接等比縮放填滿 1920x1080
        print(" 一般寬圖像處理")
        resized_img = img.resize(resolution, Image.LANCZOS)
        resized_img.save(output_path)

    print(f"處理完成，已保存至: {output_path}")


def create_video_from_images_with_ZOOMING(directory, zoom_scale, t1, t2, output_file):
    """
    功能：Ken Burns 效果，隨機播放圖片並帶有放大 (Zoom) 特效。
    """
    image_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.jpg') and not f.startswith('.')]

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

    # [Claude Comment] : 計算需要幾張圖片才能填滿 t2 秒（每張顯示 t1 秒）
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

        # [Claude Comment] : make_frame 是 MoviePy 的逐幀渲染回呼函式；
        # [Claude Comment] : img_np=img_np 使用預設參數捕捉當前迴圈變數，避免 Python closure 捕捉最後一個值的陷阱
        def make_frame(t, img_np=img_np):
            # [Claude Comment] : 隨時間 t 線性增大縮放比例，模擬緩慢推進的 Ken Burns 效果
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
        image_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.jpg') and not f.startswith('.')]

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
            # [Claude Comment] : mix_mode=True 時跳過淡入淡出，直接硬切（適合後製混剪使用）
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
        audio_files = [os.path.join(directory, f) for f in os.listdir(directory) if (f.endswith('.m4a') or f.endswith('.mp3')) and not f.startswith('.')]

        if not audio_files:
            print(f"目錄 {directory} 中沒有找到任何 .mp3 或 m4a 文件！")
            return

        random.shuffle(audio_files)
        # [Claude Comment] : first_audio 若有指定，強制插入為第一首，確保片頭音樂可控
        if first_audio is not None:
            audio_files.insert(0, first_audio)

        clips = []
        total_duration = 0

        # [Claude Comment] : 外層 while 確保不足 t2 秒時會重新循環播放所有音訊
        while total_duration < t2:
            for audio_file in audio_files:
                clip = AudioFileClip(audio_file)
                clip_duration = clip.duration

                clip = AudioFadeOut(5).apply(clip)
                clip = AudioFadeIn(2).apply(clip)

                print(format_seconds_to_hms(total_duration) + " " + os.path.basename(audio_file.strip()))

                # [Claude Comment] : 若加入此曲後超出目標長度，仍加入（允許輕微超出），然後立即停止
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

        logger_audio = TimeTrackingLogger(os.path.basename(output_file))
        final_audio.write_audiofile(output_file, codec="libmp3lame", logger=logger_audio)
        elapsed = int(time.time() - logger_audio.start_time)
        print(f"\n音頻已成功生成：{output_file}，總共耗時: {elapsed} 秒")

    except Exception as e:
        print(f"處理音頻時出错: {e}")


def create_countdown_video(minutes, seconds, font, fontsize, color, position, output_file="countdown.mp4"):
    """
    功能：產生倒數計時影片，綠底 (00:00 時會閃爍)。
    """
    total_seconds = minutes * 60 + seconds
    resolution = (300, 100)
    bg_color = (0, 255, 0)  # 綠底

    # [Claude Comment] : 計時結束後額外產生 300 秒的閃爍動畫，提示觀眾節目即將開始
    flash_counter = 300

    background = ColorClip(size=resolution, color=bg_color, duration=total_seconds + flash_counter)

    def make_frame(t):
        if t < total_seconds:
            remaining = int(total_seconds - t)
            mm = remaining // 60
            ss = remaining % 60
            time_text = f"{mm:02}:{ss:02}"
        else:
            # [Claude Comment] : 倒數結束後每秒交替顯示 "00:00" 與空字串，形成閃爍效果
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
book_ID = '146'
clip_number = 1         # 總共分為幾段 (B77-1, B77-2, B77-3)
string_align = 'left'   # 'center': 靠中偏右; 'left': 對齊左邊邊框

# bg_img_type = 0 : 使用bg_image目錄下的圖檔 (例如： "bg_image/bg_126/0.jpg....")，製作背景影片
# bg_img_type = 1 : 依據最後影片的長度，反覆播放 default_bg_video 填滿背景影片
BG_Type = 1

# 渲染模式選擇：
# 'all'  : 生成全部影片 (Sub, Head, Img)
# 'sub'  : 僅生成綠幕字幕與插圖貼圖影片 (output1_sub.mp4)
# 'head' : 僅生成綠幕頭像影片 (output1_head.mp4)
# 'img'  : 僅生成背景影片 (output1_img.mp4)
render_mode = 'all'

# 頭像影片類型選擇：
# 'static_head' : 原本的 PIL 圓形頭像疊加
# 'dynamic_body': 載入 raw/stickman_green 的綠幕動態火柴人影片
head_type = 'dynamic_body'

# [Claude Comment] : 每段影片可指定不同的循環背景影片，目前四段皆使用同一個黑膠唱盤動畫
default_bg_video = 'data/背景影片/台幣.mp4'
default_bg_video2 = 'data/黑膠2.mp4'
default_bg_video3 = 'data/黑膠2.mp4'
default_bg_video4 = 'data/黑膠2.mp4'

import sys
is_eng = "--eng" in sys.argv

if is_eng:
    if book_ID == '135':
        txt_dir = "./135_20260528_量子狗屎/raw/txt135_E"
        voice_dir = "./135_20260528_量子狗屎/raw/voice135_E"
        bg_img_dir = "./135_20260528_量子狗屎/photo/bg135"
        output_video = "./135_20260528_量子狗屎/output/output135_E.mp4"
        output_audio = "./135_20260528_量子狗屎/output/output135_E.mp3"
        os.makedirs("./135_20260528_量子狗屎/output", exist_ok=True)
    else:
        book_ID = '134'
        txt_dir = "./134_20260527_你的生命是一場喜樂的量子遊戲/raw/txt134_E"
        voice_dir = "./134_20260527_你的生命是一場喜樂的量子遊戲/raw/voice134_E"
        bg_img_dir = "./134_20260527_你的生命是一場喜樂的量子遊戲/photo/bg134"
        output_video = "./134_20260527_你的生命是一場喜樂的量子遊戲/AV/output134_E.mp4"
        output_audio = "./134_20260527_你的生命是一場喜樂的量子遊戲/AV/output134_E.mp3"
else:
    def find_book_dir(book_id):
        for item in os.listdir('.'):
            if os.path.isdir(item) and (item.startswith(f"{book_id}_") or item.startswith(f"B{book_id}_") or item.startswith(f"1{book_id}_") or item.startswith(f"{book_id}-") or item.startswith(f"B{book_id}-") or item.startswith(f"1{book_id}-")):
                return item
        raise FileNotFoundError(f"Cannot find book directory starting with {book_id}_")
    
    book_dir = find_book_dir(book_ID)
    txt_dir = f"./{book_dir}/raw/txt{book_ID}"
    voice_dir = f"./{book_dir}/raw/voice{book_ID}"
    bg_img_dir = f"./{book_dir}/photo/bg{book_ID}"
    os.makedirs(f"./{book_dir}/output", exist_ok=True)
    output_video = f"./{book_dir}/output/output1.mp4"
    output_audio = f"./{book_dir}/output/output{book_ID}.mp3"

# 產生第 1 段影片
# [Claude Comment] : start_second=0 表示第 1 段從 0 秒開始；topic_index=0、bg_img_ID=0 皆從頭計數
topic_num1, video_length1, start_bg_img_ID = \
    generate_videos_from_txt_img_mp3(
        txt_dir,
        voice_dir,
        bg_img_dir,
        output_video,
        0, 0, 0, bg_type=BG_Type, mode=render_mode, head_type=head_type
    )
video_length4 = video_length1

'''
# 產生第 1 段影片
# [Claude Comment] : start_second=0 表示第 1 段從 0 秒開始；topic_index=0、bg_img_ID=0 皆從頭計數
topic_num1, video_length1, start_bg_img_ID = \
    generate_videos_from_txt_img_mp3(
        "./腳本/txt"+book_ID+"-1",
        "./腳本/voice"+book_ID+"-1",
        "./bg_image/bg"+book_ID,
        "./output1.mp4",
        0, 0, 0, bg_type=BG_Type, mode=render_mode
    )

# 產生第 2 段影片
# [Claude Comment] : 將第 1 段的結束秒數傳入作為第 2 段的 start_second，確保章節時間戳連續
default_bg_video = default_bg_video2
topic_num2, video_length2, start_bg_img_ID = \
        generate_videos_from_txt_img_mp3(
            "./腳本/txt"+book_ID+"-2",
            "./腳本/voice"+book_ID+"-2",
            "./bg_image/bg"+book_ID,
            "./output2.mp4",
            video_length1, topic_num1, start_bg_img_ID, bg_type=BG_Type, mode=render_mode
        )

# 產生第 3 段影片
default_bg_video = default_bg_video3
video_length3 = video_length2
if clip_number >= 3:
    topic_num3, video_length3, start_bg_img_ID = \
            generate_videos_from_txt_img_mp3(
                "./腳本/txt"+book_ID+"-3",
                "./腳本/voice"+book_ID+"-3",
                "./bg_image/bg"+book_ID,
                "./output3.mp4",
                video_length2, topic_num1+topic_num2, start_bg_img_ID, bg_type=BG_Type, mode=render_mode
            )

# 產生第 4 段影片
video_length4 = video_length3
default_bg_video = default_bg_video4
if clip_number >= 4:
    topic_num4, video_length4, start_bg_img_ID = \
            generate_videos_from_txt_img_mp3(
                "./腳本/txt"+book_ID+"-4",
                "./腳本/voice"+book_ID+"-4",
                "./bg_image/bg"+book_ID,
                "./output4.mp4",
                video_length3, topic_num1+topic_num2+topic_num3, start_bg_img_ID, bg_type=BG_Type, mode=render_mode
            )
'''

# 生成總背景音樂
# [Claude Comment] : 以最後一段的結束時間 video_length4 為目標長度，生成一整支對應的背景音樂檔
create_audio_from_mp3s(None, "./bg_mp3", video_length4, output_audio)
