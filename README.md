# YouTube 書摘影片自動化生產線 (book2video pipeline)

本專案是一套高度自動化且模組化的 YouTube 書摘對話影片生產系統。旨在將任意新書的原始文字檔案 (`book.txt`)，經過一整套結構化的半自動與全自動流水線 (SOP)，轉換為可用於 YouTube 發布的最終影片素材（包含多角色訪談語音、語意對應插圖、字幕綠幕、動態頭像與高點閱率封面縮圖）。

專案特別針對「黑狗文選 - 下班訪談室」的對話風格與剪輯版型（如：左側主持人/專家動態頭像，右側 Ken Burns 動畫故事插圖）進行了工業級的封裝與優化。

---

## 📁 標準目錄結構慣例

專案採用動態流水號與名稱解析。假設處理書籍流水號為 `B140`，書名為 `反常識投資`，其檔案結構約定如下：

```text
workspace_root/
├── 140_20260608_反常識投資/          # 書籍專屬工作目錄 (自動動態比對 140_ / B140_ / BBD140_ 等)
│   ├── raw/                           # 原始檔與腳本暫存目錄
│   │   ├── book.txt                   # 原始新書文字檔 (電子書/OCR 萃取內容)
│   │   ├── 腳本.txt                   # Phase 1 Step 1: 三人對話腳本初稿
│   │   ├── 腳本-step2.txt             # Phase 1 Step 2: 依反饋微調定案腳本
│   │   ├── 腳本-step3.txt             # Phase 1 Step 3: 自動格式化與分段標記腳本
│   │   ├── 腳本-step4.txt             # Phase 1 Step 4: 最終精煉定案腳本
│   │   ├── 分段生圖腳本.csv           # 依照語意切分的故事生圖 Prompt 清單
│   │   ├── 縮圖背景生圖prompt.csv     # 縮圖背景生圖 Prompt 候選清單
│   │   ├── info.txt                   # YouTube Meta 資訊（包含主標、副標、說明欄、Tags）
│   │   ├── txt140/                    # 批量切分後的單句文字檔目錄
│   │   └── voice140/                  # 批量合成後的單句 Edge-TTS 配音檔 (.mp3)
│   ├── photo/                         # 視覺素材存放目錄
│   │   ├── 中文封面.jpeg / 原文封面.png # 書籍封面圖檔
│   │   ├── AA.png, BB.png, CC.png     # 男主持、女主持與專家頭像素材
│   │   ├── 縮圖背景.png               # 使用者挑選後的縮圖背景圖
│   │   ├── youtube_thumbnail.png      # 最終自動合成之 16:9 封面縮圖
│   │   ├── bg140/                     # 自動下載的故事分段背景插圖 (0.png ~ 25.png)
│   │   └── thumbnail_bg_webgen/       # 縮圖背景生圖候選圖暫存區
│   └── AV/                            # 轉場與過場影片目錄
│       ├── 訪談START.mp4              # 開場過場影片
│       └── 訪談END.mp4                # 結尾過場影片
├── data/                              # 預設背景影片素材目錄 (如: data/佛像銀河.mp4 等)
├── BBD_video_generator_2026.py        # 核心影片渲染與合成腳本 (MoviePy 驅動)
├── auto_generate_images.py            # Playwright 網頁自動化批量生圖與下載腳本
├── check_readiness.py                 # Pipeline 完整度與綠燈就緒度檢查工具
├── format_script.py                   # 腳本格式化與章節、轉場標記插入工具
├── generate_audio.py                  # 批量 Edge-TTS 語音合成腳本 (支援超時重試與靜音檔)
├── generate_prompts.py                # 語意分析與 1:1 分段生圖腳本生成工具
├── generate_thumbnail.py              # PIL 動態縮圖排版與自動封面貼圖合成工具
└── README.md                          # 本說明文件
```

---

## 🔄 核心流水線步驟 (Step-by-Step SOP)

### Phase 1: 腳本生成與格式化 (人機協作)
1. **生成初稿**：執行 `book_to_script.py`，讀取 `book.txt` 並轉換為男/女主持與專家的三人對話腳本 `腳本.txt`。
2. **精煉一校**：依需求微調產生 `腳本-step2.txt`。
3. **格式化標記**：執行 `format_script.py` 對 step2 腳本進行切分，自動標記章節（`>>>>`）、轉場（`@@@@`）並加入每一句字數限制，生成 `腳本-step3.txt`。
4. **二校定案**：進行最終句讀微調，產生定案版 `腳本-step4.txt`。

### Phase 2: 語音與行銷素材生成
5. **語音批量合成**：修改並執行 `generate_audio.py`，呼叫 Edge-TTS 產生對應文字檔與高音質配音檔（男主、女主、受訪專家三種音色配對）。空行與轉場標記會自動映射為 0-byte 靜音檔，並加入 3 次錯誤重試機制，保證批量流程不中斷。
6. **YouTube 資訊生成**：將大模型生成的 YouTube 標題、副標、SEO 標籤和詳細說明寫入 `info.txt`。
7. **媒體素材確認**：於 `photo/` 目錄放置直立封面與三人頭像，於 `AV/` 目錄確認 `訪談START.mp4` 與 `訪談END.mp4` 已就位。

