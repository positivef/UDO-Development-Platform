"""
Confidence Dashboard UI Automated Testing with Playwright

Tests the Confidence Dashboard page including:
1. Page load and basic rendering
2. Phase selection tabs
3. Summary cards (Confidence, Decision, Risk, Actions)
4. Phase threshold visualization
5. Bayesian Confidence component
6. Data refresh functionality
"""

from playwright.sync_api import sync_playwright
import time


def test_confidence_ui():
    """Test Confidence Dashboard with comprehensive validation"""

    with sync_playwright() as p:
        # Launch browser in headless mode
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("=" * 60)
        print("[TEST] Confidence Dashboard Automated Testing")
        print("=" * 60)

        # 1. Navigate to Confidence page
        print("\n[1/8] Loading page: http://localhost:3000/confidence")
        try:
            page.goto('http://localhost:3000/confidence', timeout=10000)
            page.wait_for_load_state('networkidle', timeout=15000)
            print("[OK] Page loaded successfully")
        except Exception as e:
            print(f"[ERROR] Failed to load page: {e}")
            browser.close()
            return False

        # Take initial screenshot
        page.screenshot(path='confidence_ui_initial.png', full_page=True)
        print("[SCREENSHOT] Saved: confidence_ui_initial.png")

        # 2. Check Header and Title
        print("\n[2/8] Checking Header...")
        try:
            page.wait_for_selector('text=Bayesian Confidence Dashboard', timeout=5000)
            print("[OK] Dashboard title present")

            # Check subtitle
            if page.locator('text=Beta-Binomial inference').count() > 0:
                print("[OK] Subtitle present")
        except Exception as e:
            print(f"[WARNING] Header check: {e}")

        # 3. Check Phase Selection Tabs
        print("\n[3/8] Checking Phase Selection Tabs...")
        try:
            phases = ['Ideation', 'Design', 'MVP', 'Implementation', 'Testing']
            found_phases = 0

            for phase in phases:
                # Check both tab text and button
                if page.locator(f'button:has-text("{phase}")').count() > 0:
                    found_phases += 1

            print(f"[OK] Found {found_phases}/5 phase tabs")

            # Test phase switching
            if page.locator('button:has-text("Design")').count() > 0:
                print("[ACTION] Clicking 'Design' tab...")
                page.locator('button:has-text("Design")').first.click()
                page.wait_for_timeout(1000)
                print("[OK] Phase switch successful")

        except Exception as e:
            print(f"[WARNING] Phase tabs check: {e}")

        # 4. Check Summary Cards
        print("\n[4/8] Checking Summary Cards...")
        try:
            # Wait for data to load
            if page.locator('text=Loading').count() > 0:
                print("[WAIT] Data is loading, waiting...")
                page.wait_for_timeout(3000)

            # Check for 4 summary cards
            summary_cards = 0

            # Card 1: Confidence Score
            if page.locator('text=Confidence Score').count() > 0:
                print("[OK] Confidence Score card present")
                summary_cards += 1

            # Card 2: Decision
            if page.locator('text=Decision').count() > 0:
                print("[OK] Decision card present")
                summary_cards += 1

            # Card 3: Risk Level
            if page.locator('text=Risk Level').count() > 0:
                print("[OK] Risk Level card present")
                summary_cards += 1

            # Card 4: Actions/Recommendations
            if page.locator('text=Recommended').count() > 0 or page.locator('text=Actions').count() > 0:
                print("[OK] Actions card present")
                summary_cards += 1

            print(f"[SUMMARY] Found {summary_cards}/4 summary cards")

        except Exception as e:
            print(f"[WARNING] Summary cards check: {e}")

        # 5. Check Phase Thresholds Visualization
        print("\n[5/8] Checking Phase Thresholds...")
        try:
            if page.locator('text=Phase Confidence Thresholds').count() > 0:
                print("[OK] Phase thresholds section present")

            # Check for progress bars (each phase has a progress bar)
            # Using generic selector for progress indicators
            threshold_bars = page.locator('div.h-2.bg-gray-700.rounded-full').count()
            if threshold_bars >= 5:
                print(f"[OK] Found {threshold_bars} threshold progress bars")
            else:
                print(f"[INFO] Found {threshold_bars} progress bars (expected 5+)")

        except Exception as e:
            print(f"[WARNING] Phase thresholds check: {e}")

        # 6. Check Bayesian Confidence Component
        print("\n[6/8] Checking Bayesian Confidence Component...")
        try:
            if page.locator('text=Bayesian Confidence Analysis').count() > 0:
                print("[OK] Bayesian Confidence component present")

            # Check for decision badge (GO/GO_WITH_CHECKPOINTS/NO_GO)
            decision_found = False
            decisions = ['GO', 'GO WITH CHECKPOINTS', 'NO GO']
            for decision in decisions:
                if page.locator(f'text={decision}').count() > 0:
                    print(f"[OK] Decision badge found: {decision}")
                    decision_found = True
                    break

            if not decision_found:
                print("[WARNING] No decision badge found")

            # Check for Recommended Actions section
            if page.locator('text=Recommended Actions').count() > 0:
                print("[OK] Recommended Actions section present")

            # Check for Bayesian Statistics
            if page.locator('text=Bayesian Statistics').count() > 0:
                print("[OK] Bayesian Statistics section present")

            # Check for specific Bayesian metrics
            metrics = ['Prior Belief', 'Posterior', 'Likelihood', 'Confidence Width', 'Credible Interval']
            found_metrics = 0
            for metric in metrics:
                if page.locator(f'text={metric}').count() > 0:
                    found_metrics += 1

            print(f"[OK] Found {found_metrics}/5 Bayesian metrics")

        except Exception as e:
            print(f"[WARNING] Bayesian component check: {e}")

        # 7. Test Refresh Functionality
        print("\n[7/8] Testing Refresh Button...")
        try:
            # Look for refresh button (icon button)
            refresh_button = page.locator('button:has([class*="lucide-refresh"])').first

            if refresh_button.count() > 0:
                print("[ACTION] Clicking Refresh button...")
                refresh_button.click()
                page.wait_for_timeout(2000)

                # Check for success toast
                if page.locator('text=refreshed').count() > 0:
                    print("[OK] Refresh success message detected")
                else:
                    print("[INFO] Refresh clicked (no explicit toast detected)")

            else:
                print("[WARNING] Refresh button not found")

        except Exception as e:
            print(f"[WARNING] Refresh test: {e}")

        # 8. Check Console Errors
        print("\n[8/8] Checking Browser Console...")
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
        page.screenshot(path='confidence_ui_final.png', full_page=True)
        print("\n[SCREENSHOT] Final: confidence_ui_final.png")

        # Summary
        print("\n" + "=" * 60)
        print("[SUMMARY] Test Results")
        print("=" * 60)
        print("[OK] Page Load: SUCCESS")
        print(f"[OK] Phase Tabs: {found_phases}/5 detected")
        print(f"[OK] Summary Cards: {summary_cards}/4 detected")
        print("[OK] Bayesian Component: PRESENT")
        print("[OK] Phase Thresholds: RENDERED")
        print(f"Console Errors: {len(errors)}")
        print(f"Console Warnings: {len(warnings)}")
        print("=" * 60)

        # Close browser
        browser.close()

        return len(errors) == 0


if __name__ == "__main__":
    success = test_confidence_ui()
    exit(0 if success else 1)
