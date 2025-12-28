#!/bin/bash
# Git Safety Wrapper Script
# Created: 2025-12-23
# Purpose: Block dangerous git commands (git clean) to prevent data loss
# Installation: See scripts/install_git_wrapper.sh

# Color codes for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Check if this is a dangerous git clean command
if [[ "$1" == "clean" ]]; then
    echo ""
    echo -e "${RED}🚫 ==========================================${NC}"
    echo -e "${RED}⚠️  git clean is DISABLED for safety!${NC}"
    echo -e "${RED}==========================================${NC}"
    echo ""
    echo -e "${YELLOW}Reason:${NC} git clean -fd permanently deletes files (no recovery)"
    echo ""
    echo -e "${GREEN}Safe alternatives:${NC}"
    echo "  - Remove specific file: ${GREEN}rm <filename>${NC}"
    echo "  - Preview what would be deleted: ${GREEN}git clean -n -fd${NC}"
    echo "  - Temporarily save: ${GREEN}git stash -u${NC}"
    echo ""
    echo -e "${YELLOW}If you REALLY need git clean:${NC}"
    echo "  1. Backup first: ${GREEN}python scripts/auto_backup_untracked.py --backup${NC}"
    echo "  2. Verify backup: ${GREEN}python scripts/auto_backup_untracked.py --list${NC}"
    echo "  3. Use real git: ${GREEN}/usr/bin/git clean ...${NC} (Unix)"
    echo "     Or: ${GREEN}\"C:\\Program Files\\Git\\cmd\\git.exe\" clean ...${NC} (Windows)"
    echo ""
    exit 1
fi

# Pass through all other git commands to real git
# Find the real git executable
REAL_GIT=""

# Try common git locations
if [ -f "/usr/bin/git" ]; then
    REAL_GIT="/usr/bin/git"
elif [ -f "/bin/git" ]; then
    REAL_GIT="/bin/git"
elif [ -f "/usr/local/bin/git.real" ]; then
    REAL_GIT="/usr/local/bin/git.real"
elif command -v git.real &> /dev/null; then
    REAL_GIT="git.real"
else
    # Fallback: try to find git in PATH, excluding this wrapper
    REAL_GIT=$(which -a git | grep -v "$(readlink -f "$0")" | head -1)
fi

# Execute real git with all arguments
exec "$REAL_GIT" "$@"
