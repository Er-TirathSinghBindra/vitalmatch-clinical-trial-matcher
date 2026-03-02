"""
Unit tests for Amazon Bedrock Client

Tests cover:
- Client initialization
- Medical text analysis
- Prompt building
- Response parsing
- Error handling for various API failures
- Token limit handling
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError, BotoCoreError

from src.ai_matching.bedrock_client import BedrockClient, BedrockError


class TestBedrockClientInitialization:
    """Test Bedrock client initialization"""
    
    def test_client_initialization_success(self):
        """Test successful client initialization"""
        with patch('boto3.client') as mock_boto_client:
            mock_boto_client.return_value = Mock()
            
            client = BedrockClient(region_name="us-east-1")
            
            assert client is not None
            mock_boto_client.assert_called_once_with(
                service_name='bedrock-runtime',
                region_name='us-east-1'
            )
    
    def test_client_initialization_failure(self):
        """Test client initialization failure"""
        with patch('boto3.client', side_effect=Exception("AWS credentials not found")):
            with pytest.raises(BedrockError) as exc_info:
                BedrockClient()
            
            assert "Bedrock client initialization failed" in str(exc_info.value)


class TestPromptBuilding:
    """Test prompt template building"""
    
    def test_build_prompt_with_inclusion_only(self):
        """Test prompt building with only inclusion criteria"""
        client = BedrockClient()
        
        prompt = client._build_prompt(
            patient_history="Patient has diabetes and hypertension",
            inclusion_criteria="Must have diabetes",
            exclusion_criteria=None
        )
        
        assert "Patient has diabetes and hypertension" in prompt
        assert "Must have diabetes" in prompt
        assert "Trial Exclusion Criteria" not in prompt
        assert "Response Format (JSON only)" in prompt
    
    def test_build_prompt_with_inclusion_and_exclusion(self):
        """Test prompt building with both inclusion and exclusion criteria"""
        client = BedrockClient()
        
        prompt = client._build_prompt(
            patient_history="Patient has diabetes",
            inclusion_criteria="Must have diabetes",
            exclusion_criteria="Cannot have kidney disease"
        )
        
        assert "Patient has diabetes" in prompt
        assert "Must have diabetes" in prompt
        assert "Cannot have kidney disease" in prompt
        assert "Trial Exclusion Criteria" in prompt


class TestModelInvocation:
    """Test Bedrock model invocation"""
    
    def test_invoke_model_success(self):
        """Test successful model invocation"""
        with patch('boto3.client') as mock_boto_client:
            # Mock successful response
            mock_response = {
                'body': MagicMock(),
                'ResponseMetadata': {'HTTPStatusCode': 200}
            }
            mock_response['body'].read.return_value = json.dumps({
                'content': [
                    {
                        'text': json.dumps({
                            'match_score': 0.85,
                            'explanation': 'Good match',
                            'inclusion_match': True,
                            'exclusion_match': False
                        })
                    }
                ]
            }).encode('utf-8')
            
            mock_client = Mock()
            mock_client.invoke_model.return_value = mock_response
            mock_boto_client.return_value = mock_client
            
            client = BedrockClient()
            response = client._invoke_model("test prompt")
            
            assert 'content' in response
            assert len(response['content']) > 0
    
    def test_invoke_model_throttling_error(self):
        """Test handling of throttling errors"""
        with patch('boto3.client') as mock_boto_client:
            mock_client = Mock()
            mock_client.invoke_model.side_effect = ClientError(
                {'Error': {'Code': 'ThrottlingException', 'Message': 'Rate exceeded'}},
                'InvokeModel'
            )
            mock_boto_client.return_value = mock_client
            
            client = BedrockClient()
            
            with pytest.raises(BedrockError) as exc_info:
                client._invoke_model("test prompt")
            
            assert "rate limit exceeded" in str(exc_info.value).lower()
    
    def test_invoke_model_validation_error(self):
        """Test handling of validation errors"""
        with patch('boto3.client') as mock_boto_client:
            mock_client = Mock()
            mock_client.invoke_model.side_effect = ClientError(
                {'Error': {'Code': 'ValidationException', 'Message': 'Invalid input'}},
                'InvokeModel'
            )
            mock_boto_client.return_value = mock_client
            
            client = BedrockClient()
            
            with pytest.raises(BedrockError) as exc_info:
                client._invoke_model("test prompt")
            
            assert "Invalid request" in str(exc_info.value)
    
    def test_invoke_model_timeout_error(self):
        """Test handling of timeout errors"""
        with patch('boto3.client') as mock_boto_client:
            mock_client = Mock()
            mock_client.invoke_model.side_effect = ClientError(
                {'Error': {'Code': 'ModelTimeoutException', 'Message': 'Timeout'}},
                'InvokeModel'
            )
            mock_boto_client.return_value = mock_client
            
            client = BedrockClient()
            
            with pytest.raises(BedrockError) as exc_info:
                client._invoke_model("test prompt")
            
            assert "timed out" in str(exc_info.value).lower()
    
    def test_invoke_model_generic_client_error(self):
        """Test handling of generic client errors"""
        with patch('boto3.client') as mock_boto_client:
            mock_client = Mock()
            mock_client.invoke_model.side_effect = ClientError(
                {'Error': {'Code': 'UnknownError', 'Message': 'Something went wrong'}},
                'InvokeModel'
            )
            mock_boto_client.return_value = mock_client
            
            client = BedrockClient()
            
            with pytest.raises(BedrockError) as exc_info:
                client._invoke_model("test prompt")
            
            assert "Bedrock API error" in str(exc_info.value)
    
    def test_invoke_model_botocore_error(self):
        """Test handling of BotoCoreError"""
        with patch('boto3.client') as mock_boto_client:
            mock_client = Mock()
            mock_client.invoke_model.side_effect = BotoCoreError()
            mock_boto_client.return_value = mock_client
            
            client = BedrockClient()
            
            with pytest.raises(BedrockError) as exc_info:
                client._invoke_model("test prompt")
            
            assert "AWS SDK error" in str(exc_info.value)


class TestResponseParsing:
    """Test response parsing and validation"""
    
    def test_parse_valid_response(self):
        """Test parsing a valid response"""
        client = BedrockClient()
        
        response_body = {
            'content': [
                {
                    'text': json.dumps({
                        'match_score': 0.85,
                        'explanation': 'Patient meets inclusion criteria',
                        'inclusion_match': True,
                        'exclusion_match': False
                    })
                }
            ]
        }
        
        result = client._parse_response(response_body)
        
        assert result['match_score'] == 0.85
        assert result['explanation'] == 'Patient meets inclusion criteria'
        assert result['inclusion_match'] is True
        assert result['exclusion_match'] is False
    
    def test_parse_response_missing_content(self):
        """Test parsing response with missing content"""
        client = BedrockClient()
        
        response_body = {}
        
        with pytest.raises(BedrockError) as exc_info:
            client._parse_response(response_body)
        
        assert "Missing 'content'" in str(exc_info.value)
    
    def test_parse_response_empty_content(self):
        """Test parsing response with empty content"""
        client = BedrockClient()
        
        response_body = {'content': []}
        
        with pytest.raises(BedrockError) as exc_info:
            client._parse_response(response_body)
        
        assert "Empty content" in str(exc_info.value)
    
    def test_parse_response_missing_required_field(self):
        """Test parsing response with missing required field"""
        client = BedrockClient()
        
        response_body = {
            'content': [
                {
                    'text': json.dumps({
                        'match_score': 0.85,
                        'explanation': 'Test'
                        # Missing inclusion_match and exclusion_match
                    })
                }
            ]
        }
        
        with pytest.raises(BedrockError) as exc_info:
            client._parse_response(response_body)
        
        assert "Missing required field" in str(exc_info.value)
    
    def test_parse_response_invalid_match_score_range(self):
        """Test parsing response with match_score out of range"""
        client = BedrockClient()
        
        response_body = {
            'content': [
                {
                    'text': json.dumps({
                        'match_score': 1.5,  # Invalid: > 1.0
                        'explanation': 'Test',
                        'inclusion_match': True,
                        'exclusion_match': False
                    })
                }
            ]
        }
        
        with pytest.raises(BedrockError) as exc_info:
            client._parse_response(response_body)
        
        assert "Invalid match_score" in str(exc_info.value)
    
    def test_parse_response_invalid_boolean_type(self):
        """Test parsing response with non-boolean inclusion_match"""
        client = BedrockClient()
        
        response_body = {
            'content': [
                {
                    'text': json.dumps({
                        'match_score': 0.85,
                        'explanation': 'Test',
                        'inclusion_match': 'yes',  # Invalid: should be boolean
                        'exclusion_match': False
                    })
                }
            ]
        }
        
        with pytest.raises(BedrockError) as exc_info:
            client._parse_response(response_body)
        
        assert "must be a boolean" in str(exc_info.value)
    
    def test_parse_response_invalid_json(self):
        """Test parsing response with invalid JSON"""
        client = BedrockClient()
        
        response_body = {
            'content': [
                {
                    'text': 'This is not valid JSON'
                }
            ]
        }
        
        with pytest.raises(BedrockError) as exc_info:
            client._parse_response(response_body)
        
        assert "Invalid JSON" in str(exc_info.value)


class TestAnalyzeMedicalMatch:
    """Test the main analyze_medical_match method"""
    
    def test_analyze_medical_match_success(self):
        """Test successful medical match analysis"""
        with patch('boto3.client') as mock_boto_client:
            # Mock successful response
            mock_response = {
                'body': MagicMock(),
                'ResponseMetadata': {'HTTPStatusCode': 200}
            }
            mock_response['body'].read.return_value = json.dumps({
                'content': [
                    {
                        'text': json.dumps({
                            'match_score': 0.92,
                            'explanation': 'Excellent match: Patient has diabetes and is within age range',
                            'inclusion_match': True,
                            'exclusion_match': False
                        })
                    }
                ]
            }).encode('utf-8')
            
            mock_client = Mock()
            mock_client.invoke_model.return_value = mock_response
            mock_boto_client.return_value = mock_client
            
            client = BedrockClient()
            result = client.analyze_medical_match(
                patient_medical_history="Patient has type 2 diabetes, age 55",
                trial_inclusion_criteria="Must have diabetes, age 18-70",
                trial_exclusion_criteria="Cannot have kidney disease"
            )
            
            assert result['match_score'] == 0.92
            assert result['inclusion_match'] is True
            assert result['exclusion_match'] is False
            assert 'Excellent match' in result['explanation']
    
    def test_analyze_medical_match_with_exclusion_violation(self):
        """Test medical match analysis with exclusion criteria violation"""
        with patch('boto3.client') as mock_boto_client:
            # Mock response indicating exclusion violation
            mock_response = {
                'body': MagicMock(),
                'ResponseMetadata': {'HTTPStatusCode': 200}
            }
            mock_response['body'].read.return_value = json.dumps({
                'content': [
                    {
                        'text': json.dumps({
                            'match_score': 0.15,
                            'explanation': 'Poor match: Patient has kidney disease which is excluded',
                            'inclusion_match': True,
                            'exclusion_match': True
                        })
                    }
                ]
            }).encode('utf-8')
            
            mock_client = Mock()
            mock_client.invoke_model.return_value = mock_response
            mock_boto_client.return_value = mock_client
            
            client = BedrockClient()
            result = client.analyze_medical_match(
                patient_medical_history="Patient has diabetes and kidney disease",
                trial_inclusion_criteria="Must have diabetes",
                trial_exclusion_criteria="Cannot have kidney disease"
            )
            
            assert result['match_score'] < 0.3
            assert result['exclusion_match'] is True
    
    def test_analyze_medical_match_api_failure(self):
        """Test medical match analysis with API failure"""
        with patch('boto3.client') as mock_boto_client:
            mock_client = Mock()
            mock_client.invoke_model.side_effect = ClientError(
                {'Error': {'Code': 'ThrottlingException', 'Message': 'Rate exceeded'}},
                'InvokeModel'
            )
            mock_boto_client.return_value = mock_client
            
            client = BedrockClient()
            
            with pytest.raises(BedrockError):
                client.analyze_medical_match(
                    patient_medical_history="Test history",
                    trial_inclusion_criteria="Test criteria"
                )


class TestTokenLimitHandling:
    """Test token limit configuration"""
    
    def test_max_tokens_configuration(self):
        """Test that max tokens is properly configured"""
        client = BedrockClient()
        
        assert client.MAX_RESPONSE_TOKENS == 500
        assert hasattr(client, 'MODEL_ID')
        assert client.MODEL_ID == "anthropic.claude-3-sonnet-20240229-v1:0"
    
    def test_invoke_model_includes_token_limit(self):
        """Test that model invocation includes token limit"""
        with patch('boto3.client') as mock_boto_client:
            mock_response = {
                'body': MagicMock(),
                'ResponseMetadata': {'HTTPStatusCode': 200}
            }
            mock_response['body'].read.return_value = json.dumps({
                'content': [{'text': '{"match_score": 0.5, "explanation": "test", "inclusion_match": true, "exclusion_match": false}'}]
            }).encode('utf-8')
            
            mock_client = Mock()
            mock_client.invoke_model.return_value = mock_response
            mock_boto_client.return_value = mock_client
            
            client = BedrockClient()
            client._invoke_model("test prompt")
            
            # Verify invoke_model was called with correct parameters
            call_args = mock_client.invoke_model.call_args
            body = json.loads(call_args[1]['body'])
            
            assert body['max_tokens'] == 500
            assert body['temperature'] == 0.3


class TestMedicalTerminologyVariations:
    """Test handling of medical terminology variations"""
    
    def test_prompt_mentions_terminology_variations(self):
        """Test that prompt instructs model to handle terminology variations"""
        client = BedrockClient()
        
        prompt = client._build_prompt(
            patient_history="Patient has high blood pressure",
            inclusion_criteria="Must have hypertension",
            exclusion_criteria=None
        )
        
        # Verify prompt includes instructions for terminology variations
        assert "terminology variations" in prompt.lower()
        assert "hypertension" in prompt.lower()
        assert "high blood pressure" in prompt.lower()
