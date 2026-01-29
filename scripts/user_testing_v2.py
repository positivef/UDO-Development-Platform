"""
User Testing Simulation v2 - With warmup and adjusted selectors
"""

import json
import time
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:3000"
BACKEND_URL = "http://localhost:8000"
SCREENSHOT_DIR = Path("claudedocs/user-testing-screenshots")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


def take_screenshot(page, name):
    path = SCREENSHOT_DIR / f"{name}.png"
    page.screenshot(path=str(path), full_page=True)
    return str(path)


def warmup_pages(page):
    """Visit all pages once to trigger Next.js compilation"""
    pages = [
        "/",
        "/kanban",
        "/uncertainty",
        "/confidence",
        "/quality",
        "/time-tracking",
        "/governance",
        "/ck-theory",
        "/gi-formula",
        "/archive",
    ]
    print("  Warming up pages (Next.js compilation)...")
    for p in pages:
        try:
            page.goto(f"{BASE_URL}{p}", timeout=60000)
            page.wait_for_load_state("networkidle", timeout=60000)
        except Exception:
            pass
    print("  Warmup complete!")


def test_api_endpoints():
    """Test backend API endpoints"""
    import urllib.request

    results = []
    endpoints = [
        ("/docs", "Swagger UI"),
        ("/api/health", "Health Check"),
        ("/api/kanban/tasks", "Kanban Tasks"),
        ("/api/time-tracking/roi", "Time Tracking ROI"),
        ("/api/uncertainty/status", "Uncertainty Status"),
    ]
    for path, name in endpoints:
        try:
            req = urllib.request.Request(f"{BACKEND_URL}{path}")
            with urllib.request.urlopen(req, timeout=5) as resp:
                results.append({"endpoint": path, "name": name, "status": "pass", "code": resp.status})
        except Exception as e:
            results.append({"endpoint": path, "name": name, "status": "fail", "error": str(e)[:50]})
    return results


def test_page(page, path, name, checks):
    """Generic page tester"""
    scenario = {"name": name, "steps": [], "issues": []}

    start = time.time()
    page.goto(f"{BASE_URL}{path}", timeout=30000)
    page.wait_for_load_state("networkidle", timeout=30000)
    load_ms = round((time.time() - start) * 1000)

    # Page load (dev mode: 5s tolerance)
    scenario["steps"].append(
        {
            "name": f"{name} loads",
            "status": "pass" if load_ms < 5000 else "warn",
            "load_time_ms": load_ms,
        }
    )
    take_screenshot(page, f"{path.replace('/', '_')}_{int(time.time())}")

    # Run checks
    for check_name, selector, min_count in checks:
        elements = page.locator(selector)
        count = elements.count()
        passed = count >= min_count
        scenario["steps"].append(
            {
                "name": check_name,
                "status": "pass" if passed else "warn",
                "detail": f"Found {count} (need {min_count}+)",
            }
        )

    # No JS errors
    errors = []
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.reload()
    page.wait_for_load_state("networkidle", timeout=30000)
    scenario["steps"].append(
        {
            "name": "No JS errors on reload",
            "status": "pass" if len(errors) == 0 else "warn",
            "detail": f"{len(errors)} errors",
        }
    )

    passes = sum(1 for s in scenario["steps"] if s["status"] == "pass")
    scenario["score"] = round(passes / len(scenario["steps"]) * 5, 1)
    return scenario


