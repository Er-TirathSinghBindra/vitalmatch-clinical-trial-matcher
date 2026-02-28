# Database Schema Validation Tests

This directory contains comprehensive validation tests for the VitalMatch Clinical Trial Matcher database schema.

## Test Coverage

The test suite validates:

1. **Table Creation and Structure** - Verifies the trials table exists with all required columns and correct data types
2. **Constraints** - Tests primary key, NOT NULL constraints, and uniqueness enforcement
3. **Indexes** - Validates all 6 indexes exist with correct types (B-tree and GIN)
4. **Index Performance** - Tests query performance using indexes with sample data
5. **Data Types** - Verifies TEXT, INTEGER, and TIMESTAMP fields work correctly
6. **Nullable Fields** - Tests that optional fields accept NULL values
7. **Triggers** - Validates the automatic updated_date trigger functionality
8. **Sample Data** - Verifies sample data is loaded correctly

## Requirements

- Python 3.11+
- PostgreSQL 15+
- Access to a test database

## Installation

Install test dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

Set the following environment variables for database connection:

```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=trials_db
export DB_USER=vitalmatch_admin
export DB_PASSWORD=your_password
```

Or create a `.env` file in the `database/tests/` directory:

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=trials_db
DB_USER=vitalmatch_admin
DB_PASSWORD=your_password
```

## Running Tests

### Run all tests:

```bash
cd database/tests
pytest test_schema_validation.py -v
```

### Run specific test class:

```bash
pytest test_schema_validation.py::TestTableCreation -v
```

### Run specific test:

```bash
pytest test_schema_validation.py::TestTableCreation::test_trials_table_exists -v
```

### Run with detailed output:

```bash
pytest test_schema_validation.py -v -s
```

### Run with coverage report:

```bash
pytest test_schema_validation.py --cov=. --cov-report=html
```

## Test Database Setup

Before running tests, ensure:

1. PostgreSQL is running
2. The database exists: `CREATE DATABASE trials_db;`
3. The schema migration has been applied: `./database/run_migration.sh`
4. Sample data is loaded (optional, tests will load it if missing)

### Quick Setup for Local Testing:

```bash
# Create database
createdb trials_db

# Run migration
cd database
./run_migration.sh

# Load sample data (optional)
psql -d trials_db -f migrations/sample_data.sql

# Run tests
cd tests
pytest test_schema_validation.py -v
```

## AWS RDS Testing

To test against an AWS RDS instance:

1. Ensure your Lambda security group allows access from your IP
2. Use the RDS endpoint as DB_HOST
3. Use the RDS Proxy endpoint for production-like testing

```bash
export DB_HOST=your-rds-instance.region.rds.amazonaws.com
export DB_PORT=5432
export DB_NAME=trials_db
export DB_USER=vitalmatch_admin
export DB_PASSWORD=your_rds_password

pytest test_schema_validation.py -v
```

## CI/CD Integration

These tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run Database Schema Tests
  env:
    DB_HOST: localhost
    DB_PORT: 5432
    DB_NAME: trials_db_test
    DB_USER: postgres
    DB_PASSWORD: postgres
  run: |
    cd database/tests
    pip install -r requirements.txt
    pytest test_schema_validation.py -v --junitxml=test-results.xml
```

## Test Results

All tests should pass if:
- The migration script `001_create_trials_table.sql` was executed successfully
- The database is accessible with the provided credentials
- PostgreSQL version is 15 or higher

## Troubleshooting

### Connection Errors

If you get connection errors:
- Verify PostgreSQL is running: `pg_isready`
- Check credentials are correct
- Ensure database exists: `psql -l | grep trials_db`

### Permission Errors

If you get permission errors:
- Ensure the database user has necessary privileges
- Grant permissions: `GRANT ALL PRIVILEGES ON DATABASE trials_db TO vitalmatch_admin;`

### Missing Sample Data

If sample data tests fail:
- Load sample data: `psql -d trials_db -f ../migrations/sample_data.sql`
- Or let the tests load it automatically (requires write permissions)

## Requirements Validation

These tests validate **Requirement TR2**:
- Database stores trials with structured fields (id, title, condition, min_age, max_age, gender_criteria)
- Database stores unstructured eligibility text (inclusion_text, exclusion_text)
- System supports efficient SQL-based filtering for hard criteria
- Indexes optimize query performance for filtering operations

## Related Files

- `../migrations/001_create_trials_table.sql` - Schema migration script
- `../migrations/sample_data.sql` - Sample trial data for testing
- `../run_migration.sh` - Migration execution script
