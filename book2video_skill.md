# Skill: book2video (YouTube 書摘影片自動化生產線)

## 🎯 技能目的
此 Skill 旨在將一本新書的原始文字檔，經過一系列自動化與半自動化的標準作業流程 (SOP)，轉換為可直接用於 YouTube 最終剪輯的高畫質書摘影片素材 (影像、語音、字幕、縮圖、SEO)。

## 📁 目錄結構慣例
假設新書流水號為 `B130`，書名為 `XXX`，AI 會預期或協助建立以下目錄結構：
- `B130_XXX/raw/`: 存放原始電子檔 (`book.txt`)、各階段腳本 (`腳本.txt` ~ `腳本-step4.txt`)、生圖腳本 (`分段生圖腳本.csv`)、發音人對照表 (`發音人清單.csv`)、影片資訊 (`info.txt`)。
  * `B130_XXX/raw/txt130/`: 存放切分後的單句文字檔。
  * `B130_XXX/raw/voice130/`: 存放 Edge-TTS 生成的單句配音檔。
- `B130_XXX/photo/`: 存放縮圖背景、封面圖片 (`中文封面.jpeg`、`原文封面.png`)、最終 `youtube_thumbnail.png`、作者頭像等。
  * `B130_XXX/photo/bg130/`: 存放依照分段腳本生成的 1:1 背景插圖 (`0.jpg`, `1.jpg`...)。
- `B130_XXX/AV/`: 存放 `訪談START.mp4` 與 `訪談END.mp4` 過場影片（★ 統一命名的標準規範）。

---

## 🔄 執行步驟 (Step-by-Step)

### Phase 1: 腳本生成與精煉 (需要人工協作)
1. **[AI 執行] 腳本初稿**：AI 讀取 `B130_XXX/raw/book.txt`，萃取核心知識，並使用多角色對話格式 (。男主持 / 。。女主持 / 。。。專家) 產出 `腳本.txt`。
   * 💡 **【開頭鉤子原則 (Opening Hook Principle)】**：腳本開頭前幾句必須加入 3~4 個吸引觀眾的「鉤子」（Hooks）。這些鉤子應直擊痛點（如「存股卻賺股息賠價差」）、指出隱形風險（如「持股正跌入C級黑洞」）、或揭示高價值方案（如「雷總親授6步驟價值投資SOP」），在開場 30 秒內牢牢抓住觀眾注意力。
   * 💡 **【腳本分章節原則 (Script Chaptering Principle)】**：整篇對話腳本必須在內容上明確劃分為 4~6 個章節，並在腳本中以「第一章：XXX」、「第二章：XXX」等標頭文字明確標示。每個章節應聚焦於單一主題（如篩選、分析、交易估價、自我精進），以利於後續的格式化、字幕切割、圖片生成，以及 YouTube 時間軸 (Chapters) 的自動生成。
   * ⏸️ **[等待審查]** 使用者人工審查初稿。
2. **[AI 執行] 腳本一校**：AI 根據使用者提供的「修改原則」進行調整，產出 `腳本-step2.txt`。
   * ⏸️ **[等待審查]** 使用者確認內容無誤，回覆「腳本-step2.txt 可定案」。
3. **[AI 執行] 腳本格式化**：AI 修改並執行 `format_script.py`，加入章節標記 (`>>>>`) 與轉場標記 (`@@@@`)，限制每句字數，產出 `腳本-step3.txt`。
4. **[AI 執行] 腳本二校**：AI 根據使用者針對 Step3 的微調要求，產出最終版 `腳本-step4.txt`。
   * ⏸️ **[等待審查]** 使用者確認並回覆「腳本-step4.txt 可定案」或「腳本-step4.txt 無誤」。
   * ⚠️ **【鐵律】必須等待使用者明確表示 step4 無誤後，才能進入 Step 5 生成語音檔，絕對不可提前自動執行語音合成！**

