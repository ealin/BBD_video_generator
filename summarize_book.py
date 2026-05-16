import re

with open('129_20260508_外資這樣買半導體股/raw/book.txt', 'r', encoding='utf-8') as f:
    text = f.read()

# Try to find chapter titles
# Usually they might be "第X章", "特點", "Part" etc.
lines = text.split('\n')
chapters = []
for line in lines:
    line = line.strip()
    if len(line) > 0 and len(line) < 30:
        if re.match(r'^(第[一二三四五六七八九十]+章|特點\s*\d+|[0-9]+\.|Part\s*\d+)', line):
            chapters.append(line)

if not chapters:
    # If no standard chapters, just print some headings based on empty lines or indentation
    pass

print("Potential Chapters found:")
for c in chapters[:30]:
    print(c)
