#!/bin/bash
#
# Code-Forge Update Script
# Updates Code-Forge to the latest version from GitHub
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${BLUE}==>${NC} $1"; }
print_success() { echo -e "${GREEN}==>${NC} $1"; }
print_warning() { echo -e "${YELLOW}==>${NC} $1"; }
print_error() { echo -e "${RED}==>${NC} $1"; }

# Determine script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
INSTALL_DIR="${FORGE_INSTALL_DIR:-$HOME/.forge}"
VENV_DIR="$INSTALL_DIR/venv"

echo ""
echo "  Code-Forge Updater"
echo ""

# Check if we're in a git repo
if [ ! -d "$SCRIPT_DIR/.git" ]; then
    print_error "Not a git repository. Cannot update."
    print_warning "Clone from: git@github.com:corey-rosamond/Code-Forge.git"
    exit 1
fi

cd "$SCRIPT_DIR"

# Get current version
CURRENT_VERSION=$(git describe --tags 2>/dev/null || git rev-parse --short HEAD)
print_status "Current version: $CURRENT_VERSION"

# Fetch updates
print_status "Checking for updates..."
git fetch origin main --tags 2>/dev/null || git fetch origin master --tags 2>/dev/null || {
    print_error "Failed to fetch updates. Check your network connection."
    exit 1
}

# Check if updates available
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main 2>/dev/null || git rev-parse origin/master 2>/dev/null)

if [ "$LOCAL" = "$REMOTE" ]; then
    print_success "Already up to date!"
    exit 0
fi

# Show what's new
echo ""
print_status "Changes since $CURRENT_VERSION:"
git log --oneline HEAD..origin/main 2>/dev/null || git log --oneline HEAD..origin/master 2>/dev/null | head -10
echo ""

read -p "Update to latest version? [Y/n] " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]] && [[ -n $REPLY ]]; then
    echo "Update cancelled."
    exit 0
fi

# Pull updates
print_status "Pulling latest changes..."
git pull origin main 2>/dev/null || git pull origin master 2>/dev/null

# Reinstall if venv exists
if [ -d "$VENV_DIR" ]; then
    print_status "Updating installed package..."
    source "$VENV_DIR/bin/activate"
    pip install -e "$SCRIPT_DIR" -q
    deactivate
fi

# Get new version
NEW_VERSION=$(git describe --tags 2>/dev/null || git rev-parse --short HEAD)

print_success "Updated from $CURRENT_VERSION to $NEW_VERSION"
echo ""
