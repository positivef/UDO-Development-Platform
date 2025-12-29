import argparse
import sys
import os
import httpx
import json
from pathlib import Path

# Add scripts directory to path for imports
SCRIPT_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

# URL configuration
API_URL = os.environ.get("UDO_API_URL", "http://127.0.0.1:8001")

# ANSI color codes
def get_colors():
    """Get ANSI color codes, respecting NO_COLOR environment variable."""
    if os.environ.get("NO_COLOR"):
        return {"GREEN": "", "YELLOW": "", "BLUE": "", "CYAN": "", "MAGENTA": "", "RESET": "", "BOLD": "", "DIM": ""}
    return {
        "GREEN": "\033[92m",
        "YELLOW": "\033[93m",
        "BLUE": "\033[94m",
        "CYAN": "\033[96m",
        "MAGENTA": "\033[95m",
        "RESET": "\033[0m",
        "BOLD": "\033[1m",
        "DIM": "\033[2m",
    }

def get_tier_status():
    try:
        with httpx.Client() as client:
            resp = client.get(f"{API_URL}/api/governance/tier/status")
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        print(f"Error connecting to UDO Backend ({API_URL}): {e}")
        print("Ensure the backend server is running.")
        sys.exit(1)

def command_status(args):
    """Show current governance status"""
    data = get_tier_status()

    c = get_colors()
    GREEN, YELLOW, BLUE, RESET, BOLD = c["GREEN"], c["YELLOW"], c["BLUE"], c["RESET"], c["BOLD"]

    print(f"\n{BOLD}UDO Governance Status{RESET}")
    print("=========================")
    print(f"Current Tier:  {BLUE}{data['current_tier']}{RESET}")
    print(f"Description:   {data['tier_description']}")

    score_color = GREEN if data['compliance_score'] >= 80 else YELLOW
    print(f"Compliance:    {score_color}{data['compliance_score']}%{RESET}")

    if data['missing_rules']:
        print(f"\n{YELLOW}⚠️  Missing Rules:{RESET}")
        for rule in data['missing_rules']:
            print(f"  - {rule}")

    if data['next_tier']:
        print(f"\n{GREEN}🚀 Next Level: {data['next_tier']}{RESET}")
        print(f"   Run '{BOLD}udo upgrade-tier --to={data['next_tier']}{RESET}' to upgrade.")
    else:
        print(f"\n✨ {GREEN}You are at the highest tier!{RESET}")

def command_upgrade(args):
    """Upgrade project tier"""
    target = args.to
    print(f"🚀 Initiating upgrade to {target}...")

    try:
        with httpx.Client() as client:
            resp = client.post(f"{API_URL}/api/governance/tier/upgrade", json={"target_tier": target})
            resp.raise_for_status()
            result = resp.json()

        print(f"\n✅ Upgrade Successful!")
        print(f"Result: {result['message']}")
        print("\nChanges Applied:")
        for change in result['changes_applied']:
            print(f"  + {change}")

    except httpx.HTTPStatusError as e:
        print(f"❌ Upgrade Failed: {e.response.text}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Connection Failed: {e}")
        sys.exit(1)

# =============================================================================
# Curriculum Commands
# =============================================================================

def get_curriculum_info():
    """Load curriculum information from obsidian_auto_sync module."""
    try:
        from obsidian_auto_sync import load_learning_progress, save_learning_progress, LEARNING_CURRICULUM
        return load_learning_progress, save_learning_progress, LEARNING_CURRICULUM
    except ImportError as e:
        print(f"Error: Could not import curriculum module: {e}")
        print("Make sure scripts/obsidian_auto_sync.py exists.")
        sys.exit(1)


def calculate_progress(month: int, week: int) -> tuple:
    """Calculate learning progress percentage and current week number.

    Returns:
        (current_week_number, total_weeks, percentage)
    """
    # 3 months x 4 weeks = 12 total weeks
    total_weeks = 12
    current_week_num = (month - 1) * 4 + week
    percentage = int((current_week_num / total_weeks) * 100)
    return current_week_num, total_weeks, percentage


