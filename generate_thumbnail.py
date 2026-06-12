import os
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

def find_book_dir(book_id):
    for item in os.listdir('.'):
        if os.path.isdir(item) and (item.startswith(f"{book_id}_") or item.startswith(f"B{book_id}_") or item.startswith(f"1{book_id}_")):
            return item
    raise FileNotFoundError(f"Cannot find book directory starting with {book_id}_")

def create_thumbnail():
    # 檔案路徑設定
    book_id = "141"
    book_dir = find_book_dir(book_id)
    info_path = os.path.join(book_dir, "raw", "info.txt")
    bg_path = os.path.join(book_dir, "photo", "縮圖背景.png")
    
    # 支援中英文及多種副檔名封面偵測
    book_paths = [
        os.path.join(book_dir, "photo", "原文封面.png"),
        os.path.join(book_dir, "photo", "原文封面.jpg"),
        os.path.join(book_dir, "photo", "原文封面.jpeg"),
        os.path.join(book_dir, "photo", "中文封面.jpeg"),
        os.path.join(book_dir, "photo", "中文封面.jpg"),
        os.path.join(book_dir, "photo", "中文封面.png")
    ]
    book_path = None
    for bp in book_paths:
        if os.path.exists(bp):
            book_path = bp
            break
    
    output_path = os.path.join(book_dir, "photo", "youtube_thumbnail.png")
    font_path = "TaipeiSansTCBeta-Bold.ttf"
    
    # 預設標題與副標題
    main_title = "萬曆(中、日、韓)朝鮮戰爭"
    sub_title = "豐臣秀吉的最後野望"
    
    # 從 info.txt 解析縮圖標題
    if os.path.exists(info_path):
        print(f"解析 {info_path} 中的縮圖標題...")
        try:
            with open(info_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            in_section = False
            for line in lines:
                line = line.strip()
                if "【縮圖標題】" in line:
                    in_section = True
                    continue
                if in_section and line.startswith("【"):
                    break
                if in_section and line:
                    if "第一行" in line or "第一句" in line:
                        parts = line.split("：", 1)
                        if len(parts) == 1:
                            parts = line.split(":", 1)
                        if len(parts) == 2:
                            sub_title = parts[1].strip()
                    elif "第二行" in line or "第二句" in line:
                        parts = line.split("：", 1)
                        if len(parts) == 1:
                            parts = line.split(":", 1)
                        if len(parts) == 2:
                            main_title = parts[1].strip()
            print(f"解析成功：副標題=[{sub_title}], 主標題=[{main_title}]")
        except Exception as e:
            print(f"解析 info.txt 失敗，使用預設值: {e}")

    # 尺寸與參數
    THUMB_WIDTH = 1920
    THUMB_HEIGHT = 1080
    
    # 1. 處理背景圖片
    print("載入並處理背景圖片...")
    if not os.path.exists(bg_path):
        print(f"錯誤：找不到背景圖 {bg_path}")
        return
        
    bg_img = Image.open(bg_path).convert("RGBA")
    # Resize and crop to fill 1920x1080
    bg_ratio = bg_img.width / bg_img.height
    target_ratio = THUMB_WIDTH / THUMB_HEIGHT
    
    if bg_ratio > target_ratio:
        new_height = THUMB_HEIGHT
        new_width = int(new_height * bg_ratio)
    else:
        new_width = THUMB_WIDTH
        new_height = int(new_width / bg_ratio)
        
    bg_img = bg_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    left = (new_width - THUMB_WIDTH) / 2
    top = (new_height - THUMB_HEIGHT) / 2
    right = (new_width + THUMB_WIDTH) / 2
    bottom = (new_height + THUMB_HEIGHT) / 2
    bg_img = bg_img.crop((left, top, right, bottom))
    
    # 建立最終畫布
    canvas = Image.new("RGBA", (THUMB_WIDTH, THUMB_HEIGHT), (0,0,0,255))
    canvas.paste(bg_img, (0,0))
    
    # 3. 測量文字大小以進行排版
    print("測量標題與副標題尺寸...")
    if not os.path.exists(font_path):
        print(f"警告：找不到字體 {font_path}，將使用預設字體。")
        font_main = ImageFont.load_default()
        font_sub = ImageFont.load_default()
    else:
        font_main = ImageFont.truetype(font_path, 200)
        font_sub = ImageFont.truetype(font_path, 78)
        
    # 文字位置參數
    left_margin = 80
    max_text_width = 1180
    bottom_margin = 80
    
    temp_draw = ImageDraw.Draw(canvas)
    if os.path.exists(font_path):
        main_size = 200
        while main_size > 118:
            font_main = ImageFont.truetype(font_path, main_size)
            bbox = temp_draw.textbbox((0, 0), main_title, font=font_main, stroke_width=12)
            if bbox[2] - bbox[0] <= max_text_width:
                break
            main_size -= 6
        sub_size = 78
        while sub_size > 50:
            font_sub = ImageFont.truetype(font_path, sub_size)
            bbox = temp_draw.textbbox((0, 0), sub_title, font=font_sub, stroke_width=8)
            if bbox[2] - bbox[0] <= max_text_width:
                break
            sub_size -= 4

    main_bbox = temp_draw.textbbox((0, 0), main_title, font=font_main)
    main_h = main_bbox[3] - main_bbox[1]
    
    sub_bbox = temp_draw.textbbox((0, 0), sub_title, font=font_sub)
    sub_h = sub_bbox[3] - sub_bbox[1]
    
    # 計算 Y 座標
    main_y = THUMB_HEIGHT - bottom_margin - main_h - 40
    sub_y = main_y - sub_h - 30
    
    # 2. 處理書籍封面 (無旋轉、80%不透明度、置於右下、下方與標題對齊)
    print("載入並處理書籍封面...")
    if os.path.exists(book_path):
        book_img = Image.open(book_path).convert("RGBA")
        
        # 調整封面大小，高度佔 58%，避免壓到較長的縮圖標題
        target_book_height = int(THUMB_HEIGHT * 0.58)
        book_ratio = book_img.width / book_img.height
        target_book_width = int(target_book_height * book_ratio)
        book_img = book_img.resize((target_book_width, target_book_height), Image.Resampling.LANCZOS)
        
        # 套用 80% 不透明度
        alpha = book_img.split()[3]
        alpha = ImageEnhance.Brightness(alpha).enhance(0.80)
        book_img.putalpha(alpha)
        
        # 放置於靠近右下角，下方與主標題文字下方對齊
        book_x = THUMB_WIDTH - book_img.width - 80 # 靠右下偏 80px 邊距
        book_y = (main_y + main_bbox[3]) - book_img.height
        
        print(f"書封位置：x={book_x}, y={book_y}")
        canvas.paste(book_img, (book_x, book_y), book_img)
    else:
        print(f"警告：找不到封面圖 {book_path}")
        
    # 4. 繪製文字
    print("繪製標題與副標題...")
    draw = ImageDraw.Draw(canvas)
    
    # 繪製副標題 (白色字體 + 黑色粗邊框 + 陰影效果)
    shadow_offset = 6
    stroke_width = 8
    
    # 陰影
    draw.text((left_margin + shadow_offset, sub_y + shadow_offset), sub_title, font=font_sub, fill=(0,0,0,180))
    # 文字本體與邊框
    draw.text((left_margin, sub_y), sub_title, font=font_sub, fill=(255, 255, 255, 255), 
              stroke_width=stroke_width, stroke_fill=(0, 0, 0, 255))
              
    # 繪製主標題 (亮黃色字體 + 黑色粗邊框 + 陰影效果)
    shadow_offset_main = 10
    stroke_width_main = 12
    main_color = (255, 220, 0, 255) # 鮮豔的 YouTube 黃
    
    # 陰影
    draw.text((left_margin + shadow_offset_main, main_y + shadow_offset_main), main_title, font=font_main, fill=(0,0,0,200))
    # 文字本體與邊框
    draw.text((left_margin, main_y), main_title, font=font_main, fill=main_color, 
              stroke_width=stroke_width_main, stroke_fill=(0, 0, 0, 255))
              
    # 5. 輸出最終縮圖
    final_output = canvas.convert("RGB")
    final_output.save(output_path, "PNG")
    print(f"縮圖已成功重新生成並儲存至：{output_path}")
    
if __name__ == "__main__":
    create_thumbnail()
