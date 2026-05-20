#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
formatter.py
-----------------
依規則為段落插入「行內換行記號 <」與必要的分段（實際 \\n），並輸出到新檔（預設 temp.txt）。

新增修正要點：
- 「段落總字數 > 門檻」後，**在下一個句讀標點**（全/半形：，、：、。 與 , : .）
  且其後仍有內容時，直接以 '\\n' 另起新段（不再只限定於 '。' 或 '.'）。
- 段尾是 '。' 不加 '<' 的規則維持不變。
- 段落開頭是 '>>>>' 或 '!!!!' → 段落完全不處理、原樣輸出。

使用方式：
    python formatter.py input.txt
    python formatter.py input.txt --output out.txt
    python formatter.py --para-limit 40
    python formatter.py --test
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Iterable

# --- 常數與工具 --------------------------------------------------------------

EN_TOKEN = re.compile(r"[A-Za-z]+")
PUNC_BREAK = {
    "，", "：",  "！", "？","。",  # 全形
    ",", ":", ".",          # ASCII
}
SPACE_CHARS = {" ", "\t", "\u3000"}  # 半形空白、Tab、全形空白

MAX_UNITS_PER_LINE = 22
MAX_LINES_PER_PARAGRAPH = 6
PARA_CHAR_LIMIT_DEFAULT = 60  # 可由 CLI 調整


def _is_space(ch: str) -> bool:
    return ch in SPACE_CHARS


def _english_token_at(text: str, i: int) -> tuple[str, int] | None:
    m = EN_TOKEN.match(text, i)
    if not m:
        return None
    tok = m.group(0)
    return tok, len(tok)


def _only_spaces_to_end(text: str, i: int) -> bool:
    """text[i:] 是否只剩空白（半形、全形、Tab）。"""
    n = len(text)
    while i < n:
        if not _is_space(text[i]):
            return False
        i += 1
    return True


# --- 核心處理：單一段落 --------------------------------------------------------

def format_paragraph(text: str, para_char_limit: int = PARA_CHAR_LIMIT_DEFAULT) -> str:
    """
    處理單一段落字串，依規則插入行內換行記號 '<' 與必要的段落切分（實際 '\\n'）。

    規則摘要：
    - 一行上限 20 單位；英文 token [A-Za-z]+ 固定 4 單位且不可切；數字/其他字元各 1 單位。
    - 句讀即換行：遇到 ，、：、。 或 , : . 立即插入 '<'（但段尾的 '。' 不加 '<'）。
    - 段落最多 6 行；超過即以 '\\n' 新段。
    - 段落總字數（真實字元數，不用 4 單位制）**超過 para_char_limit** 後，
      於**下一個句讀標點**（PUNC_BREAK）且該標點後仍有內容時，改以 '\\n' 新段。
    - 換行或新段後避免行首空白。
    - 段落若以 '>>>>' 或 '!!!!' 開頭 → 完全不處理，原樣返回。
    """
    if text == "":
        return ""
    if text.startswith(">>>>") or text.startswith("!!!!"):
        return text

    out: list[str] = []
    units = 0
    lines_in_para = 1
    i = 0
    n = len(text)
    skip_leading_spaces = False

    # 「真實字元數」的段內計數與觸發旗標
    para_chars = 0
    split_at_next_break = False

    def _break_line(paragraph_split: bool = False):
        nonlocal units, lines_in_para, skip_leading_spaces, para_chars, split_at_next_break
        if paragraph_split:
            out.append("\n")
            lines_in_para = 1
            para_chars = 0
            split_at_next_break = False
        else:
            out.append("<")
            lines_in_para += 1
        units = 0
        skip_leading_spaces = True

    while i < n:
        if skip_leading_spaces:
            while i < n and _is_space(text[i]):
                i += 1
            skip_leading_spaces = False
            if i >= n:
                break

        eng = _english_token_at(text, i)
        if eng:
            tok, L = eng
            tok_units = 4
            if units + tok_units > MAX_UNITS_PER_LINE:
                if lines_in_para >= MAX_LINES_PER_PARAGRAPH:
                    _break_line(paragraph_split=True)
                else:
                    _break_line(paragraph_split=False)
            out.append(tok)
            units += tok_units
            para_chars += L  # 真實字數
            if para_chars > para_char_limit:
                split_at_next_break = True
            i += L
            continue

        ch = text[i]
        ch_units = 1

        # 若加入會超標，先換行/分段
        if units + ch_units > MAX_UNITS_PER_LINE:
            if lines_in_para >= MAX_LINES_PER_PARAGRAPH:
                _break_line(paragraph_split=True)
            else:
                _break_line(paragraph_split=False)
            if skip_leading_spaces and _is_space(ch):
                i += 1
                skip_leading_spaces = False
                continue
            skip_leading_spaces = False

        out.append(ch)
        units += ch_units
        para_chars += 1
        if para_chars > para_char_limit:
            split_at_next_break = True
        i += 1

        # 句讀處理
        if ch in PUNC_BREAK:
            # 若已觸發 >limit，且該標點後仍有內容 → 直接**段落切分**
            if split_at_next_break and not _only_spaces_to_end(text, i):
                _break_line(paragraph_split=True)
                continue

            # 段尾是 '。' → 不加 '<'
            if ch == "。" and (i >= n or _only_spaces_to_end(text, i)):
                continue

            # 一般情況：插入行內換行 '<'（或因 6 行上限改分段）
            if lines_in_para >= MAX_LINES_PER_PARAGRAPH:
                _break_line(paragraph_split=True)
            else:
                _break_line(paragraph_split=False)

    return "".join(out)


