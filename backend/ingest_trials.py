"""
Data Ingestion Lambda Function
Scheduled Lambda function to ingest clinical trial data from ClinicalTrials.gov
Requirements: TR5, 4.1, 4.2, 4.7
"""

import json
import logging
import os
import boto3
from datetime import datetime, timedelta
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
        aurora_endpoint = os.environ.get('AURORA_CLUSTER_ENDPOINT')
        db_name = os.environ.get('DB_NAME', 'trials_db')
        db_secret_arn = os.environ.get('DB_SECRET_ARN')
        sns_alert_topic = os.environ.get('SNS_ALERT_TOPIC')
        
        # Validate required environment variables
        if not aurora_endpoint:
            raise ValueError("AURORA_CLUSTER_ENDPOINT environment variable not set")
        if not db_secret_arn:
            raise ValueError("DB_SECRET_ARN environment variable not set")
        
        # Get database credentials from Secrets Manager
        logger.info("Retrieving database credentials from Secrets Manager...")
        secrets_client = boto3.client('secretsmanager')
        secret_response = secrets_client.get_secret_value(SecretId=db_secret_arn)
        secret = json.loads(secret_response['SecretString'])
        db_user = secret['username']
        db_password = secret['password']
        logger.info(f"Credentials retrieved for user: {db_user}")
        
        # Initialize components
        api_client = ClinicalTrialsAPIClient()
        parser = TrialParser()
        storage = DatabaseStorage(
            host=aurora_endpoint,
            database=db_name,
            user=db_user,
            password=db_password
        )
        
        # Test database connection
        logger.info("Testing database connection...")
        if not storage.test_connection():
            raise Exception("Failed to connect to database")
        logger.info("Database connection successful")
        
        # Fetch trials day-by-day for better progress tracking and memory management
        days_to_fetch = int(os.environ.get('INGESTION_DAYS', '7'))
        logger.info(f"Starting day-by-day ingestion for last {days_to_fetch} days...")
        
        total_fetched = 0
        total_parsed = 0
        total_inserted = 0
        total_updated = 0
        total_failed = 0
        
        # Process each day separately with specific date ranges
        for day_offset in range(days_to_fetch):
            # Calculate date range for this specific day
            # day_offset=0 means today, day_offset=1 means yesterday, etc.
            start_date = datetime.utcnow() - timedelta(days=day_offset + 1)
            end_date = datetime.utcnow() - timedelta(days=day_offset)
            
            logger.info(f"Processing day {day_offset + 1}/{days_to_fetch} ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})...")
            
            try:
                # Fetch trials updated within this specific day range
                raw_trials = api_client.fetch_trials(
                    updated_since=start_date,
                    updated_until=end_date,
                    max_pages=10
                )
                logger.info(f"  Fetched {len(raw_trials)} trials for day {day_offset + 1}")
                
                if len(raw_trials) == 0:
                    logger.info(f"  No trials found for day {day_offset + 1}, skipping...")
                    continue
                
                # Parse trials
                parsed_trials = parser.parse_trials(raw_trials)
                logger.info(f"  Parsed {len(parsed_trials)} trials for day {day_offset + 1}")
                
                # Store trials in database
                storage_result = storage.store_trials(parsed_trials)
                logger.info(f"  Stored {storage_result['inserted']} new, {storage_result['updated']} updated for day {day_offset + 1}")
                
                # Accumulate metrics
                total_fetched += len(raw_trials)
                total_parsed += len(parsed_trials)
                total_inserted += storage_result['inserted']
                total_updated += storage_result['updated']
                total_failed += storage_result['failed']
                
            except Exception as day_error:
                logger.error(f"  Error processing day {day_offset + 1}: {day_error}")
                total_failed += 1
                continue
        
        # Calculate metrics
        end_time = datetime.utcnow()
        duration_seconds = (end_time - start_time).total_seconds()
        
        metrics = {
            'trials_fetched': total_fetched,
            'trials_parsed': total_parsed,
            'trials_inserted': total_inserted,
            'trials_updated': total_updated,
            'trials_failed': total_failed,
            'duration_seconds': duration_seconds,
            'total_trials_in_db': storage.get_trial_count()
        }
        
        # Log metrics
        logger.info(f"Ingestion complete! Metrics: {json.dumps(metrics)}")
        
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
