# VitalMatch - Clinical Trial Matcher - Requirements

## Overview
VitalMatch is an intelligent eligibility engine that goes beyond simple keyword search to match patients with relevant clinical trials based on complex medical criteria. Instead of returning thousands of irrelevant results, the system provides a ranked list of 3-5 best-match trials with clear explanations of why each trial is suitable.

## Problem Statement
Current clinical trial search engines use basic keyword matching, returning overwhelming numbers of irrelevant results. For example, searching "Diabetes" returns 50,000+ results with no indication of patient eligibility. Patients and doctors waste hours sifting through irrelevant trials, often missing genuinely suitable opportunities.

**Pain Points We Address:**
- **Information Overload**: Too many irrelevant results to process
- **Medical Complexity**: Complex eligibility criteria written in medical jargon
- **No Personalization**: Generic results that don't consider individual patient profiles
- **Time Waste**: Hours spent manually filtering through unsuitable trials
- **Missed Opportunities**: Suitable trials buried in thousands of irrelevant results

**Our Solution:**
An intelligent system that can:
- Filter trials based on patient-specific criteria using AWS AI services
- Interpret complex medical eligibility requirements with medical NLP
- Provide clear match explanations and confidence scores
- Deliver results in seconds, not hours

## Unique Selling Proposition (USP)

### 🎯 **"From 50,000 Trials to 5 Perfect Matches in 15 Seconds"**

**What Makes Us Different:**
1. **Hybrid Intelligence**: Combines SQL-based hard filtering with AWS AI-powered soft matching for unprecedented accuracy
2. **Medical Context Understanding**: Uses Amazon Bedrock and Comprehend Medical to interpret complex medical terminology and eligibility criteria
3. **Explainable AI**: Every match comes with clear, visual explanations showing exactly why a trial fits the patient
4. **Speed & Scale**: Processes thousands of trials in seconds using AWS serverless architecture
5. **Patient-Centric Design**: Transforms overwhelming medical jargon into clear, actionable insights

**The Problem We Solve:**
- **Current State**: ClinicalTrials.gov search for "Diabetes" returns 50,000+ unsorted results
- **Our Solution**: Returns 3-5 ranked matches with 92% accuracy scores and clear explanations like "✅ Perfect fit: Trial seeks patients with your exact condition and age range"

**Key Differentiators:**
- **Intelligent Filtering**: Reduces 1000+ trials to <10 relevant matches using AI
- **Medical NLP**: Understands "hypertension" = "high blood pressure" and complex eligibility criteria
- **Visual Match Explanations**: Shows exactly why each trial matches with checkmarks and warnings
- **AWS-Powered Reliability**: 99.9% uptime with global CDN performance
- **Cost-Effective**: Serverless architecture keeps costs under $500/month for 1000 daily users

## Core Features

### 🔍 **Smart Patient Profiling**
- **Intuitive Web Form**: Simple, guided input for medical condition, demographics, and history
- **Medical History Intelligence**: AI-powered parsing of complex medical backgrounds
- **Location-Based Matching**: Distance radius filtering with autocomplete
- **Accessibility First**: Mobile-responsive, WCAG 2.1 compliant interface

### ⚡ **Hybrid Filtering Engine**
- **Hard Filters (SQL)**: Lightning-fast elimination based on age, gender, location criteria
- **Soft Filters (AI)**: Amazon Bedrock-powered medical text analysis
- **Medical NLP**: Understands terminology variations ("hypertension" = "high blood pressure")
- **Exclusion Criteria Processing**: Intelligent screening to prevent unsuitable matches

### 🎯 **Intelligent Match Scoring**
- **Confidence Percentages**: Clear 92%, 75%, 60% match scores
- **Visual Explanations**: ✅ checkmarks and ⚠️ warnings for each criterion
- **Ranked Results**: Top 3-5 best matches, not overwhelming lists
- **Transparent AI**: "Why this matches you" explanations for every recommendation

### 📊 **Real-Time Processing Dashboard**
- **Progress Indicators**: Live updates showing "Searching → Filtering → AI Analysis"
- **Processing Transparency**: Shows trial counts at each filtering stage
- **Performance Metrics**: Sub-15 second total processing time
- **User Control**: Cancel search option and estimated completion times

### 🔄 **Automated Data Pipeline**
- **AWS-Powered Ingestion**: EventBridge + Lambda for scheduled ClinicalTrials.gov updates
- **Always Current**: Daily/weekly automated data refresh
- **Scalable Storage**: RDS PostgreSQL with optimized indexing
- **Error Monitoring**: SNS alerts for failed data updates

### 🛡️ **Enterprise-Grade Infrastructure**
- **Serverless Architecture**: API Gateway + Lambda for infinite scalability
- **Global Performance**: CloudFront CDN for worldwide fast loading
- **Security First**: HIPAA-ready with encryption at rest and in transit
- **Cost Optimized**: Pay-per-use model keeping costs under $500/month