### Phase 2: 語音與行銷素材生成
5. **[AI 執行] 批量語音合成與發音對照**：**（須先取得 Step 4 審查通過）** AI 修改並執行 `generate_audio.py` (更新 Book ID)，呼叫 Edge-TTS 將 Step4 腳本轉換為 `txt130` 與 `voice130` 內的檔案，確保空行也能正確產生靜音檔。同時，腳本會自動在 `raw/` 目錄下多生成一個對照清單 `發音人清單.csv`，完整紀錄每一個分段音檔的發音人標記（如：。、。。、。。。）、對應的角色名稱（如：AA、BB、CC）、TTS語音引擎以及對應的文字內容前50字，以利於進行配音完整度與角色分配的稽核。
6. **[AI 執行] YouTube Meta 生成**：AI 根據書籍內容與行銷原則生成主標題、副標題、縮圖標題、SEO Tags、影片說明等，並存入 `B130_XXX/raw/info.txt`。
   * 💡 **【YouTube 標題與縮圖行銷設計原則】**：
     1. **品牌與書名雙重定錨 (Double-Anchoring Format)**：影片主標題與縮圖標題開頭格式必須結合「知名品牌/主角」與「書名」，例如：`《知名品牌・書名》`（如《SpaceX・衝向火星》），在 0.5 秒內點出核心主題。
     2. **高衝突悖論對比 (High-Contrast Paradox)**：標題應強烈呈現角色的「谷底逆境」（如：連環爆、幾乎賣房破產）與「峰值成就」（如：兩兆美元、史上最高金額IPO）之反差，利用矛盾與反直覺激發點閱慾望。
     3. **客觀張力代替浮誇渲染 (Objective Tension over Hype)**：拒絕使用「驚天」、「最瘋狂」、「破銅爛鐵」等俗套形容詞；改用具戲劇張力的客觀事實與專業詞彙（如「連環爆」、「幾乎賣房破產」、「商業帝國」、「IPO」），維持高端知識型頻道的專業格調。
     4. **縮圖雙句分工 (Thumbnail Text Separation)**：
        - *第一句 (吸睛張力)*：放置高衝突對比或巨額數字（如：從破產邊緣到2兆美元商業帝國）。
        - *第二句 (主題定錨)*：固定放置品牌與書名（如：SpaceX・衝向火星），建立頻道的品牌辨識度。
   * ⏸️ **[等待審查]** AI 必須在此暫停，提醒使用者審查並確認 `info.txt` 中的「主標題」與「縮圖標題」是否無誤。必須在使用者確認無誤後，方可繼續後續的縮圖生成與合成。
7. **[人工準備] 視覺素材收集**：
   * ⏸️ **[等待上傳]** AI 提醒使用者提供並上傳：作者大頭照、書籍封面 (`中文封面` / `原文封面`)，確認 `AV` 目錄已包含標準命名的 `訪談START.mp4` 與 `訪談END.mp4`。

### Phase 3: 影像生成規劃與製作
8. **[AI 執行] 分段生圖腳本與網頁生圖自動化**：
   - **A. 生成 CSV**：AI 修改並執行 `generate_prompts.py`，將腳本切分為約 30-47 段，並生成 1:1 解析度的生圖 Prompt，匯出至 `分段生圖腳本.csv`。
     * 💡 **【生圖 Prompt 設計三大核心原則】**：
       1. **語意貼合與動態故事性 (Narrative & Metaphorical Alignment)**：插圖設計必須更貼近分段 dialogue 內容、章節主旨及整本書的主底。應避免死板的財經概念平鋪直敘，改用具備故事性、敘事張力及隱喻性的視覺畫面（例如：以「時鐘內流沙化為金幣消逝」隱喻通膨侵蝕、以「深根發光的橡樹」隱喻複利成長、以「暴風雨中禪院內的打坐僧侶」隱喻面對波動的心不動）。
       2. **統一的現代商務水彩風格基底 (Business Watercolor Style)**：
          - 規格：`Aspect ratio 1:1, square format, exactly 1024x1024 resolution`。
          - 畫風描述：`premium modern business editorial watercolor illustration, richly visible cold-pressed paper texture, expressive charcoal linework, layered translucent watercolor washes, subtle light rays`。
          - 氛圍：`thoughtful, inspiring, and premium, not cartoonish and not fantasy`。
          - 色調：`deep navy blue, warm sand ivory, soft forest green, muted charcoal grey, and restrained gold accents`。
       3. **【鐵律】無文字與浮水印限制 (Strict Zero-Text Constraint)**：
          - Prompt 尾部必須附帶風格約束：`Absolutely no text, no words, no alphabet letters, no numbers, no logos, and no watermark visible anywhere. The image must communicate only through symbolic, clean visual concepts.`
     * 🛠️ **【沙盒環境下 Prompt 設計方法】**：因執行沙盒常無 API Key 權限，AI 應先在會話中讀取切段文字，運用自身的推理能力設計出 29-47 段故事性 prompts，並將這些 prompts 寫入/更新至 `generate_prompts.py` 來寫入 CSV，避開運行期 API 呼叫失敗。
   - **B. 自動化批量生圖 (ChatGPT/Gemini 雙引擎併發執行)**：AI 執行 `auto_generate_images.py`。
     * 🏎️ **雙引擎併發執行（平行工作）**：偶數編號的圖要用 ChatGPT 產生，奇數編號的圖用 Gemini 產生，可以平行工作。可併發啟動 ChatGPT（負責偶數編號圖片：`--engine chatgpt --even`）與 Gemini（負責奇數編號圖片：`--engine gemini --odd`），加速 50% 的生圖時間。
     * ⚙️ **獨立 Profile 避鎖**：ChatGPT 和 Gemini 必須分別使用獨立的 Playwright Profile（例如 `~/.playwright_chatgpt_profile` 與 `~/.playwright_gemini_profile`）以防同時開啟時發生 Chromium 的 Session 鎖衝突。
     * 🔑 **Gemini 傳送按鈕修復**：Gemini 輸入框中按 `Enter` 僅會換行，因此自動化腳本必須點擊 Send 按鈕（或使用 `Control+Enter` 組合鍵）以防 prompt 無法成功送出。
     * *操作指引*：Playwright 瀏覽器會以有頭模式（headless=False）啟動。AI 會提示使用者手動在視窗中一鍵登入 Google 帳號 `ealin.chiu@gmail.com`，完成後程式將自動批量輸入生圖。
     * *無損極速下載*：腳本整合了 Canvas 影像二進位提取下載器，可瞬間將 `blob:` 圖片解碼儲存為 `0.png`, `1.png`... 存入 `photo/bg{book_id}/`，並提供模擬 Hover 下載、Lightbox 下載、HTTP 下載與元素截圖等多重容錯備份機制。
