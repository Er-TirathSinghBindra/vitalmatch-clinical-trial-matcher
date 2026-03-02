# Test Deployment Prerequisites
# This script checks if all required tools and configurations are in place

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Testing Deployment Prerequisites" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$allGood = $true

# Test 1: Check AWS CLI
Write-Host "[1/6] Checking AWS CLI..." -ForegroundColor Yellow
try {
    $awsVersion = aws --version 2>&1
    Write-Host "  [OK] AWS CLI found: $awsVersion" -ForegroundColor Green
}
catch {
    Write-Host "  [FAIL] AWS CLI not found" -ForegroundColor Red
    Write-Host "    Install from: https://aws.amazon.com/cli/" -ForegroundColor Yellow
    $allGood = $false
}

# Test 2: Check AWS Credentials
Write-Host "[2/6] Checking AWS credentials..." -ForegroundColor Yellow
try {
    $accountId = aws sts get-caller-identity --query Account --output text 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] AWS credentials configured (Account: $accountId)" -ForegroundColor Green
    }
    else {
        Write-Host "  [FAIL] AWS credentials not configured" -ForegroundColor Red
        Write-Host "    Run: aws configure" -ForegroundColor Yellow
        $allGood = $false
    }
}
catch {
    Write-Host "  [FAIL] Cannot verify AWS credentials" -ForegroundColor Red
    $allGood = $false
}

# Test 3: Check Node.js
Write-Host "[3/6] Checking Node.js..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version 2>&1
    $nodeMajor = [int]($nodeVersion -replace 'v(\d+)\..*', '$1')
    if ($nodeMajor -ge 18) {
        Write-Host "  [OK] Node.js found: $nodeVersion" -ForegroundColor Green
    }
    else {
        Write-Host "  [FAIL] Node.js version too old: $nodeVersion (need 18+)" -ForegroundColor Red
        $allGood = $false
    }
}
catch {
    Write-Host "  [FAIL] Node.js not found" -ForegroundColor Red
    Write-Host "    Install from: https://nodejs.org/" -ForegroundColor Yellow
    $allGood = $false
}

# Test 4: Check npm
Write-Host "[4/6] Checking npm..." -ForegroundColor Yellow
try {
    $npmVersion = npm --version 2>&1
    Write-Host "  [OK] npm found: $npmVersion" -ForegroundColor Green
}
catch {
    Write-Host "  [FAIL] npm not found" -ForegroundColor Red
    $allGood = $false
}

# Test 5: Check CloudFormation Stack
Write-Host "[5/6] Checking CloudFormation stack..." -ForegroundColor Yellow
try {
    $stackStatus = aws cloudformation describe-stacks `
        --stack-name vitalmatch-clinical-trial-matcher `
        --query "Stacks[0].StackStatus" `
        --output text 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        if ($stackStatus -match "COMPLETE") {
            Write-Host "  [OK] Stack found: $stackStatus" -ForegroundColor Green
        }
        else {
            Write-Host "  [WARN] Stack status: $stackStatus" -ForegroundColor Yellow
        }
    }
    else {
        Write-Host "  [FAIL] Stack not found: vitalmatch-clinical-trial-matcher" -ForegroundColor Red
        Write-Host "    Deploy infrastructure first (Tasks 1.1, 1.2, 1.3, 11.1, 11.2)" -ForegroundColor Yellow
        $allGood = $false
    }
}
catch {
    Write-Host "  [FAIL] Cannot check CloudFormation stack" -ForegroundColor Red
    $allGood = $false
}

# Test 6: Check Frontend Directory
Write-Host "[6/6] Checking frontend directory..." -ForegroundColor Yellow
if (Test-Path "frontend/package.json") {
    Write-Host "  [OK] Frontend directory found" -ForegroundColor Green
}
else {
    Write-Host "  [FAIL] Frontend directory not found" -ForegroundColor Red
    $allGood = $false
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan

if ($allGood) {
    Write-Host "[SUCCESS] All prerequisites met!" -ForegroundColor Green
    Write-Host "You can now run the deployment script:" -ForegroundColor Green
    Write-Host "  .\scripts\deploy-frontend.ps1 -Environment dev" -ForegroundColor Cyan
}
else {
    Write-Host "[ERROR] Some prerequisites are missing" -ForegroundColor Red
    Write-Host "Please fix the issues above before deploying" -ForegroundColor Yellow
}

Write-Host "========================================" -ForegroundColor Cyan
