import os
import json
from google import genai
from google.genai import types

def generate_script_and_seo(input_txt_path, output_script_path, output_seo_path):
    """
    透過 Gemini API 讀取書本內容，生成格式化的影片對話腳本及 SEO 資訊
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("請先設定環境變數 GEMINI_API_KEY")
        return False

    client = genai.Client(api_key=api_key)

    try:
        with open(input_txt_path, 'r', encoding='utf-8') as f:
            book_content = f.read()
    except Exception as e:
        print(f"讀取書本文字檔失敗: {e}")
        return False

    # 由於書本可能很長，我們使用模型來摘要並生成對話。
    # 這裡為示範，限制輸入長度或依賴大模型 context window。Gemini 1.5 Pro 支援百萬 token。
    prompt = f"""
    你現在是一位專業的 YouTube 知識類頻道編劇。
    我們正在製作一支關於以下這本書摘的影片。這是一個訪談形式的對話腳本。
    
    角色：
    1. 主持人A (大黑狗)：熱情、引導話題。每句台詞必須以「。」(一個全形句號) 開頭。
    2. 主持人B (小黑妹)：好奇、提出觀眾可能的疑問。每句台詞必須以「。。」(兩個全形句號) 開頭。
    3. 受訪者 (書本作者分身)：負責解答與深入說明。每句台詞必須以「。。。」(三個全形句號) 開頭。

    特殊格式要求：
    - 章節標題：必須以「>>>>」開頭，例如：`>>>>從牛頓到量子：我們為何在現代社會中感到無比疏離？`
    - 黑畫面過場：在章節切換或需要沈默轉場時，使用單獨一行的「@@@@」。
    - 強制換行：如果同一句台詞太長需要在同一畫面換行，請在句中使用「<」符號。但請盡量將段落斷好，不宜過長。
    - 不能有任何 Markdown 語法 (如 **bold**)。

    請根據以下書本內容，撰寫一段約 15 分鐘影片長度的精彩對話腳本 (約 3000-4000 字)：
    
    【書本內容開始】
    {book_content[:50000]} # 若內容過長，截取前 50000 字作示範
    【書本內容結束】
    
    除了腳本，你還需要提供這支影片的 SEO 資訊，包含：
    1. title (標題，吸引人，包含關鍵字)
    2. description (資訊欄描述)
    3. tags (標籤陣列)
    4. thumbnail_prompt (給 AI 生成縮圖的 Prompt 提示詞)

    請將回應嚴格依照以下 JSON 格式輸出：
    {{
        "seo": {{
            "title": "影片標題",
            "description": "...",
            "tags": ["tag1", "tag2"],
            "thumbnail_prompt": "..."
        }},
        "script": "完整的腳本文字，包含上述所有控制符號..."
    }}
    """

    print("正在呼叫 LLM 產生腳本與 SEO 資訊...")
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-pro',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        
        result_json = json.loads(response.text)
        
        # 寫入腳本
        with open(output_script_path, 'w', encoding='utf-8') as f:
            f.write(result_json["script"])
            
        # 寫入 SEO
        with open(output_seo_path, 'w', encoding='utf-8') as f:
            json.dump(result_json["seo"], f, ensure_ascii=False, indent=4)
            
        print(f"成功！腳本已儲存至 {output_script_path}")
        print(f"SEO 資訊已儲存至 {output_seo_path}")
        return True
        
    except Exception as e:
        print(f"LLM 處理失敗: {e}")
        return False

if __name__ == "__main__":
    # 測試執行
    input_file = "128_20260322_量子与生活/raw/book.txt"
    script_out = "128_20260322_量子与生活/raw/book_abstract_auto.txt"
    seo_out = "128_20260322_量子与生活/raw/seo_info.json"
    if os.path.exists(input_file):
        generate_script_and_seo(input_file, script_out, seo_out)
    else:
        print(f"找不到測試檔案 {input_file}")
