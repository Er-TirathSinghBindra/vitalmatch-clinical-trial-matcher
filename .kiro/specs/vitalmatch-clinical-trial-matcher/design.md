# VitalMatch - Clinical Trial Matcher - Design Document

## System Architecture

### Overview
VitalMatch uses a hybrid architecture combining SQL-based hard filtering with AI-powered soft matching to provide intelligent clinical trial recommendations. The system follows a three-layer approach: data ingestion, intelligent filtering, and result presentation.

### AWS Architecture Diagram
```
┌─────────────────────────────────────────────────────────────────────┐
│                          AWS Cloud                                  │
│                                                                     │
│  ┌──────────────┐         ┌─────────────────────────────────────┐ │
│  │  AWS WAF     │────────▶│         CloudFront                  │ │
│  │ (Firewall)   │         │      (Edge Protection)              │ │
│  └──────────────┘         └─────────────────────────────────────┘ │
│         │                              │                           │
│         │                              ▼                           │
│         │                    ┌──────────────────┐                 │
│         │                    │   S3 Bucket      │                 │
│         │                    │  (Static Web)    │                 │
│         │                    └──────────────────┘                 │
│         │                                                          │
│         ▼                                                          │
│  ┌──────────────┐                                                 │
│  │ API Gateway  │                                                 │
│  │  (REST API)  │                                                 │
│  └──────────────┘                                                 │
│         │                                                          │
│         │                                                          │
│  ┌──────▼──────────────────────────────────────────────────────┐ │
│  │                        VPC                                   │ │
│  │                                                              │ │
│  │  ┌────────────────────────────────────────────────────────┐ │ │
│  │  │              Private Subnet                            │ │ │
│  │  │                                                        │ │ │
│  │  │  ┌─────────────────────┐    ┌────────────────────┐   │ │ │
│  │  │  │  Lambda Function    │    │  Security Group    │   │ │ │
│  │  │  │  Filter Engine &    │◀───│  (RDS Access)      │   │ │ │
│  │  │  │  Match Logic        │    └────────────────────┘   │ │ │
│  │  │  └─────────────────────┘              │              │ │ │
│  │  │            │                           ▼              │ │ │
│  │  │            │                  ┌────────────────────┐ │ │ │
│  │  │            │                  │  RDS PostgreSQL    │ │ │ │
│  │  │            │                  │  (Trial Data)      │ │ │ │
│  │  │            │                  └────────────────────┘ │ │ │
│  │  │            │                           ▲              │ │ │
│  │  │            │                           │              │ │ │
│  │  │  ┌─────────▼───────────┐              │              │ │ │
│  │  │  │  Lambda Function    │              │              │ │ │
│  │  │  │  Data Ingestion     │──────────────┘              │ │ │
│  │  │  └─────────────────────┘                             │ │ │
│  │  │            ▲                                          │ │ │
│  │  └────────────┼──────────────────────────────────────────┘ │ │
│  │               │                                            │ │
│  └───────────────┼────────────────────────────────────────────┘ │
│                  │                                              │
│         ┌────────┴────────┐                                     │
│         │  EventBridge    │                                     │
│         │  (Cron Schedule)│                                     │
│         └─────────────────┘                                     │
│                  │                                              │
│                  └──────────────────────────────────────────────┼──▶
│                                                                 │   ClinicalTrials.gov
└─────────────────────────────────────────────────────────────────┘   API
```

## AWS Component Design

### 0. Network Architecture - VPC Configuration
**Purpose**: Secure network isolation for Lambda functions and RDS database

**AWS Services**:
- **VPC**: Isolated virtual network for all backend resources
- **Private Subnets**: Host Lambda functions and RDS instances
- **Security Groups**: Firewall rules controlling resource access
- **NAT Gateway**: Outbound internet access for Lambda functions (for ClinicalTrials.gov API)
- **VPC Flow Logs**: Network traffic monitoring and audit

