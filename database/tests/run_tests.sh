#!/bin/bash

# ============================================================================
# VitalMatch Clinical Trial Matcher - Database Schema Validation Test Runner
# Task 2.2: Write database schema validation tests
# ============================================================================

set -e  # Exit on error

echo "=========================================="
echo "VitalMatch Database Schema Validation Tests"
echo "=========================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Check if PostgreSQL is accessible
if ! command -v psql &> /dev/null; then
    echo "Warning: psql command not found. Ensure PostgreSQL client is installed."
fi

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    echo "Loading environment variables from .env file..."
    export $(cat .env | grep -v '^#' | xargs)
fi

# Set default values if not provided
export DB_HOST=${DB_HOST:-localhost}
export DB_PORT=${DB_PORT:-5432}
export DB_NAME=${DB_NAME:-trials_db}
export DB_USER=${DB_USER:-vitalmatch_admin}

# Check if password is set
if [ -z "$DB_PASSWORD" ]; then
    echo "Warning: DB_PASSWORD environment variable is not set"
    echo "Please set it before running tests:"
    echo "  export DB_PASSWORD=your_password"
    echo ""
fi

echo "Database Configuration:"
echo "  Host: $DB_HOST"
echo "  Port: $DB_PORT"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo ""

# Check if pytest is installed
if ! python3 -c "import pytest" 2>/dev/null; then
    echo "Installing test dependencies..."
    pip install -r requirements.txt
    echo ""
fi

# Run tests
echo "Running database schema validation tests..."
echo ""

# Run pytest with verbose output
python3 -m pytest test_schema_validation.py -v --tb=short

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✅ All tests passed successfully!"
    echo "=========================================="
    exit 0
else
    echo ""
    echo "=========================================="
    echo "❌ Some tests failed. Please review the output above."
    echo "=========================================="
    exit 1
fi
