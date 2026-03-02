"""
Match Trials Lambda Handler
API Gateway Lambda function for clinical trial matching
Requirements: TR4, US1, US2, US3
"""

import json
import logging
import os
import time
import boto3
from datetime import datetime
from typing import Dict, Any, List, Optional

from hard_filter.filter_engine import HardFilterEngine, PatientProfile as HardFilterPatientProfile
from ai_matching.medical_matcher import MedicalMatcher
from ai_matching.match_scorer import MatchScorer, PatientProfile as ScorerPatientProfile, Trial

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize CloudWatch client for custom metrics
cloudwatch_client = boto3.client('cloudwatch')


class ValidationError(Exception):
    """Custom exception for input validation errors"""
    pass


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for match-trials API endpoint
    
    Args:
        event: API Gateway event with patient profile in body
        context: Lambda context object
        
    Returns:
        API Gateway response with match results
    """
    start_time = time.time()
    request_id = context.request_id if context else 'local'
    
    logger.info(f"Request {request_id}: Starting trial matching")
    
    try:
        # Parse and validate patient profile
        patient_profile = parse_and_validate_request(event)
        logger.info(f"Request {request_id}: Patient profile validated")
        
        # Initialize components
        hard_filter_engine = initialize_hard_filter_engine()
        match_scorer = initialize_match_scorer()
        
        # Step 1: Hard filtering
        logger.info(f"Request {request_id}: Starting hard filtering")
        hard_filter_result = hard_filter_engine.filter_trials(
            HardFilterPatientProfile(
                condition=patient_profile['condition'],
                age=patient_profile['age'],
                gender=patient_profile['gender'],
                location=patient_profile['location'],
                distance_miles=patient_profile.get('distance_miles', 50),
                medical_history=patient_profile.get('medical_history')
            )
        )
        
        logger.info(
            f"Request {request_id}: Hard filtering complete - "
            f"{hard_filter_result.total_count} -> {hard_filter_result.filtered_count} trials "
            f"in {hard_filter_result.processing_time_ms:.2f}ms"
        )
        
        # Step 2: AI-powered soft filtering and scoring
        logger.info(f"Request {request_id}: Starting AI scoring")
        ai_start_time = time.time()
        
        # Convert hard filtered trials to Trial objects
        trials = convert_to_trial_objects(hard_filter_result.trials)
        
        # Score and rank trials
        match_results = match_scorer.score_and_rank_trials(
            patient_profile=ScorerPatientProfile(
                condition=patient_profile['condition'],
                age=patient_profile['age'],
                gender=patient_profile['gender'],
                location=patient_profile['location'],
                distance_miles=patient_profile.get('distance_miles', 50),
                medical_history=patient_profile.get('medical_history', '')
            ),
            hard_filtered_trials=trials
        )
        
        ai_processing_time_ms = (time.time() - ai_start_time) * 1000
        logger.info(
            f"Request {request_id}: AI scoring complete - "
            f"{len(match_results)} matches in {ai_processing_time_ms:.2f}ms"
        )
        
        # Step 3: Format response
        total_processing_time_ms = (time.time() - start_time) * 1000
        
        response_body = format_response(
            match_results=match_results,
            total_trials_considered=hard_filter_result.total_count,
            hard_filtered_count=hard_filter_result.filtered_count,
            processing_time_ms=total_processing_time_ms
        )
        
        logger.info(
            f"Request {request_id}: Complete - "
            f"{len(match_results)} matches in {total_processing_time_ms:.2f}ms"
        )
        
        # Emit custom CloudWatch metrics
        emit_custom_metrics(
            total_trials=hard_filter_result.total_count,
            hard_filtered_count=hard_filter_result.filtered_count,
            matches_returned=len(match_results),
            match_scores=[result.match_percentage / 100.0 for result in match_results]
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST, OPTIONS'
            },
            'body': json.dumps(response_body)
        }
        
    except ValidationError as e:
        logger.warning(f"Request {request_id}: Validation error - {str(e)}")
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Validation Error',
                'message': str(e)
            })
        }
        
    except Exception as e:
        logger.error(f"Request {request_id}: Unexpected error - {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Internal Server Error',
                'message': 'An unexpected error occurred while processing your request'
            })
        }


def parse_and_validate_request(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse and validate patient profile from API Gateway event
    
    Args:
        event: API Gateway event
        
    Returns:
        Validated patient profile dictionary
        
    Raises:
        ValidationError: If validation fails
    """
    # Parse body
    try:
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON in request body: {str(e)}")
    
    # Extract patient profile
    patient_profile = body.get('patient_profile', {})
    
    if not patient_profile:
        raise ValidationError("Missing 'patient_profile' in request body")
    
    # Validate required fields
    required_fields = ['condition', 'age', 'gender', 'location']
    missing_fields = [field for field in required_fields if not patient_profile.get(field)]
    
    if missing_fields:
        raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")
    
    # Validate age
    try:
        age = int(patient_profile['age'])
        if age < 0 or age > 120:
            raise ValidationError("Age must be between 0 and 120")
        patient_profile['age'] = age
    except (ValueError, TypeError):
        raise ValidationError("Age must be a valid integer")
    
    # Validate gender
    valid_genders = ['male', 'female', 'other', 'all']
    gender = patient_profile['gender'].lower()
    if gender not in valid_genders:
        raise ValidationError(f"Gender must be one of: {', '.join(valid_genders)}")
    patient_profile['gender'] = gender.capitalize()
    
    # Validate condition (non-empty string)
    condition = patient_profile['condition'].strip()
    if not condition:
        raise ValidationError("Condition cannot be empty")
    patient_profile['condition'] = condition
    
    # Validate location (non-empty string)
    location = patient_profile['location'].strip()
    if not location:
        raise ValidationError("Location cannot be empty")
    patient_profile['location'] = location
    
    # Validate optional distance_miles
    if 'distance_miles' in patient_profile:
        try:
            distance = int(patient_profile['distance_miles'])
            if distance < 1 or distance > 500:
                raise ValidationError("Distance must be between 1 and 500 miles")
            patient_profile['distance_miles'] = distance
        except (ValueError, TypeError):
            raise ValidationError("Distance must be a valid integer")
    
    # Validate optional medical_history
    if 'medical_history' in patient_profile:
        medical_history = patient_profile['medical_history'].strip()
        if not medical_history:
            raise ValidationError("Medical history cannot be empty if provided")
        patient_profile['medical_history'] = medical_history
    
    return patient_profile


