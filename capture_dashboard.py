#!/usr/bin/env python3
"""
Capture screenshot of UDO Dashboard
"""
from playwright.sync_api import sync_playwright
import sys

def capture_dashboard():
    """Capture dashboard screenshot"""
    with sync_playwright() as p:
        try:
            # Launch browser (headless)
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={'width': 1920, 'height': 1080})

            # Capture console logs
            console_logs = []
            page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))

            print("Navigating to http://localhost:3000...")
            page.goto('http://localhost:3000', timeout=30000, wait_until='domcontentloaded')

            print("Waiting for page to render...")
            page.wait_for_timeout(3000)

            print("Taking screenshot...")
            screenshot_path = 'dashboard_screenshot.png'
            page.screenshot(path=screenshot_path, full_page=True)

            print(f"Screenshot saved to: {screenshot_path}")

            # Get page title
            title = page.title()
            print(f"Page title: {title}")

            # Print console logs
            if console_logs:
                print("\n=== Console Logs ===")
                for log in console_logs[:20]:  # First 20 logs
                    print(log)

            browser.close()
            return True

        except Exception as e:
            print(f"Error: {e}")
            if 'browser' in locals():
                browser.close()
            return False

if __name__ == "__main__":
    success = capture_dashboard()
    sys.exit(0 if success else 1)
