import os
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

def create_thumbnail():
    # 檔案路徑設定
    bg_path = "129_20260508_外資這樣買半導體股/photo/Gemini_背景縮圖4.png"
    book_path = "129_20260508_外資這樣買半導體股/photo/中文封面.jpeg"
    output_path = "129_20260508_外資這樣買半導體股/photo/youtube_thumbnail.png"
    font_path = "TaipeiSansTCBeta-Bold.ttf"
    
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
        # Background is wider, scale by height
        new_height = THUMB_HEIGHT
        new_width = int(new_height * bg_ratio)
    else:
        # Background is taller, scale by width
        new_width = THUMB_WIDTH
        new_height = int(new_width / bg_ratio)
        
    bg_img = bg_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    # Center crop
    left = (new_width - THUMB_WIDTH) / 2
    top = (new_height - THUMB_HEIGHT) / 2
    right = (new_width + THUMB_WIDTH) / 2
    bottom = (new_height + THUMB_HEIGHT) / 2
    bg_img = bg_img.crop((left, top, right, bottom))
    
    # 建立最終畫布
    canvas = Image.new("RGBA", (THUMB_WIDTH, THUMB_HEIGHT), (0,0,0,255))
    canvas.paste(bg_img, (0,0))
    
    # 2. 處理書籍封面 (右側、角度、60%透明度)
    print("載入並處理書籍封面...")
    if os.path.exists(book_path):
        book_img = Image.open(book_path).convert("RGBA")
        
        # 調整封面大小，讓它佔據畫面右側一定比例
        target_book_height = int(THUMB_HEIGHT * 0.75) # 高度佔畫面的 75%
        book_ratio = book_img.width / book_img.height
        target_book_width = int(target_book_height * book_ratio)
        book_img = book_img.resize((target_book_width, target_book_height), Image.Resampling.LANCZOS)
        
        # 套用 60% 透明度 (153 / 255)
        alpha = book_img.split()[3]
        alpha = ImageEnhance.Brightness(alpha).enhance(0.6)
        book_img.putalpha(alpha)
        
        # 旋轉圖片
        rotate_angle = 12 # 傾斜角度
        book_img = book_img.rotate(rotate_angle, resample=Image.Resampling.BICUBIC, expand=True)
        
        # 放置於右側
        # 計算右側座標，讓封面貼齊偏右下
        book_x = THUMB_WIDTH - book_img.width - 50
        book_y = THUMB_HEIGHT - book_img.height - 50
        
        canvas.paste(book_img, (book_x, book_y), book_img)
    else:
        print(f"警告：找不到封面圖 {book_path}")
        
    # 3. 繪製文字
    print("繪製標題與副標題...")
    draw = ImageDraw.Draw(canvas)
    
    # 檢查字體
    if not os.path.exists(font_path):
        print(f"警告：找不到字體 {font_path}，將使用預設字體。")
        font_main = ImageFont.load_default()
        font_sub = ImageFont.load_default()
    else:
        # 設定極大字體以符合 YouTube 縮圖風格
        font_main = ImageFont.truetype(font_path, 160)
        font_sub = ImageFont.truetype(font_path, 100)
        
    main_title = "半導體股票操作手冊"
    sub_title = "外資主力の"
    
    # 文字位置參數
    left_margin = 80
    bottom_margin = 80
    
    # 測量文字大小，以計算垂直排列
    # 使用 textbbox 獲取精確尺寸
    main_bbox = draw.textbbox((0, 0), main_title, font=font_main)
    main_h = main_bbox[3] - main_bbox[1]
    
    sub_bbox = draw.textbbox((0, 0), sub_title, font=font_sub)
    sub_h = sub_bbox[3] - sub_bbox[1]
    
    # 計算 Y 座標
    main_y = THUMB_HEIGHT - bottom_margin - main_h - 40 # 預留下方邊距與字體基線偏移
    sub_y = main_y - sub_h - 30 # 在主標題上方
    
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
              
    # 4. 輸出最終縮圖
    # 將 RGBA 轉回 RGB 以儲存為 JPG (或是直接存 PNG)
    final_output = canvas.convert("RGB")
    final_output.save(output_path, "PNG")
    print(f"縮圖已成功生成並儲存至：{output_path}")
    
if __name__ == "__main__":
    create_thumbnail()
