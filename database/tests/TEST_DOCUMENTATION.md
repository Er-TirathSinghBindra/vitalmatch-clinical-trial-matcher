# Database Schema Validation Test Documentation

## Overview

This document provides detailed information about the database schema validation tests for the VitalMatch Clinical Trial Matcher system.

## Test Suite Structure

The test suite is organized into 7 test classes, each focusing on a specific aspect of the database schema:

### 1. TestTableCreation (2 tests)
**Purpose**: Verify the trials table exists with correct structure

**Tests**:
- `test_trials_table_exists`: Confirms the trials table exists in the public schema
- `test_trials_table_columns`: Validates all 11 columns exist with correct data types and nullable constraints

**Validates**:
- Table existence
- Column names and data types
- NOT NULL constraints on required fields (id, title, condition)
- Nullable constraints on optional fields
- Default values for timestamp fields

### 2. TestConstraints (3 tests)
**Purpose**: Verify database constraints and primary key enforcement

**Tests**:
- `test_primary_key_constraint`: Confirms PRIMARY KEY constraint exists on id column
- `test_primary_key_uniqueness`: Verifies duplicate id values are rejected
- `test_not_null_constraints`: Validates NOT NULL constraints prevent missing required fields

**Validates**:
- Primary key constraint existence
- Uniqueness enforcement
- NOT NULL constraint enforcement on id, title, and condition

### 3. TestIndexes (2 tests)
**Purpose**: Verify all required indexes exist with correct configuration

**Tests**:
- `test_all_indexes_exist`: Confirms all 6 indexes exist (plus primary key index)
- `test_index_types`: Validates correct index types (B-tree vs GIN)

**Validates**:
- idx_condition_age (B-tree composite index)
- idx_location_fulltext (GIN full-text search index)
- idx_inclusion_text_fulltext (GIN full-text search index)
- idx_exclusion_text_fulltext (GIN full-text search index)
- idx_gender_criteria (B-tree index)
- idx_created_date (B-tree index with DESC ordering)

### 4. TestIndexPerformance (5 tests)
**Purpose**: Test query performance using indexes with sample data

**Tests**:
- `test_condition_age_index_performance`: Tests composite index on condition and age range
- `test_location_fulltext_index_performance`: Tests GIN full-text search on location
- `test_inclusion_text_fulltext_index_performance`: Tests GIN full-text search on inclusion criteria
- `test_gender_criteria_index_performance`: Tests B-tree index on gender criteria
- `test_created_date_index_performance`: Tests B-tree index on created_date with ordering

**Performance Criteria**:
- All queries should complete in < 100ms for small datasets
- Uses EXPLAIN ANALYZE to verify query execution
- Validates index usage (when applicable for dataset size)

### 5. TestDataTypes (4 tests)
**Purpose**: Verify data type handling and nullable field behavior

**Tests**:
- `test_text_fields_accept_long_content`: Validates TEXT fields can store 10,000+ characters
- `test_integer_age_fields`: Confirms INTEGER type for min_age and max_age
- `test_nullable_fields_accept_null`: Verifies optional fields accept NULL values
- `test_timestamp_fields_auto_populate`: Validates automatic timestamp population

**Validates**:
- TEXT fields support long content (no VARCHAR limitations)
- INTEGER fields store numeric values correctly
- NULL values accepted for optional fields
- TIMESTAMP fields auto-populate with CURRENT_TIMESTAMP

### 6. TestTriggers (1 test)
**Purpose**: Test automatic trigger for updated_date

**Tests**:
- `test_updated_date_trigger`: Verifies updated_date changes on UPDATE, created_date remains unchanged

**Validates**:
- Trigger function `update_updated_date_column()` exists
- Trigger `update_trials_updated_date` fires on UPDATE
- updated_date automatically updates to current timestamp
- created_date remains unchanged on updates

### 7. TestSampleData (2 tests)
**Purpose**: Validate sample data is correctly loaded

**Tests**:
- `test_sample_data_exists`: Confirms at least 8 sample trials are loaded
- `test_sample_data_variety`: Validates variety in conditions, genders, and age ranges

**Validates**:
- Sample data from sample_data.sql is loaded
- Data includes diverse conditions (5+ unique)
- Data includes diverse demographics (2+ gender criteria)
- Age ranges cover young adults (≤18) to older adults (≥75)

## Test Execution Flow

### Setup Phase
1. **Module-level fixture** (`db_connection`): Establishes PostgreSQL connection
2. **Module-level fixture** (`db_cursor`): Creates cursor for query execution
3. **Class-level fixture** (`setup_sample_data`): Loads sample data if not present

### Test Phase
- Each test class runs independently
- Tests within a class may depend on fixtures
- Database state is cleaned up after each test (where applicable)

### Teardown Phase
- Cursors are closed
- Database connections are closed
- Test data is cleaned up (except sample data)

## Requirements Validation

