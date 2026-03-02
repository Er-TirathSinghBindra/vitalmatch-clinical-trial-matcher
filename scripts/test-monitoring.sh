#!/bin/bash

# VitalMatch Monitoring Test Script
# This script tests the monitoring and alerting infrastructure

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-dev}
REGION=${AWS_REGION:-us-east-1}

echo "=========================================="
echo "VitalMatch Monitoring Test"
echo "Environment: $ENVIRONMENT"
echo "Region: $REGION"
echo "=========================================="
echo ""

# Function to check if a resource exists
check_resource() {
    local resource_type=$1
    local resource_name=$2
    local check_command=$3
    
    echo -n "Checking $resource_type: $resource_name... "
    if eval "$check_command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Found${NC}"
        return 0
    else
        echo -e "${RED}✗ Not Found${NC}"
        return 1
    fi
}

# Test CloudWatch Dashboards
echo "=== Testing CloudWatch Dashboards ==="
check_resource "Dashboard" "${ENVIRONMENT}-VitalMatch-System-Overview" \
    "aws cloudwatch get-dashboard --dashboard-name ${ENVIRONMENT}-VitalMatch-System-Overview --region $REGION"

check_resource "Dashboard" "${ENVIRONMENT}-VitalMatch-Lambda-Performance" \
    "aws cloudwatch get-dashboard --dashboard-name ${ENVIRONMENT}-VitalMatch-Lambda-Performance --region $REGION"

check_resource "Dashboard" "${ENVIRONMENT}-VitalMatch-API-Gateway" \
    "aws cloudwatch get-dashboard --dashboard-name ${ENVIRONMENT}-VitalMatch-API-Gateway --region $REGION"

check_resource "Dashboard" "${ENVIRONMENT}-VitalMatch-RDS-Database" \
    "aws cloudwatch get-dashboard --dashboard-name ${ENVIRONMENT}-VitalMatch-RDS-Database --region $REGION"

check_resource "Dashboard" "${ENVIRONMENT}-VitalMatch-Custom-Metrics" \
    "aws cloudwatch get-dashboard --dashboard-name ${ENVIRONMENT}-VitalMatch-Custom-Metrics --region $REGION"

echo ""

# Test CloudWatch Alarms
echo "=== Testing CloudWatch Alarms ==="
check_resource "Alarm" "${ENVIRONMENT}-vitalmatch-match-trials-error-rate" \
    "aws cloudwatch describe-alarms --alarm-names ${ENVIRONMENT}-vitalmatch-match-trials-error-rate --region $REGION | grep -q AlarmName"

check_resource "Alarm" "${ENVIRONMENT}-vitalmatch-match-trials-duration" \
    "aws cloudwatch describe-alarms --alarm-names ${ENVIRONMENT}-vitalmatch-match-trials-duration --region $REGION | grep -q AlarmName"

check_resource "Alarm" "${ENVIRONMENT}-vitalmatch-data-ingestion-errors" \
    "aws cloudwatch describe-alarms --alarm-names ${ENVIRONMENT}-vitalmatch-data-ingestion-errors --region $REGION | grep -q AlarmName"

check_resource "Alarm" "${ENVIRONMENT}-vitalmatch-rds-cpu-high" \
    "aws cloudwatch describe-alarms --alarm-names ${ENVIRONMENT}-vitalmatch-rds-cpu-high --region $REGION | grep -q AlarmName"

check_resource "Alarm" "${ENVIRONMENT}-vitalmatch-rds-storage-low" \
    "aws cloudwatch describe-alarms --alarm-names ${ENVIRONMENT}-vitalmatch-rds-storage-low --region $REGION | grep -q AlarmName"

check_resource "Alarm" "${ENVIRONMENT}-vitalmatch-api-latency" \
    "aws cloudwatch describe-alarms --alarm-names ${ENVIRONMENT}-vitalmatch-api-latency --region $REGION | grep -q AlarmName"

check_resource "Alarm" "${ENVIRONMENT}-vitalmatch-waf-high-block-rate" \
    "aws cloudwatch describe-alarms --alarm-names ${ENVIRONMENT}-vitalmatch-waf-high-block-rate --region $REGION | grep -q AlarmName"

echo ""

# Test SNS Topics
echo "=== Testing SNS Topics ==="
check_resource "SNS Topic" "${ENVIRONMENT}-vitalmatch-system-alerts" \
    "aws sns list-topics --region $REGION | grep -q ${ENVIRONMENT}-vitalmatch-system-alerts"

check_resource "SNS Topic" "${ENVIRONMENT}-vitalmatch-waf-alerts" \
    "aws sns list-topics --region $REGION | grep -q ${ENVIRONMENT}-vitalmatch-waf-alerts"

