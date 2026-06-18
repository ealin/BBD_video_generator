#!/usr/bin/env python3
"""
auto_generate_images.py
========================
自動化 ChatGPT 生圖腳本 — 使用 Playwright 瀏覽器自動化。

工作流程：
1. 讀取 分段生圖腳本.csv 中的 Prompt
2. 啟動 Chromium 瀏覽器（使用您的 Chrome 登入狀態）
3. 逐一在 ChatGPT 網頁輸入 Prompt，等待生圖完成
4. 自動下載圖片並命名為 0.jpg, 1.jpg, ..., 46.jpg
5. 儲存至 bg_image/bg{book_id}/ 目錄

用法：
  python3 auto_generate_images.py              # 生成全部 47 張
  python3 auto_generate_images.py --start 10   # 從第 10 張開始（跳過 0~9）
  python3 auto_generate_images.py --start 10 --end 15  # 只生成 10~15
"""

import os
import csv
import sys
import time
import re
import argparse
import shutil
import requests
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# ============ 設定區 ============
BOOK_ID = "144"

def find_book_dir(book_id):
    for item in os.listdir('.'):
        if os.path.isdir(item) and (item.startswith(f"{book_id}_") or item.startswith(f"B{book_id}_") or item.startswith(f"1{book_id}_") or item.startswith(f"{book_id}-") or item.startswith(f"B{book_id}-") or item.startswith(f"1{book_id}-")):
            return item
    raise FileNotFoundError(f"Cannot find book directory starting with {book_id}_")

book_dir = find_book_dir(BOOK_ID)
CSV_PATH = os.path.join(book_dir, "raw", "分段生圖腳本.csv")
OUTPUT_DIR = os.path.join(book_dir, "photo", f"bg{BOOK_ID}")
CHATGPT_URL = "https://chatgpt.com"
# Chrome user data — 用以繼承登入狀態
CHROME_USER_DATA = os.path.expanduser("~/Library/Application Support/Google/Chrome")
# Playwright 會複製一份到暫存目錄，避免鎖衝突
PW_PROFILE_DIR = os.path.expanduser("~/.playwright_chatgpt_profile")

# 生圖等待的最大時間（秒）— ChatGPT 生圖通常需要 30~90 秒
MAX_WAIT_FOR_IMAGE = 180
# 每張圖之間的休息間隔（秒）— 避免被判定為濫用
COOLDOWN_BETWEEN = 10
# ================================


def read_prompts(csv_path: str) -> list[dict]:
    """讀取 CSV，回傳 list of {seg_id, concept, prompt}"""
    prompts = []
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_prompt = row["生圖 Prompt"]
            # 僅提取序號作為 seg_id，不刪除 Prompt 開頭的序號！
            match = re.match(r"^(\d+)\.\s*", raw_prompt)
            if match:
                seg_id = int(match.group(1))
            else:
                seg_id = len(prompts)
            prompts.append({
                "seg_id": seg_id,
                "concept": row.get("插圖設計概念", ""),
                "prompt": raw_prompt, # 保留完整 Prompt（包含開頭序號，使 ChatGPT 能辨識為不同圖片）
            })
    return prompts


def setup_browser(pw, engine="chatgpt"):
    """啟動瀏覽器，使用持久化 profile 以保留登入狀態。"""
    profile_dir = os.path.expanduser(f"~/.playwright_{engine}_profile")
    # 首次啟動時，建立 profile 目錄
    if not os.path.exists(profile_dir):
        print(f"ℹ️  首次啟動：建立 Playwright {engine} profile 目錄...")
        os.makedirs(profile_dir, exist_ok=True)
    
    context = pw.chromium.launch_persistent_context(
        user_data_dir=profile_dir,
        headless=False,          # 有頭模式，方便觀察與手動介入
        channel="chromium",
        viewport={"width": 1440, "height": 900},
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-first-run",
            "--no-default-browser-check",
        ],
        ignore_default_args=["--enable-automation"],
    )
    return context


