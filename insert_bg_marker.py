import csv

script_path = "129_20260508_外資這樣買半導體股/raw/腳本-step4.txt"
csv_path = "129_20260508_外資這樣買半導體股/raw/分段生圖腳本.csv"
output_path = "129_20260508_外資這樣買半導體股/raw/腳本-step5.txt"

# 讀取腳本區塊
with open(script_path, 'r', encoding='utf-8') as f:
    content = f.read()
blocks = [b.strip() for b in content.split('\n\n') if b.strip()]

# 讀取 CSV 以獲取分段資訊
# 我們之前在 generate_prompts.py 中是用 blocks_per_segment = len(blocks) // 31 來分段的
# 為了最準確，我們直接讀取 CSV 的「段落內容」
segments_from_csv = []
with open(csv_path, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        segments_from_csv.append(row['段落內容'].strip())

# 建立新的腳本內容
new_content = []
current_block_idx = 0

for seg_text in segments_from_csv:
    # 在每個分段開頭加入 _bg
    new_content.append("_bg")
    
    # 計算這個分段包含多少個 block
    # 由於 CSV 中的段落內容是用 \n 合併的 block，我們可以根據 \n 拆分回來的數量來判定
    # 或者是直接比對文字
    seg_blocks = [b.strip() for b in seg_text.split('\n') if b.strip()]
    
    for _ in range(len(seg_blocks)):
        if current_block_idx < len(blocks):
            new_content.append(blocks[current_block_idx])
            current_block_idx += 1

# 寫入檔案
with open(output_path, 'w', encoding='utf-8') as f:
    f.write("\n\n".join(new_content))

print(f"腳本-step5.txt 已生成於 {output_path}")
