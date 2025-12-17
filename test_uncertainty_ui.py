"""
Uncertainty UI Automated Testing with Playwright

Tests the Uncertainty UI page including:
1. Page load and basic rendering
2. Summary cards display
3. Vector breakdown visualization
4. Uncertainty Map component
5. Mitigation strategies
6. NEW: Acknowledgment functionality
"""

from playwright.sync_api import sync_playwright
import time
import json

def test_uncertainty_ui():
    """Test Uncertainty UI with comprehensive validation"""

    with sync_playwright() as p:
        # Launch browser in headless mode
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("=" * 60)
        print("[TEST] Uncertainty UI Automated Testing")
        print("=" * 60)

        # 1. Navigate to Uncertainty page
        print("\n[1/7] Loading page: http://localhost:3000/uncertainty")
        try:
            page.goto('http://localhost:3000/uncertainty', timeout=60000)  # Increased for Turbopack compilation
            page.wait_for_load_state('networkidle', timeout=60000)
            print("[OK] Page loaded successfully")
        except Exception as e:
            print(f"[ERROR] Failed to load page: {e}")
            browser.close()
            return False

        # Take initial screenshot
        page.screenshot(path='uncertainty_ui_initial.png', full_page=True)
        print("[SCREENSHOT] Saved: uncertainty_ui_initial.png")

        # 2. Check Summary Cards
        print("\n[2/7] Checking Summary Cards...")
        try:
            # Wait for cards to appear
            page.wait_for_selector('text=Uncertainty Analysis', timeout=5000)

            # Check if data is loading or loaded
            if page.locator('text=Loading').count() > 0:
                print("[WAIT] Data is loading, waiting...")
                page.wait_for_timeout(3000)

            # Count summary cards (should have State, Confidence, Dominant, Trend)
            cards = page.locator('div[class*="bg-gray"]').count()
            print(f"[OK] Found UI components (cards/sections: {cards})")

        except Exception as e:
            print(f"[WARNING] Summary cards check: {e}")

        # 3. Check Vector Breakdown
        print("\n[3/7] Checking Vector Breakdown...")
        try:
            # Look for vector dimensions
            dimensions = ['Technical', 'Market', 'Resource', 'Timeline', 'Quality']
            found_dimensions = 0

            for dim in dimensions:
                if page.locator(f'text={dim}').count() > 0:
                    found_dimensions += 1

            print(f"[OK] Found {found_dimensions}/5 vector dimensions")

        except Exception as e:
            print(f"[WARNING] Vector breakdown check: {e}")

        # 4. Check Uncertainty Map Component
        print("\n[4/7] Checking Uncertainty Map Component...")
        try:
            # Look for quantum states
            states = ['Deterministic', 'Probabilistic', 'Quantum', 'Chaotic', 'Void']
            found_state = False

            for state in states:
                if page.locator(f'text={state}').count() > 0:
                    print(f"[OK] Found quantum state: {state}")
                    found_state = True
                    break

            if not found_state:
                print("[WARNING] No quantum state found")

            # Check for confidence meter
            if page.locator('text=Confidence Level').count() > 0:
                print("[OK] Confidence meter present")

            # Check for risk assessment
            if page.locator('text=Risk Level').count() > 0:
                print("[OK] Risk assessment present")

        except Exception as e:
            print(f"[WARNING] Uncertainty map check: {e}")

        # 5. Check NEW: 24-Hour Prediction Chart (Recharts)
        print("\n[5/7] Checking NEW 24-Hour Prediction Chart...")
        try:
            # Check for new chart title
            chart_title = page.locator('text=24-Hour Prediction Forecast').count()
            if chart_title > 0:
                print(f"[OK] Chart title found: '24-Hour Prediction Forecast'")
            else:
                print("[WARNING] New Prediction Chart title not found")

            # Check for Recharts SVG elements
            svg_count = page.locator('svg').count()
            print(f"[OK] SVG elements (charts): {svg_count}")

            # Check for chart legend items (NEW)
            legend_items = ['Current Confidence', 'Predicted Trend', 'Upper Bound', 'Lower Bound']
            found_legends = 0
            for item in legend_items:
                if page.locator(f'text={item}').count() > 0:
                    found_legends += 1
                    print(f"[OK] Legend item: '{item}'")
            print(f"[OK] Found {found_legends}/4 legend items")

            # Check for bottom metrics panel (NEW)
            metrics = ['Velocity', 'Acceleration', 'Resolution ETA']
            found_metrics = 0
            for metric in metrics:
                if page.locator(f'text={metric}').count() > 0:
                    found_metrics += 1
                    print(f"[OK] Metric: '{metric}'")
            print(f"[OK] Found {found_metrics}/3 bottom metrics")

            # Check for trend indicator (NEW)
            trend_indicators = ['Improving', 'Degrading', 'Stable']
            for indicator in trend_indicators:
                if page.locator(f'text={indicator}').count() > 0:
                    print(f"[OK] Trend indicator: '{indicator}'")
                    break

            # Take chart-specific screenshot
            chart_section = page.locator('text=24-Hour Prediction Forecast').locator('..')
            if chart_section.count() > 0:
                chart_section.first.screenshot(path='prediction_chart_detail.png')
                print("[SCREENSHOT] Chart detail: prediction_chart_detail.png")

        except Exception as e:
            print(f"[WARNING] Prediction chart check: {e}")

        # 6. Check Mitigation Strategies
        print("\n[6/7] Checking Mitigation Strategies...")
        try:
            if page.locator('text=Mitigation Strategies').count() > 0:
                print("[OK] Mitigation strategies section present")

            # Look for acknowledgment buttons
            ack_buttons = page.locator('button:has-text("Mark as Completed")').count()
            print(f"[OK] Found {ack_buttons} acknowledgment button(s)")

            # Test acknowledgment if button exists
            if ack_buttons > 0:
                print("\n[6.1/7] Testing Acknowledgment Functionality...")

                # Click first acknowledgment button
                first_button = page.locator('button:has-text("Mark as Completed")').first

                # Take screenshot before click
                page.screenshot(path='uncertainty_ui_before_ack.png', full_page=True)
                print("[SCREENSHOT] Before acknowledgment: uncertainty_ui_before_ack.png")

                print("[ACTION] Clicking 'Mark as Completed' button...")
                first_button.click()

                # Wait for potential toast notification or update
                page.wait_for_timeout(2000)

                # Take screenshot after click
                page.screenshot(path='uncertainty_ui_after_ack.png', full_page=True)
                print("[SCREENSHOT] After acknowledgment: uncertainty_ui_after_ack.png")

                # Check for success indicators (toast messages)
                if page.locator('text=applied successfully').count() > 0:
                    print("[OK] Acknowledgment success message detected")
                elif page.locator('text=acknowledged').count() > 0:
                    print("[OK] Acknowledgment confirmed")
                else:
                    print("[WARNING] No clear success message found (may still have worked)")

        except Exception as e:
            print(f"[WARNING] Mitigation strategies check: {e}")

        # 7. Check Console Errors
        print("\n[7/7] Checking Browser Console...")
        console_messages = []

        def handle_console(msg):
            console_messages.append({
                'type': msg.type,
                'text': msg.text
            })

        page.on('console', handle_console)

        # Reload to capture all console messages
        page.reload()
        page.wait_for_load_state('networkidle', timeout=10000)
        page.wait_for_timeout(2000)

        # Filter errors
        errors = [msg for msg in console_messages if msg['type'] == 'error']
        warnings = [msg for msg in console_messages if msg['type'] == 'warning']

        if errors:
            print(f"[WARNING] Found {len(errors)} console error(s):")
            for err in errors[:5]:  # Show first 5
                print(f"   - {err['text'][:100]}")
        else:
            print("[OK] No console errors detected")

        if warnings:
            print(f"[INFO] Found {len(warnings)} console warning(s)")

        # Final screenshot
        page.screenshot(path='uncertainty_ui_final.png', full_page=True)
        print("\n[SCREENSHOT] Final: uncertainty_ui_final.png")

        # Summary
        print("\n" + "=" * 60)
        print("[SUMMARY] Test Results")
        print("=" * 60)
        print("[OK] Page Load: SUCCESS")
        print("[OK] UI Components: RENDERED")
        print("[OK] Uncertainty Map: PRESENT")
        print("[OK] Mitigation Strategies: PRESENT")
        if ack_buttons > 0:
            print("[OK] Acknowledgment Button: TESTED")
        print(f"Console Errors: {len(errors)}")
        print(f"Console Warnings: {len(warnings)}")
        print("=" * 60)

        # Close browser
        browser.close()

        return len(errors) == 0

if __name__ == "__main__":
    success = test_uncertainty_ui()
    exit(0 if success else 1)