9. **[AI 執行] YouTube 縮圖自動化合成**：
   - **A. 自動化生圖背景**：AI 提取 `info.txt` 中的「縮圖標題」及概念，使用 `generate_image` 繪圖工具**直接生成精美的高端水彩商務風格背景圖**。
     * ⚠️ **核心規範（防裁切安全邊距）**：Prompt 必須包含 **「構圖留白與防裁切安全區（Padded Safe Area）」** 指令，要求主體元素（如 Pi 符號、齒輪或地圖）在 1:1 的畫布中央縮小、精巧呈現，並在四周預留大面積純色/漸層水彩暈染。這樣在 PIL 自動裁切為 16:9（1920x1080）時，核心圖案能 100% 完整居中，絕不產生任何拉伸、截斷與失真。
   - **B. 複製背景圖**：將生成的背景圖存為 `photo/縮圖背景.png`。
   - **C. 自動執行合成**：AI 讀取 `info.txt` 獲得主標題與副標題（若副標題字數多，字體自動縮小 12~22 點以利排版美觀）。修改 `generate_thumbnail.py` 代碼的路徑、字體大小、封面貼法（可相容直立無旋轉 80% 貼齊右下，或傾斜旋轉 60% 懸浮），執行該腳本自動合成產出 `photo/youtube_thumbnail.png`。

### Phase 4: 渲染前置檢查與輸出
10. **[AI 執行] 渲染參數更新**：AI 檢查並修改主渲染腳本 `BBD_video_generator_2026.py` 中的 `book_ID` 與相關路徑設定。
11. **[AI 執行] 最終就緒度檢查**：AI 修改並執行 `check_readiness.py`，全面檢查：
    - `info.txt` 欄位完整性。
    - `youtube_thumbnail.png` 是否存在。
    - `txt` 與 `voice` 檔案數量是否 1:1 完美一致。
    - `發音人清單.csv` 是否生成，且檔名與語音檔 100% 一致。
    - 頭像、標準命名的過場影片 (`訪談START.mp4` 與 `訪談END.mp4`)、封面圖是否存在。
    - `bg{book_id}` 中的背景插圖數量與檔案連續性（均由 Step 8B 自動化下載儲存完成）。
    * ⏸️ **[等待補件]** 若檢查有缺漏，AI 會列出清單提醒使用者補齊；若全數通過 (✓ READY)，則通知使用者準備渲染。
12. **[人工執行] 最終渲染**：一切就緒，使用者可安心執行 `BBD_video_generator_2026.py`，產出最終影片素材 (`_sub`, `_img`, `_head`) 交由後製合成。

---
**💡 喚醒詞用法**：
之後您只要對我說：`「啟動 book2video skill，這次要處理的新書是 B130_致富心態」`，我就會自動展開 Phase 1 的第一步，並一路引導您完成整條生產線！