**VPC Configuration**:
```yaml
VPC:
  CIDR: 10.0.0.0/16
  
Private Subnets:
  - Subnet A: 10.0.1.0/24 (AZ: us-east-1a)
  - Subnet B: 10.0.2.0/24 (AZ: us-east-1b)
  
Security Groups:
  Lambda-SG:
    Inbound: None (Lambda doesn't accept inbound)
    Outbound:
      - RDS-SG on port 5432 (PostgreSQL)
      - 0.0.0.0/0 on port 443 (HTTPS for external APIs)
  
  RDS-SG:
    Inbound:
      - Lambda-SG on port 5432
    Outbound: None
    
NAT Gateway:
  - Deployed in public subnet for Lambda outbound internet access
  - Required for ClinicalTrials.gov API calls
```

**Security Considerations**:
- Lambda functions have no public IP addresses
- RDS database is not publicly accessible
- All traffic between Lambda and RDS stays within VPC
- VPC Flow Logs capture all network traffic for audit

### 0.5. Security Layer - AWS WAF
**Purpose**: Protect CloudFront and API Gateway from common web attacks

**AWS Services**:
- **AWS WAF**: Web Application Firewall with managed and custom rules
- **AWS Shield Standard**: DDoS protection (included by default)

**WAF Configuration**:
```yaml
WAF Rules:
  - AWS Managed Rules - Core Rule Set (CRS)
  - AWS Managed Rules - Known Bad Inputs
  - SQL Injection Protection
  - Cross-Site Scripting (XSS) Protection
  - Rate Limiting: 2000 requests per 5 minutes per IP
  - Geographic Restrictions: Optional (if needed)
  
WAF Associations:
  - CloudFront Distribution (edge protection)
  - API Gateway (API protection)
  
Logging:
  - All blocked requests logged to CloudWatch
  - Alerts sent via SNS for suspicious patterns
```

### 1. Frontend - S3 + CloudFront
**Purpose**: Host static React web application with global CDN

**AWS Services**:
- **S3 Bucket**: Static website hosting for React build
- **CloudFront**: Global CDN for fast loading, SSL termination
- **Route 53**: Custom domain management

**Configuration**:
```yaml
S3 Bucket:
  - Static website hosting enabled
  - Public read access for web assets
  - Versioning enabled for deployments

CloudFront Distribution:
  - Origin: S3 bucket
  - SSL certificate via ACM
  - Caching policies for static assets
  - Error pages for SPA routing
```

### 2. API Layer - API Gateway + Lambda
**Purpose**: Serverless REST API for trial matching

**AWS Services**:
- **API Gateway**: REST API endpoints with throttling
- **Lambda Functions**: Serverless compute for business logic
- **Lambda Layers**: Shared libraries (NLP models, utilities)
- **VPC Integration**: Lambda functions deployed in VPC private subnet

**API Gateway Configuration**:
```yaml
API Gateway:
  Type: REST API
  Throttling:
    Rate Limit: 1000 requests/second
    Burst Limit: 2000 requests
  CORS: Enabled for web application
  Authorization: API Key (optional for public access)
  Logging: Full request/response logging to CloudWatch
  WAF: Protected by AWS WAF rules
```

**Lambda Functions**:
```python
# Function 1: Trial Matching Engine
def lambda_match_trials(event, context):
    patient_profile = json.loads(event['body'])
    
    # Hard filtering via RDS
    hard_filtered = query_rds_trials(patient_profile)
    
    # Soft filtering via Bedrock/SageMaker
    ai_scored = score_trials_with_ai(hard_filtered, patient_profile)
    
    return {
        'statusCode': 200,
        'body': json.dumps(ai_scored)
    }

# Function 2: Data Ingestion
def lambda_ingest_trials(event, context):
    # Triggered by EventBridge schedule
    trials_data = fetch_clinicaltrials_api()
    store_in_rds(trials_data)
```

**Lambda VPC Configuration**:
```yaml
Lambda Configuration:
  VPC: Main VPC
  Subnets: Private Subnets A & B
  Security Group: Lambda-SG
  Memory: 1024 MB (matching engine), 512 MB (ingestion)
  Timeout: 30 seconds (matching), 300 seconds (ingestion)
  Environment Variables:
    - RDS_ENDPOINT: From Parameter Store
    - DB_NAME: trials_db
    - BEDROCK_MODEL_ID: anthropic.claude-3-sonnet
```

