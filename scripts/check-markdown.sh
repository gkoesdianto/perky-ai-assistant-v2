#!/bin/bash
# Script to check and fix markdown linting issues

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Markdown Linting Check${NC}"
echo "========================="

# Check if markdownlint is available
if command -v markdownlint &> /dev/null; then
    echo -e "${GREEN}✓ markdownlint found${NC}"
    
    # Check all markdown files
    echo -e "\n${YELLOW}Checking markdown files...${NC}"
    markdownlint "**/*.md" --ignore node_modules
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ All markdown files pass linting${NC}"
    else
        echo -e "\n${YELLOW}To auto-fix issues, run:${NC}"
        echo "markdownlint '**/*.md' --fix --ignore node_modules"
    fi
else
    echo -e "${RED}✗ markdownlint not found${NC}"
    echo -e "\n${YELLOW}To install markdownlint:${NC}"
    echo "npm install -g markdownlint-cli"
    echo -e "\n${YELLOW}Or install locally:${NC}"
    echo "npm install --save-dev markdownlint-cli"
    echo "npx markdownlint '**/*.md' --ignore node_modules"
fi