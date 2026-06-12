import os
import csv

def find_book_dir(book_id):
    for item in os.listdir('.'):
        if os.path.isdir(item) and (item.startswith(f"{book_id}_") or item.startswith(f"B{book_id}_") or item.startswith(f"1{book_id}_")):
            return item
    raise FileNotFoundError(f"Cannot find book directory starting with {book_id}_")

def generate_csv():
    # 檔案路徑與設定
    book_id = "141"
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
        
    # 3. 基礎生圖設計風格 (B141 萬曆朝鮮戰爭全史：歷史水彩戰爭敘事插畫)
    base_prompt = (
        "Aspect ratio 1:1, square format, exactly 1024x1024 resolution. Create a premium historical editorial watercolor illustration "
        "for a Chinese-language history book summary video about the Imjin War, also known as the Wanli Korean War. The visual style must combine "
        "East Asian historical atmosphere, cinematic war-documentary composition, and refined commercial magazine illustration quality. Use richly visible "
        "cold-pressed paper texture, expressive ink linework, layered watercolor washes, mist, smoke, firelight, sea wind, old maps, armor silhouettes, banners, "
        "fortress walls, warships, diplomatic halls, and battlefield landscapes. The mood should be serious, epic, tragic, scholarly, and historically immersive, "
        "not cartoonish and not fantasy. Avoid modern objects, modern uniforms, modern weapons, anachronistic buildings, and exaggerated anime aesthetics. "
        "Absolutely no text, no words, no alphabet letters, no Chinese characters, no Korean Hangul, no Japanese kana, no numbers, no logos, and no watermark visible anywhere. "
        "The image must communicate only through symbolic historical visuals. Use a sophisticated palette of aged parchment ivory, ink black, muted Ming blue, "
        "deep ocean teal, smoky grey, burnt umber, blood-red banners, and restrained gold accents. Every scene should feel like a carefully researched historical "
        "painting with cinematic lighting, dramatic depth, balanced composition, and strong storytelling clarity. "
    )

    # 精巧的視覺設計概念庫 (Book 141 萬曆朝鮮戰爭全史)
    concepts = [
        ("開場：十六世紀東亞秩序的裂縫", "An old East Asian map spread across a wooden table, with three shadowed realms implied by different colored ink washes; storm clouds gather over the Korean peninsula, a compass and war drums nearby, representing the looming regional crisis."),
        ("作者分身與歷史訪談", "A quiet scholar silhouette in a Ming-style study, surrounded by open historical scrolls, ink brushes, and translucent battlefield visions rising from the pages, representing an authorial historical guide entering an interview."),
        ("豐臣秀吉統一日本後的野心", "A powerful warlord silhouette standing before a newly unified island realm, samurai banners and ships gathering behind him, distant mainland mountains fading across the sea, representing expansionist ambition after civil war."),
        ("對馬島的欺瞞外交", "A small misty island between two larger lands, with a fragile messenger boat crossing turbulent water and two sealed letters casting conflicting shadows, representing ambiguous diplomacy and mistranslation."),
        ("日軍渡海與釜山危機", "A fleet of wooden warships approaching a Korean coast under a red dawn, soldiers landing near burning watchtowers and frightened civilians fleeing in the distance, representing the sudden invasion."),
        ("東萊與彈琴臺的崩潰", "A besieged Korean fortress gate under smoke and arrows, exhausted defenders on the walls, while cavalry and musket smoke clash in a muddy field beyond, representing early battlefield collapse."),
        ("漢城、開城、平壤相繼陷落", "An empty royal road leading north through abandoned gates, scattered banners, refugees, and distant flames under a cold sky, representing the fall of the three capitals."),
        ("李舜臣與海上補給線", "Korean panokseon warships cutting through dark blue waves, cannon smoke and disciplined formations striking enemy supply ships, representing naval resistance and disrupted logistics."),
        ("明朝是否出兵的戰略抉擇", "A Ming court war council in a dim palace hall, generals and officials around a large border map, candlelight illuminating the Liaodong frontier and Korean peninsula, representing strategic deliberation."),
        ("沈惟敬與小西行長的灰色談判", "Two envoys seated across a low table in a tense military tent, behind them layered shadows of armies waiting outside, representing negotiation as delay, deception, and intelligence gathering."),
        ("明軍入朝與平壤大捷", "Ming troops assaulting a snow-covered fortress city with cannons, fire arrows, ladders, and banners in coordinated attack, dramatic winter smoke rising over the walls, representing the recapture of Pyongyang."),
        ("碧蹄館遭遇戰", "A chaotic winter road battle near a roadside station, cavalry and infantry colliding in close combat, fog, banners, and exhausted soldiers, representing uncertainty and contested victory."),
        ("晉州血戰與城池悲劇", "A Korean fortress surrounded by fire and smoke, defenders and civilians crowded on the walls, enemy banners pressing from all sides, representing a desperate siege and civilian catastrophe."),
        ("明日和談的兩頭欺瞞", "A split diplomatic scene with two separate courts connected by a thin distorted thread, sealed documents glowing in candlelight while masks hang above the table, representing contradictory promises and deception."),
        ("大坂冊封與和談破裂", "A grand but tense audience hall in Japan, a ceremonial envoy scroll presented under cold light, while a warlord's shadow looms angrily behind a screen, representing the collapse of diplomacy."),
        ("丁酉再亂再度燃燒", "A second wave of invasion under a dark red sky, coastal fortresses burning again, soldiers marching through smoke and devastated villages, representing renewed war and harsher destruction."),
        ("漆川梁海戰的慘敗", "A shattered fleet at night, broken masts and burning ships drifting in black water, with storm clouds and scattered survivors, representing a devastating naval defeat."),
        ("鳴梁海戰的逆轉", "A narrow turbulent strait with a few Korean warships holding formation against a much larger fleet, whirlpools and crashing waves creating dramatic tension, representing tactical brilliance against overwhelming odds."),
        ("南原與黃石山城的慘烈抵抗", "A mountain fortress and walled city under simultaneous siege, smoke, ladders, defenders, and civilians under a tragic dusk, representing brutal land warfare in southern Korea."),
        ("蔚山攻城與寒冬圍困", "A coastal Japanese fortress under winter siege, Ming and Korean troops surrounding walls through snow and smoke, starving defenders within, representing the Ulsan campaign."),
        ("泗川戰役與四路總攻的挫折", "A wide battlefield with divided Ming columns, sudden counterattack, smoke, broken siege lines, and confused banners, representing the risks of multi-front offensives."),
        ("順天倭城與撤退困局", "A fortified coastal castle beside dark water, trapped troops looking toward distant rescue ships, while allied fleets block the sea route, representing the difficult Japanese withdrawal."),
        ("露梁海戰與李舜臣之死", "A dawn naval battle filled with smoke, fire arrows, clashing ships, and a heroic admiral silhouette struck amid command flags, representing the tragic final sea battle."),
        ("日軍撤離與戰後廢墟", "A devastated Korean landscape after battle, abandoned armor, burned villages, returning refugees, and distant ships disappearing over a grey sea, representing the aftermath of invasion."),
        ("萬曆東征的歷史意義", "A solemn memorial landscape with Ming, Korean, and oceanic symbolic elements, broken weapons laid before a rising sun over a peaceful coastline, representing sacrifice, resistance, and restored regional order.")
    ]

    # 4. 對應生成 Prompts 並寫入 CSV
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["段落編號", "段落內容", "插圖設計概念", "生圖 Prompt"])
        
        for seg_id in range(total_segments):
            segment_text = "\n".join(seg_blocks[seg_id])
            
            # 使用線性插值將 total_segments 對應到 concepts 列表
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
