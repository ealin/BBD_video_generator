# Skill: book2video V2 (YouTube 書摘影片自動化生產線)

## 技能目的
此 Skill 將一本書的原始文字檔，轉換為可直接用於 YouTube 書摘影片製作的完整素材包：章節式訪談腳本、TTS 語音、分段插圖、縮圖、SEO 資訊、渲染前檢查清單。

V2 補強重點來自 B136《人生只有兩件事》實作：
- 每一步完成後都要回報結果，遇到需人工決策或缺料時停下來問。
- `book.txt` 若有缺漏、不順或 OCR 疑似錯誤，可依常識與必要的網路查詢補足，但不可擅自補使用者明確要求確認的資料。
- 腳本預設採「分章節」結構，並可參考既有專案的 `腳本.txt` 風格。
- 生圖可分奇偶 prompt 使用不同引擎，且可中途切換 ChatGPT/Gemini。
- YouTube 縮圖背景要先產生候選圖讓使用者選擇，使用者確認後才合成正式 `youtube_thumbnail.png`。
- 最終檢查必須精確確認正式檔案，而不是只用模糊檔名前綴誤判。

## 目錄結構慣例
假設新書流水號為 `B130`，書名為 `XXX`：

- `B130_YYYYMMDD_XXX/raw/`
  - `book.txt`
  - `腳本.txt`
  - `腳本-step2.txt`
  - `腳本-step3.txt`
  - `腳本-step4.txt`
  - `分段生圖腳本.csv`
  - `info.txt`
  - 可選：`縮圖背景生圖prompt.csv`
- `B130_YYYYMMDD_XXX/photo/`
  - `中文封面.jpeg` 或其他中文封面圖
  - `原文封面.*`，若本書無原文封面可省略
  - `AA.png`, `BB.png`, `CC.png`
  - `縮圖背景.png`
  - `youtube_thumbnail.png`
  - 可選：`thumbnail_bg_webgen/`、縮圖背景候選圖
- `B130_YYYYMMDD_XXX/AV/`
  - `訪談START.mp4`
  - `訪談END.mp4`
- `腳本/txt130/`
- `腳本/voice130/`
- `bg_image/bg130/`

## 執行總原則
1. 每個 Step 完成後都要報告產物、檔案位置、數量與是否可進入下一步。
2. 所有明確標示「等待審查 / 等待選擇 / 等待補件」的步驟必須暫停。
3. 使用者若直接修改中間檔，後續必須以使用者修改後的版本為準，不覆蓋。
4. 修改腳本前先回報即將修改哪些對接點，例如 Book ID、路徑、輸出目錄。
5. 若自動化工具因登入、金鑰、網路或平台限制失敗，先回報原因，再提出可保留流程完整性的替代方案。

## Phase 1: 腳本生成與精煉

### Step 1. 腳本初稿
AI 讀取 `raw/book.txt`，萃取核心觀點並產出 `raw/腳本.txt`。

要求：
- 使用多角色訪談格式：`。`、`。。`、`。。。` 對應不同說話者。
- 預設產生分章節腳本，可參考既有專案如 B134、B133 的 `腳本.txt`。
- 若使用者指定篇幅，例如 5000 個繁體中文字以上，必須遵守。
- 內容應為繁體中文，適合 YouTube 書摘口播。
- 若 `book.txt` 有缺漏或文字不流暢，可依常識補順；涉及外部事實且不確定時可查詢網路並回報依據。

停點：產出後等待使用者審查 `腳本.txt`。

### Step 2. 腳本一校
依使用者回饋調整 `腳本.txt`，產出 `raw/腳本-step2.txt`。

停點：使用者確認 `腳本-step2.txt 可定案` 後才繼續。

### Step 3. 腳本格式化
修改並執行 `format_script.py`，以 Step2 內容產出 `raw/腳本-step3.txt`。

要求：
- 加入章節標記 `>>>>`。
- 加入轉場標記 `@@@@`。
- 保留說話者前綴 `。/。。/。。。`。
- 控制每句長度，使 TTS 與字幕切分合理。

停點：若使用者要直接修改 `腳本-step3.txt`，後續以目前檔案版本為準。

### Step 4. 腳本二校 / 最終腳本
依使用者修改或指示產出 / 確認 `raw/腳本-step4.txt`。

停點：使用者確認 `腳本-step4.txt` 可用後才進入語音。

