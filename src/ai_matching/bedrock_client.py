"""
Amazon Bedrock Client for Medical Text Analysis

This module provides a client for Amazon Bedrock to analyze medical text
and match patient medical histories with clinical trial eligibility criteria.
Uses Claude 3 Sonnet for intelligent medical terminology understanding.
"""

import json
import logging
from typing import Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError, BotoCoreError

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class BedrockError(Exception):
    """Custom exception for Bedrock API errors"""
    pass


class BedrockClient:
    """
    Client for Amazon Bedrock medical text analysis using Claude 3 Sonnet.
    
    This client handles:
    - Medical history matching with trial inclusion/exclusion criteria
    - Medical terminology variation handling
    - Token limit management (max 500 tokens for response)
    - Comprehensive error handling for API failures
    """
    
    # Model configuration
    MODEL_ID = "anthropic.claude-3-sonnet-20240229-v1:0"
    MAX_RESPONSE_TOKENS = 500
    TEMPERATURE = 0.3  # Lower temperature for more consistent medical analysis
    
    def __init__(self, region_name: str = "us-east-1"):
        """
        Initialize Bedrock runtime client.
        
        Args:
            region_name: AWS region for Bedrock service (default: us-east-1)
        
        Raises:
            BedrockError: If client initialization fails
        """
        try:
            self.client = boto3.client(
                service_name='bedrock-runtime',
                region_name=region_name
            )
            logger.info(f"Bedrock client initialized successfully in region {region_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock client: {str(e)}")
            raise BedrockError(f"Bedrock client initialization failed: {str(e)}")
    
    def analyze_medical_match(
        self,
        patient_medical_history: str,
        trial_inclusion_criteria: str,
        trial_exclusion_criteria: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze if patient medical history matches trial eligibility criteria.
        
        Args:
            patient_medical_history: Patient's medical history text
            trial_inclusion_criteria: Trial's inclusion criteria text
            trial_exclusion_criteria: Trial's exclusion criteria text (optional)
        
        Returns:
            Dictionary containing:
                - match_score: Float between 0-1 indicating match quality
                - explanation: String explaining the match reasoning
                - inclusion_match: Boolean indicating if inclusion criteria are met
                - exclusion_match: Boolean indicating if exclusion criteria are violated
        
        Raises:
            BedrockError: If API call fails or response is invalid
        """
        try:
            # Build the prompt
            prompt = self._build_prompt(
                patient_medical_history,
                trial_inclusion_criteria,
                trial_exclusion_criteria
            )
            
            # Invoke Bedrock model
            response = self._invoke_model(prompt)
            
            # Parse and validate response
            result = self._parse_response(response)
            
            logger.info(f"Medical match analysis completed. Score: {result['match_score']}")
            return result
            
        except BedrockError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in analyze_medical_match: {str(e)}")
            raise BedrockError(f"Medical match analysis failed: {str(e)}")
    
    def _build_prompt(
        self,
        patient_history: str,
        inclusion_criteria: str,
        exclusion_criteria: Optional[str]
    ) -> str:
        """
        Build the prompt for Claude 3 Sonnet medical analysis.
        
        Args:
            patient_history: Patient's medical history
            inclusion_criteria: Trial inclusion criteria
            exclusion_criteria: Trial exclusion criteria (optional)
        
        Returns:
            Formatted prompt string
        """
        prompt = f"""You are a medical expert analyzing clinical trial eligibility. 
Your task is to determine if a patient's medical history matches a clinical trial's eligibility criteria.

**Patient Medical History:**
{patient_history}

**Trial Inclusion Criteria:**
{inclusion_criteria}
"""
        
        if exclusion_criteria:
            prompt += f"""
**Trial Exclusion Criteria:**
{exclusion_criteria}
"""
        
        prompt += """
**Instructions:**
1. Analyze if the patient's medical history aligns with the inclusion criteria
2. Check if any exclusion criteria are violated
3. Consider medical terminology variations (e.g., "hypertension" = "high blood pressure")
4. Provide a match score from 0.0 to 1.0 where:
   - 0.0-0.3: Poor match (exclusion criteria violated or major inclusion criteria not met)
   - 0.4-0.6: Moderate match (some criteria met, some unclear)
   - 0.7-0.9: Good match (most criteria met)
   - 0.9-1.0: Excellent match (all criteria clearly met)

**Response Format (JSON only):**
{
  "match_score": <float between 0.0 and 1.0>,
  "explanation": "<brief explanation of the match reasoning>",
  "inclusion_match": <true if inclusion criteria are met, false otherwise>,
  "exclusion_match": <true if exclusion criteria are violated, false otherwise>
}

Respond with ONLY the JSON object, no additional text.
"""
        return prompt
    
    def _invoke_model(self, prompt: str) -> Dict[str, Any]:
        """
        Invoke Bedrock model with the given prompt.
        
        Args:
            prompt: The prompt to send to the model
        
        Returns:
            Raw response from Bedrock API
        
        Raises:
            BedrockError: If API call fails
        """
        try:
            # Prepare request body for Claude 3 Sonnet
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": self.MAX_RESPONSE_TOKENS,
                "temperature": self.TEMPERATURE,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            logger.debug(f"Invoking Bedrock model: {self.MODEL_ID}")
            
            # Invoke the model
            response = self.client.invoke_model(
                modelId=self.MODEL_ID,
                body=json.dumps(request_body),
                contentType="application/json",
                accept="application/json"
            )
            
            # Parse response body
            response_body = json.loads(response['body'].read())
            
            logger.debug("Bedrock model invocation successful")
            return response_body
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_message = e.response.get('Error', {}).get('Message', str(e))
            
            # Handle specific error types
            if error_code == 'ThrottlingException':
                logger.error("Bedrock API throttling detected")
                raise BedrockError("Bedrock API rate limit exceeded. Please retry later.")
            elif error_code == 'ValidationException':
                logger.error(f"Bedrock API validation error: {error_message}")
                raise BedrockError(f"Invalid request to Bedrock API: {error_message}")
            elif error_code == 'ModelTimeoutException':
                logger.error("Bedrock model timeout")
                raise BedrockError("Bedrock model request timed out. Please retry.")
            else:
                logger.error(f"Bedrock API error: {error_code} - {error_message}")
                raise BedrockError(f"Bedrock API error: {error_message}")
                
        except BotoCoreError as e:
            logger.error(f"Boto3 error: {str(e)}")
            raise BedrockError(f"AWS SDK error: {str(e)}")
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Bedrock response: {str(e)}")
            raise BedrockError("Invalid JSON response from Bedrock API")
            
        except Exception as e:
            logger.error(f"Unexpected error invoking Bedrock: {str(e)}")
            raise BedrockError(f"Unexpected error: {str(e)}")
    
    def _parse_response(self, response_body: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse and validate Bedrock response.
        
        Args:
            response_body: Raw response from Bedrock API
        
        Returns:
            Parsed and validated result dictionary
        
        Raises:
            BedrockError: If response format is invalid
        """
        try:
            # Extract content from Claude response
            if 'content' not in response_body:
                raise BedrockError("Missing 'content' in Bedrock response")
            
            content_blocks = response_body['content']
            if not content_blocks or len(content_blocks) == 0:
                raise BedrockError("Empty content in Bedrock response")
            
            # Get the text content
            text_content = content_blocks[0].get('text', '')
            if not text_content:
                raise BedrockError("No text content in Bedrock response")
            
            # Parse JSON from text content
            result = json.loads(text_content.strip())
            
            # Validate required fields
            required_fields = ['match_score', 'explanation', 'inclusion_match', 'exclusion_match']
            for field in required_fields:
                if field not in result:
                    raise BedrockError(f"Missing required field '{field}' in response")
            
            # Validate match_score range
            match_score = result['match_score']
            if not isinstance(match_score, (int, float)) or not (0.0 <= match_score <= 1.0):
                raise BedrockError(f"Invalid match_score: {match_score}. Must be between 0.0 and 1.0")
            
            # Validate boolean fields
            if not isinstance(result['inclusion_match'], bool):
                raise BedrockError("inclusion_match must be a boolean")
            if not isinstance(result['exclusion_match'], bool):
                raise BedrockError("exclusion_match must be a boolean")
            
            # Validate explanation is a string
            if not isinstance(result['explanation'], str):
                raise BedrockError("explanation must be a string")
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from Bedrock response: {str(e)}")
            raise BedrockError(f"Invalid JSON in Bedrock response: {str(e)}")
            
        except BedrockError:
            raise
            
        except Exception as e:
            logger.error(f"Unexpected error parsing response: {str(e)}")
            raise BedrockError(f"Response parsing failed: {str(e)}")