def wait_for_login(page, timeout=300, engine="chatgpt"):
    """等待使用者完成登入。"""
    print(f"\n🔐 請在瀏覽器中登入 {engine.upper()}（使用 Google 帳號 ealin.chiu@gmail.com）")
    print(f"   ⏳ 等待登入完成（最多 {timeout} 秒）...\n")
    
    try:
        # 等到主頁面載入完成（出現輸入框）
        if engine == "chatgpt":
            page.wait_for_selector(
                'div[id="composer-background"], textarea[id="prompt-textarea"], div[contenteditable="true"]',
                timeout=timeout * 1000
            )
        else: # gemini
            page.wait_for_selector(
                'div[role="textbox"], div[contenteditable="true"], textarea',
                timeout=timeout * 1000
            )
        print(f"✅ 登入成功！偵測到 {engine.upper()} 聊天介面。")
        return True
    except PlaywrightTimeout:
        print("❌ 登入逾時。請重新執行腳本。")
        return False


def close_modals_if_any(page):
    """偵測並關閉 ChatGPT 和 Gemini 常見的歡迎彈窗、隱私同意書、新功能導覽或對話框，避免擋住輸入框"""
    print("🔍 檢查是否有干擾彈窗...")
    modal_selectors = [
        'button:has-text("Got it")',
        'button:has-text("知道了")',
        'button:has-text("Okay")',
        'button:has-text("OK")',
        'button:has-text("確定")',
        'button:has-text("Dismiss")',
        'button:has-text("Close")',
        'button:has-text("關閉")',
        'button:has-text("I agree")',
        'button:has-text("我同意")',
        'button:has-text("Agree")',
        'button:has-text("Skip")',
        'button:has-text("跳過")',
        'button:has-text("Next")',
        'button:has-text("下一步")',
        'button[aria-label="Close"]',
        'div[role="dialog"] button:has-text("Okay")',
        'div[role="dialog"] button:has-text("Got it")',
    ]
    for selector in modal_selectors:
        try:
            btn = page.query_selector(selector)
            if btn and btn.is_visible():
                print(f"  💡 偵測到彈窗按鈕 [{selector}]，自動點擊關閉...")
                btn.click()
                time.sleep(1)
        except Exception:
            continue


def is_image_avatar(img, src: str, cls: str, alt: str) -> bool:
    """判斷圖片是否為頭像或 UI 小圖示，而非生成的故事插圖"""
    src_l = src.lower()
    cls_l = cls.lower()
    alt_l = alt.lower()
    
    # 1. 關鍵詞與特徵路徑判定
    if "avatar" in src_l or "avatar" in cls_l or "avatar" in alt_l:
        return True
    if "profile" in src_l or "profile" in cls_l or "profile" in alt_l:
        return True
    
    # Google 帳戶頭像常見路徑
    if "googleusercontent.com/a/" in src or "googleusercontent.com/a-" in src or "/a/" in src or "/a-" in src:
        # 確保不是 drawings 或 rts 等生成圖片路徑
        if "drawings/" not in src and "rts/" not in src:
            return True
            
    # ChatGPT 與 Gemini 助理頭像 / 圖標
    if "spark" in src_l or "spark" in cls_l or "sparkle" in cls_l:
        return True
        
    if "rounded-full" in cls or "h-6" in cls or "w-6" in cls:
        return True
        
    if any(k in alt for k in ["設定檔圖像", "帳戶", "Google Account", "Profile Picture", "Gemini", "ChatGPT"]):
        return True
        
    # 2. 尺寸大小判定 (頭像與小圖標通常小於 150 像素)
    try:
        # 透過 evaluate 取得 naturalWidth/naturalHeight (最精確，不受 CSS 縮放影響)
        natural_width = img.evaluate("el => el.naturalWidth")
        natural_height = img.evaluate("el => el.naturalHeight")
        if natural_width > 0 and (natural_width < 150 or natural_height < 150):
            return True
    except Exception:
        pass
        
    try:
        bbox = img.bounding_box()
        if bbox and (bbox["width"] < 150 or bbox["height"] < 150):
            return True
    except Exception:
        pass
        
    return False


