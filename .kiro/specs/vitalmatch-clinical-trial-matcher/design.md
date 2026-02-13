# VitalMatch - Clinical Trial Matcher - Design Document

## System Architecture

### Overview
VitalMatch uses a hybrid architecture combining SQL-based hard filtering with AI-powered soft matching to provide intelligent clinical trial recommendations. The system follows a three-layer approach: data ingestion, intelligent filtering, and result presentation.

### AWS Architecture Diagram
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   CloudFront    │───▶│   API Gateway    │───▶│   Lambda Functions│
│   (Web UI)      │    │   (REST API)     │    │   (Filter Engine) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │                          │
                              ▼                          ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │   S3 Bucket      │    │   RDS PostgreSQL│
                       │   (Static Web)   │    │   (Trial Data)  │
                       └──────────────────┘    └─────────────────┘
                                                         ▲
                                                         │
                                                ┌─────────────────┐
                                                │  EventBridge +  │
                                                │  Lambda Cron    │
                                                │ (Data Ingestion)│
                                                └─────────────────┘
```

## AWS Component Design

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

### 3. Database - RDS PostgreSQL
**Purpose**: Managed relational database for structured trial data

**AWS Services**:
- **RDS PostgreSQL**: Managed database with automated backups
- **RDS Proxy**: Connection pooling for Lambda functions
- **Parameter Store**: Database credentials management

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

**Ingestion Flow**:
```python
def scheduled_data_ingestion():
    # Triggered by EventBridge rule
    # Fetch from ClinicalTrials.gov API
    # Process and store in RDS
    # Send notifications via SNS if errors
```

### 6. Monitoring and Logging
**AWS Services**:
- **CloudWatch**: Metrics, logs, and alarms
- **X-Ray**: Distributed tracing for Lambda functions
- **SNS**: Error notifications and alerts

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

### API Security
- Rate limiting to prevent abuse
- Input validation and sanitization
- SQL injection prevention through parameterized queries

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

Resources:
  TrialMatcherAPI:
    Type: AWS::Serverless::Api
    Properties:
      StageName: prod
      Cors:
        AllowMethods: "'GET,POST,OPTIONS'"
        AllowHeaders: "'content-type'"
        AllowOrigin: "'*'"

  MatchTrialsFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: src/
      Handler: match_trials.lambda_handler
      Runtime: python3.9
      Environment:
        Variables:
          RDS_ENDPOINT: !GetAtt TrialDatabase.Endpoint.Address
      Events:
        MatchTrials:
          Type: Api
          Properties:
            RestApiId: !Ref TrialMatcherAPI
            Path: /match-trials
            Method: post

  TrialDatabase:
    Type: AWS::RDS::DBInstance
    Properties:
      DBInstanceClass: db.t3.micro
      Engine: postgres
      MasterUsername: !Ref DBUsername
      MasterUserPassword: !Ref DBPassword
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