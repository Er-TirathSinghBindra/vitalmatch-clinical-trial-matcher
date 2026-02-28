"""
Medical Terminology Matching Logic

This module provides intelligent medical terminology matching between patient
medical histories and clinical trial eligibility criteria. It uses Amazon Bedrock
for AI-powered medical text analysis and implements caching for performance.

Key Features:
- Medical terminology variation handling (e.g., "hypertension" vs "high blood pressure")
- Exclusion criteria penalty logic
- Caching for common medical term mappings
- Comprehensive error handling
"""

import logging
from typing import Dict, Any, Optional, Tuple
from functools import lru_cache

from .bedrock_client import BedrockClient, BedrockError

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class MedicalMatcherError(Exception):
    """Custom exception for medical matcher errors"""
    pass


class MedicalMatcher:
    """
    Medical terminology matcher using Amazon Bedrock for intelligent matching.
    
    This class handles:
    - Comparing patient medical history with trial inclusion/exclusion criteria
    - Medical terminology variation handling
    - Exclusion criteria penalty logic (reduces score if exclusion violated)
    - Caching for performance optimization
    """
    
    # Exclusion penalty configuration
    EXCLUSION_PENALTY_THRESHOLD = 0.3  # Score reduced to <0.3 if exclusion violated
    
    def __init__(self, bedrock_client: Optional[BedrockClient] = None, region_name: str = "us-east-1"):
        """
        Initialize Medical Matcher with Bedrock client.
        
        Args:
            bedrock_client: Optional BedrockClient instance (creates new if None)
            region_name: AWS region for Bedrock service (default: us-east-1)
        
        Raises:
            MedicalMatcherError: If initialization fails
        """
        try:
            self.bedrock_client = bedrock_client or BedrockClient(region_name=region_name)
            self._term_cache = {}  # Simple dict cache for medical term mappings
            logger.info("MedicalMatcher initialized successfully")
        except BedrockError as e:
            logger.error(f"Failed to initialize MedicalMatcher: {str(e)}")
            raise MedicalMatcherError(f"MedicalMatcher initialization failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error initializing MedicalMatcher: {str(e)}")
            raise MedicalMatcherError(f"Unexpected initialization error: {str(e)}")
    
    def match_patient_to_trial(
        self,
        patient_medical_history: str,
        trial_inclusion_criteria: str,
        trial_exclusion_criteria: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Match patient medical history with trial eligibility criteria.
        
        This method:
        1. Validates input parameters
        2. Calls Bedrock for AI-powered medical text analysis
        3. Applies exclusion criteria penalty if needed
        4. Returns comprehensive match result
        
        Args:
            patient_medical_history: Patient's medical history text
            trial_inclusion_criteria: Trial's inclusion criteria text
            trial_exclusion_criteria: Trial's exclusion criteria text (optional)
        
        Returns:
            Dictionary containing:
                - match_score: Float between 0-1 (adjusted for exclusion penalty)
                - original_score: Float between 0-1 (before exclusion penalty)
                - explanation: String explaining the match reasoning
                - inclusion_match: Boolean indicating if inclusion criteria are met
                - exclusion_match: Boolean indicating if exclusion criteria are violated
                - exclusion_penalty_applied: Boolean indicating if penalty was applied
        
        Raises:
            MedicalMatcherError: If matching fails or input is invalid
        """
        try:
            # Validate inputs
            self._validate_inputs(patient_medical_history, trial_inclusion_criteria)
            
            # Check cache for this specific combination
            cache_key = self._generate_cache_key(
                patient_medical_history,
                trial_inclusion_criteria,
                trial_exclusion_criteria
            )
            
            if cache_key in self._term_cache:
                logger.info("Returning cached match result")
                return self._term_cache[cache_key]
            
            # Call Bedrock for AI analysis
            logger.info("Analyzing medical match with Bedrock")
            bedrock_result = self.bedrock_client.analyze_medical_match(
                patient_medical_history=patient_medical_history,
                trial_inclusion_criteria=trial_inclusion_criteria,
                trial_exclusion_criteria=trial_exclusion_criteria
            )
            
            # Apply exclusion criteria penalty
            result = self._apply_exclusion_penalty(bedrock_result)
            
            # Cache the result
            self._term_cache[cache_key] = result
            
            logger.info(f"Match completed. Final score: {result['match_score']}")
            return result
            
        except BedrockError as e:
            logger.error(f"Bedrock error during matching: {str(e)}")
            raise MedicalMatcherError(f"Medical matching failed: {str(e)}")
        except MedicalMatcherError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during matching: {str(e)}")
            raise MedicalMatcherError(f"Unexpected matching error: {str(e)}")
    
    def _validate_inputs(
        self,
        patient_medical_history: str,
        trial_inclusion_criteria: str
    ) -> None:
        """
        Validate input parameters.
        
        Args:
            patient_medical_history: Patient's medical history
            trial_inclusion_criteria: Trial's inclusion criteria
        
        Raises:
            MedicalMatcherError: If inputs are invalid
        """
        if not patient_medical_history or not isinstance(patient_medical_history, str):
            raise MedicalMatcherError("patient_medical_history must be a non-empty string")
        
        if not trial_inclusion_criteria or not isinstance(trial_inclusion_criteria, str):
            raise MedicalMatcherError("trial_inclusion_criteria must be a non-empty string")
        
        if not patient_medical_history.strip():
            raise MedicalMatcherError("patient_medical_history cannot be empty or whitespace")
        
        if not trial_inclusion_criteria.strip():
            raise MedicalMatcherError("trial_inclusion_criteria cannot be empty or whitespace")
    
    def _generate_cache_key(
        self,
        patient_history: str,
        inclusion_criteria: str,
        exclusion_criteria: Optional[str]
    ) -> str:
        """
        Generate cache key for medical term mapping.
        
        Args:
            patient_history: Patient's medical history
            inclusion_criteria: Trial inclusion criteria
            exclusion_criteria: Trial exclusion criteria (optional)
        
        Returns:
            Cache key string
        """
        # Create a simple hash-based cache key
        exclusion_part = exclusion_criteria or ""
        cache_key = f"{hash(patient_history)}_{hash(inclusion_criteria)}_{hash(exclusion_part)}"
        return cache_key
    
    def _apply_exclusion_penalty(self, bedrock_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply exclusion criteria penalty to match score.
        
        If exclusion criteria are violated (exclusion_match is True), the match score
        is reduced to below the penalty threshold (0.3) to indicate poor match.
        
        Args:
            bedrock_result: Result from Bedrock analysis
        
        Returns:
            Modified result with exclusion penalty applied if needed
        """
        original_score = bedrock_result['match_score']
        exclusion_match = bedrock_result['exclusion_match']
        
        # Create result with original score preserved
        result = {
            'match_score': original_score,
            'original_score': original_score,
            'explanation': bedrock_result['explanation'],
            'inclusion_match': bedrock_result['inclusion_match'],
            'exclusion_match': exclusion_match,
            'exclusion_penalty_applied': False
        }
        
        # Apply penalty if exclusion criteria are violated
        if exclusion_match:
            # Reduce score to below threshold
            penalized_score = min(original_score, self.EXCLUSION_PENALTY_THRESHOLD - 0.05)
            result['match_score'] = penalized_score
            result['exclusion_penalty_applied'] = True
            
            # Update explanation to mention penalty
            result['explanation'] = (
                f"{bedrock_result['explanation']} "
                f"[Exclusion penalty applied: score reduced from {original_score:.2f} to {penalized_score:.2f}]"
            )
            
            logger.info(
                f"Exclusion penalty applied: {original_score:.2f} -> {penalized_score:.2f}"
            )
        
        return result
    
    def clear_cache(self) -> None:
        """
        Clear the medical term mapping cache.
        
        Useful for testing or when memory needs to be freed.
        """
        self._term_cache.clear()
        logger.info("Medical term cache cleared")
    
    def get_cache_size(self) -> int:
        """
        Get the current size of the cache.
        
        Returns:
            Number of cached entries
        """
        return len(self._term_cache)


# Utility function for common medical terminology mappings
@lru_cache(maxsize=1000)
def normalize_medical_term(term: str) -> str:
    """
    Normalize common medical terminology variations.
    
    This function provides a simple normalization for common medical terms
    to improve cache hit rates. Uses LRU cache for performance.
    
    Args:
        term: Medical term to normalize
    
    Returns:
        Normalized term (lowercase, stripped)
    
    Examples:
        >>> normalize_medical_term("Hypertension")
        'hypertension'
        >>> normalize_medical_term("  High Blood Pressure  ")
        'high blood pressure'
    """
    if not term or not isinstance(term, str):
        return ""
    
    return term.strip().lower()


def get_common_medical_synonyms() -> Dict[str, list]:
    """
    Get dictionary of common medical terminology synonyms.
    
    This provides a reference for common medical term variations that
    the AI should recognize. Useful for documentation and testing.
    
    Returns:
        Dictionary mapping canonical terms to their synonyms
    """
    return {
        'hypertension': ['high blood pressure', 'elevated blood pressure', 'htn'],
        'diabetes': ['diabetes mellitus', 'high blood sugar', 'dm', 'type 2 diabetes', 't2dm'],
        'myocardial infarction': ['heart attack', 'mi', 'cardiac arrest'],
        'cerebrovascular accident': ['stroke', 'cva', 'brain attack'],
        'chronic obstructive pulmonary disease': ['copd', 'emphysema', 'chronic bronchitis'],
        'cancer': ['malignancy', 'tumor', 'neoplasm', 'carcinoma'],
        'kidney disease': ['renal disease', 'nephropathy', 'kidney failure', 'renal failure'],
        'asthma': ['reactive airway disease', 'bronchial asthma'],
        'depression': ['major depressive disorder', 'mdd', 'clinical depression'],
        'anxiety': ['anxiety disorder', 'generalized anxiety disorder', 'gad']
    }