## User Stories

### US1: Patient Profile Input
**As a** patient or healthcare provider  
**I want to** enter a comprehensive patient profile through an intuitive web form  
**So that** the system can find trials specifically relevant to my medical situation  

**Acceptance Criteria:**
- 1.1 Web form displays with clear sections for condition, demographics, and medical history
- 1.2 Condition field offers dropdown of common conditions plus free text option
- 1.3 Age accepts numeric input with validation (0-120 years)
- 1.4 Gender provides radio button options (Male/Female/Other/Prefer not to say)
- 1.5 Location field has autocomplete for cities/states with distance radius slider
- 1.6 Medical history provides large text area with helpful prompts and examples
- 1.7 Form validates all required fields before submission
- 1.8 Form is accessible and mobile-responsive

### US1.5: User Experience During Processing
**As a** user waiting for results  
**I want to** see clear progress indicators and estimated completion time  
**So that** I understand the system is working and know what to expect  

**Acceptance Criteria:**
- 1.9 Progress bar shows current processing stage ("Searching trials", "Filtering", "AI analysis")
- 1.10 System displays number of trials being processed at each stage
- 1.11 Estimated completion time is shown (typically 10-15 seconds)
- 1.12 User can cancel the search if needed

### US2: Intelligent Trial Filtering
**As a** user of the system  
**I want** trials to be filtered using both hard criteria and intelligent matching  
**So that** I only see trials that are genuinely relevant to the patient profile  

**Acceptance Criteria:**
- 2.1 System applies hard filters (age, gender, location) using SQL queries
- 2.2 System reduces large trial datasets (1000+) to manageable candidates (20-50)
- 2.3 System applies soft filters using NLP/AI for medical history matching
- 2.4 System handles medical terminology variations (e.g., "hypertension" vs "high blood pressure")
- 2.5 System processes inclusion and exclusion criteria text blocks

### US3: Match Scoring and Ranking
**As a** user  
**I want** to see trials ranked by match quality with clear visual explanations  
**So that** I can understand why each trial is recommended and make informed decisions  

**Acceptance Criteria:**
- 3.1 System generates match scores displayed as percentages (e.g., 92%, 75%, 60%)
- 3.2 Each trial displays in a card format with match score prominently shown
- 3.3 Cards show clear explanations with checkmarks/warnings (e.g., "✅ Perfect fit: Trial seeks patients with smoking history")
- 3.4 System returns top 3-5 best matches, not overwhelming lists
- 3.5 Each card displays trial title, location with distance, and key eligibility highlights
- 3.6 Match explanations reference specific criteria that align with patient profile
- 3.7 Users can click to view full trial details and contact information
- 3.8 Results include summary showing total trials searched and filtered counts

### US3.5: Trial Detail View
**As a** user interested in a specific trial  
**I want** to see comprehensive trial information with highlighted matches  
**So that** I can make an informed decision about participation  

**Acceptance Criteria:**
- 3.9 Detail view shows complete trial description and requirements
- 3.10 Eligibility criteria are highlighted to show which ones match the patient
- 3.11 Contact information and next steps are clearly displayed
- 3.12 "Why this matches you" section explains the AI reasoning
- 3.13 Users can save trials for later reference
- 3.14 Users can easily return to the results list

### US4: Data Management
**As a** system administrator  
**I want** the system to maintain current trial data through automated AWS processes  
**So that** users always see relevant and up-to-date clinical trials  

**Acceptance Criteria:**
- 4.1 System automatically ingests data from ClinicalTrials.gov API using scheduled Lambda functions
- 4.2 EventBridge triggers daily/weekly data updates without manual intervention
- 4.3 System parses trial data including title, condition, eligibility criteria, age ranges, location
- 4.4 System stores structured data in RDS PostgreSQL for efficient querying
- 4.5 System handles both JSON and XML data formats from the API
- 4.6 System can fetch top 1,000 recent trials for specific conditions
- 4.7 Failed ingestion processes trigger SNS notifications to administrators
- 4.8 System maintains data backup and recovery through RDS automated backups

### US5: System Monitoring and Operations
**As a** system administrator  
**I want** comprehensive monitoring and alerting for the AWS infrastructure  
**So that** I can ensure system reliability and performance  

**Acceptance Criteria:**
- 5.1 CloudWatch monitors all Lambda function performance and errors
- 5.2 RDS performance metrics are tracked and alerted on
- 5.3 API Gateway request/response metrics are monitored
- 5.4 X-Ray provides distributed tracing for debugging performance issues
- 5.5 SNS sends alerts for system errors or performance degradation
- 5.6 CloudWatch dashboards provide real-time system health visibility

