#!/bin/bash
#
# Code-Forge Uninstall Script
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

INSTALL_DIR="${FORGE_INSTALL_DIR:-$HOME/.forge}"
BIN_DIR="$HOME/.local/bin"

echo ""
echo "  Code-Forge Uninstaller"
echo ""

read -p "Remove Code-Forge installation? [y/N] " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

# Remove command
if [ -f "$BIN_DIR/forge" ]; then
    print_status "Removing forge command..."
    rm -f "$BIN_DIR/forge"
fi

# Remove installation directory
if [ -d "$INSTALL_DIR" ]; then
    print_status "Removing installation directory..."
    rm -rf "$INSTALL_DIR"
fi

# Remove config directory (optional)
if [ -d "$HOME/.forge" ]; then
    read -p "Remove config directory (~/.forge)? [y/N] " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$HOME/.forge"
        print_status "Removed config directory"
    fi
fi

print_success "Code-Forge has been uninstalled"
