#!/bin/bash

# Test Deployment Prerequisites
# This script checks if all required tools and configurations are in place

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}Testing Deployment Prerequisites${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

all_good=true

# Test 1: Check AWS CLI
echo -e "${YELLOW}[1/6] Checking AWS CLI...${NC}"
if command -v aws &> /dev/null; then
    aws_version=$(aws --version 2>&1)
    echo -e "${GREEN}  ✓ AWS CLI found: $aws_version${NC}"
else
    echo -e "${RED}  ✗ AWS CLI not found${NC}"
    echo -e "${YELLOW}    Install from: https://aws.amazon.com/cli/${NC}"
    all_good=false
fi

# Test 2: Check AWS Credentials
echo -e "${YELLOW}[2/6] Checking AWS credentials...${NC}"
if account_id=$(aws sts get-caller-identity --query Account --output text 2>&1); then
    echo -e "${GREEN}  ✓ AWS credentials configured (Account: $account_id)${NC}"
else
    echo -e "${RED}  ✗ AWS credentials not configured${NC}"
    echo -e "${YELLOW}    Run: aws configure${NC}"
    all_good=false
fi

# Test 3: Check Node.js
echo -e "${YELLOW}[3/6] Checking Node.js...${NC}"
if command -v node &> /dev/null; then
    node_version=$(node --version)
    node_major=$(echo $node_version | sed 's/v\([0-9]*\).*/\1/')
    if [ "$node_major" -ge 18 ]; then
        echo -e "${GREEN}  ✓ Node.js found: $node_version${NC}"
    else
        echo -e "${RED}  ✗ Node.js version too old: $node_version (need 18+)${NC}"
        all_good=false
    fi
else
    echo -e "${RED}  ✗ Node.js not found${NC}"
    echo -e "${YELLOW}    Install from: https://nodejs.org/${NC}"
    all_good=false
fi

# Test 4: Check npm
echo -e "${YELLOW}[4/6] Checking npm...${NC}"
if command -v npm &> /dev/null; then
    npm_version=$(npm --version)
    echo -e "${GREEN}  ✓ npm found: $npm_version${NC}"
else
    echo -e "${RED}  ✗ npm not found${NC}"
    all_good=false
fi

# Test 5: Check CloudFormation Stack
echo -e "${YELLOW}[5/6] Checking CloudFormation stack...${NC}"
if stack_status=$(aws cloudformation describe-stacks \
    --stack-name vitalmatch-clinical-trial-matcher \
    --query "Stacks[0].StackStatus" \
    --output text 2>&1); then
    
    if [[ $stack_status == *"COMPLETE"* ]]; then
        echo -e "${GREEN}  ✓ Stack found: $stack_status${NC}"
    else
        echo -e "${YELLOW}  ⚠ Stack status: $stack_status${NC}"
    fi
else
    echo -e "${RED}  ✗ Stack not found: vitalmatch-clinical-trial-matcher${NC}"
    echo -e "${YELLOW}    Deploy infrastructure first (Tasks 1.1, 1.2, 1.3, 11.1, 11.2)${NC}"
    all_good=false
fi

# Test 6: Check Frontend Directory
echo -e "${YELLOW}[6/6] Checking frontend directory...${NC}"
if [ -f "frontend/package.json" ]; then
    echo -e "${GREEN}  ✓ Frontend directory found${NC}"
else
    echo -e "${RED}  ✗ Frontend directory not found${NC}"
    all_good=false
fi

echo ""
echo -e "${CYAN}========================================${NC}"

if [ "$all_good" = true ]; then
    echo -e "${GREEN}✓ All prerequisites met!${NC}"
    echo -e "${GREEN}You can now run the deployment script:${NC}"
    echo -e "${CYAN}  ./scripts/deploy-frontend.sh dev${NC}"
else
    echo -e "${RED}✗ Some prerequisites are missing${NC}"
    echo -e "${YELLOW}Please fix the issues above before deploying${NC}"
fi

echo -e "${CYAN}========================================${NC}"
