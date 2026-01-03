#!/usr/bin/env python3
"""
Governance Auto-Update System

Automatically checks for and applies governance rule updates.
Can run on schedule (CI) or manually.

Part of UDO Platform Layer 2: Platform Features
"""

import sys
import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import yaml

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))


# ============================================
# Constants
# ============================================

GOVERNANCE_VERSION = "1.0.0"
UPDATE_LOG_FILE = project_root / ".governance_updates.json"
TEMPLATES_DIR = project_root / "templates"


# ============================================
# Helper Functions
# ============================================


def load_update_log() -> Dict:
    """Load update history log"""
    if UPDATE_LOG_FILE.exists():
        with open(UPDATE_LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"updates": [], "last_check": None}


def save_update_log(log: Dict):
    """Save update history log"""
    with open(UPDATE_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, default=str)


def get_file_hash(filepath: Path) -> str:
    """Calculate MD5 hash of file"""
    if not filepath.exists():
        return ""
    with open(filepath, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def load_governance_config(path: Path) -> Optional[Dict]:
    """Load .governance.yaml file"""
    config_file = path / ".governance.yaml"
    if config_file.exists():
        with open(config_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return None


# ============================================
# Update Check Functions
# ============================================


def check_template_updates() -> List[Dict]:
    """Check for template updates"""
    updates = []

    for template_name in ["minimal", "standard", "full"]:
        template_path = TEMPLATES_DIR / template_name / ".governance.yaml"
        if template_path.exists():
            config = load_governance_config(TEMPLATES_DIR / template_name)
            if config:
                current_version = config.get("version", "0.0.0")
                if current_version != GOVERNANCE_VERSION:
                    updates.append(
                        {
                            "template": template_name,
                            "current_version": current_version,
                            "new_version": GOVERNANCE_VERSION,
                            "path": str(template_path),
                        }
                    )

    return updates


def check_rule_consistency() -> List[Dict]:
    """Check for consistency issues between rule files"""
    issues = []

    # Check if UNIFIED_RULES.md exists
    unified_rules = project_root / "docs" / "governance" / "UNIFIED_RULES.md"
    if not unified_rules.exists():
        issues.append(
            {
                "type": "missing_file",
                "file": str(unified_rules),
                "message": "UNIFIED_RULES.md is missing",
            }
        )

    # Check if .governance.yaml exists
    governance_yaml = project_root / ".governance.yaml"
    if not governance_yaml.exists():
        issues.append(
            {
                "type": "missing_file",
                "file": str(governance_yaml),
                "message": ".governance.yaml is missing",
            }
        )

    # Check pre-commit config
    precommit_config = project_root / ".pre-commit-config.yaml"
    if not precommit_config.exists():
        issues.append(
            {
                "type": "missing_file",
                "file": str(precommit_config),
                "message": ".pre-commit-config.yaml is missing",
            }
        )

    return issues


def generate_compliance_report() -> Dict:
    """Generate compliance report"""
    report = {
        "timestamp": datetime.now().isoformat(),
        "version": GOVERNANCE_VERSION,
        "status": "compliant",
        "checks": [],
        "issues": [],
    }

    # Check 1: .governance.yaml exists
    governance_yaml = project_root / ".governance.yaml"
    if governance_yaml.exists():
        report["checks"].append(
            {
                "name": "governance_config",
                "status": "pass",
                "message": ".governance.yaml present",
            }
        )
    else:
        report["checks"].append(
            {
                "name": "governance_config",
                "status": "fail",
                "message": ".governance.yaml missing",
            }
        )
        report["status"] = "non-compliant"

    # Check 2: Pre-commit hooks
    precommit = project_root / ".pre-commit-config.yaml"
    if precommit.exists():
        report["checks"].append(
            {
                "name": "pre_commit",
                "status": "pass",
                "message": "Pre-commit configured",
            }
        )
    else:
        report["checks"].append(
            {
                "name": "pre_commit",
                "status": "fail",
                "message": "Pre-commit not configured",
            }
        )
        report["status"] = "non-compliant"

    # Check 3: CLAUDE.md exists
    claude_md = project_root / "CLAUDE.md"
    if claude_md.exists():
        report["checks"].append(
            {
                "name": "claude_md",
                "status": "pass",
                "message": "CLAUDE.md present",
            }
        )
    else:
        report["checks"].append(
            {
                "name": "claude_md",
                "status": "fail",
                "message": "CLAUDE.md missing",
            }
        )
        report["status"] = "non-compliant"

    # Check 4: Templates exist
    all_templates_exist = all((TEMPLATES_DIR / name / ".governance.yaml").exists() for name in ["minimal", "standard", "full"])
    if all_templates_exist:
        report["checks"].append(
            {
                "name": "templates",
                "status": "pass",
                "message": "All templates present",
            }
        )
    else:
        report["checks"].append(
            {
                "name": "templates",
                "status": "warn",
                "message": "Some templates missing",
            }
        )

    # Check 5: MCP server
    mcp_server = project_root / "mcp-server" / "udo-server.py"
    if mcp_server.exists():
        report["checks"].append(
            {
                "name": "mcp_server",
                "status": "pass",
                "message": "MCP server present",
            }
        )
    else:
        report["checks"].append(
            {
                "name": "mcp_server",
                "status": "warn",
                "message": "MCP server not found",
            }
        )

    # Calculate summary
    passed = sum(1 for c in report["checks"] if c["status"] == "pass")
    total = len(report["checks"])
    report["summary"] = {
        "passed": passed,
        "total": total,
        "percentage": round(passed / total * 100, 1) if total > 0 else 0,
    }

    return report


def update_template_versions():
    """Update all template versions to current"""
    for template_name in ["minimal", "standard", "full"]:
        template_path = TEMPLATES_DIR / template_name / ".governance.yaml"
        if template_path.exists():
            with open(template_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            if config.get("version") != GOVERNANCE_VERSION:
                config["version"] = GOVERNANCE_VERSION

                with open(template_path, "w", encoding="utf-8") as f:
                    yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

                print(f"  [OK] Updated {template_name} to version {GOVERNANCE_VERSION}")


# ============================================
# Main Functions
# ============================================


def run_check(verbose: bool = True) -> Tuple[bool, Dict]:
    """Run all governance checks"""
    if verbose:
        print("\n" + "=" * 60)
        print("  [*] Governance Auto-Update Check")
        print("=" * 60 + "\n")

    all_ok = True
    results = {
        "template_updates": [],
        "consistency_issues": [],
        "compliance": None,
    }

    # Check template updates
    template_updates = check_template_updates()
    results["template_updates"] = template_updates

    if template_updates:
        all_ok = False
        if verbose:
            print("[*] Template Updates Available:")
            for update in template_updates:
                print(f"   - {update['template']}: {update['current_version']} -> {update['new_version']}")
            print()
    elif verbose:
        print("  [OK] All templates up to date\n")

    # Check consistency
    consistency_issues = check_rule_consistency()
    results["consistency_issues"] = consistency_issues

    if consistency_issues:
        all_ok = False
        if verbose:
            print("[WARN] Consistency Issues:")
            for issue in consistency_issues:
                print(f"   - {issue['message']}")
            print()
    elif verbose:
        print("  [OK] All rule files consistent\n")

    # Generate compliance report
    compliance = generate_compliance_report()
    results["compliance"] = compliance

    if verbose:
        print(
            f"[*] Compliance: {compliance['summary']['passed']}/{compliance['summary']['total']} ({compliance['summary']['percentage']}%)"
        )
        print(f"   Status: {compliance['status'].upper()}\n")

        for check in compliance["checks"]:
            icon = "[OK]" if check["status"] == "pass" else ("[WARN]" if check["status"] == "warn" else "[FAIL]")
            print(f"   {icon} {check['name']}: {check['message']}")

    # Update log
    log = load_update_log()
    log["last_check"] = datetime.now().isoformat()
    log["last_result"] = {
        "all_ok": all_ok,
        "template_updates": len(template_updates),
        "consistency_issues": len(consistency_issues),
        "compliance": compliance["status"],
    }
    save_update_log(log)

    if verbose:
        print("\n" + "=" * 60)
        print(f"  {'[OK] All checks passed!' if all_ok else '[WARN] Issues found - review above'}")
        print("=" * 60 + "\n")

    return all_ok, results


def run_update(verbose: bool = True) -> bool:
    """Apply pending updates"""
    if verbose:
        print("\n" + "=" * 60)
        print("  [*] Applying Governance Updates")
        print("=" * 60 + "\n")

    # Update template versions
    update_template_versions()

    # Log update
    log = load_update_log()
    log["updates"].append(
        {
            "timestamp": datetime.now().isoformat(),
            "version": GOVERNANCE_VERSION,
            "action": "version_update",
        }
    )
    save_update_log(log)

    if verbose:
        print("\n  [OK] Updates applied successfully\n")

    return True


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Governance Auto-Update System")
    parser.add_argument("--check", action="store_true", help="Check for updates (default)")
    parser.add_argument("--update", action="store_true", help="Apply pending updates")
    parser.add_argument("--report", action="store_true", help="Generate compliance report only")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if args.report:
        report = generate_compliance_report()
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print(f"\n[*] Compliance Report")
            print(f"   Status: {report['status'].upper()}")
            print(f"   Score: {report['summary']['percentage']}%")
            for check in report["checks"]:
                icon = "[OK]" if check["status"] == "pass" else "[FAIL]"
                print(f"   {icon} {check['name']}")
        return

    if args.update:
        run_update()
    else:
        all_ok, results = run_check(verbose=not args.json)
        if args.json:
            print(json.dumps(results, indent=2, default=str))
        sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
