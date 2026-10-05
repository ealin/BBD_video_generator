# Skill: book2video V3 (YouTube 書摘影片自動化生產線)

## 技能目的
此 Skill 將一本書的原始文字檔，轉換為可直接用於 YouTube 書摘影片製作的完整素材包：章節式訪談腳本、TTS 語音、分段插圖、縮圖、SEO 資訊、渲染前檢查清單。

V3 補強重點來自 B136 與 B148 實作：
- 每一步完成後都要回報結果，遇到需人工決策或缺料時停下來問。
- `book.txt` 若有缺漏、不順或 OCR 疑似錯誤，可依常識與必要的網路查詢補足，但不可擅自補使用者明確要求確認的資料。
- 腳本預設採「分章節」結構，並可參考既有專案的 `腳本.txt` 風格。
- ⚠️**【生圖風格事前選定】**：生成生圖 Prompt 之前，Agent 必須根據書籍題材提出 3~5 種視覺藝術風格（如高級水彩、油畫質感、電影概念藝術、極簡幾何等）供使用者選擇，選定後全局套用。
- ⚠️**【語意與金句驅動分段】**：廢除舊版機械式每 10 個 Block 切一段的做法。以 `@@@@` / `>>>>` 章節為硬邊界，章節內部依「話題轉換」與「核心金句」切分為 20~30 個語意段落，產出 `raw/concepts_B{book_id}.csv`。
- ⚠️**【具體場景與絕對無文字原則】**：生圖 Prompt 必須描述具體可拍攝畫面（非抽象隱喻），並結合腳本金句與情緒標記（EMPATHY, CLARITY, RATIONAL, TENSION, NARRATIVE, REVELATION, TRIUMPH）。**所有生圖 Prompt 強制寫入絕對禁止出現任何文字、數字、字母、標籤或 Logo**。
- ⚠️**【新版 Prompt 生成器】**：採用 `generate_prompts_v2.py` 讀取 Agent 產出的 `concepts_B{book_id}.csv` 與 `txt{book_id}` 組裝成標準 `分段生圖腳本.csv`。
- 生圖可分奇偶 prompt 使用不同引擎，且可中途切換 ChatGPT/Gemini。
- YouTube 縮圖標題與主標題先生成 5 組供使用者選擇，確定後寫入 `info.txt`；縮圖背景先產生候選圖讓使用者選擇，使用者確認後才合成正式 `youtube_thumbnail.png`。
- 最終檢查必須精確確認正式檔案，而不是只用模糊檔名前綴誤判。

## 目錄結構慣例
假設新書流水號為 `B130`，書名為 `XXX`：

- `B130_YYYYMMDD_XXX/raw/`
  - `book.txt`
  - `腳本.txt`
  - `腳本-step2.txt`
  - `腳本-step3.txt`
  - `腳本-step4.txt`
  - `concepts_B130.csv` (V3 新增：語意與金句設計檔)
  - `分段生圖腳本.csv`
  - `發音人清單.csv`
  - `info.txt`
  - `stickman_green/`: 存放生成後的動態人物綠幕影片 (*.mp4)
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
- ⚠️**【角色前綴冒號約束】**：角色前綴符號（。、。。、。。。）後方「絕對不得加冒號」（如 `。。：` 或 `。。:`），前綴完必須緊接對話內容（例如 `。。喔？這太有意思了。`），以確保字幕定位與解析格式正確。
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
- 加入章節標記 `>>>>` 與轉場標記 `@@@@`。
- ⚠️**【章節開頭組合標記】**：章節開頭必須是「轉場標記 `@@@@`」與「標題標記 `>>>>`」兩行緊接的組合標記，格式如下：
  ```text
  @@@@
  >>>> 第一章：主題名稱
  ```
- 保留說話者前綴 `。/。。/。。。`，並繼續遵循前綴後不得有冒號的約束。
- 控制每句長度，使 TTS 與字幕切分合理。

