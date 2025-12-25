import argparse
import sys
import os
import httpx
import json

# URL configuration
API_URL = os.environ.get("UDO_API_URL", "http://127.0.0.1:8001")

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
    
    # ANSI colors (may not work in all Windows terminals without enablement, but good for standardization)
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"
    
    # Check if NO_COLOR is set
    if os.environ.get("NO_COLOR"):
        GREEN = YELLOW = BLUE = RESET = BOLD = ""

    print(f"\n{BOLD}🛡️  UDO Governance Status{RESET}")
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

def main():
    parser = argparse.ArgumentParser(description="UDO Development Platform CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # status command
    subparsers.add_parser("status", help="Show current project governance status")
    
    # upgrade-tier command
    upg_parser = subparsers.add_parser("upgrade-tier", help="Upgrade project to next tier")
    upg_parser.add_argument("--to", required=True, choices=["tier-2", "tier-3", "tier-4"], help="Target tier")
    
    args = parser.parse_args()
    
    if args.command == "status":
        command_status(args)
    elif args.command == "upgrade-tier":
        command_upgrade(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
