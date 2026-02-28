# VitalMatch Data Ingestion Tests

This directory contains integration tests for the VitalMatch data ingestion pipeline.

## Test Coverage

### test_clinicaltrials_api_client.py
Tests for the ClinicalTrials.gov API client:
- Fetching trials with mock responses
- Pagination handling
- Retry logic on timeout and HTTP errors
- Error handling for client errors (4xx)
- Max retries exceeded
- Query parameter building
- Helper methods (fetch_recent_trials, fetch_trials_by_condition)

### test_trial_parser.py
Tests for the trial data parser:
- Parsing complete trials with all fields
- Handling missing required fields (NCT ID, title, condition)
- Age parsing (years, months, invalid values)
- Gender criteria mapping
- Location extraction
- Inclusion/exclusion criteria extraction
- Multiple trial parsing
- Title truncation
- Fallback to brief title

### test_database_storage.py
Tests for the database storage layer:
- Database connection testing
- Storing single and multiple trials
- Upsert operations (insert then update)
- Retrieving trials by ID
- Deleting trials
- Batch processing (>100 trials)
- Handling missing optional fields
- SQL injection prevention

## Running Tests

### Prerequisites

1. Install test dependencies:
```bash
pip install -r requirements.txt
pip install pytest pytest-cov
```

2. For database tests, set up a test database and configure environment variables:
```bash
export TEST_DB_HOST=localhost
export TEST_DB_NAME=trials_db_test
export TEST_DB_USER=postgres
export TEST_DB_PASSWORD=your_password
```

### Run All Tests

```bash
# Using unittest
python -m unittest discover -s src/tests -p "test_*.py"

# Using pytest (recommended)
pytest src/tests/ -v

# With coverage report
pytest src/tests/ --cov=src/data_ingestion --cov-report=html
```

### Run Specific Test Files

```bash
# API client tests (no database required)
python -m unittest src/tests/test_clinicaltrials_api_client.py

# Parser tests (no database required)
python -m unittest src/tests/test_trial_parser.py

# Database tests (requires test database)
python -m unittest src/tests/test_database_storage.py
```

### Run Specific Test Cases

```bash
# Run a specific test class
python -m unittest src.tests.test_trial_parser.TestTrialParser

# Run a specific test method
python -m unittest src.tests.test_trial_parser.TestTrialParser.test_parse_complete_trial
```

## Test Database Setup

For database integration tests, you need a PostgreSQL test database:

1. Create test database:
```sql
CREATE DATABASE trials_db_test;
```

2. Run migrations:
```bash
psql -h localhost -U postgres -d trials_db_test -f database/migrations/001_create_trials_table.sql
```

3. Set environment variables (see Prerequisites above)

## Continuous Integration

These tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  env:
    TEST_DB_HOST: localhost
    TEST_DB_NAME: trials_db_test
    TEST_DB_USER: postgres
    TEST_DB_PASSWORD: postgres
  run: |
    pytest src/tests/ -v --cov=src/data_ingestion
```

## Test Data

Tests use mock data and do not require access to the real ClinicalTrials.gov API. Database tests create and clean up their own test data.

## Skipping Tests

Database tests will be automatically skipped if:
- Test database credentials are not provided
- Database connection cannot be established

To skip database tests explicitly:
```bash
pytest src/tests/ -v -k "not database"
```

## Troubleshooting

### Database Connection Errors
- Verify PostgreSQL is running
- Check environment variables are set correctly
- Ensure test database exists and migrations are applied
- Check firewall/security group settings

### Import Errors
- Ensure you're running tests from the project root directory
- Verify all dependencies are installed: `pip install -r src/requirements.txt`

### Mock Errors
- Tests use unittest.mock for API mocking
- Ensure Python version is 3.11+ (as specified in Lambda runtime)

## Requirements Validation

These tests validate the following requirements:
- **TR5**: Data Sources and Ingestion
- **4.1**: Automated data ingestion from ClinicalTrials.gov API
- **4.3**: Trial data parsing
- **4.4**: Database storage with RDS
- **4.5**: Handle JSON and XML formats
- **4.7**: Error handling and notifications