### 3. Database - RDS PostgreSQL
**Purpose**: Managed relational database for structured trial data

**AWS Services**:
- **RDS PostgreSQL**: Managed database with automated backups
- **RDS Proxy**: Connection pooling for Lambda functions
- **Parameter Store**: Database credentials management
- **VPC Deployment**: Database in private subnet with security group protection

**RDS Configuration**:
```yaml
RDS Instance:
  Engine: PostgreSQL 15
  Instance Class: db.t3.medium (production), db.t3.micro (dev)
  Storage: 100 GB SSD with auto-scaling enabled
  Multi-AZ: Enabled for high availability
  Backup: Automated daily backups, 7-day retention
  Encryption: Enabled using AWS KMS
  VPC: Private subnet deployment
  Security Group: RDS-SG (only Lambda access)
  
RDS Proxy:
  Purpose: Connection pooling for Lambda functions
  Max Connections: 100
  Idle Timeout: 30 minutes
  Authentication: IAM-based from Lambda
```

**Database Schema** (Updated for AWS):
```sql
-- Optimized for RDS PostgreSQL
CREATE TABLE trials (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    condition TEXT NOT NULL,
    min_age INTEGER,
    max_age INTEGER,
    gender_criteria TEXT,
    location TEXT,
    inclusion_text TEXT,
    exclusion_text TEXT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_condition_age ON trials(condition, min_age, max_age);
CREATE INDEX idx_location ON trials USING GIN(to_tsvector('english', location));
CREATE INDEX idx_inclusion_text ON trials USING GIN(to_tsvector('english', inclusion_text));
```

### 4. AI/NLP Services - Amazon Bedrock
**Purpose**: Managed AI services for medical text processing

**AWS Services**:
- **Amazon Bedrock**: Access to foundation models (Claude, Titan)
- **Amazon Comprehend Medical**: Medical entity extraction
- **SageMaker**: Custom model hosting if needed

**AI Processing Pipeline**:
```python
import boto3

def process_medical_text_with_bedrock(patient_history, trial_criteria):
    bedrock = boto3.client('bedrock-runtime')
    
    prompt = f"""
    Patient Medical History: {patient_history}
    Trial Inclusion Criteria: {trial_criteria}
    
    Analyze if this patient matches the trial criteria. 
    Return a score from 0-1 and explanation.
    """
    
    response = bedrock.invoke_model(
        modelId='anthropic.claude-3-sonnet-20240229-v1:0',
        body=json.dumps({
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': 500
        })
    )
    
    return parse_ai_response(response)
```

### 5. Data Ingestion - EventBridge + Lambda
**Purpose**: Scheduled data updates from ClinicalTrials.gov

**AWS Services**:
- **EventBridge**: Scheduled triggers (daily/weekly)
- **Lambda**: Data fetching and processing
- **Systems Manager Parameter Store**: API keys and configuration
- **SNS**: Error notifications for failed ingestion

**EventBridge Configuration**:
```yaml
EventBridge Rule:
  Name: DailyTrialDataIngestion
  Schedule: cron(0 2 * * ? *)  # Daily at 2 AM UTC
  Target: Data Ingestion Lambda Function
  Retry Policy: 3 attempts with exponential backoff
```

