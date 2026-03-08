# VitalMatch Deployment Guide

This comprehensive guide covers both infrastructure and frontend deployment for the VitalMatch clinical trial matching system.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Infrastructure Deployment](#infrastructure-deployment)
3. [Frontend Deployment](#frontend-deployment)
4. [Post-Deployment Configuration](#post-deployment-configuration)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Tools
- **AWS CLI** (v2.x or later)
- **AWS SAM CLI** (v1.x or later)
- **Node.js** (v18 or later)
- **npm** (v8 or later)
- **Git** (for version control)

### AWS Account Requirements
- Active AWS account with billing enabled
- IAM user or role with permissions for:
  - CloudFormation stack creation
  - VPC and networking resources
  - RDS database creation
  - S3 and CloudFront
  - IAM role creation
  - CloudWatch and WAF configuration
  - Systems Manager Parameter Store

### Install AWS CLI
```bash
# macOS
brew install awscli

# Linux
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Windows
# Download and run the MSI installer from:
# https://awscli.amazonaws.com/AWSCLIV2.msi

# Verify installation
aws --version
```

### Install AWS SAM CLI
```bash
# macOS
brew install aws-sam-cli

# Linux
wget https://github.com/aws/aws-sam-cli/releases/latest/download/aws-sam-cli-linux-x86_64.zip
unzip aws-sam-cli-linux-x86_64.zip -d sam-installation
sudo ./sam-installation/install

# Windows
# Download and run the MSI installer from:
# https://github.com/aws/aws-sam-cli/releases/latest/download/AWS_SAM_CLI_64_PY3.msi

# Verify installation
sam --version
```

### Install Node.js
```bash
# macOS
brew install node

# Linux (using nvm)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 18

# Windows
# Download from https://nodejs.org/

# Verify installation
node --version
npm --version
```

### Prerequisites Check

Run the automated prerequisites test:

**Windows (PowerShell)**
```powershell
.\scripts\test-deployment-prerequisites.ps1
```

**Linux/Mac (Bash)**
```bash
chmod +x scripts/test-deployment-prerequisites.sh
./scripts/test-deployment-prerequisites.sh
```

---

## Infrastructure Deployment

### Initial Setup

#### 1. Configure AWS Credentials

```bash
aws configure
```

You'll be prompted for:
- **AWS Access Key ID**: Your IAM user access key
- **AWS Secret Access Key**: Your IAM user secret key
- **Default region**: e.g., `us-east-1`
- **Default output format**: `json` (recommended)

#### 2. Clone the Repository

```bash
git clone <repository-url>
cd vitalmatch-clinical-trial-matcher
```

#### 3. Review Configuration

Edit `samconfig.toml` to customize:
- Stack name
- AWS region
- Environment (dev/staging/prod)
- Database username (default: `vitalmatch_admin`)

**Important**: Never commit database passwords to version control!

### Deployment Steps

#### Step 1: Validate the Template

Ensure the SAM template is valid:

```bash
sam validate --lint
```

Expected output:
```
template.yaml is a valid SAM Template
```

#### Step 2: Build the Application

```bash
sam build
```

This prepares the template for deployment.

#### Step 3: Deploy with Guided Mode (First Time)

For first-time deployment, use guided mode:

```bash
sam deploy --guided
```

You'll be prompted for:

1. **Stack Name**: `vitalmatch-dev` (or your preferred name)
2. **AWS Region**: `us-east-1` (or your preferred region)
3. **Parameter Environment**: `dev`, `staging`, or `prod`
4. **Parameter DBUsername**: `vitalmatch_admin` (or custom username)
5. **Parameter DBPassword**: Enter a secure password (min 8 characters)
   - Use a strong password with uppercase, lowercase, numbers, and symbols
   - Example: `MySecureP@ssw0rd2024!`
6. **Confirm changes before deploy**: `Y`
7. **Allow SAM CLI IAM role creation**: `Y`
8. **Disable rollback**: `N` (recommended for production)
9. **Save arguments to configuration file**: `Y`
10. **SAM configuration file**: `samconfig.toml`
11. **SAM configuration environment**: `default`

#### Step 4: Monitor Deployment

The deployment will take approximately 15-20 minutes due to:
- VPC and networking setup (~5 minutes)
- RDS database creation (~10-15 minutes)
- WAF and security configuration (~2-3 minutes)

Monitor progress:
```bash
# In another terminal
aws cloudformation describe-stack-events \
  --stack-name vitalmatch-dev \
  --query 'StackEvents[0:10].[Timestamp,ResourceStatus,ResourceType,LogicalResourceId]' \
  --output table
```

#### Step 5: Subsequent Deployments

After initial deployment, use:

```bash
# Deploy with saved configuration
sam deploy

# Or deploy to specific environment
sam deploy --config-env prod
```

---

## Frontend Deployment

### Overview

The frontend deployment process:
1. Builds the React application using Vite
2. Uploads the production bundle to S3
3. Invalidates CloudFront cache to serve fresh content
4. Verifies the deployment

### Deployment Methods

#### Method 1: Automated Script (Recommended)

**Windows (PowerShell)**
```powershell
.\scripts\deploy-frontend.ps1 -Environment dev
```

**Linux/Mac (Bash)**
```bash
chmod +x scripts/deploy-frontend.sh
./scripts/deploy-frontend.sh dev
```

#### Method 2: Manual Deployment

1. **Retrieve Infrastructure Details**
```bash
BUCKET_NAME=$(aws cloudformation describe-stacks --stack-name vitalmatch-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`FrontendBucketName`].OutputValue' --output text)

DISTRIBUTION_ID=$(aws cloudformation describe-stacks --stack-name vitalmatch-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontDistributionId`].OutputValue' --output text)

API_ENDPOINT=$(aws cloudformation describe-stacks --stack-name vitalmatch-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' --output text)
```

2. **Build and Deploy**
```bash
cd frontend
echo "VITE_API_ENDPOINT=$API_ENDPOINT" > .env.production
npm install && npm run test && npm run build

# Upload with cache headers
aws s3 sync dist/ s3://$BUCKET_NAME/ --delete \
  --cache-control "public, max-age=31536000, immutable" --exclude "*.html"

aws s3 sync dist/ s3://$BUCKET_NAME/ --exclude "*" --include "*.html" \
  --cache-control "public, max-age=300, must-revalidate"

# Invalidate CloudFront
aws cloudfront create-invalidation --distribution-id $DISTRIBUTION_ID --paths "/*"
```

### Cache Strategy

**Static Assets (CSS, JS, Images)**: 1 year cache (content-hashed filenames)
```
Cache-Control: public, max-age=31536000, immutable
```

**HTML Files**: 5 minutes cache (references to hashed assets)
```
Cache-Control: public, max-age=300, must-revalidate
```

### Expected Output

```
========================================
Deployment completed successfully!
========================================
CloudFront URL: https://d1234567890abc.cloudfront.net
API Endpoint: https://abcdef1234.execute-api.us-east-1.amazonaws.com/dev
========================================
```

---

## Post-Deployment Configuration

### 1. Retrieve Stack Outputs

```bash
aws cloudformation describe-stacks \
  --stack-name vitalmatch-dev \
  --query 'Stacks[0].Outputs' \
  --output table
```

Key outputs:
- **VPCId**: VPC identifier
- **RDSProxyEndpoint**: Use this for Lambda database connections
- **WebACLArn**: WAF Web ACL ARN
- **SystemAlertTopicArn**: SNS topic for alerts
- **CloudFrontURL**: Frontend application URL
- **FrontendBucketName**: S3 bucket for frontend assets

### 2. Subscribe to SNS Alerts

Subscribe to receive email notifications:

```bash
# WAF alerts
aws sns subscribe \
  --topic-arn <WAF_ALERT_TOPIC_ARN> \
  --protocol email \
  --notification-endpoint your-email@example.com

# System alerts
aws sns subscribe \
  --topic-arn <SYSTEM_ALERT_TOPIC_ARN> \
  --protocol email \
  --notification-endpoint your-email@example.com
```

Confirm the subscription by clicking the link in the email.

### 3. Store Database Credentials Securely

The deployment automatically stores credentials in:
- **Secrets Manager**: `/dev/vitalmatch/db-credentials`
- **Parameter Store**: `/dev/vitalmatch/db/username`, `/dev/vitalmatch/db/password`

Retrieve credentials:
```bash
# From Secrets Manager
aws secretsmanager get-secret-value \
  --secret-id dev/vitalmatch/db-credentials \
  --query SecretString \
  --output text | jq .

# From Parameter Store
aws ssm get-parameter \
  --name /dev/vitalmatch/db/username \
  --query Parameter.Value \
  --output text
```

### 4. Update Database Password (Recommended)

For production, use a more secure password storage:

```bash
# Generate a secure password
NEW_PASSWORD=$(openssl rand -base64 32)

# Update in Secrets Manager
aws secretsmanager update-secret \
  --secret-id prod/vitalmatch/db-credentials \
  --secret-string "{\"username\":\"vitalmatch_admin\",\"password\":\"$NEW_PASSWORD\",\"engine\":\"postgres\",\"host\":\"<RDS_ENDPOINT>\",\"port\":5432,\"dbname\":\"trials_db\"}"

# Update RDS master password
aws rds modify-db-instance \
  --db-instance-identifier prod-vitalmatch-db \
  --master-user-password "$NEW_PASSWORD" \
  --apply-immediately
```

---

## Verification

### Infrastructure Verification

#### 1. Verify VPC Configuration

```bash
# Check VPC
aws ec2 describe-vpcs \
  --filters "Name=tag:Name,Values=dev-vitalmatch-vpc" \
  --query 'Vpcs[0].[VpcId,CidrBlock,State]' \
  --output table

# Check subnets
aws ec2 describe-subnets \
  --filters "Name=tag:Name,Values=dev-vitalmatch-private-subnet-*" \
  --query 'Subnets[].[SubnetId,CidrBlock,AvailabilityZone]' \
  --output table

# Check NAT Gateway
aws ec2 describe-nat-gateways \
  --filter "Name=tag:Name,Values=dev-vitalmatch-nat" \
  --query 'NatGateways[0].[NatGatewayId,State,VpcId]' \
  --output table
```

#### 2. Verify RDS Database

```bash
# Check RDS instance
aws rds describe-db-instances \
  --db-instance-identifier dev-vitalmatch-db \
  --query 'DBInstances[0].[DBInstanceIdentifier,DBInstanceStatus,Engine,EngineVersion,MultiAZ]' \
  --output table

# Check RDS Proxy
aws rds describe-db-proxies \
  --db-proxy-name dev-vitalmatch-proxy \
  --query 'DBProxies[0].[DBProxyName,Status,Endpoint]' \
  --output table
```

#### 3. Verify WAF Configuration

```bash
# Check WAF Web ACL
aws wafv2 list-web-acls \
  --scope REGIONAL \
  --region us-east-1 \
  --query 'WebACLs[?Name==`dev-vitalmatch-waf`]' \
  --output table

# Check WAF rules
aws wafv2 get-web-acl \
  --scope REGIONAL \
  --id <WEB_ACL_ID> \
  --name dev-vitalmatch-waf \
  --region us-east-1 \
  --query 'WebACL.Rules[].Name' \
  --output table
```

#### 4. Verify Security Groups

```bash
# Lambda security group
aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=dev-vitalmatch-lambda-sg" \
  --query 'SecurityGroups[0].{GroupId:GroupId,Egress:IpPermissionsEgress}' \
  --output json

# RDS security group
aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=dev-vitalmatch-rds-sg" \
  --query 'SecurityGroups[0].{GroupId:GroupId,Ingress:IpPermissions}' \
  --output json
```

### Frontend Verification

#### 1. Check CloudFront Status
```bash
aws cloudfront get-distribution --id <DISTRIBUTION_ID> \
  --query 'Distribution.Status' --output text
```
Expected: `Deployed`

#### 2. Test Application
- Open CloudFront URL in browser
- Check browser console for errors
- Verify form loads correctly
- Test patient profile submission
- Check Network tab for API calls

#### 3. Verify Security Headers
```bash
curl -I <CLOUDFRONT_URL>
```
Expected headers:
- `Strict-Transport-Security`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection`

#### 4. Test Cache Behavior
- First load: `X-Cache: Miss from cloudfront`
- Reload: `X-Cache: Hit from cloudfront`

### Frontend Rollback

**Option 1: S3 Version Rollback**
```bash
# List versions
aws s3api list-object-versions --bucket <BUCKET_NAME> --prefix index.html

# Restore previous version
aws s3api copy-object --bucket <BUCKET_NAME> \
  --copy-source <BUCKET_NAME>/index.html?versionId=<VERSION_ID> --key index.html

# Invalidate cache
aws cloudfront create-invalidation --distribution-id <DISTRIBUTION_ID> --paths "/*"
```

**Option 2: Git Rollback**
```bash
git checkout <PREVIOUS_COMMIT>
./scripts/deploy-frontend.sh dev
git checkout main
```

#### 6. Test Database Connectivity (Optional)

If you have a bastion host or EC2 instance in the VPC:

```bash
# Install PostgreSQL client
sudo yum install postgresql15 -y  # Amazon Linux
sudo apt-get install postgresql-client -y  # Ubuntu

# Connect via RDS Proxy
psql -h <RDS_PROXY_ENDPOINT> -U vitalmatch_admin -d trials_db
```

---

## Troubleshooting

### Infrastructure Issues

#### Issue: Stack Creation Failed

**Solution**: Check CloudFormation events for specific error:
```bash
aws cloudformation describe-stack-events \
  --stack-name vitalmatch-dev \
  --query 'StackEvents[?ResourceStatus==`CREATE_FAILED`].[LogicalResourceId,ResourceStatusReason]' \
  --output table
```

#### Issue: RDS Creation Timeout

**Cause**: RDS instances take 10-15 minutes to create.

**Solution**: Wait for completion or check RDS console for status.

#### Issue: Insufficient IAM Permissions

**Error**: `User: arn:aws:iam::xxx:user/xxx is not authorized to perform: xxx`

**Solution**: Ensure your IAM user has the required permissions:
- `AWSCloudFormationFullAccess`
- `AmazonVPCFullAccess`
- `AmazonRDSFullAccess`
- `IAMFullAccess`
- `CloudWatchFullAccess`
- `AWSWAFFullAccess`

#### Issue: Parameter Store Access Denied

**Solution**: Add SSM permissions to your IAM user:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ssm:PutParameter",
        "ssm:GetParameter",
        "ssm:GetParameters"
      ],
      "Resource": "arn:aws:ssm:*:*:parameter/*/vitalmatch/*"
    }
  ]
}
```

#### Issue: NAT Gateway Costs Too High

**Solution**: For development, consider:
1. Using VPC endpoints for AWS services (S3, DynamoDB)
2. Temporarily stopping NAT Gateway when not in use
3. Using a smaller instance type for testing

#### Issue: WAF Blocking Legitimate Traffic

**Solution**: Review WAF logs and adjust rules:
```bash
# View blocked requests
aws logs filter-log-events \
  --log-group-name /aws/waf/dev-vitalmatch \
  --filter-pattern "BLOCK" \
  --max-items 10
