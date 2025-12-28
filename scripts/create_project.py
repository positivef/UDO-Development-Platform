#!/usr/bin/env python3
"""
UDO Project Creation CLI

Creates new projects with governance templates automatically applied.
Part of UDO Platform Layer 3: User Project Application

Usage:
    python scripts/create_project.py --name "my-project" --template standard
    python scripts/create_project.py --name "my-app" --language typescript --template minimal
    python scripts/create_project.py --guided  # Interactive mode
"""

import argparse
import sys
import os
import shutil
from pathlib import Path
from typing import Optional, List
import yaml

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))


# ============================================
# Constants
# ============================================

TEMPLATES_DIR = project_root / "templates"
DEFAULT_TEMPLATE = "standard"

TEMPLATE_INFO = {
    "minimal": {
        "description": "최소 규칙 - 개인 프로젝트/실험용",
        "features": ["Pre-commit (basic)", "CLAUDE.md", "README.md"],
        "strict_mode": False,
    },
    "standard": {
        "description": "표준 규칙 - 팀 프로젝트용",
        "features": ["Pre-commit (full)", "CLAUDE.md", "CI/CD", "Testing"],
        "strict_mode": True,
    },
    "full": {
        "description": "전체 규칙 - 기업/대규모 프로젝트용",
        "features": ["Pre-commit (full)", "CLAUDE.md", "CI/CD", "Testing", "Security", "Compliance"],
        "strict_mode": True,
    },
}


# ============================================
# Helper Functions
# ============================================

def print_banner():
    """Print UDO banner"""
    print("\n" + "=" * 60)
    print("  🚀 UDO Project Creator")
    print("  Governance-enabled project scaffolding")
    print("=" * 60 + "\n")


def print_success(message: str):
    """Print success message"""
    print(f"  ✅ {message}")


def print_error(message: str):
    """Print error message"""
    print(f"  ❌ {message}")


def print_info(message: str):
    """Print info message"""
    print(f"  ℹ️  {message}")


