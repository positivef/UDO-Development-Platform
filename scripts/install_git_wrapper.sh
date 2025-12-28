#!/bin/bash
# Git Wrapper Installation Script
# Created: 2025-12-23
# Purpose: Install git-safe-wrapper.sh to block dangerous git commands

set -e  # Exit on error

WRAPPER_SCRIPT="$(pwd)/scripts/git-safe-wrapper.sh"
INSTALL_DIR="/usr/local/bin"
WRAPPER_NAME="git"

echo "🔧 Git Safety Wrapper Installation"
echo "=================================="
echo ""

# Check if running on Windows (Git Bash)
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo "⚠️  Windows Environment Detected"
    echo ""
    echo "On Windows, the wrapper installation is more complex."
    echo "We recommend using PowerShell function instead."
    echo ""
    echo "Please see: docs/GIT_WRAPPER_WINDOWS_INSTALL.md"
    echo ""
    echo "Or use the PowerShell installation script:"
    echo "  scripts/install_git_wrapper.ps1"
    echo ""
    exit 1
fi

# Check if running as root/sudo
if [ "$EUID" -ne 0 ]; then
    echo "❌ This script requires sudo privileges"
    echo "   Please run: sudo bash $0"
    exit 1
fi

# Make wrapper executable
chmod +x "$WRAPPER_SCRIPT"
echo "✅ Made wrapper executable"

# Backup existing git if it's not already backed up
if [ -f "$INSTALL_DIR/$WRAPPER_NAME" ] && [ ! -f "$INSTALL_DIR/$WRAPPER_NAME.real" ]; then
    cp "$INSTALL_DIR/$WRAPPER_NAME" "$INSTALL_DIR/$WRAPPER_NAME.real"
    echo "✅ Backed up original git to git.real"
fi

# Install wrapper
cp "$WRAPPER_SCRIPT" "$INSTALL_DIR/$WRAPPER_NAME"
echo "✅ Installed wrapper to $INSTALL_DIR/$WRAPPER_NAME"

# Verify installation
echo ""
echo "🧪 Testing installation..."
if git clean 2>&1 | grep -q "DISABLED for safety"; then
    echo "✅ Wrapper is working correctly!"
    echo "   'git clean' is now blocked"
else
    echo "❌ Wrapper test failed"
    echo "   Please check the installation"
    exit 1
fi

echo ""
echo "✅ Installation complete!"
echo ""
echo "To uninstall:"
echo "  sudo rm $INSTALL_DIR/$WRAPPER_NAME"
echo "  sudo mv $INSTALL_DIR/$WRAPPER_NAME.real $INSTALL_DIR/$WRAPPER_NAME"