These tests validate **Technical Requirement TR2**:

> "Database must store trials with structured fields (id, title, condition, min_age, max_age, gender_criteria) and unstructured eligibility text (inclusion_text, exclusion_text), support efficient SQL-based filtering"

**How tests validate TR2**:

1. **Structured Fields**: TestTableCreation validates all structured fields exist with correct types
2. **Unstructured Text**: TestDataTypes validates TEXT fields can store long eligibility criteria
3. **Efficient Filtering**: TestIndexPerformance validates indexes enable fast SQL queries
4. **Data Integrity**: TestConstraints validates primary key and NOT NULL constraints

## Running Specific Test Categories

Use pytest markers to run specific test categories:

```bash
# Run only table structure tests
pytest -m table

# Run only constraint tests
pytest -m constraints

# Run only index tests
pytest -m indexes

# Run only performance tests
pytest -m performance

# Run only data type tests
pytest -m datatypes

# Run only trigger tests
pytest -m triggers

# Run only sample data tests
pytest -m sample_data

# Run multiple categories
pytest -m "table or constraints"

# Exclude performance tests (for quick validation)
pytest -m "not performance"
```

## Expected Test Results

### All Tests Pass Scenario
When all tests pass, you should see:
```
======================== 19 passed in X.XXs ========================
```

This indicates:
- ✅ Table structure is correct
- ✅ All constraints are enforced
- ✅ All indexes exist and are configured correctly
- ✅ Query performance meets requirements
- ✅ Data types work as expected
- ✅ Triggers function correctly
- ✅ Sample data is loaded properly

### Common Failure Scenarios

#### Connection Failures
```
psycopg2.OperationalError: could not connect to server
```
**Solution**: Verify database is running and credentials are correct

#### Missing Table
```
AssertionError: trials table should exist
```
**Solution**: Run migration script `001_create_trials_table.sql`

#### Missing Indexes
```
AssertionError: idx_condition_age should exist
```
**Solution**: Re-run migration script to create indexes

#### Performance Issues
```
AssertionError: Query should complete in < 100ms, took 150.00ms
```
**Solution**: Check database load, run ANALYZE, or investigate slow queries

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Database Schema Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: trials_db
          POSTGRES_USER: vitalmatch_admin
          POSTGRES_PASSWORD: test_password
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd database/tests
          pip install -r requirements.txt
      
      - name: Run migrations
        env:
          PGPASSWORD: test_password
        run: |
          psql -h localhost -U vitalmatch_admin -d trials_db -f database/migrations/001_create_trials_table.sql
      
      - name: Run tests
        env:
          DB_HOST: localhost
          DB_PORT: 5432
          DB_NAME: trials_db
          DB_USER: vitalmatch_admin
          DB_PASSWORD: test_password
        run: |
          cd database/tests
          pytest test_schema_validation.py -v --junitxml=test-results.xml
      
      - name: Publish test results
        uses: EnricoMi/publish-unit-test-result-action@v2
        if: always()
        with:
          files: database/tests/test-results.xml
```

## Test Maintenance

### Adding New Tests

When adding new schema elements:

1. Update migration script `001_create_trials_table.sql`
2. Add corresponding tests to `test_schema_validation.py`
3. Update this documentation
4. Run tests to verify changes

### Modifying Existing Tests

When modifying schema:

1. Update migration script
2. Update affected tests
3. Verify all tests still pass
4. Update documentation if test behavior changes

## Performance Benchmarks

Expected performance on standard hardware:

| Test Category | Expected Duration |
|--------------|-------------------|
| Table Creation | < 1 second |
| Constraints | < 2 seconds |
| Indexes | < 1 second |
| Performance | < 3 seconds |
| Data Types | < 2 seconds |
| Triggers | < 1 second |
| Sample Data | < 1 second |
| **Total** | **< 11 seconds** |

## Troubleshooting Guide

### Issue: Tests fail with "relation does not exist"
**Cause**: Migration not run or database not initialized
**Solution**: Run `./database/run_migration.sh`

### Issue: Performance tests timeout
**Cause**: Database under heavy load or missing indexes
**Solution**: Run `ANALYZE trials;` and verify indexes exist

### Issue: Sample data tests fail
**Cause**: Sample data not loaded
**Solution**: Run `psql -d trials_db -f database/migrations/sample_data.sql`

### Issue: Connection refused
**Cause**: PostgreSQL not running or wrong credentials
**Solution**: Verify PostgreSQL is running and check environment variables

## Related Documentation

- [Database README](../README.md) - Database setup and migration guide
- [Migration Script](../migrations/001_create_trials_table.sql) - Schema definition
- [Sample Data](../migrations/sample_data.sql) - Test data
- [Design Document](../../.kiro/specs/vitalmatch-clinical-trial-matcher/design.md) - System architecture
- [Requirements](../../.kiro/specs/vitalmatch-clinical-trial-matcher/requirements.md) - Technical requirements
