"""
Integration tests for Match Trials Lambda Function

Tests cover:
- Complete flow from API request to response
- Various patient profiles
- Error handling for invalid inputs
- Performance with large trial datasets
- Requirements: US2, US3
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from match_trials import (
    lambda_handler,
    parse_and_validate_request,
    initialize_hard_filter_engine,
    initialize_match_scorer,
    convert_to_trial_objects,
    format_response,
    ValidationError
)
from hard_filter.filter_engine import FilterResult
from ai_matching.match_scorer import MatchResult


class TestLambdaHandlerIntegration:
    """Test complete Lambda handler flow"""
    
    @patch('match_trials.initialize_match_scorer')
    @patch('match_trials.initialize_hard_filter_engine')
    def test_successful_match_request(self, mock_hard_filter, mock_scorer):
        """Test successful match request with valid patient profile"""
        # Setup mocks
        mock_engine = Mock()
        mock_engine.filter_trials.return_value = FilterResult(
            trials=[
                {
                    'id': 'NCT12345678',
                    'title': 'Diabetes Trial',
                    'condition': 'Diabetes',
                    'min_age': 18,
                    'max_age': 70,
                    'gender_criteria': 'All',
                    'location': 'New York, NY',
                    'inclusion_text': 'Must have type 2 diabetes',
                    'exclusion_text': 'No kidney disease'
                }
            ],
            total_count=1000,
            filtered_count=1,
            processing_time_ms=150.5,
            filters_applied=['condition', 'age_range', 'gender']
        )
        mock_hard_filter.return_value = mock_engine

        
        mock_scorer_instance = Mock()
        mock_scorer_instance.score_and_rank_trials.return_value = [
            MatchResult(
                trial_id='NCT12345678',
                title='Diabetes Trial',
                match_score=92.0,
                match_percentage='92%',
                explanation='Excellent match',
                key_criteria=['✅ Age requirement met', '✅ Condition matches'],
                location='New York, NY',
                distance_miles=10.5
            )
        ]
        mock_scorer.return_value = mock_scorer_instance
        
        # Create test event
        event = {
            'body': json.dumps({
                'patient_profile': {
                    'condition': 'Diabetes',
                    'age': 45,
                    'gender': 'Male',
                    'location': 'New York',
                    'distance_miles': 50,
                    'medical_history': 'Type 2 diabetes, controlled with metformin'
                }
            })
        }
        
        # Create mock context
        context = Mock()
        context.request_id = 'test-request-123'
        
        # Execute Lambda handler
        response = lambda_handler(event, context)
        
        # Verify response
        assert response['statusCode'] == 200
        assert 'body' in response
        
        body = json.loads(response['body'])
        assert 'matches' in body
        assert len(body['matches']) == 1
        assert body['matches'][0]['trial_id'] == 'NCT12345678'
        assert body['matches'][0]['match_score'] == '92%'
        assert body['total_trials_considered'] == 1000
        assert body['hard_filtered_count'] == 1
        assert 'processing_time_ms' in body

    
    @patch('match_trials.initialize_match_scorer')
    @patch('match_trials.initialize_hard_filter_engine')
    def test_multiple_matches_returned(self, mock_hard_filter, mock_scorer):
        """Test Lambda returns multiple matches ranked by score"""
        # Setup mocks with multiple trials
        mock_engine = Mock()
        mock_engine.filter_trials.return_value = FilterResult(
            trials=[
                {'id': 'NCT001', 'title': 'Trial 1', 'condition': 'Diabetes', 
                 'min_age': 18, 'max_age': 70, 'gender_criteria': 'All',
                 'location': 'New York, NY', 'inclusion_text': 'Diabetes', 'exclusion_text': None},
                {'id': 'NCT002', 'title': 'Trial 2', 'condition': 'Diabetes',
                 'min_age': 18, 'max_age': 70, 'gender_criteria': 'All',
                 'location': 'Boston, MA', 'inclusion_text': 'Diabetes', 'exclusion_text': None},
                {'id': 'NCT003', 'title': 'Trial 3', 'condition': 'Diabetes',
                 'min_age': 18, 'max_age': 70, 'gender_criteria': 'All',
                 'location': 'Philadelphia, PA', 'inclusion_text': 'Diabetes', 'exclusion_text': None}
            ],
            total_count=1000,
            filtered_count=3,
            processing_time_ms=200.0,
            filters_applied=['condition', 'age_range']
        )
        mock_hard_filter.return_value = mock_engine
        
        mock_scorer_instance = Mock()
        mock_scorer_instance.score_and_rank_trials.return_value = [
            MatchResult('NCT001', 'Trial 1', 95.0, '95%', 'Excellent', ['✅ Perfect'], 'New York, NY', 10.0),
            MatchResult('NCT002', 'Trial 2', 85.0, '85%', 'Good', ['✅ Good'], 'Boston, MA', 25.0),
            MatchResult('NCT003', 'Trial 3', 75.0, '75%', 'Moderate', ['⚠️ Moderate'], 'Philadelphia, PA', 40.0)
        ]
        mock_scorer.return_value = mock_scorer_instance
        
        event = {
            'body': json.dumps({
                'patient_profile': {
                    'condition': 'Diabetes',
                    'age': 45,
                    'gender': 'Male',
                    'location': 'New York',
                    'medical_history': 'Type 2 diabetes'
                }
            })
        }
        
        context = Mock()
        context.request_id = 'test-request-456'
        
        response = lambda_handler(event, context)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert len(body['matches']) == 3
        # Verify ranking (highest score first)
        assert body['matches'][0]['match_score'] == '95%'
        assert body['matches'][1]['match_score'] == '85%'
        assert body['matches'][2]['match_score'] == '75%'

    
    @patch('match_trials.initialize_match_scorer')
    @patch('match_trials.initialize_hard_filter_engine')
    def test_no_matches_found(self, mock_hard_filter, mock_scorer):
        """Test Lambda handles case with no matching trials"""
        mock_engine = Mock()
        mock_engine.filter_trials.return_value = FilterResult(
            trials=[],
            total_count=1000,
            filtered_count=0,
            processing_time_ms=100.0,
            filters_applied=['condition', 'age_range']
        )
        mock_hard_filter.return_value = mock_engine
        
        mock_scorer_instance = Mock()
        mock_scorer_instance.score_and_rank_trials.return_value = []
        mock_scorer.return_value = mock_scorer_instance
        
        event = {
            'body': json.dumps({
                'patient_profile': {
                    'condition': 'Rare Disease',
                    'age': 45,
                    'gender': 'Male',
                    'location': 'New York',
                    'medical_history': 'Rare condition'
                }
            })
        }
        
        context = Mock()
        context.request_id = 'test-request-789'
        
        response = lambda_handler(event, context)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['matches'] == []
        assert body['total_trials_considered'] == 1000
        assert body['hard_filtered_count'] == 0


class TestInputValidation:
    """Test input validation and error handling"""
    
    def test_missing_patient_profile(self):
        """Test validation error for missing patient_profile"""
        event = {
            'body': json.dumps({})
        }
        
        context = Mock()
        context.request_id = 'test-validation-1'
        
        response = lambda_handler(event, context)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'error' in body
        assert 'patient_profile' in body['message'].lower()

    
    def test_missing_required_fields(self):
        """Test validation error for missing required fields"""
        event = {
            'body': json.dumps({
                'patient_profile': {
                    'condition': 'Diabetes',
                    'age': 45
                    # Missing gender and location
                }
            })
        }
        
        context = Mock()
        context.request_id = 'test-validation-2'
        
        response = lambda_handler(event, context)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'Missing required fields' in body['message']
    
    def test_invalid_age(self):
        """Test validation error for invalid age"""
        event = {
            'body': json.dumps({
                'patient_profile': {
                    'condition': 'Diabetes',
                    'age': 150,  # Invalid age
                    'gender': 'Male',
                    'location': 'New York'
                }
            })
        }
        
        context = Mock()
        context.request_id = 'test-validation-3'
        
        response = lambda_handler(event, context)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'Age must be between 0 and 120' in body['message']
    
    def test_invalid_gender(self):
        """Test validation error for invalid gender"""
        event = {
            'body': json.dumps({
                'patient_profile': {
                    'condition': 'Diabetes',
                    'age': 45,
                    'gender': 'InvalidGender',
                    'location': 'New York'
                }
            })
        }
        
        context = Mock()
        context.request_id = 'test-validation-4'
        
        response = lambda_handler(event, context)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'Gender must be one of' in body['message']
    
    def test_invalid_json(self):
        """Test validation error for invalid JSON"""
        event = {
            'body': 'invalid json {'
        }
        
        context = Mock()
        context.request_id = 'test-validation-5'
        
        response = lambda_handler(event, context)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'Invalid JSON' in body['message']

    
    def test_empty_condition(self):
        """Test validation error for empty condition"""
        event = {
            'body': json.dumps({
                'patient_profile': {
                    'condition': '',
                    'age': 45,
                    'gender': 'Male',
                    'location': 'New York'
                }
            })
        }
        
        context = Mock()
        context.request_id = 'test-validation-6'
        
        response = lambda_handler(event, context)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'Missing required fields' in body['message']
    
    def test_invalid_distance_miles(self):
        """Test validation error for invalid distance"""
        event = {
            'body': json.dumps({
                'patient_profile': {
                    'condition': 'Diabetes',
                    'age': 45,
                    'gender': 'Male',
                    'location': 'New York',
                    'distance_miles': 1000  # Too large
                }
            })
        }
        
        context = Mock()
        context.request_id = 'test-validation-7'
        
        response = lambda_handler(event, context)
        
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert 'Distance must be between 1 and 500 miles' in body['message']


class TestVariousPatientProfiles:
    """Test with various patient profiles"""
    
    @patch('match_trials.initialize_match_scorer')
    @patch('match_trials.initialize_hard_filter_engine')
    def test_elderly_patient_profile(self, mock_hard_filter, mock_scorer):
        """Test with elderly patient profile"""
        mock_engine = Mock()
        mock_engine.filter_trials.return_value = FilterResult(
            trials=[{'id': 'NCT001', 'title': 'Elderly Trial', 'condition': 'Hypertension',
                    'min_age': 65, 'max_age': 90, 'gender_criteria': 'All',
                    'location': 'Boston, MA', 'inclusion_text': 'Elderly with hypertension',
                    'exclusion_text': None}],
            total_count=500,
            filtered_count=1,
            processing_time_ms=120.0,
            filters_applied=['condition', 'age_range']
        )
        mock_hard_filter.return_value = mock_engine
        
        mock_scorer_instance = Mock()
        mock_scorer_instance.score_and_rank_trials.return_value = [
            MatchResult('NCT001', 'Elderly Trial', 88.0, '88%', 'Good match', 
                       ['✅ Age appropriate'], 'Boston, MA', 15.0)
        ]
        mock_scorer.return_value = mock_scorer_instance
        
        event = {
            'body': json.dumps({
                'patient_profile': {
                    'condition': 'Hypertension',
                    'age': 75,
                    'gender': 'Female',
                    'location': 'Boston',
                    'medical_history': 'High blood pressure for 10 years'
                }
            })
        }
        
        context = Mock()
        context.request_id = 'test-elderly'
        
        response = lambda_handler(event, context)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert len(body['matches']) == 1
        assert body['matches'][0]['trial_id'] == 'NCT001'

    
    @patch('match_trials.initialize_match_scorer')
    @patch('match_trials.initialize_hard_filter_engine')
    def test_young_patient_profile(self, mock_hard_filter, mock_scorer):
        """Test with young patient profile"""
        mock_engine = Mock()
        mock_engine.filter_trials.return_value = FilterResult(
            trials=[{'id': 'NCT002', 'title': 'Pediatric Trial', 'condition': 'Asthma',
                    'min_age': 5, 'max_age': 18, 'gender_criteria': 'All',
                    'location': 'Chicago, IL', 'inclusion_text': 'Children with asthma',
                    'exclusion_text': None}],
            total_count=300,
            filtered_count=1,
            processing_time_ms=110.0,
            filters_applied=['condition', 'age_range']
        )
        mock_hard_filter.return_value = mock_engine
        
        mock_scorer_instance = Mock()
        mock_scorer_instance.score_and_rank_trials.return_value = [
            MatchResult('NCT002', 'Pediatric Trial', 90.0, '90%', 'Excellent match',
                       ['✅ Age appropriate', '✅ Condition matches'], 'Chicago, IL', 20.0)
        ]
        mock_scorer.return_value = mock_scorer_instance
        
        event = {
            'body': json.dumps({
                'patient_profile': {
                    'condition': 'Asthma',
                    'age': 12,
                    'gender': 'Male',
                    'location': 'Chicago',
                    'medical_history': 'Asthma diagnosed at age 8'
                }
            })
        }
        
        context = Mock()
        context.request_id = 'test-young'
        
        response = lambda_handler(event, context)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert len(body['matches']) == 1
        assert body['matches'][0]['match_score'] == '90%'
    
    @patch('match_trials.initialize_match_scorer')
    @patch('match_trials.initialize_hard_filter_engine')
    def test_complex_medical_history(self, mock_hard_filter, mock_scorer):
        """Test with complex medical history"""
        mock_engine = Mock()
        mock_engine.filter_trials.return_value = FilterResult(
            trials=[{'id': 'NCT003', 'title': 'Complex Trial', 'condition': 'Cancer',
                    'min_age': 18, 'max_age': 75, 'gender_criteria': 'All',
                    'location': 'Houston, TX', 'inclusion_text': 'Cancer patients',
                    'exclusion_text': 'No active infections'}],
            total_count=800,
            filtered_count=1,
            processing_time_ms=180.0,
            filters_applied=['condition', 'age_range']
        )
        mock_hard_filter.return_value = mock_engine
        
        mock_scorer_instance = Mock()
        mock_scorer_instance.score_and_rank_trials.return_value = [
            MatchResult('NCT003', 'Complex Trial', 78.0, '78%', 'Good match',
                       ['✅ Primary condition matches', '⚠️ Multiple comorbidities noted'],
                       'Houston, TX', 30.0)
        ]
        mock_scorer.return_value = mock_scorer_instance
        
        event = {
            'body': json.dumps({
                'patient_profile': {
                    'condition': 'Cancer',
                    'age': 58,
                    'gender': 'Female',
                    'location': 'Houston',
                    'medical_history': 'Stage II breast cancer, history of hypertension, type 2 diabetes, currently on chemotherapy'
                }
            })
        }
        
        context = Mock()
        context.request_id = 'test-complex'
        
        response = lambda_handler(event, context)
        
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert len(body['matches']) == 1




class TestErrorHandling:
    """Test error handling scenarios"""
    
    @patch('match_trials.initialize_hard_filter_engine')
    def test_database_connection_error(self, mock_hard_filter):
        """Test handling of database connection errors"""
        mock_hard_filter.side_effect = Exception("Database connection failed")
        
        event = {
            'body': json.dumps({
                'patient_profile': {
                    'condition': 'Diabetes',
                    'age': 45,
                    'gender': 'Male',
                    'location': 'New York',
                    'medical_history': 'Type 2 diabetes'
                }
            })
        }
        
        context = Mock()
        context.request_id = 'test-db-error'
        
        response = lambda_handler(event, context)
        
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert 'error' in body
        assert body['error'] == 'Internal Server Error'
    
    @patch('match_trials.initialize_match_scorer')
    @patch('match_trials.initialize_hard_filter_engine')
    def test_ai_service_error(self, mock_hard_filter, mock_scorer):
        """Test handling of AI service errors"""
        mock_engine = Mock()
        mock_engine.filter_trials.return_value = FilterResult(
            trials=[{'id': 'NCT001', 'title': 'Trial', 'condition': 'Diabetes',
                    'min_age': 18, 'max_age': 70, 'gender_criteria': 'All',
                    'location': 'New York, NY', 'inclusion_text': 'Diabetes',
                    'exclusion_text': None}],
            total_count=100,
            filtered_count=1,
            processing_time_ms=100.0,
            filters_applied=['condition']
        )
        mock_hard_filter.return_value = mock_engine
        
        mock_scorer_instance = Mock()
        mock_scorer_instance.score_and_rank_trials.side_effect = Exception("Bedrock API error")
        mock_scorer.return_value = mock_scorer_instance
        
        event = {
            'body': json.dumps({
                'patient_profile': {
                    'condition': 'Diabetes',
                    'age': 45,
                    'gender': 'Male',
                    'location': 'New York',
                    'medical_history': 'Type 2 diabetes'
                }
            })
        }
        
        context = Mock()
        context.request_id = 'test-ai-error'
        
        response = lambda_handler(event, context)
        
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert 'error' in body


class TestResponseFormat:
    """Test response formatting"""
    
    def test_format_response_with_matches(self):
        """Test response formatting with matches"""
        match_results = [
            MatchResult(
                trial_id='NCT001',
                title='Trial 1',
                match_score=92.5,
                match_percentage='92%',
                explanation='Excellent match',
                key_criteria=['✅ Age met', '✅ Condition matches'],
                location='New York, NY',
                distance_miles=15.3
            ),
            MatchResult(
                trial_id='NCT002',
                title='Trial 2',
                match_score=85.0,
                match_percentage='85%',
                explanation='Good match',
                key_criteria=['✅ Condition matches'],
                location='Boston, MA',
                distance_miles=None
            )
        ]
        
        response = format_response(
            match_results=match_results,
            total_trials_considered=1000,
            hard_filtered_count=50,
            processing_time_ms=12345.678
        )
        
        assert response['total_trials_considered'] == 1000
        assert response['hard_filtered_count'] == 50
        assert response['processing_time_ms'] == 12345.68
        assert len(response['matches']) == 2
        
        # Check first match
        assert response['matches'][0]['trial_id'] == 'NCT001'
        assert response['matches'][0]['match_score'] == '92%'
        assert response['matches'][0]['distance_miles'] == 15.3
        
        # Check second match (no distance)
        assert response['matches'][1]['trial_id'] == 'NCT002'
        assert 'distance_miles' not in response['matches'][1]

    
    def test_format_response_empty_matches(self):
        """Test response formatting with no matches"""
        response = format_response(
            match_results=[],
            total_trials_considered=1000,
            hard_filtered_count=0,
            processing_time_ms=5000.0
        )
        
        assert response['matches'] == []
        assert response['total_trials_considered'] == 1000
        assert response['hard_filtered_count'] == 0
        assert response['processing_time_ms'] == 5000.0


class TestConvertToTrialObjects:
    """Test trial dictionary to object conversion"""
    
    def test_convert_single_trial(self):
        """Test converting single trial dictionary to Trial object"""
        trial_dicts = [
            {
                'id': 'NCT12345678',
                'title': 'Diabetes Trial',
                'condition': 'Diabetes',
                'min_age': 18,
                'max_age': 70,
                'gender_criteria': 'All',
                'location': 'New York, NY',
                'inclusion_text': 'Must have diabetes',
                'exclusion_text': 'No kidney disease'
            }
        ]
        
        trials = convert_to_trial_objects(trial_dicts)
        
        assert len(trials) == 1
        assert trials[0].id == 'NCT12345678'
        assert trials[0].title == 'Diabetes Trial'
        assert trials[0].condition == 'Diabetes'
        assert trials[0].min_age == 18
        assert trials[0].max_age == 70
        assert trials[0].gender_criteria == 'All'
        assert trials[0].location == 'New York, NY'
        assert trials[0].inclusion_text == 'Must have diabetes'
        assert trials[0].exclusion_text == 'No kidney disease'
    
    def test_convert_multiple_trials(self):
        """Test converting multiple trial dictionaries"""
        trial_dicts = [
            {'id': 'NCT001', 'title': 'Trial 1', 'condition': 'Diabetes',
             'min_age': 18, 'max_age': 70, 'gender_criteria': 'Male',
             'location': 'New York', 'inclusion_text': 'Diabetes', 'exclusion_text': None},
            {'id': 'NCT002', 'title': 'Trial 2', 'condition': 'Hypertension',
             'min_age': None, 'max_age': None, 'gender_criteria': None,
             'location': 'Boston', 'inclusion_text': 'Hypertension', 'exclusion_text': 'No diabetes'}
        ]
        
        trials = convert_to_trial_objects(trial_dicts)
        
        assert len(trials) == 2
        assert trials[0].id == 'NCT001'
        assert trials[1].id == 'NCT002'
        assert trials[1].min_age is None
        assert trials[1].max_age is None
    
    def test_convert_empty_list(self):
        """Test converting empty list"""
        trials = convert_to_trial_objects([])
        assert trials == []


class TestParseAndValidateRequest:
    """Test request parsing and validation"""
    
    def test_parse_valid_request(self):
        """Test parsing valid request"""
        event = {
            'body': json.dumps({
                'patient_profile': {
                    'condition': 'Diabetes',
                    'age': 45,
                    'gender': 'Male',
                    'location': 'New York',
                    'distance_miles': 50,
                    'medical_history': 'Type 2 diabetes'
                }
            })
        }
        
        profile = parse_and_validate_request(event)
        
        assert profile['condition'] == 'Diabetes'
        assert profile['age'] == 45
        assert profile['gender'] == 'Male'
        assert profile['location'] == 'New York'
        assert profile['distance_miles'] == 50
        assert profile['medical_history'] == 'Type 2 diabetes'
    
    def test_parse_request_with_dict_body(self):
        """Test parsing request with dict body (not string)"""
        event = {
            'body': {
                'patient_profile': {
                    'condition': 'Diabetes',
                    'age': 45,
                    'gender': 'Male',
                    'location': 'New York'
                }
            }
        }
        
        profile = parse_and_validate_request(event)
        
        assert profile['condition'] == 'Diabetes'
        assert profile['age'] == 45

    
    def test_parse_request_normalizes_gender(self):
        """Test that gender is normalized to capitalized form"""
        event = {
            'body': json.dumps({
                'patient_profile': {
                    'condition': 'Diabetes',
                    'age': 45,
                    'gender': 'male',  # lowercase
                    'location': 'New York'
                }
            })
        }
        
        profile = parse_and_validate_request(event)
        
        assert profile['gender'] == 'Male'  # Should be capitalized
    
    def test_parse_request_strips_whitespace(self):
        """Test that strings are stripped of whitespace"""
        event = {
            'body': json.dumps({
                'patient_profile': {
                    'condition': '  Diabetes  ',
                    'age': 45,
                    'gender': 'Male',
                    'location': '  New York  '
                }
            })
        }
        
        profile = parse_and_validate_request(event)
        
        assert profile['condition'] == 'Diabetes'
        assert profile['location'] == 'New York'
    
    def test_parse_request_validates_age_range(self):
        """Test age validation"""
        # Test negative age
        event = {
            'body': json.dumps({
                'patient_profile': {
                    'condition': 'Diabetes',
                    'age': -5,
                    'gender': 'Male',
                    'location': 'New York'
                }
            })
        }
        
        with pytest.raises(ValidationError) as exc_info:
            parse_and_validate_request(event)
        
        assert 'Age must be between 0 and 120' in str(exc_info.value)
    
    def test_parse_request_validates_distance_range(self):
        """Test distance validation"""
        event = {
            'body': json.dumps({
                'patient_profile': {
                    'condition': 'Diabetes',
                    'age': 45,
                    'gender': 'Male',
                    'location': 'New York',
                    'distance_miles': 0  # Too small
                }
            })
        }
        
        with pytest.raises(ValidationError) as exc_info:
            parse_and_validate_request(event)
        
        assert 'Distance must be between 1 and 500 miles' in str(exc_info.value)


class TestCORSHeaders:
    """Test CORS headers in responses"""
    
    @patch('match_trials.initialize_match_scorer')
    @patch('match_trials.initialize_hard_filter_engine')
    def test_cors_headers_in_success_response(self, mock_hard_filter, mock_scorer):
        """Test CORS headers are present in successful response"""
        mock_engine = Mock()
        mock_engine.filter_trials.return_value = FilterResult(
            trials=[], total_count=0, filtered_count=0,
            processing_time_ms=100.0, filters_applied=[]
        )
        mock_hard_filter.return_value = mock_engine
        
        mock_scorer_instance = Mock()
        mock_scorer_instance.score_and_rank_trials.return_value = []
        mock_scorer.return_value = mock_scorer_instance
        
        event = {
            'body': json.dumps({
                'patient_profile': {
                    'condition': 'Diabetes',
                    'age': 45,
                    'gender': 'Male',
                    'location': 'New York',
                    'medical_history': 'Diabetes'
                }
            })
        }
        
        context = Mock()
        context.request_id = 'test-cors'
        
        response = lambda_handler(event, context)
        
        assert 'Access-Control-Allow-Origin' in response['headers']
        assert response['headers']['Access-Control-Allow-Origin'] == '*'
        assert 'Access-Control-Allow-Headers' in response['headers']
        assert 'Access-Control-Allow-Methods' in response['headers']
    
    def test_cors_headers_in_error_response(self):
        """Test CORS headers are present in error response"""
        event = {
            'body': json.dumps({})  # Missing patient_profile
        }
        
        context = Mock()
        context.request_id = 'test-cors-error'
        
        response = lambda_handler(event, context)
        
        assert response['statusCode'] == 400
        assert 'Access-Control-Allow-Origin' in response['headers']
        assert response['headers']['Access-Control-Allow-Origin'] == '*'


class TestPerformanceMetrics:
    """Test performance metrics logging"""
    
    @patch('match_trials.initialize_match_scorer')
    @patch('match_trials.initialize_hard_filter_engine')
    def test_processing_time_included_in_response(self, mock_hard_filter, mock_scorer):
        """Test that processing time is included in response"""
        mock_engine = Mock()
        mock_engine.filter_trials.return_value = FilterResult(
            trials=[], total_count=100, filtered_count=0,
            processing_time_ms=150.5, filters_applied=['condition']
        )
        mock_hard_filter.return_value = mock_engine
        
        mock_scorer_instance = Mock()
        mock_scorer_instance.score_and_rank_trials.return_value = []
        mock_scorer.return_value = mock_scorer_instance
        
        event = {
            'body': json.dumps({
                'patient_profile': {
                    'condition': 'Diabetes',
                    'age': 45,
                    'gender': 'Male',
                    'location': 'New York',
                    'medical_history': 'Diabetes'
                }
            })
        }
        
        context = Mock()
        context.request_id = 'test-perf'
        
        response = lambda_handler(event, context)
        
        body = json.loads(response['body'])
        assert 'processing_time_ms' in body
        assert isinstance(body['processing_time_ms'], (int, float))
        assert body['processing_time_ms'] > 0
