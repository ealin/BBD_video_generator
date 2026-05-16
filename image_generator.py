import os
import json
from PIL import Image, ImageDraw, ImageFont

# 引入 Google GenAI (用於 Imagen 圖片生成示範)
# 若您使用 DALL-E 3，可替換為 OpenAI API
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

def generate_ai_image(prompt, output_path):
    """
    呼叫 LLM 影像生成模型 (例如 Google Imagen 或 DALL-E) 產生圖片
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key or not GENAI_AVAILABLE:
        print(f"[{output_path}] 未設定金鑰或未安裝套件，產生單色測試圖")
        img = Image.new('RGB', (1920, 1080), color=(73, 109, 137))
        img.save(output_path)
        return

    client = genai.Client(api_key=api_key)
    print(f"正在生成圖片: {output_path} ...")
    
    try:
        # 使用 Google Imagen 模型生成圖片
        result = client.models.generate_images(
            model='imagen-3.0-generate-002',
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="16:9"
            )
        )
        for generated_image in result.generated_images:
            image = Image.open(generated_image.image.image_bytes)
            image.save(output_path)
            break # 只要第一張
        print(f"產生圖片成功: {output_path}")
    except Exception as e:
        print(f"生圖失敗: {e}，將使用測試圖片。")
        img = Image.new('RGB', (1920, 1080), color=(100, 100, 150))
        img.save(output_path)

def generate_avatars(output_dir):
    """
    產生三位主持人的頭像：AA (男主持), BB (女主持), CC (來賓)
    """
    os.makedirs(output_dir, exist_ok=True)
    
    generate_ai_image("A professional 2D cartoon avatar of a cheerful male host, circular frame, transparent background, solid colors", os.path.join(output_dir, "AA.png"))
    generate_ai_image("A professional 2D cartoon avatar of a smart female host, circular frame, transparent background, solid colors", os.path.join(output_dir, "BB.png"))
    generate_ai_image("A professional 2D cartoon avatar of a wise author guest, circular frame, transparent background, solid colors", os.path.join(output_dir, "CC.png"))

def generate_backgrounds(script_path, output_dir):
    """
    分析腳本大綱，生成對應的背景圖片
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # 這裡為簡化，直接產生 5 張預設圖。
    # 實際上可讀取腳本內容，抽取出關鍵字來當 prompt
    prompts = [
        "A quiet study room with a vintage turntable playing, warm lighting, cinematic, 4k",
        "A futuristic quantum realm visualization, glowing particles, abstract, blue and purple tones",
        "A bustling modern city street at dusk, reflecting alienation and solitude",
        "Two people talking deeply in a cozy cafe, cinematic lighting",
        "A peaceful garden representing mindfulness and connection with nature"
    ]
    
    for i, prompt in enumerate(prompts):
        generate_ai_image(prompt, os.path.join(output_dir, f"{i}.jpg"))

def create_youtube_thumbnail(seo_json_path, bg_image_path, cover_image_path, output_path):
    """
    使用 PIL 自動合成 YouTube 縮圖
    """
    print("正在製作縮圖...")
    
    try:
        # 建立 1920x1080 畫布
        thumbnail = Image.new('RGB', (1920, 1080), (255, 255, 255))
        
        # 1. 貼上背景圖
        if os.path.exists(bg_image_path):
            bg = Image.open(bg_image_path).resize((1920, 1080), Image.LANCZOS)
            thumbnail.paste(bg, (0, 0))
        else:
            # 如果沒有背景圖，自己畫漸層或單色
            draw = ImageDraw.Draw(thumbnail)
            draw.rectangle([0, 0, 1920, 1080], fill=(0, 49, 83))

        # 2. 貼上書本封面 (放右側)
        if cover_image_path and os.path.exists(cover_image_path):
            cover = Image.open(cover_image_path)
            # 依比例縮放封面，高度設為 800
            w_percent = (800 / float(cover.size[1]))
            h_size = int((float(cover.size[0]) * float(w_percent)))
            cover = cover.resize((h_size, 800), Image.LANCZOS)
            # 貼在右邊
            thumbnail.paste(cover, (1920 - h_size - 100, 140))
            
        # 3. 讀取標題文字
        title_text = "新影片上架！"
        if os.path.exists(seo_json_path):
            with open(seo_json_path, 'r', encoding='utf-8') as f:
                seo_data = json.load(f)
                title_text = seo_data.get('title', title_text)

        # 4. 畫上文字
        draw = ImageDraw.Draw(thumbnail)
        # 嘗試使用系統字體，需確認字體路徑
        font_path = "TaipeiSansTCBeta-Bold.ttf"
        try:
            font = ImageFont.truetype(font_path, 120)
        except IOError:
            print(f"找不到字型 {font_path}，使用預設字型。")
            font = ImageFont.load_default()
            
        # 簡單文字排版 (這裡可以更進階做換行)
        draw.text((100, 400), title_text[:10], fill="yellow", stroke_width=4, stroke_fill="black", font=font)
        if len(title_text) > 10:
            draw.text((100, 550), title_text[10:20], fill="white", stroke_width=4, stroke_fill="black", font=font)

        thumbnail.save(output_path)
        print(f"縮圖已儲存至 {output_path}")
        return True
    except Exception as e:
        print(f"合成縮圖失敗: {e}")
        return False

if __name__ == "__main__":
    out_dir = "128_20260322_量子与生活/auto_output/visuals"
    os.makedirs(out_dir, exist_ok=True)
    
    generate_avatars(out_dir)
    generate_backgrounds("dummy.txt", os.path.join(out_dir, "bg_image"))
    create_youtube_thumbnail("128_20260322_量子与生活/raw/seo_info.json", os.path.join(out_dir, "bg_image", "0.jpg"), None, os.path.join(out_dir, "thumbnail.jpg"))
