#!/bin/bash
#
# Code-Forge Installation Script
# Installs Code-Forge and adds 'forge' command to your PATH
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() { echo -e "${BLUE}==>${NC} $1"; }
print_success() { echo -e "${GREEN}==>${NC} $1"; }
print_warning() { echo -e "${YELLOW}==>${NC} $1"; }
print_error() { echo -e "${RED}==>${NC} $1"; }

# Determine script directory (where Code-Forge is located)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
INSTALL_DIR="${FORGE_INSTALL_DIR:-$HOME/.forge}"
VENV_DIR="$INSTALL_DIR/venv"
BIN_DIR="$HOME/.local/bin"

echo ""
echo "  ╔═══════════════════════════════════════╗"
echo "  ║        Code-Forge Installer           ║"
echo "  ╚═══════════════════════════════════════╝"
echo ""

# Check Python version
print_status "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not installed."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
    print_error "Python 3.11+ is required. Found: Python $PYTHON_VERSION"
    exit 1
fi
print_success "Found Python $PYTHON_VERSION"

# Create installation directory
print_status "Creating installation directory at $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"

# Create virtual environment
print_status "Creating virtual environment..."
if [ -d "$VENV_DIR" ]; then
    print_warning "Virtual environment already exists, recreating..."
    rm -rf "$VENV_DIR"
fi
python3 -m venv "$VENV_DIR"

# Activate and install
print_status "Installing Code-Forge..."
source "$VENV_DIR/bin/activate"
pip install --upgrade pip -q
pip install -e "$SCRIPT_DIR" -q

# Save source directory for updates
echo "$SCRIPT_DIR" > "$INSTALL_DIR/.source_dir"

# Create wrapper script with update support
print_status "Creating 'forge' command..."
cat > "$BIN_DIR/forge" << 'WRAPPER_EOF'
#!/bin/bash
# Code-Forge CLI wrapper

INSTALL_DIR="${FORGE_INSTALL_DIR:-$HOME/.forge}"
VENV_DIR="$INSTALL_DIR/venv"
SOURCE_DIR_FILE="$INSTALL_DIR/.source_dir"

# Handle 'forge update' command
if [ "$1" = "update" ]; then
    if [ -f "$SOURCE_DIR_FILE" ]; then
        SOURCE_DIR=$(cat "$SOURCE_DIR_FILE")
        if [ -f "$SOURCE_DIR/update.sh" ]; then
            exec "$SOURCE_DIR/update.sh"
        else
            echo "Error: update.sh not found in $SOURCE_DIR"
            exit 1
        fi
    else
        echo "Error: Source directory not recorded. Reinstall Code-Forge."
        exit 1
    fi
fi

# Handle 'forge check-update' command
if [ "$1" = "check-update" ]; then
    if [ -f "$SOURCE_DIR_FILE" ]; then
        SOURCE_DIR=$(cat "$SOURCE_DIR_FILE")
        cd "$SOURCE_DIR"
        git fetch origin main --tags 2>/dev/null || git fetch origin master --tags 2>/dev/null
        LOCAL=$(git rev-parse HEAD)
        REMOTE=$(git rev-parse origin/main 2>/dev/null || git rev-parse origin/master 2>/dev/null)
        if [ "$LOCAL" != "$REMOTE" ]; then
            echo "Update available! Run 'forge update' to update."
            exit 0
        else
            echo "Code-Forge is up to date."
            exit 0
        fi
    fi
    exit 0
fi

# Normal execution
source "$VENV_DIR/bin/activate"
exec python -m code_forge "$@"
WRAPPER_EOF
chmod +x "$BIN_DIR/forge"

# Check if ~/.local/bin is in PATH
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    print_warning "$BIN_DIR is not in your PATH"

    # Detect shell and config file
    SHELL_NAME=$(basename "$SHELL")
    case "$SHELL_NAME" in
        bash)
            SHELL_RC="$HOME/.bashrc"
            ;;
        zsh)
            SHELL_RC="$HOME/.zshrc"
            ;;
        fish)
            SHELL_RC="$HOME/.config/fish/config.fish"
            ;;
        *)
            SHELL_RC="$HOME/.profile"
            ;;
    esac

    echo ""
    read -p "Add $BIN_DIR to PATH in $SHELL_RC? [Y/n] " -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
        if [ "$SHELL_NAME" = "fish" ]; then
            echo "set -gx PATH \$HOME/.local/bin \$PATH" >> "$SHELL_RC"
        else
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_RC"
        fi
        print_success "Added to $SHELL_RC"
        print_warning "Run 'source $SHELL_RC' or restart your terminal"
    else
        print_warning "Please add the following to your shell config:"
        echo '  export PATH="$HOME/.local/bin:$PATH"'
    fi
fi

# Verify installation
print_status "Verifying installation..."
if "$BIN_DIR/forge" --version &> /dev/null; then
    VERSION=$("$BIN_DIR/forge" --version 2>&1)
    print_success "Installation complete!"
    echo ""
    echo "  $VERSION"
    echo ""
    echo "  Run 'forge' to start Code-Forge"
    echo "  Run 'forge --help' for usage information"
    echo ""
else
    print_error "Installation verification failed"
    exit 1
fi
