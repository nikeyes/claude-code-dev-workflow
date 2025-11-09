#!/usr/bin/env bash
set -euo pipefail

# install.sh - Install Claude Code workflow components globally
# Installs commands, agents, and thoughts scripts

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

# Target directories
CLAUDE_DIR="$HOME/.claude"
COMMANDS_DIR="$CLAUDE_DIR/commands"
AGENTS_DIR="$CLAUDE_DIR/agents"
BIN_DIR="$HOME/.local/bin"
BACKUP_DIR="$HOME/.claude-workflow-backup-$(date +%Y%m%d-%H%M%S)"

# Source directories
SRC_COMMANDS="$SCRIPT_DIR/.claude/commands"
SRC_AGENTS="$SCRIPT_DIR/.claude/agents"
SRC_BIN="$SCRIPT_DIR/bin"

# Display banner
header "Claude Code Workflow Installer"
echo "This will install:"
echo "  • 6 slash commands to $COMMANDS_DIR"
echo "  • 5 specialized agents to $AGENTS_DIR"
echo "  • 3 thoughts scripts to $BIN_DIR"
echo ""

# Confirmation
read -p "Continue with installation? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  info "Installation cancelled"
  exit 0
fi

# Create backup directory if needed
create_backup=false
if [ -d "$COMMANDS_DIR" ] || [ -d "$AGENTS_DIR" ] || \
   [ -f "$BIN_DIR/thoughts-init" ] || [ -f "$BIN_DIR/thoughts-sync" ] || [ -f "$BIN_DIR/thoughts-metadata" ]; then
  create_backup=true
  info "Existing files detected. Creating backup at: $BACKUP_DIR"
  mkdir -p "$BACKUP_DIR"
fi

# Backup function
backup_file() {
  local src="$1"
  local rel_path="${src#$HOME/}"
  local backup_path="$BACKUP_DIR/$rel_path"

  if [ -f "$src" ] || [ -d "$src" ]; then
    mkdir -p "$(dirname "$backup_path")"
    cp -r "$src" "$backup_path"
  fi
}

# Install commands
header "Installing Commands"
mkdir -p "$COMMANDS_DIR"

for cmd in "$SRC_COMMANDS"/*.md; do
  cmd_name=$(basename "$cmd")
  target="$COMMANDS_DIR/$cmd_name"

  # Backup existing
  if [ -f "$target" ] && [ "$create_backup" = true ]; then
    backup_file "$target"
  fi

  # Install
  cp "$cmd" "$target"
  success "Installed: $cmd_name"
done

# Install agents
header "Installing Agents"
mkdir -p "$AGENTS_DIR"

for agent in "$SRC_AGENTS"/*.md; do
  agent_name=$(basename "$agent")
  target="$AGENTS_DIR/$agent_name"

  # Backup existing
  if [ -f "$target" ] && [ "$create_backup" = true ]; then
    backup_file "$target"
  fi

  # Install
  cp "$agent" "$target"
  success "Installed: $agent_name"
done

# Install scripts
header "Installing Thoughts Scripts"
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
else
  success "$BIN_DIR is in your PATH"
fi

# Summary
header "Installation Complete!"
echo ""
echo "Installed Components:"
echo "  • 6 commands in: $COMMANDS_DIR"
echo "  • 5 agents in: $AGENTS_DIR"
echo "  • 3 scripts in: $BIN_DIR"
echo ""

if [ "$create_backup" = true ]; then
  echo "Backup created at: $BACKUP_DIR"
  echo ""
fi

echo "Commands installed:"
echo "  /research_codebase - Research and document codebase"
echo "  /create_plan       - Create implementation plans"
echo "  /iterate_plan      - Update existing plans"
echo "  /implement_plan    - Execute plans phase by phase"
echo "  /validate_plan     - Validate implementation"
echo "  /commit            - Create git commits"
echo ""

echo "Scripts installed:"
echo "  thoughts-init      - Initialize thoughts/ in a project"
echo "  thoughts-sync      - Sync hardlinks in searchable/"
echo "  thoughts-metadata  - Generate git metadata"
echo ""

header "Next Steps"
echo "1. Navigate to your project directory:"
echo "   cd /path/to/your/project"
echo ""
echo "2. Initialize thoughts/ structure:"
echo "   thoughts-init"
echo ""
echo "3. Start using Claude Code commands:"
echo "   /research_codebase [topic]"
echo "   /create_plan [description]"
echo ""
echo "4. Read the README for detailed usage:"
echo "   cat $SCRIPT_DIR/README.md"
echo ""

success "Setup complete! Happy coding with Claude 🚀"
