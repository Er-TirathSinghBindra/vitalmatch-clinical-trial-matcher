"""
Data Ingestion Lambda Function
Scheduled Lambda function to ingest clinical trial data from ClinicalTrials.gov
Requirements: TR5, 4.1, 4.2, 4.7
"""

import json
import logging
import os
import boto3
from datetime import datetime
from typing import Dict, Any

from data_ingestion.clinicaltrials_api_client import ClinicalTrialsAPIClient
from data_ingestion.trial_parser import TrialParser
from data_ingestion.database_storage import DatabaseStorage

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
sns_client = boto3.client('sns')
cloudwatch_client = boto3.client('cloudwatch')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for scheduled data ingestion
    
    Args:
        event: EventBridge scheduled event
        context: Lambda context
        
    Returns:
        Response dictionary with status and metrics
    """
    start_time = datetime.utcnow()
    logger.info("Starting data ingestion process")
    logger.info(f"Event: {json.dumps(event)}")
    
    try:
        # Get configuration from environment variables
        rds_proxy_endpoint = os.environ.get('RDS_PROXY_ENDPOINT')
        db_name = os.environ.get('DB_NAME', 'trials_db')
        db_user = os.environ.get('DB_USER', 'vitalmatch_admin')
        db_password = os.environ.get('DB_PASSWORD')
        sns_alert_topic = os.environ.get('SNS_ALERT_TOPIC')
        
        # Validate required environment variables
        if not rds_proxy_endpoint:
            raise ValueError("RDS_PROXY_ENDPOINT environment variable not set")
        if not db_password:
            raise ValueError("DB_PASSWORD environment variable not set")
        
        # Initialize components
        api_client = ClinicalTrialsAPIClient()
        parser = TrialParser()
        storage = DatabaseStorage(
            host=rds_proxy_endpoint,
            database=db_name,
            user=db_user,
            password=db_password
        )
        
        # Test database connection
        logger.info("Testing database connection...")
        if not storage.test_connection():
            raise Exception("Failed to connect to database")
        logger.info("Database connection successful")
        
        # Fetch trials updated in the last 24 hours
        logger.info("Fetching trials from ClinicalTrials.gov API...")
        raw_trials = api_client.fetch_recent_trials(days=1)
        logger.info(f"Fetched {len(raw_trials)} trials from API")
        
        # Parse trials
        logger.info("Parsing trial data...")
        parsed_trials = parser.parse_trials(raw_trials)
        logger.info(f"Successfully parsed {len(parsed_trials)} trials")
        
        # Store trials in database
        logger.info("Storing trials in database...")
        storage_result = storage.store_trials(parsed_trials)
        logger.info(f"Storage complete: {storage_result}")
        
        # Calculate metrics
        end_time = datetime.utcnow()
        duration_seconds = (end_time - start_time).total_seconds()
        
        metrics = {
            'trials_fetched': len(raw_trials),
            'trials_parsed': len(parsed_trials),
            'trials_inserted': storage_result['inserted'],
            'trials_updated': storage_result['updated'],
            'trials_failed': storage_result['failed'],
            'duration_seconds': duration_seconds,
            'total_trials_in_db': storage.get_trial_count()
        }
        
        # Log metrics
        logger.info(f"Ingestion metrics: {json.dumps(metrics)}")
        
        # Publish metrics to CloudWatch
        publish_metrics(metrics)
        
        # Send success notification if configured
        if sns_alert_topic and metrics['trials_failed'] > 0:
            send_warning_notification(sns_alert_topic, metrics)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Data ingestion completed successfully',
                'metrics': metrics
            })
        }
        
    except Exception as e:
        logger.error(f"Data ingestion failed: {e}", exc_info=True)
        
        # Calculate duration even on failure
        end_time = datetime.utcnow()
        duration_seconds = (end_time - start_time).total_seconds()
        
        # Send failure notification
        sns_alert_topic = os.environ.get('SNS_ALERT_TOPIC')
        if sns_alert_topic:
            send_failure_notification(sns_alert_topic, str(e), duration_seconds)
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Data ingestion failed',
                'error': str(e)
            })
        }


def publish_metrics(metrics: Dict[str, Any]) -> None:
    """
    Publish custom metrics to CloudWatch
    
    Args:
        metrics: Dictionary of metrics to publish
    """
    try:
        namespace = 'VitalMatch/DataIngestion'
        
        metric_data = [
            {
                'MetricName': 'TrialsFetched',
                'Value': metrics['trials_fetched'],
                'Unit': 'Count'
            },
            {
                'MetricName': 'TrialsParsed',
                'Value': metrics['trials_parsed'],
                'Unit': 'Count'
            },
            {
                'MetricName': 'TrialsInserted',
                'Value': metrics['trials_inserted'],
                'Unit': 'Count'
            },
            {
                'MetricName': 'TrialsUpdated',
                'Value': metrics['trials_updated'],
                'Unit': 'Count'
            },
            {
                'MetricName': 'TrialsFailed',
                'Value': metrics['trials_failed'],
                'Unit': 'Count'
            },
            {
                'MetricName': 'IngestionDuration',
                'Value': metrics['duration_seconds'],
                'Unit': 'Seconds'
            },
            {
                'MetricName': 'TotalTrialsInDatabase',
                'Value': metrics['total_trials_in_db'],
                'Unit': 'Count'
            }
        ]
        
        cloudwatch_client.put_metric_data(
            Namespace=namespace,
            MetricData=metric_data
        )
        
        logger.info("Metrics published to CloudWatch")
    except Exception as e:
        logger.error(f"Failed to publish metrics: {e}")


def send_warning_notification(topic_arn: str, metrics: Dict[str, Any]) -> None:
    """
    Send warning notification for partial failures
    
    Args:
        topic_arn: SNS topic ARN
        metrics: Ingestion metrics
    """
    try:
        subject = "VitalMatch Data Ingestion - Partial Failures"
        message = f"""
Data ingestion completed with some failures.

Metrics:
- Trials Fetched: {metrics['trials_fetched']}
- Trials Parsed: {metrics['trials_parsed']}
- Trials Inserted: {metrics['trials_inserted']}
- Trials Updated: {metrics['trials_updated']}
- Trials Failed: {metrics['trials_failed']}
- Duration: {metrics['duration_seconds']:.2f} seconds
- Total Trials in Database: {metrics['total_trials_in_db']}

Please review CloudWatch logs for details on failed trials.
"""
        
        sns_client.publish(
            TopicArn=topic_arn,
            Subject=subject,
            Message=message
        )
        
        logger.info("Warning notification sent")
    except Exception as e:
        logger.error(f"Failed to send warning notification: {e}")


def send_failure_notification(topic_arn: str, error: str, duration: float) -> None:
    """
    Send failure notification
    
    Args:
        topic_arn: SNS topic ARN
        error: Error message
        duration: Duration in seconds
    """
    try:
        subject = "VitalMatch Data Ingestion - FAILED"
        message = f"""
Data ingestion process failed.

Error: {error}

Duration: {duration:.2f} seconds

Please check CloudWatch logs for detailed error information.
"""
        
        sns_client.publish(
            TopicArn=topic_arn,
            Subject=subject,
            Message=message
        )
        
        logger.info("Failure notification sent")
    except Exception as e:
        logger.error(f"Failed to send failure notification: {e}")
