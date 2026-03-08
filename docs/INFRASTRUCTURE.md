# VitalMatch Infrastructure Reference

Quick reference guide for the AWS infrastructure components.

## Architecture Summary

```
Internet
    │
    ├─→ CloudFront (CDN) ──→ S3 (Static Website)
    │        │
    │        └─→ WAF (Web Application Firewall)
    │
    └─→ API Gateway ──→ WAF
             │
             └─→ Lambda Functions (in VPC Private Subnets)
                      │
                      ├─→ RDS Proxy ──→ RDS PostgreSQL
                      │
                      └─→ Amazon Bedrock (AI/ML)
```

## Network Architecture

### VPC Configuration
- **CIDR Block**: 10.0.0.0/16
- **DNS Support**: Enabled
- **DNS Hostnames**: Enabled

### Subnets

| Subnet | CIDR | Type | Purpose |
|--------|------|------|---------|
| Public Subnet | 10.0.0.0/24 | Public | NAT Gateway |
| Private Subnet A | 10.0.1.0/24 | Private | Lambda, RDS (AZ-1) |
| Private Subnet B | 10.0.2.0/24 | Private | Lambda, RDS (AZ-2) |

### Internet Connectivity
- **Internet Gateway**: Attached to VPC for public subnet
- **No NAT Gateway**: Using hybrid Lambda approach instead
- **Data Ingestion Lambda**: Runs outside VPC with native internet access
- **Match Trials Lambda**: Runs inside VPC, connects to RDS via RDS Proxy

### Route Tables

**Public Route Table**:
- 10.0.0.0/16 → Local
- 0.0.0.0/0 → Internet Gateway