## Phase 2: 語音與行銷素材

### Step 5. 批量語音合成
修改並執行 `generate_audio.py`。

必改對接點：
- `TXT_DIR = "腳本/txt{book_id}"`
- `VOICE_DIR = "腳本/voice{book_id}"`
- `script_path = "{book_dir}/raw/腳本-step4.txt"`
- 輸出檔名前綴使用當前 Book ID，例如 `B136_%04d`

檢查要求：
- `.txt` 與 `.mp3` 數量一致。
- 所有 `.mp3` 檔案存在且非 0-byte。
- 若 `@@@@` 或轉場段落生成 0-byte 音訊，應以短靜音 mp3 補齊，並回報補了哪些檔案。
- 若 Edge-TTS 因網路 / DNS 失敗，停止錯誤產物，重新執行或請求使用者允許網路。

### Step 6. YouTube Meta 生成
產出 `raw/info.txt`，至少包含：
- `【影片主標題】`
- `【縮圖標題】`
- `【SEO 標籤】`
- `【影片說明欄】`

縮圖標題可支援：
- `第一行 / 第二行`
- `第一句 / 第二句`
- 全形冒號 `：` 或半形冒號 `:`

停點：必須提醒使用者審查 `info.txt` 的縮圖標題。使用者確認後才進入縮圖與後續流程。

### Step 7. 視覺素材收集
請使用者確認：
- 書封是否有中文封面、原文封面。若只有中文封面，記錄為可接受狀態。
- `photo/AA.png`, `photo/BB.png`, `photo/CC.png` 是否存在。
- `AV/訪談START.mp4` 與 `AV/訪談END.mp4` 是否存在。

停點：缺必要素材時停止並列出缺件。

## Phase 3: 影像生成規劃與製作

### Step 8. 分段生圖腳本與網頁自動生圖

#### A. 生成分段 CSV
修改並執行 `generate_prompts.py`。

要求：
- 設定正確 `book_id` 與 `csv_path`。
- 根據本書主題重寫插圖概念庫，不沿用前一本書的概念。
- 產出 `raw/分段生圖腳本.csv`。
- 回報段落數，例如 75 段。

#### B. 批量生圖
修改並執行 `auto_generate_images.py`。

建議讓腳本支援：
- `--engine chatgpt|gemini`
- `--start N`
- `--end N`
- `--odd`
- `--even`
- `--csv PATH`
- `--output-dir PATH`

引擎分配規則：
- 偶數編號的圖要用 ChatGPT 產生，奇數編號的圖用 Gemini 產生，可以平行工作。
- 若中途某引擎不可用，可從指定編號開始改用另一個引擎，例如 `--engine gemini --even --start 34`。
- 已存在的圖檔應跳過，不覆蓋。

下載與檢查：
- 優先用 blob/canvas 方式下載原圖。
- 可容錯使用 hover 下載、預覽下載、HTTP 下載或元素截圖。
- 生圖完成後檢查 `bg_image/bg{book_id}`：
  - 編號是否 0 到 N 連續
  - 數量是否等於 CSV 段落數
  - 是否有異常小檔或缺檔

## Phase 3 Step 9: YouTube 縮圖自動化合成

### 9A. 產生縮圖背景候選
優先使用與 Step 8 類似的網頁版 ChatGPT/Gemini 生圖流程，而不是只靠本地 fallback。

建議流程：
1. 建立 `raw/縮圖背景生圖prompt.csv`，只放 2 到 4 個縮圖背景 prompt。
2. 使用 `auto_generate_images.py --csv ... --output-dir photo/thumbnail_bg_webgen` 生成候選。
3. Prompt 必須明確要求：
   - YouTube thumbnail background
   - 16:9 composition
   - no text, no letters, no words, no logo, no watermark
   - lower-left 預留大標題空間
   - right third 預留書封位置
   - 水彩 editorial / 商務書籍 / 本書主題視覺
4. 產出後展示候選圖並等待使用者選擇。

停點：使用者選定背景圖後，才可覆蓋 `photo/縮圖背景.png` 並合成縮圖。

備用方案：
- 若 OpenAI/Gemini 生圖不可用，可先用本地 PIL 產生候選，但必須明確告知這是 fallback，且仍需使用者選圖。

### 9B. 合成正式縮圖
使用選定背景圖存為：
- `photo/縮圖背景.png`