def validate_project_name(name: str) -> bool:
    """Validate project name"""
    if not name:
        return False
    if len(name) > 100:
        return False
    # Allow alphanumeric, hyphens, underscores
    import re
    return bool(re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', name))


def list_templates() -> List[str]:
    """List available templates"""
    return list(TEMPLATE_INFO.keys())


def get_template_path(template_name: str) -> Optional[Path]:
    """Get path to template directory"""
    template_path = TEMPLATES_DIR / template_name
    if template_path.exists():
        return template_path
    return None


# ============================================
# Project Creation
# ============================================

def create_project(
    name: str,
    template: str = DEFAULT_TEMPLATE,
    output_dir: Optional[Path] = None,
    language: str = "python",
    include_pre_commit: bool = True,
    include_ci: bool = True,
) -> Path:
    """
    Create a new project with governance template applied.
    
    Args:
        name: Project name
        template: Template to use (minimal, standard, full)
        output_dir: Where to create the project (default: current directory)
        language: Primary language (python, typescript, both)
        include_pre_commit: Include pre-commit configuration
        include_ci: Include CI/CD configuration
    
    Returns:
        Path to created project
    """
    if output_dir is None:
        output_dir = Path.cwd()
    
    project_path = output_dir / name
    
    # Check if project already exists
    if project_path.exists():
        raise FileExistsError(f"Project directory already exists: {project_path}")
    
    # Get template path
    template_path = get_template_path(template)
    if not template_path:
        raise ValueError(f"Template not found: {template}. Available: {', '.join(list_templates())}")
    
    print_info(f"Creating project '{name}' with '{template}' template...")
    
    # Create project directory
    project_path.mkdir(parents=True, exist_ok=True)
    
    # Copy template files
    files_copied = []
    
    # Copy .governance.yaml
    governance_src = template_path / ".governance.yaml"
    if governance_src.exists():
        governance_dst = project_path / ".governance.yaml"
        shutil.copy(governance_src, governance_dst)
        
        # Update project name in governance file
        with open(governance_dst, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        if 'project' in config:
            config['project']['name'] = name
        
        with open(governance_dst, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        
        files_copied.append(".governance.yaml")
        print_success("Created .governance.yaml")
    
    # Create CLAUDE.md
    claude_content = f"""# {name}

> AI 컨텍스트 문서 - 이 파일을 첫 번째로 읽어주세요.

## 프로젝트 개요

- **이름**: {name}
- **거버넌스 템플릿**: {template}
- **언어**: {language}

## 현재 상태

```yaml
개발 단계: 초기화
테스트 상태: 설정 전
CI/CD: {'활성화' if include_ci else '비활성화'}
```

## 주요 파일

- `.governance.yaml` - 거버넌스 설정
- `README.md` - 프로젝트 소개

## 다음 단계

1. 개발 환경 설정
2. 의존성 설치
3. 첫 번째 기능 구현
"""
    
    (project_path / "CLAUDE.md").write_text(claude_content, encoding='utf-8')
    files_copied.append("CLAUDE.md")
    print_success("Created CLAUDE.md")
    
    # Create README.md
    readme_content = f"""# {name}

> Created with UDO Governance Template: {template}

## Description

TODO: Add project description

## Getting Started

```bash
# Install dependencies
pip install -r requirements.txt  # Python
npm install  # TypeScript

# Pre-commit setup
pip install pre-commit
pre-commit install
```

## Governance

This project uses UDO governance rules. See `.governance.yaml` for configuration.

### Template: {template}

{TEMPLATE_INFO[template]['description']}

**Features**:
{chr(10).join(f'- {f}' for f in TEMPLATE_INFO[template]['features'])}

## License

TODO: Add license
"""
    
    (project_path / "README.md").write_text(readme_content, encoding='utf-8')
    files_copied.append("README.md")
    print_success("Created README.md")
    
    # Create source directories
    if language in ["python", "both"]:
        (project_path / "src").mkdir(exist_ok=True)
        (project_path / "tests").mkdir(exist_ok=True)
        (project_path / "src" / "__init__.py").write_text("# Source package\n", encoding='utf-8')
        files_copied.extend(["src/", "tests/"])
        print_success("Created Python structure (src/, tests/)")
    
    if language in ["typescript", "both"]:
        (project_path / "src").mkdir(exist_ok=True)
        (project_path / "components").mkdir(exist_ok=True)
        files_copied.extend(["src/", "components/"])
        print_success("Created TypeScript structure (src/, components/)")
    
    # Copy pre-commit config if requested
    if include_pre_commit:
        precommit_src = project_root / ".pre-commit-config.yaml"
        if precommit_src.exists():
            shutil.copy(precommit_src, project_path / ".pre-commit-config.yaml")
            files_copied.append(".pre-commit-config.yaml")
            print_success("Created .pre-commit-config.yaml")
    
    # Create .gitignore
    gitignore_content = """# Python
__pycache__/
*.py[cod]
.venv/
*.egg-info/

# TypeScript
node_modules/
dist/
.next/

# IDE
.idea/
.vscode/
*.swp

# Environment
.env
.env.local

# Coverage
htmlcov/
.coverage
coverage/
"""
    
    (project_path / ".gitignore").write_text(gitignore_content, encoding='utf-8')
    files_copied.append(".gitignore")
    print_success("Created .gitignore")
    
    return project_path


# ============================================
# Interactive Mode
# ============================================

def interactive_mode():
    """Run interactive project creation wizard"""
    print_banner()
    print("🧙 Interactive Project Creation Wizard\n")
    
    # Get project name
    while True:
        name = input("📝 Project name: ").strip()
        if validate_project_name(name):
            break
        print_error("Invalid name. Use letters, numbers, hyphens, underscores.")
    
    # Show templates
    print("\n📋 Available templates:\n")
    for i, (tname, tinfo) in enumerate(TEMPLATE_INFO.items(), 1):
        print(f"  {i}. {tname.upper()}")
        print(f"     {tinfo['description']}")
        print(f"     Features: {', '.join(tinfo['features'][:3])}")
        print()
    
    # Get template choice
    while True:
        choice = input("📦 Choose template (1-3) [2]: ").strip() or "2"
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(TEMPLATE_INFO):
                template = list(TEMPLATE_INFO.keys())[idx]
                break
        except ValueError:
            pass
        print_error("Invalid choice. Enter 1, 2, or 3.")
    
    # Get language
    print("\n🔤 Language options: python, typescript, both")
    language = input("🔤 Primary language [python]: ").strip() or "python"
    if language not in ["python", "typescript", "both"]:
        language = "python"
    
    # Confirm
    print(f"\n📋 Summary:")
    print(f"   Name: {name}")
    print(f"   Template: {template}")
    print(f"   Language: {language}")
    
    confirm = input("\n❓ Create project? (y/n) [y]: ").strip().lower() or "y"
    if confirm != "y":
        print("\n⏹️ Cancelled.")
        return None
    
    print()
    project_path = create_project(
        name=name,
        template=template,
        language=language,
    )
    
    return project_path


# ============================================
# Main
# ============================================

def main():
    parser = argparse.ArgumentParser(
        description="Create new projects with UDO governance templates",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/create_project.py --name my-app
  python scripts/create_project.py --name my-app --template minimal
  python scripts/create_project.py --name my-app --language typescript
  python scripts/create_project.py --guided
  python scripts/create_project.py --list-templates
        """
    )
    
    parser.add_argument("--name", "-n", help="Project name")
    parser.add_argument(
        "--template", "-t",
        default=DEFAULT_TEMPLATE,
        choices=list_templates(),
        help=f"Template to use (default: {DEFAULT_TEMPLATE})"
    )
    parser.add_argument(
        "--language", "-l",
        default="python",
        choices=["python", "typescript", "both"],
        help="Primary language (default: python)"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=None,
        help="Output directory (default: current directory)"
    )
    parser.add_argument(
        "--guided", "-g",
        action="store_true",
        help="Run interactive wizard"
    )
    parser.add_argument(
        "--list-templates",
        action="store_true",
        help="List available templates"
    )
    
    args = parser.parse_args()
    
    # List templates
    if args.list_templates:
        print_banner()
        print("📋 Available Templates:\n")
        for name, info in TEMPLATE_INFO.items():
            print(f"  {name.upper()}")
            print(f"    {info['description']}")
            print(f"    Strict Mode: {'Yes' if info['strict_mode'] else 'No'}")
            print(f"    Features: {', '.join(info['features'])}")
            print()
        return
    
    # Interactive mode
    if args.guided:
        project_path = interactive_mode()
        if project_path:
            print(f"\n🎉 Project created at: {project_path}")
            print("\n📝 Next steps:")
            print(f"   cd {project_path.name}")
            print("   pip install pre-commit && pre-commit install")
            print("   git init && git add . && git commit -m 'Initial commit'")
        return
    
    # Normal mode - require name
    if not args.name:
        parser.error("--name is required (or use --guided for interactive mode)")
    
    if not validate_project_name(args.name):
        print_error("Invalid project name. Use letters, numbers, hyphens, underscores.")
        sys.exit(1)
    
    print_banner()
    
    try:
        project_path = create_project(
            name=args.name,
            template=args.template,
            language=args.language,
            output_dir=args.output,
        )
        
        print(f"\n🎉 Project created at: {project_path}")
        print("\n📝 Next steps:")
        print(f"   cd {project_path.name}")
        print("   pip install pre-commit && pre-commit install")
        print("   git init && git add . && git commit -m 'Initial commit'")
        
    except FileExistsError as e:
        print_error(str(e))
        sys.exit(1)
    except ValueError as e:
        print_error(str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