echo ""

# Test Lambda X-Ray Tracing
echo "=== Testing Lambda X-Ray Tracing ==="
MATCH_TRIALS_FUNCTION="${ENVIRONMENT}-vitalmatch-match-trials"
DATA_INGESTION_FUNCTION="${ENVIRONMENT}-vitalmatch-data-ingestion"

echo -n "Checking X-Ray tracing for $MATCH_TRIALS_FUNCTION... "
TRACING_CONFIG=$(aws lambda get-function-configuration --function-name $MATCH_TRIALS_FUNCTION --region $REGION --query 'TracingConfig.Mode' --output text 2>/dev/null || echo "NOT_FOUND")
if [ "$TRACING_CONFIG" = "Active" ]; then
    echo -e "${GREEN}✓ Active${NC}"
else
    echo -e "${RED}✗ Not Active (Current: $TRACING_CONFIG)${NC}"
fi

echo -n "Checking X-Ray tracing for $DATA_INGESTION_FUNCTION... "
TRACING_CONFIG=$(aws lambda get-function-configuration --function-name $DATA_INGESTION_FUNCTION --region $REGION --query 'TracingConfig.Mode' --output text 2>/dev/null || echo "NOT_FOUND")
if [ "$TRACING_CONFIG" = "Active" ]; then
    echo -e "${GREEN}✓ Active${NC}"
else
    echo -e "${RED}✗ Not Active (Current: $TRACING_CONFIG)${NC}"
fi

echo ""

# Test API Gateway X-Ray Tracing
echo "=== Testing API Gateway X-Ray Tracing ==="
API_ID=$(aws cloudformation describe-stacks --stack-name ${ENVIRONMENT}-vitalmatch --region $REGION --query "Stacks[0].Outputs[?OutputKey=='ApiGatewayId'].OutputValue" --output text 2>/dev/null || echo "NOT_FOUND")

if [ "$API_ID" != "NOT_FOUND" ]; then
    for STAGE in dev staging prod; do
        echo -n "Checking X-Ray tracing for API Gateway stage $STAGE... "
        TRACING_ENABLED=$(aws apigateway get-stage --rest-api-id $API_ID --stage-name $STAGE --region $REGION --query 'tracingEnabled' --output text 2>/dev/null || echo "NOT_FOUND")
        if [ "$TRACING_ENABLED" = "True" ]; then
            echo -e "${GREEN}✓ Enabled${NC}"
        else
            echo -e "${RED}✗ Not Enabled${NC}"
        fi
    done
else
    echo -e "${YELLOW}⚠ API Gateway not found (stack may not be deployed)${NC}"
fi

echo ""

# Test CloudWatch Log Groups
echo "=== Testing CloudWatch Log Groups ==="
check_resource "Log Group" "/aws/lambda/${ENVIRONMENT}-vitalmatch-match-trials" \
    "aws logs describe-log-groups --log-group-name-prefix /aws/lambda/${ENVIRONMENT}-vitalmatch-match-trials --region $REGION | grep -q logGroupName"

check_resource "Log Group" "/aws/lambda/${ENVIRONMENT}-vitalmatch-data-ingestion" \
    "aws logs describe-log-groups --log-group-name-prefix /aws/lambda/${ENVIRONMENT}-vitalmatch-data-ingestion --region $REGION | grep -q logGroupName"

check_resource "Log Group" "/aws/apigateway/${ENVIRONMENT}-vitalmatch-api" \
    "aws logs describe-log-groups --log-group-name-prefix /aws/apigateway/${ENVIRONMENT}-vitalmatch-api --region $REGION | grep -q logGroupName"

check_resource "Log Group" "/aws/waf/${ENVIRONMENT}-vitalmatch" \
    "aws logs describe-log-groups --log-group-name-prefix /aws/waf/${ENVIRONMENT}-vitalmatch --region $REGION | grep -q logGroupName"

echo ""

# Summary
echo "=========================================="
echo "Monitoring Test Complete"
echo "=========================================="
echo ""
echo "Next Steps:"
echo "1. Subscribe to SNS topics for email notifications:"
echo "   aws sns subscribe --topic-arn <TOPIC_ARN> --protocol email --notification-endpoint your-email@example.com"
echo ""
echo "2. Configure X-Ray sampling rules:"
echo "   aws xray create-sampling-rule --cli-input-json file://xray-sampling-rules.json"
echo ""
echo "3. View dashboards in AWS Console:"
echo "   https://console.aws.amazon.com/cloudwatch/home?region=$REGION#dashboards:"
echo ""
echo "4. View X-Ray service map:"
echo "   https://console.aws.amazon.com/xray/home?region=$REGION#/service-map"
echo ""