**Data Ingestion Flow**:
```python
import boto3
import requests
from datetime import datetime, timedelta

def lambda_ingest_trials(event, context):
    """
    Scheduled data ingestion from ClinicalTrials.gov API
    """
    sns = boto3.client('sns')
    
    try:
        # Fetch recent trials from ClinicalTrials.gov
        trials_data = fetch_clinicaltrials_api()
        
        # Parse and normalize data
        normalized_trials = parse_trial_data(trials_data)
        
        # Store in RDS via connection pool
        store_in_rds(normalized_trials)
        
        # Log success metrics
        log_ingestion_metrics(len(normalized_trials))
        
        return {
            'statusCode': 200,
            'message': f'Successfully ingested {len(normalized_trials)} trials'
        }
        
    except Exception as e:
        # Send SNS alert on failure
        sns.publish(
            TopicArn=os.environ['SNS_ALERT_TOPIC'],
            Subject='Trial Data Ingestion Failed',
            Message=f'Error: {str(e)}'
        )
        raise

def fetch_clinicaltrials_api():
    """
    Fetch trials from ClinicalTrials.gov API with rate limiting
    """
    base_url = "https://clinicaltrials.gov/api/v2/studies"
    
    # Fetch trials updated in last 24 hours
    params = {
        'query.term': 'AREA[LastUpdatePostDate]RANGE[MIN,MAX]',
        'pageSize': 1000,
        'format': 'json'
    }
    
    response = requests.get(base_url, params=params, timeout=30)
    response.raise_for_status()
    
    return response.json()

def parse_trial_data(raw_data):
    """
    Parse and normalize trial data from API response
    """
    trials = []
    
    for study in raw_data.get('studies', []):
        trial = {
            'id': study['protocolSection']['identificationModule']['nctId'],
            'title': study['protocolSection']['identificationModule']['officialTitle'],
            'condition': extract_conditions(study),
            'min_age': extract_min_age(study),
            'max_age': extract_max_age(study),
            'gender_criteria': extract_gender(study),
            'location': extract_locations(study),
            'inclusion_text': extract_inclusion_criteria(study),
            'exclusion_text': extract_exclusion_criteria(study)
        }
        trials.append(trial)
    
    return trials
```

**ClinicalTrials.gov API Integration**:
```yaml
API Details:
  Base URL: https://clinicaltrials.gov/api/v2/studies
  Authentication: None (public API)
  Rate Limits: 
    - 1000 requests per hour
    - Implement exponential backoff
  Response Format: JSON or XML
  Pagination: 1000 records per page
  
Error Handling:
  - Retry failed requests 3 times with exponential backoff
  - Log all API errors to CloudWatch
  - Send SNS alerts for persistent failures
  - Continue processing successful records even if some fail
```

### 6. Monitoring and Logging
**AWS Services**:
- **CloudWatch**: Metrics, logs, and alarms
- **X-Ray**: Distributed tracing for Lambda functions
- **SNS**: Error notifications and alerts
- **VPC Flow Logs**: Network traffic monitoring

**CloudWatch Configuration**:
```yaml
CloudWatch Metrics:
  Lambda Metrics:
    - Invocation count
    - Duration
    - Error rate
    - Concurrent executions
    - Throttles
  
  RDS Metrics:
    - CPU utilization
    - Database connections
    - Read/Write IOPS
    - Storage space
  
  API Gateway Metrics:
    - Request count
    - Latency (p50, p99)
    - 4XX/5XX errors
    - Cache hit/miss rate

CloudWatch Alarms:
  - Lambda error rate > 5%
  - API Gateway latency > 3 seconds
  - RDS CPU > 80%
  - RDS storage < 20% free
  - WAF blocked requests > 1000/hour

CloudWatch Logs:
  - All Lambda function logs
  - API Gateway access logs
  - VPC Flow Logs
  - WAF logs
  - Retention: 30 days

X-Ray Tracing:
  - Enabled for all Lambda functions
  - Trace API Gateway requests end-to-end
  - Identify performance bottlenecks
  - Debug errors with full request context

SNS Topics:
  - Critical Alerts: Immediate notification for system failures
  - Warning Alerts: Non-critical issues requiring attention
  - Info Notifications: Successful data ingestion, deployments
```

## User Interface Design

### User Interaction Flow

**Step 1: Patient Profile Form**
- Simple web form with clear sections:
  - **Medical Condition**: Dropdown with common conditions + free text option
  - **Basic Info**: Age (number input), Gender (radio buttons), Location (text with autocomplete)
  - **Medical History**: Large text area with helpful prompts like "List any chronic conditions, medications, previous treatments..."
  - **Search Preferences**: Distance radius slider (10-100 miles)

**Step 2: Processing Indicator**
- Progress bar showing: "Searching 1,247 trials → Filtering by age/location → AI analysis of 43 candidates"
- Estimated time: "This usually takes 10-15 seconds"

