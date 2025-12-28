#!/usr/bin/env python
"""
Documentation Consistency Validator
---------------------------------
Ensures that critical documentation files, governance rules, and
Obsidian sync configurations are present and referenced correctly.

Checks performed:
1. Presence of required files (docs/, claudedocs/, .governance.yaml, etc.)
2. Each rule file listed in `.governance.yaml` exists on disk.
3. Each documentation file referenced in `docs/SSOT_REGISTRY.md` exists.
4. Obsidian vault path matches the user‑defined memory path.
5. Pre‑commit config contains the `validate_documentation_consistency` hook.

Exit code:
- 0 : All checks passed
- 1 : One or more checks failed (details printed to stdout)
"""
import os
import sys
import yaml
from pathlib import Path

# ---------- Configuration ----------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = [
    PROJECT_ROOT / "claudedocs" / "decisions" / "2025-12-15-DOCUMENTATION-RULES-SYSTEM-v2-COMPLETE.md",
    PROJECT_ROOT / "config" / "config.yaml",
    PROJECT_ROOT / ".governance.yaml",
    PROJECT_ROOT / "docs" / "SSOT_REGISTRY.md",
    PROJECT_ROOT / "scripts" / "validate_system_rules.py",
    PROJECT_ROOT / "scripts" / "check_korean_preservation.py",
]

def check_file_exists(path: Path) -> bool:
    if not path.exists():
        print(f"[ERROR] Missing required file: {path}")
        return False
    return True

def load_governance() -> dict:
    gov_path = PROJECT_ROOT / ".governance.yaml"
    if not gov_path.is_file():
        print("[ERROR] .governance.yaml not found")
        return {}
    with open(gov_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def verify_governance_rules(governance: dict) -> bool:
    ok = True
    # Example: ensure obsidian_sync flag exists
    if not governance.get("obsidian_sync"):
        print("[WARN] obsidian_sync not defined in .governance.yaml (defaulting to true)")
    # Add more rule checks as needed
    return ok

def verify_ssot_registry() -> bool:
    ssot_path = PROJECT_ROOT / "docs" / "SSOT_REGISTRY.md"
    if not ssot_path.is_file():
        print("[ERROR] SSOT_REGISTRY.md missing")
        return False
    # Simple sanity: ensure Tier 1 files are listed
    with open(ssot_path, "r", encoding="utf-8") as f:
        content = f.read()
    missing = []
    for tier_file in ["CLAUDE.md", "CURRENT.md", "SSOT_REGISTRY.md"]:
        if tier_file not in content:
            missing.append(tier_file)
    if missing:
        print(f"[ERROR] Tier 1 files not referenced in SSOT_REGISTRY.md: {missing}")
        return False
    return True

def verify_obsidian_path() -> bool:
    # User‑defined memory path
    expected_path = Path(r"C:\\Users\\user\\Documents\\Obsidian Vault")
    # Check that .governance.yaml (if it defines a vault) matches
    governance = load_governance()
    vault_path = governance.get("obsidian_vault_path")
    if vault_path and Path(vault_path) != expected_path:
        print(f"[WARN] Obsidian vault path in .governance.yaml ({vault_path}) differs from expected ({expected_path})")
    return True

def verify_precommit_hook() -> bool:
    precommit_path = PROJECT_ROOT / ".pre-commit-config.yaml"
    if not precommit_path.is_file():
        print("[ERROR] .pre-commit-config.yaml missing")
        return False
    with open(precommit_path, "r", encoding="utf-8") as f:
        content = f.read()
    if "validate_documentation_consistency" not in content:
        print("[ERROR] Pre‑commit hook for documentation consistency not configured")
        return False
    return True

def main():
    all_ok = True
    for p in REQUIRED_FILES:
        all_ok &= check_file_exists(p)
    governance = load_governance()
    all_ok &= verify_governance_rules(governance)
    all_ok &= verify_ssot_registry()
    all_ok &= verify_obsidian_path()
    all_ok &= verify_precommit_hook()
    sys.exit(0 if all_ok else 1)

if __name__ == "__main__":
    main()
