import os
import csv
import math

def generate_csv():
    script_path = "129_20260508_外資這樣買半導體股/raw/腳本-step4.txt"
    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    blocks = [b.strip() for b in content.split('\n\n') if b.strip()]
    
    # Calculate how many blocks per segment for exactly 32 segments
    # 220 blocks // 32 = 6 blocks per segment
    # Let's aim for 30-35 segments
    blocks_per_segment = len(blocks) // 31
    
    segments = []
    for i in range(0, len(blocks), blocks_per_segment):
        segment_text = "\n".join(blocks[i:i+blocks_per_segment])
        if segment_text.strip():
            segments.append(segment_text)
            
    # Base prompt (approx 400 words)
    base_prompt = (
        "Aspect ratio 1:1, square format, exactly 1024x1024 resolution. This image must be an absolute masterpiece of visual storytelling, "
        "designed specifically to captivate an audience interested in high-level financial analysis and global semiconductor markets. The visual style is an "
        "exquisite watercolor realism, intricately characterized by high-quality commercial magazine illustration aesthetics, avoiding any trace of flat, "
        "cartoonish, or overly simplistic vector art. Rich, deeply visible cold-pressed paper textures and highly expressive, artistic wet-on-wet brushstrokes "
        "are prominently featured throughout the entire canvas, giving the artwork a tangible, physical presence. The composition is exceptionally detailed "
        "and meticulously balanced, featuring a highly sophisticated color palette that seamlessly blends deep, moody atmospheric tones—such as midnight blues, "
        "rich indigos, and deep forest greens—with radiant, luminous highlights of electric cyan, glowing amber, and opulent gold. The lighting design is "
        "dramatic, theatrical, and highly cinematic, casting soft, diffused shadows while creating a premium, luxurious, and exclusive atmosphere. "
        "Absolutely no text, no words, no alphabet letters, and no numerical characters should be visible anywhere in the image; the communication must be "
        "entirely visual and symbolic. The aesthetic should be extremely polished, elegant, and sophisticated, evoking the feeling of reading a prestigious "
        "luxury financial periodical or stepping into the private, quiet study of an elite, seasoned institutional investor. The artwork should masterfully "
        "bridge the gap between traditional fine art techniques and modern digital conceptual design, utilizing deliberate ink spatters, delicate and precise "
        "line work, and multiple transparent layered watercolor washes to build immense depth, volume, and visual complexity. The overall mood should be "
        "intellectually stimulating, thought-provoking, and deeply engaging, perfectly capturing the high-stakes essence of global macroeconomic shifts, "
        "rapid technological advancement, and meticulous long-term investment strategies. Every single detail, from the macro structures to the micro textures, "
        "must be rendered with sharp, hyper-realistic precision, ensuring a high-definition presentation that is flawless. The watercolor brushstrokes should "
        "feel incredibly organic, chaotic, and fluid, standing in stark, beautiful contrast with the precise, rigid geometric shapes of any technological "
        "elements present, creating a powerful visual metaphor for the dynamic intersection of human psychological intuition and the cold, hard, calculating "
        "nature of market data. The atmosphere is simultaneously tense and serene, reflecting the volatile, unpredictable nature of the global stock market "
        "and the supreme calm, disciplined mindset required to navigate it successfully and profitably. This piece must resonate with themes of wealth "
        "generation, strategic foresight, and technological supremacy. "
    )
    
    # Specific concepts for each segment
    concepts = [
        # 1-10
        ("開場與散戶困境", "A lone investor looking at a confusing, abstract maze made of red and green stock market candles, surrounded by falling golden coins."),
        ("外資觀點與韓國市場", "A stylized map of East Asia, with glowing connection lines between South Korea and Taiwan, illuminated by golden semiconductor chips."),
        ("破解投資謎團", "A glowing key made of complex silicon circuitry unlocking a heavy, ancient vault door that reveals a bright, golden light."),
        ("半導體的獨特面貌", "A futuristic semiconductor factory seamlessly blending with a tranquil, ancient Zen garden, symbolizing the hidden nature of the industry."),
        ("白菜理論與成熟產業", "A surreal field where traditional green cabbages are growing side-by-side with glowing, crystalline silicon wafers under a moody sky."),
        ("PC到AI的週期演變", "A timeline represented by a flowing river of light, starting from chunky desktop computers and evolving into sleek, floating AI brains."),
        ("成熟資產的波動性", "A massive pendulum swinging back and forth over a landscape of circuit boards, representing the predictable yet dramatic swings of a mature market."),
        ("規格化產品與價格戰", "Multiple identical, glowing microchips lined up on an assembly line, with sharp red arrows pointing downwards, symbolizing price slashing."),
        ("龐大的建廠成本", "A colossal, monolithic factory under construction, with golden scaffolding and massive cranes, bathed in dramatic, cinematic sunlight."),
        ("庫存與缺貨循環", "A giant hourglass where golden sand flows down, turning into glowing microchips at the bottom, while the top remains empty, symbolizing scarcity."),
        # 11-20
        ("資本密集的護城河", "A deep, glowing moat filled with liquid gold surrounding a towering fortress made of stacked silicon wafers and servers."),
        ("寡占市場的優勢", "Three giant, glowing pillars rising above a stormy sea of data, representing the three dominant players in a consolidated market."),
        ("DRAM與NAND的差異", "A split screen concept: on one side, three harmonious glowing orbs; on the other, six aggressively colliding, sparking geometric shapes."),
        ("跟著外資看指標", "A glowing compass made of circuit board traces pointing towards a bright, golden star in a dark, starry night sky of financial data."),
        ("P/B比的秘密", "An elegant balance scale made of brass; one side holds a glowing microchip, the other holds a heavy gold bar, perfectly balanced."),
        ("三星的P/B區間", "A majestic mountain range where the peaks and valleys perfectly align with a glowing, undulating line graph representing historical P/B ratios."),
        ("買在景氣寒冬", "A solitary, glowing silicon wafer resting on a landscape of pristine, white snow, with a faint, warm sunrise breaking through dark winter clouds."),
        ("賣在獲利巔峰", "A triumphant, glowing golden bull standing on top of a peak made of stacked, gleaming semiconductors, bathed in bright, victorious sunlight."),
        ("SK海力士的鐘擺", "A magnificent, oversized grandfather clock where the pendulum is a giant, glowing microchip, swinging steadily between deep red and bright green zones."),
        ("買下公司淨值", "A transparent, glowing blueprint of a massive factory and its cash reserves, being wrapped in a golden ribbon, symbolizing buying at book value."),
        # 21-30
        ("散戶的追高迷思", "A flock of glowing birds flying towards a dangerously bright, burning sun made of stock charts, ignoring the safe, golden valleys below."),
        ("AI時代的質變", "A traditional silicon wafer transforming, pixel by pixel, into a luminous, hyper-intelligent, floating artificial brain emitting golden light."),
        ("HBM的強勢崛起", "A towering, multi-layered monolith of HBM memory chips, glowing with intense, radiant energy, standing above standard, flatter microchips."),
        ("資料傳輸的瓶頸", "A glowing hourglass where the neck is extremely narrow, but the liquid light flowing through it is blindingly bright and powerful."),
        ("SK海力士的領先", "A sleek, futuristic racing vehicle made of semiconductor materials speeding far ahead of its competitors on a track of glowing data streams."),
        ("台積電的神隊友", "Two massive, glowing gears—one representing memory, one representing logic—perfectly interlocking and turning together to generate immense power."),
        ("三星的絕地反擊", "A dormant, colossal technological volcano beginning to erupt with golden, glowing circuits and liquid data, symbolizing a powerful comeback."),
        ("先進封裝的戰局", "A complex, 3D puzzle made of glowing silicon blocks assembling itself in mid-air, surrounded by sparks of energy and technical blueprints."),
        ("散戶實戰守則", "A glowing, open book with pages made of light and financial charts, resting on a sturdy wooden desk alongside a compass and golden coins."),
        ("別買在超級週期", "A warning sign flashing in neon red over a chaotic, overly bright and crowded marketplace of floating semiconductor symbols."),
        ("等待打折出清", "A golden, glowing shopping cart filled with high-tech microchips, with a bright 'SALE' tag hanging from it, in a dark, calm warehouse."),
        # 31+
        ("獨立思考的價值", "A single, bright golden lightbulb glowing intensely among a sea of dark, unlit lightbulbs, symbolizing independent and clear investment thought."),
        ("結語與呼籲", "A majestic, glowing sunrise over a horizon made of silicon wafers, with a golden path leading the viewer towards a prosperous, technological future."),
        ("訂閱與按讚", "A subtle, elegant golden bell and a thumbs-up symbol naturally integrated into a beautiful, abstract watercolor landscape of data streams.")
    ]
    
    # Ensure concepts list is long enough
    while len(concepts) < len(segments):
        concepts.append(("延續探討", "An abstract, flowing composition of glowing data streams and golden watercolor washes, maintaining the intellectual and financial atmosphere."))
        
    # Write to CSV
    csv_path = "129_20260508_外資這樣買半導體股/raw/分段生圖腳本.csv"
    with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["段落編號", "段落內容", "插圖設計概念", "生圖 Prompt"])
        
        for i, segment_text in enumerate(segments):
            concept_title, concept_desc = concepts[i]
            
            # Combine base prompt with specific concept
            full_prompt = base_prompt + f"The central focus of this specific image is: {concept_desc}"
            
            writer.writerow([f"段落_{i+1:02d}", segment_text, concept_title, full_prompt])
            
    print(f"Excel (CSV) generated at {csv_path} with {len(segments)} segments.")
    
if __name__ == "__main__":
    generate_csv()
