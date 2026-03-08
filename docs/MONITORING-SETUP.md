# VitalMatch Monitoring and Alerting Setup

## Overview

This document describes the monitoring and alerting infrastructure for the VitalMatch Clinical Trial Matcher system.

## CloudWatch Dashboards

The system includes five comprehensive CloudWatch dashboards:

### 1. System Overview Dashboard
**Name**: `{Environment}-VitalMatch-System-Overview`

Provides a high-level view of the entire system including:
- Lambda invocations and duration
- Lambda errors and concurrent executions
- API Gateway requests and errors
- API Gateway latency
- RDS CPU utilization and connections
- RDS IOPS and storage
- WAF blocked requests
- Recent Lambda errors (log insights)

### 2. Lambda Performance Dashboard
**Name**: `{Environment}-VitalMatch-Lambda-Performance`

Detailed Lambda function metrics:
- Match Trials function: invocations, duration statistics (avg, min, max, p50, p90, p99), errors, throttles, concurrent executions
- Data Ingestion function: invocations, duration, errors
- Duration percentiles over time (log insights)

### 3. API Gateway Dashboard
**Name**: `{Environment}-VitalMatch-API-Gateway`

API Gateway specific metrics:
- Total requests
- 4XX and 5XX errors
- Latency percentiles (avg, p50, p90, p99)
- Integration latency
- Cache hit/miss rates
- Recent API errors (log insights)

### 4. RDS Database Dashboard
**Name**: `{Environment}-VitalMatch-RDS-Database`

Database performance metrics:
- CPU utilization
- Database connections (average and maximum)
- Read/Write IOPS
- Read/Write latency
- Free storage space
- Freeable memory
- Network throughput
- Disk throughput

### 5. Custom Metrics Dashboard
**Name**: `{Environment}-VitalMatch-Custom-Metrics`

Application-specific metrics:
- Total trials processed
- Match score distribution (avg, p50, p90, p99)
- Average trials after hard filtering
- Average matches returned to users
- Bedrock AI invocations
- Trials ingested per run

## CloudWatch Alarms

### Lambda Alarms

#### Match Trials Error Rate Alarm
- **Name**: `{Environment}-vitalmatch-match-trials-error-rate`
- **Condition**: Error rate > 5%
- **Evaluation**: 5 minutes
- **Action**: Send notification to System Alert SNS topic

#### Match Trials Duration Alarm
- **Name**: `{Environment}-vitalmatch-match-trials-duration`
- **Condition**: Average duration > 15 seconds
- **Evaluation**: 5 minutes
- **Action**: Send notification to System Alert SNS topic

#### Data Ingestion Error Alarm
- **Name**: `{Environment}-vitalmatch-data-ingestion-errors`
- **Condition**: Any errors
- **Evaluation**: 5 minutes
- **Action**: Send notification to System Alert SNS topic

#### Data Ingestion Duration Alarm
- **Name**: `{Environment}-vitalmatch-data-ingestion-duration`
- **Condition**: Average duration > 270 seconds (90% of timeout)
- **Evaluation**: 5 minutes
- **Action**: Send notification to System Alert SNS topic

### RDS Alarms

#### RDS CPU Utilization Alarm
- **Name**: `{Environment}-vitalmatch-rds-cpu-high`
- **Condition**: Average CPU > 80%
- **Evaluation**: 10 minutes (2 periods of 5 minutes)
- **Action**: Send notification to System Alert SNS topic

#### RDS Storage Alarm
- **Name**: `{Environment}-vitalmatch-rds-storage-low`
- **Condition**: Free storage < 20 GB (20% of 100 GB)
- **Evaluation**: 5 minutes
- **Action**: Send notification to System Alert SNS topic

#### RDS Connections Alarm
- **Name**: `{Environment}-vitalmatch-rds-connections-high`
- **Condition**: Average connections > 80
- **Evaluation**: 10 minutes (2 periods of 5 minutes)
- **Action**: Send notification to System Alert SNS topic

#### RDS Read Latency Alarm
- **Name**: `{Environment}-vitalmatch-rds-read-latency-high`
- **Condition**: Average read latency > 100ms
- **Evaluation**: 10 minutes (2 periods of 5 minutes)
- **Action**: Send notification to System Alert SNS topic

#### RDS Write Latency Alarm
- **Name**: `{Environment}-vitalmatch-rds-write-latency-high`
- **Condition**: Average write latency > 100ms
- **Evaluation**: 10 minutes (2 periods of 5 minutes)
- **Action**: Send notification to System Alert SNS topic

