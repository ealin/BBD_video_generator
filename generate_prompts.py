import os
import csv
import math

def generate_csv():
    script_path = "130_20260518_台灣半導體如何成為世界的心臟/raw/腳本-step4.txt"
    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    blocks = [b.strip() for b in content.split('\n\n') if b.strip()]
    
    # Calculate how many blocks per segment for exactly ~33 segments
    blocks_per_segment = len(blocks) // 31
    
    segments = []
    for i in range(0, len(blocks), blocks_per_segment):
        segment_text = "\n".join(blocks[i:i+blocks_per_segment])
        if segment_text.strip():
            segments.append(segment_text)
            
    # Base prompt (approx 400 words)
    base_prompt = (
        "Aspect ratio 1:1, square format, exactly 1024x1024 resolution. This image must be an absolute masterpiece of visual storytelling, "
        "designed specifically to captivate an audience interested in global semiconductor industry, high-tech history, and geopolitics. The visual style is an "
        "exquisite watercolor realism, intricately characterized by high-quality commercial magazine illustration aesthetics, avoiding any trace of flat, "
        "cartoonish, or overly simplistic vector art. Rich, deeply visible cold-pressed paper textures and highly expressive, artistic wet-on-wet brushstrokes "
        "are prominently featured throughout the entire canvas, giving the artwork a tangible, physical presence. The composition is exceptionally detailed "
        "and meticulously balanced, featuring a highly sophisticated color palette that seamlessly blends deep, moody atmospheric tones—such as midnight blues, "
        "rich indigos, and deep forest greens—with radiant, luminous highlights of electric cyan, glowing amber, and opulent gold. The lighting design is "
        "dramatic, theatrical, and highly cinematic, casting soft, diffused shadows while creating a premium, luxurious, and exclusive atmosphere. "
        "Absolutely no text, no words, no alphabet letters, and no numerical characters should be visible anywhere in the image; the communication must be "
        "entirely visual and symbolic. The aesthetic should be extremely polished, elegant, and sophisticated, evoking the feeling of reading a prestigious "
        "luxury technology periodical or stepping into the private, quiet study of a senior tech strategist. The artwork should masterfully "
        "bridge the gap between traditional fine art techniques and modern digital conceptual design, utilizing deliberate ink spatters, delicate and precise "
        "line work, and multiple transparent layered watercolor washes to build immense depth, volume, and visual complexity. Every single detail, from the "
        "macro structures to the micro textures, must be rendered with sharp, hyper-realistic precision. The watercolor brushstrokes should feel organic and fluid, "
        "standing in stark contrast with the precise, rigid geometric shapes of any technological elements present, creating a visual metaphor for the intersection "
        "of organic human history and the precise nature of silicon technology. "
    )
    
    # Specific concepts for each segment (total 33 concepts)
    concepts = [
        ("開場：世界的心臟", "A glowing island of Taiwan shaped like a golden, intricate computer chip, connected to the rest of the world by pulsing, glowing optical fiber cables across a dark blue ocean."),
        ("RCA計畫與一頓早餐", "A nostalgic 1970s American diner table with a coffee cup and an older handwritten plan on a napkin, with faint blue circuit traces starting to glow on the paper."),
        ("CMOS技術選擇的遠見", "A scientific diagram showing the CMOS architecture, illustrated as glowing, balanced golden circuits with green energy channels, representing efficiency and foresight."),
        ("工研院示範工廠", "A busy 1970s factory interior where young Taiwanese engineers in cleanroom suits are carefully aligning glowing glass photomasks under microscope lights."),
        ("VLSI計畫與聯電", "A giant microchip from the 1980s, showcasing micro-scale circuits, with the wordless layout glowing in vibrant blue, signifying technological scaling."),
        ("張忠謀與純晶圓代工", "An elegant, conceptual portrait of a visionary business leader's desk, featuring a clean silicon wafer on a stand, a drafting compass, and blueprint rolls under a single warm spotlight."),
        ("不與客戶競爭", "A hand holding a blank silicon wafer, surrounded by floating, diverse colorful chip designs from other companies, symbolizing neutral, dedicated service."),
        ("英特爾的品質認證", "A heavy, gold-embossed quality certificate showing a glowing checkmark, resting next to a pristine, highly detailed silicon wafer on a velvet cushion."),
        ("邏輯晶片vsDRAM", "A split composition: the left side shows highly complex, diverse logic circuit logic paths; the right side shows simple, repetitive grid cells of memory chips."),
        ("DRAM設計與製造耦合", "A double helix or interwoven golden gears, representing the tight integration of product design and manufacturing process in DRAM."),
        ("台灣DRAM失敗與警告", "A stormy sea with a lonely ship (representing a DRAM manufacturer) navigating giant waves, under dark clouds, with a faint red warning light on the horizon."),
        ("缺乏產品設計能力", "An empty architect's drawing board next to a busy, fully automated factory floor, symbolizing having the means of production but lacking the original design blueprint."),
        ("日本半導體興盛", "A triumphant rising sun casting golden light over a massive, ultra-modern factory in Tokyo, with five giant columns symbolizing the five major Japanese electronics conglomerates."),
        ("美日貿易協定", "A heavy metal stamp press coming down on a map of Japan, with sparks of electric blue flying, representing trade sanctions and restrictions."),
        ("PC-98與封閉系統", "A computer monitor showing a proprietary Japanese operating system interface, isolated on an island, while a global digital network passes it by in the background."),
        ("綜合電氣製造商弊端", "A giant tree with too many branches spreading out, each branch carrying different electronic products, causing the trunk to look strained under the weight."),
        ("韓國財閥與三星崛起", "A massive, powerful fortress made of steel and silicon, built by Samsung, standing firm against a stormy sea, with three pillars glowing in blue."),
        ("財閥的三大優勢", "A heavy golden vault, a cargo ship carrying electronics, and a government document with a stamp, symbolizing financial scale, market integration, and policy support."),
        ("中小企業vs大財閥", "A contrast between small, fragile wooden boats (中小企業) trying to survive a storm, and a colossal steel aircraft carrier (韓國財閥) cutting through the waves smoothly."),
        ("中國半導體的大基金", "A giant, golden container of liquid capital being poured onto a barren soil of silicon wafers, with new factories starting to sprout up like digital plants."),
        ("融入全球化與限制", "A glowing circuit board trying to connect to a global network, but blocked by a transparent, solid glass wall representing export restrictions."),
        ("中芯國際與梁孟松", "A bridge connecting two distinct tech hubs, with silhouettes of engineers crossing over carrying blueprint tubes, under a sky filled with shooting stars."),
        ("美國對華為海思制裁", "A glowing, advanced microchip being cut off from a power source by a heavy lock and key, with red warning alerts glowing around it."),
        ("微影技術的百年追光", "A series of lenses focusing light of progressively shorter wavelengths—from red, to green, to ultraviolet—onto a microscopic silicon target."),
        ("浸潤式微影與折射水", "A beam of bright laser light passing through a pure, clear droplet of water onto a silicon wafer, bending the light to make it sharper and more precise."),
        ("物理極限與EUV艱難", "A massive, futuristic machinery room where an ultra-complex EUV light source is generated by laser pulses hitting tin droplets, radiating a brilliant, white-blue light."),
        ("ASML在荷蘭的壟斷", "A monolithic, extremely advanced EUV lithography machine built by ASML, surrounded by international flags and component blueprints, representing global reliance."),
        ("矽盾與地緣政治", "A protective, glowing blue shield formed by layers of silicon wafers and circuits, enclosing a beautiful, prosperous island of Taiwan under a starry night sky."),
        ("美國晶片法案與亞利桑那", "A construction site of a massive wafer factory in the middle of a dry, hot Arizona desert, with giant cranes and steel structures under a bright sun."),
        ("日本熊本建廠與黑船", "A traditional Japanese castle in Kumamoto, with a modern, high-tech cleanroom facility integrated inside it, under cherry blossom trees in full bloom."),
        ("歐盟晶片法與德國廠", "An industrial park in Dresden, Germany, surrounded by old European architectures, with a new semiconductor fab under construction and glowing digital roads."),
        ("小循環與供應鏈裂解", "A globe showing localized, independent loops of supply chains in North America, Europe, and Asia, yet all still connected by a single thread of technology."),
        ("結語：未來的挑戰與啟示", "A forward-looking view of a modern research lab, where next-generation 3D-stacked chips are being designed, under a bright, promising morning sun.")
    ]
    
    # Ensure concepts list is long enough
    while len(concepts) < len(segments):
        concepts.append(("延續探討", "An abstract, flowing composition of glowing data streams and golden watercolor washes, maintaining the intellectual and financial atmosphere."))
        
    # Write to CSV
    csv_path = "130_20260518_台灣半導體如何成為世界的心臟/raw/分段生圖腳本.csv"
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
