# VitalMatch Frontend Deployment Script (PowerShell)
# This script builds the React application and deploys it to S3 with CloudFront cache invalidation

param(
    [Parameter(Mandatory=$true)]
    [string]$Environment
)

# Function to print colored output
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

function Write-ErrorMsg {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

Write-Info "Starting frontend deployment for environment: $Environment"

# Get AWS Account ID
try {
    $AccountId = (aws sts get-caller-identity --query Account --output text)
    if ([string]::IsNullOrEmpty($AccountId)) {
        throw "Failed to get AWS Account ID"
    }
    Write-Info "AWS Account ID: $AccountId"
}
catch {
    Write-ErrorMsg "Failed to get AWS Account ID. Make sure AWS CLI is configured."
    exit 1
}

# Get S3 bucket name from CloudFormation stack outputs
$StackName = "vitalmatch-clinical-trial-matcher"
try {
    $BucketName = (aws cloudformation describe-stacks `
        --stack-name $StackName `
        --query "Stacks[0].Outputs[?OutputKey=='FrontendBucketName'].OutputValue" `
        --output text)
    
    if ([string]::IsNullOrEmpty($BucketName)) {
        Write-Warning "Failed to get S3 bucket name from CloudFormation stack"
        $BucketName = "$Environment-vitalmatch-frontend-$AccountId"
        Write-Warning "Using constructed bucket name: $BucketName"
    }
    
    Write-Info "S3 Bucket: $BucketName"
}
catch {
    Write-ErrorMsg "Failed to get S3 bucket name from CloudFormation stack"
    exit 1
}

# Get CloudFront Distribution ID from CloudFormation stack outputs
try {
    $DistributionId = (aws cloudformation describe-stacks `
        --stack-name $StackName `
        --query "Stacks[0].Outputs[?OutputKey=='CloudFrontDistributionId'].OutputValue" `
        --output text)
    
    if ([string]::IsNullOrEmpty($DistributionId)) {
        throw "Failed to get CloudFront Distribution ID"
    }
    
    Write-Info "CloudFront Distribution ID: $DistributionId"
}
catch {
    Write-ErrorMsg "Failed to get CloudFront Distribution ID from CloudFormation stack"
    exit 1
}

# Get API Gateway endpoint from CloudFormation stack outputs
try {
    $ApiEndpoint = (aws cloudformation describe-stacks `
        --stack-name $StackName `
        --query "Stacks[0].Outputs[?OutputKey=='ApiEndpoint'].OutputValue" `
        --output text)
    
    if ([string]::IsNullOrEmpty($ApiEndpoint)) {
        throw "Failed to get API Gateway endpoint"
    }
    
    Write-Info "API Gateway Endpoint: $ApiEndpoint"
}
catch {
    Write-ErrorMsg "Failed to get API Gateway endpoint from CloudFormation stack"
    exit 1
}

# Navigate to frontend directory
Set-Location frontend

# Create .env.production file with API endpoint
Write-Info "Creating .env.production file with API endpoint"
@"
VITE_API_ENDPOINT=$ApiEndpoint
"@ | Out-File -FilePath .env.production -Encoding utf8

# Install dependencies
Write-Info "Installing dependencies..."
npm install
if ($LASTEXITCODE -ne 0) {
    Write-ErrorMsg "Failed to install dependencies"
    Set-Location ..
    exit 1
}

# Run tests
Write-Info "Running tests..."
npm run test
if ($LASTEXITCODE -ne 0) {
    Write-ErrorMsg "Tests failed"
    Set-Location ..
    exit 1
}

# Build the React application
Write-Info "Building React application..."
npm run build
if ($LASTEXITCODE -ne 0) {
    Write-ErrorMsg "Build failed"
    Set-Location ..
    exit 1
}

# Check if build was successful
if (-not (Test-Path "dist")) {
    Write-ErrorMsg "Build failed - dist directory not found"
    Set-Location ..
    exit 1
}

Write-Info "Build completed successfully"

# Upload build files to S3
Write-Info "Uploading build files to S3 bucket: $BucketName"
aws s3 sync dist/ s3://$BucketName/ `
    --delete `
    --cache-control "public, max-age=31536000, immutable" `
    --exclude "index.html" `
    --exclude "*.html"

if ($LASTEXITCODE -ne 0) {
    Write-ErrorMsg "Failed to upload files to S3"
    Set-Location ..
    exit 1
}

# Upload HTML files with shorter cache control
Write-Info "Uploading HTML files with shorter cache control"
aws s3 sync dist/ s3://$BucketName/ `
    --cache-control "public, max-age=300, must-revalidate" `
    --exclude "*" `
    --include "*.html"

if ($LASTEXITCODE -ne 0) {
    Write-ErrorMsg "Failed to upload HTML files to S3"
    Set-Location ..
    exit 1
}

Write-Info "Files uploaded successfully"

# Invalidate CloudFront cache
Write-Info "Invalidating CloudFront cache..."
$InvalidationId = (aws cloudfront create-invalidation `
    --distribution-id $DistributionId `
    --paths "/*" `
    --query 'Invalidation.Id' `
    --output text)

if ($LASTEXITCODE -ne 0) {
    Write-ErrorMsg "Failed to create CloudFront invalidation"
    Set-Location ..
    exit 1
}

Write-Info "CloudFront invalidation created: $InvalidationId"
Write-Info "Waiting for invalidation to complete (this may take a few minutes)..."

# Wait for invalidation to complete
aws cloudfront wait invalidation-completed `
    --distribution-id $DistributionId `
    --id $InvalidationId

if ($LASTEXITCODE -ne 0) {
    Write-Warning "Failed to wait for invalidation completion, but invalidation was created"
}
else {
    Write-Info "CloudFront cache invalidation completed"
}

# Get CloudFront URL
$CloudFrontUrl = (aws cloudformation describe-stacks `
    --stack-name $StackName `
    --query "Stacks[0].Outputs[?OutputKey=='CloudFrontURL'].OutputValue" `
    --output text)

Write-Info "=========================================="
Write-Info "Deployment completed successfully!"
Write-Info "=========================================="
Write-Info "CloudFront URL: $CloudFrontUrl"
Write-Info "API Endpoint: $ApiEndpoint"
Write-Info "S3 Bucket: $BucketName"
Write-Info "CloudFront Distribution ID: $DistributionId"
Write-Info "=========================================="
Write-Info "You can now access the application at:"
Write-Info "$CloudFrontUrl"
Write-Info "=========================================="

# Return to original directory
Set-Location ..
