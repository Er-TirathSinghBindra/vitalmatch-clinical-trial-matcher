# Architecture Decisions

This document captures key architectural decisions made for VitalMatch and their rationale.

## Key Architectural Decisions

## 1. Hybrid Lambda Architecture (NAT Gateway Removal)

**Decision**: Use hybrid Lambda deployment - Data Ingestion outside VPC, Match Trials inside VPC

**Rationale:**
- Data Ingestion Lambda needs internet access for ClinicalTrials.gov API
- Match Trials Lambda needs RDS access but no internet
- Eliminates need for NAT Gateway (~$384/year cost savings)
- RDS made publicly accessible with IAM authentication for security

**Trade-offs:**
- ✅ Cost savings: ~$32/month
- ✅ Simpler network architecture
- ✅ No NAT Gateway single point of failure
- ⚠️ RDS publicly accessible (mitigated by IAM auth + security groups)

## 2. RDS Public Accessibility with IAM Authentication

**Decision**: RDS publicly accessible with IAM database authentication

**Rationale:**
- Allows Data Ingestion Lambda (outside VPC) to connect without NAT Gateway
- IAM authentication eliminates password-based access vulnerabilities
- Security groups restrict access to authorized sources only
- All connections logged to CloudWatch for audit trail

**Security Measures:**
- IAM authentication required (no password brute force possible)
- TLS encryption in transit enforced
- KMS encryption at rest
- Security group IP restrictions
- VPC Flow Logs for network monitoring
- CloudWatch logging for all connection attempts

## 3. PostgreSQL Version Selection

**Decision**: PostgreSQL 17.7 (latest stable)

**Rationale:**
- Latest security patches and performance improvements
- Better JSON support for trial data storage
- Improved query performance for complex eligibility criteria
- Long-term support and AWS RDS compatibility

## 4. RDS Proxy for Connection Pooling

**Decision**: Use RDS Proxy for Match Trials Lambda connections

**Rationale:**
- Lambda functions create many concurrent connections
- RDS Proxy pools connections efficiently
- Reduces database connection overhead
- Automatic failover for Multi-AZ deployments
- IAM authentication integration

**Benefits:**
- Improved Lambda cold start performance
- Better database resource utilization
- Enhanced security with IAM roles
- Simplified credential management

## 5. Multi-AZ Deployment Strategy

**Decision**: Multi-AZ enabled for production, disabled for development

**Rationale:**
- Production requires high availability (99.95% SLA)
- Development prioritizes cost savings over availability
- Automatic failover for production workloads
- Cross-AZ data replication for disaster recovery

**Cost Impact:**
- Development: Single-AZ saves ~$15/month
- Production: Multi-AZ worth the cost for reliability

## 6. Serverless Architecture

**Decision**: AWS Lambda + API Gateway instead of EC2/ECS

**Rationale:**
- Pay-per-use pricing model (no idle costs)
- Automatic scaling based on demand
- No server management overhead
- Built-in high availability
- Faster time to market

**Trade-offs:**
- ✅ Lower operational costs
- ✅ Zero infrastructure management
- ✅ Automatic scaling
- ⚠️ Cold start latency (mitigated with provisioned concurrency if needed)
- ⚠️ 15-minute execution limit (acceptable for our use case)

## Cost Analysis

### Before (with NAT Gateway)
| Environment | Monthly Cost |
|-------------|--------------|
| Development | $50-100 |
| Production | $200-500 |

### After (Hybrid Lambda)
| Environment | Monthly Cost | Savings |
|-------------|--------------|---------|
| Development | $20-70 | $30-40/month |
| Production | $170-470 | $30-40/month |

**Annual Savings**: ~$360-480/year

## Security Architecture Decisions

### Defense in Depth Strategy

**Layers:**
1. **Network Layer**: VPC isolation, security groups, Flow Logs
2. **Application Layer**: WAF with managed rule sets, rate limiting
3. **Data Layer**: Encryption at rest (KMS), encryption in transit (TLS)
4. **Access Layer**: IAM authentication, least privilege policies
5. **Monitoring Layer**: CloudWatch logs, X-Ray tracing, SNS alerts

### Public RDS Security Justification

Despite being publicly accessible, the RDS instance is secure because:
- **IAM Authentication**: No password-based access (can't brute force)
- **Security Groups**: IP-based access restrictions
- **TLS Required**: All connections encrypted in transit
- **KMS Encryption**: Data encrypted at rest
- **Audit Logging**: All connection attempts logged to CloudWatch
- **Network Monitoring**: VPC Flow Logs track all traffic

**Attack Surface Analysis:**
- Reduced: No NAT Gateway public IP to target
- Controlled: IAM authentication prevents unauthorized access
- Monitored: Real-time logging and alerting

## Future Considerations

### Potential Enhancements
1. **VPC Endpoints**: Add endpoints for Bedrock/Comprehend Medical (additional cost savings)
2. **Read Replicas**: Scale read operations for high traffic
3. **Aurora Serverless**: Consider for variable workloads
4. **Global Accelerator**: Improve latency for international users
5. **Multi-Region**: Disaster recovery and global availability

### Monitoring Improvements
1. CloudWatch dashboards for key metrics
2. Automated backup testing
3. Connection retry logic in Lambda functions
4. Performance benchmarking and optimization

## References

- [INFRASTRUCTURE.md](INFRASTRUCTURE.md) - Detailed infrastructure documentation
- [COST_OPTIMIZATION.md](COST_OPTIMIZATION.md) - Cost management strategies
- [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment procedures
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)

## Decision Log

| Date | Decision | Rationale | Impact |
|------|----------|-----------|--------|
| 2024 | Hybrid Lambda Architecture | Cost optimization | -$384/year |
| 2024 | IAM Database Authentication | Enhanced security | Eliminated password risks |
| 2024 | PostgreSQL 17.7 | Latest features | Better performance |
| 2024 | RDS Proxy | Connection pooling | Improved Lambda performance |
| 2024 | Multi-AZ for Production | High availability | 99.95% SLA |
