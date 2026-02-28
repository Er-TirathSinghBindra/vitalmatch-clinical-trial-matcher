# VitalMatch - Clinical Trial Matcher

An intelligent eligibility engine that matches patients with relevant clinical trials using AWS serverless architecture and AI-powered analysis.

## Architecture Overview

VitalMatch uses a hybrid architecture combining:
- **SQL-based hard filtering** for age, gender, and location criteria
- **AI-powered soft matching** using Amazon Bedrock for medical text analysis
- **Serverless AWS infrastructure** for scalability and cost efficiency

## Infrastructure Components

### Network Layer (VPC)
- VPC with CIDR 10.0.0.0/16
- Two private subnets in different AZs (10.0.1.0/24, 10.0.2.0/24)
- Public subnet for NAT Gateway
- Security groups for Lambda and RDS with least privilege access
- VPC Flow Logs for network monitoring

### Database Layer
- RDS PostgreSQL 15 with Multi-AZ (production)
- RDS Proxy for connection pooling
- Encryption at rest using AWS KMS
- IAM database authentication
- Automated backups with 7-day retention

### Security Layer
- AWS WAF with managed rule sets (Core, Known Bad Inputs, SQLi)
- Rate limiting (2000 requests per 5 minutes per IP)
- CloudWatch logging for blocked requests
- SNS alerts for suspicious patterns

## Prerequisites

Before deploying, ensure you have:

1. **AWS CLI** installed and configured
   ```bash
   aws --version
   aws configure
   ```

2. **AWS SAM CLI** installed
   ```bash
   sam --version
   ```
   Install from: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html

3. **AWS Account** with appropriate permissions:
   - VPC and networking resources
   - RDS database creation
   - IAM role creation
   - CloudWatch and WAF configuration

## Deployment Instructions

### Step 1: Validate the Template

```bash
sam validate --lint
```

### Step 2: Build the Application

```bash
sam build
```

### Step 3: Deploy the Infrastructure

For first-time deployment:

```bash
sam deploy --guided
```

You will be prompted for:
- **Stack Name**: e.g., `vitalmatch-dev`
- **AWS Region**: e.g., `us-east-1`
- **Environment**: `dev`, `staging`, or `prod`
- **DBUsername**: Database master username (default: `vitalmatch_admin`)
- **DBPassword**: Database master password (minimum 8 characters)

The guided deployment will save your configuration to `samconfig.toml` for future deployments.

### Step 4: Subsequent Deployments

After the initial guided deployment:

```bash
sam deploy
```

### Step 5: Verify Deployment

Check the CloudFormation stack outputs:

```bash
aws cloudformation describe-stacks \
  --stack-name vitalmatch-dev \
  --query 'Stacks[0].Outputs'
```

Key outputs include:
- `VPCId`: VPC identifier
- `RDSEndpoint`: Direct RDS endpoint
- `RDSProxyEndpoint`: RDS Proxy endpoint (use this for Lambda connections)
- `WebACLArn`: WAF Web ACL ARN
- `SystemAlertTopicArn`: SNS topic for alerts

## Environment-Specific Configurations

### Development Environment
- RDS Instance: `db.t3.micro`
- Multi-AZ: Disabled
- Lower cost for testing

### Production Environment
- RDS Instance: `db.t3.medium`
- Multi-AZ: Enabled for high availability
- Enhanced monitoring and alerting

## Security Considerations

### Database Credentials
- Stored in AWS Secrets Manager
- Also available in Systems Manager Parameter Store
- Use IAM authentication for Lambda connections

### Network Security
- Lambda functions have no public IP addresses
- RDS database is not publicly accessible
- All traffic between Lambda and RDS stays within VPC
- NAT Gateway provides controlled outbound internet access

### WAF Protection
- Protects against common web attacks (SQLi, XSS)
- Rate limiting prevents DDoS attacks
- All blocked requests are logged to CloudWatch

## Monitoring and Alerts

### CloudWatch Logs
- VPC Flow Logs: `/aws/vpc/{environment}-vitalmatch-flowlogs`
- WAF Logs: `/aws/waf/{environment}-vitalmatch`
- RDS Logs: Exported to CloudWatch

### SNS Topics
- **WAF Alerts**: High block rate notifications
- **System Alerts**: General system notifications

Subscribe to SNS topics:
```bash
aws sns subscribe \
  --topic-arn <TOPIC_ARN> \
  --protocol email \
  --notification-endpoint your-email@example.com
```

## Cost Estimation

### Development Environment (~$50-100/month)
- RDS db.t3.micro: ~$15/month
- NAT Gateway: ~$32/month
- Data transfer: ~$5-10/month
- CloudWatch Logs: ~$5/month

### Production Environment (~$200-500/month)
- RDS db.t3.medium Multi-AZ: ~$120/month
- NAT Gateway: ~$32/month
- Data transfer: ~$20-50/month
- Lambda executions: ~$10-50/month (1000 daily users)
- CloudWatch and monitoring: ~$10-20/month

## Cleanup

To delete all resources:

```bash
sam delete --stack-name vitalmatch-dev
```

**Warning**: This will delete:
- VPC and all networking resources
- RDS database (a final snapshot will be created)
- All CloudWatch logs
- WAF configuration

## Next Steps

After infrastructure deployment:

1. **Database Schema**: Run migration scripts to create the trials table
2. **Lambda Functions**: Deploy data ingestion and matching functions
3. **API Gateway**: Set up REST API endpoints
4. **Frontend**: Deploy React application to S3/CloudFront

## Troubleshooting

### RDS Connection Issues
- Verify Lambda is in the correct VPC and subnets
- Check security group rules allow Lambda → RDS on port 5432
- Use RDS Proxy endpoint, not direct RDS endpoint

### NAT Gateway Costs
- NAT Gateway charges for data transfer
- Consider VPC endpoints for AWS services to reduce costs

### WAF False Positives
- Review WAF logs in CloudWatch
- Adjust rule sensitivity if needed
- Add custom rules to allow legitimate traffic

## Support

For issues or questions:
- Review CloudWatch logs for error details
- Check AWS CloudFormation events for deployment issues
- Verify IAM permissions for all services

## License

See LICENSE file for details.
