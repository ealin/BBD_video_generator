import os
import sys
import time
import glob
import json
import argparse
from playwright.sync_api import sync_playwright

def parse_args():
    parser = argparse.ArgumentParser(description="Batch generate character animations from audio using Adobe Express.")
    parser.add_argument("--input-dir", required=True, help="Directory containing input MP3 files")
    parser.add_argument("--output-dir", required=True, help="Directory to save generated MP4 files")
    parser.add_argument("--csv-path", required=True, help="Path to speaker mapping CSV file")
    parser.add_argument("--char-mapping", required=True, help="JSON string mapping TTS voice/speaker to Adobe character name")
    parser.add_argument("--session-path", default="config/adobe_session.json", help="Path to Adobe session state JSON")
    parser.add_argument("--target-url", default="https://new.express.adobe.com/home/tools/animate-from-audio", help="Adobe Express tool URL")
    return parser.parse_args()

def process_single_file(mp3_path, output_mp4_path, character_name, session_path, target_url):
    print(f"=== 開始處理音檔: {os.path.basename(mp3_path)} (使用角色: {character_name}) ===")
    
    # 若為轉場/標頭靜音檔 (< 5KB)，Adobe Express 無法識別無語音檔，直接以 ffmpeg 生成純綠幕影片
    if os.path.getsize(mp3_path) < 5000:
        print(f"  -> 轉場/標頭靜音檔 ({os.path.basename(mp3_path)})，直接以 ffmpeg 生成純綠幕影片...")
        import subprocess
        try:
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", "color=c=0x27BB36:s=1280x720:r=30",
                "-i", mp3_path,
                "-c:v", "libx264", "-c:a", "aac", "-shortest",
                output_mp4_path
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"  -> 純綠幕影片已成功生成: {os.path.basename(output_mp4_path)}")
            return True
        except Exception as e:
            print(f"  -> 生成純綠幕影片失敗: {e}")
            return False
    
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
            storage_state=session_path,
            viewport={"width": 1280, "height": 800},
            locale="zh-TW"
        )
        
        page = context.new_page()
        
        # Navigate to Adobe Express tool
        page.goto(target_url, wait_until="domcontentloaded")
        
        # Check if editor modal is present
        editor = page.get_by_test_id("quick-action-modal")
        try:
            editor.wait_for(state="visible", timeout=45000)
        except Exception as e_vis:
            print(f"錯誤：找不到編輯器視窗（等待超時）。Session 可能過期，請重新登入。詳情: {e_vis}")
            browser.close()
            return False
            
        # 1. Select character
        print(f"點擊『角色』頁籤，並選擇角色 {character_name}...")
        page.evaluate("""() => {
            function queryAllShadow(root, selector) {
                let res = [];
                if (!root) return res;
                let elems = Array.from(root.querySelectorAll(selector));
                res = res.concat(elems);
                let all = Array.from(root.querySelectorAll('*'));
                for (let el of all) {
                    if (el.shadowRoot) res = res.concat(queryAllShadow(el.shadowRoot, selector));
                }
                return res;
            }
            let tabs = queryAllShadow(document, 'sp-tab');
            let charTab = tabs.find(t => {
                let txt = (t.textContent || '').trim().toLowerCase();
                let val = (t.getAttribute('value') || t.getAttribute('id') || '').toLowerCase();
                return txt.includes('角色') || txt.includes('character') || val.includes('char');
            });
            if (charTab) { charTab.click(); }
            else if (tabs.length >= 1) { tabs[0].click(); }
        }""")
        time.sleep(2)

        # The character grid is a virtualized list: a name that isn't near the top may
        # simply not be mounted in the DOM yet, so a single query can miss it even though
        # nothing is "wrong". Retry the query a few times (catches it if it mounts on its
        # own), and if that fails, actually scroll the panel (real mouse wheel events —
        # scrolling via JS does not reliably trigger the virtualizer) until the thumbnail
        # appears, then click it. Never silently fall back to the default character.
        find_and_click_char_js = """(name) => {
            function queryAllShadow(root, selector) {
                let res = [];
                if (!root) return res;
                let elems = Array.from(root.querySelectorAll(selector));
                res = res.concat(elems);
                let all = Array.from(root.querySelectorAll('*'));
                for (let el of all) {
                    if (el.shadowRoot) res = res.concat(queryAllShadow(el.shadowRoot, selector));
                }
                return res;
            }
            let thumbs = queryAllShadow(document, 'qa-thumbnail');
            let t = thumbs.find(el => (el.shadowRoot ? el.shadowRoot.textContent : el.textContent || '').trim() === name);
            if (!t) return false;
            let btn = t.shadowRoot ? (t.shadowRoot.querySelector('button') || t.shadowRoot.querySelector('.qa-thumbnail-button')) : null;
            if (btn) { btn.click(); } else { t.click(); }
            return true;
        }"""
        find_char_rect_js = """(name) => {
            function queryAllShadow(root, selector) {
                let res = [];
                if (!root) return res;
                let elems = Array.from(root.querySelectorAll(selector));
                res = res.concat(elems);
                let all = Array.from(root.querySelectorAll('*'));
                for (let el of all) {
                    if (el.shadowRoot) res = res.concat(queryAllShadow(el.shadowRoot, selector));
                }
                return res;
            }
            let thumbs = queryAllShadow(document, 'qa-thumbnail');
            let t = thumbs.find(el => (el.shadowRoot ? el.shadowRoot.textContent : el.textContent || '').trim() === name);
            if (!t) return null;
            let r = t.getBoundingClientRect();
            return {x: r.x, y: r.y, w: r.width, h: r.height};
        }"""

        char_success = False
        for _ in range(6):
            char_success = page.evaluate(find_and_click_char_js, character_name)
            if char_success:
                break
            time.sleep(0.7)

        if not char_success:
            page.mouse.move(900, 400)
            for _ in range(40):
                rect = page.evaluate(find_char_rect_js, character_name)
                if rect and rect["w"] > 0 and 0 <= rect["y"] <= 780:
                    char_success = page.evaluate(find_and_click_char_js, character_name)
                    if char_success:
                        break
                page.mouse.wheel(0, 300)
                time.sleep(0.4)

        if not char_success:
            print(f"錯誤：選擇 {character_name} 角色失敗！")
            browser.close()
            return False
        time.sleep(2)

        # 2. Select green background (#27BB36) via the "自訂顏色" (Custom Color) picker.
        # Adobe Express has no ready-made "green screen" preset thumbnail; the only
        # reliable path is: open Background tab -> Custom Color -> Custom (hex) sub-tab
        # -> type the hex value. Clicks on the *inner* shadow-root button (not the outer
        # custom element, and not raw mouse coordinates) are what reliably register with
        # this virtualized/shadow-DOM UI.
        click_bg_tab_js = """() => {
            function queryAllShadow(root, selector) {
                let res = [];
                if (!root) return res;
                let elems = Array.from(root.querySelectorAll(selector));
                res = res.concat(elems);
                let all = Array.from(root.querySelectorAll('*'));
                for (let el of all) {
                    if (el.shadowRoot) res = res.concat(queryAllShadow(el.shadowRoot, selector));
                }
                return res;
            }
            let tabs = queryAllShadow(document, 'sp-tab');
            let bgTab = tabs.find(t => (t.getAttribute('value') || '') === 'backgrounds');
            if (!bgTab) return false;
            let btn = bgTab.shadowRoot ? (bgTab.shadowRoot.querySelector('button') || bgTab.shadowRoot.querySelector('[role="tab"]')) : null;
            if (btn) { btn.click(); } else { bgTab.click(); }
            return true;
        }"""
        # The sp-tab list can take a moment to mount after the character panel loads;
        # retry a few times instead of failing on the first miss.
        bg_tab_success = False
        for _ in range(8):
            bg_tab_success = page.evaluate(click_bg_tab_js)
            if bg_tab_success:
                break
            time.sleep(0.7)
        if not bg_tab_success:
            print("錯誤：找不到「背景」頁籤！")
            browser.close()
            return False
        time.sleep(1.5)

        click_custom_color_js = """() => {
            function queryAllShadow(root, selector) {
                let res = [];
                if (!root) return res;
                let elems = Array.from(root.querySelectorAll(selector));
                res = res.concat(elems);
                let all = Array.from(root.querySelectorAll('*'));
                for (let el of all) {
                    if (el.shadowRoot) res = res.concat(queryAllShadow(el.shadowRoot, selector));
                }
                return res;
            }
            let thumbs = queryAllShadow(document, 'qa-thumbnail');
            let t = thumbs.find(el => {
                let txt = (el.shadowRoot ? el.shadowRoot.textContent : el.textContent || '').trim();
                return txt === '自訂顏色' || txt.toLowerCase() === 'custom color';
            });
            if (!t) return false;
            let btn = t.shadowRoot ? (t.shadowRoot.querySelector('button') || t.shadowRoot.querySelector('.qa-thumbnail-button')) : null;
            if (btn) { btn.click(); } else { t.click(); }
            return true;
        }"""
        custom_color_clicked = False
        for _ in range(8):
            custom_color_clicked = page.evaluate(click_custom_color_js)
            if custom_color_clicked:
                break
            time.sleep(0.7)
        if not custom_color_clicked:
            print("錯誤：找不到「自訂顏色」背景選項！")
            browser.close()
            return False
        time.sleep(1.2)

        # Switch the color-picker popup from "色票 (Swatches)" to "自訂 (Custom)" so a hex
        # input is available, then type the exact green screen color. Match by the tab's
        # `value="custom"` attribute, not its visible text label: Adobe's tab labels here
        # intermittently fail to render as text (an issue on their end, not virtualization),
        # while the `value` attribute stays stable — the same reason the outer 角色/背景/大小
        # nav tabs are matched by `value` elsewhere in this file.
        find_custom_tab_js = """() => {
            function queryAllShadow(root, selector) {
                let res = [];
                if (!root) return res;
                let elems = Array.from(root.querySelectorAll(selector));
                res = res.concat(elems);
                let all = Array.from(root.querySelectorAll('*'));
                for (let el of all) {
                    if (el.shadowRoot) res = res.concat(queryAllShadow(el.shadowRoot, selector));
                }
                return res;
            }
            let tabs = queryAllShadow(document, 'sp-tab');
            let t = tabs.find(el => (el.getAttribute('value') || '') === 'custom');
            if (!t) return null;
            let r = t.getBoundingClientRect();
            if (r.width <= 0) return null;
            return {x: r.x, y: r.y, w: r.width, h: r.height};
        }"""
        custom_tab_rect = None
        for _ in range(6):
            custom_tab_rect = page.evaluate(find_custom_tab_js)
            if custom_tab_rect:
                break
            time.sleep(0.5)
        if not custom_tab_rect:
            print("錯誤：找不到色彩選擇器的「自訂」分頁！")
            browser.close()
            return False
        page.mouse.click(custom_tab_rect["x"] + custom_tab_rect["w"] / 2, custom_tab_rect["y"] + custom_tab_rect["h"] / 2)
        time.sleep(1)

        hex_rect = page.evaluate("""() => {
            function queryAllShadow(root, selector) {
                let res = [];
                if (!root) return res;
                let elems = Array.from(root.querySelectorAll(selector));
                res = res.concat(elems);
                let all = Array.from(root.querySelectorAll('*'));
                for (let el of all) {
                    if (el.shadowRoot) res = res.concat(queryAllShadow(el.shadowRoot, selector));
                }
                return res;
            }
            let inputs = queryAllShadow(document, 'input[type=text]');
            let hx = inputs.find(el => /^#?[0-9A-Fa-f]{6}$/.test(el.value || ''));
            if (!hx) return null;
            let r = hx.getBoundingClientRect();
            return {x: r.x, y: r.y, w: r.width, h: r.height};
        }""")
        if not hex_rect:
            print("錯誤：找不到色彩 Hex 輸入欄位！")
            browser.close()
            return False
        page.mouse.click(hex_rect["x"] + hex_rect["w"] / 2, hex_rect["y"] + hex_rect["h"] / 2, click_count=3)
        time.sleep(0.3)
        page.keyboard.type("27BB36", delay=50)
        time.sleep(0.3)
        page.keyboard.press("Tab")
        time.sleep(0.8)

        hex_applied = page.evaluate("""() => {
            function queryAllShadow(root, selector) {
                let res = [];
                if (!root) return res;
                let elems = Array.from(root.querySelectorAll(selector));
                res = res.concat(elems);
                let all = Array.from(root.querySelectorAll('*'));
                for (let el of all) {
                    if (el.shadowRoot) res = res.concat(queryAllShadow(el.shadowRoot, selector));
                }
                return res;
            }
            let inputs = queryAllShadow(document, 'input[type=text]');
            return inputs.some(el => (el.value || '').toLowerCase().includes('27bb36'));
        }""")
        if not hex_applied:
            print("錯誤：綠幕顏色 Hex 未套用成功！")
            browser.close()
            return False

        # Note: deliberately not closing the color-picker popup here. Searching the whole
        # document for a generic "close"/"關閉" button is ambiguous with the editor's own
        # close button and previously closed the entire quick-action-modal instead. The
        # popup floats over the background thumbnail list, not over the audio upload
        # control, and set_input_files() below works on the input element directly
        # regardless of any overlay covering it, so leaving it open is harmless.

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
            with page.expect_download(timeout=180000) as download_info:
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
    args = parse_args()
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Load character mapping
    try:
        char_mapping = json.loads(args.char_mapping)
        print(f"載入角色對照表: {char_mapping}")
    except Exception as e:
        print(f"錯誤：無法解析 --char-mapping JSON 字串: {e}")
        return
        
    # Load CSV mapping (Filename -> Speaker/Voice ID)
    voice_mapping = {}
    if os.path.exists(args.csv_path):
        print(f"載入發音人清單: {args.csv_path}")
        with open(args.csv_path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                filename = row.get("檔名", "").strip()
                tts_voice = row.get("TTS語音", "").strip()
                if not tts_voice:
                    # Fallback to check other column names just in case
                    tts_voice = row.get("發音人", "").strip() or row.get("角色標記", "").strip()
                if filename and tts_voice:
                    # Map the file to the corresponding character based on the speaker mapping
                    character = char_mapping.get(tts_voice, "Sticky")
                    voice_mapping[filename] = character
        print(f"成功對照 {len(voice_mapping)} 個音檔之發音角色。")
    else:
        print(f"警告：找不到發音人清單 {args.csv_path}，將全部預設為 Sticky 角色。")
        
    # Get and sort all mp3 files
    mp3_files = sorted(glob.glob(os.path.join(args.input_dir, "*.mp3")))
    total_files = len(mp3_files)
    
    if total_files == 0:
        print(f"在 {args.input_dir} 目錄下找不到任何 MP3 檔案。")
        return
        
    print(f"找到 {total_files} 個待處理的語音檔。")
    print(f"輸出目錄: {args.output_dir}")
    print("-" * 50)
    
    success_count = 0
    skip_count = 0
    fail_count = 0
    
    for idx, mp3_path in enumerate(mp3_files, 1):
        filename = os.path.basename(mp3_path)
        basename = os.path.splitext(filename)[0]
        output_mp4 = os.path.join(args.output_dir, f"{basename}.mp4")
        
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
            
            success = process_single_file(
                mp3_path, 
                output_mp4, 
                character_name,
                args.session_path,
                args.target_url
            )
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
            if not os.path.exists(args.session_path):
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
