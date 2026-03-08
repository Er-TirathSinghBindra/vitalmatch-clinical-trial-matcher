# Pre-Deployment Checklist

## Required Before Deployment

### 1. AWS CLI Configuration ✅ (Already Done)
You already have AWS CLI installed and configured since `sam validate` worked.

Verify your configuration:
```bash
aws sts get-caller-identity
```

This should show:
- Your AWS Account ID
- Your IAM user/role ARN
- Your user ID

### 2. AWS Credentials
Your AWS credentials should already be configured. Check:
```bash
aws configure list
```

If you need to reconfigure:
```bash
aws configure
```

You'll need:
- AWS Access Key ID
- AWS Secret Access Key
- Default region (e.g., `us-east-1`)
- Default output format (e.g., `json`)

### 3. IAM Permissions Required

Your IAM user/role needs these permissions:
- ✅ CloudFormation (create/update/delete stacks)
- ✅ VPC (create VPC, subnets, security groups)
- ✅ RDS (create database instances)
- ✅ Lambda (create functions)
- ✅ IAM (create roles and policies)
- ✅ S3 (SAM will create a deployment bucket)
- ✅ CloudWatch (create log groups, alarms)
- ✅ Secrets Manager (create secrets)
- ✅ Systems Manager (create parameters)
- ✅ KMS (create encryption keys)
- ✅ WAF (create web ACLs)
- ✅ SNS (create topics)
- ✅ EventBridge (create rules)

**Recommended Policy**: `AdministratorAccess` (for initial deployment)

Or create a custom policy with the above permissions.

### 4. Database Credentials (IMPORTANT!)

During `sam deploy --guided`, you'll be prompted for:

**DBUsername** (default: `vitalmatch_admin`)
- Can use default or choose your own
- Must be alphanumeric (no special characters except underscore)
- Cannot be a PostgreSQL reserved word

