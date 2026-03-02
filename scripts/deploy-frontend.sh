#!/bin/bash

# VitalMatch Frontend Deployment Script
# This script builds the React application and deploys it to S3 with CloudFront cache invalidation

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

# Check if environment parameter is provided
if [ -z "$1" ]; then
    print_error "Environment parameter is required"
    echo "Usage: ./deploy-frontend.sh <environment>"
    echo "Example: ./deploy-frontend.sh dev"
    exit 1
fi

ENVIRONMENT=$1

print_info "Starting frontend deployment for environment: $ENVIRONMENT"

# Get AWS Account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
if [ -z "$ACCOUNT_ID" ]; then
    print_error "Failed to get AWS Account ID. Make sure AWS CLI is configured."
    exit 1
fi

print_info "AWS Account ID: $ACCOUNT_ID"

# Get S3 bucket name from CloudFormation stack outputs
STACK_NAME="vitalmatch-clinical-trial-matcher"
BUCKET_NAME=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --query "Stacks[0].Outputs[?OutputKey=='FrontendBucketName'].OutputValue" \
    --output text)

if [ -z "$BUCKET_NAME" ]; then
    print_error "Failed to get S3 bucket name from CloudFormation stack"
    print_info "Expected bucket name: ${ENVIRONMENT}-vitalmatch-frontend-${ACCOUNT_ID}"
    BUCKET_NAME="${ENVIRONMENT}-vitalmatch-frontend-${ACCOUNT_ID}"
    print_warning "Using constructed bucket name: $BUCKET_NAME"
fi

print_info "S3 Bucket: $BUCKET_NAME"

# Get CloudFront Distribution ID from CloudFormation stack outputs
DISTRIBUTION_ID=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --query "Stacks[0].Outputs[?OutputKey=='CloudFrontDistributionId'].OutputValue" \
    --output text)

if [ -z "$DISTRIBUTION_ID" ]; then
    print_error "Failed to get CloudFront Distribution ID from CloudFormation stack"
    exit 1
fi

print_info "CloudFront Distribution ID: $DISTRIBUTION_ID"

# Get API Gateway endpoint from CloudFormation stack outputs
API_ENDPOINT=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --query "Stacks[0].Outputs[?OutputKey=='ApiEndpoint'].OutputValue" \
    --output text)

if [ -z "$API_ENDPOINT" ]; then
    print_error "Failed to get API Gateway endpoint from CloudFormation stack"
    exit 1
fi

print_info "API Gateway Endpoint: $API_ENDPOINT"

# Navigate to frontend directory
cd frontend

# Create .env.production file with API endpoint
print_info "Creating .env.production file with API endpoint"
cat > .env.production << EOF
VITE_API_ENDPOINT=$API_ENDPOINT
EOF

# Install dependencies
print_info "Installing dependencies..."
npm install

# Run tests
print_info "Running tests..."
npm run test

# Build the React application
print_info "Building React application..."
npm run build

# Check if build was successful
if [ ! -d "dist" ]; then
    print_error "Build failed - dist directory not found"
    exit 1
fi

print_info "Build completed successfully"

# Upload build files to S3
print_info "Uploading build files to S3 bucket: $BUCKET_NAME"
aws s3 sync dist/ s3://$BUCKET_NAME/ \
    --delete \
    --cache-control "public, max-age=31536000, immutable" \
    --exclude "index.html" \
    --exclude "*.html"

# Upload HTML files with shorter cache control
print_info "Uploading HTML files with shorter cache control"
aws s3 sync dist/ s3://$BUCKET_NAME/ \
    --cache-control "public, max-age=300, must-revalidate" \
    --exclude "*" \
    --include "*.html"

print_info "Files uploaded successfully"

# Invalidate CloudFront cache
print_info "Invalidating CloudFront cache..."
INVALIDATION_ID=$(aws cloudfront create-invalidation \
    --distribution-id $DISTRIBUTION_ID \
    --paths "/*" \
    --query 'Invalidation.Id' \
    --output text)

print_info "CloudFront invalidation created: $INVALIDATION_ID"
print_info "Waiting for invalidation to complete (this may take a few minutes)..."

# Wait for invalidation to complete
aws cloudfront wait invalidation-completed \
    --distribution-id $DISTRIBUTION_ID \
    --id $INVALIDATION_ID

print_info "CloudFront cache invalidation completed"

# Get CloudFront URL
CLOUDFRONT_URL=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --query "Stacks[0].Outputs[?OutputKey=='CloudFrontURL'].OutputValue" \
    --output text)

print_info "=========================================="
print_info "Deployment completed successfully!"
print_info "=========================================="
print_info "CloudFront URL: $CLOUDFRONT_URL"
print_info "API Endpoint: $API_ENDPOINT"
print_info "S3 Bucket: $BUCKET_NAME"
print_info "CloudFront Distribution ID: $DISTRIBUTION_ID"
print_info "=========================================="
print_info "You can now access the application at:"
print_info "$CLOUDFRONT_URL"
print_info "=========================================="

# Return to original directory
cd ..