#### ⚠️ 斷行 7 大原則（Step 3 / Step 4 格式化規範）

以下原則適用於 `format_script.py` 自動斷行以及使用者手動審稿時的標準：

**原則 1：詞語完整性**
絕不在一個中文詞語、英文單字或專有名詞的中間斷行。
- ❌ `資產管理公<司創辦人` → ✅ `資產管理公司創辦人<...`
- ❌ `stan<d there!` → ✅ `stand there!`
- ❌ `點<擊率與廣告收益` → ✅ `點擊率與廣告收益`

**原則 2：語意合併**
語意上屬於同一論點或論據的短句，應合併到同一畫面中顯示（允許多行）。反之，概念獨立的短句即使很短也應獨立成段。
- ❌ `完全正確。`（獨占一畫面）+ `這就是我在書中說的...`（下一畫面）
- ✅ `完全正確。<這就是我在書中說的「詭辯與複雜化陷阱」。`（合併為一畫面）

**原則 3：列舉標記領頭**
「第一/第二/第三…」等列舉編號必須出現在新畫面的**開頭**位置，不能黏在前一句的尾巴，也不能獨占一個畫面。
- ❌ `你真正能夠100%控制的只有四件事：<第一，`（黏在前句尾）
- ❌ `第一，`（獨占一畫面）
- ✅ `第一，<你的「儲蓄率」與本金累積；`（領頭新畫面）

**原則 4：章節標題不斷行**
`>>>>` 章節標題行永遠保持為完整一行，絕不使用 `<` 斷行。
- ❌ `>>>> 第五章：<牛仔帳戶與人性防禦機制...`
- ✅ `>>>> 第五章：牛仔帳戶與人性防禦機制——用制度給人性留一條安全出路`

**原則 5：斷在語氣停頓點與標點之後**
`<` 換行位置必須落在標點符號（逗號、句號、頓號、分號、冒號、破折號）之後，或語意從句的邊界處，絕不能斷在詞語中間。
- ❌ `證明自<己眼光獨到`（斷在字中間）
- ✅ `證明自己眼光獨到<或參與市場熱點的原始衝動。`（斷在語意轉折處）
- ⚠️**【破折號斷行規範】**：遇破折號 `──` 斷行時，`<` 必須統一放置在**破折號之後**（如 `重量級人物──<李開復博士`），嚴禁將 `<` 放在破折號前或中間（如 `人物<──` 或 `人─<─物`），避免破折號孤立於下一行行首造成排版懸掛。

**原則 6：畫面行數彈性與單行長度上限**
- **單行長度上限**：每一行字幕長度嚴格控制在 **22 ~ 24 個全形字元以內**（最佳舒適長度為 12~18 字）。超過 22~24 字的長句，必須在合適的停頓點（逗號、連詞、從句邊界）補上 `<` 拆為多行，防止字幕溢出螢幕邊緣或過度縮小。
- **畫面行數彈性**：每畫面（TTS Block）允許最多 3 行（即包含最多 2 個 `<` 符號），必要時可到 4 行，以完整語意單元為準。不應為了嚴格遵守 2 行上限而拆散一個完整概念。
- ✅ `甚至你總覺得自己不夠聰明、<看不懂複雜的財務報表，<所以注定在股市裡被法人外資收割？`（3 行，語意完整）
- ✅ `你必須連續猜對兩次——<第一次是精確在暴跌前賣出，<第二次是精確在底部重新買入！`（3 行，列舉完整）
- ✅ `前沿A I 模型能獨立完成任務的時長上限，<從七分鐘躍升至約十二小時，<增幅超過一百倍。`（3 行，行長均衡且在安全寬度內）