**Private Route Table**:
- 10.0.0.0/16 → Local
- No NAT Gateway route (Match Lambda doesn't need internet)

## Security Groups

### Lambda Security Group
**Inbound**: None (Lambda doesn't accept inbound connections)

**Outbound**:
- Port 5432 (PostgreSQL) → RDS Security Group
- Port 443 (HTTPS) → 0.0.0.0/0 (for external APIs)

### RDS Security Group
**Inbound**:
- Port 5432 (PostgreSQL) ← Lambda Security Group (VPC Lambda)
- Port 5432 (PostgreSQL) ← 0.0.0.0/0 (Data Ingestion Lambda with IAM auth)

**Outbound**: None

## Database Configuration

### RDS PostgreSQL Instance

| Setting | Development | Production |
|---------|-------------|------------|
| Instance Class | db.t3.micro | db.t3.medium |
| Engine | PostgreSQL 15.4 | PostgreSQL 15.4 |
| Storage | 100 GB gp3 | 100 GB gp3 |
| Multi-AZ | No | Yes |
| Encryption | Yes (KMS) | Yes (KMS) |
| Backup Retention | 7 days | 7 days |
| IAM Auth | Enabled | Enabled |
| Publicly Accessible | Yes (IAM auth only) | Yes (IAM auth only) |

### RDS Proxy
- **Purpose**: Connection pooling for Lambda functions
- **Max Connections**: 100
- **Idle Timeout**: 30 minutes (1800 seconds)
- **TLS**: Required
- **Authentication**: IAM + Secrets Manager

### Database Credentials Storage

**Secrets Manager**:
- Secret Name: `{environment}/vitalmatch/db-credentials`
- Contains: username, password, host, port, dbname, engine

**Parameter Store**:
- `/{environment}/vitalmatch/db/username`
- `/{environment}/vitalmatch/db/password`
- `/{environment}/vitalmatch/db/endpoint`
- `/{environment}/vitalmatch/db/proxy-endpoint`

## WAF Configuration

### Web ACL Rules

| Priority | Rule | Action | Purpose |
|----------|------|--------|---------|
| 1 | AWS Managed - Core Rule Set | Block | Common web attacks |
| 2 | AWS Managed - Known Bad Inputs | Block | Known malicious patterns |
| 3 | AWS Managed - SQLi Rule Set | Block | SQL injection attacks |
| 4 | Rate Limiting | Block | 2000 req/5min per IP |

### WAF Logging
- **Log Group**: `/aws/waf/{environment}-vitalmatch`
- **Retention**: 30 days
- **Metrics**: Enabled for all rules

### WAF Alerts
- **SNS Topic**: `{environment}-vitalmatch-waf-alerts`
- **Alarm Threshold**: >1000 blocked requests per hour

## Monitoring and Logging

### VPC Flow Logs
- **Log Group**: `/aws/vpc/{environment}-vitalmatch-flowlogs`
- **Traffic Type**: ALL (accepted and rejected)
- **Retention**: 30 days

### CloudWatch Log Groups

| Log Group | Source | Retention |
|-----------|--------|-----------|
| `/aws/vpc/{env}-vitalmatch-flowlogs` | VPC Flow Logs | 30 days |
| `/aws/waf/{env}-vitalmatch` | WAF | 30 days |
| `/aws/rds/instance/{env}-vitalmatch-db/postgresql` | RDS | 7 days |

### SNS Topics

| Topic | Purpose | Subscribers |
|-------|---------|-------------|
| `{env}-vitalmatch-waf-alerts` | WAF security alerts | Email (configure) |
| `{env}-vitalmatch-system-alerts` | General system alerts | Email (configure) |

## Resource Naming Convention

All resources follow the pattern: `{environment}-vitalmatch-{resource-type}`

Examples:
- `dev-vitalmatch-vpc`
- `prod-vitalmatch-db`
- `staging-vitalmatch-lambda-sg`

## IAM Roles

### VPC Flow Logs Role
- **Service**: vpc-flow-logs.amazonaws.com
- **Permissions**: CloudWatch Logs write access

### RDS Proxy Role
- **Service**: rds.amazonaws.com
- **Permissions**: 
  - Secrets Manager read access
  - KMS decrypt for database credentials

## Cost Breakdown

### Development Environment (~$20-70/month)

| Service | Cost | Notes |
|---------|------|-------|
| RDS db.t3.micro | ~$15 | Single-AZ |
| ~~NAT Gateway~~ | ~~$32~~ | **REMOVED - Hybrid Lambda approach** |
| Data Transfer | ~$5-10 | Varies by usage |
| CloudWatch Logs | ~$5 | 30-day retention |
| VPC (subnets, etc.) | Free | No charge for VPC resources |
| WAF | ~$5 | Web ACL + rules |

### Production Environment (~$170-470/month)

| Service | Cost | Notes |
|---------|------|-------|
| RDS db.t3.medium Multi-AZ | ~$120 | High availability |
| ~~NAT Gateway~~ | ~~$32~~ | **REMOVED - Hybrid Lambda approach** |
| Data Transfer | ~$20-50 | Higher usage |
| Lambda | ~$10-50 | 1000 daily users |
| CloudWatch | ~$10-20 | Logs + metrics |
| WAF | ~$10 | Higher request volume |

### Cost Optimization Tips
1. ~~Use VPC endpoints for AWS services (S3, DynamoDB) to reduce NAT Gateway data transfer~~
2. **Hybrid Lambda approach eliminates NAT Gateway entirely (~$384/year savings)**
3. Right-size RDS instance based on actual usage
4. Use CloudWatch Logs retention policies
5. Consider Reserved Instances for RDS in production
6. Monitor and optimize Lambda memory allocation

## Outputs Reference

After deployment, retrieve these values:

```bash
aws cloudformation describe-stacks \
  --stack-name {stack-name} \
  --query 'Stacks[0].Outputs'
```

### Key Outputs

| Output | Description | Usage |
|--------|-------------|-------|
| VPCId | VPC identifier | Reference in other stacks |
| PrivateSubnetAId | Private subnet A ID | Lambda configuration |
| PrivateSubnetBId | Private subnet B ID | Lambda configuration |
| LambdaSecurityGroupId | Lambda SG ID | Lambda configuration |
| RDSSecurityGroupId | RDS SG ID | Database access control |
| RDSEndpoint | Direct RDS endpoint | Direct connections (not recommended) |
| RDSProxyEndpoint | RDS Proxy endpoint | **Use this for Lambda** |
| DBSecretArn | Secrets Manager ARN | Lambda environment variable |
| WebACLArn | WAF Web ACL ARN | API Gateway/CloudFront association |
| WAFAlertTopicArn | WAF alerts SNS topic | Subscribe for notifications |
| SystemAlertTopicArn | System alerts SNS topic | Subscribe for notifications |

## Security Best Practices

### Network Security
✅ Match Lambda functions in private subnets (no public IPs)
✅ Data Ingestion Lambda outside VPC uses IAM authentication
✅ RDS publicly accessible but secured with IAM auth (no passwords)
✅ Security groups follow least privilege
✅ VPC Flow Logs enabled for audit
✅ No NAT Gateway needed (cost savings)

### Data Security
✅ RDS encryption at rest (KMS)
✅ TLS required for RDS Proxy connections
✅ Secrets stored in Secrets Manager
✅ IAM database authentication enabled
✅ Automated backups with 7-day retention

### Application Security
✅ WAF protects against common attacks
✅ Rate limiting prevents DDoS
✅ All requests logged to CloudWatch
✅ SNS alerts for suspicious activity

### Access Control
✅ IAM roles with least privilege
✅ No hardcoded credentials
✅ Parameter Store for configuration
✅ CloudTrail for API audit (enable separately)

## Maintenance Tasks

### Daily
- Monitor CloudWatch alarms
- Review WAF blocked requests

### Weekly
- Review RDS performance metrics
- Check CloudWatch Logs for errors
- Verify backup completion

### Monthly
- Review and optimize costs
- Update security group rules if needed
- Review and rotate database credentials
- Check for AWS service updates

### Quarterly
- Review and update WAF rules
- Audit IAM roles and permissions
- Test disaster recovery procedures
- Review and optimize RDS instance size

## Disaster Recovery

### RDS Backups
- **Automated Backups**: Daily, 7-day retention
- **Backup Window**: 03:00-04:00 UTC
- **Maintenance Window**: Sunday 04:00-05:00 UTC

### Recovery Procedures

**Restore from Backup**:
```bash
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier {new-instance-id} \
  --db-snapshot-identifier {snapshot-id}
```

**Point-in-Time Recovery**:
```bash
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier {source-id} \
  --target-db-instance-identifier {target-id} \
  --restore-time {timestamp}
```

### Multi-AZ Failover
- **Production**: Automatic failover to standby (1-2 minutes)
- **Development**: Manual restore from snapshot required

## Troubleshooting

### Common Issues

**Lambda can't connect to RDS**:
- **Match Lambda (in VPC)**: Verify Lambda is in correct VPC and subnets, check security group allows Lambda → RDS on port 5432, use RDS Proxy endpoint
- **Data Ingestion Lambda (outside VPC)**: Verify IAM role has `rds-db:connect` permission, use direct RDS endpoint (not proxy), ensure IAM authentication is configured

**High data transfer costs**:
- With hybrid Lambda approach, data transfer costs are minimal
- Data Ingestion Lambda has native internet access (no NAT Gateway charges)
- Match Lambda doesn't need internet access

**WAF blocking legitimate traffic**:
- Review WAF logs: `/aws/waf/{env}-vitalmatch`
- Identify blocked request patterns
- Add custom allow rules if needed

**RDS connection pool exhausted**:
- Increase RDS Proxy max connections
- Optimize Lambda connection handling
- Review and close idle connections

## Additional Resources

- [AWS VPC Documentation](https://docs.aws.amazon.com/vpc/)
- [Amazon RDS Documentation](https://docs.aws.amazon.com/rds/)
- [AWS WAF Documentation](https://docs.aws.amazon.com/waf/)
- [RDS Proxy Documentation](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/rds-proxy.html)
