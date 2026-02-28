#!/bin/bash

# ============================================================================
# VitalMatch Database Migration Runner
# ============================================================================
# This script runs database migrations against AWS RDS PostgreSQL
# Usage: ./run_migration.sh <environment> <migration_file>
# Example: ./run_migration.sh dev 001_create_trials_table.sql
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check arguments
if [ $# -lt 2 ]; then
    print_error "Usage: $0 <environment> <migration_file>"
    print_info "Example: $0 dev 001_create_trials_table.sql"
    exit 1
fi

ENVIRONMENT=$1
MIGRATION_FILE=$2
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MIGRATION_PATH="${SCRIPT_DIR}/migrations/${MIGRATION_FILE}"

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
    print_error "Invalid environment: $ENVIRONMENT"
    print_info "Valid environments: dev, staging, prod"
    exit 1
fi

# Check if migration file exists
if [ ! -f "$MIGRATION_PATH" ]; then
    print_error "Migration file not found: $MIGRATION_PATH"
    exit 1
fi

print_info "Running migration: $MIGRATION_FILE"
print_info "Environment: $ENVIRONMENT"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI is not installed. Please install it first."
    exit 1
fi

# Check if psql is installed
if ! command -v psql &> /dev/null; then
    print_error "PostgreSQL client (psql) is not installed. Please install it first."
    exit 1
fi

# Get database credentials from AWS Parameter Store
print_info "Retrieving database credentials from AWS Parameter Store..."

DB_USERNAME=$(aws ssm get-parameter \
    --name "/${ENVIRONMENT}/vitalmatch/db/username" \
    --query "Parameter.Value" \
    --output text 2>/dev/null)

if [ -z "$DB_USERNAME" ]; then
    print_error "Failed to retrieve database username from Parameter Store"
    print_info "Make sure the parameter /${ENVIRONMENT}/vitalmatch/db/username exists"
    exit 1
fi

DB_PASSWORD=$(aws ssm get-parameter \
    --name "/${ENVIRONMENT}/vitalmatch/db/password" \
    --with-decryption \
    --query "Parameter.Value" \
    --output text 2>/dev/null)

if [ -z "$DB_PASSWORD" ]; then
    print_error "Failed to retrieve database password from Parameter Store"
    print_info "Make sure the parameter /${ENVIRONMENT}/vitalmatch/db/password exists"
    exit 1
fi

# Get RDS Proxy endpoint (preferred) or direct RDS endpoint
DB_ENDPOINT=$(aws ssm get-parameter \
    --name "/${ENVIRONMENT}/vitalmatch/db/proxy-endpoint" \
    --query "Parameter.Value" \
    --output text 2>/dev/null)

if [ -z "$DB_ENDPOINT" ]; then
    print_warning "RDS Proxy endpoint not found, trying direct RDS endpoint..."
    DB_ENDPOINT=$(aws ssm get-parameter \
        --name "/${ENVIRONMENT}/vitalmatch/db/endpoint" \
        --query "Parameter.Value" \
        --output text 2>/dev/null)
fi

if [ -z "$DB_ENDPOINT" ]; then
    print_error "Failed to retrieve database endpoint from Parameter Store"
    exit 1
fi

DB_NAME="trials_db"

print_info "Database endpoint: $DB_ENDPOINT"
print_info "Database name: $DB_NAME"
print_info "Database user: $DB_USERNAME"

# Confirm before running in production
if [ "$ENVIRONMENT" == "prod" ]; then
    print_warning "You are about to run a migration in PRODUCTION!"
    read -p "Are you sure you want to continue? (yes/no): " CONFIRM
    if [ "$CONFIRM" != "yes" ]; then
        print_info "Migration cancelled."
        exit 0
    fi
fi

# Run the migration
print_info "Executing migration..."

export PGPASSWORD="$DB_PASSWORD"

if psql -h "$DB_ENDPOINT" -U "$DB_USERNAME" -d "$DB_NAME" -f "$MIGRATION_PATH"; then
    print_info "Migration completed successfully! ✓"
    
    # Verify table was created
    print_info "Verifying table creation..."
    psql -h "$DB_ENDPOINT" -U "$DB_USERNAME" -d "$DB_NAME" -c "\dt trials" -c "\di trials*"
    
    print_info "Migration verification complete."
else
    print_error "Migration failed! ✗"
    exit 1
fi

# Clean up password from environment
unset PGPASSWORD

print_info "Done!"
