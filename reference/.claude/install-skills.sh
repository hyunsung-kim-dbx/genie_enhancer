#!/bin/bash
#
# Install Genie Lamp Agent skills to Claude Code
#
# Usage: ./.claude/install-skills.sh

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}==================================================${NC}"
echo -e "${BLUE}Installing Genie Lamp Agent Skills to Claude Code${NC}"
echo -e "${BLUE}==================================================${NC}"
echo

# Get project root (where .git is)
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKILLS_DIR="${PROJECT_ROOT}/.claude/skills"
CLAUDE_SKILLS_DIR="${HOME}/.codex/skills"

echo -e "${BLUE}Project root:${NC} ${PROJECT_ROOT}"
echo -e "${BLUE}Skills source:${NC} ${SKILLS_DIR}"
echo -e "${BLUE}Install target:${NC} ${CLAUDE_SKILLS_DIR}"
echo

# Check if skills directory exists
if [ ! -d "${SKILLS_DIR}" ]; then
    echo -e "${YELLOW}Error: Skills directory not found at ${SKILLS_DIR}${NC}"
    exit 1
fi

# Create Claude skills directory if it doesn't exist
mkdir -p "${CLAUDE_SKILLS_DIR}"

# Install each skill
for skill_path in "${SKILLS_DIR}"/*; do
    if [ -d "${skill_path}" ] && [ -f "${skill_path}/SKILL.md" ]; then
        skill_name=$(basename "${skill_path}")
        target_path="${CLAUDE_SKILLS_DIR}/${skill_name}"

        echo -e "${BLUE}Installing skill:${NC} ${skill_name}"

        # Check if skill already exists
        if [ -L "${target_path}" ]; then
            echo -e "  ${YELLOW}→ Symlink already exists, removing${NC}"
            rm "${target_path}"
        elif [ -d "${target_path}" ]; then
            echo -e "  ${YELLOW}→ Directory already exists, removing${NC}"
            rm -rf "${target_path}"
        fi

        # Create symlink
        ln -s "${skill_path}" "${target_path}"
        echo -e "  ${GREEN}✓ Installed as symlink${NC}"

    fi
done

echo
echo -e "${GREEN}==================================================${NC}"
echo -e "${GREEN}✓ Installation complete!${NC}"
echo -e "${GREEN}==================================================${NC}"
echo
echo -e "${YELLOW}Next steps:${NC}"
echo -e "  1. Restart Claude Code to load the new skills"
echo -e "  2. Try using a skill by asking: ${BLUE}\"commit these changes\"${NC}"
echo
