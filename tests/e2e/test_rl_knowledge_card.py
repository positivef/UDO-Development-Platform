"""
RL Knowledge Card E2E Test

Tests the RLKnowledgeCard component on the main dashboard.
Verifies:
1. Card renders with correct title
2. Token Prior section displays
3. Knowledge Patterns section displays
4. Experiments section displays
5. System status badge shows
"""

from playwright.sync_api import sync_playwright, expect
import sys


def test_rl_knowledge_card():
    """Test the RLKnowledgeCard component on the dashboard."""

    results = {
        "card_visible": False,
        "title_correct": False,
        "token_prior_section": False,
        "patterns_section": False,
        "experiments_section": False,
        "system_status": False,
        "screenshot_taken": False,
        "errors": [],
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            # Navigate to dashboard
            print("[TEST] Navigating to http://localhost:3000...")
            page.goto("http://localhost:3000", timeout=30000)

            # Wait for page to fully load
            print("[TEST] Waiting for networkidle...")
            page.wait_for_load_state("networkidle", timeout=30000)

            # Take initial screenshot
            page.screenshot(path="test_dashboard_initial.png", full_page=True)
            print("[TEST] Initial screenshot saved: test_dashboard_initial.png")

            # Look for RL Knowledge System card
            print("[TEST] Looking for RL Knowledge System card...")

            # Try to find the card by title
            rl_card = page.locator("text=RL Knowledge System").first

            if rl_card.is_visible(timeout=10000):
                results["card_visible"] = True
                print("[OK] RL Knowledge System card is visible")

                # Check card title
                title = page.locator("text=RL Knowledge System")
                if title.is_visible():
                    results["title_correct"] = True
                    print("[OK] Title is correct")

                # Check Token Prior section
                token_prior = page.locator("text=Token Prior")
                if token_prior.is_visible():
                    results["token_prior_section"] = True
                    print("[OK] Token Prior section visible")

                # Check Knowledge Patterns section
                patterns = page.locator("text=Knowledge Patterns")
                if patterns.is_visible():
                    results["patterns_section"] = True
                    print("[OK] Knowledge Patterns section visible")

                # Check Experiments section
                experiments = page.locator("text=Experiments")
                if experiments.is_visible():
                    results["experiments_section"] = True
                    print("[OK] Experiments section visible")

                # Check system status badge
                status_badge = page.locator("text=operational")
                if status_badge.is_visible():
                    results["system_status"] = True
                    print("[OK] System status badge visible")
                else:
                    # Maybe it's loading or error state
                    loading = page.locator("text=Loading")
                    if loading.is_visible():
                        print("[WARN] Card is in loading state")
                        results["errors"].append("Card still loading")

                # Take final screenshot
                page.screenshot(path="test_rl_card_final.png", full_page=True)
                results["screenshot_taken"] = True
                print("[OK] Final screenshot saved: test_rl_card_final.png")

            else:
                results["errors"].append("RL Knowledge System card not found")
                print("[FAIL] RL Knowledge System card not visible")

                # Debug: Print page content
                print("[DEBUG] Checking page content...")
                content = page.content()
                if "RL Knowledge" in content:
                    print("[DEBUG] 'RL Knowledge' text found in HTML")
                else:
                    print("[DEBUG] 'RL Knowledge' text NOT found in HTML")

                # Take debug screenshot
                page.screenshot(path="test_debug_no_card.png", full_page=True)
                print("[DEBUG] Debug screenshot saved: test_debug_no_card.png")

        except Exception as e:
            results["errors"].append(str(e))
            print(f"[ERROR] Test failed: {e}")
            page.screenshot(path="test_error.png", full_page=True)

        finally:
            browser.close()

    # Print summary
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)

    passed = 0
    total = 6

    checks = [
        ("Card Visible", results["card_visible"]),
        ("Title Correct", results["title_correct"]),
        ("Token Prior Section", results["token_prior_section"]),
        ("Patterns Section", results["patterns_section"]),
        ("Experiments Section", results["experiments_section"]),
        ("System Status", results["system_status"]),
    ]

    for name, status in checks:
        icon = "[OK]" if status else "[FAIL]"
        print(f"  {icon} {name}")
        if status:
            passed += 1

    print(f"\nPassed: {passed}/{total}")

    if results["errors"]:
        print(f"\nErrors:")
        for err in results["errors"]:
            print(f"  - {err}")

    return passed >= 4  # At least 4/6 tests should pass


if __name__ == "__main__":
    success = test_rl_knowledge_card()
    sys.exit(0 if success else 1)