### API Gateway Alarms

#### API Gateway 4XX Error Alarm
- **Name**: `{Environment}-vitalmatch-api-4xx-errors`
- **Condition**: Sum of 4XX errors > 50
- **Evaluation**: 5 minutes
- **Action**: Send notification to System Alert SNS topic

#### API Gateway 5XX Error Alarm
- **Name**: `{Environment}-vitalmatch-api-5xx-errors`
- **Condition**: Sum of 5XX errors > 10
- **Evaluation**: 5 minutes
- **Action**: Send notification to System Alert SNS topic

#### API Gateway Latency Alarm
- **Name**: `{Environment}-vitalmatch-api-latency`
- **Condition**: Average latency > 3 seconds
- **Evaluation**: 5 minutes
- **Action**: Send notification to System Alert SNS topic

### WAF Alarms

#### WAF Block Rate Alarm
- **Name**: `{Environment}-vitalmatch-waf-high-block-rate`
- **Condition**: Blocked requests > 1000 per hour
- **Evaluation**: 1 hour
- **Action**: Send notification to WAF Alert SNS topic

## X-Ray Tracing

### Enabled Components

X-Ray tracing is enabled for:
- **Match Trials Lambda Function**: Active tracing for all invocations
- **Data Ingestion Lambda Function**: Active tracing for all invocations
- **API Gateway**: Tracing enabled for all stages (dev, staging, prod)

### Sampling Rules

X-Ray sampling rules are configured to balance cost and observability:

1. **Match Trials Function** (Priority 100)
   - Fixed target: 1 request per second
   - Sample rate: 10% of additional requests
   - Service: `*vitalmatch-match-trials*`

2. **Data Ingestion Function** (Priority 200)
   - Fixed target: 1 request per second
   - Sample rate: 100% (sample all invocations)
   - Service: `*vitalmatch-data-ingestion*`

3. **API Gateway** (Priority 300)
   - Fixed target: 1 request per second
   - Sample rate: 10% of additional requests
   - Service: `*vitalmatch-api*`

4. **Default Rule** (Priority 1000)
   - Fixed target: 1 request per second
   - Sample rate: 5% of additional requests
   - Applies to all other services

### Applying X-Ray Sampling Rules

To apply the X-Ray sampling rules:

```bash
# Create sampling rules from the configuration file
aws xray create-sampling-rule --cli-input-json file://xray-sampling-rules.json --region us-east-1

# Or update existing rules
aws xray update-sampling-rule --cli-input-json file://xray-sampling-rules.json --region us-east-1
```

**Note**: X-Ray sampling rules are global and apply across all regions. You only need to create them once.

### Viewing X-Ray Traces

1. Open the AWS X-Ray console
2. Navigate to "Service Map" to see the architecture visualization
3. Navigate to "Traces" to see individual request traces
4. Use filters to find specific traces:
   - Filter by URL: `/match-trials`
   - Filter by response time: `responsetime > 3`
   - Filter by errors: `error = true`

## SNS Topics

### System Alert Topic
- **Name**: `{Environment}-vitalmatch-system-alerts`
- **Purpose**: Receives all system-level alerts (Lambda, RDS, API Gateway)
- **Subscribers**: Configure email or other notification endpoints

### WAF Alert Topic
- **Name**: `{Environment}-vitalmatch-waf-alerts`
- **Purpose**: Receives WAF security alerts
- **Subscribers**: Configure email or other notification endpoints for security team

## Setting Up Email Notifications

To receive email notifications for alarms:

```bash
# Subscribe to System Alert topic
aws sns subscribe \
  --topic-arn arn:aws:sns:REGION:ACCOUNT_ID:ENV-vitalmatch-system-alerts \
  --protocol email \
  --notification-endpoint your-email@example.com

# Subscribe to WAF Alert topic
aws sns subscribe \
  --topic-arn arn:aws:sns:REGION:ACCOUNT_ID:ENV-vitalmatch-waf-alerts \
  --protocol email \
  --notification-endpoint security-team@example.com

# Confirm the subscription by clicking the link in the confirmation email
```

## Custom Metrics

The application emits custom CloudWatch metrics in the `VitalMatch` namespace:

### Metrics

1. **TrialsProcessed**
   - Unit: Count
   - Dimension: Environment
   - Description: Total number of trials processed in a match request

