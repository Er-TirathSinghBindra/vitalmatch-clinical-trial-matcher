# VitalMatch Pre-Deployment Checklist (PowerShell)

Write-Host "=== VitalMatch Pre-Deployment Checklist ===" -ForegroundColor Cyan
Write-Host ""

$allChecksPassed = $true

# Check AWS CLI
Write-Host "1. Checking AWS CLI..." -ForegroundColor Yellow
try {
    # Try direct command first
    $awsVersion = aws --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ AWS CLI installed" -ForegroundColor Green
        Write-Host "   $awsVersion" -ForegroundColor Gray
    } else {
        throw "AWS CLI not found"
    }
} catch {
    # Try python -m awscli (for pip installations)
    try {
        $awsVersion = python -m awscli --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✅ AWS CLI installed (via pip)" -ForegroundColor Green
            Write-Host "   $awsVersion" -ForegroundColor Gray
            # Set alias for rest of script
            Set-Alias -Name aws -Value "python -m awscli" -Scope Script
        } else {
            throw "AWS CLI not found"
        }
    } catch {
        Write-Host "   ❌ AWS CLI not found" -ForegroundColor Red
        Write-Host "   Install from: https://aws.amazon.com/cli/ or pip install awscli" -ForegroundColor Yellow
        $allChecksPassed = $false
    }
}

# Check SAM CLI
Write-Host ""
Write-Host "2. Checking SAM CLI..." -ForegroundColor Yellow
try {
    $samVersion = sam --version 2>&1
    Write-Host "   ✅ SAM CLI installed" -ForegroundColor Green
    Write-Host "   $samVersion" -ForegroundColor Gray
} catch {
    Write-Host "   ❌ SAM CLI not found" -ForegroundColor Red
    Write-Host "   Install from: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html" -ForegroundColor Yellow
    $allChecksPassed = $false
}

# Check AWS credentials
Write-Host ""
Write-Host "3. Checking AWS credentials..." -ForegroundColor Yellow
try {
    # Try direct aws command first
    $identityJson = aws sts get-caller-identity 2>&1
    if ($LASTEXITCODE -ne 0) {
        # Try python -m awscli for pip installations
        $identityJson = python -m awscli sts get-caller-identity 2>&1
    }
    
    if ($LASTEXITCODE -eq 0) {
        $identity = $identityJson | ConvertFrom-Json
        Write-Host "   ✅ AWS credentials configured" -ForegroundColor Green
        Write-Host ""
        Write-Host "   Account: $($identity.Account)" -ForegroundColor Gray
        Write-Host "   User: $($identity.Arn)" -ForegroundColor Gray
    } else {
        throw "Credentials not configured"
    }
} catch {
    Write-Host "   ❌ AWS credentials not configured" -ForegroundColor Red
    Write-Host "   Run: aws configure (or python -m awscli configure)" -ForegroundColor Yellow
    $allChecksPassed = $false
}

# Check backend directory
Write-Host ""
Write-Host "4. Checking backend directory..." -ForegroundColor Yellow
if (Test-Path "backend") {
    Write-Host "   ✅ backend/ directory exists" -ForegroundColor Green
    
    # Check Lambda handlers
    $missingFiles = $false
    
    if (Test-Path "backend/match_trials.py") {
        Write-Host "   ✅ backend/match_trials.py exists" -ForegroundColor Green
    } else {
        Write-Host "   ❌ backend/match_trials.py missing" -ForegroundColor Red
        $missingFiles = $true
    }
    
    if (Test-Path "backend/ingest_trials.py") {
        Write-Host "   ✅ backend/ingest_trials.py exists" -ForegroundColor Green
    } else {
        Write-Host "   ❌ backend/ingest_trials.py missing" -ForegroundColor Red
        $missingFiles = $true
    }
    
    if (Test-Path "backend/requirements.txt") {
        Write-Host "   ✅ backend/requirements.txt exists" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  backend/requirements.txt missing (optional)" -ForegroundColor Yellow
    }
    
    if ($missingFiles) {
        Write-Host ""
        Write-Host "   Create missing files with:" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "   New-Item -Path backend/match_trials.py -ItemType File -Force" -ForegroundColor Gray
        Write-Host "   New-Item -Path backend/ingest_trials.py -ItemType File -Force" -ForegroundColor Gray
        Write-Host ""
        Write-Host "   See PRE_DEPLOYMENT_CHECKLIST.md for file contents" -ForegroundColor Gray
        $allChecksPassed = $false
    }
} else {
    Write-Host "   ❌ backend/ directory not found" -ForegroundColor Red
    Write-Host ""
    Write-Host "   Run: mkdir backend" -ForegroundColor Yellow
    Write-Host "   Then create Lambda handler files (see PRE_DEPLOYMENT_CHECKLIST.md)" -ForegroundColor Yellow
    $allChecksPassed = $false
}