**Step 3: Results Display**
- **Summary Card**: "Found 4 high-quality matches out of 1,247 trials"
- **Match Cards** (one per trial):
  ```
  ┌─────────────────────────────────────────────────────────┐
  │ 🎯 92% Match - Phase II Study of Drug X in NSCLC       │
  │                                                         │
  │ ✅ Perfect fit: Trial seeks patients with smoking history│
  │ ✅ Age requirement: 18-70 (you: 65)                    │
  │ ✅ Location: Memorial Sloan Kettering, NYC (12 miles)  │
  │ ⚠️  Note: Hypertension will require extra monitoring    │
  │                                                         │
  │ [View Full Details] [Save Trial] [Contact Info]        │
  └─────────────────────────────────────────────────────────┘
  ```

**Step 4: Detailed Trial View**
- Full trial description
- Complete eligibility criteria (highlighted matches)
- Contact information and next steps
- "Why this matches you" explanation

### Interface Types

**Primary Interface: Web Application**
- Responsive design for desktop/tablet/mobile
- Clean, medical-professional styling
- Accessibility compliant (WCAG 2.1)

**Secondary Interface: API for Healthcare Providers**
- RESTful API for integration into EMR systems
- Bulk patient processing capabilities
- Structured data exchange

## API Design

### Endpoints

**POST /api/match-trials**
```json
{
  "patient_profile": {
    "condition": "Non-small cell lung cancer",
    "age": 65,
    "gender": "Male",
    "location": "New York",
    "distance_miles": 50,
    "medical_history": "High blood pressure, history of smoking"
  }
}
```

**Response**:
```json
{
  "matches": [
    {
      "trial_id": "NCT12345678",
      "title": "Phase II Study of Drug X in NSCLC Patients",
      "match_score": 0.92,
      "explanation": "High match: Trial specifically seeks patients with smoking history. Age and location criteria met.",
      "key_criteria": [
        "✅ History of smoking (required)",
        "✅ Age 18-70 (patient: 65)",
        "✅ Location: New York area",
        "⚠️ Hypertension noted - may require monitoring"
      ]
    }
  ],
  "total_trials_considered": 1247,
  "hard_filtered_count": 43,
  "processing_time_ms": 8500
}
```

## Technology Stack

### Frontend (AWS)
- **S3**: Static website hosting for React application
- **CloudFront**: Global CDN with SSL termination
- **Route 53**: DNS management and custom domains
- **Certificate Manager (ACM)**: SSL/TLS certificates

### Backend (AWS)
- **API Gateway**: REST API with request/response transformation
- **Lambda**: Serverless compute for all business logic
- **RDS PostgreSQL**: Managed relational database
- **RDS Proxy**: Connection pooling for Lambda functions

### AI/ML Services (AWS)
- **Amazon Bedrock**: Foundation models (Claude, Titan) for medical text analysis
- **Amazon Comprehend Medical**: Medical entity extraction and PHI detection
- **SageMaker**: Custom model hosting if needed

### Data & Storage (AWS)
- **RDS PostgreSQL**: Primary database for trial data
- **S3**: Static assets, data backups, logs
- **Systems Manager Parameter Store**: Configuration and secrets

### Monitoring & Operations (AWS)
- **CloudWatch**: Metrics, logs, alarms, and dashboards
- **X-Ray**: Distributed tracing and performance monitoring
- **SNS**: Notifications and alerts
- **EventBridge**: Scheduled data ingestion triggers

### Security (AWS)
- **IAM**: Role-based access control
- **VPC**: Network isolation
- **Security Groups**: Firewall rules
- **AWS WAF**: Web application firewall for API Gateway

## Correctness Properties

### Property 1: Hard Filter Accuracy
**Validates: Requirements 2.1, 2.2**
```python
def test_hard_filter_accuracy(patient_profile, trial_database):
    """
    Property: All trials returned by hard filter must satisfy basic eligibility criteria
    """
    filtered_trials = hard_filter.filter_trials(patient_profile)
    
    for trial in filtered_trials:
        assert trial.min_age <= patient_profile.age <= trial.max_age
        assert trial.gender_criteria in [patient_profile.gender, 'All', None]
        assert location_within_distance(trial.location, patient_profile.location, patient_profile.distance_miles)
```