def send_prompt_and_download(page, prompt: str, seg_id: int, output_dir: str, engine: str = "chatgpt") -> bool:
    """
    在 ChatGPT 或 Gemini 中送出 prompt，等待圖片生成，然後下載。
    回傳 True 表示成功，False 表示失敗。
    """
    output_path_jpg = os.path.join(output_dir, f"{seg_id}.jpg")
    output_path_png = os.path.join(output_dir, f"{seg_id}.png")
    
    # 如果已存在則跳過
    if os.path.exists(output_path_jpg) or os.path.exists(output_path_png):
        print(f"  ⏭️  seg {seg_id:02d} 已存在，跳過。")
        return True

    # 關閉任何可能干擾的彈窗
    close_modals_if_any(page)

    # 0. 計算送出 Prompt 前，頁面上已存在的 DALL-E/Imagen 圖片數量
    initial_image_count = 0
    try:
        existing_imgs = []
        if engine == "chatgpt":
            img_selectors = [
                'article[data-message-author-role="assistant"] img',
                'div[data-message-author-role="assistant"] img',
                '[data-message-author-role="assistant"] img',
                'img[src*="oaidalleapiprodscus"]',
                'img[src*="files.oaiusercontent.com"]',
                'img[src*="backend-api/estuary"]',
                'img[src^="blob:"]',
            ]
        else: # gemini
            img_selectors = [
                'div.model-response img',
                'message-content img',
                'img[src*="googleusercontent.com"]',
                'img[src*="google"]',
            ]

        for selector in img_selectors:
            found = page.query_selector_all(selector)
            if found:
                for img in found:
                    src = img.get_attribute("src")
                    if src:
                        cls = img.get_attribute("class") or ""
                        alt = img.get_attribute("alt") or ""
                        if not is_image_avatar(img, src, cls, alt):
                            existing_imgs.append(img)
                if existing_imgs:
                    break
        initial_image_count = len(existing_imgs)
        print(f"  🔍 送出前偵測到 {initial_image_count} 張已存在的圖片。")
    except Exception as e_count:
        print(f"  ⚠️ 計算初始圖片數量時出錯 (預設為0): {e_count}")
        initial_image_count = 0

    try:
        # 1. 找到輸入框並填入 prompt
        input_box = None
        if engine == "chatgpt":
            selectors = [
                'div#prompt-textarea',
                'textarea#prompt-textarea',
                'div[contenteditable="true"]',
                '#prompt-textarea',
            ]
        else: # gemini
            selectors = [
                'div.ql-editor',
                'div[role="textbox"]',
                'div[contenteditable="true"]',
                'textarea',
                'input-area div[contenteditable="true"]',
            ]

        for selector in selectors:
            try:
                box = page.wait_for_selector(selector, timeout=5000, state="visible")
                if box and box.is_editable():
                    input_box = box
                    break
            except PlaywrightTimeout:
                continue
        
        if not input_box:
            print(f"  ❌ seg {seg_id:02d}: 找不到 {engine.upper()} 輸入框。")
            return False

        # 清空並填入 prompt
        input_box.click()
        time.sleep(0.3)
        page.keyboard.press("Meta+A")
        page.keyboard.press("Backspace")
        time.sleep(0.5)
        
        # 輸入 prompt
        input_box.fill(prompt)
        time.sleep(1)
        
        # 2. 點擊送出按鈕
        send_btn = None
        if engine == "chatgpt":
            send_selectors = [
                'button[data-testid="send-button"]',
                'button[aria-label="Send prompt"]',
                'button[aria-label="傳送提示"]',
                'button[data-testid="composer-send-button"]',
                'form button[type="submit"]',
            ]
        else: # gemini
            send_selectors = [
                'button[aria-label*="Send" i]',
                'button[aria-label*="傳送" i]',
                'button.send-button',
                'button[aria-label="Send message"]',
                'button[aria-label="傳送訊息"]',
            ]

        for selector in send_selectors:
            try:
                btn = page.query_selector(selector)
                if btn and btn.is_visible():
                    send_btn = btn
                    break
            except Exception:
                continue
        
        if send_btn:
            print(f"  👉 點擊送出按鈕...")
            send_btn.click()
        else:
            print(f"  👉 未找到送出按鈕，嘗試送出...")
            input_box.focus()
            if engine == "gemini":
                page.keyboard.press("Control+Enter")
            else:
                page.keyboard.press("Enter")
        
        print(f"  📤 seg {seg_id:02d}: Prompt 已送出，等待生圖...")
        
        # 3. 等待圖片出現
        time.sleep(8)  # 給予足夠的初始生成時間
        
        img_element = None
        start_wait = time.time()
        
        while time.time() - start_wait < MAX_WAIT_FOR_IMAGE:
            # 尋找頁面中所有的 img 標籤
            images = []
            for selector in img_selectors:
                try:
                    found = page.query_selector_all(selector)
                    if found:
                        for img in found:
                            src = img.get_attribute("src")
                            if src:
                                cls = img.get_attribute("class") or ""
                                alt = img.get_attribute("alt") or ""
                                if not is_image_avatar(img, src, cls, alt):
                                    images.append(img)
                        if images:
                            break
                except Exception:
                    continue
            
            # 關鍵判斷：當前找到的圖片數量必須大於初始數量，才代表新圖片已產生！
            if len(images) > initial_image_count:
                # 取最後一張圖（最新生成的）
                last_img = images[-1]
                src = last_img.get_attribute("src")
                if src:
                    img_element = last_img
                    break
            
            # 檢查是否有「下載」按鈕出現（表示圖片已生成完畢）
            download_btns = []
            for selector in ['a[download]', 'button[aria-label*="download" i]', 'button[aria-label*="下載" i]', 'button[aria-label*="Download" i]']:
                try:
                    found = page.query_selector_all(selector)
                    if found:
                        download_btns.extend(found)
                except Exception:
                    continue
            
            if download_btns:
                # 重新獲取最新的 img
                try:
                    found_imgs = page.query_selector_all('img')
                    images = []
                    for img in found_imgs:
                        src = img.get_attribute("src")
                        if src and any(k in src for k in ["oaidalleapiprodscus", "files.oaiusercontent.com", "blob:", "backend-api/estuary", "estuary/content", "googleusercontent.com"]):
                            cls = img.get_attribute("class") or ""
                            alt = img.get_attribute("alt") or ""
                            if not is_image_avatar(img, src, cls, alt):
                                images.append(img)
                    if len(images) > initial_image_count:
                        img_element = images[-1]
                        break
                except Exception:
                    pass
            
            elapsed = int(time.time() - start_wait)
            print(f"    ⏳ 等待中... ({elapsed}s / {MAX_WAIT_FOR_IMAGE}s)", end="\r")
            time.sleep(5)
        
        if not img_element:
            print(f"\n  ❌ seg {seg_id:02d}: 等待超時，未偵測到生成的圖片。")
            return False
        
        src = img_element.get_attribute("src") or ""
        print(f"\n  🖼️  seg {seg_id:02d}: 偵測到圖片！(src={src[:60]}...)")
        
        # 4. 下載圖片
        
        # 方式 0: 針對 blob: 網址，在網頁內直接將 Blob 讀入 Canvas 轉換成 DataURL 下載（極速、無失真高解析、避開 CSP 限制）
        if src and src.startswith("blob:"):
            try:
                print(f"  🧪 偵測到 blob: 網址，嘗試在網頁 Context 中進行 Canvas 轉換下載...")
                js_code = """
                async (url) => {
                    // 優先使用 Canvas 繪製以避免 CSP 阻擋 fetch
                    try {
                        return await new Promise((resolve, reject) => {
                            const img = new Image();
                            img.onload = () => {
                                try {
                                    const canvas = document.createElement("canvas");
                                    canvas.width = img.naturalWidth;
                                    canvas.height = img.naturalHeight;
                                    const ctx = canvas.getContext("2d");
                                    ctx.drawImage(img, 0, 0);
                                    resolve(canvas.toDataURL("image/png"));
                                } catch (err) {
                                    reject(err);
                                }
                            };
                            img.onerror = () => reject(new Error("Failed to load image on canvas"));
                            img.src = url;
                        });
                    } catch (e) {
                        // Fallback to fetch
                        const resp = await fetch(url);
                        const blob = await resp.blob();
                        return new Promise((resolve, reject) => {
                            const reader = new FileReader();
                            reader.onloadend = () => resolve(reader.result);
                            reader.onerror = reject;
                            reader.readAsDataURL(blob);
                        });
                    }
                }
                """
                data_url = page.evaluate(js_code, src)
                if data_url and data_url.startswith("data:image/"):
                    header, encoded = data_url.split(",", 1)
                    import base64
                    data = base64.b64decode(encoded)
                    
                    ext = ".png"
                    if "jpeg" in header or "jpg" in header:
                        ext = ".jpg"
                    final_path = os.path.join(output_dir, f"{seg_id}{ext}")
                    
                    with open(final_path, "wb") as f:
                        f.write(data)
                    file_size = os.path.getsize(final_path)
                    print(f"  ✅ seg {seg_id:02d}: Blob Canvas 轉換下載成功！({file_size/1024:.1f} KB) → {final_path}")
                    return True
            except Exception as e_blob:
                print(f"  ⚠️ Blob 轉換下載失敗: {e_blob}")

        # 方式 1: 嘗試 hover 顯示下載按鈕並點擊下載
        try:
            print(f"  👉 嘗試 hover 圖片並點擊下載按鈕...")
            img_element.hover()
            time.sleep(1)
            
            download_btn = None
            if engine == "chatgpt":
                btn_selectors = [
                    'button[aria-label="Download"]',
                    'button[aria-label="下載"]',
                    'button[aria-label*="download"]',
                    'button[aria-label*="下載"]',
                    'a[download]',
                ]
            else: # gemini
                btn_selectors = [
                    'button[aria-label*="Download" i]',
                    'button[aria-label*="下載" i]',
                    'button[aria-label*="download" i]',
                    'a[download]',
                ]
                
            for btn_selector in btn_selectors:
                try:
                    btn = page.query_selector(btn_selector)
                    if btn and btn.is_visible():
                        download_btn = btn
                        break
                except Exception:
                    continue
            
            if download_btn:
                print(f"  👇 找到下載按鈕，觸發瀏覽器下載...")
                with page.expect_download(timeout=15000) as download_info:
                    download_btn.click()
                download = download_info.value
                
                # 確定下載的副檔名
                suggested_filename = download.suggested_filename
                ext = os.path.splitext(suggested_filename)[1] or ".png"
                final_path = os.path.join(output_dir, f"{seg_id}{ext}")
                
                download.save_as(final_path)
                print(f"  ✅ seg {seg_id:02d}: 下載成功！→ {final_path}")
                return True
        except Exception as e_click_dl:
            print(f"  ⚠️  方式 1 (Hover點擊下載) 失敗: {e_click_dl}")
            
        # 方式 2: 點擊圖片打開預覽大圖，然後點擊預覽中的下載按鈕
        try:
            print(f"  🔍 嘗試點擊圖片以開啟預覽大圖...")
            img_element.click()
            time.sleep(2)
            
            preview_download_btn = None
            for btn_selector in [
                'button[aria-label="Download"]',
                'button[aria-label="下載"]',
                'button[aria-label*="download"]',
                'button[aria-label*="下載"]',
                'a[download]',
                'button[aria-label*="Download image" i]',
            ]:
                try:
                    btn = page.query_selector(btn_selector)
                    if btn and btn.is_visible():
                        preview_download_btn = btn
                        break
                except Exception:
                    continue
            
            if preview_download_btn:
                print(f"  👇 找到預覽模式的下載按鈕，嘗試點擊...")
                with page.expect_download(timeout=15000) as download_info:
                    preview_download_btn.click()
                download = download_info.value
                
                suggested_filename = download.suggested_filename
                ext = os.path.splitext(suggested_filename)[1] or ".png"
                final_path = os.path.join(output_dir, f"{seg_id}{ext}")
                
                download.save_as(final_path)
                print(f"  ✅ seg {seg_id:02d}: 下載成功！→ {final_path}")
                
                # 關閉預覽模式 (按 ESC 鍵)
                page.keyboard.press("Escape")
                time.sleep(1)
                return True
            else:
                # 如果沒找到按鈕，按 Escape 關閉
                page.keyboard.press("Escape")
                time.sleep(0.5)
        except Exception as e_preview:
            print(f"  ⚠️  方式 2 (預覽下載) 失敗: {e_preview}")
            try:
                page.keyboard.press("Escape")
            except Exception:
                pass

        # 方式 3: 直接使用 HTTP GET 下載
        if src and src.startswith("http") and not src.startswith("blob:"):
            print(f"  🌐 嘗試使用 HTTP 直接下載...")
            try:
                cookies = page.context.cookies()
                cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
                
                headers = {
                    "Cookie": cookie_str,
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                }
                
                resp = requests.get(src, headers=headers, timeout=60, stream=True)
                if resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "")
                    ext = ".png" if "png" in content_type else ".jpg"
                    final_path = os.path.join(output_dir, f"{seg_id}{ext}")
                    
                    with open(final_path, "wb") as f:
                        for chunk in resp.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    file_size = os.path.getsize(final_path)
                    print(f"  ✅ seg {seg_id:02d}: HTTP 下載成功！({file_size/1024:.1f} KB) → {final_path}")
                    return True
            except Exception as e_http:
                print(f"  ⚠️  方式 3 (HTTP 下載) 失敗: {e_http}")
        
        # 方式 4: 最後手段：元素截圖
        try:
            print(f"  📸 嘗試對圖片元素進行截圖儲存...")
            bbox = img_element.bounding_box()
            if bbox:
                final_path = os.path.join(output_dir, f"{seg_id}.png")
                img_element.screenshot(path=final_path)
                print(f"  ✅ seg {seg_id:02d}: 透過截圖成功儲存！→ {final_path}")
                return True
        except Exception as e_screenshot:
            print(f"  ❌ seg {seg_id:02d}: 所有下載方式皆失敗 ({e_screenshot})")
            return False
    
    except Exception as e:
        print(f"  ❌ seg {seg_id:02d}: 發生錯誤: {e}")
        return False


