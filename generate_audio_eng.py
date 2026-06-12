import os
import re
import asyncio
import edge_tts

# Directories
TXT_DIR = "/Users/mac/00prj/2026PRJ/BBD_video_generator/134_20260527_你的生命是一場喜樂的量子遊戲/raw/txt134_E"
VOICE_DIR = "/Users/mac/00prj/2026PRJ/BBD_video_generator/134_20260527_你的生命是一場喜樂的量子遊戲/raw/voice134_E"
os.makedirs(VOICE_DIR, exist_ok=True)

# English Voice Settings
VOICE_MALE_HOST = "en-US-AndrewNeural"   # Male Host (。): en-US-AndrewNeural, rate: +0%
VOICE_FEMALE_HOST = "en-US-AriaNeural"   # Female Host (。。): en-US-AriaNeural, rate: +0%
VOICE_GUEST = "en-GB-RyanNeural"         # Male Expert (。。。): en-GB-RyanNeural, rate: +0%

def clean_text_for_tts(text):
    """Filters out all control characters to generate a clean TTS string."""
    # Remove >, @, < characters
    text = text.replace(">", "").replace("@", "").replace("<", "")
    # Remove prefix dot markers
    text = re.sub(r'^。+', '', text)
    # Replace newlines with spaces
    text = text.replace('\n', ' ')
    return text.strip()

async def generate_english_audios():
    current_voice = VOICE_MALE_HOST
    current_rate = "+0%"
    
    total_files = 246
    generated_count = 0
    skipped_count = 0
    
    print("Starting English voice generation...")
    
    for i in range(1, total_files + 1):
        filename = f"B134_{i:04d}.txt"
        filepath = os.path.join(TXT_DIR, filename)
        
        if not os.path.exists(filepath):
            print(f"Warning: File {filename} not found in {TXT_DIR}!")
            continue
            
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 1. Update the state of current speaker first (critical for correct state persistence)
        if content.startswith("。。。"):
            current_voice = VOICE_GUEST
            current_rate = "+0%"
        elif content.startswith("。。"):
            current_voice = VOICE_FEMALE_HOST
            current_rate = "+0%"
        elif content.startswith("。"):
            current_voice = VOICE_MALE_HOST
            current_rate = "+0%"
            
        # 2. Check if output file already exists and is valid (cache check)
        mp3_filename = f"B134_{i:04d}.mp3"
        mp3_path = os.path.join(VOICE_DIR, mp3_filename)
        
        if os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 0:
            skipped_count += 1
            continue
            
        # 3. Clean up the text for TTS
        tts_text = clean_text_for_tts(content)
        final_tts_text = tts_text if tts_text else " "
        
        # 4. Generate audio
        communicate = edge_tts.Communicate(
            text=final_tts_text,
            voice=current_voice,
            rate=current_rate
        )
        
        try:
            await communicate.save(mp3_path)
            generated_count += 1
            print(f"[{i:04d}] Generated {mp3_filename} with {current_voice} (rate: {current_rate})")
        except Exception as e:
            print(f"Error generating {mp3_filename}: {e}")
            
    print(f"\nVoice generation finished!")
    print(f"Total: {total_files} files.")
    print(f"Generated: {generated_count} files.")
    print(f"Skipped (already exists): {skipped_count} files.")

if __name__ == "__main__":
    asyncio.run(generate_english_audios())