### Property 2: Match Score Consistency
**Validates: Requirements 3.1, 3.2**
```python
def test_match_score_consistency(patient_profile, trials):
    """
    Property: Higher match scores must correspond to better criterion alignment
    """
    scored_trials = [(trial, calculate_match_score(trial, patient_profile)) for trial in trials]
    scored_trials.sort(key=lambda x: x[1], reverse=True)
    
    for i in range(len(scored_trials) - 1):
        higher_scored = scored_trials[i]
        lower_scored = scored_trials[i + 1]
        
        # Higher scored trial should have better or equal criterion matches
        assert count_matching_criteria(higher_scored[0], patient_profile) >= \
               count_matching_criteria(lower_scored[0], patient_profile)
```

### Property 3: Exclusion Criteria Enforcement
**Validates: Requirements 2.5**
```python
def test_exclusion_criteria_enforcement(patient_profile, trials):
    """
    Property: Trials with strong exclusion matches should receive very low scores
    """
    for trial in trials:
        exclusion_match = check_exclusion_criteria(trial.exclusion_text, patient_profile.medical_history)
        match_score = calculate_match_score(trial, patient_profile)
        
        if exclusion_match > 0.8:  # Strong exclusion match
            assert match_score < 0.3  # Should result in low overall score
```

## Testing Strategy

### Unit Tests
- Individual component testing (parsers, filters, scorers)
- Mock external API calls
- Database operation testing

### Integration Tests
- End-to-end API testing
- Database integration testing
- External API integration testing

### Property-Based Tests
- Use Hypothesis for generating diverse patient profiles
- Test scoring consistency across input variations
- Validate filter accuracy with random trial data

### Performance Tests
- Load testing with 1000+ concurrent requests
- Database query performance testing
- Memory usage profiling for large datasets

## Security Considerations

### Data Privacy
- No storage of actual patient data beyond session
- Anonymized logging and analytics
- HIPAA compliance considerations for healthcare deployment
- All patient queries encrypted in transit using TLS 1.2+
- No PHI (Protected Health Information) stored in logs

### API Security
- Rate limiting to prevent abuse (2000 requests per 5 minutes per IP)
- Input validation and sanitization on all API endpoints
- SQL injection prevention through parameterized queries
- AWS WAF protection against common web attacks
- API Gateway throttling to prevent DDoS
- CORS configuration to restrict allowed origins

### Network Security
- Lambda functions deployed in private subnets with no public IPs
- RDS database not publicly accessible
- Security groups enforce least privilege access
- VPC Flow Logs monitor all network traffic
- NAT Gateway for controlled outbound internet access
- All inter-service communication within VPC

### IAM and Access Control
```yaml
IAM Roles:
  Lambda Execution Role:
    Permissions:
      - RDS Proxy connection
      - Bedrock model invocation
      - CloudWatch Logs write
      - X-Ray tracing
      - Parameter Store read (for secrets)
    
  Data Ingestion Lambda Role:
    Permissions:
      - RDS write access
      - SNS publish (for alerts)
      - CloudWatch Logs write
      - Internet access via NAT Gateway
  
  RDS Access:
    - IAM database authentication enabled
    - No hardcoded credentials
    - Secrets stored in Parameter Store with encryption
```

### Compliance Considerations
- **HIPAA**: System designed with HIPAA compliance in mind
  - Encryption at rest and in transit
  - Audit logging enabled
  - Access controls and authentication
  - No PHI storage (queries only, no patient records)
- **Data Retention**: Logs retained for 30 days, backups for 7 days
- **Audit Trail**: All API requests logged with timestamps and user context

## AWS Deployment Strategy

### Development Environment
- **AWS SAM**: Infrastructure as Code for Lambda functions
- **LocalStack**: Local AWS service emulation for development
- **RDS Dev Instance**: Small instance for development database
- **S3 Dev Bucket**: Development static hosting

### Production Environment
- **Multi-AZ RDS**: High availability database setup
- **Lambda Provisioned Concurrency**: Reduced cold starts
- **CloudFront Global Distribution**: Edge locations worldwide
- **Auto Scaling**: API Gateway and Lambda auto-scaling
- **Backup Strategy**: RDS automated backups, S3 versioning

