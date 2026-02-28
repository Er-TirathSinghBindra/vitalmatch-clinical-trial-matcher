# VitalMatch Database Migrations

This directory contains SQL migration scripts for the VitalMatch Clinical Trial Matcher database.

## Overview

The database uses PostgreSQL 15.4 on AWS RDS with optimized indexes for both SQL-based hard filtering and AI-powered soft matching.

## Migration Files

### 001_create_trials_table.sql
Creates the main `trials` table with:
- **Structured fields**: id, title, condition, age ranges, gender, location
- **Unstructured fields**: inclusion_text, exclusion_text (for AI/NLP processing)
- **Audit fields**: created_date, updated_date with automatic timestamp updates
- **Optimized indexes**:
  - Composite index on condition + age range for hard filtering
  - GIN full-text search indexes on location, inclusion_text, and exclusion_text
  - Additional indexes on gender_criteria and created_date

**Requirements**: TR2, 4.4

## Running Migrations

### Option 1: Direct PostgreSQL Connection

```bash
# Connect to RDS database
psql -h <RDS_ENDPOINT> -U <DB_USERNAME> -d trials_db -f database/migrations/001_create_trials_table.sql
```

### Option 2: Using AWS RDS Proxy (Recommended for Lambda)

```bash
# Connect via RDS Proxy endpoint
psql -h <RDS_PROXY_ENDPOINT> -U <DB_USERNAME> -d trials_db -f database/migrations/001_create_trials_table.sql
```

### Option 3: Using AWS Systems Manager Session Manager

```bash
# Get database credentials from Parameter Store
DB_USERNAME=$(aws ssm get-parameter --name "/dev/vitalmatch/db/username" --query "Parameter.Value" --output text)
DB_ENDPOINT=$(aws ssm get-parameter --name "/dev/vitalmatch/db/endpoint" --query "Parameter.Value" --output text)

# Run migration
PGPASSWORD=$(aws ssm get-parameter --name "/dev/vitalmatch/db/password" --with-decryption --query "Parameter.Value" --output text) \
psql -h $DB_ENDPOINT -U $DB_USERNAME -d trials_db -f database/migrations/001_create_trials_table.sql
```

### Option 4: Using AWS Secrets Manager

```bash
# Get database credentials from Secrets Manager
SECRET=$(aws secretsmanager get-secret-value --secret-id dev/vitalmatch/db-credentials --query SecretString --output text)
DB_HOST=$(echo $SECRET | jq -r .host)
DB_USER=$(echo $SECRET | jq -r .username)
DB_PASS=$(echo $SECRET | jq -r .password)
DB_NAME=$(echo $SECRET | jq -r .dbname)

# Run migration
PGPASSWORD=$DB_PASS psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f database/migrations/001_create_trials_table.sql
```

## Verifying Migration

After running the migration, verify the table and indexes were created:

```sql
-- Check table exists
\dt trials

-- Check table structure
\d trials

-- Check indexes
\di trials*

-- Verify index details
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'trials'
ORDER BY indexname;

-- Check table comments
SELECT 
    column_name,
    data_type,
    col_description('trials'::regclass, ordinal_position) as column_comment
FROM information_schema.columns
WHERE table_name = 'trials'
ORDER BY ordinal_position;
```

## Performance Considerations

### Index Usage
- **idx_condition_age**: Used for hard filtering queries on condition and age range
- **idx_location_fulltext**: GIN index for full-text search on location (e.g., "New York", "Boston")
- **idx_inclusion_text_fulltext**: GIN index for AI/NLP processing of inclusion criteria
- **idx_exclusion_text_fulltext**: GIN index for AI/NLP processing of exclusion criteria
- **idx_gender_criteria**: B-tree index for gender filtering
- **idx_created_date**: B-tree index for data freshness queries

### Query Examples

```sql
-- Hard filter: Find trials for a 65-year-old male with diabetes in New York area
SELECT id, title, condition, location
FROM trials
WHERE condition = 'Diabetes'
  AND min_age <= 65
  AND max_age >= 65
  AND gender_criteria IN ('Male', 'All')
  AND to_tsvector('english', location) @@ to_tsquery('New & York');

-- Full-text search on inclusion criteria
SELECT id, title, inclusion_text
FROM trials
WHERE to_tsvector('english', inclusion_text) @@ to_tsquery('smoking & history');

-- Find recently updated trials
SELECT id, title, updated_date
FROM trials
WHERE updated_date > NOW() - INTERVAL '7 days'
ORDER BY updated_date DESC;
```

## Rollback

To rollback this migration (⚠️ WARNING: This will delete all trial data):

```sql
-- Drop trigger first
DROP TRIGGER IF EXISTS update_trials_updated_date ON trials;

-- Drop function
DROP FUNCTION IF EXISTS update_updated_date_column();

-- Drop table (this will automatically drop all indexes)
DROP TABLE IF EXISTS trials CASCADE;
```

## Database Schema

```
trials
├── id (TEXT, PRIMARY KEY)                    # NCT identifier
├── title (TEXT, NOT NULL)                    # Trial title
├── condition (TEXT, NOT NULL)                # Medical condition
├── min_age (INTEGER)                         # Minimum age requirement
├── max_age (INTEGER)                         # Maximum age requirement
├── gender_criteria (TEXT)                    # Gender eligibility
├── location (TEXT)                           # Trial location(s)
├── inclusion_text (TEXT)                     # Inclusion criteria (unstructured)
├── exclusion_text (TEXT)                     # Exclusion criteria (unstructured)
├── created_date (TIMESTAMP)                  # Record creation timestamp
└── updated_date (TIMESTAMP)                  # Last update timestamp
```

## Security Notes

- Database is deployed in private subnets with no public access
- Access restricted via security groups to Lambda functions only
- All connections use TLS encryption
- IAM database authentication enabled
- Credentials stored in AWS Secrets Manager and Parameter Store
- VPC Flow Logs enabled for network traffic monitoring

## Monitoring

Monitor database performance using:
- **CloudWatch Metrics**: CPU, connections, IOPS, storage
- **RDS Performance Insights**: Query performance analysis
- **CloudWatch Logs**: PostgreSQL logs exported to CloudWatch

## Next Steps

After running this migration:
1. Verify table and indexes are created successfully
2. Run the data ingestion Lambda function to populate the table
3. Test query performance with sample data
4. Monitor index usage and query patterns
5. Adjust indexes based on actual query patterns if needed