def initialize_hard_filter_engine() -> HardFilterEngine:
    """
    Initialize hard filter engine with database connection
    
    Returns:
        HardFilterEngine instance
        
    Raises:
        Exception: If initialization fails
    """
    # Get database connection parameters from environment variables
    db_host = os.environ.get('RDS_PROXY_ENDPOINT')
    db_name = os.environ.get('DB_NAME', 'trials_db')
    db_user = os.environ.get('DB_USER', 'postgres')
    db_password = os.environ.get('DB_PASSWORD')
    db_port = int(os.environ.get('DB_PORT', '5432'))
    
    if not db_host:
        raise Exception("RDS_PROXY_ENDPOINT environment variable not set")
    
    if not db_password:
        raise Exception("DB_PASSWORD environment variable not set")
    
    return HardFilterEngine(
        host=db_host,
        database=db_name,
        user=db_user,
        password=db_password,
        port=db_port
    )


def initialize_match_scorer() -> MatchScorer:
    """
    Initialize match scorer with medical matcher
    
    Returns:
        MatchScorer instance
        
    Raises:
        Exception: If initialization fails
    """
    # Get AWS region from environment
    aws_region = os.environ.get('AWS_REGION', 'us-east-1')
    
    # Initialize medical matcher with Bedrock client
    medical_matcher = MedicalMatcher(region_name=aws_region)
    
    # Initialize match scorer
    return MatchScorer(medical_matcher=medical_matcher)