**原則 7：英文簡化**
字幕中的專有名詞以中文為主；英文原文僅在該術語首次出現且觀眾需要對照時才保留，否則應移除英文括號註解以保持字幕清爽。需要 TTS 逐字母唸的英文縮寫（如 ETF），可加入空格（`E T F`）。
- ❌ `「損失厭惡（Loss Aversion）」`（每次都附英文）
- ✅ `「損失厭惡」`（移除非必要英文）
- ✅ `全球指數化 E T F`（加空格讓 TTS 逐字母唸）

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
- ⚠️**【發音人與角色的動態匹配】**：語音生成時，程式應自動產生 `raw/發音人清單.csv` 對照表，完整映射句首符號（。、。。、。。。）、對應的角色名稱（AA、BB、CC）、TTS發音人引擎名稱（如 Emeric、Aihan）與台詞內容首句，以作為後續動態綠幕生成對接的基準。必須注意的是：產生 `raw/發音人清單.csv`之前，必須停下來詢問TTS發音人引擎名稱。

### Step 5B. 動態綠幕人物批次生成 (當 head_type == "dynamic_body")
若專案啟用動態人物綠幕模式（而非靜態頭像模式），AI 應在 Step 5 的音訊生成完畢後，呼叫 `voice2video_skill` 技能。
依據 `發音人清單.csv` 上的角色配置（例如 AA 對應 Aihan，CC 對應 Emeric），將 `txt{book_id}` 與 `voice{book_id}` 中的分段音檔與台詞，在 Adobe Express 網頁自動化工具中批次合成動態綠幕人物動畫影片，並下載儲存至 `raw/stickman_green/` 目錄下（檔名與音訊一致，例如 `B147_0001.mp4`）。

### Step 6. YouTube Meta 生成
產出 `raw/info.txt`，至少包含：
- 5 組候選的 `【影片主標題】` 與 `【縮圖標題】` 組合供使用者審查與選擇。
- ⚠️**【全書核心主題導向】**：產出的 5 組【影片主標題】與【縮圖標題】必須皆針對「整本書的核心主題與總體價值」進行不同切入點的展現（更像是整本書名與核心精神的 5 種吸引人說法），嚴禁將特定單一章節或細節（如單一案例、單一細節技巧或單一帳戶名稱）單獨作為某組主標題，確保每一組方案都能完整代表整支影片。
- `【SEO 標籤】`
- `【影片說明欄】`

縮圖標題可支援：
- `第一行 / 第二行`
- `第一句 / 第二句`
- 全形冒號 `：` 或半形冒號 `:`

停點：必須提醒使用者審查並選擇一組最喜愛的【影片主標題】與【縮圖標題】方案。使用者確認所選方案後，AI 才可寫入 info.txt 並進入縮圖設計與後續流程。

### Step 7. 視覺素材收集
請使用者確認：
- 書封是否有中文封面、原文封面。若只有中文封面，記錄為可接受狀態。
- `photo/AA.png`, `photo/BB.png`, `photo/CC.png` 是否存在（若使用靜態頭像模式）。
- 若使用動態綠幕模式，檢查 `raw/stickman_green/` 目錄下是否已由 Step 5B 完整產出與語音 1:1 對應的角色動畫綠幕影片。
- `AV/訪談START.mp4` 與 `AV/訪談END.mp4` 是否存在。

停點：缺必要素材時停止並列出缺件。

## Phase 3: 影像生成規劃與製作

### Step 8. 段落插圖生成（V3 全新流程）

#### 8A. 視覺藝術風格選擇 (Style Selection)
在產生任何生圖 Prompt 前，AI 必須根據書籍題材與調性，提出 3~5 種建議的圖畫風格選項（例如：高級水彩、油畫質感、電影概念藝術、極簡幾何、古典版畫等），並說明每一種風格的視覺特色與適用理由。

停點：等待使用者審查並選擇一種風格，選定後全局寫入生圖 Prompt 的基礎風格模板。

#### 8B. 語意與金句分段規劃 (Semantic Concepts CSV)
AI 在 Antigravity 內部閱讀 `腳本.txt`（或 `腳本-step4.txt`），依據以下原則建立 `raw/concepts_B{book_id}.csv`：

