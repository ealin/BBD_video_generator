import os
import sys
import time

# Ensure workspace site-packages is on sys.path
_curr = os.path.dirname(os.path.abspath(__file__))
while _curr and _curr != "/":
    _sp = os.path.join(_curr, "site-packages")
    if os.path.exists(_sp):
        if _sp not in sys.path:
            sys.path.insert(0, _sp)
        break
    _curr = os.path.dirname(_curr)

from playwright.sync_api import sync_playwright

SESSION_PATH = "config/adobe_session.json"
TARGET_URL = "https://new.express.adobe.com/home/tools/animate-from-audio"

def run():
    # Make sure config folder exists
    os.makedirs(os.path.dirname(SESSION_PATH), exist_ok=True)
    
    print("正在啟動瀏覽器以供手動登入...")
    with sync_playwright() as p:
        # Launch headed browser using local Chrome to bypass Google bot detection
        try:
            print("嘗試啟動您電腦中的 Google Chrome 以避開安全偵測...")
            browser = p.chromium.launch(
                headless=False,
                channel="chrome",
                args=["--disable-blink-features=AutomationControlled"]
            )
        except Exception as e:
            print(f"啟動 Chrome 失敗 ({e})，改用預設 Chromium 啟動...")
            browser = p.chromium.launch(
                headless=False,
                args=["--disable-blink-features=AutomationControlled"]
            )
        
        # Create a clean context
        context = browser.new_context(
            viewport={"width": 1280, "height": 800}
        )
        
        page = context.new_page()
        page.goto(TARGET_URL)
        
        print("\n=======================================================")
        print("【操作指引】")
        print("1. 請在瀏覽器視窗中點擊『登入』或進行註冊。")
        print("2. 成功登入後，請確認您已看見 Adobe Express 的動畫編輯介面。")
        print("3. 完成後，請回到此終端機，按下 Enter 鍵以儲存登入狀態。")
        print("=======================================================\n")
        
        input("--> 登入完成後，按 Enter 鍵繼續... ")
        
        # Save storage state (cookies, local storage, etc.)
        context.storage_state(path=SESSION_PATH)
        print(f"登入狀態已成功儲存至: {SESSION_PATH}")
        
        # Verify it is saved
        if os.path.exists(SESSION_PATH):
            print("Session 檔案確認存在，大小為:", os.path.getsize(SESSION_PATH), "bytes")
        else:
            print("警告: Session 檔案儲存失敗！")
            
        browser.close()

if __name__ == "__main__":
    run()