## Technical Requirements

### TR1: AWS Cloud Architecture
- System must be built entirely on AWS services for scalability and managed operations
- Frontend must be hosted on S3 with CloudFront CDN for global performance
- Backend must use serverless architecture (API Gateway + Lambda) for cost efficiency
- Database must use managed RDS PostgreSQL with automated backups and high availability
- All Lambda functions must be deployed within a VPC private subnet for security
- RDS database must be deployed in a private subnet with security group restrictions
- AWS WAF must protect both CloudFront and API Gateway from common web attacks

### TR2: Data Architecture
- Database must store trials with structured fields (id, title, condition, min_age, max_age, gender_criteria)
- Database must store unstructured eligibility text (inclusion_text, exclusion_text)
- System must support efficient SQL-based filtering for hard criteria
- RDS Proxy must be used for Lambda database connection pooling
- Database must be accessible only from Lambda functions within the VPC private subnet
- Security groups must restrict database access to authorized Lambda functions only

### TR3: AI/NLP Integration
- System must use AWS managed AI services (Amazon Bedrock) for medical text matching
- System must leverage Amazon Comprehend Medical for medical entity extraction
- System must handle medical terminology variations and synonyms using AWS AI services
- System must process complex eligibility criteria text blocks with foundation models

### TR4: Performance Requirements
- Hard filtering (SQL via RDS) must reduce 1000+ trials to <50 candidates in <2 seconds
- Soft filtering (AI via Bedrock) must process remaining candidates in <10 seconds
- Total response time for match results must be <15 seconds
- Lambda functions must have provisioned concurrency to minimize cold starts

### TR5: Data Sources and Ingestion
- Primary data source: ClinicalTrials.gov public API
- Data ingestion must be automated using EventBridge scheduled triggers
- Lambda functions must handle API rate limits and bulk download options
- System must parse and normalize data from external sources
- Ingestion errors must trigger SNS notifications for monitoring
- Data ingestion Lambda must run within VPC private subnet with internet access via NAT Gateway
- ClinicalTrials.gov API must be accessed securely with proper authentication and rate limiting
- System must handle both JSON and XML response formats from the external API
- Failed API calls must implement exponential backoff retry logic

### TR6: Security and Compliance
- All data must be encrypted in transit and at rest using AWS KMS
- API access must be secured through AWS WAF and API Gateway throttling
- Database access must be restricted through VPC and security groups
- System must be designed with HIPAA compliance considerations for healthcare data
- AWS WAF must implement rules to protect against SQL injection, XSS, and DDoS attacks
- Security groups must follow principle of least privilege for all resources
- Lambda functions must use IAM roles with minimal required permissions
- VPC Flow Logs must be enabled for network traffic monitoring
- All API requests must be logged to CloudWatch for audit purposes

## Non-Functional Requirements

### NFR1: Usability
- Interface must be simple enough for patients to use independently
- Medical terminology must be explained in patient-friendly language
- Results must be clearly presented with visual match indicators
- Web application must load quickly via CloudFront CDN globally

### NFR2: Accuracy
- Match scores must reflect genuine eligibility likelihood
- System must minimize false positives (trials patient isn't eligible for)
- Medical terminology matching must be medically accurate using AWS AI services
- AI explanations must be transparent and understandable to users

### NFR3: Scalability and Reliability
- System must handle multiple concurrent users through serverless auto-scaling
- Database must efficiently store and query thousands of trials via RDS optimization
- System must support adding new medical conditions and trial types
- Lambda functions must scale automatically based on demand
- System must maintain 99.9% uptime through AWS managed services

### NFR4: Security and Compliance
- All data transmission must be encrypted using HTTPS/TLS
- Database must be encrypted at rest using AWS KMS
- API must be protected against common attacks using AWS WAF
- System must follow AWS security best practices for healthcare applications
- Access logs must be maintained for audit purposes

### NFR5: Cost Optimization
- System must use serverless architecture to minimize idle costs
- RDS instance must be right-sized for actual usage patterns
- S3 storage must use intelligent tiering for cost optimization
- Lambda functions must be optimized for execution time to reduce costs

## Out of Scope (V1)
- Direct integration with healthcare provider systems
- Patient enrollment or contact functionality
- Real-time trial status updates
- Multi-language support
- Mobile application interface

## Success Metrics
- Reduction in irrelevant trial results (target: <10 results per query)
- User satisfaction with match explanations (target: >80% find explanations helpful)
- System response time (target: <15 seconds end-to-end)
- Match accuracy (target: >85% of high-scored matches are genuinely eligible)
- System uptime (target: >99.9% availability through AWS managed services)
- Cost efficiency (target: <$500/month for 1000 daily users through serverless architecture)
- Data freshness (target: Trial data updated within 24 hours of ClinicalTrials.gov changes)