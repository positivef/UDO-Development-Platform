# Git Safety Wrapper Installation Script (PowerShell)
# Created: 2025-12-23
# Purpose: Install git safety wrapper for Windows PowerShell
# Usage: Run in PowerShell as Administrator

Write-Host "🔧 Git Safety Wrapper Installation (Windows)" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "❌ This script requires Administrator privileges" -ForegroundColor Red
    Write-Host "   Please run PowerShell as Administrator" -ForegroundColor Yellow
    exit 1
}

# Get PowerShell profile path
$profilePath = $PROFILE.CurrentUserAllHosts

Write-Host "📝 PowerShell Profile: $profilePath" -ForegroundColor Green
Write-Host ""

# Create profile if it doesn't exist
if (-not (Test-Path $profilePath)) {
    New-Item -Path $profilePath -ItemType File -Force | Out-Null
    Write-Host "✅ Created PowerShell profile" -ForegroundColor Green
}

# Read existing profile
$profileContent = Get-Content $profilePath -Raw -ErrorAction SilentlyContinue

# Check if git wrapper already exists
if ($profileContent -match "function git") {
    Write-Host "⚠️  Git function already exists in profile" -ForegroundColor Yellow
    Write-Host "   Please manually edit: $profilePath" -ForegroundColor Yellow
    Write-Host ""
    exit 0
}

# Add git wrapper function
$gitWrapper = @'

# Git Safety Wrapper - Block dangerous commands
# Added by: scripts/install_git_wrapper.ps1
# Date: 2025-12-23

function git {
    param(
        [Parameter(Position=0)]
        [string]$Command,
        [Parameter(ValueFromRemainingArguments=$true)]
        [string[]]$Args
    )

    # Block 'git clean'
    if ($Command -eq "clean") {
        Write-Host ""
        Write-Host "🚫 ==========================================" -ForegroundColor Red
        Write-Host "⚠️  git clean is DISABLED for safety!" -ForegroundColor Red
        Write-Host "==========================================" -ForegroundColor Red
        Write-Host ""
        Write-Host "Reason: " -NoNewline -ForegroundColor Yellow
        Write-Host "git clean -fd permanently deletes files (no recovery)"
        Write-Host ""
        Write-Host "Safe alternatives:" -ForegroundColor Green
        Write-Host "  - Remove specific file: " -NoNewline
        Write-Host "rm <filename>" -ForegroundColor Green
        Write-Host "  - Preview what would be deleted: " -NoNewline
        Write-Host "git clean -n -fd" -ForegroundColor Green
        Write-Host "  - Temporarily save: " -NoNewline
        Write-Host "git stash -u" -ForegroundColor Green
        Write-Host ""
        Write-Host "If you REALLY need git clean:" -ForegroundColor Yellow
        Write-Host "  1. Backup first: " -NoNewline
        Write-Host "python scripts/auto_backup_untracked.py --backup" -ForegroundColor Green
        Write-Host "  2. Verify backup: " -NoNewline
        Write-Host "python scripts/auto_backup_untracked.py --list" -ForegroundColor Green
        Write-Host "  3. Use real git: " -NoNewline
        Write-Host "& 'C:\Program Files\Git\cmd\git.exe' clean ..." -ForegroundColor Green
        Write-Host ""
        return
    }

    # Pass through to real git
    & "C:\Program Files\Git\cmd\git.exe" $Command @Args
}

Write-Host "[Git Safety] Wrapper loaded - git clean is blocked" -ForegroundColor Green

'@

# Append to profile
Add-Content -Path $profilePath -Value $gitWrapper

Write-Host "✅ Git wrapper function added to PowerShell profile" -ForegroundColor Green
Write-Host ""
Write-Host "🧪 Testing installation..." -ForegroundColor Cyan

# Reload profile
. $profilePath

# Test wrapper
Write-Host ""
Write-Host "To activate the wrapper:" -ForegroundColor Yellow
Write-Host "  1. Close and reopen PowerShell" -ForegroundColor Yellow
Write-Host "  OR" -ForegroundColor Yellow
Write-Host "  2. Run: . `$PROFILE" -ForegroundColor Yellow
Write-Host ""
Write-Host "To test:" -ForegroundColor Cyan
Write-Host "  git clean -fd" -ForegroundColor Cyan
Write-Host "  (Should be blocked with safety message)" -ForegroundColor Gray
Write-Host ""
Write-Host "✅ Installation complete!" -ForegroundColor Green