修改並執行 `generate_thumbnail.py`：
- `info_path` 指向本書 `raw/info.txt`
- `bg_path` 指向本書 `photo/縮圖背景.png`
- `book_path` 指向本書封面
- `output_path` 指向本書 `photo/youtube_thumbnail.png`

合成要求：
- 背景自動 resize/crop 到 1920x1080。
- 主標與副標從 `info.txt` 解析。
- 字體動態縮小，避免超出文字區。
- 書封放右側，避免遮擋標題。
- 產出後必須視覺確認。

快取與誤判處理：
- 若使用者指出背景不對，需比對來源圖與 `縮圖背景.png` 的尺寸與 hash。
- 可另外輸出一份新檔名，例如 `youtube_thumbnail_候選0指定版.png`，避免同名預覽快取造成誤判。
- 最終仍必須覆蓋正式檔 `youtube_thumbnail.png`。

## Phase 4: 渲染前置檢查與輸出

### Step 10. 渲染參數更新
修改 `BBD_video_generator_2026.py`：
- `book_ID = "{book_id}"`
- 確認 txt、voice、bg_image 路徑由當前 Book ID 組合。
- 確認頭像載入可優先使用本書 `photo/AA.png`, `BB.png`, `CC.png`。
- 不改動與本任務無關的渲染邏輯。

### Step 11. 最終就緒度檢查
修改並執行 `check_readiness.py`。

檢查項目：
- `raw/info.txt` 存在且欄位完整。
- 正式 `photo/youtube_thumbnail.png` 精確存在，尺寸為 1920x1080。
- `photo/縮圖背景.png` 存在。
- `腳本/txt{book_id}` 與 `腳本/voice{book_id}` 數量一致，檔名一對一。
- 所有 mp3 非 0-byte。
- `photo/AA.png`, `BB.png`, `CC.png` 存在。
- `AV/訪談START.mp4`, `AV/訪談END.mp4` 存在。
- 中文封面存在；原文封面可選，若使用者已確認只有中文封面，不列為失敗。
- `bg_image/bg{book_id}` 圖檔數量等於 `分段生圖腳本.csv` 段落數。
- 圖檔編號連續，例如 0 到 74。

注意：
- 不可只用 `startswith("youtube_thumbnail")` 判定縮圖存在，避免抓到備份檔。
- 檢查完成後回報 `✓ READY` 或列出缺件清單。

停點：若有缺件，等待使用者補件；若全數通過，通知可進入最終渲染。

### Step 12. 最終渲染
此步為人工執行或依使用者要求由 AI 協助執行。

執行：
- `python3 BBD_video_generator_2026.py`

預期產物：
- `output1_sub.mp4`
- `output1_head.mp4`
- `output1_img.mp4`，視 `render_mode` 而定
- `output{book_id}.mp3`

渲染前再次確認：
- `render_mode` 是否符合當次需求，例如 `sub`, `head`, `img`, `all`。
- `BG_Type` 是否符合使用背景圖或背景影片。
- `default_bg_video` 是否存在。

## 常見問題與處理

### zsh: permission denied: /Users/mac
原因：指令前誤加 `~`，例如：

```bash
~ python3 auto_generate_images.py --engine chatgpt --even --start 34
```

應改為：

```bash
python3 auto_generate_images.py --engine chatgpt --even --start 34
```

### ChatGPT/Gemini 生圖中途失敗
處理：
- 保留已生成圖檔。
- 找出最後成功編號。
- 從下一個編號使用同引擎或切換引擎續跑。

範例：

```bash
python3 -u auto_generate_images.py --engine gemini --even --start 34
python3 -u auto_generate_images.py --engine gemini --odd
```

### 生圖腳本最後 EOFError
若摘要顯示成功張數正確，最後 EOFError 只是 `input("按 Enter...")` 在非互動環境讀不到 stdin，不代表圖片失敗。

### OpenAI imagegen CLI 沒有 API key
若出現 `OPENAI_API_KEY is not set`：
- 不可假裝已成功使用 OpenAI 生圖。
- 可改用網頁版 ChatGPT/Gemini 自動化。
- 或使用本地 fallback 先產生候選，並清楚回報。

## 喚醒詞用法
使用者可說：

```text
使用 book2video skill，開始處理目錄 "B130_YYYYMMDD_XXX" 下的書本 "raw/book.txt"
```

AI 必須依照本 V2 流程逐步執行、逐步回報、在指定停點等待確認。