```

### Frontend Issues

#### Issue: AWS CLI Not Found

**Solution:**
```bash
# Install AWS CLI
# Windows: https://aws.amazon.com/cli/
# Mac: brew install awscli
# Linux: pip install awscli

aws configure
```

#### Issue: CloudFormation Stack Not Found

**Solution:** Deploy infrastructure first using the Infrastructure Deployment section above.

#### Issue: Build Fails

**Solution:**
```bash
cd frontend
npm install
npm run build
# Check output for specific errors
```

#### Issue: CloudFront Shows Old Content

**Solution:**
```bash
aws cloudfront create-invalidation --distribution-id <DISTRIBUTION_ID> --paths "/*"
# Hard refresh browser: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)
```

#### Issue: API Calls Fail with CORS Errors

**Solution:**
1. Verify API endpoint in `.env.production`
2. Check API Gateway CORS configuration
3. Ensure API Gateway is deployed
4. Check browser console for exact error

#### Issue: Upload to S3 Fails

**Solution:**
```bash
# Check permissions
aws sts get-caller-identity

# Ensure IAM user/role has:
# - s3:PutObject
# - s3:DeleteObject
# - s3:ListBucket
```

### Rollback Procedures

#### Infrastructure Rollback

If infrastructure deployment fails, CloudFormation automatically rolls back. To manually rollback:

```bash
sam delete --stack-name vitalmatch-dev
git checkout <PREVIOUS_COMMIT>
sam deploy
```

---

## Performance Optimization

### Infrastructure

- **RDS Proxy**: Connection pooling for Lambda functions
- **Multi-AZ**: High availability for production
- **VPC Flow Logs**: Network monitoring with minimal overhead

### Frontend Cache Headers

**Static Assets (CSS, JS, Images)**
```
Cache-Control: public, max-age=31536000, immutable
```
- 1 year cache (content-hashed filenames)
- Reduces CloudFront requests

**HTML Files**
```
Cache-Control: public, max-age=300, must-revalidate
```
- 5 minutes cache
- Ensures users get updates quickly

### CloudFront Optimization

- HTTP/2 and HTTP/3 enabled
- Automatic compression (gzip, brotli)
- Global edge locations
- Origin Access Control (S3 not public)

---

## Security Features

The deployment includes:

- ✅ HTTPS only (HTTP redirects to HTTPS)
- ✅ Security headers (HSTS, X-Frame-Options, etc.)
- ✅ WAF protection (SQL injection, XSS, rate limiting)
- ✅ Origin Access Control (S3 not publicly accessible)
- ✅ Encryption in transit (TLS 1.2+)
- ✅ VPC isolation for backend resources
- ✅ RDS encryption at rest
- ✅ Secrets Manager for credentials

---

## Cost Considerations

### Infrastructure Costs
- **RDS**: ~$50-100/month (db.t3.micro)
- **NAT Gateway**: ~$32/month + data transfer
- **VPC**: Free (except NAT Gateway)
- **WAF**: ~$5/month + $1 per million requests

### Frontend Costs
- **CloudFront**: ~$0.085 per GB (first 10 TB/month)
- **CloudFront Requests**: ~$0.0075 per 10,000 HTTPS requests
- **S3 Storage**: ~$0.023 per GB/month
- **S3 Requests**: ~$0.005 per 1,000 PUT requests
- **Invalidations**: First 1,000 paths free per month

### Estimated Monthly Cost
For 1,000 daily users:
- Infrastructure: ~$100-150/month
- Frontend: ~$10-20/month
- **Total**: ~$110-170/month

---

## Cleanup

To delete all resources and avoid ongoing charges:

```bash
# Delete the stack
sam delete --stack-name vitalmatch-dev