def convert_to_trial_objects(trials: List[Dict[str, Any]]) -> List[Trial]:
    """
    Convert trial dictionaries to Trial objects
    
    Args:
        trials: List of trial dictionaries from database
        
    Returns:
        List of Trial objects
    """
    trial_objects = []
    
    for trial_dict in trials:
        trial = Trial(
            id=trial_dict['id'],
            title=trial_dict['title'],
            condition=trial_dict['condition'],
            min_age=trial_dict.get('min_age'),
            max_age=trial_dict.get('max_age'),
            gender_criteria=trial_dict.get('gender_criteria'),
            location=trial_dict.get('location', ''),
            inclusion_text=trial_dict.get('inclusion_text', ''),
            exclusion_text=trial_dict.get('exclusion_text')
        )
        trial_objects.append(trial)
    
    return trial_objects


def format_response(
    match_results: List[Any],
    total_trials_considered: int,
    hard_filtered_count: int,
    processing_time_ms: float
) -> Dict[str, Any]:
    """
    Format match results into API response
    
    Args:
        match_results: List of MatchResult objects
        total_trials_considered: Total trials in database
        hard_filtered_count: Trials after hard filtering
        processing_time_ms: Total processing time in milliseconds
        
    Returns:
        Formatted response dictionary
    """
    matches = []
    
    for result in match_results:
        match = {
            'trial_id': result.trial_id,
            'title': result.title,
            'match_score': result.match_percentage,
            'explanation': result.explanation,
            'key_criteria': result.key_criteria,
            'location': result.location
        }
        
        if result.distance_miles is not None:
            match['distance_miles'] = result.distance_miles
        
        matches.append(match)
    
    return {
        'matches': matches,
        'total_trials_considered': total_trials_considered,
        'hard_filtered_count': hard_filtered_count,
        'processing_time_ms': round(processing_time_ms, 2)
    }


def emit_custom_metrics(
    total_trials: int,
    hard_filtered_count: int,
    matches_returned: int,
    match_scores: List[float]
) -> None:
    """
    Emit custom CloudWatch metrics for trial matching
    
    Args:
        total_trials: Total number of trials considered
        hard_filtered_count: Number of trials after hard filtering
        matches_returned: Number of matches returned to user
        match_scores: List of match scores (0-1 scale)
    """
    try:
        environment = os.environ.get('ENVIRONMENT', 'dev')
        
        metric_data = [
            {
                'MetricName': 'TrialsProcessed',
                'Value': total_trials,
                'Unit': 'Count',
                'Timestamp': datetime.utcnow(),
                'Dimensions': [
                    {
                        'Name': 'Environment',
                        'Value': environment
                    }
                ]
            },
            {
                'MetricName': 'HardFilteredTrials',
                'Value': hard_filtered_count,
                'Unit': 'Count',
                'Timestamp': datetime.utcnow(),
                'Dimensions': [
                    {
                        'Name': 'Environment',
                        'Value': environment
                    }
                ]
            },
            {
                'MetricName': 'MatchesReturned',
                'Value': matches_returned,
                'Unit': 'Count',
                'Timestamp': datetime.utcnow(),
                'Dimensions': [
                    {
                        'Name': 'Environment',
                        'Value': environment
                    }
                ]
            }
        ]
        
        # Add individual match scores
        for score in match_scores:
            metric_data.append({
                'MetricName': 'MatchScore',
                'Value': score,
                'Unit': 'None',
                'Timestamp': datetime.utcnow(),
                'Dimensions': [
                    {
                        'Name': 'Environment',
                        'Value': environment
                    }
                ]
            })
        
        # Emit metrics to CloudWatch
        cloudwatch_client.put_metric_data(
            Namespace='VitalMatch',
            MetricData=metric_data
        )
        
        logger.info(f"Emitted {len(metric_data)} custom metrics to CloudWatch")
        
    except Exception as e:
        # Don't fail the request if metrics emission fails
        logger.warning(f"Failed to emit custom metrics: {str(e)}")
