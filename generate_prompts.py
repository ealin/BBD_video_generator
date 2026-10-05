import os
import csv
import sys

def find_book_dir(book_id):
    for item in os.listdir('.'):
        if os.path.isdir(item) and (item.startswith(f"{book_id}_") or item.startswith(f"B{book_id}_") or item.startswith(f"1{book_id}_") or item.startswith(f"{book_id}-") or item.startswith(f"B{book_id}-") or item.startswith(f"1{book_id}-")):
            return item
    raise FileNotFoundError(f"Cannot find book directory starting with {book_id}_")

def generate_csv():
    # 檔案路徑與設定
    book_id = sys.argv[1] if len(sys.argv) > 1 else "146"
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
        
    # 3. 基礎生圖設計風格
    # 3. 基礎生圖設計風格
    if book_id == "147":
        theme = "mindsets, personal growth, and financial wisdom"
    elif book_id == "148":
        theme = "asset allocation, portfolio risk management, stock-bond-gold rotation, and financial freedom"
    else:
        theme = "value investing, stock picking, and financial statement analysis"
        
    base_prompt = (
        f"Aspect ratio 1:1, square format, exactly 1024x1024 resolution. Create a premium modern business editorial watercolor illustration "
        f"for a professional book summary video about {theme}. "
        "The visual style must combine financial wisdom, corporate analysis, and poetic storytelling. Use richly visible cold-pressed paper texture, "
        "extremely faint and delicate pencil sketch outlines, highly blended translucent watercolor washes with soft transitions, and subtle light rays. "
        "No heavy black outlines, no comic book style, no harsh borders. The mood should be thoughtful, "
        "inspiring, and premium, not cartoonish and not fantasy. Use a sophisticated, harmonious color palette of deep navy blue, "
        "warm sand ivory, soft forest green, muted charcoal grey, and restrained gold accents. "
        "Absolutely no text, no words, no alphabet letters, no numbers, no logos, and no watermark visible anywhere. "
        "The image must communicate only through symbolic, clean visual concepts. "
    )

    if book_id == "147":
        concepts = [
            ("開場：財務痛點提問", "Emily holding a microphone in front of a modern city library, welcoming the audience. Soft watercolor."),
            ("鉤子與金錢現狀", "A person looking at a small empty wallet with a sad expression, while a golden path of keys floats in the sky."),
            ("哈維·艾克的嚴厲警告", "A teacher at a blackboard drawing a big question mark, indicating 'Don't believe a word'."),
            ("第一章：金錢的因果規律", "A beautiful watercolor oak tree with glowing roots underground and small apples above ground, highlighting 'invisible roots create visible fruits'."),
            ("實現程序公式 P-T-F-A-R", "A circular flowchart of glowing letters: P -> T -> F -> A = R, with light washes of ivory and navy."),
            ("制約管道一：語言設定", "A child listening to dark, heavy speech bubbles filled with warning signs, representing negative money words."),
            ("制約管道二：模仿", "A child watching parents argue over a broken piggy bank, reflecting modeling behavior."),
            ("制約管道三：特殊事件", "A dramatic event: a table with tea spilled, showing childhood financial trauma."),
            ("第二章：察覺與理解", "A person writing in a journal under a warm desk lamp, gaining self-awareness."),
            ("離析與宣告", "A person standing on a mountain peak, hand on chest, declaring new beliefs to the wind."),
            ("檔案1-我創造我的人生", "A pilot firmly holding the steering wheel of a small plane flying above the clouds."),
            ("受害者特徵與抱怨的代價", "A person pointing fingers at others in a stormy sea, wearing a victim tag."),
            ("檔案2-玩金錢遊戲是為了贏", "An archer aiming a bow at the bullseye of a target, pulling the arrow to win."),
            ("檔案3-致力於變得富有", "A warrior climbing a steep cliff in a storm, showing absolute commitment."),
            ("想要的三個層次", "A scholar writing 'I commit' on parchment with a gold quill."),
            ("檔案4-想得很大", "A captain of a giant container ship sailing into the open ocean towards a horizon of light."),
            ("檔案5-專注於機會與走廊理論", "A traveler walking towards a newly opened doorway glowing with soft green light, ignoring a dark wall."),
            ("踏上走廊實踐案例", "A person washing coffee cups in the back of a bustling cafe, looking through the door to the manager's office."),
            ("檔案6-欣賞有錢人", "A person clapping and smiling at a beautiful villa on a hill, showing genuine admiration and blessing."),
            ("檔案7-與成功人士交往", "A group of professionals sitting around a wooden table in a high-end club, discussing ideas."),
            ("檔案8-宣傳自我價值", "A presenter standing confidently on a stage, showcasing a glowing golden sphere of value."),
            ("檔案9-大於你的問題", "A giant standing tall, looking down at a small mountain peak, representing stepping over obstacles."),
            ("檔案10-是很棒的接受者", "A person opening their arms to catch falling stardust and golden raindrops from the night sky."),
            ("給予與接受的平衡", "A scale in perfect balance, with a heart on one side and a glowing coin on the other."),
            ("檔案11-根據結果拿酬勞", "A consultant shaking hands with a client, with a scoreboard in the background showing performance metrics."),
            ("時間與限制的代價", "An hourglass running out of sand, illustrating the limit of paying by time."),
            ("檔案12-兩個都要", "A scale holding both a stack of gold coins and a happy, healthy family portrait."),
            ("專注於淨值", "A scale balancing all assets (gold, houses, stocks) against liabilities, showing net worth."),
            ("淨值四要素一與二", "A person putting a gold coin into a clean piggy bank next to growing green plants."),
            ("淨值四要素三與四", "A simple cottage with a small vegetable garden, representing simple living, next to a growing chart."),
            ("檔案14-管理金錢", "Six glass jars on a table, each with a different colored ribbon and glowing contents."),
            ("理財分流六個帳戶系統", "A hand dividing gold coins into FFA (10%), Play (10%), etc."),
            ("檔案15-讓錢辛苦工作", "A tiny gold coin planted in soil, growing into a tree that produces more gold coins."),
            ("被動收入的自動運作", "A beautiful windmill turning on a green hill, producing power automatically."),
            ("檔案16-恐懼中採取行動", "A climber stepping off a ledge into the air, connected by a secure golden rope, face showing focus."),
            ("舒適區等於財富區", "A circular outline representing comfort zone expanding outwards to include new territory."),
            ("檔案17-持續學習成長", "A pile of leather-bound books with a small green sprout growing from the top book."),
            ("成為-去做-擁有", "A staircase with labels 'Be' at the bottom, 'Do' in the middle, and 'Have' at the top."),
            ("現在該做什麼", "A person touching their forehead with a smile, in front of a warm golden sunrise, declaring success.")
        ]
    elif book_id == "148":
        concepts = [
            ("開場與小林醫生的焦慮", "An exhausted surgeon in scrubs leaning against a sterile hospital hallway wall, holding a glowing vintage hourglass. Soft watercolor style."),
            ("財務自由與儲蓄的界限", "A person stacking gold coins inside a dark stone vault, while a giant dark shadow symbolizing inflation looms outside. Warm sand and navy watercolor washes."),
            ("老闆錢包的起點：馬可維茲", "A classic brass scale balancing a colorful globe (representing VT) on one side and a stack of bonds (representing BNDW) on the other. Delicate watercolor wash."),
            ("老闆錢包的兩大核心", "A merchant ship navigating a calm, deep navy sea guided by two lighthouses: one glowing warm green, the other soft blue. Poetic watercolor style."),
            ("股債比例的選擇", "A person at a wooden desk holding a brass compass, pointing to a circular pie chart divided into 80% growth and 20% stability sectors."),
            ("再平衡的魔法：低買高賣", "A vintage wooden balance scale being adjusted by a hand, automatically transferring glowing gold dust from the higher side to the lower side."),
            ("再平衡的執行時機", "A vintage desk calendar with a specific date circled, next to a notebook showing a simple mathematical calculation with a gold pen."),
            ("黑天鵝的降臨與系統漏洞", "A giant dark wave rising behind a calm coastal town under a stormy purple sky, with a small sailboat securing its anchor. Dramatic watercolor wash."),
            ("防禦性槓鈴策略", "A barbell held by a hand: one giant heavy sphere represents 90% safe assets, and a tiny glowing gold sphere represents 10% high-reward risk assets."),
            ("四層防禦網的概念", "A medieval stone fortress with four concentric circular walls surrounding a glowing treasure chest, protected from a distant lightning storm."),
            ("第一與第二層防線：緊急金與保險", "A warm, cozy living room with a glowing fireplace, protected from a heavy rainstorm outside by a giant golden shield overhead."),
            ("第三與第四層防線：生活債券與老闆錢包", "A stone bridge supported by strong arches connecting a personal house to a vibrant marketplace, symbolizing stability and growth."),
            ("時間分散與生命週期配置", "A winding mountain road: a young traveler with a backpack walks towards a bright sunrise, while an elderly traveler rests in a sunlit garden."),
            ("年輕人的成長包配置", "A young green seedling sprouting vigorously from rich soil, bathed in warm sand-colored sunbeams. Clean, symbolic watercolor."),
            ("開槓桿與年齡的智慧", "A mechanical gear system multiplying a small force into a larger motion, with a glowing symbol of '30% leverage' on a parchment paper."),
            ("退休族的價值包配置", "A mature orchard in autumn, trees laden with ripe red apples, representing harvest, security, and stability. Soft forest green and gold accents."),
            ("資產輪動的必要性", "A circular track where a runner in a navy uniform passes a glowing baton to a runner in a gold uniform, under a peaceful sky."),
            ("密西西比泡沫的教訓", "An 18th-century French marketplace where merchants trade paper bank notes for barren land plots, while gold coins are hidden away in dark chests."),
            ("法幣與實物資產的對比", "A hand holding a paper bank note dissolving into ashes in the wind, while the other hand holds a solid gold coin glowing with light."),
            ("黃金作為防禦性資產", "A solid, shining gold bar acting as a shield, blocking a lightning bolt from a dark storm cloud. Poetic watercolor wash."),
            ("道瓊/黃金比值 (Dow/Gold Ratio)", "A vintage balance scale with a factory gear (stocks) on one side and a gold ingot (gold) on the other, showing their ratio. Navy and gold accents."),
            ("小金庫輪動策略", "A clean concept drawing with gold and navy arrows showing the mechanical flow of buying gold when stocks are expensive, and vice versa."),
            ("比值大於20的避險操作", "A red warning lantern glowing next to a bubble bath, with a hand moving gold ingots into a secure vault. Faint pencil sketch outlines."),
            ("比值小於5的抄底操作", "A green lantern glowing next to a fertile plowed field, with a hand planting glowing seeds (stocks). Soft green and warm sand washes."),
            ("歷史實證：穿越百年的策略", "A timeline chart showing historical years 1929 and 2000, with a gold curve climbing steadily while a red stock curve drops and recovers."),
            ("總結：永不崩盤的財富金字塔", "A majestic golden pyramid standing stable in a vast desert under a clear blue sky, glowing in the warm sunrise. Premium watercolor wash.")
        ]
    else:
        # B146 concepts (fallback)
        concepts = [
            ("第一章 開場：走向價值投資之路", "A thoughtful traveler standing at a fork in a mountain road, one path covered in sharp dark thorns representing chaotic stock trading, the other path paved with glowing golden bricks leading to a beautiful sunrise symbolizing financial freedom."),
            ("第一章 評估公司與思考市場", "A split concept illustration. On the left side, a hand uses a vintage magnifying glass to inspect a gold-plated machine. On the right side, a stormy, emotional sea represents the volatile market."),
            ("第一章 六步驟價值投資SOP架構", "A circular diagram representing six stepping stones crossing a calm blue river, with a glowing temple on the far bank, illustrating a systematic investment process."),
            ("第二章 三大財務指標防線", "Three sturdy shields standing on a stone platform, labeled with gold engravings, protecting a chest of gold coins from heavy rain, symbolizing ROE, Free Cash Flow, and Earnings Quality."),
            ("第二章 ROE 的動態過濾網", "A massive funnel filtering out dark stones, leaving only shining golden gemstones representing companies with high ROE."),
            ("第二章 每股自由現金流防禦", "A golden umbrella shielding a growing green plant from a heavy downpour of financial red graphs, representing cash flow protection."),
            ("第二章 董監持股與誠信門檻", "A captain at the ship's wheel looking forward, holding hands with the passengers, showing shared destination and trust."),
            ("第二章 獲利能力矩陣：A級企業", "A pristine, golden cash-printing machine in a bright library, printing bills smoothly, representing an A-grade cash generator."),
            ("第二章 獲利能力矩陣：B一級高成長股", "A growing rocket booster being built in a high-tech workshop, surrounded by pipes and equipment, waiting for fuel, representing high-growth stocks."),
            ("第二章 獲利能力矩陣：B二級與C級淘汰", "A mature windmill turning slowly in a quiet meadow representing B2-grade stocks, while a broken, dark coal factory stands abandoned in the distance representing C-grade stocks."),
            ("第三章 資產負債表安全防線", "A strong, ancient stone castle wall standing tall against high tidal waves, protecting a peaceful town."),
            ("第三章 好債：無息貸款與談判籌碼", "A merchant receiving goods from suppliers with friendly handshakes, showing trust and bargaining power."),
            ("第三章 壞債的利息重擔", "A person climbing a mountain carrying a heavy iron ball labeled with bank debt, showing financial leverage load."),
            ("第三章 股東權益與淨值含金量", "A treasure chest where the main storage is a deep golden lake of accumulated wealth, representing retained earnings."),
            ("第三章 損益表與長期增長力道", "A merchant ship sailing with full sails on a golden sea, loaded with boxes of cargo, showing quantity and price growth."),
            ("第三章 十二月滾動營收年增率", "A navigator looking through a brass telescope, spotting a green lighthouse through the morning fog, predicting business turnaround."),
            ("第三章 雙率走勢同步向上", "Two golden arrows climbing steadily together on a grid board, moving upward towards the top right."),
            ("第三章 預估EPS的三個版本", "A scholar comparing three drafting designs on a wooden table: a conservative plan, a realistic plan, and a balanced plan."),
            ("第四章 閱讀年報與波特五力", "A scholar in a quiet library reading a massive leather-bound book, with five winds blowing against a candle, but the flame remains steady."),
            ("第四章 成本策略：規模與通路優勢", "A vast network of ships and roads carrying cargo across a map, showing deep logistical dominance."),
            ("第四章 差異化：技術與轉移成本", "A lock and key made of glowing golden code, holding a glowing database, showing high customer switching barrier."),
            ("第五章 本益比與盈餘殖利率", "A scale balancing a pile of gold coins against a simple price tag, indicating opportunity cost comparison."),
            ("第五章 高登公式的總報酬率", "A glowing glass orb filled with growing green vines and dripping gold coins, representing the compounding force of growth and yield."),
            ("第五章 本益比對應合理高價", "A graph showing three colored zones: a green low-price safety zone, a yellow fair zone, and a red hot zone."),
            ("第五章 安全邊際打折與過熱警訊", "A shield blocking falling arrows, while a warning red light glows at the top of a stone tower."),
            ("第五章 彼得林區評價法", "A researcher using a magnifier to look at a small sprout growing rapidly, outperforming nearby dry weeds."),
            ("第五章 巴費特指標與宏觀配置", "A captain adjusting the sails of a ship, keeping cash reserves high when the sea is stormy, and deploying nets when it is calm."),
            ("第六章 雷式GTD投資工作流", "A clean desk with a leather-bound folder, showing files organized neatly into distinct compartments: Inbox, Study, Watchlist, Portfolio.")
        ]

    # 安全檢查
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
            
            seq_num = f"{seg_id:02d}"
            full_prompt = base_prompt + f"The central focus of this specific image is: {concept_desc}"
            numbered_prompt = f"{seq_num}. {full_prompt}"
            
            writer.writerow([f"段落_{seg_id+1:02d}", segment_text, concept_title, numbered_prompt])
            
    print(f"Excel (CSV) generated at {csv_path} with {total_segments} segments.")

if __name__ == "__main__":
    generate_csv()
