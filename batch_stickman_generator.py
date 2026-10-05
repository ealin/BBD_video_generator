import os
import sys
import time
import glob
from playwright.sync_api import sync_playwright

# Configurations
SESSION_PATH = "config/adobe_session.json"
TARGET_URL = "https://new.express.adobe.com/home/tools/animate-from-audio"
BOOK_ID = "148"
BOOK_DIR_NAME = "148_20260716_永不崩盤"
INPUT_DIR = f"/Users/mac/00prj/2026PRJ/BBD_video_generator/{BOOK_DIR_NAME}/raw/voice{BOOK_ID}"
OUTPUT_DIR = f"/Users/mac/00prj/2026PRJ/BBD_video_generator/{BOOK_DIR_NAME}/raw/stickman_green"

def process_single_file(mp3_path, output_mp4_path, character_name):
    print(f"=== 開始處理音檔: {os.path.basename(mp3_path)} (使用角色: {character_name}) ===")
    
    with sync_playwright() as p:
        try:
            # Launch Chrome with session state
            browser = p.chromium.launch(
                headless=True,
                channel="chrome",
                args=["--disable-http2", "--disable-blink-features=AutomationControlled"]
            )
        except Exception as e:
            print(f"啟動 Chrome 失敗，改用預設 Chromium: {e}")
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-http2", "--disable-blink-features=AutomationControlled"]
            )
            
        context = browser.new_context(
            storage_state=SESSION_PATH,
            viewport={"width": 1280, "height": 800},
            locale="zh-TW"
        )
        
        page = context.new_page()
        
        # Navigate to Adobe Express tool
        page.goto(TARGET_URL, wait_until="domcontentloaded")
        time.sleep(12)  # Wait for editor elements to load
        
        # Check if editor modal is present
        editor = page.get_by_test_id("quick-action-modal")
        if not editor.is_visible():
            print("錯誤：找不到編輯器視窗。Session 可能過期，請重新登入。")
            browser.close()
            return False
            
        # 1. Select character
        print(f"點擊『角色』頁籤，並選擇角色 {character_name}...")
        try:
            char_tab = editor.get_by_text("角色", exact=True)
            char_tab.click()
            time.sleep(2)
        except Exception as e:
            print(f"警告：點擊角色頁籤失敗: {e}")

        char_success = page.evaluate("""(name) => {
            function selectCharacter(root, name) {
                if (!root) return false;
                let thumbnails = Array.from(root.querySelectorAll('qa-thumbnail'));
                for (let t of thumbnails) {
                    let id = t.getAttribute('data-thumbnail-id') || '';
                    let labelText = '';
                    let altText = '';
                    if (t.shadowRoot) {
                        let label = t.shadowRoot.querySelector('label');
                        if (label) labelText = label.textContent;
                        let img = t.shadowRoot.querySelector('img');
                        if (img) altText = img.getAttribute('alt') || '';
                    }
                    if (id.toLowerCase().includes(name.toLowerCase()) || 
                        labelText.toLowerCase().includes(name.toLowerCase()) || 
                        altText.toLowerCase().includes(name.toLowerCase())) {
                        let btn = t.shadowRoot.querySelector('button.qa-thumbnail-button') || t;
                        btn.click();
                        return true;
                    }
                }
                let all = root.querySelectorAll('*');
                for (let i = 0; i < all.length; i++) {
                    if (all[i].shadowRoot) {
                        let found = selectCharacter(all[i].shadowRoot, name);
                        if (found) return true;
                    }
                }
                return false;
            }
            return selectCharacter(document, name);
        }""", character_name)
        
        if not char_success:
            print(f"錯誤：選擇 {character_name} 角色失敗！")
            browser.close()
            return False
        time.sleep(2)
        
        # 2. Select green background
        try:
            bg_tab = editor.get_by_text("背景", exact=True)
            bg_tab.click()
            time.sleep(2)
            
            custom_color_btn = editor.locator("qa-thumbnail").filter(has_text="自訂顏色").locator("button.qa-thumbnail-button")
            custom_color_btn.click()
            time.sleep(2)
            
            bg_success = page.evaluate("""() => {
                function findAndClickSwatch(root, hex) {
                    if (!root) return false;
                    let triggers = Array.from(root.querySelectorAll('overlay-trigger'));
                    let el = triggers.find(t => t.textContent && t.textContent.includes(hex));
                    if (el) {
                        let swatch = el.querySelector('sp-swatch') || el;
                        swatch.click();
                        return true;
                    }
                    let all = root.querySelectorAll('*');
                    for (let i = 0; i < all.length; i++) {
                        if (all[i].shadowRoot) {
                            let found = findAndClickSwatch(all[i].shadowRoot, hex);
                            if (found) return true;
                        }
                    }
                    return false;
                }
                return findAndClickSwatch(document, '#27BB36');
            }""")
            if not bg_success:
                print("錯誤：選擇綠色背景失敗！")
                browser.close()
                return False
            time.sleep(3)
        except Exception as e:
            print(f"背景設定異常: {e}")
            browser.close()
            return False
            
        # 3. Find input and upload audio file
        input_handle = page.evaluate_handle("""() => {
            function findAudioInput(root) {
                if (!root) return null;
                let fileUploads = Array.from(root.querySelectorAll('qa-file-upload'));
                for (let fu of fileUploads) {
                    if (fu.shadowRoot) {
                        let inp = fu.shadowRoot.querySelector('input#file-input');
                        if (inp) return inp;
                    }
                }
                let all = root.querySelectorAll('*');
                for (let i = 0; i < all.length; i++) {
                    if (all[i].shadowRoot) {
                        let found = findAudioInput(all[i].shadowRoot);
                        if (found) return found;
                    }
                }
                return null;
            }
            return findAudioInput(document);
        }""")
        
        input_element = input_handle.as_element()
        if not input_element:
            print("錯誤：找不到音檔上傳 input 元素。")
            browser.close()
            return False
            
        input_element.set_input_files(mp3_path)
        print("音檔上傳完成，等待動畫處理...")
        
        # 4. Poll for download button (max 150 seconds)
        download_btn_found = False
        start_time = time.time()
        while time.time() - start_time < 150:
            buttons_info = page.evaluate("""() => {
                function findButtons(root) {
                    let res = [];
                    let all = root.querySelectorAll('*');
                    all.forEach(el => {
                        if (el.tagName === 'BUTTON' || el.tagName === 'SP-BUTTON') {
                            res.push(el.textContent.trim());
                        }
                        if (el.shadowRoot) {
                            res = res.concat(findButtons(el.shadowRoot));
                        }
                    });
                    return res;
                }
                return findButtons(document);
            }""")
            
            if any("下載" in text for text in buttons_info):
                download_btn_found = True
                break
            time.sleep(5)
            
        if not download_btn_found:
            print("錯誤：動畫處理超時，未出現下載按鈕。")
            browser.close()
            return False
            
        # 5. Capture download stream and save as output file
        print("開始下載影片...")
        try:
            with page.expect_download(timeout=60000) as download_info:
                page.evaluate("""() => {
                    function clickDownload(root) {
                        if (!root) return false;
                        let all = root.querySelectorAll('*');
                        for (let el of all) {
                            if ((el.tagName === 'BUTTON' || el.tagName === 'SP-BUTTON') && el.textContent.includes('下載')) {
                                el.click();
                                return true;
                            }
                            if (el.shadowRoot) {
                                let found = clickDownload(el.shadowRoot);
                                if (found) return true;
                            }
                        }
                        return false;
                    }
                    return clickDownload(document);
                }""")
            download = download_info.value
            download.save_as(output_mp4_path)
            print(f"成功儲存影片至: {output_mp4_path}")
            browser.close()
            return True
        except Exception as e:
            print(f"下載或儲存影片失敗: {e}")
            browser.close()
            return False

