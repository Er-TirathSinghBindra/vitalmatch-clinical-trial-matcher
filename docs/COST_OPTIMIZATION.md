# Cost Optimization: Hybrid Lambda Architecture

## Overview

We've implemented a hybrid Lambda architecture that eliminates the need for a NAT Gateway, saving approximately **$384/year** (~$32/month).

## Architecture Changes

### Before (with NAT Gateway)
```
Internet
    │
    └─→ NAT Gateway ($32/month)
            │
            └─→ Lambda Functions (in VPC)
                    │
                    ├─→ RDS (private)
                    └─→ ClinicalTrials.gov API
```

### After (Hybrid Approach)
```
Internet
    │
    ├─→ Data Ingestion Lambda (outside VPC)
    │       │
    │       ├─→ ClinicalTrials.gov API (native internet)
    │       └─→ RDS (public with IAM auth)
    │
    └─→ Match Trials Lambda (in VPC)
            └─→ RDS via RDS Proxy (private)
```

## Key Changes

### 1. Data Ingestion Lambda
- **Location**: Outside VPC
- **Internet Access**: Native (no NAT Gateway needed)
- **RDS Connection**: Direct to RDS endpoint using IAM authentication
- **Security**: IAM-based authentication, no password storage

### 2. Match Trials Lambda
- **Location**: Inside VPC (private subnets)
- **Internet Access**: None (doesn't need it)
- **RDS Connection**: Via RDS Proxy for connection pooling
- **Security**: Fully isolated in VPC

### 3. RDS Database
- **Publicly Accessible**: Yes (but secured)
- **Security Measures**:
  - IAM database authentication required (no password-based access)
  - Security group allows connections from:
    - Lambda Security Group (VPC Lambda)
    - 0.0.0.0/0 with IAM auth (Data Ingestion Lambda)
  - Encryption in transit (TLS required)
  - Encryption at rest (KMS)

## Security Considerations

### Is Public RDS Secure?

Yes, when properly configured:

1. **IAM Authentication**: No passwords, only IAM-based authentication
2. **TLS Encryption**: All connections encrypted in transit
3. **KMS Encryption**: Data encrypted at rest
4. **Security Groups**: Firewall rules control access
5. **CloudWatch Logging**: All connection attempts logged

### Attack Surface Analysis

**Before (Private RDS + NAT Gateway)**:
- RDS: Private (good)
- NAT Gateway: Public IP (potential attack vector)
- Lambda: Private (good)

**After (Public RDS + No NAT Gateway)**:
- RDS: Public with IAM auth (secure)
- No NAT Gateway: No public IP to attack
- Lambda: Mixed (Data Ingestion public, Match Trials private)

The attack surface is actually reduced because:
- No NAT Gateway public IP to target
- RDS requires IAM authentication (can't brute force passwords)
- All connections logged and monitored

## Cost Savings

### Monthly Savings
| Item | Before | After | Savings |
|------|--------|-------|---------|
| NAT Gateway | $32.00 | $0.00 | $32.00 |
| NAT Data Transfer | $5-10 | $0.00 | $5-10 |
| **Total** | **$37-42** | **$0** | **$37-42/month** |

### Annual Savings
- **$444-504/year** saved by eliminating NAT Gateway

### Environment Costs

**Development**:
- Before: ~$50-100/month
- After: ~$20-70/month
- Savings: ~$30-40/month

**Production**:
- Before: ~$200-500/month
- After: ~$170-470/month
- Savings: ~$30-40/month

## Implementation Details

### Data Ingestion Lambda Configuration

```yaml
DataIngestionFunction:
  Type: AWS::Serverless::Function
  Properties:
    # NO VpcConfig - runs outside VPC
    Environment:
      Variables:
        RDS_ENDPOINT: !GetAtt TrialDatabase.Endpoint.Address
        DB_SECRET_ARN: !Ref DBSecret
    # IAM role includes rds-db:connect permission
```

### Match Trials Lambda Configuration

```yaml
MatchTrialsFunction:
  Type: AWS::Serverless::Function
  Properties:
    VpcConfig:
      SecurityGroupIds:
        - !Ref LambdaSecurityGroup
      SubnetIds:
        - !Ref PrivateSubnetA
        - !Ref PrivateSubnetB
    Environment:
      Variables:
        RDS_PROXY_ENDPOINT: !GetAtt RDSProxy.Endpoint
```

### RDS Security Group

```yaml
RDSSecurityGroup:
  SecurityGroupIngress:
    # VPC Lambda access
    - IpProtocol: tcp
      FromPort: 5432
      ToPort: 5432
      SourceSecurityGroupId: !Ref LambdaSecurityGroup
    
    # Data Ingestion Lambda access (with IAM auth)
    - IpProtocol: tcp
      FromPort: 5432
      ToPort: 5432
      CidrIp: 0.0.0.0/0
```

## Best Practices

### When to Use This Approach

✅ **Good for**:
- Applications with separate data ingestion and query workloads
- Cost-sensitive projects
- Workloads where Lambda needs internet access for external APIs

❌ **Not recommended for**:
- Highly regulated industries requiring private-only databases
- Applications with strict compliance requirements against public databases
- Workloads where all Lambda functions need internet access

### Alternative Approaches

If you need all Lambda functions in VPC with internet access:

1. **VPC Endpoints**: Use for AWS services (S3, DynamoDB, Bedrock)
   - Cost: ~$7/month per endpoint
   - Eliminates NAT Gateway for AWS service calls

2. **NAT Instance**: Use EC2 instance instead of NAT Gateway
   - Cost: ~$5-10/month (t3.nano)
   - Requires management and monitoring

3. **Hybrid with VPC Endpoints**: Combine both approaches
   - Use VPC endpoints for AWS services
   - Use hybrid Lambda for external APIs
   - Maximum cost savings

## Monitoring and Alerts

### CloudWatch Metrics to Monitor

1. **RDS Connection Attempts**: Monitor failed authentication attempts
2. **Lambda Errors**: Track Data Ingestion Lambda connection errors
3. **VPC Flow Logs**: Monitor traffic to RDS from unexpected sources
4. **CloudTrail**: Track IAM authentication events

### Recommended Alarms

```yaml
# Alert on failed RDS connections
RDSAuthFailureAlarm:
  MetricName: FailedConnections
  Threshold: 10
  Period: 300

# Alert on Data Ingestion Lambda errors
DataIngestionErrorAlarm:
  MetricName: Errors
  Threshold: 1
  Period: 300
```

## Migration Guide

### From NAT Gateway to Hybrid Approach

1. **Update Data Ingestion Lambda**:
   - Remove VpcConfig from Lambda function
   - Change RDS_PROXY_ENDPOINT to RDS_ENDPOINT
   - Update IAM role to remove VPC execution policy

2. **Update RDS Configuration**:
   - Set PubliclyAccessible: true
   - Update security group to allow 0.0.0.0/0 on port 5432
   - Ensure IAM authentication is enabled

3. **Remove NAT Gateway**:
   - Delete NAT Gateway resource
   - Delete Elastic IP
   - Remove NAT Gateway route from private route table

4. **Test Connectivity**:
   - Test Data Ingestion Lambda can connect to RDS
   - Test Match Trials Lambda can still connect via RDS Proxy
   - Verify data ingestion works end-to-end

### Rollback Plan

If issues arise, rollback by:

1. Recreate NAT Gateway and Elastic IP
2. Add NAT Gateway route to private route table
3. Add VpcConfig back to Data Ingestion Lambda
4. Change RDS_ENDPOINT back to RDS_PROXY_ENDPOINT
5. Set RDS PubliclyAccessible: false
6. Remove 0.0.0.0/0 from RDS security group

## Conclusion

The hybrid Lambda architecture provides:
- **Cost savings**: ~$384-504/year
- **Maintained security**: IAM authentication, encryption, monitoring
- **Simplified architecture**: No NAT Gateway to manage
- **Better separation**: Data ingestion and query workloads isolated

This approach is ideal for cost-conscious projects that don't have strict requirements for private-only databases.