def render_progress_bar(percentage: int, width: int = 20) -> str:
    """Render a text-based progress bar."""
    filled = int(width * percentage / 100)
    empty = width - filled
    # Use Unicode block characters for better visual
    bar = "[" + "=" * filled + " " * empty + "]"
    return bar


def command_curriculum_status(args):
    """Show current learning stage."""
    load_learning_progress, _, LEARNING_CURRICULUM = get_curriculum_info()

    c = get_colors()
    GREEN, YELLOW, BLUE, CYAN, MAGENTA, RESET, BOLD, DIM = (
        c["GREEN"], c["YELLOW"], c["BLUE"], c["CYAN"],
        c["MAGENTA"], c["RESET"], c["BOLD"], c["DIM"]
    )

    progress = load_learning_progress()
    month = progress.get("month", 1)
    week = progress.get("week", 1)
    started_at = progress.get("started_at")
    checkpoints_done = progress.get("checkpoints_done", [])

    # Get curriculum details
    key = (month, week)
    curriculum = LEARNING_CURRICULUM.get(key, LEARNING_CURRICULUM.get((1, 1), {}))

    # Calculate progress
    current_week_num, total_weeks, percentage = calculate_progress(month, week)
    progress_bar = render_progress_bar(percentage)

    # Display
    print(f"\n{BOLD}Current Learning Stage: Month {month} Week {week}{RESET}")
    print(f"   {DIM}Progress:{RESET} {progress_bar} {percentage}% (Week {current_week_num}/{total_weeks})")
    print(f"   {DIM}Focus:{RESET}    {CYAN}{curriculum.get('focus', 'N/A')}{RESET}")
    print(f"   {DIM}Title:{RESET}    {curriculum.get('title', 'N/A')}")

    if started_at:
        print(f"   {DIM}Started:{RESET}  {started_at[:10]}")

    # Show checkpoints
    checkpoints = curriculum.get("checkpoints", [])
    if checkpoints:
        print(f"\n{BOLD}Checkpoints:{RESET}")
        for cp in checkpoints:
            done = cp in checkpoints_done
            status = f"{GREEN}[Done]{RESET}" if done else f"{YELLOW}[Todo]{RESET}"
            print(f"   {status} {cp}")

    # Show considerations if any
    considerations = curriculum.get("considerations", [])
    if considerations:
        print(f"\n{BOLD}Considerations:{RESET}")
        for item in considerations:
            print(f"   {BLUE}-{RESET} {item}")

    # Show warnings if any
    warnings = curriculum.get("warnings", [])
    if warnings:
        print(f"\n{BOLD}Warnings:{RESET}")
        for item in warnings:
            print(f"   {YELLOW}!{RESET} {item}")

    # Show guide reference
    guide = curriculum.get("guide", "")
    if guide:
        print(f"\n{DIM}Guide: {guide}{RESET}")

    print()


def command_curriculum_next(args):
    """Advance to next week in the curriculum."""
    load_learning_progress, save_learning_progress, LEARNING_CURRICULUM = get_curriculum_info()

    c = get_colors()
    GREEN, YELLOW, CYAN, RESET, BOLD = c["GREEN"], c["YELLOW"], c["CYAN"], c["RESET"], c["BOLD"]

    progress = load_learning_progress()
    old_month = progress.get("month", 1)
    old_week = progress.get("week", 1)

    # Calculate next week
    new_month = old_month
    new_week = old_week + 1

    if new_week > 4:
        new_week = 1
        new_month += 1

    # Check if we've completed the curriculum
    if new_month > 3:
        print(f"\n{GREEN}Congratulations! You have completed the entire 3-month curriculum!{RESET}")
        print(f"   Current: Month {old_month} Week {old_week}")
        print(f"\n   Consider starting over or exploring advanced topics.")
        print()
        return

    # Update progress
    progress["month"] = new_month
    progress["week"] = new_week
    progress["checkpoints_done"] = []  # Reset checkpoints for new week

    if save_learning_progress(progress):
        # Get new focus
        key = (new_month, new_week)
        curriculum = LEARNING_CURRICULUM.get(key, {})
        new_focus = curriculum.get("focus", "N/A")
        new_title = curriculum.get("title", "N/A")

        print(f"\n{GREEN}Month {old_month} Week {old_week} -> Month {new_month} Week {new_week} Done!{RESET}")
        print(f"   {BOLD}New Focus:{RESET} {CYAN}{new_focus}{RESET}")
        print(f"   {BOLD}Title:{RESET}     {new_title}")
        print()
    else:
        print(f"\n{YELLOW}Error: Failed to save progress. Check .udo/session_state.json permissions.{RESET}")
        sys.exit(1)


