import re

with open('129_20260508_外資這樣買半導體股/raw/腳本.txt', 'r', encoding='utf-8') as f:
    text = f.read()

pure_text = re.sub(r'[^\w\u4e00-\u9fff]+', '', text)
length = len(pure_text)
print(f"Final script character count (pure text): {length}")
