"""
Unit tests for Medical Matcher

Tests cover:
- MedicalMatcher initialization
- Patient-to-trial matching logic
- Exclusion criteria penalty application
- Input validation
- Caching mechanism
- Error handling
- Medical terminology normalization utilities
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.ai_matching.medical_matcher import (
    MedicalMatcher,
    MedicalMatcherError,
    normalize_medical_term,
    get_common_medical_synonyms
)
from src.ai_matching.bedrock_client import BedrockClient, BedrockError


class TestMedicalMatcherInitialization:
    """Test MedicalMatcher initialization"""
    
    def test_initialization_with_default_client(self):
        """Test initialization creates default Bedrock client"""
        with patch('src.ai_matching.medical_matcher.BedrockClient') as mock_bedrock:
            mock_bedrock.return_value = Mock()
            
            matcher = MedicalMatcher()
            
            assert matcher is not None
            assert matcher.bedrock_client is not None
            mock_bedrock.assert_called_once_with(region_name='us-east-1')
    
    def test_initialization_with_custom_client(self):
        """Test initialization with provided Bedrock client"""
        mock_client = Mock(spec=BedrockClient)
        
        matcher = MedicalMatcher(bedrock_client=mock_client)
        
        assert matcher.bedrock_client is mock_client
    
    def test_initialization_with_custom_region(self):
        """Test initialization with custom AWS region"""
        with patch('src.ai_matching.medical_matcher.BedrockClient') as mock_bedrock:
            mock_bedrock.return_value = Mock()
            
            matcher = MedicalMatcher(region_name='us-west-2')
            
            mock_bedrock.assert_called_once_with(region_name='us-west-2')
    
    def test_initialization_failure(self):
        """Test initialization failure handling"""
        with patch('src.ai_matching.medical_matcher.BedrockClient', side_effect=BedrockError("Init failed")):
            with pytest.raises(MedicalMatcherError) as exc_info:
                MedicalMatcher()
            
            assert "initialization failed" in str(exc_info.value).lower()


class TestInputValidation:
    """Test input validation"""
    
    def test_validate_empty_patient_history(self):
        """Test validation rejects empty patient history"""
        mock_client = Mock(spec=BedrockClient)
        matcher = MedicalMatcher(bedrock_client=mock_client)
        
        with pytest.raises(MedicalMatcherError) as exc_info:
            matcher.match_patient_to_trial(
                patient_medical_history="",
                trial_inclusion_criteria="Must have diabetes"
            )
        
        assert "patient_medical_history" in str(exc_info.value).lower()
    
    def test_validate_whitespace_patient_history(self):
        """Test validation rejects whitespace-only patient history"""
        mock_client = Mock(spec=BedrockClient)
        matcher = MedicalMatcher(bedrock_client=mock_client)
        
        with pytest.raises(MedicalMatcherError) as exc_info:
            matcher.match_patient_to_trial(
                patient_medical_history="   ",
                trial_inclusion_criteria="Must have diabetes"
            )
        
        assert "empty or whitespace" in str(exc_info.value).lower()
    
    def test_validate_none_patient_history(self):
        """Test validation rejects None patient history"""
        mock_client = Mock(spec=BedrockClient)
        matcher = MedicalMatcher(bedrock_client=mock_client)
        
        with pytest.raises(MedicalMatcherError) as exc_info:
            matcher.match_patient_to_trial(
                patient_medical_history=None,
                trial_inclusion_criteria="Must have diabetes"
            )
        
        assert "patient_medical_history" in str(exc_info.value).lower()
    
    def test_validate_empty_inclusion_criteria(self):
        """Test validation rejects empty inclusion criteria"""
        mock_client = Mock(spec=BedrockClient)
        matcher = MedicalMatcher(bedrock_client=mock_client)
        
        with pytest.raises(MedicalMatcherError) as exc_info:
            matcher.match_patient_to_trial(
                patient_medical_history="Patient has diabetes",
                trial_inclusion_criteria=""
            )
        
        assert "trial_inclusion_criteria" in str(exc_info.value).lower()
    
    def test_validate_non_string_inputs(self):
        """Test validation rejects non-string inputs"""
        mock_client = Mock(spec=BedrockClient)
        matcher = MedicalMatcher(bedrock_client=mock_client)
        
        with pytest.raises(MedicalMatcherError):
            matcher.match_patient_to_trial(
                patient_medical_history=123,
                trial_inclusion_criteria="Must have diabetes"
            )


class TestMatchPatientToTrial:
    """Test patient-to-trial matching logic"""
    
    def test_successful_match_without_exclusion(self):
        """Test successful matching without exclusion criteria"""
        mock_client = Mock(spec=BedrockClient)
        mock_client.analyze_medical_match.return_value = {
            'match_score': 0.85,
            'explanation': 'Good match: Patient has diabetes',
            'inclusion_match': True,
            'exclusion_match': False
        }
        
        matcher = MedicalMatcher(bedrock_client=mock_client)
        result = matcher.match_patient_to_trial(
            patient_medical_history="Patient has type 2 diabetes",
            trial_inclusion_criteria="Must have diabetes"
        )
        
        assert result['match_score'] == 0.85
        assert result['original_score'] == 0.85
        assert result['inclusion_match'] is True
        assert result['exclusion_match'] is False
        assert result['exclusion_penalty_applied'] is False
        assert 'Good match' in result['explanation']
    
    def test_successful_match_with_exclusion_not_violated(self):
        """Test successful matching with exclusion criteria not violated"""
        mock_client = Mock(spec=BedrockClient)
        mock_client.analyze_medical_match.return_value = {
            'match_score': 0.90,
            'explanation': 'Excellent match: Patient meets all criteria',
            'inclusion_match': True,
            'exclusion_match': False
        }
        
        matcher = MedicalMatcher(bedrock_client=mock_client)
        result = matcher.match_patient_to_trial(
            patient_medical_history="Patient has diabetes, no kidney disease",
            trial_inclusion_criteria="Must have diabetes",
            trial_exclusion_criteria="Cannot have kidney disease"
        )
        
        assert result['match_score'] == 0.90
        assert result['exclusion_penalty_applied'] is False
    
    def test_match_with_exclusion_violated(self):
        """Test matching with exclusion criteria violated"""
        mock_client = Mock(spec=BedrockClient)
        mock_client.analyze_medical_match.return_value = {
            'match_score': 0.75,
            'explanation': 'Patient has excluded condition',
            'inclusion_match': True,
            'exclusion_match': True
        }
        
        matcher = MedicalMatcher(bedrock_client=mock_client)
        result = matcher.match_patient_to_trial(
            patient_medical_history="Patient has diabetes and kidney disease",
            trial_inclusion_criteria="Must have diabetes",
            trial_exclusion_criteria="Cannot have kidney disease"
        )
        
        # Score should be reduced below 0.3
        assert result['match_score'] < 0.3
        assert result['original_score'] == 0.75
        assert result['exclusion_match'] is True
        assert result['exclusion_penalty_applied'] is True
        assert 'Exclusion penalty applied' in result['explanation']
    
    def test_match_with_low_score_and_exclusion_violated(self):
        """Test matching with already low score and exclusion violated"""
        mock_client = Mock(spec=BedrockClient)
        mock_client.analyze_medical_match.return_value = {
            'match_score': 0.20,
            'explanation': 'Poor match',
            'inclusion_match': False,
            'exclusion_match': True
        }
        
        matcher = MedicalMatcher(bedrock_client=mock_client)
        result = matcher.match_patient_to_trial(
            patient_medical_history="Patient has excluded condition",
            trial_inclusion_criteria="Must have diabetes",
            trial_exclusion_criteria="Cannot have kidney disease"
        )
        
        # Score should remain low (penalty doesn't increase it)
        assert result['match_score'] == 0.20
        assert result['exclusion_penalty_applied'] is True


class TestExclusionPenaltyLogic:
    """Test exclusion criteria penalty application"""
    
    def test_penalty_reduces_score_below_threshold(self):
        """Test that penalty reduces score below 0.3 threshold"""
        mock_client = Mock(spec=BedrockClient)
        matcher = MedicalMatcher(bedrock_client=mock_client)
        
        bedrock_result = {
            'match_score': 0.85,
            'explanation': 'Test',
            'inclusion_match': True,
            'exclusion_match': True
        }
        
        result = matcher._apply_exclusion_penalty(bedrock_result)
        
        assert result['match_score'] < 0.3
        assert result['original_score'] == 0.85
        assert result['exclusion_penalty_applied'] is True
    
    def test_no_penalty_when_exclusion_not_violated(self):
        """Test no penalty applied when exclusion not violated"""
        mock_client = Mock(spec=BedrockClient)
        matcher = MedicalMatcher(bedrock_client=mock_client)
        
        bedrock_result = {
            'match_score': 0.85,
            'explanation': 'Test',
            'inclusion_match': True,
            'exclusion_match': False
        }
        
        result = matcher._apply_exclusion_penalty(bedrock_result)
        
        assert result['match_score'] == 0.85
        assert result['original_score'] == 0.85
        assert result['exclusion_penalty_applied'] is False
    
    def test_penalty_explanation_updated(self):
        """Test that explanation is updated when penalty applied"""
        mock_client = Mock(spec=BedrockClient)
        matcher = MedicalMatcher(bedrock_client=mock_client)
        
        bedrock_result = {
            'match_score': 0.85,
            'explanation': 'Original explanation',
            'inclusion_match': True,
            'exclusion_match': True
        }
        
        result = matcher._apply_exclusion_penalty(bedrock_result)
        
        assert 'Original explanation' in result['explanation']
        assert 'Exclusion penalty applied' in result['explanation']
        assert '0.85' in result['explanation']


class TestCachingMechanism:
    """Test caching for medical term mappings"""
    
    def test_cache_stores_results(self):
        """Test that results are cached"""
        mock_client = Mock(spec=BedrockClient)
        mock_client.analyze_medical_match.return_value = {
            'match_score': 0.85,
            'explanation': 'Test',
            'inclusion_match': True,
            'exclusion_match': False
        }
        
        matcher = MedicalMatcher(bedrock_client=mock_client)
        
        # First call
        result1 = matcher.match_patient_to_trial(
            patient_medical_history="Patient has diabetes",
            trial_inclusion_criteria="Must have diabetes"
        )
        
        # Second call with same inputs
        result2 = matcher.match_patient_to_trial(
            patient_medical_history="Patient has diabetes",
            trial_inclusion_criteria="Must have diabetes"
        )
        
        # Bedrock should only be called once
        assert mock_client.analyze_medical_match.call_count == 1
        assert result1 == result2
    
    def test_cache_different_inputs(self):
        """Test that different inputs are not cached together"""
        mock_client = Mock(spec=BedrockClient)
        mock_client.analyze_medical_match.return_value = {
            'match_score': 0.85,
            'explanation': 'Test',
            'inclusion_match': True,
            'exclusion_match': False
        }
        
        matcher = MedicalMatcher(bedrock_client=mock_client)
        
        # First call
        matcher.match_patient_to_trial(
            patient_medical_history="Patient has diabetes",
            trial_inclusion_criteria="Must have diabetes"
        )
        
        # Second call with different inputs
        matcher.match_patient_to_trial(
            patient_medical_history="Patient has hypertension",
            trial_inclusion_criteria="Must have high blood pressure"
        )
        
        # Bedrock should be called twice
        assert mock_client.analyze_medical_match.call_count == 2
    
    def test_clear_cache(self):
        """Test cache clearing functionality"""
        mock_client = Mock(spec=BedrockClient)
        mock_client.analyze_medical_match.return_value = {
            'match_score': 0.85,
            'explanation': 'Test',
            'inclusion_match': True,
            'exclusion_match': False
        }
        
        matcher = MedicalMatcher(bedrock_client=mock_client)
        
        # First call
        matcher.match_patient_to_trial(
            patient_medical_history="Patient has diabetes",
            trial_inclusion_criteria="Must have diabetes"
        )
        
        assert matcher.get_cache_size() == 1
        
        # Clear cache
        matcher.clear_cache()
        
        assert matcher.get_cache_size() == 0
        
        # Second call should hit Bedrock again
        matcher.match_patient_to_trial(
            patient_medical_history="Patient has diabetes",
            trial_inclusion_criteria="Must have diabetes"
        )
        
        assert mock_client.analyze_medical_match.call_count == 2
    
    def test_get_cache_size(self):
        """Test getting cache size"""
        mock_client = Mock(spec=BedrockClient)
        mock_client.analyze_medical_match.return_value = {
            'match_score': 0.85,
            'explanation': 'Test',
            'inclusion_match': True,
            'exclusion_match': False
        }
        
        matcher = MedicalMatcher(bedrock_client=mock_client)
        
        assert matcher.get_cache_size() == 0
        
        # Add one entry
        matcher.match_patient_to_trial(
            patient_medical_history="Patient has diabetes",
            trial_inclusion_criteria="Must have diabetes"
        )
        
        assert matcher.get_cache_size() == 1
        
        # Add another entry
        matcher.match_patient_to_trial(
            patient_medical_history="Patient has hypertension",
            trial_inclusion_criteria="Must have high blood pressure"
        )
        
        assert matcher.get_cache_size() == 2


class TestErrorHandling:
    """Test error handling"""
    
    def test_bedrock_error_propagation(self):
        """Test that Bedrock errors are properly propagated"""
        mock_client = Mock(spec=BedrockClient)
        mock_client.analyze_medical_match.side_effect = BedrockError("API error")
        
        matcher = MedicalMatcher(bedrock_client=mock_client)
        
        with pytest.raises(MedicalMatcherError) as exc_info:
            matcher.match_patient_to_trial(
                patient_medical_history="Patient has diabetes",
                trial_inclusion_criteria="Must have diabetes"
            )
        
        assert "Medical matching failed" in str(exc_info.value)
    
    def test_unexpected_error_handling(self):
        """Test handling of unexpected errors"""
        mock_client = Mock(spec=BedrockClient)
        mock_client.analyze_medical_match.side_effect = Exception("Unexpected error")
        
        matcher = MedicalMatcher(bedrock_client=mock_client)
        
        with pytest.raises(MedicalMatcherError) as exc_info:
            matcher.match_patient_to_trial(
                patient_medical_history="Patient has diabetes",
                trial_inclusion_criteria="Must have diabetes"
            )
        
        assert "Unexpected matching error" in str(exc_info.value)


class TestMedicalTerminologyNormalization:
    """Test medical terminology normalization utilities"""
    
    def test_normalize_medical_term_lowercase(self):
        """Test normalization converts to lowercase"""
        result = normalize_medical_term("Hypertension")
        assert result == "hypertension"
    
    def test_normalize_medical_term_strips_whitespace(self):
        """Test normalization strips whitespace"""
        result = normalize_medical_term("  High Blood Pressure  ")
        assert result == "high blood pressure"
    
    def test_normalize_medical_term_empty_string(self):
        """Test normalization handles empty string"""
        result = normalize_medical_term("")
        assert result == ""
    
    def test_normalize_medical_term_none(self):
        """Test normalization handles None"""
        result = normalize_medical_term(None)
        assert result == ""
    
    def test_normalize_medical_term_non_string(self):
        """Test normalization handles non-string input"""
        result = normalize_medical_term(123)
        assert result == ""
    
    def test_normalize_medical_term_caching(self):
        """Test that normalization uses LRU cache"""
        # Call twice with same input
        result1 = normalize_medical_term("Hypertension")
        result2 = normalize_medical_term("Hypertension")
        
        # Results should be identical (cached)
        assert result1 == result2
        assert result1 == "hypertension"


class TestCommonMedicalSynonyms:
    """Test common medical synonyms dictionary"""
    
    def test_get_common_medical_synonyms_returns_dict(self):
        """Test that function returns a dictionary"""
        synonyms = get_common_medical_synonyms()
        assert isinstance(synonyms, dict)
    
    def test_synonyms_include_hypertension(self):
        """Test that synonyms include hypertension variations"""
        synonyms = get_common_medical_synonyms()
        assert 'hypertension' in synonyms
        assert 'high blood pressure' in synonyms['hypertension']
    
    def test_synonyms_include_diabetes(self):
        """Test that synonyms include diabetes variations"""
        synonyms = get_common_medical_synonyms()
        assert 'diabetes' in synonyms
        assert 'diabetes mellitus' in synonyms['diabetes']
    
    def test_synonyms_include_heart_attack(self):
        """Test that synonyms include heart attack variations"""
        synonyms = get_common_medical_synonyms()
        assert 'myocardial infarction' in synonyms
        assert 'heart attack' in synonyms['myocardial infarction']
    
    def test_synonyms_structure(self):
        """Test that synonyms have correct structure"""
        synonyms = get_common_medical_synonyms()
        
        for canonical_term, variations in synonyms.items():
            assert isinstance(canonical_term, str)
            assert isinstance(variations, list)
            assert len(variations) > 0
            assert all(isinstance(v, str) for v in variations)


class TestCacheKeyGeneration:
    """Test cache key generation"""
    
    def test_cache_key_generation(self):
        """Test that cache keys are generated consistently"""
        mock_client = Mock(spec=BedrockClient)
        matcher = MedicalMatcher(bedrock_client=mock_client)
        
        key1 = matcher._generate_cache_key(
            "Patient has diabetes",
            "Must have diabetes",
            None
        )
        
        key2 = matcher._generate_cache_key(
            "Patient has diabetes",
            "Must have diabetes",
            None
        )
        
        # Same inputs should generate same key
        assert key1 == key2
    
    def test_cache_key_different_for_different_inputs(self):
        """Test that different inputs generate different keys"""
        mock_client = Mock(spec=BedrockClient)
        matcher = MedicalMatcher(bedrock_client=mock_client)
        
        key1 = matcher._generate_cache_key(
            "Patient has diabetes",
            "Must have diabetes",
            None
        )
        
        key2 = matcher._generate_cache_key(
            "Patient has hypertension",
            "Must have diabetes",
            None
        )
        
        # Different inputs should generate different keys
        assert key1 != key2
    
    def test_cache_key_includes_exclusion_criteria(self):
        """Test that cache key includes exclusion criteria"""
        mock_client = Mock(spec=BedrockClient)
        matcher = MedicalMatcher(bedrock_client=mock_client)
        
        key1 = matcher._generate_cache_key(
            "Patient has diabetes",
            "Must have diabetes",
            None
        )
        
        key2 = matcher._generate_cache_key(
            "Patient has diabetes",
            "Must have diabetes",
            "Cannot have kidney disease"
        )
        
        # Different exclusion criteria should generate different keys
        assert key1 != key2


class TestIntegrationScenarios:
    """Test realistic integration scenarios"""
    
    def test_diabetes_trial_match(self):
        """Test realistic diabetes trial matching scenario"""
        mock_client = Mock(spec=BedrockClient)
        mock_client.analyze_medical_match.return_value = {
            'match_score': 0.92,
            'explanation': 'Excellent match: Patient has type 2 diabetes and is within age range',
            'inclusion_match': True,
            'exclusion_match': False
        }
        
        matcher = MedicalMatcher(bedrock_client=mock_client)
        result = matcher.match_patient_to_trial(
            patient_medical_history="55-year-old male with type 2 diabetes, controlled with metformin",
            trial_inclusion_criteria="Adults aged 18-70 with type 2 diabetes mellitus",
            trial_exclusion_criteria="Severe kidney disease, active cancer"
        )
        
        assert result['match_score'] == 0.92
        assert result['inclusion_match'] is True
        assert result['exclusion_match'] is False
        assert result['exclusion_penalty_applied'] is False
    
    def test_hypertension_trial_with_exclusion(self):
        """Test hypertension trial with exclusion criteria violated"""
        mock_client = Mock(spec=BedrockClient)
        mock_client.analyze_medical_match.return_value = {
            'match_score': 0.80,
            'explanation': 'Patient has hypertension but also has excluded kidney disease',
            'inclusion_match': True,
            'exclusion_match': True
        }
        
        matcher = MedicalMatcher(bedrock_client=mock_client)
        result = matcher.match_patient_to_trial(
            patient_medical_history="Patient with high blood pressure and chronic kidney disease",
            trial_inclusion_criteria="Must have hypertension",
            trial_exclusion_criteria="Cannot have kidney disease"
        )
        
        assert result['match_score'] < 0.3
        assert result['original_score'] == 0.80
        assert result['exclusion_match'] is True
        assert result['exclusion_penalty_applied'] is True