def main():
    print("=" * 60)
    print("UDO Platform v3.0 - User Testing Simulation v2")
    print("=" * 60)
    print()

    # API Tests
    print("[1/7] Testing Backend API...")
    api = test_api_endpoints()
    api_ok = sum(1 for a in api if a["status"] == "pass")
    print(f"  API: {api_ok}/{len(api)} endpoints OK")

    results = {
        "test_date": datetime.now().isoformat(),
        "version": "v2",
        "api_tests": api,
        "scenarios": [],
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = ctx.new_page()

        # Warmup
        print("[2/7] Warming up pages...")
        warmup_pages(page)

        # Scenario 1: Kanban Board
        print("[3/7] Scenario 1: Kanban Board (Junior Dev)...")
        s1 = test_page(
            page,
            "/kanban",
            "Kanban Board",
            [
                ("Headings visible", "h1, h2, h3", 1),
                ("Task cards visible", "[class*='task'], [class*='Task'], [class*='card'], [class*='Card']", 1),
                ("Interactive buttons", "button", 3),
                ("SVG/canvas elements", "svg, canvas", 1),
            ],
        )
        s1["profile"] = "Junior Developer"
        results["scenarios"].append(s1)
        print(f"  Score: {s1['score']}/5.0")

        # Scenario 2: Navigation (All pages)
        print("[4/7] Scenario 2: Navigation (Senior Dev)...")
        s2 = {"name": "Navigation Coverage", "profile": "Senior Developer", "steps": [], "issues": []}
        nav_pages = [
            "/",
            "/kanban",
            "/uncertainty",
            "/confidence",
            "/quality",
            "/time-tracking",
            "/governance",
            "/ck-theory",
            "/gi-formula",
            "/archive",
        ]
        working = 0
        for np in nav_pages:
            try:
                start = time.time()
                page.goto(f"{BASE_URL}{np}", timeout=15000)
                page.wait_for_load_state("networkidle", timeout=15000)
                ms = round((time.time() - start) * 1000)
                s2["steps"].append({"name": f"Page {np}", "status": "pass", "load_time_ms": ms})
                working += 1
            except Exception:
                s2["steps"].append({"name": f"Page {np}", "status": "fail"})
        passes = sum(1 for s in s2["steps"] if s["status"] == "pass")
        s2["score"] = round(passes / len(s2["steps"]) * 5, 1)
        results["scenarios"].append(s2)
        print(f"  Score: {s2['score']}/5.0 ({working}/{len(nav_pages)} pages)")

        # Scenario 3: Uncertainty Map
        print("[5/7] Scenario 3: Uncertainty Map (PM)...")
        s3 = test_page(
            page,
            "/uncertainty",
            "Uncertainty Map",
            [
                ("Headings", "h1, h2, h3", 1),
                ("Charts/SVGs", "svg, canvas, [class*='chart'], [class*='Chart']", 1),
                ("Data cards", "[class*='card'], [class*='Card']", 1),
            ],
        )
        s3["profile"] = "Project Manager"
        results["scenarios"].append(s3)
        print(f"  Score: {s3['score']}/5.0")

        # Scenario 4: Confidence Dashboard
        print("[6/7] Scenario 4: Confidence Dashboard (DevOps)...")
        s4 = test_page(
            page,
            "/confidence",
            "Confidence Dashboard",
            [
                ("Headings", "h1, h2, h3", 1),
                ("Charts/visuals", "svg, canvas", 1),
                ("Interactive elements", "button, select, input", 1),
            ],
        )
        s4["profile"] = "DevOps Engineer"
        results["scenarios"].append(s4)
        print(f"  Score: {s4['score']}/5.0")

        # Scenario 5: Governance + Quality + Time
        print("[7/7] Scenario 5: Governance & Quality (PO)...")
        s5 = {"name": "Governance & Quality", "profile": "Product Owner", "steps": [], "issues": []}
        test_pages = [
            ("/governance", "Governance"),
            ("/quality", "Quality"),
            ("/time-tracking", "Time Tracking"),
        ]
        for tp_path, tp_name in test_pages:
            try:
                start = time.time()
                page.goto(f"{BASE_URL}{tp_path}", timeout=15000)
                page.wait_for_load_state("networkidle", timeout=15000)
                ms = round((time.time() - start) * 1000)
                s5["steps"].append({"name": f"{tp_name} loads", "status": "pass", "load_time_ms": ms})

                # Check content
                content = page.locator("h1, h2, h3, [class*='card'], [class*='Card']")
                has_content = content.count() > 0
                s5["steps"].append(
                    {
                        "name": f"{tp_name} has content",
                        "status": "pass" if has_content else "warn",
                        "detail": f"{content.count()} elements",
                    }
                )
            except Exception as e:
                s5["steps"].append({"name": f"{tp_name} loads", "status": "fail", "error": str(e)[:50]})

        passes = sum(1 for s in s5["steps"] if s["status"] == "pass")
        s5["score"] = round(passes / max(len(s5["steps"]), 1) * 5, 1)
        results["scenarios"].append(s5)
        print(f"  Score: {s5['score']}/5.0")

        browser.close()

    # Summary
    scores = [s.get("score", 0) for s in results["scenarios"]]
    avg = round(sum(scores) / len(scores), 1)
    results["summary"] = {
        "scenarios": len(results["scenarios"]),
        "average_score": avg,
        "target": 4.0,
        "target_met": avg >= 4.0,
        "api_ok": api_ok,
        "scores_by_scenario": {s["name"]: s.get("score", 0) for s in results["scenarios"]},
    }

    print()
    print("=" * 60)
    print(f"OVERALL: {avg}/5.0 (Target: 4.0)")
    print(f"TARGET: {'PASS' if avg >= 4.0 else 'NOT MET'}")
    for s in results["scenarios"]:
        print(f"  {s['name']}: {s.get('score', 0)}/5.0 ({s.get('profile', '-')})")
    print(f"API: {api_ok}/{len(api)}")
    print("=" * 60)

    output = Path("claudedocs/user-testing-screenshots/results_v2.json")
    with open(output, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    print(f"\nSaved: {output}")


if __name__ == "__main__":
    main()