### Infrastructure as Code (AWS CDK/SAM)
```yaml
# template.yaml (AWS SAM)
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Parameters:
  Environment:
    Type: String
    Default: dev
    AllowedValues: [dev, staging, prod]

Resources:
  # VPC Configuration
  VPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: 10.0.0.0/16
      EnableDnsHostnames: true
      EnableDnsSupport: true
      Tags:
        - Key: Name
          Value: !Sub ${Environment}-vitalmatch-vpc

  PrivateSubnetA:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: 10.0.1.0/24
      AvailabilityZone: !Select [0, !GetAZs '']

  PrivateSubnetB:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: 10.0.2.0/24
      AvailabilityZone: !Select [1, !GetAZs '']

  # Security Groups
  LambdaSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Security group for Lambda functions
      VpcId: !Ref VPC
      SecurityGroupEgress:
        - IpProtocol: tcp
          FromPort: 5432
          ToPort: 5432
          DestinationSecurityGroupId: !Ref RDSSecurityGroup
        - IpProtocol: tcp
          FromPort: 443
          ToPort: 443
          CidrIp: 0.0.0.0/0

  RDSSecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupDescription: Security group for RDS database
      VpcId: !Ref VPC
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 5432
          ToPort: 5432
          SourceSecurityGroupId: !Ref LambdaSecurityGroup

  # WAF Configuration
  WebACL:
    Type: AWS::WAFv2::WebACL
    Properties:
      Scope: REGIONAL
      DefaultAction:
        Allow: {}
      Rules:
        - Name: AWSManagedRulesCommonRuleSet
          Priority: 1
          Statement:
            ManagedRuleGroupStatement:
              VendorName: AWS
              Name: AWSManagedRulesCommonRuleSet
          OverrideAction:
            None: {}
          VisibilityConfig:
            SampledRequestsEnabled: true
            CloudWatchMetricsEnabled: true
            MetricName: AWSManagedRulesCommonRuleSetMetric
        - Name: RateLimitRule
          Priority: 2
          Statement:
            RateBasedStatement:
              Limit: 2000
              AggregateKeyType: IP
          Action:
            Block: {}
          VisibilityConfig:
            SampledRequestsEnabled: true
            CloudWatchMetricsEnabled: true
            MetricName: RateLimitMetric

  # API Gateway
  TrialMatcherAPI:
    Type: AWS::Serverless::Api
    Properties:
      StageName: !Ref Environment
      Cors:
        AllowMethods: "'GET,POST,OPTIONS'"
        AllowHeaders: "'content-type'"
        AllowOrigin: "'*'"
      TracingEnabled: true
      MethodSettings:
        - ResourcePath: '/*'
          HttpMethod: '*'
          LoggingLevel: INFO
          DataTraceEnabled: true
          MetricsEnabled: true

  # Lambda Functions
  MatchTrialsFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: src/
      Handler: match_trials.lambda_handler
      Runtime: python3.11
      MemorySize: 1024
      Timeout: 30
      VpcConfig:
        SecurityGroupIds:
          - !Ref LambdaSecurityGroup
        SubnetIds:
          - !Ref PrivateSubnetA
          - !Ref PrivateSubnetB
      Environment:
        Variables:
          RDS_PROXY_ENDPOINT: !GetAtt RDSProxy.Endpoint
          DB_NAME: trials_db
          BEDROCK_MODEL_ID: anthropic.claude-3-sonnet-20240229-v1:0
      Policies:
        - AWSLambdaVPCAccessExecutionRole
        - Version: '2012-10-17'
          Statement:
            - Effect: Allow
              Action:
                - rds-db:connect
                - bedrock:InvokeModel
                - comprehendmedical:*
              Resource: '*'
      Events:
        MatchTrials:
          Type: Api
          Properties:
            RestApiId: !Ref TrialMatcherAPI
            Path: /match-trials
            Method: post
      Tracing: Active

  DataIngestionFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: src/
      Handler: ingest_trials.lambda_handler
      Runtime: python3.11
      MemorySize: 512
      Timeout: 300
      VpcConfig:
        SecurityGroupIds:
          - !Ref LambdaSecurityGroup
        SubnetIds:
          - !Ref PrivateSubnetA
          - !Ref PrivateSubnetB
      Environment:
        Variables:
          RDS_PROXY_ENDPOINT: !GetAtt RDSProxy.Endpoint
          DB_NAME: trials_db
          SNS_ALERT_TOPIC: !Ref AlertTopic
      Policies:
        - AWSLambdaVPCAccessExecutionRole
        - Version: '2012-10-17'
          Statement:
            - Effect: Allow
              Action:
                - rds-db:connect
                - sns:Publish
              Resource: '*'
      Events:
        DailySchedule:
          Type: Schedule
          Properties:
            Schedule: cron(0 2 * * ? *)
            Description: Daily trial data ingestion
      Tracing: Active

  # RDS Database
  TrialDatabase:
    Type: AWS::RDS::DBInstance
    Properties:
      DBInstanceIdentifier: !Sub ${Environment}-vitalmatch-db
      DBInstanceClass: !If [IsProd, db.t3.medium, db.t3.micro]
      Engine: postgres
      EngineVersion: '15.4'
      AllocatedStorage: 100
      StorageType: gp3
      StorageEncrypted: true
      MasterUsername: !Sub '{{resolve:ssm:/${Environment}/db/username}}'
      MasterUserPassword: !Sub '{{resolve:ssm-secure:/${Environment}/db/password}}'
      VPCSecurityGroups:
        - !Ref RDSSecurityGroup
      DBSubnetGroupName: !Ref DBSubnetGroup
      MultiAZ: !If [IsProd, true, false]
      BackupRetentionPeriod: 7
      PreferredBackupWindow: '03:00-04:00'
      PreferredMaintenanceWindow: 'sun:04:00-sun:05:00'

  DBSubnetGroup:
    Type: AWS::RDS::DBSubnetGroup
    Properties:
      DBSubnetGroupDescription: Subnet group for RDS
      SubnetIds:
        - !Ref PrivateSubnetA
        - !Ref PrivateSubnetB

  RDSProxy:
    Type: AWS::RDS::DBProxy
    Properties:
      DBProxyName: !Sub ${Environment}-vitalmatch-proxy
      EngineFamily: POSTGRESQL
      Auth:
        - AuthScheme: SECRETS
          IAMAuth: REQUIRED
          SecretArn: !Ref DBSecret
      RoleArn: !GetAtt RDSProxyRole.Arn
      VpcSubnetIds:
        - !Ref PrivateSubnetA
        - !Ref PrivateSubnetB
      VpcSecurityGroupIds:
        - !Ref RDSSecurityGroup

  # SNS Topic for Alerts
  AlertTopic:
    Type: AWS::SNS::Topic
    Properties:
      TopicName: !Sub ${Environment}-vitalmatch-alerts
      DisplayName: VitalMatch System Alerts

  # CloudWatch Alarms
  LambdaErrorAlarm:
    Type: AWS::CloudWatch::Alarm
    Properties:
      AlarmName: !Sub ${Environment}-lambda-errors
      MetricName: Errors
      Namespace: AWS/Lambda
      Statistic: Sum
      Period: 300
      EvaluationPeriods: 1
      Threshold: 5
      ComparisonOperator: GreaterThanThreshold
      AlarmActions:
        - !Ref AlertTopic

Conditions:
  IsProd: !Equals [!Ref Environment, prod]

Outputs:
  ApiEndpoint:
    Description: API Gateway endpoint URL
    Value: !Sub https://${TrialMatcherAPI}.execute-api.${AWS::Region}.amazonaws.com/${Environment}
  
  RDSProxyEndpoint:
    Description: RDS Proxy endpoint
    Value: !GetAtt RDSProxy.Endpoint
```

### Cost Optimization
- **Lambda**: Pay per request, no idle costs
- **RDS**: Right-sized instances with reserved capacity
- **S3**: Intelligent tiering for static assets
- **CloudFront**: Reduced origin requests through caching

## Future Enhancements

### Phase 2 Features
- Real-time trial status updates
- Integration with healthcare provider systems
- Patient notification system for new matching trials

### Phase 3 Features
- Machine learning model training on match success rates
- Multi-language support
- Mobile application development
- Advanced medical ontology integration