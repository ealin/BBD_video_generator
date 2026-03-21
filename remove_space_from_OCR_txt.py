

'''

A. 使用MacOS內建的PDF OCR:

1. Finder雙擊PDF檔，“檔案”-->"輸出”，勾選"嵌入的文字"，另存檔名(xxx.pdf)
2. pdftotext temp.pdf temp.txt
3. 執行此程式
4. 手動眼看處理


B. 使用ocrmypdf套件
ocrmypdf -l chi_tra+eng book.pdf temp.pdf
ocrmypdf -l chi_sim+chi_sim_vert temp.pdf

（新機器）準備工作
==> OCR的語言列表
tesseract --list-langs

==> 安裝 OCR相關套件
brew install ocrmypdf poppler pandoc
brew install tesseract-lang

'''

'''
使用範例：

python3 clean_cn_space.py book.txt clean.txt

'''


import re
import sys

inp = sys.argv[1]
out = sys.argv[2]

with open(inp, "r", encoding="utf8") as f:
    text = f.read()


# =========================
# 1 清理頁碼與頁眉
# =========================

text = re.sub(r'—*\s*\d+\s*—*', '', text)
text = re.sub(r'\n\d+\n', '\n', text)


# =========================
# 2 中文空格清理
# =========================

text = re.sub(
    r'(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])',
    '',
    text
)


# =========================
# 3 括號修復
# =========================

text = re.sub(r'（\s*\n\s*', '（', text)
text = re.sub(r'\s*\n\s*）', '）', text)


# =========================
# 4 直排碎行重建
# =========================

def merge_vertical(lines):

    merged = []
    buffer = ""

    for line in lines:

        line = line.strip()

        if not line:
            if buffer:
                merged.append(buffer)
                buffer = ""
            merged.append("")
            continue

        if len(line) <= 2 and re.search(r'[\u4e00-\u9fff]', line):

            buffer += line

        else:

            if buffer:
                line = buffer + line
                buffer = ""

            merged.append(line)

    if buffer:
        merged.append(buffer)

    return merged


lines = text.split("\n")
lines = merge_vertical(lines)


# =========================
# 5 章節標題修復
# =========================

def fix_titles(lines):

    out = []
    buffer = ""

    for line in lines:

        if re.match(r'[第章節卷部篇一二三四五六七八九十百千]+$', line):

            buffer += line

        else:

            if buffer:

                line = buffer + " " + line
                buffer = ""

            out.append(line)

    return out


lines = fix_titles(lines)


text = "\n".join(lines)


# =========================
# 6 修復錯誤換行
# =========================

text = re.sub(
    r'(?<![。！？；])\n(?=[\u4e00-\u9fff])',
    '',
    text
)


# =========================
# 7 合併短行
# =========================

text = re.sub(
    r'([\u4e00-\u9fff]{1,10})\n([\u4e00-\u9fff])',
    r'\1\2',
    text
)


# =========================
# 8 句子段落化
# =========================

text = re.sub(
    r'([。！？])',
    r'\1\n\n',
    text
)


# =========================
# 9 清理多餘空行
# =========================

text = re.sub(
    r'\n{3,}',
    '\n\n',
    text
)


# =========================
# 10 清理孤立字行
# =========================

text = re.sub(
    r'\n([\u4e00-\u9fff])\n',
    r'\1',
    text
)


# =========================
# 11 清理多餘空格
# =========================

text = re.sub(r'[ \t]+', ' ', text)


# =========================
# 輸出
# =========================

with open(out, "w", encoding="utf8") as f:
    f.write(text)

print("Cleaned OCR text saved to:", out)