### Phase 3: 插圖與縮圖生成 (雙引擎分工)
8. **分段插圖 Prompt**：執行 `generate_prompts.py` 分析 `腳本-step4.txt`，依語意劃分約 25~45 個插圖段落，並將 1:1 插圖提示詞輸出至 `分段生圖腳本.csv`。
9. **瀏覽器自動化生圖**：
   執行 `auto_generate_images.py`。本工具會使用 Playwright 開啟實體 Chromium 瀏覽器，引導使用者登入後接管操作，循序在同一個對話 Session 下送出 Prompt，並透過獨創的 **Canvas 二進位轉換下載器** 無損下載為 `0.png`, `1.png`... 存入 `bg{book_id}` 目錄。
   * **奇偶數分工語法**：
     * **ChatGPT (偶數編號)**：`python3 -u auto_generate_images.py --engine chatgpt --even`
     * **Gemini (奇數編號)**：`python3 -u auto_generate_images.py --engine gemini --odd`
10. **封面縮圖排版合成**：
    * **生圖背景**：將 2-3 個 16:9 安全留白構圖的 Prompt 寫入 `縮圖背景生圖prompt.csv`，利用 `auto_generate_images.py` 生成縮圖背景候選。
    * **選擇與複製**：使用者挑選背景並存為 `photo/縮圖背景.png`。
    * **合成**：執行 `generate_thumbnail.py`，程式會自動解析 `info.txt` 中指定的標題字數與行數，自動計算並縮小字級避開裁切區，並將直立封面以高質感光影貼齊右下，輸出最終 `youtube_thumbnail.png`。

### Phase 4: 渲染前置檢查與輸出
11. **就緒度檢查**：執行 `check_readiness.py`。程式會進行嚴格的 Pipeline 檢驗，確保檔案數量、命名序列（0, 1... 檔案連續性）、必要欄位、封面頭像以及音訊文字 1:1 對應無誤後，亮起全綠燈 (**✓ READY**)。
12. **最終影片渲染**：確認 `BBD_video_generator_2026.py` 中 `book_ID` 設置無誤後，執行：
    ```bash
    python3 BBD_video_generator_2026.py
    ```
    即可輸出 `output1_sub.mp4`（綠幕字幕與故事插圖動畫貼圖軌）以及 `output1_head.mp4`（綠幕頭像軌）影片。

---

## 🛠️ 開發與自動化執行指令

### Playwright 生圖自動化腳本 (`auto_generate_images.py`)

支援參數過濾、指定 CSV、調整冷卻間隔等功能：

```bash
# 1. 基本生圖 (預設讀取當前 Book ID 目錄下的 分段生圖腳本.csv，使用 ChatGPT)
python3 -u auto_generate_images.py

# 2. 局部區間補件生成 (如: 重新生成編號 10 至 15 的圖片)
python3 -u auto_generate_images.py --start 10 --end 15

# 3. 指定生圖引擎 (chatgpt / gemini)
python3 -u auto_generate_images.py --engine gemini

# 4. 奇偶數過濾分工 (可用於多進程並行生成或風格搭配)
python3 -u auto_generate_images.py --engine chatgpt --even   # 只生成 0, 2, 4...
python3 -u auto_generate_images.py --engine gemini --odd     # 只生成 1, 3, 5...

# 5. 指定自訂 CSV 與輸出路徑 (如：生成縮圖背景候選圖)
python3 -u auto_generate_images.py --csv [CSV路徑] --output-dir [輸出路徑]
```

### 就緒度驗證 (`check_readiness.py`)

渲染前務必執行以預防因檔案缺漏導致 MoviePy 渲染中途崩潰：

```bash
python3 check_readiness.py
```

---

## 📦 依賴環境與安裝

本專案運行於 macOS/Linux 環境，需安裝以下依賴庫：

1. **Python 依賴庫**：
   ```bash
   pip install pillow moviepy playwright edge-tts requests
   ```
2. **Playwright 瀏覽器初始化**：
   ```bash
   playwright install chromium
   ```
3. **系統字體要求**：
   專案在合成縮圖及渲染字幕時需讀取字體，預設使用台北黑體：`TaipeiSansTCBeta-Bold.ttf`（需放置於專案根目錄）。

---

## ⚠️ 執行注意事項

1. **Playwright 登入緩存**：`auto_generate_images.py` 會共享主機的 Chrome 用戶 Profile (`~/Library/Application Support/Google/Chrome`)。如遇帳號讀寫鎖衝突，請先關閉實體 Chrome 瀏覽器再執行生圖指令。
2. **Edge-TTS 速率限制**：因語音批量合成發送請求較快，本系統已內置防限制機制的隨機延遲。如遇網路逾時，重新運行 `generate_audio.py` 將自動跳過已成功下載的音檔進行增量補件。
3. **MoviePy 綠幕色碼**：影片渲染預設之綠幕背景色碼為 `(0, 255, 0)`。合成故事插圖時將自動套用 48 點圓角遮罩與 Ken Burns（1.3x -> 1.0x）微縮放動畫。
