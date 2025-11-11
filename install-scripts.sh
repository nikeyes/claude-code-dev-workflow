#!/usr/bin/env bash
set -euo pipefail

# install-scripts.sh - Install thoughts/ helper scripts only
# Use this after installing the plugin to add PATH scripts

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

info() {
  echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
  echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
  echo -e "${RED}[ERROR]${NC} $1"
  exit 1
}

success() {
  echo -e "${GREEN}✓${NC} $1"
}

header() {
  echo -e "\n${BOLD}${BLUE}===${NC} ${BOLD}$1${NC} ${BOLD}${BLUE}===${NC}\n"
}

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Target directory
BIN_DIR="$HOME/.local/bin"
BACKUP_DIR="$HOME/.local/bin/backup-$(date +%Y%m%d-%H%M%S)"

# Source directory
SRC_BIN="$SCRIPT_DIR/bin"

# Display banner
header "Thoughts Scripts Installer"
echo "This will install 3 helper scripts to $BIN_DIR:"
echo "  • thoughts-init      - Initialize thoughts/ structure"
echo "  • thoughts-sync      - Sync searchable/ hardlinks"
echo "  • thoughts-metadata  - Generate git metadata"
echo ""

# Confirmation
read -p "Continue with installation? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  info "Installation cancelled"
  exit 0
fi

# Create backup if scripts exist
create_backup=false
if [ -f "$BIN_DIR/thoughts-init" ] || [ -f "$BIN_DIR/thoughts-sync" ] || \
   [ -f "$BIN_DIR/thoughts-metadata" ]; then
  create_backup=true
  info "Existing scripts detected. Creating backup at: $BACKUP_DIR"
  mkdir -p "$BACKUP_DIR"
fi

# Backup function
backup_file() {
  local src="$1"
  local filename
  filename=$(basename "$src")
  local backup_path="$BACKUP_DIR/$filename"

  if [ -f "$src" ]; then
    cp "$src" "$backup_path"
  fi
}

# Install scripts
header "Installing Scripts"
mkdir -p "$BIN_DIR"

for script in "$SRC_BIN"/*; do
  script_name=$(basename "$script")
  target="$BIN_DIR/$script_name"

  # Backup existing
  if [ -f "$target" ] && [ "$create_backup" = true ]; then
    backup_file "$target"
  fi

  # Install and make executable
  cp "$script" "$target"
  chmod +x "$target"
  success "Installed: $script_name"
done

# Check if ~/.local/bin is in PATH
header "Checking PATH"
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
  warn "$BIN_DIR is not in your PATH"
  echo ""
  echo "Add this line to your shell configuration (~/.bashrc, ~/.zshrc, etc.):"
  echo ""
  echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
  echo ""
  echo "Then reload your shell configuration:"
  echo "  source ~/.bashrc  # or ~/.zshrc"
  echo ""
else
  success "$BIN_DIR is in your PATH"
fi

# Summary
header "Installation Complete!"
echo ""
echo "Scripts installed to: $BIN_DIR"
echo "  • thoughts-init"
echo "  • thoughts-sync"
echo "  • thoughts-metadata"
echo ""

if [ "$create_backup" = true ]; then
  echo "Backup created at: $BACKUP_DIR"
  echo ""
fi

header "Next Steps"
echo "1. Ensure $BIN_DIR is in your PATH (see above)"
echo ""
echo "2. Navigate to your project directory:"
echo "   cd /path/to/your/project"
echo ""
echo "3. Initialize thoughts/ structure:"
echo "   thoughts-init"
echo ""
echo "4. Start using Claude Code commands:"
echo "   /research_codebase [topic]"
echo "   /create_plan [description]"
echo ""

success "Scripts installation complete! 🚀"
