import os
import csv

def find_book_dir(book_id):
    for item in os.listdir('.'):
        if os.path.isdir(item) and (item.startswith(f"{book_id}_") or item.startswith(f"B{book_id}_") or item.startswith(f"1{book_id}_") or item.startswith(f"{book_id}-") or item.startswith(f"B{book_id}-") or item.startswith(f"1{book_id}-")):
            return item
    raise FileNotFoundError(f"Cannot find book directory starting with {book_id}_")

def generate_csv():
    # 檔案路徑與設定
    book_id = "144"
    book_dir = find_book_dir(book_id)
    txt_dir = os.path.join(book_dir, "raw", f"txt{book_id}")
    csv_path = os.path.join(book_dir, "raw", "分段生圖腳本.csv")
    
    # 1. 讀取所有切分好的單句文字檔
    if not os.path.exists(txt_dir):
        print(f"Error: Directory {txt_dir} does not exist.")
        return
        
    txt_files = sorted([f for f in os.listdir(txt_dir) if f.endswith(".txt") and not f.startswith('.')])
    print(f"Found {len(txt_files)} block files in {txt_dir}.")
    
    blocks = []
    for f_name in txt_files:
        p = os.path.join(txt_dir, f_name)
        with open(p, 'r', encoding='utf-8') as f:
            blocks.append(f.read().strip())
            
    total_blocks = len(blocks)
    if total_blocks == 0:
        print("Error: No block files read.")
        return

    # 2. 段落分組邏輯：與 BBD_video_generator_2026.py 動態匹配
    BLOCKS_PER_SEGMENT = 10
    max_seg_id = 1 + (total_blocks - 14) // BLOCKS_PER_SEGMENT
    total_segments = max_seg_id + 1
    print(f"Total blocks: {total_blocks}. MoviePy segments needed: {total_segments} (seg_id 00 to {max_seg_id:02d}).")
    
    seg_blocks = {i: [] for i in range(total_segments)}
    
    for idx, block_text in enumerate(blocks):
        block_count = idx + 1 # 1-based index
        if block_count < 14:
            seg_id = 0
        else:
            seg_id = 1 + (block_count - 14) // BLOCKS_PER_SEGMENT
            if seg_id >= total_segments:
                seg_id = total_segments - 1
        seg_blocks[seg_id].append(block_text)
        
    # 3. 基礎生圖設計風格 (B144: 現代商務水彩風格 - AI 協作與產品經理主題)
    base_prompt = (
        "Aspect ratio 1:1, square format, exactly 1024x1024 resolution. Create a premium modern business editorial watercolor illustration "
        "for a professional book summary video about product management and AI agents. The visual style must combine "
        "sophisticated software design concepts, digital collaboration, and poetic storytelling. Use richly visible cold-pressed paper texture, "
        "expressive charcoal linework, layered translucent watercolor washes, and subtle light rays. The mood should be thoughtful, "
        "inspiring, and premium, not cartoonish and not sci-fi fantasy. Use a sophisticated, harmonious color palette of deep indigo blue, "
        "warm sand ivory, soft olive green, muted charcoal grey, and restrained gold accents. "
        "Absolutely no text, no words, no alphabet letters, no numbers, no logos, and no watermark visible anywhere. "
        "The image must communicate only through symbolic, clean visual concepts. "
    )

    # 35組針對每個分段精心設計的「故事性/隱喻性」視覺概念
    concepts = [
        (
            "開場：撕開PM的「技術焦慮」與依賴循環",
            "A professional product manager sitting at a desk surrounded by abstract locks, with lines connecting to glowing servers and floating code blocks in the background."
        ),
        (
            "PM看不懂代碼陷入的依賴循環",
            "A person standing in front of giant interlocking gear wheels that are tangled with lines of code, waiting for a developer to turn them."
        ),
        (
            "等上兩天或更久的無奈",
            "A classic hourglass on a wooden desk, sand flowing slowly, with shadows of calendars and clock faces on the wall."
        ),
        (
            "對話式與代理式 AI 的區別",
            "A split concept illustration. Left: a simple chat bubble icon. Right: autonomous glowing AI agent birds flying between files and blueprint drawings."
        ),
        (
            "AI 可以直接讀寫項目文件，在硬碟上生成分析報告",
            "An invisible hand composed of particles flipping pages and editing blueprints and code files on a desk."
        ),
        (
            "直接讀寫 Jira、Slack、Figma 和數據庫",
            "A shining tech tree where branches grow into icons representing project tracking, database, chat, and UI design."
        ),
        (
            "非技術背景 PM 面對終端機退縮",
            "A product manager looking at a large glowing green matrix terminal screen on a dark wall, showing minor hesitation."
        ),
        (
            "終端中按 Shift+Tab AI 生成文檔",
            "A finger pressing a key on a glowing computer keyboard, causing clean documents and PDF files to float up from the screen."
        ),
        (
            "調查功能「What data does feature access?」",
            "A large glowing magnifying glass magnifying rows of tables and data flow streams inside a database cylinder."
        ),
        (
            "四大模式覆蓋了 PM 調查功能的絕大多數場景",
            "A compass pointing to four distinct glowing quadrants on a map, symbolizing four investigation scenarios."
        ),
        (
            "安全漏洞分析與性能瓶頸",
            "A complex glowing circuit maze with red warning dots at key intersections, being analyzed by a probe of light."
        ),
        (
            "不僅是技術問題，更是團隊協作的藝術",
            "A puzzle where a hand of a PM and a hand of a developer fit the final glowing piece together."
        ),
        (
            "步驟 4：形成可測試的假設",
            "A balancing scale, balancing a glowing lightbulb idea on one side and a scientific flask and ruler on the other."
        ),
        (
            "利用 Claude Code 進行競品與市場分析",
            "A person looking through binoculars from a peak toward digital mountains, paper planes with charts flying in the sky."
        ),
        (
            "Claude Code 可以存取網路，自己搜索最新資料",
            "Shining virtual swallows flying through cloud networks, gathering glowing golden fibers and bringing them to a notebook."
        ),
        (
            "強在能幫您結構化您的方法論，並讓假設顯性化",
            "A 3D transparent geometric grid structure where nested assumptions and boxes are organized perfectly."
        ),
        (
            "呈現給高管層的市場估算報告",
            "A sunlit meeting room white-board showing a golden arrow curve shooting straight upward."
        ),
        (
            "昨天有一個 VIP 客戶在大發雷霆要求功能",
            "A bolt of lightning striking a server rack and user feedback cards, creating pressure and urgency."
        ),
        (
            "反饋工單中往往帶有客戶的隱私資料",
            "A digital folder locked by a glowing security lock, protecting personal text cards inside."
        ),
        (
            "提示詞跑步機（Prompt Treadmill）",
            "A person running on a glowing treadmill, chasing a carrot shaped like a perfect prompt word hanging in front."
        ),
        (
            "包含名稱和用來觸發 AI 的技能描述",
            "An open ancient scroll filled with modern API code scripts and functional configurations."
        ),
        (
            "5 大實用工具（反饋綜合器、競品掃描器等）",
            "A wooden toolbox opened, revealing five distinct glowing tech tools, each emitting a different colored light."
        ),
        (
            "是否有未說明的待辦項目？",
            "A check list with almost all items checked, with one last unchecked item glowing softly in the dark."
        ),
        (
            "這對 PM 的工作效率意味著效率大躍升",
            "A glowing mechanical bird soaring high, carrying a PM silhouette above mountains of paperwork."
        ),
        (
            "分析研發留言，找出未解決的技術依賴",
            "A beam of searchlight illuminating a network of developer comments, highlighting a red warning chain icon."
        ),
        (
            "PM在使用數據庫 MCP 拉取指標時必須連接到唯讀從庫",
            "A faucet with blue water of binary codes connected to a safe, read-only water tower next to a main server."
        ),
        (
            "PM什麼時候需要派生子代理？這會帶來成本負擔嗎？",
            "A main bubble splitting into smaller sub-agents, with floating dollar sign shadows below them."
        ),
        (
            "子代理模式中主代理扮演協調者",
            "An orchestral conductor leading several musicians with different instruments, guiding them into harmony."
        ),
        (
            "每個子代理都要重新讀取基礎文件並載入環境",
            "Multiple scholars studying the same massive book on a table, with sandglasses symbolizing redundant tasks."
        ),
        (
            "底線：PM絕對不要用 Claude Code 去修改生產代碼庫！",
            "A thick red laser line blocking access to a glowing, complex central system core representing production codebase."
        ),
        (
            "引導文件變成了團隊唯一的真實來源，兩邊對接",
            "A bridge connecting two cliffs. On one side a PM, on the other an engineer. An open, glowing manual floats at the center."
        ),
        (
            "AI 擅長處理具體、覆蓋面小的局部任務",
            "A microscope zooming in on a tiny silicon chip, performing detailed soldering in a microscopic view."
        ),
        (
            "AI會開始變得丟三落四、反覆給出已被否定的建議",
            "A confused robot holding its head, surrounded by scattered notes and canceled sketches."
        ),
        (
            "剛學會寫技能就寫了極其複雜的年度審查技能",
            "A person using a giant complex steam-punk machine to prune a tiny daisy flower, representing over-engineering."
        ),
        (
            "謝謝 Robin，也謝謝大家的收聽！",
            "A warm study desk at night, illuminated by a reading lamp, with the book and a steaming cup of tea on it."
        )
    ]

    # 安全檢查：若分段數與我們的設計不符，發出警告並使用線性插值 fallback
    if len(concepts) != total_segments:
        print(f"Warning: concepts list size ({len(concepts)}) does not match total_segments ({total_segments}). Using interpolation fallback.")
        use_direct_mapping = False
    else:
        use_direct_mapping = True

    # 4. 對應生成 Prompts 並寫入 CSV
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["段落編號", "段落內容", "插圖設計概念", "生圖 Prompt"])
        
        for seg_id in range(total_segments):
            segment_text = "\n".join(seg_blocks[seg_id])
            
            if use_direct_mapping:
                concept_title, concept_desc = concepts[seg_id]
            else:
                concept_idx = min(int(seg_id * len(concepts) / total_segments), len(concepts) - 1)
                concept_title, concept_desc = concepts[concept_idx]
            
            # 生成序號（從 00 開始）
            seq_num = f"{seg_id:02d}"
            full_prompt = base_prompt + f"The central focus of this specific image is: {concept_desc}"
            numbered_prompt = f"{seq_num}. {full_prompt}"
            
            writer.writerow([f"段落_{seg_id+1:02d}", segment_text, concept_title, numbered_prompt])
            
    print(f"Excel (CSV) generated at {csv_path} with {total_segments} segments.")

if __name__ == "__main__":
    generate_csv()