# Check template.yaml
Write-Host ""
Write-Host "5. Checking template.yaml..." -ForegroundColor Yellow
if (Test-Path "template.yaml") {
    Write-Host "   ✅ template.yaml exists" -ForegroundColor Green
} else {
    Write-Host "   ❌ template.yaml not found" -ForegroundColor Red
    $allChecksPassed = $false
}

# Validate template
Write-Host ""
Write-Host "6. Validating SAM template..." -ForegroundColor Yellow
try {
    $validation = sam validate --lint 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Template is valid" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Template validation failed" -ForegroundColor Red
        Write-Host ""
        Write-Host $validation -ForegroundColor Red
        $allChecksPassed = $false
    }
} catch {
    Write-Host "   ❌ Template validation failed" -ForegroundColor Red
    $allChecksPassed = $false
}

# Check for .gitignore
Write-Host ""
Write-Host "7. Checking .gitignore..." -ForegroundColor Yellow
if (Test-Path ".gitignore") {
    Write-Host "   ✅ .gitignore exists" -ForegroundColor Green
    
    $gitignoreContent = Get-Content .gitignore -Raw
    
    if ($gitignoreContent -match "samconfig.toml") {
        Write-Host "   ✅ samconfig.toml is ignored" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Consider adding samconfig.toml to .gitignore" -ForegroundColor Yellow
    }
    
    if ($gitignoreContent -match ".aws-sam") {
        Write-Host "   ✅ .aws-sam/ is ignored" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Consider adding .aws-sam/ to .gitignore" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ⚠️  .gitignore not found (recommended)" -ForegroundColor Yellow
}

# Summary
Write-Host ""
if ($allChecksPassed) {
    Write-Host "=== All checks passed! ===" -ForegroundColor Green
    Write-Host ""
    Write-Host "Ready to deploy with: sam deploy --guided" -ForegroundColor Green
    Write-Host ""
    Write-Host "Deployment Prompts You'll See:" -ForegroundColor Cyan
    Write-Host "   1. Stack Name: vitalmatch-dev (or your choice)"
    Write-Host "   2. AWS Region: us-east-1 (or your choice)"
    Write-Host "   3. Parameter Environment: dev"
    Write-Host "   4. Parameter DBUsername: vitalmatch_admin (default is fine)"
    Write-Host "   5. Parameter DBPassword: [CREATE A STRONG PASSWORD]"
    Write-Host ""
    Write-Host "Database Password Requirements:" -ForegroundColor Cyan
    Write-Host "   - Minimum 8 characters"
    Write-Host "   - Mix of uppercase, lowercase, numbers, special chars"
    Write-Host "   - Example: MySecureP@ssw0rd2024!"
    Write-Host ""
    Write-Host "Deployment Time: ~15-20 minutes (RDS takes time to create)" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Estimated Monthly Cost (Dev): `$13-21/month" -ForegroundColor Yellow
    Write-Host ""
} else {
    Write-Host "=== Some checks failed ===" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please fix the issues above before deploying." -ForegroundColor Yellow
    Write-Host ""
    exit 1
}