def command_curriculum_set(args):
    """Set a specific month and week in the curriculum."""
    load_learning_progress, save_learning_progress, LEARNING_CURRICULUM = get_curriculum_info()

    c = get_colors()
    GREEN, YELLOW, CYAN, RESET, BOLD = c["GREEN"], c["YELLOW"], c["CYAN"], c["RESET"], c["BOLD"]

    target_month = args.month
    target_week = args.week

    # Validate range
    if target_month < 1 or target_month > 3:
        print(f"\n{YELLOW}Error: Month must be between 1 and 3.{RESET}")
        sys.exit(1)

    if target_week < 1 or target_week > 4:
        print(f"\n{YELLOW}Error: Week must be between 1 and 4.{RESET}")
        sys.exit(1)

    # Check if curriculum exists for this week
    key = (target_month, target_week)
    if key not in LEARNING_CURRICULUM:
        print(f"\n{YELLOW}Error: No curriculum defined for Month {target_month} Week {target_week}.{RESET}")
        sys.exit(1)

    # Load current progress
    progress = load_learning_progress()
    old_month = progress.get("month", 1)
    old_week = progress.get("week", 1)

    # Update progress
    progress["month"] = target_month
    progress["week"] = target_week
    progress["checkpoints_done"] = []  # Reset checkpoints

    if save_learning_progress(progress):
        curriculum = LEARNING_CURRICULUM[key]
        new_focus = curriculum.get("focus", "N/A")
        new_title = curriculum.get("title", "N/A")

        print(f"\n{GREEN}Month {old_month} Week {old_week} -> Month {target_month} Week {target_week} Set!{RESET}")
        print(f"   {BOLD}New Focus:{RESET} {CYAN}{new_focus}{RESET}")
        print(f"   {BOLD}Title:{RESET}     {new_title}")
        print()
    else:
        print(f"\n{YELLOW}Error: Failed to save progress. Check .udo/session_state.json permissions.{RESET}")
        sys.exit(1)


def command_curriculum(args):
    """Handle curriculum subcommand routing."""
    if args.curriculum_command == "status":
        command_curriculum_status(args)
    elif args.curriculum_command == "next":
        command_curriculum_next(args)
    elif args.curriculum_command == "set":
        command_curriculum_set(args)
    else:
        print("Usage: udo curriculum {status|next|set}")
        print("\nCommands:")
        print("  status              Show current learning stage")
        print("  next                Advance to next week")
        print("  set --month M --week W   Set specific month and week")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="UDO Development Platform CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # status command
    subparsers.add_parser("status", help="Show current project governance status")

    # upgrade-tier command
    upg_parser = subparsers.add_parser("upgrade-tier", help="Upgrade project to next tier")
    upg_parser.add_argument("--to", required=True, choices=["tier-2", "tier-3", "tier-4"], help="Target tier")

    # curriculum command with subcommands
    curriculum_parser = subparsers.add_parser("curriculum", help="Manage learning curriculum progress")
    curriculum_subparsers = curriculum_parser.add_subparsers(dest="curriculum_command", help="Curriculum commands")

    # curriculum status
    curriculum_subparsers.add_parser("status", help="Show current learning stage")

    # curriculum next
    curriculum_subparsers.add_parser("next", help="Advance to next week")

    # curriculum set
    set_parser = curriculum_subparsers.add_parser("set", help="Set specific month and week")
    set_parser.add_argument("--month", "-m", type=int, required=True, help="Target month (1-3)")
    set_parser.add_argument("--week", "-w", type=int, required=True, help="Target week (1-4)")

    args = parser.parse_args()

    if args.command == "status":
        command_status(args)
    elif args.command == "upgrade-tier":
        command_upgrade(args)
    elif args.command == "curriculum":
        command_curriculum(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
