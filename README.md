# VitalMatch - Clinical Trial Matcher

An intelligent eligibility engine that matches patients with relevant clinical trials using AWS serverless architecture and AI-powered analysis.

## What is VitalMatch?

VitalMatch helps patients find clinical trials they're eligible for by analyzing their medical profile against trial criteria. It combines rule-based filtering with AI-powered medical text analysis to provide accurate, ranked matches.

## Key Features

- **Smart Matching**: Hybrid approach using SQL filtering + AI analysis
- **Real-time Data**: Integrates with ClinicalTrials.gov API
- **Secure & Scalable**: AWS serverless architecture with enterprise security
- **User-friendly**: React-based web interface with CloudFront CDN
- **Cost-optimized**: Hybrid Lambda design saves ~$384/year on infrastructure

## Technology Stack

**Frontend**: React, Vite, CloudFront, S3  
**Backend**: AWS Lambda (Python), API Gateway, RDS PostgreSQL  
**AI/ML**: Amazon Bedrock (Claude models)  
**Security**: WAF, VPC, IAM, Secrets Manager  
**Data**: ClinicalTrials.gov API

## Quick Start

```bash
# 1. Install prerequisites
aws --version && sam --version

# 2. Deploy infrastructure
sam build && sam deploy --guided

# 3. Deploy frontend
./scripts/deploy-frontend.sh dev

# 4. Access application
# Use CloudFront URL from deployment output
```

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed instructions.

## Architecture Overview

VitalMatch uses a hybrid architecture combining:
- **SQL-based hard filtering** for age, gender, and location criteria
- **AI-powered soft matching** using Amazon Bedrock for medical text analysis
- **Serverless AWS infrastructure** for scalability and cost efficiency
- **Hybrid Lambda approach**: Data ingestion outside VPC (internet access), matching inside VPC (database access)

## Infrastructure Components

### Network Layer (VPC)
- VPC with CIDR 10.0.0.0/16
- Two private subnets in different AZs (10.0.1.0/24, 10.0.2.0/24)
- Public subnet for internet gateway
- Security groups for Lambda and RDS with least privilege access
- VPC Flow Logs for network monitoring
- **Hybrid Lambda approach**: Data ingestion Lambda outside VPC (internet access), Match Lambda in VPC (RDS access)

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

## Project Structure

```
├── backend/              # Python Lambda functions and AI matching logic
├── frontend/             # React application
├── database/             # PostgreSQL schema and migrations
├── docs/                 # Detailed documentation
├── template.yaml         # AWS SAM infrastructure template
└── samconfig.toml        # SAM deployment configuration
```

## Development

### Local Setup

```bash
# Backend tests
cd backend
pip install -r requirements.txt
pytest

# Frontend development
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
# Backend unit tests
pytest backend/tests/

# Frontend tests
cd frontend && npm test
```

## Deployment

### Prerequisites

- AWS CLI v2.x+ configured with credentials
- AWS SAM CLI v1.x+
- Node.js 18+ and npm (for frontend)
- IAM permissions for CloudFormation, VPC, RDS, Lambda, S3, CloudFront

### Infrastructure Deployment

```bash
sam build
sam deploy --guided
```

### Frontend Deployment

```bash
# Windows
.\scripts\deploy-frontend.ps1 -Environment dev

# Linux/Mac
./scripts/deploy-frontend.sh dev
```

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for complete instructions.

## Security Considerations

### Database Credentials
- Stored in AWS Secrets Manager
- Also available in Systems Manager Parameter Store
- Use IAM authentication for Lambda connections

### Network Security
- Match Lambda functions have no public IP addresses (in VPC)
- Data Ingestion Lambda outside VPC uses IAM authentication for RDS access
- RDS database is publicly accessible but secured with:
  - IAM database authentication (no password-based access)
  - Security group restricts access to Lambda and specific IPs
  - Encryption in transit (TLS required)
  - Encryption at rest (KMS)
- All traffic between Match Lambda and RDS stays within VPC

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

### Development (~$20-40/month)
- RDS db.t3.micro: ~$15/month
- Data transfer: ~$5-10/month
- CloudWatch: ~$5/month

### Production (~$140-290/month)
- RDS db.t3.medium Multi-AZ: ~$120/month
- Lambda + API Gateway: ~$10-50/month
- CloudFront + S3: ~$10-20/month

**Cost Savings**: Hybrid Lambda design eliminates NAT Gateway (~$384/year savings)

## Documentation

- [DEPLOYMENT.md](docs/DEPLOYMENT.md) - Complete deployment guide
- [INFRASTRUCTURE.md](docs/INFRASTRUCTURE.md) - Architecture details
- [COST_OPTIMIZATION.md](docs/COST_OPTIMIZATION.md) - Cost management strategies
- [PRE_DEPLOYMENT_CHECKLIST.md](docs/PRE_DEPLOYMENT_CHECKLIST.md) - Pre-flight checks
- [TEST_SAMPLES_SUMMARY.md](docs/TEST_SAMPLES_SUMMARY.md) - Test patient profiles for Frontend Testing

## Troubleshooting

**RDS Connection Issues**: Use RDS Proxy endpoint, verify security groups  
**WAF Blocking Traffic**: Check CloudWatch logs, adjust rules  
**Frontend Not Loading**: Verify CloudFront invalidation completed

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed troubleshooting.

## Cleanup

To delete all resources:

```bash
sam delete --stack-name vitalmatch-dev
```

This removes VPC, RDS (with final snapshot), CloudWatch logs, WAF, S3, and CloudFront.

## License

See LICENSE file for details.
