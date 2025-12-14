#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test UDO Web Dashboard with Playwright
Checks for console errors, network errors, and UI elements
"""

from playwright.sync_api import sync_playwright
import json
import sys
import io

# Fix Windows encoding issue
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def test_dashboard():
    """Test the UDO Web Dashboard"""

    console_messages = []
    network_errors = []
    network_requests = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Listen for console messages
        page.on("console", lambda msg: console_messages.append({
            "type": msg.type,
            "text": msg.text,
            "location": msg.location
        }))

        # Listen for network responses
        def handle_response(response):
            network_requests.append({
                "url": response.url,
                "status": response.status,
                "ok": response.ok
            })
            if not response.ok and "/api/" in response.url:
                network_errors.append({
                    "url": response.url,
                    "status": response.status,
                    "statusText": response.status_text
                })

        page.on("response", handle_response)

        print("=" * 80)
        print("🚀 Testing UDO Web Dashboard at http://localhost:3001")
        print("=" * 80)

        # Navigate to dashboard
        try:
            page.goto('http://localhost:3001', timeout=30000)
            print("✅ Page loaded successfully")
        except Exception as e:
            print(f"❌ Failed to load page: {e}")
            browser.close()
            return False

        # Wait for network to be idle
        try:
            page.wait_for_load_state('networkidle', timeout=20000)
            print("✅ Network idle - all resources loaded")
        except Exception as e:
            print(f"⚠️  Network not idle after 20s: {e}")

        # Take screenshot
        screenshot_path = 'C:\\Users\\user\\Documents\\GitHub\\UDO-Development-Platform\\dashboard_screenshot.png'
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"📸 Screenshot saved to {screenshot_path}")

        # Wait a bit more for any async operations
        page.wait_for_timeout(2000)

        # Check for console errors
        print("\n" + "=" * 80)
        print("📋 CONSOLE MESSAGES")
        print("=" * 80)

        errors = [msg for msg in console_messages if msg['type'] == 'error']
        warnings = [msg for msg in console_messages if msg['type'] == 'warning']

        if errors:
            print(f"\n❌ Found {len(errors)} console errors:")
            for i, error in enumerate(errors[:10], 1):  # Show first 10
                print(f"  {i}. {error['text']}")
                if error.get('location'):
                    print(f"     Location: {error['location']}")
        else:
            print("✅ No console errors")

        if warnings:
            print(f"\n⚠️  Found {len(warnings)} console warnings:")
            for i, warning in enumerate(warnings[:5], 1):  # Show first 5
                print(f"  {i}. {warning['text']}")
        else:
            print("✅ No console warnings")

        # Check for network errors
        print("\n" + "=" * 80)
        print("🌐 NETWORK REQUESTS")
        print("=" * 80)

        api_requests = [req for req in network_requests if "/api/" in req['url']]

        if network_errors:
            print(f"\n❌ Found {len(network_errors)} failed API requests:")
            for i, error in enumerate(network_errors, 1):
                print(f"  {i}. {error['url']}")
                print(f"     Status: {error['status']} {error['statusText']}")
        else:
            print("✅ All API requests successful")

        if api_requests:
            print(f"\n📊 API Requests summary ({len(api_requests)} total):")
            for req in api_requests:
                status_icon = "✅" if req['ok'] else "❌"
                print(f"  {status_icon} {req['status']} - {req['url']}")

        # Check for specific UI elements
        print("\n" + "=" * 80)
        print("🎨 UI ELEMENTS CHECK")
        print("=" * 80)

        # Check for common elements
        elements_to_check = [
            ("h1", "Page title"),
            ("nav", "Navigation"),
            ("button", "Buttons"),
            ("[role='main']", "Main content area"),
        ]

        for selector, name in elements_to_check:
            try:
                count = page.locator(selector).count()
                if count > 0:
                    print(f"✅ {name}: {count} found")
                else:
                    print(f"⚠️  {name}: None found")
            except Exception as e:
                print(f"❌ Error checking {name}: {e}")

        # Get page title
        title = page.title()
        print(f"\n📄 Page Title: {title}")

        # Summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)

        total_issues = len(errors) + len(network_errors)

        if total_issues == 0:
            print("🎉 ✅ ALL TESTS PASSED - No errors found!")
            success = True
        else:
            print(f"⚠️  Found {total_issues} issues:")
            print(f"   - Console errors: {len(errors)}")
            print(f"   - Network errors: {len(network_errors)}")
            success = False

        browser.close()
        return success

if __name__ == "__main__":
    success = test_dashboard()
    sys.exit(0 if success else 1)
