#!/usr/bin/env python3
"""
generate_prompts_v2.py
=======================
語意與金句驅動的分段生圖 Prompt 生成器 V2

工作流程：
1. 讀取 concepts_B{book_id}.csv 概念檔（由 Agent 閱讀腳本後產出）
2. 根據概念檔記載的 block_start 與 block_end，從 txt{book_id}/ 精確組合段落內容
3. 根據選定的藝術風格與情緒標記（mood_tag），組裝生圖 Prompt
4. 強制寫入「絕對無文字」規範（no text, no numbers, no words, no logos）
5. 輸出相容於後續自動生圖腳本的 raw/分段生圖腳本.csv
"""

import os
import csv
import sys

def find_book_dir(book_id):
    for item in os.listdir('.'):
        if os.path.isdir(item) and (
            item.startswith(f"{book_id}_") or item.startswith(f"B{book_id}_") or 
            item.startswith(f"1{book_id}_") or item.startswith(f"{book_id}-") or 
            item.startswith(f"B{book_id}-") or item.startswith(f"1{book_id}-")
        ):
            return item
    raise FileNotFoundError(f"Cannot find book directory starting with {book_id}_")

# 情緒標記 (mood_tag) 對應的風格修飾語映射
MOOD_MODIFIERS = {
    "EMPATHY": "Mood: anxious, relatable, urban pressure. Deep indigo and stormy gray watercolor washes with isolated warm ochre highlights.",
    "CLARITY": "Mood: enlightening, aha-moment. Soft amber watercolor glazes with warm light breaking through subtle umber shadows.",
    "RATIONAL": "Mood: professional, structured, trustworthy. Balanced composition with neat navy and ivory watercolor layering.",
    "TENSION": "Mood: dramatic, cautionary, urgent. Deep crimson and stormy dark blue watercolor washes with high contrast.",
    "NARRATIVE": "Mood: historical, cinematic, epic. Classic illustration style with period-accurate details and warm sepia watercolor glazes.",
    "REVELATION": "Mood: breakthrough, exciting, golden. Luminous golden sunrise palette with transparent watercolor layering.",
    "TRIUMPH": "Mood: confident, majestic, inspiring. Grand landscape style with majestic golden light and vibrant watercolor pigments."
}

def generate_csv():
    book_id = sys.argv[1] if len(sys.argv) > 1 else "148"
    book_dir = find_book_dir(book_id)
    txt_dir = os.path.join(book_dir, "raw", f"txt{book_id}")
    concepts_csv = os.path.join(book_dir, "raw", f"concepts_B{book_id}.csv")
    csv_path = os.path.join(book_dir, "raw", "分段生圖腳本.csv")

    if not os.path.exists(concepts_csv):
        # 備用檔名檢查
        alt_concepts = os.path.join(book_dir, "raw", f"concepts_{book_id}.csv")
        if os.path.exists(alt_concepts):
            concepts_csv = alt_concepts
        else:
            print(f"Error: Concepts CSV {concepts_csv} does not exist. Please create it first.")
            return

    if not os.path.exists(txt_dir):
        print(f"Error: Directory {txt_dir} does not exist.")
        return

    # 1. 讀取 concepts 檔
    concepts = []
    with open(concepts_csv, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            concepts.append(row)

    print(f"Loaded {len(concepts)} segment concepts from {concepts_csv}.")

    # 2. 基礎風格設定 (以使用者選定的水彩風格為預設)
    base_prompt = (
        "Aspect ratio 1:1, square format, exactly 1024x1024 resolution. "
        "Create a premium warm detailed watercolor style commercial illustration for a professional book summary video. "
        "The visual style must feature soft and warm colors, beautiful watercolor washes, gentle blending, and a cozy atmosphere. "
        "Absolutely no text, no words, no alphabet letters, no numbers, no logos, and no watermark visible anywhere. "
        "The image must communicate only through visual narrative and symbolic composition. "
    )

    # 3. 組裝 Prompt 並寫入 分段生圖腳本.csv
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["段落編號", "段落內容", "插圖設計概念", "生圖 Prompt"])

        for row in concepts:
            seg_id = int(row['seg_id'])
            b_start = int(row['block_start'])
            b_end = int(row['block_end'])
            topic_title = row['topic_title']
            visual_scene = row['visual_scene']
            mood_tag = row['mood_tag']
            mood_mod = MOOD_MODIFIERS.get(mood_tag, "")

            # 從 txt148 組合該段落的文字內容
            block_texts = []
            for b_idx in range(b_start, b_end + 1):
                block_file = os.path.join(txt_dir, f"B{book_id}_{b_idx+1:04d}.txt")
                if os.path.exists(block_file):
                    with open(block_file, 'r', encoding='utf-8') as bf:
                        block_texts.append(bf.read().strip())
                else:
                    # 嘗試備用檔名格式
                    block_file_alt = os.path.join(txt_dir, f"{book_id}_{b_idx+1:04d}.txt")
                    if os.path.exists(block_file_alt):
                        with open(block_file_alt, 'r', encoding='utf-8') as bf:
                            block_texts.append(bf.read().strip())

            segment_text = "\n".join(block_texts)
            seq_num = f"{seg_id:02d}"

            full_prompt = (
                f"{base_prompt} "
                f"The central focus of this specific image is: {visual_scene} "
                f"{mood_mod}"
            )
            numbered_prompt = f"{seq_num}. {full_prompt}"

            writer.writerow([
                f"段落_{seg_id+1:02d}",
                segment_text,
                topic_title,
                numbered_prompt
            ])

    print(f"Successfully generated {csv_path} with {len(concepts)} semantic segments.")

if __name__ == "__main__":
    generate_csv()
