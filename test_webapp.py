#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web Application Testing Script
Tests the UDO Development Platform web application for errors and functionality
"""

import sys
import io
from playwright.sync_api import sync_playwright
import json

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def test_webapp():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Capture console messages
        console_messages = []
        page.on("console", lambda msg: console_messages.append({
            "type": msg.type,
            "text": msg.text
        }))

        # Capture network errors
        network_errors = []
        page.on("response", lambda response:
            network_errors.append({
                "url": response.url,
                "status": response.status,
                "status_text": response.status_text
            }) if response.status >= 400 else None
        )

        print("=" * 80)
        print("Testing Main Dashboard (http://localhost:3000)")
        print("=" * 80)

        try:
            # Navigate to main dashboard
            page.goto('http://localhost:3000', wait_until='networkidle', timeout=30000)

            # Take screenshot
            page.screenshot(path='dashboard_screenshot.png', full_page=True)
            print("✓ Screenshot saved: dashboard_screenshot.png")

            # Get page title
            title = page.title()
            print(f"✓ Page Title: {title}")

            # Check for error messages in the page
            error_elements = page.locator('text=/error|Error|ERROR/i').all()
            if error_elements:
                print(f"\n⚠ Found {len(error_elements)} error elements:")
                for i, elem in enumerate(error_elements[:5]):  # Show first 5
                    print(f"  {i+1}. {elem.text_content()[:100]}")

            # Get page content
            content = page.content()
            if "Internal Server Error" in content:
                print("\n❌ FOUND: Internal Server Error in page content")
                # Try to extract error details
                error_divs = page.locator('div:has-text("Internal Server Error")').all()
                if error_divs:
                    print("\nError Details:")
                    for div in error_divs[:3]:
                        print(f"  {div.text_content()[:200]}")

            # Check for specific UI elements
            print("\n" + "=" * 80)
            print("Checking UI Elements")
            print("=" * 80)

            # Check for project selector
            project_selector = page.locator('button:has-text("Select Project"), button:has-text("UDO")').count()
            print(f"✓ Project Selector: {'Found' if project_selector > 0 else 'Not Found'}")

            # Check for navigation buttons
            gi_button = page.locator('button:has-text("GI Formula")').count()
            ck_button = page.locator('button:has-text("C-K Theory")').count()
            quality_button = page.locator('button:has-text("Quality")').count()

            print(f"✓ GI Formula button: {'Found' if gi_button > 0 else 'Not Found'}")
            print(f"✓ C-K Theory button: {'Found' if ck_button > 0 else 'Not Found'}")
            print(f"✓ Quality button: {'Found' if quality_button > 0 else 'Not Found'}")

        except Exception as e:
            print(f"\n❌ Error navigating to dashboard: {str(e)}")

        # Print console messages
        if console_messages:
            print("\n" + "=" * 80)
            print("Console Messages")
            print("=" * 80)
            for msg in console_messages[:10]:  # Show first 10
                print(f"[{msg['type'].upper()}] {msg['text']}")

        # Print network errors
        if network_errors:
            print("\n" + "=" * 80)
            print("Network Errors (Status >= 400)")
            print("=" * 80)
            for err in network_errors[:10]:  # Show first 10
                print(f"{err['status']} {err['status_text']}: {err['url']}")

        # Test GI Formula page
        print("\n" + "=" * 80)
        print("Testing GI Formula Page (http://localhost:3000/gi-formula)")
        print("=" * 80)

        try:
            page.goto('http://localhost:3000/gi-formula', wait_until='networkidle', timeout=30000)
            page.screenshot(path='gi_formula_screenshot.png', full_page=True)
            print("✓ Screenshot saved: gi_formula_screenshot.png")

            # Check for key elements
            textarea = page.locator('textarea[placeholder*="problem"]').count()
            button = page.locator('button:has-text("Generate Insight")').count()

            print(f"✓ Problem input textarea: {'Found' if textarea > 0 else 'Not Found'}")
            print(f"✓ Generate button: {'Found' if button > 0 else 'Not Found'}")

        except Exception as e:
            print(f"❌ Error navigating to GI Formula: {str(e)}")

        # Test C-K Theory page
        print("\n" + "=" * 80)
        print("Testing C-K Theory Page (http://localhost:3000/ck-theory)")
        print("=" * 80)

        try:
            page.goto('http://localhost:3000/ck-theory', wait_until='networkidle', timeout=30000)
            page.screenshot(path='ck_theory_screenshot.png', full_page=True)
            print("✓ Screenshot saved: ck_theory_screenshot.png")

            # Check for key elements
            textarea = page.locator('textarea[placeholder*="challenge"]').count()
            button = page.locator('button:has-text("Generate Alternatives")').count()

            print(f"✓ Challenge input textarea: {'Found' if textarea > 0 else 'Not Found'}")
            print(f"✓ Generate button: {'Found' if button > 0 else 'Not Found'}")

        except Exception as e:
            print(f"❌ Error navigating to C-K Theory: {str(e)}")

        browser.close()
        print("\n" + "=" * 80)
        print("Testing Complete")
        print("=" * 80)

if __name__ == "__main__":
    test_webapp()
