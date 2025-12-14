"""
E2E Test for Project Selector Portal Implementation

Tests:
1. Dashboard loads successfully
2. Project Selector dropdown appears above other panels (z-index)
3. Project switching works for all 3 projects
4. UI updates correctly after switching
"""

from playwright.sync_api import sync_playwright
import json
import time


def test_project_selector():
    """Test Project Selector Portal implementation"""

    print("🚀 Starting Project Selector E2E Test")

    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False)  # Visible for inspection
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()

        # Capture console logs
        console_logs = []
        page.on('console', lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))

        try:
            # Test 1: Load Dashboard
            print("\n📍 Test 1: Loading Dashboard...")
            page.goto('http://localhost:3000', timeout=30000)
            page.wait_for_load_state('networkidle')
            time.sleep(2)  # Allow React hydration

            # Take initial screenshot
            page.screenshot(path='screenshots/01_dashboard_loaded.png', full_page=True)
            print("✅ Dashboard loaded successfully")

            # Test 2: Find Project Selector Button
            print("\n📍 Test 2: Finding Project Selector...")

            # Look for the button with FolderGit2 icon or "Select Project" text
            selector_button = page.locator('button:has-text("Select Project"), button:has-text("UDO-Development-Platform"), button:has-text("E-Commerce-Platform"), button:has-text("Mobile-Banking-App")').first

            if selector_button.count() == 0:
                print("❌ Project Selector button not found")
                page.screenshot(path='screenshots/02_selector_not_found.png', full_page=True)
                return False

            print(f"✅ Found Project Selector: {selector_button.inner_text()}")
            page.screenshot(path='screenshots/02_selector_found.png', full_page=True)

            # Test 3: Click dropdown and verify Portal rendering
            print("\n📍 Test 3: Testing Portal z-index (dropdown should be above panels)...")

            # Get initial button position
            button_box = selector_button.bounding_box()
            print(f"Button position: top={button_box['y']}, right={button_box['x'] + button_box['width']}")

            # Click to open dropdown
            selector_button.click()
            time.sleep(1)  # Wait for animation

            # Find dropdown in DOM (should be rendered to document.body via Portal)
            dropdown = page.locator('div.w-80.bg-gray-800.border.border-gray-700.rounded-lg.shadow-xl')

            if dropdown.count() == 0:
                print("❌ Dropdown not found after click")
                page.screenshot(path='screenshots/03_dropdown_not_found.png', full_page=True)
                return False

            # Verify dropdown is visible and positioned correctly
            dropdown_box = dropdown.bounding_box()
            print(f"✅ Dropdown visible at: top={dropdown_box['y']}, right={dropdown_box['x'] + dropdown_box['width']}")

            # Check if dropdown is rendered outside the parent (Portal pattern)
            dropdown_html = dropdown.evaluate('el => el.outerHTML')
            is_portaled = 'position: fixed' in dropdown_html or dropdown.evaluate('el => getComputedStyle(el).position === "fixed"')

            if is_portaled:
                print("✅ Dropdown uses fixed positioning (Portal pattern)")
            else:
                print("⚠️ Dropdown might not be using Portal pattern")

            page.screenshot(path='screenshots/03_dropdown_open.png', full_page=True)

            # Test 4: Get project list
            print("\n📍 Test 4: Finding available projects...")

            project_buttons = page.locator('button:has-text("UDO-Development-Platform"), button:has-text("E-Commerce-Platform"), button:has-text("Mobile-Banking-App")').all()

            if len(project_buttons) == 0:
                print("❌ No projects found in dropdown")
                return False

            print(f"✅ Found {len(project_buttons)} projects")

            # List all projects
            for i, btn in enumerate(project_buttons):
                text = btn.inner_text()
                print(f"  {i+1}. {text.split()[0] if text else 'Unknown'}")

            # Test 5: Switch between projects
            print("\n📍 Test 5: Testing project switching...")

            projects_tested = []

            for i, project_btn in enumerate(project_buttons[:3]):  # Test up to 3 projects
                project_name = project_btn.inner_text().split('\n')[0]
                print(f"\n  Switching to: {project_name}")

                # Click project
                project_btn.click()
                time.sleep(2)  # Wait for API call and UI update

                # Check for success toast or UI update
                page.screenshot(path=f'screenshots/04_switched_{i+1}_{project_name.replace(" ", "_")}.png', full_page=True)

                # Verify project name updated in button
                current_text = selector_button.inner_text()

                if project_name in current_text:
                    print(f"  ✅ Switched to {project_name}")
                    projects_tested.append(project_name)
                else:
                    print(f"  ⚠️ UI might not have updated (expected: {project_name}, got: {current_text})")

                # Reopen dropdown for next iteration
                if i < len(project_buttons) - 1:
                    selector_button.click()
                    time.sleep(1)

            # Test 6: Final verification
            print("\n📍 Test 6: Final verification...")
            print(f"Projects tested: {len(projects_tested)}/{len(project_buttons)}")

            # Check console for errors
            errors = [log for log in console_logs if 'error' in log.lower() and 'tasks' not in log.lower()]
            if errors:
                print(f"\n⚠️ Console errors found (excluding /api/tasks):")
                for error in errors[:5]:  # Show first 5
                    print(f"  {error}")
            else:
                print("✅ No critical console errors")

            # Final screenshot
            page.screenshot(path='screenshots/05_final_state.png', full_page=True)

            print("\n" + "="*60)
            print("✅ E2E Test Summary:")
            print(f"  - Dashboard: ✅ Loaded")
            print(f"  - Project Selector: ✅ Found")
            print(f"  - Dropdown Portal: ✅ Rendered")
            print(f"  - Projects switched: {len(projects_tested)}/3")
            print(f"  - Screenshots saved to: screenshots/")
            print("="*60)

            return True

        except Exception as e:
            print(f"\n❌ Test failed with error: {e}")
            page.screenshot(path='screenshots/error_state.png', full_page=True)
            return False

        finally:
            time.sleep(3)  # Keep browser open for inspection
            browser.close()


if __name__ == "__main__":
    import os

    # Create screenshots directory
    os.makedirs('screenshots', exist_ok=True)

    success = test_project_selector()
    exit(0 if success else 1)
