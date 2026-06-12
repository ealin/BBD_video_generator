import os
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

def create_english_thumbnail():
    # File Paths
    project_dir = "134_20260527_你的生命是一場喜樂的量子遊戲"
    bg_path = os.path.join(project_dir, "photo/縮圖背景.png")
    output_path = os.path.join(project_dir, "photo/youtube_thumbnail_E.png")
    
    # Fonts in root directory
    font_main_path = "Montserrat-Bold.ttf"
    font_sub_path = "Montserrat-SemiBold.ttf"
    
    # 1. Determine Cover Image (English cover first, otherwise Chinese)
    book_candidates = [
        os.path.join(project_dir, "photo/原文封面.jpg"),
        os.path.join(project_dir, "photo/英文封面.jpg"),
        os.path.join(project_dir, "photo/english_cover.jpg"),
        os.path.join(project_dir, "photo/english_cover.png"),
        os.path.join(project_dir, "photo/中文封面.jpg"), # fallback
    ]
    
    book_path = None
    for candidate in book_candidates:
        if os.path.exists(candidate):
            book_path = candidate
            break
            
    if book_path:
        print(f"Using cover image: {book_path}")
    else:
        print("Warning: No cover image found!")

    # English Titles
    sub_title = "A Quantum Thinking Guide"
    main_title_line1 = "YOUR THOUGHTS ARE"
    main_title_line2 = "CREATING REALITY"

    # Dimensions
    THUMB_WIDTH = 1920
    THUMB_HEIGHT = 1080
    
    # 1. Load Background Image
    print("Loading and processing background image...")
    if not os.path.exists(bg_path):
        print(f"Error: Background image not found at {bg_path}")
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
    
    # Create final canvas
    canvas = Image.new("RGBA", (THUMB_WIDTH, THUMB_HEIGHT), (0,0,0,255))
    canvas.paste(bg_img, (0,0))
    
    # 2. Text Sizing & Fonts
    print("Setting up fonts and measuring text size...")
    # Default sizes
    main_font_size = 110
    sub_font_size = 55
    
    if not os.path.exists(font_main_path) or not os.path.exists(font_sub_path):
        print("Warning: Montserrat fonts not found, using default fonts.")
        font_main = ImageFont.load_default()
        font_sub = ImageFont.load_default()
    else:
        font_main = ImageFont.truetype(font_main_path, main_font_size)
        font_sub = ImageFont.truetype(font_sub_path, sub_font_size)
        
    # Text position parameters
    left_margin = 85
    max_text_width = 1180
    bottom_margin = 85
    
    temp_draw = ImageDraw.Draw(canvas)
    
    # Adjust main font size dynamically to fit width
    if os.path.exists(font_main_path):
        while main_font_size > 70:
            font_main = ImageFont.truetype(font_main_path, main_font_size)
            bbox1 = temp_draw.textbbox((0, 0), main_title_line1, font=font_main, stroke_width=12)
            bbox2 = temp_draw.textbbox((0, 0), main_title_line2, font=font_main, stroke_width=12)
            w1 = bbox1[2] - bbox1[0]
            w2 = bbox2[2] - bbox2[0]
            if max(w1, w2) <= max_text_width:
                break
            main_font_size -= 4
            
        while sub_font_size > 40:
            font_sub = ImageFont.truetype(font_sub_path, sub_font_size)
            bbox_sub = temp_draw.textbbox((0, 0), sub_title, font=font_sub, stroke_width=8)
            if bbox_sub[2] - bbox_sub[0] <= max_text_width:
                break
            sub_font_size -= 2

    # Measure line heights
    bbox_sub = temp_draw.textbbox((0, 0), sub_title, font=font_sub)
    sub_h = bbox_sub[3] - bbox_sub[1]
    
    bbox_l1 = temp_draw.textbbox((0, 0), main_title_line1, font=font_main)
    l1_h = bbox_l1[3] - bbox_l1[1]
    
    bbox_l2 = temp_draw.textbbox((0, 0), main_title_line2, font=font_main)
    l2_h = bbox_l2[3] - bbox_l2[1]
    
    # Calculate Y coordinates from bottom up
    line2_y = THUMB_HEIGHT - bottom_margin - l2_h - 20
    line1_y = line2_y - l1_h - 20
    sub_y = line1_y - sub_h - 30
    
    # 3. Process Book Cover
    if book_path and os.path.exists(book_path):
        print("Loading and pasting book cover...")
        book_img = Image.open(book_path).convert("RGBA")
        
        # Scale cover to occupy 58% of height
        target_book_height = int(THUMB_HEIGHT * 0.58)
        book_ratio = book_img.width / book_img.height
        target_book_width = int(target_book_height * book_ratio)
        book_img = book_img.resize((target_book_width, target_book_height), Image.Resampling.LANCZOS)
        
        # Apply 80% opacity
        alpha = book_img.split()[3]
        alpha = ImageEnhance.Brightness(alpha).enhance(0.80)
        book_img.putalpha(alpha)
        
        # Place near bottom right, bottom edge aligned with the main title bottom
        book_x = THUMB_WIDTH - book_img.width - 95
        # Align with the bottom of line 2
        book_y = (line2_y + bbox_l2[3]) - book_img.height
        
        print(f"Book cover placed at: x={book_x}, y={book_y}")
        canvas.paste(book_img, (book_x, book_y), book_img)
        
    # 4. Draw English Titles
    print("Drawing English text layers...")
    draw = ImageDraw.Draw(canvas)
    
    # Draw Subtitle (White text + Black outline + drop shadow)
    shadow_offset = 5
    stroke_width = 8
    
    # Shadow
    draw.text((left_margin + shadow_offset, sub_y + shadow_offset), sub_title, font=font_sub, fill=(0,0,0,180))
    # Outline + Text
    draw.text((left_margin, sub_y), sub_title, font=font_sub, fill=(255, 255, 255, 255), 
              stroke_width=stroke_width, stroke_fill=(0, 0, 0, 255))
              
    # Draw Main Title Line 1 & Line 2 (Bright Yellow + Black outline + drop shadow)
    shadow_offset_main = 9
    stroke_width_main = 12
    main_color = (255, 220, 0, 255) # Bright YouTube Yellow
    
    # Line 1 Shadow
    draw.text((left_margin + shadow_offset_main, line1_y + shadow_offset_main), main_title_line1, font=font_main, fill=(0,0,0,200))
    # Line 1 Text
    draw.text((left_margin, line1_y), main_title_line1, font=font_main, fill=main_color, 
              stroke_width=stroke_width_main, stroke_fill=(0, 0, 0, 255))
              
    # Line 2 Shadow
    draw.text((left_margin + shadow_offset_main, line2_y + shadow_offset_main), main_title_line2, font=font_main, fill=(0,0,0,200))
    # Line 2 Text
    draw.text((left_margin, line2_y), main_title_line2, font=font_main, fill=main_color, 
              stroke_width=stroke_width_main, stroke_fill=(0, 0, 0, 255))
              
    # 5. Output Final Image
    final_output = canvas.convert("RGB")
    final_output.save(output_path, "PNG")
    print(f"Success! English thumbnail saved to: {output_path}")

if __name__ == "__main__":
    create_english_thumbnail()