def start_new_chat(page):
    """開啟一個新的 ChatGPT 對話。"""
    print("🔄 開啟新對話...")
    try:
        # 1. 嘗試尋找並點擊 New chat 按鈕
        for selector in [
            'a[aria-label="New chat"]',
            'button[aria-label="New chat"]',
            'a[aria-label="新對話"]',
            'button[aria-label="新對話"]',
            'a[href="/"]',
            '[data-testid="create-new-chat-button"]',
        ]:
            try:
                btn = page.query_selector(selector)
                if btn and btn.is_visible():
                    btn.click()
                    print("  ✅ 成功點擊新對話按鈕")
                    time.sleep(3)
                    return True
            except Exception:
                continue
        
        # 2. 如果點擊按鈕失敗，使用快捷鍵 Meta+Shift+O (Mac 上的 ChatGPT 快捷鍵)
        try:
            print("  ⌨️ 嘗試使用快捷鍵開啟新對話...")
            page.keyboard.press("Meta+Shift+O")
            time.sleep(3)
            return True
        except Exception:
            pass

        # 3. Fallback: 直接導航
        print("  🌐 導航回到 ChatGPT 首頁...")
        page.goto(CHATGPT_URL, wait_until="domcontentloaded", timeout=30000)
        time.sleep(4)
        return True
        
    except Exception as e:
        print(f"  ⚠️  開啟新對話失敗: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="AI 自動生圖腳本 (支援 ChatGPT / Gemini)")
    parser.add_argument("--start", type=int, default=0, help="起始 seg_id（預設 0）")
    parser.add_argument("--end", type=int, default=-1, help="結束 seg_id（預設 -1 = 全部）")
    parser.add_argument("--cooldown", type=int, default=COOLDOWN_BETWEEN, help="每張圖間隔秒數")
    parser.add_argument("--engine", type=str, choices=["chatgpt", "gemini"], default="chatgpt", help="生圖引擎 (chatgpt 或 gemini，預設 chatgpt)")
    parser.add_argument("--csv", type=str, default=CSV_PATH, help="Prompt CSV 路徑（預設使用本書分段生圖腳本）")
    parser.add_argument("--output-dir", type=str, default=OUTPUT_DIR, help="圖片輸出目錄（預設輸出到本書 bg_image 目錄）")
    
    # 奇偶數過濾參數組
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--odd", action="store_true", help="只處理奇數 (基數) 序列號的 prompt")
    group.add_argument("--even", action="store_true", help="只處理偶數序列號的 prompt")
    
    args = parser.parse_args()
    
    # 讀取 Prompt
    csv_path = args.csv
    output_dir = args.output_dir

    if not os.path.exists(csv_path):
        print(f"❌ 找不到 CSV 檔案: {csv_path}")
        sys.exit(1)
        
    prompts = read_prompts(csv_path)
    total = len(prompts)
    print(f"📋 已讀取 {total} 個 Prompt（seg_id 00 ~ {total-1:02d}）")
    
    # 過濾範圍
    end_id = args.end if args.end >= 0 else total - 1
    target_prompts = [p for p in prompts if args.start <= p["seg_id"] <= end_id]
    
    # 奇偶數過濾
    if args.odd:
        target_prompts = [p for p in target_prompts if p["seg_id"] % 2 == 1]
        filter_desc = " (僅限奇數/基數序列號)"
    elif args.even:
        target_prompts = [p for p in target_prompts if p["seg_id"] % 2 == 0]
        filter_desc = " (僅限偶數序列號)"
    else:
        filter_desc = ""
        
    print(f"🎯 目標範圍: seg_id {args.start:02d} ~ {end_id:02d}{filter_desc}（共 {len(target_prompts)} 張）")
    print(f"⚙️ 引擎設定: {args.engine.upper()}")
    
    # 建立輸出目錄
    os.makedirs(output_dir, exist_ok=True)
    
    # 設定目標網址
    target_url = "https://gemini.google.com" if args.engine == "gemini" else CHATGPT_URL
    
    # 啟動瀏覽器
    print("\n🚀 啟動瀏覽器...")
    with sync_playwright() as pw:
        context = setup_browser(pw, args.engine)
        page = context.pages[0] if context.pages else context.new_page()
        
        # 導航到目標網站
        print(f"🌐 前往 {args.engine.upper()}...")
        page.goto(target_url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(3)
        
        # 檢查是否需要登入
        login_needed = False
        try:
            if args.engine == "chatgpt":
                login_btn = page.query_selector('button:has-text("Log in"), a:has-text("Log in"), button:has-text("登入")')
            else: # gemini
                login_btn = page.query_selector('a:has-text("Sign in"), button:has-text("Sign in"), a:has-text("登入"), button:has-text("登入")')
            if login_btn:
                login_needed = True
        except Exception:
            pass
        
        if login_needed:
            print(f"\n⚠️  偵測到尚未登入 {args.engine.upper()}。")
            print("   請在瀏覽器視窗中手動完成以下步驟：")
            if args.engine == "chatgpt":
                print("   1. 點擊 'Log in'")
                print("   2. 選擇 'Continue with Google'")
                print("   3. 選擇帳號 ealin.chiu@gmail.com")
            else: # gemini
                print("   1. 點擊 'Sign in' 或 '登入'")
                print("   2. 選擇帳號 ealin.chiu@gmail.com")
            print("   4. 完成登入後，腳本會自動繼續。\n")
            
            if not wait_for_login(page, engine=args.engine):
                context.close()
                sys.exit(1)
            
            print("⏳ 登入完成！等待 5 秒讓頁面加載穩定，避免 context 遺失...")
            time.sleep(5)
        else:
            print("✅ 已偵測到已登入狀態。")
        
        # 開始逐張生成
        success_count = 0
        fail_count = 0
        fail_list = []
        
        for i, p in enumerate(target_prompts):
            seg_id = p["seg_id"]
            concept = p["concept"]
            prompt = p["prompt"]
            
            print(f"\n{'='*60}")
            print(f"[{i+1}/{len(target_prompts)}] seg_id={seg_id:02d} | 概念: {concept}")
            print(f"{'='*60}")
            
            # 不開啟新對話，多張圖都在同一個對話中生成以保持風格一致性
            pass
            
            # 送出 prompt 並下載
            success = send_prompt_and_download(page, prompt, seg_id, output_dir, engine=args.engine)
            
            if success:
                success_count += 1
            else:
                fail_count += 1
                fail_list.append(seg_id)
            
            # 冷卻間隔
            if i < len(target_prompts) - 1:
                print(f"  💤 休息 {args.cooldown} 秒...")
                time.sleep(args.cooldown)
        
        # 摘要報告
        print(f"\n\n{'='*60}")
        print(f"📊 生成結果摘要 ({args.engine.upper()})")
        print(f"{'='*60}")
        print(f"  ✅ 成功: {success_count} 張")
        print(f"  ❌ 失敗: {fail_count} 張")
        if fail_list:
            print(f"  🔄 失敗的 seg_id: {fail_list}")
            print(f"     可重新執行: python3 auto_generate_images.py --engine {args.engine} --start {min(fail_list)} --end {max(fail_list)}")
        print(f"  📁 輸出目錄: {output_dir}")
        
        input("\n按 Enter 關閉瀏覽器...")
        context.close()


if __name__ == "__main__":
    main()