**DBPassword** (REQUIRED - no default)
- Minimum 8 characters
- Must contain:
  - Uppercase letters (A-Z)
  - Lowercase letters (a-z)
  - Numbers (0-9)
  - Special characters (recommended: !@#$%^&*)
- Example: `MySecureP@ssw0rd2024!`

**IMPORTANT**: 
- Write down your password securely
- Don't commit it to git
- The password will be stored in AWS Secrets Manager

### 5. Create Backend Directory (REQUIRED)

The template references `backend/` for Lambda code. Create placeholder files:

```bash
# Create backend directory
mkdir -p backend

# Create placeholder Lambda handlers
cat > backend/match_trials.py << 'EOF'
import json

def lambda_handler(event, context):
    """
    Match trials Lambda handler
    TODO: Implement trial matching logic
    """
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Match trials function - not yet implemented'
        })
    }
EOF

cat > backend/ingest_trials.py << 'EOF'
import json

def lambda_handler(event, context):
    """
    Data ingestion Lambda handler
    TODO: Implement data ingestion logic
    """
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Data ingestion function - not yet implemented'
        })
    }
EOF

# Create requirements.txt for Lambda dependencies
cat > backend/requirements.txt << 'EOF'
boto3>=1.28.0
psycopg2-binary>=2.9.0
requests>=2.31.0
EOF
```

### 6. Choose AWS Region

Decide which region to deploy to:
- **us-east-1** (N. Virginia) - Most services, lowest cost
- **us-west-2** (Oregon) - Good alternative
- **eu-west-1** (Ireland) - For European users
- **ap-southeast-1** (Singapore) - For Asian users

**Note**: Some services (like CloudFront WAF) require `us-east-1`

### 7. Choose Environment Name

During deployment, you'll choose:
- `dev` - Development environment
- `staging` - Staging environment
- `prod` - Production environment

**Recommendation**: Start with `dev`

---

## Deployment Command

Once everything above is ready:

```bash
sam deploy --guided
```

You'll be prompted for:

1. **Stack Name**: `vitalmatch-dev` (or your choice)
2. **AWS Region**: `us-east-1` (or your choice)
3. **Parameter Environment**: `dev`
4. **Parameter DBUsername**: `vitalmatch_admin` (or your choice)
5. **Parameter DBPassword**: `[your secure password]`
6. **Confirm changes before deploy**: `Y`
7. **Allow SAM CLI IAM role creation**: `Y`
8. **Disable rollback**: `N` (recommended)
9. **MatchTrialsFunction has no authentication**: `Y`
10. **DataIngestionFunction has no authentication**: `Y`
11. **Save arguments to configuration file**: `Y`
12. **SAM configuration file**: `samconfig.toml`
13. **SAM configuration environment**: `default`

---

## Quick Pre-Deployment Script

Run this to check everything:

```bash
#!/bin/bash

echo "=== Pre-Deployment Checklist ==="
echo ""

# Check AWS CLI
echo "1. Checking AWS CLI..."
if command -v aws &> /dev/null; then
    echo "   ✅ AWS CLI installed"
    aws --version
else
    echo "   ❌ AWS CLI not found"
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
    exit 1
fi

# Check AWS credentials
echo ""
echo "3. Checking AWS credentials..."
if aws sts get-caller-identity &> /dev/null; then
    echo "   ✅ AWS credentials configured"
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
    if [ -f "backend/match_trials.py" ] && [ -f "backend/ingest_trials.py" ]; then
        echo "   ✅ Lambda handlers exist"
    else
        echo "   ⚠️  Lambda handlers missing"
        echo "   Create backend/match_trials.py and backend/ingest_trials.py"
    fi
else
    echo "   ❌ backend/ directory not found"
    echo "   Run: mkdir backend"
    exit 1
fi

# Validate template
echo ""
echo "5. Validating SAM template..."
if sam validate --lint &> /dev/null; then
    echo "   ✅ Template is valid"
else
    echo "   ❌ Template validation failed"
    sam validate --lint
    exit 1
fi

echo ""
echo "=== All checks passed! ==="
echo ""
echo "Ready to deploy with: sam deploy --guided"
echo ""
echo "⚠️  IMPORTANT: Have your database password ready!"
echo "   - Minimum 8 characters"
echo "   - Mix of uppercase, lowercase, numbers, special chars"
echo "   - Example: MySecureP@ssw0rd2024!"
```

Save this as `pre-deploy-check.sh` and run:
```bash
chmod +x pre-deploy-check.sh
./pre-deploy-check.sh
```

---

## After Deployment

Once deployment completes:

1. **Note the Outputs**:
   - VPC ID
   - RDS Endpoint
   - RDS Proxy Endpoint
   - API Gateway URL
   - CloudFront URL

2. **Subscribe to SNS Topics**:
   ```bash
   aws sns subscribe \
     --topic-arn <WAF_ALERT_TOPIC_ARN> \
     --protocol email \
     --notification-endpoint your-email@example.com
   ```

3. **Test Database Connection**:
   - Use the RDS endpoint from outputs
   - Connect with your database credentials
   - Verify IAM authentication works

4. **Test Lambda Functions**:
   - Invoke Match Trials Lambda
   - Check CloudWatch Logs
   - Verify no errors

---

## Troubleshooting

### Issue: "Unable to locate credentials"
**Solution**: Run `aws configure` and enter your credentials

### Issue: "Access Denied" during deployment
**Solution**: Check IAM permissions, ensure you have CloudFormation access

### Issue: "Stack already exists"
**Solution**: Choose a different stack name or delete the existing stack

### Issue: "Invalid parameter: DBPassword"
**Solution**: Ensure password meets requirements (8+ chars, mixed case, numbers, special chars)

### Issue: "Backend directory not found"
**Solution**: Create `backend/` directory with Lambda handler files

---

## Security Reminders

1. ✅ Never commit AWS credentials to git
2. ✅ Never commit database passwords to git
3. ✅ Use strong passwords (16+ characters recommended)
4. ✅ Enable MFA on your AWS account
5. ✅ Review IAM permissions regularly
6. ✅ Monitor CloudWatch for suspicious activity

---

## Ready to Deploy?

If all checks pass, run:

```bash
sam deploy --guided
```

Deployment will take approximately **15-20 minutes** due to RDS instance creation.

Good luck! 🚀
