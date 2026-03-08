#!/bin/bash

echo "=== VitalMatch Pre-Deployment Checklist ==="
echo ""

# Check AWS CLI
echo "1. Checking AWS CLI..."
if command -v aws &> /dev/null; then
    echo "   ✅ AWS CLI installed"
    aws --version
else
    echo "   ❌ AWS CLI not found"
    echo "   Install from: https://aws.amazon.com/cli/"
    exit 1
fi

# Check SAM CLI
echo ""
echo "2. Checking SAM CLI..."
if command -v sam &> /dev/null; then
    echo "   ✅ SAM CLI installed"
    sam --version
else
    echo "   ❌ SAM CLI not found"
    echo "   Install from: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html"
    exit 1
fi

# Check AWS credentials
echo ""
echo "3. Checking AWS credentials..."
if aws sts get-caller-identity &> /dev/null; then
    echo "   ✅ AWS credentials configured"
    echo ""
    aws sts get-caller-identity
else
    echo "   ❌ AWS credentials not configured"
    echo "   Run: aws configure"
    exit 1
fi

# Check backend directory
echo ""
echo "4. Checking backend directory..."
if [ -d "backend" ]; then
    echo "   ✅ backend/ directory exists"
    
    # Check Lambda handlers
    if [ -f "backend/match_trials.py" ]; then
        echo "   ✅ backend/match_trials.py exists"
    else
        echo "   ❌ backend/match_trials.py missing"
        MISSING_FILES=true
    fi
    
    if [ -f "backend/ingest_trials.py" ]; then
        echo "   ✅ backend/ingest_trials.py exists"
    else
        echo "   ❌ backend/ingest_trials.py missing"
        MISSING_FILES=true
    fi
    
    if [ -f "backend/requirements.txt" ]; then
        echo "   ✅ backend/requirements.txt exists"
    else
        echo "   ⚠️  backend/requirements.txt missing (optional)"
    fi
    
    if [ "$MISSING_FILES" = true ]; then
        echo ""
        echo "   Run the following to create missing files:"
        echo ""
        echo "   cat > backend/match_trials.py << 'EOF'"
        echo "import json"
        echo ""
        echo "def lambda_handler(event, context):"
        echo "    return {"
        echo "        'statusCode': 200,"
        echo "        'body': json.dumps({'message': 'Match trials - not yet implemented'})"
        echo "    }"
        echo "EOF"
        echo ""
        echo "   cat > backend/ingest_trials.py << 'EOF'"
        echo "import json"
        echo ""
        echo "def lambda_handler(event, context):"
        echo "    return {"
        echo "        'statusCode': 200,"
        echo "        'body': json.dumps({'message': 'Data ingestion - not yet implemented'})"
        echo "    }"
        echo "EOF"
        exit 1
    fi
else
    echo "   ❌ backend/ directory not found"
    echo ""
    echo "   Run: mkdir backend"
    echo "   Then create Lambda handler files (see PRE_DEPLOYMENT_CHECKLIST.md)"
    exit 1
fi

# Check template.yaml
echo ""
echo "5. Checking template.yaml..."
if [ -f "template.yaml" ]; then
    echo "   ✅ template.yaml exists"
else
    echo "   ❌ template.yaml not found"
    exit 1
fi

# Validate template
echo ""
echo "6. Validating SAM template..."
if sam validate --lint > /dev/null 2>&1; then
    echo "   ✅ Template is valid"
else
    echo "   ❌ Template validation failed"
    echo ""
    sam validate --lint
    exit 1
fi

# Check for .gitignore
echo ""
echo "7. Checking .gitignore..."
if [ -f ".gitignore" ]; then
    echo "   ✅ .gitignore exists"
    
    # Check if important patterns are ignored
    if grep -q "samconfig.toml" .gitignore 2>/dev/null; then
        echo "   ✅ samconfig.toml is ignored"
    else
        echo "   ⚠️  Consider adding samconfig.toml to .gitignore"
    fi
    
    if grep -q ".aws-sam" .gitignore 2>/dev/null; then
        echo "   ✅ .aws-sam/ is ignored"
    else
        echo "   ⚠️  Consider adding .aws-sam/ to .gitignore"
    fi
else
    echo "   ⚠️  .gitignore not found (recommended)"
fi

# Summary
echo ""
echo "=== All checks passed! ==="
echo ""
echo "✅ Ready to deploy with: sam deploy --guided"
echo ""
echo "📋 Deployment Prompts You'll See:"
echo "   1. Stack Name: vitalmatch-dev (or your choice)"
echo "   2. AWS Region: us-east-1 (or your choice)"
echo "   3. Parameter Environment: dev"
echo "   4. Parameter DBUsername: vitalmatch_admin (default is fine)"
echo "   5. Parameter DBPassword: [CREATE A STRONG PASSWORD]"
echo ""
echo "🔑 Database Password Requirements:"
echo "   - Minimum 8 characters"
echo "   - Mix of uppercase, lowercase, numbers, special chars"
echo "   - Example: MySecureP@ssw0rd2024!"
echo ""
echo "⏱️  Deployment Time: ~15-20 minutes (RDS takes time to create)"
echo ""
echo "💰 Estimated Monthly Cost (Dev): $13-21/month"
echo ""