def main():
    import csv
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Load 發音人清單.csv and create a filename-to-character mapping
    csv_path = f"/Users/mac/00prj/2026PRJ/BBD_video_generator/{BOOK_DIR_NAME}/raw/發音人清單.csv"
    voice_mapping = {}
    
    if os.path.exists(csv_path):
        print(f"載入發音人清單: {csv_path}")
        with open(csv_path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                filename = row.get("檔名", "").strip()
                tts_voice = row.get("TTS語音", "").strip()
                if filename and tts_voice:
                    # zh-TW-HsiaoChenNeural is female voice -> "Soo Min", others -> "Zeno" (Author)
                    character = "Soo Min" if tts_voice == "zh-TW-HsiaoChenNeural" else "Zeno"
                    voice_mapping[filename] = character
        print(f"成功對照 {len(voice_mapping)} 個音檔之發音角色。")
    else:
        print(f"警告：找不到發音人清單 {csv_path}，將全部預設為 Zeno 角色。")
        
    # Get and sort all mp3 files
    mp3_files = sorted(glob.glob(os.path.join(INPUT_DIR, "*.mp3")))
    total_files = len(mp3_files)
    
    if total_files == 0:
        print(f"在 {INPUT_DIR} 目錄下找不到任何 MP3 檔案。")
        return
        
    print(f"找到 {total_files} 個待處理的語音檔。")
    print(f"輸出目錄: {OUTPUT_DIR}")
    print("-" * 50)
    
    success_count = 0
    skip_count = 0
    fail_count = 0
    
    for idx, mp3_path in enumerate(mp3_files, 1):
        filename = os.path.basename(mp3_path)
        basename = os.path.splitext(filename)[0]
        output_mp4 = os.path.join(OUTPUT_DIR, f"{basename}.mp4")
        
        # Get dynamic character name
        character_name = voice_mapping.get(filename, "Sticky")
        
        print(f"[{idx}/{total_files}] 處理檔案: {filename} (配角: {character_name})")
        
        # Check resume condition
        if os.path.exists(output_mp4) and os.path.getsize(output_mp4) > 0:
            print(f"--> [跳過] 影片已存在且非空: {os.path.basename(output_mp4)}")
            skip_count += 1
            print("-" * 50)
            continue
            
        # Process single file (retry once if fails)
        success = False
        for attempt in range(1, 3):
            if attempt > 1:
                print(f"--> [重試] 正在嘗試第 {attempt} 次...")
            
            success = process_single_file(mp3_path, output_mp4, character_name)
            if success:
                break
            time.sleep(5)
            
        if success:
            success_count += 1
            print("--> [成功]")
        else:
            fail_count += 1
            print("--> [失敗]")
            # If session is expired, abort early to avoid continuous fails
            if not os.path.exists(SESSION_PATH):
                print("Session 檔案遺失，終止程式。")
                break
                
        print("-" * 50)
        time.sleep(2)  # Cooldown between browser instances
        
    print("\n=== 批次處理結束 ===")
    print(f"總檔案數: {total_files}")
    print(f"成功生成: {success_count}")
    print(f"跳過已存在: {skip_count}")
    print(f"失敗個數: {fail_count}")

if __name__ == "__main__":
    main()
