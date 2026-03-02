# VitalMatch Backend

This directory contains the AWS Lambda functions and shared modules for the VitalMatch Clinical Trial Matcher backend.

## Structure

```
backend/
├── ai_matching/          # AI-powered medical text matching
│   ├── bedrock_client.py       # AWS Bedrock client wrapper
│   ├── medical_matcher.py      # Medical terminology matching
│   └── match_scorer.py         # Trial scoring and ranking
├── data_ingestion/       # ClinicalTrials.gov data ingestion
│   ├── clinicaltrials_api_client.py  # API client
│   ├── trial_parser.py               # Data parser
│   └── database_storage.py           # RDS storage
├── hard_filter/          # SQL-based hard filtering
│   └── filter_engine.py        # Age, gender, location filters
├── tests/                # Unit and property-based tests
├── ingest_trials.py      # Lambda handler for data ingestion
├── match_trials.py       # Lambda handler for trial matching
└── requirements.txt      # Python dependencies
```

## Lambda Functions

### 1. Match Trials (`match_trials.py`)
**Purpose**: API Gateway endpoint for matching patients with clinical trials

**Trigger**: API Gateway POST /match-trials

**Process**:
1. Validates patient profile (condition, age, gender, location, medical history)
2. Applies hard filters using SQL (age, gender, location)
3. Applies AI-powered soft matching using Amazon Bedrock
4. Scores and ranks trials by match quality
5. Returns top 3-5 matches with explanations

**Environment Variables**:
- `RDS_PROXY_ENDPOINT`: RDS Proxy endpoint
- `DB_NAME`: Database name (default: trials_db)
- `DB_USER`: Database user
- `DB_PASSWORD`: Database password
- `DB_PORT`: Database port (default: 5432)
- `AWS_REGION`: AWS region for Bedrock

**Response Time**: < 15 seconds (target)

### 2. Data Ingestion (`ingest_trials.py`)
**Purpose**: Scheduled ingestion of clinical trial data from ClinicalTrials.gov

**Trigger**: EventBridge scheduled rule (daily at 2 AM UTC)

**Process**:
1. Fetches trials updated in last 24 hours from ClinicalTrials.gov API
2. Parses trial data (NCT ID, title, condition, eligibility, location)
3. Stores/updates trials in RDS PostgreSQL
4. Publishes metrics to CloudWatch
5. Sends SNS alerts on failures

**Environment Variables**:
- `RDS_PROXY_ENDPOINT`: RDS Proxy endpoint
- `DB_NAME`: Database name
- `DB_USER`: Database user
- `DB_PASSWORD`: Database password
- `SNS_ALERT_TOPIC`: SNS topic ARN for alerts

**Execution Time**: ~5 minutes (for 1000 trials)

## Shared Modules

### AI Matching (`ai_matching/`)
- **bedrock_client.py**: Wrapper for AWS Bedrock API calls
- **medical_matcher.py**: Medical terminology matching using Claude 3 Sonnet
- **match_scorer.py**: Combines hard filter results with AI scores

### Data Ingestion (`data_ingestion/`)
- **clinicaltrials_api_client.py**: ClinicalTrials.gov API v2 client
- **trial_parser.py**: Parses and normalizes trial data
- **database_storage.py**: RDS PostgreSQL storage with connection pooling

### Hard Filter (`hard_filter/`)
- **filter_engine.py**: SQL-based filtering by age, gender, location, condition

## Testing

### Run All Tests
```bash
cd backend
pytest
```

### Run Specific Test Categories
```bash
# Unit tests
pytest tests/test_match_scorer.py

# Property-based tests
pytest tests/test_hard_filter_properties.py
pytest tests/test_match_scorer_properties.py
pytest tests/test_exclusion_criteria_properties.py

# Integration tests
pytest tests/test_match_trials_lambda.py
```

### Test Coverage
```bash
pytest --cov=. --cov-report=html
```

## Local Development

### Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### Set Environment Variables
```bash
export RDS_PROXY_ENDPOINT=your-rds-proxy-endpoint
export DB_NAME=trials_db
export DB_USER=postgres
export DB_PASSWORD=your-password
export AWS_REGION=us-east-1
```

### Test Lambda Functions Locally
```bash
# Using AWS SAM
sam local invoke MatchTrialsFunction --event events/match-trials-event.json

# Using Python directly
python -c "from match_trials import lambda_handler; print(lambda_handler({'body': '{...}'}, None))"
```

## Deployment

### Deploy with AWS SAM
```bash
# Build
sam build

# Deploy
sam deploy --guided
```

### Deploy Specific Function
```bash
sam build MatchTrialsFunction
sam deploy
```

## Dependencies

### Production Dependencies
- **requests**: HTTP client for ClinicalTrials.gov API
- **psycopg2-binary**: PostgreSQL database adapter
- **boto3**: AWS SDK (included in Lambda runtime)

### Development Dependencies
- **pytest**: Testing framework
- **hypothesis**: Property-based testing

## Architecture

### Data Flow - Match Trials
```
API Gateway → Lambda (match_trials.py)
                ↓
    Hard Filter (SQL) → RDS PostgreSQL
                ↓
    AI Matching → Amazon Bedrock (Claude 3)
                ↓
    Match Scorer → Ranked Results
                ↓
    API Gateway Response
```

### Data Flow - Data Ingestion
```
EventBridge (Schedule) → Lambda (ingest_trials.py)
                            ↓
    ClinicalTrials.gov API → Parse Trials
                            ↓
    RDS PostgreSQL ← Store/Update
                            ↓
    CloudWatch Metrics + SNS Alerts
```

## Performance Targets

- **Match Trials**: < 15 seconds end-to-end
  - Hard filtering: < 2 seconds
  - AI scoring: < 10 seconds
  - Response formatting: < 1 second

- **Data Ingestion**: < 5 minutes for 1000 trials
  - API fetch: ~2 minutes
  - Parsing: ~30 seconds
  - Database storage: ~2 minutes

## Error Handling

### Match Trials
- **400 Bad Request**: Invalid patient profile (missing fields, invalid values)
- **500 Internal Server Error**: Database connection, Bedrock API, or unexpected errors
- All errors logged to CloudWatch with request ID

### Data Ingestion
- **Partial Failures**: Continues processing, sends warning via SNS
- **Complete Failures**: Sends critical alert via SNS
- All errors logged to CloudWatch with detailed stack traces

## Monitoring

### CloudWatch Metrics
- **Match Trials**: Invocations, Duration, Errors, Throttles
- **Data Ingestion**: TrialsFetched, TrialsParsed, TrialsInserted, IngestionDuration

### CloudWatch Logs
- All Lambda function logs with request IDs
- Structured logging for easy searching

### X-Ray Tracing
- Distributed tracing enabled for performance analysis
- Trace API Gateway → Lambda → RDS → Bedrock

## Security

- **VPC Deployment**: Lambda functions run in private subnets
- **RDS Proxy**: Connection pooling and IAM authentication
- **Secrets Management**: Database credentials in Parameter Store
- **Least Privilege IAM**: Minimal permissions for each function

## Related Documentation

- [Frontend README](../frontend/README.md)
- [Database Schema](../database/README.md)
- [Deployment Guide](../DEPLOYMENT_INSTRUCTIONS.md)
- [API Documentation](../docs/api-gateway-setup.md)