1. **章節硬邊界**：以 `@@@@` / `>>>>` 為不可跨越的切割點。
2. **語意與話題切分**：章節內部依對話話題轉換、情緒起伏與金句密度，切分為 20~30 個子段落（每段約 4~17 個 TTS Block）。
3. **提取核心金句**：從該段腳本選出最打動觀眾的 1~2 句話。
4. **設計具體視覺場景**：將金句轉化為可拍攝的具體場景畫面，而非抽象隱喻。
5. **情緒標記 (Mood Tag)**：為每段標記情緒標籤（`EMPATHY`, `CLARITY`, `RATIONAL`, `TENSION`, `NARRATIVE`, `REVELATION`, `TRIUMPH`）。
6. **⚠️【絕對無文字原則】**：所有 Prompt 強制包含 `Absolutely no text, no words, no alphabet letters, no numbers, no logos, and no watermark visible anywhere.`，禁止任何文字或數字。

`raw/concepts_B{book_id}.csv` 格式欄位：
`seg_id, block_start, block_end, chapter, topic_title, key_quote, visual_scene, mood_tag`

停點：產出概念審查表並等待使用者確認「主題切割」、「核心金句」和「視覺場景」。

#### 8C. 生成分段 CSV (`generate_prompts_v2.py`)
執行 `python3 generate_prompts_v2.py {book_id}`。

功能：
- 讀取 `raw/concepts_B{book_id}.csv`。
- 從 `txt{book_id}/` 下的 Block 文字精確組裝每段的完整「段落內容」。
- 將選定的藝術風格 base_prompt + 具體視覺場景 + 情緒修飾語組裝成「生圖 Prompt」。
- 產出標準 `raw/分段生圖腳本.csv`。

#### 8D. 批量自動生圖 (`auto_generate_images.py`)
執行 `python3 auto_generate_images.py --book-id {book_id}`。

引擎分配與平行運作規則：
- 偶數編號圖用 ChatGPT（`--engine chatgpt --even`），奇數編號圖用 Gemini（`--engine gemini --odd`），可平行工作。
- 支援 `--start N` / `--end N` 斷點續跑與單張重生成。
- 圖片儲存至 `bg_image/bg{book_id}/` (或 `photo/bg{book_id}/`)，檔名為 `0.png`, `1.png`...`N.png`。
- 完成後檢查數量是否與 CSV 段落數完全一致，且無 0-byte 檔。

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
   - 搭配本書主題與選定風格
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
- `raw/發音人清單.csv` 存在。
- 正式 `photo/youtube_thumbnail.png` 精確存在，尺寸為 1920x1080。
- `photo/縮圖背景.png` 存在。
- `腳本/txt{book_id}` 與 `腳本/voice{book_id}` 數量一致，檔名一對一。
- 所有 mp3 非 0-byte。
- 若為靜態頭像模式，檢查 `photo/AA.png`, `BB.png`, `CC.png` 存在。
- 若為動態綠幕模式，檢查 `raw/stickman_green/` 底下的角色動畫影片數量與音訊完美一致。
- `AV/訪談START.mp4`, `AV/訪談END.mp4` 存在。
- 中文封面存在；原文封面可選，若使用者已確認只有中文封面，不列為失敗。
- `bg_image/bg{book_id}` (或 `photo/bg{book_id}`) 圖檔數量等於 `分段生圖腳本.csv` 段落數。
- 圖檔編號連續，例如 0 到 25。

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
- 或使用本地 fallback 先提出候選，並清楚回報。

## 喚醒詞用法
使用者可說：

```text
使用 book2video skill V3，開始處理目錄 "B130_YYYYMMDD_XXX" 下的書本 "raw/book.txt"
```

AI 必須依照本 V3 流程逐步執行、逐步回報、在指定停點等待確認。
