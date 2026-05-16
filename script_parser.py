import os
import asyncio
import edge_tts

def create_dummy_mp3(output_path):
    """
    產生一個空的 (或極小的) mp3 檔，用來騙過主程式的 os.path.exists 檢查
    如果是 >>>> 或 @@@@，BBD_video_generator 內不會去播放它，只需檔案存在即可
    """
    with open(output_path, 'wb') as f:
        f.write(b'\x00')

async def _generate_edge_tts(text, output_mp3_path, role_prefix):
    """
    非同步呼叫 edge-tts 產生語音
    """
    # 根據前綴設定語音角色
    # 。 -> 主持人A (預設男生)
    # 。。 -> 主持人B (預設女生)
    # 。。。 -> 受訪者 (預設長者或作者)
    if role_prefix == '。。。':
        voice_name = "zh-CN-YunjianNeural"
    elif role_prefix == '。。':
        voice_name = "zh-CN-XiaoxiaoNeural"
    elif role_prefix == '。':
        voice_name = "zh-CN-YunxiNeural"
    else:
        voice_name = "zh-CN-YunxiNeural"

    # 移除前綴文字，因為我們不希望 TTS 唸出「。 。 。」
    clean_text = text.replace('。。。', '').replace('。。', '').replace('。', '').strip()
    
    # 處理特殊符號，例如 < 是換行用，不用唸
    clean_text = clean_text.replace('<', ',')
    
    if not clean_text:
        create_dummy_mp3(output_mp3_path)
        return

    try:
        communicate = edge_tts.Communicate(clean_text, voice_name)
        await communicate.save(output_mp3_path)
    except Exception as e:
        print(f"語音合成失敗 [{clean_text}]: {e}")
        create_dummy_mp3(output_mp3_path)

def generate_edge_tts(text, output_mp3_path, role_prefix):
    """
    同步的 wrapper，方便在迴圈中呼叫
    """
    asyncio.run(_generate_edge_tts(text, output_mp3_path, role_prefix))

def parse_and_generate_audio(script_path, output_base_dir, book_id="128", num_clips=4):
    """
    讀取腳本，切分成 N 個段落，並逐行產生 txt 與 mp3
    """
    if not os.path.exists(script_path):
        print(f"腳本 {script_path} 不存在")
        return False

    with open(script_path, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]

    # 盡量在 @@@@ 處切割段落
    split_points = []
    for i, line in enumerate(lines):
        if line.startswith('@@@@'):
            split_points.append(i)

    # 如果切分點不夠，就平均切分
    chunk_size = len(lines) // num_clips
    
    chunks = []
    start_idx = 0
    for i in range(num_clips):
        if i == num_clips - 1:
            chunks.append(lines[start_idx:])
        else:
            # 尋找靠近 chunk_size 且是 @@@@ 的位置
            target_idx = start_idx + chunk_size
            best_split = target_idx
            for sp in split_points:
                if sp > start_idx and sp <= target_idx + 10: # 容許一些誤差
                    best_split = sp + 1
            
            # 如果還是找不到合適的 @@@@，就硬切
            if best_split == target_idx:
                best_split = target_idx
                
            chunks.append(lines[start_idx:best_split])
            start_idx = best_split

    print(f"腳本切分為 {len(chunks)} 段")

    for clip_idx, chunk_lines in enumerate(chunks, 1):
        txt_dir = os.path.join(output_base_dir, f"txt{book_id}-{clip_idx}")
        voice_dir = os.path.join(output_base_dir, f"voice{book_id}-{clip_idx}")
        
        os.makedirs(txt_dir, exist_ok=True)
        os.makedirs(voice_dir, exist_ok=True)
        
        for line_idx, line in enumerate(chunk_lines, 1):
            base_name = f"B{book_id}-{clip_idx}-{line_idx:04d}"
            txt_file = os.path.join(txt_dir, f"{base_name}.txt")
            mp3_file = os.path.join(voice_dir, f"{base_name}.mp3")
            
            # 寫入 txt
            with open(txt_file, 'w', encoding='utf-8') as f:
                f.write(line)
                
            # 判斷是否需要呼叫 TTS
            if line.startswith('>>>>') or line.startswith('@@@@') or line == '_bg':
                create_dummy_mp3(mp3_file)
            else:
                # 偵測角色前綴
                prefix = ''
                if line.startswith('。。。'): prefix = '。。。'
                elif line.startswith('。。'): prefix = '。。'
                elif line.startswith('。'): prefix = '。'
                
                print(f"[{base_name}] 正在生成音訊...")
                generate_edge_tts(line, mp3_file, prefix)
                
        print(f"完成第 {clip_idx} 段，產生了 {len(chunk_lines)} 句音訊與腳本檔")

    return True

if __name__ == "__main__":
    script = "128_20260322_量子与生活/raw/book_abstract.txt"
    out_dir = "128_20260322_量子与生活/auto_output" # 測試時輸出到另一個目錄避免覆蓋原始檔案
    parse_and_generate_audio(script, out_dir, book_id="128", num_clips=4)