# --- 檔案層處理 ---------------------------------------------------------------

def process_file(in_path: str, out_path: str = "temp.txt", para_char_limit: int = PARA_CHAR_LIMIT_DEFAULT) -> None:
    src = Path(in_path)
    dst = Path(out_path)

    lines_out: list[str] = []
    with src.open("r", encoding="utf-8-sig", newline="") as f:
        for raw in f.readlines():
            line = raw.rstrip("\r\n")
            if line == "":
                lines_out.append("")
            else:
                lines_out.append(format_paragraph(line, para_char_limit=para_char_limit))

    with dst.open("w", encoding="utf-8", newline="\n") as wf:
        wf.write("\n".join(lines_out))


# --- 測試 ----------------------------------------------------------------------

def _repeat(ch: str, n: int) -> str:
    return ch * n


def run_tests() -> None:
    # A. 純中文長句超過 20 單位強制斷行
    from copy import deepcopy
    sA = _repeat("甲", 25)
    rA = format_paragraph(sA)
    assert rA == ("甲" * 20 + "<" + "甲" * 5), f"A failed: {rA!r}"

    # B. 全形標點即換行（中間位置）
    sB = "這是測試，下一段：再來。結束"
    rB = format_paragraph(sB)
    assert "，<" in rB and "：<" in rB and "。<結束" in rB, f"B failed: {rB!r}"

    # C. ASCII 標點即換行
    sC = "Hello, world: ok."
    rC = format_paragraph(sC)
    assert "Hello,<" in rC and "world:<" in rC and "ok.<" in rC, f"C failed: {rC!r}"

    # D. 多個英文字（各 4 單位）且不可切割
    sD = "Alpha Beta Gamma Delta Epsilon Zeta"
    rD = format_paragraph(sD)
    for w in ["Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta"]:
        assert w in rD, f"D failed: {w}"
    assert "<" in rD, "D failed: no break inserted"

    # E. 混合詞 AI2、PlanB
    sE = "AI2 與 PlanB 測試"
    rE = format_paragraph(sE)
    assert "AI2" in rE and "PlanB" in rE, f"E failed: {rE!r}"

    # F. 單段超過 6 行自動分段
    sF = "字。" * 7 + "尾"
    rF = format_paragraph(sF)
    assert "\n" in rF, f"F failed: {rF!r}"
    assert rF.count("。<") + rF.count("。\n") >= 6, f"F failed: {rF!r}"

    # G. 特殊開頭直接跳過處理
    sG1 = ">>>>RAW, 不插入任何<或\\n。"
    sG2 = "!!!!KEEP RAW."
    assert format_paragraph(sG1) == sG1 and format_paragraph(sG2) == sG2, "G failed"

    # H. 段落結尾是 '。' 不加 '<'
    sH = "這是結尾句。"
    rH = format_paragraph(sH)
    assert rH.endswith("。") and not rH.endswith("。<"), f"H failed: {rH!r}"

    # I. >limit 後在「下一個句讀」分段（逗號也可）
    sI = "前句，" + ("甲" * 50) + "，這裡應該分段，然後繼續。尾"
    rI = format_paragraph(sI, para_char_limit=40)
    assert "\n這裡應該分段" in rI, f"I failed: {rI!r}"

    # J. 你的案例：>limit=40，遇第一個 '，' 就應成兩段
    sJ = "當一段親密關係中有情緒勒索的要素存在，並不代表這段關係已經被判定為失敗，而是表示我們需要更誠實地面對，改正這種造成自身痛苦的行為模式，讓所有的親密關係都能回歸到更穩固的基礎上。"
    rJ = format_paragraph(sJ, para_char_limit=40)
    assert "\n" in rJ, f"J failed (no paragraph split): {rJ!r}"
    # 確認不是把最後的 '。' 當作唯一切點（應該在前面的某個逗號切出 \n）
    assert rJ.find("\n") < rJ.rfind("。"), f"J failed (split only at final '。'): {rJ!r}"

    print("All tests passed ✔")


# --- CLI ----------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Read a UTF-8 text file (each line = a paragraph), insert '<' and paragraph splits per rules, and write to output."
    )
    p.add_argument("input", nargs="?", help="Path to input text file (UTF-8 / UTF-8-SIG).")
    p.add_argument("--output", "-o", default="temp.txt", help="Output file path (default: temp.txt).")
    p.add_argument("--para-limit", type=int, default=PARA_CHAR_LIMIT_DEFAULT,
                   help=f"Paragraph character limit to trigger next-break split (default: {PARA_CHAR_LIMIT_DEFAULT}).")
    p.add_argument("--test", action="store_true", help="Run built-in tests and exit.")
    return p


def main(argv: Iterable[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.test:
        run_tests()
        return

    if not args.input:
        parser.error("missing input file path. Use --test to run tests.")

    process_file(args.input, args.output, para_char_limit=args.para_limit)


if __name__ == "__main__":
    main()