# Confirm deletion
# This will:
# - Create a final RDS snapshot
# - Delete all networking resources
# - Delete CloudWatch logs (after retention period)
# - Delete WAF configuration
# - Delete S3 bucket and CloudFront distribution
```

**Warning**: This action cannot be undone. Ensure you have backups of any important data.

---

## Next Steps

After successful deployment:

1. ✅ **Database Schema**: Create the trials table and indexes
2. ✅ **Lambda Functions**: Deploy data ingestion and matching functions
3. ✅ **API Gateway**: Set up REST API endpoints
4. ✅ **Testing**: Run integration tests to verify end-to-end functionality
5. ✅ **Monitoring**: Set up CloudWatch alarms and dashboards
6. ✅ **Custom Domain**: Configure Route 53 and ACM certificate (optional)
7. ✅ **CI/CD Pipeline**: Set up automated deployments (optional)

---

## Related Documentation

- **Quick Reference**: `docs/DEPLOYMENT-QUICK-REFERENCE.md`
- **Frontend Details**: `docs/FRONTEND-DEPLOYMENT.md`
- **CloudFront Config**: `docs/CLOUDFRONT-CONFIGURATION.md`
- **Infrastructure**: `docs/INFRASTRUCTURE.md`
- **Cost Optimization**: `docs/COST_OPTIMIZATION.md`
- **Pre-Deployment Checklist**: `docs/PRE_DEPLOYMENT_CHECKLIST.md`

---

## Support

For deployment issues:
1. Check CloudFormation events for detailed error messages
2. Review CloudWatch logs for service-specific errors
3. Verify IAM permissions for all required services
4. Run prerequisites test script
5. Consult troubleshooting section above
6. Review AWS documentation for service-specific issues

## Additional Resources

- [AWS SAM Documentation](https://docs.aws.amazon.com/serverless-application-model/)
- [AWS CloudFormation User Guide](https://docs.aws.amazon.com/cloudformation/)
- [Amazon RDS User Guide](https://docs.aws.amazon.com/rds/)
- [AWS WAF Developer Guide](https://docs.aws.amazon.com/waf/)
- [Amazon CloudFront Documentation](https://docs.aws.amazon.com/cloudfront/)
- [Amazon S3 User Guide](https://docs.aws.amazon.com/s3/)
