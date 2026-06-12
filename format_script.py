import re
import os
import math

def get_atoms(text):
    """Tokenizes text into atoms: English words, bracketed text, or single characters."""
    pattern = r'「[^」]+」|《[^》]+》|（[^）]+）|『[^』]+』|〈[^〉]+〉|\[[^\]]+\]|"[^"]+"|\'[^\']+\'|[a-zA-Z0-9_]+|.'
    return re.findall(pattern, text)

def split_phrase_by_atoms(phrase, max_chars=24):
    """Splits a phrase into balanced chunks <= max_chars, respecting atoms."""
    atoms = get_atoms(phrase)
    atom_lengths = [len(a) for a in atoms]
    total_len = sum(atom_lengths)
    
    if total_len <= max_chars:
        return [phrase]
    
    num_chunks = math.ceil(total_len / max_chars)
    target_len = total_len / num_chunks
    
    lines = []
    current_line_atoms = []
    current_line_len = 0
    
    for atom in atoms:
        atom_len = len(atom)
        
        if atom_len > max_chars:
            if current_line_atoms:
                lines.append("".join(current_line_atoms))
                current_line_atoms = []
                current_line_len = 0
            for i in range(0, atom_len, max_chars):
                lines.append(atom[i:i+max_chars])
            continue

        if current_line_atoms:
            if current_line_len + atom_len > max_chars:
                lines.append("".join(current_line_atoms))
                current_line_atoms = [atom]
                current_line_len = atom_len
            elif len(lines) < num_chunks - 1 and current_line_len + (atom_len / 2) > target_len:
                lines.append("".join(current_line_atoms))
                current_line_atoms = [atom]
                current_line_len = atom_len
            else:
                current_line_atoms.append(atom)
                current_line_len += atom_len
        else:
            current_line_atoms.append(atom)
            current_line_len += atom_len
            
    if current_line_atoms:
        lines.append("".join(current_line_atoms))
    return lines

def process_speaker_text(text, speaker_prefix, max_chars=24, max_segment_lines=2):
    safe_prefix = speaker_prefix.replace('。', '★')
    text = safe_prefix + text
    
    major_parts = re.split(r'([。；][」”』]?)', text)
    major_sentences = []
    for i in range(0, len(major_parts)-1, 2):
        major_sentences.append(major_parts[i] + major_parts[i+1])
    if len(major_parts) % 2 != 0 and major_parts[-1]:
        major_sentences.append(major_parts[-1])
    major_sentences = [s.strip() for s in major_sentences if s.strip()]
    
    segments = []
    current_segment = []

    # max_segment_lines 由外部傳入，此處不再寫死1
    
    for ms in major_sentences:
        sub_parts = re.split(r'([，！？：][」”』]?)', ms)
        sub_phrases = []
        for i in range(0, len(sub_parts)-1, 2):
            sub_phrases.append(sub_parts[i] + sub_parts[i+1])
        if len(sub_parts) % 2 != 0 and sub_parts[-1]:
            sub_phrases.append(sub_parts[-1])
        sub_phrases = [sp.strip() for sp in sub_phrases if sp.strip()]
        
        for sp in sub_phrases:
            phrase_lines = split_phrase_by_atoms(sp, max_chars)
            if current_segment and len(current_segment) + len(phrase_lines) > max_segment_lines:
                segments.append(current_segment)
                current_segment = []
            for line in phrase_lines:
                if len(current_segment) >= max_segment_lines:
                    segments.append(current_segment)
                    current_segment = []
                current_segment.append(line)
        if current_segment:
            segments.append(current_segment)
            current_segment = []
            
    return ["<".join([line.replace('★', '。') for line in seg]) for seg in segments]

def process_script(input_path, output_path, max_chars=24, max_segment_lines=2):
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    lines = content.split('\n')
    output = []
    current_speaker_prefix = ""
    is_first_chapter = True
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        chapter_match = re.match(r'第\d+章：(.+)', line)
        if chapter_match:
            title = chapter_match.group(1)
            if not is_first_chapter:
                output.append("\n@@@@\n")
            output.append(f">>>>{title}\n")
            is_first_chapter = False
            i += 1
            continue
        if line == "男主持：":
            current_speaker_prefix = "。"
            i += 1
            continue
        elif line == "女主持：":
            current_speaker_prefix = "。。"
            i += 1
            continue
        elif line == "受訪者：":
            current_speaker_prefix = "。。。"
            i += 1
            continue
        direct_speaker_match = re.match(r'^(。。。|。。|。)(.+)$', line)
        if direct_speaker_match:
            speaker_prefix = direct_speaker_match.group(1)
            direct_lines = [direct_speaker_match.group(2)]
            i += 1
            while i < len(lines):
                next_line = lines[i].strip()
                if not next_line:
                    i += 1
                    continue
                if next_line in ["男主持：", "女主持：", "受訪者："] or re.match(r'第\d+章：', next_line):
                    break
                next_direct_match = re.match(r'^(。。。|。。|。)(.+)$', next_line)
                if next_direct_match:
                    break
                direct_lines.append(next_line)
                i += 1
            full_text = "".join(direct_lines)
            segments = process_speaker_text(full_text, speaker_prefix, max_chars=max_chars, max_segment_lines=max_segment_lines)
            if segments:
                output.append("\n\n".join(segments) + "\n\n")
            continue
        text_block = []
        while i < len(lines):
            next_line = lines[i].strip()
            if not next_line:
                i += 1
                continue
            if next_line in ["男主持：", "女主持：", "受訪者："] or re.match(r'第\d+章：', next_line):
                break
            text_block.append(next_line)
            i += 1
        full_text = "".join(text_block)
        segments = process_speaker_text(full_text, current_speaker_prefix, max_chars=max_chars, max_segment_lines=max_segment_lines)
        if segments:
            output.append("\n\n".join(segments) + "\n\n")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("".join(output).strip() + "\n")

def find_book_dir(book_id):
    for item in os.listdir('.'):
        if os.path.isdir(item) and (item.startswith(f"{book_id}_") or item.startswith(f"B{book_id}_") or item.startswith(f"1{book_id}_")):
            return item
    raise FileNotFoundError(f"Cannot find book directory starting with {book_id}_")

if __name__ == "__main__":
    BOOK_ID = "141"
    book_dir = find_book_dir(BOOK_ID)
    base_dir = os.path.join(book_dir, "raw")
    max_chars          = 30   # 每行最多幾個字元
    max_segment_lines  = 2    # 每個畫面最多幾行
    process_script(
        os.path.join(base_dir, "腳本-step2.txt"),
        os.path.join(base_dir, "腳本-step3.txt"),
        max_chars=max_chars,
        max_segment_lines=max_segment_lines
    )
    print(f"Done! max_chars={max_chars}, max_segment_lines={max_segment_lines}")