2. **MatchScore**
   - Unit: None (0-1 scale)
   - Dimension: Environment
   - Description: Match score for each trial-patient pair

3. **HardFilteredTrials**
   - Unit: Count
   - Dimension: Environment
   - Description: Number of trials remaining after hard filtering

4. **MatchesReturned**
   - Unit: Count
   - Dimension: Environment
   - Description: Number of matches returned to the user

5. **BedrockInvocations**
   - Unit: Count
   - Dimension: Environment
   - Description: Number of Bedrock API calls made

6. **DataIngestionTrialsCount**
   - Unit: Count
   - Dimension: Environment
   - Description: Number of trials ingested in each data ingestion run

### Emitting Custom Metrics

Example code for emitting custom metrics from Lambda:

```python
import boto3
from datetime import datetime

cloudwatch = boto3.client('cloudwatch')

def put_custom_metric(metric_name, value, unit='Count'):
    """Emit a custom CloudWatch metric"""
    cloudwatch.put_metric_data(
        Namespace='VitalMatch',
        MetricData=[
            {
                'MetricName': metric_name,
                'Value': value,
                'Unit': unit,
                'Timestamp': datetime.utcnow(),
                'Dimensions': [
                    {
                        'Name': 'Environment',
                        'Value': os.environ.get('ENVIRONMENT', 'dev')
                    }
                ]
            }
        ]
    )

# Usage examples
put_custom_metric('TrialsProcessed', 1247)
put_custom_metric('MatchScore', 0.92, unit='None')
put_custom_metric('HardFilteredTrials', 43)
put_custom_metric('MatchesReturned', 5)
put_custom_metric('BedrockInvocations', 1)
```

## Log Insights Queries

### Useful CloudWatch Logs Insights Queries

#### Lambda Error Analysis
```
fields @timestamp, @message
| filter @message like /ERROR/
| sort @timestamp desc
| limit 50
```

#### Lambda Performance Analysis
```
fields @timestamp, @duration, @billedDuration, @memorySize, @maxMemoryUsed
| stats avg(@duration), min(@duration), max(@duration), pct(@duration, 50), pct(@duration, 90), pct(@duration, 99)
```

#### API Gateway Error Analysis
```
fields @timestamp, status, @message
| filter status >= 400
| stats count() by status
| sort status
```

#### Match Trials Processing Time
```
fields @timestamp, @message
| filter @message like /processing_time/
| parse @message /processing_time: (?<time>\d+)/
| stats avg(time), min(time), max(time), pct(time, 50), pct(time, 90), pct(time, 99)
```

## Monitoring Best Practices

1. **Review dashboards daily** to identify trends and anomalies
2. **Set up SNS email subscriptions** for critical alarms
3. **Use X-Ray traces** to debug performance issues and errors
4. **Monitor custom metrics** to understand application behavior
5. **Adjust alarm thresholds** based on actual usage patterns
6. **Review CloudWatch Logs** regularly for errors and warnings
7. **Set up log retention policies** to manage costs (currently 30 days)
8. **Use CloudWatch Insights** for ad-hoc log analysis

## Cost Optimization

- X-Ray sampling rules are configured to balance observability with cost
- CloudWatch Logs retention is set to 30 days
- Dashboards use 5-minute periods for most metrics to reduce API calls
- Custom metrics are emitted only when necessary

## Troubleshooting

### High Lambda Error Rate
1. Check CloudWatch Logs for error messages
2. Use X-Ray traces to identify the failing component
3. Review recent code deployments
4. Check RDS connection pool exhaustion

### High API Latency
1. Check Lambda duration metrics
2. Review RDS query performance
3. Use X-Ray to identify slow components
4. Check Bedrock API response times

### High RDS CPU
1. Review slow query logs
2. Check for missing indexes
3. Analyze query patterns in CloudWatch Logs
4. Consider scaling up RDS instance

### Low RDS Storage
1. Review database growth trends
2. Clean up old data if applicable
3. Increase allocated storage
4. Enable storage auto-scaling

## Additional Resources

- [AWS CloudWatch Documentation](https://docs.aws.amazon.com/cloudwatch/)
- [AWS X-Ray Documentation](https://docs.aws.amazon.com/xray/)
- [CloudWatch Logs Insights Query Syntax](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/CWL_QuerySyntax.html)
- [X-Ray Sampling Rules](https://docs.aws.amazon.com/xray/latest/devguide/xray-console-sampling.html)
