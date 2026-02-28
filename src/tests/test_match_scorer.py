"""
Unit Tests for Match Scoring Algorithm

Tests the MatchScorer class that combines hard filter results with AI soft matching
to produce ranked trial recommendations with visual explanations.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import List

from src.ai_matching.match_scorer import (
    MatchScorer,
    MatchScorerError,
    PatientProfile,
    Trial,
    MatchResult
)
from src.ai_matching.medical_matcher import MedicalMatcherError


# Test Fixtures

@pytest.fixture
def sample_patient_profile():
    """Sample patient profile for testing"""
    return PatientProfile(
        condition="Non-small cell lung cancer",
        age=65,
        gender="Male",
        location="New York, NY",
        distance_miles=50,
        medical_history="History of smoking, hypertension, no diabetes"
    )


@pytest.fixture
def sample_trial():
    """Sample trial for testing"""
    return Trial(
        id="NCT12345678",
        title="Phase II Study of Drug X in NSCLC Patients",
        condition="Non-small cell lung cancer",
        min_age=18,
        max_age=70,
        gender_criteria="All",
        location="Memorial Sloan Kettering, NYC",
        inclusion_text="Patients with NSCLC, history of smoking",
        exclusion_text="Active diabetes, severe heart disease"
    )


@pytest.fixture
def sample_trials():
    """Sample list of trials for testing"""
    return [
        Trial(
            id="NCT11111111",
            title="Trial A - Excellent Match",
            condition="Lung cancer",
            min_age=18,
            max_age=75,
            gender_criteria="All",
            location="New York, NY",
            inclusion_text="NSCLC patients with smoking history",
            exclusion_text="Diabetes"
        ),
        Trial(
            id="NCT22222222",
            title="Trial B - Good Match",
            condition="Lung cancer",
            min_age=50,
            max_age=80,
            gender_criteria="Male",
            location="Boston, MA",
            inclusion_text="NSCLC patients",
            exclusion_text="Severe cardiac disease"
        ),
        Trial(
            id="NCT33333333",
            title="Trial C - Moderate Match",
            condition="Lung cancer",
            min_age=40,
            max_age=70,
            gender_criteria="All",
            location="Philadelphia, PA",
            inclusion_text="Cancer patients",
            exclusion_text="None"
        )
    ]


@pytest.fixture
def mock_medical_matcher():
    """Mock MedicalMatcher for testing"""
    mock = Mock()
    mock.match_patient_to_trial = Mock(return_value={
        'match_score': 0.92,
        'original_score': 0.92,
        'explanation': 'Strong match based on medical history',
        'inclusion_match': True,
        'exclusion_match': False,
        'exclusion_penalty_applied': False
    })
    return mock


# Initialization Tests

def test_match_scorer_initialization():
    """Test MatchScorer initializes successfully"""
    with patch('src.ai_matching.match_scorer.MedicalMatcher'):
        scorer = MatchScorer()
        assert scorer is not None
        assert scorer.medical_matcher is not None


def test_match_scorer_initialization_with_custom_matcher(mock_medical_matcher):
    """Test MatchScorer initializes with custom MedicalMatcher"""
    scorer = MatchScorer(medical_matcher=mock_medical_matcher)
    assert scorer.medical_matcher == mock_medical_matcher


def test_match_scorer_initialization_failure():
    """Test MatchScorer raises error when MedicalMatcher initialization fails"""
    with patch('src.ai_matching.match_scorer.MedicalMatcher', side_effect=MedicalMatcherError("Init failed")):
        with pytest.raises(MatchScorerError) as exc_info:
            MatchScorer()
        assert "initialization failed" in str(exc_info.value).lower()


# Input Validation Tests

def test_score_and_rank_trials_invalid_patient_profile(mock_medical_matcher, sample_trials):
    """Test scoring fails with invalid patient profile"""
    scorer = MatchScorer(medical_matcher=mock_medical_matcher)
    
    with pytest.raises(MatchScorerError) as exc_info:
        scorer.score_and_rank_trials(
            patient_profile="not a PatientProfile",
            hard_filtered_trials=sample_trials
        )
    assert "must be a PatientProfile instance" in str(exc_info.value)


def test_score_and_rank_trials_invalid_trials_list(mock_medical_matcher, sample_patient_profile):
    """Test scoring fails with invalid trials list"""
    scorer = MatchScorer(medical_matcher=mock_medical_matcher)
    
    with pytest.raises(MatchScorerError) as exc_info:
        scorer.score_and_rank_trials(
            patient_profile=sample_patient_profile,
            hard_filtered_trials="not a list"
        )
    assert "must be a list" in str(exc_info.value)


def test_score_and_rank_trials_empty_medical_history(mock_medical_matcher, sample_trials):
    """Test scoring fails with empty medical history"""
    scorer = MatchScorer(medical_matcher=mock_medical_matcher)
    
    invalid_profile = PatientProfile(
        condition="Cancer",
        age=65,
        gender="Male",
        location="New York",
        distance_miles=50,
        medical_history=""  # Empty
    )
    
    with pytest.raises(MatchScorerError) as exc_info:
        scorer.score_and_rank_trials(
            patient_profile=invalid_profile,
            hard_filtered_trials=sample_trials
        )
    assert "medical_history cannot be empty" in str(exc_info.value)


def test_score_and_rank_trials_empty_condition(mock_medical_matcher, sample_trials):
    """Test scoring fails with empty condition"""
    scorer = MatchScorer(medical_matcher=mock_medical_matcher)
    
    invalid_profile = PatientProfile(
        condition="",  # Empty
        age=65,
        gender="Male",
        location="New York",
        distance_miles=50,
        medical_history="Some history"
    )
    
    with pytest.raises(MatchScorerError) as exc_info:
        scorer.score_and_rank_trials(
            patient_profile=invalid_profile,
            hard_filtered_trials=sample_trials
        )
    assert "condition cannot be empty" in str(exc_info.value)


# Core Functionality Tests

def test_score_and_rank_trials_empty_list(mock_medical_matcher, sample_patient_profile):
    """Test scoring returns empty list when no trials provided"""
    scorer = MatchScorer(medical_matcher=mock_medical_matcher)
    
    results = scorer.score_and_rank_trials(
        patient_profile=sample_patient_profile,
        hard_filtered_trials=[]
    )
    
    assert results == []


def test_score_and_rank_trials_single_trial(mock_medical_matcher, sample_patient_profile, sample_trial):
    """Test scoring single trial"""
    scorer = MatchScorer(medical_matcher=mock_medical_matcher)
    
    results = scorer.score_and_rank_trials(
        patient_profile=sample_patient_profile,
        hard_filtered_trials=[sample_trial]
    )
    
    assert len(results) == 1
    assert results[0].trial_id == sample_trial.id
    assert results[0].title == sample_trial.title
    assert 0 <= results[0].match_score <= 100
    assert results[0].match_percentage.endswith('%')
    assert len(results[0].key_criteria) > 0


def test_score_and_rank_trials_converts_score_to_percentage(mock_medical_matcher, sample_patient_profile, sample_trial):
    """Test that match score is converted from 0-1 to 0-100 percentage"""
    mock_medical_matcher.match_patient_to_trial.return_value = {
        'match_score': 0.85,
        'original_score': 0.85,
        'explanation': 'Good match',
        'inclusion_match': True,
        'exclusion_match': False,
        'exclusion_penalty_applied': False
    }
    
    scorer = MatchScorer(medical_matcher=mock_medical_matcher)
    results = scorer.score_and_rank_trials(
        patient_profile=sample_patient_profile,
        hard_filtered_trials=[sample_trial]
    )
    
    assert results[0].match_score == 85.0
    assert results[0].match_percentage == "85%"


def test_score_and_rank_trials_ranks_by_score(sample_patient_profile, sample_trials):
    """Test that trials are ranked by match score (highest first)"""
    mock_matcher = Mock()
    
    # Return different scores for each trial
    mock_matcher.match_patient_to_trial.side_effect = [
        {
            'match_score': 0.60,  # Trial A - moderate
            'original_score': 0.60,
            'explanation': 'Moderate match',
            'inclusion_match': True,
            'exclusion_match': False,
            'exclusion_penalty_applied': False
        },
        {
            'match_score': 0.95,  # Trial B - excellent (should be first)
            'original_score': 0.95,
            'explanation': 'Excellent match',
            'inclusion_match': True,
            'exclusion_match': False,
            'exclusion_penalty_applied': False
        },
        {
            'match_score': 0.75,  # Trial C - good
            'original_score': 0.75,
            'explanation': 'Good match',
            'inclusion_match': True,
            'exclusion_match': False,
            'exclusion_penalty_applied': False
        }
    ]
    
    scorer = MatchScorer(medical_matcher=mock_matcher)
    results = scorer.score_and_rank_trials(
        patient_profile=sample_patient_profile,
        hard_filtered_trials=sample_trials
    )
    
    # Verify ranking (highest score first)
    assert len(results) == 3
    assert results[0].trial_id == "NCT22222222"  # Trial B - 95%
    assert results[0].match_score == 95.0
    assert results[1].trial_id == "NCT33333333"  # Trial C - 75%
    assert results[1].match_score == 75.0
    assert results[2].trial_id == "NCT11111111"  # Trial A - 60%
    assert results[2].match_score == 60.0


def test_score_and_rank_trials_limits_to_max_results(sample_patient_profile):
    """Test that results are limited to MAX_RESULTS (5)"""
    # Create 10 trials
    many_trials = [
        Trial(
            id=f"NCT{i:08d}",
            title=f"Trial {i}",
            condition="Cancer",
            min_age=18,
            max_age=80,
            gender_criteria="All",
            location="New York",
            inclusion_text="Cancer patients",
            exclusion_text=None
        )
        for i in range(10)
    ]
    
    mock_matcher = Mock()
    mock_matcher.match_patient_to_trial.return_value = {
        'match_score': 0.80,
        'original_score': 0.80,
        'explanation': 'Good match',
        'inclusion_match': True,
        'exclusion_match': False,
        'exclusion_penalty_applied': False
    }
    
    scorer = MatchScorer(medical_matcher=mock_matcher)
    results = scorer.score_and_rank_trials(
        patient_profile=sample_patient_profile,
        hard_filtered_trials=many_trials
    )
    
    assert len(results) == MatchScorer.MAX_RESULTS  # Should be 5


def test_score_and_rank_trials_handles_scoring_failures(sample_patient_profile, sample_trials):
    """Test that scoring continues even if some trials fail"""
    mock_matcher = Mock()
    
    # First trial fails, second succeeds, third fails
    mock_matcher.match_patient_to_trial.side_effect = [
        MedicalMatcherError("Scoring failed"),
        {
            'match_score': 0.85,
            'original_score': 0.85,
            'explanation': 'Good match',
            'inclusion_match': True,
            'exclusion_match': False,
            'exclusion_penalty_applied': False
        },
        MedicalMatcherError("Scoring failed")
    ]
    
    scorer = MatchScorer(medical_matcher=mock_matcher)
    results = scorer.score_and_rank_trials(
        patient_profile=sample_patient_profile,
        hard_filtered_trials=sample_trials
    )
    
    # Should return only the successful trial
    assert len(results) == 1
    assert results[0].trial_id == "NCT22222222"  # Trial B


# Visual Explanation Tests

def test_generate_visual_explanations_age_match(mock_medical_matcher, sample_patient_profile):
    """Test age criteria generates checkmark when matched"""
    trial = Trial(
        id="NCT12345678",
        title="Test Trial",
        condition="Cancer",
        min_age=18,
        max_age=70,
        gender_criteria="All",
        location="New York",
        inclusion_text="Cancer patients",
        exclusion_text=None
    )
    
    scorer = MatchScorer(medical_matcher=mock_medical_matcher)
    results = scorer.score_and_rank_trials(
        patient_profile=sample_patient_profile,
        hard_filtered_trials=[trial]
    )
    
    # Check for age explanation with checkmark
    age_explanations = [exp for exp in results[0].key_criteria if "Age requirement" in exp]
    assert len(age_explanations) > 0
    assert "✅" in age_explanations[0]
    assert "18-70" in age_explanations[0]
    assert "65" in age_explanations[0]


def test_generate_visual_explanations_age_mismatch(mock_medical_matcher, sample_patient_profile):
    """Test age criteria generates warning when not matched"""
    trial = Trial(
        id="NCT12345678",
        title="Test Trial",
        condition="Cancer",
        min_age=18,
        max_age=60,  # Patient is 65, outside range
        gender_criteria="All",
        location="New York",
        inclusion_text="Cancer patients",
        exclusion_text=None
    )
    
    scorer = MatchScorer(medical_matcher=mock_medical_matcher)
    results = scorer.score_and_rank_trials(
        patient_profile=sample_patient_profile,
        hard_filtered_trials=[trial]
    )
    
    # Check for age explanation with warning
    age_explanations = [exp for exp in results[0].key_criteria if "Age requirement" in exp]
    assert len(age_explanations) > 0
    assert "⚠️" in age_explanations[0]


def test_generate_visual_explanations_inclusion_match(sample_patient_profile, sample_trial):
    """Test inclusion criteria generates appropriate explanation"""
    mock_matcher = Mock()
    mock_matcher.match_patient_to_trial.return_value = {
        'match_score': 0.90,
        'original_score': 0.90,
        'explanation': 'Strong match',
        'inclusion_match': True,  # Inclusion matched
        'exclusion_match': False,
        'exclusion_penalty_applied': False
    }
    
    scorer = MatchScorer(medical_matcher=mock_matcher)
    results = scorer.score_and_rank_trials(
        patient_profile=sample_patient_profile,
        hard_filtered_trials=[sample_trial]
    )
    
    # Check for inclusion explanation with checkmark
    inclusion_explanations = [exp for exp in results[0].key_criteria if "Inclusion criteria" in exp]
    assert len(inclusion_explanations) > 0
    assert "✅" in inclusion_explanations[0]


def test_generate_visual_explanations_exclusion_concern(sample_patient_profile, sample_trial):
    """Test exclusion criteria generates warning when violated"""
    mock_matcher = Mock()
    mock_matcher.match_patient_to_trial.return_value = {
        'match_score': 0.25,  # Low score due to exclusion
        'original_score': 0.80,
        'explanation': 'Exclusion criteria violated',
        'inclusion_match': True,
        'exclusion_match': True,  # Exclusion violated
        'exclusion_penalty_applied': True
    }
    
    scorer = MatchScorer(medical_matcher=mock_matcher)
    results = scorer.score_and_rank_trials(
        patient_profile=sample_patient_profile,
        hard_filtered_trials=[sample_trial]
    )
    
    # Check for exclusion explanation with warning
    exclusion_explanations = [exp for exp in results[0].key_criteria if "Exclusion" in exp]
    assert len(exclusion_explanations) > 0
    assert "⚠️" in exclusion_explanations[0]


def test_generate_visual_explanations_quality_excellent(sample_patient_profile, sample_trial):
    """Test quality explanation for excellent match (>90%)"""
    mock_matcher = Mock()
    mock_matcher.match_patient_to_trial.return_value = {
        'match_score': 0.95,  # Excellent
        'original_score': 0.95,
        'explanation': 'Excellent match',
        'inclusion_match': True,
        'exclusion_match': False,
        'exclusion_penalty_applied': False
    }
    
    scorer = MatchScorer(medical_matcher=mock_matcher)
    results = scorer.score_and_rank_trials(
        patient_profile=sample_patient_profile,
        hard_filtered_trials=[sample_trial]
    )
    
    # Check for quality explanation
    quality_explanations = [exp for exp in results[0].key_criteria if "Excellent match" in exp]
    assert len(quality_explanations) > 0
    assert "✅" in quality_explanations[0]


def test_generate_visual_explanations_quality_good(sample_patient_profile, sample_trial):
    """Test quality explanation for good match (70-90%)"""
    mock_matcher = Mock()
    mock_matcher.match_patient_to_trial.return_value = {
        'match_score': 0.80,  # Good
        'original_score': 0.80,
        'explanation': 'Good match',
        'inclusion_match': True,
        'exclusion_match': False,
        'exclusion_penalty_applied': False
    }
    
    scorer = MatchScorer(medical_matcher=mock_matcher)
    results = scorer.score_and_rank_trials(
        patient_profile=sample_patient_profile,
        hard_filtered_trials=[sample_trial]
    )
    
    # Check for quality explanation
    quality_explanations = [exp for exp in results[0].key_criteria if "Good match" in exp]
    assert len(quality_explanations) > 0
    assert "✅" in quality_explanations[0]


def test_generate_visual_explanations_quality_moderate(sample_patient_profile, sample_trial):
    """Test quality explanation for moderate match (40-70%)"""
    mock_matcher = Mock()
    mock_matcher.match_patient_to_trial.return_value = {
        'match_score': 0.55,  # Moderate
        'original_score': 0.55,
        'explanation': 'Moderate match',
        'inclusion_match': True,
        'exclusion_match': False,
        'exclusion_penalty_applied': False
    }
    
    scorer = MatchScorer(medical_matcher=mock_matcher)
    results = scorer.score_and_rank_trials(
        patient_profile=sample_patient_profile,
        hard_filtered_trials=[sample_trial]
    )
    
    # Check for quality explanation
    quality_explanations = [exp for exp in results[0].key_criteria if "Moderate match" in exp]
    assert len(quality_explanations) > 0
    assert "⚠️" in quality_explanations[0]


def test_generate_visual_explanations_quality_poor(sample_patient_profile, sample_trial):
    """Test quality explanation for poor match (<40%)"""
    mock_matcher = Mock()
    mock_matcher.match_patient_to_trial.return_value = {
        'match_score': 0.25,  # Poor
        'original_score': 0.25,
        'explanation': 'Poor match',
        'inclusion_match': False,
        'exclusion_match': False,
        'exclusion_penalty_applied': False
    }
    
    scorer = MatchScorer(medical_matcher=mock_matcher)
    results = scorer.score_and_rank_trials(
        patient_profile=sample_patient_profile,
        hard_filtered_trials=[sample_trial]
    )
    
    # Check for quality explanation
    quality_explanations = [exp for exp in results[0].key_criteria if "Poor match" in exp]
    assert len(quality_explanations) > 0
    assert "⚠️" in quality_explanations[0]


# Edge Case Tests

def test_score_and_rank_trials_missing_age_criteria(mock_medical_matcher, sample_patient_profile):
    """Test scoring handles trials with missing age criteria"""
    trial = Trial(
        id="NCT12345678",
        title="Test Trial",
        condition="Cancer",
        min_age=None,  # Missing
        max_age=None,  # Missing
        gender_criteria="All",
        location="New York",
        inclusion_text="Cancer patients",
        exclusion_text=None
    )
    
    scorer = MatchScorer(medical_matcher=mock_medical_matcher)
    results = scorer.score_and_rank_trials(
        patient_profile=sample_patient_profile,
        hard_filtered_trials=[trial]
    )
    
    assert len(results) == 1
    # Should not have age explanation if criteria missing
    age_explanations = [exp for exp in results[0].key_criteria if "Age requirement" in exp]
    assert len(age_explanations) == 0


def test_score_and_rank_trials_missing_gender_criteria(mock_medical_matcher, sample_patient_profile):
    """Test scoring handles trials with missing gender criteria"""
    trial = Trial(
        id="NCT12345678",
        title="Test Trial",
        condition="Cancer",
        min_age=18,
        max_age=80,
        gender_criteria=None,  # Missing
        location="New York",
        inclusion_text="Cancer patients",
        exclusion_text=None
    )
    
    scorer = MatchScorer(medical_matcher=mock_medical_matcher)
    results = scorer.score_and_rank_trials(
        patient_profile=sample_patient_profile,
        hard_filtered_trials=[trial]
    )
    
    assert len(results) == 1
    # Should not have gender explanation if criteria missing
    gender_explanations = [exp for exp in results[0].key_criteria if "Gender requirement" in exp]
    assert len(gender_explanations) == 0


def test_score_and_rank_trials_gender_all(mock_medical_matcher, sample_patient_profile):
    """Test scoring handles trials with 'All' gender criteria"""
    trial = Trial(
        id="NCT12345678",
        title="Test Trial",
        condition="Cancer",
        min_age=18,
        max_age=80,
        gender_criteria="All",  # All genders accepted
        location="New York",
        inclusion_text="Cancer patients",
        exclusion_text=None
    )
    
    scorer = MatchScorer(medical_matcher=mock_medical_matcher)
    results = scorer.score_and_rank_trials(
        patient_profile=sample_patient_profile,
        hard_filtered_trials=[trial]
    )
    
    assert len(results) == 1
    # Should not have gender explanation if 'All' accepted
    gender_explanations = [exp for exp in results[0].key_criteria if "Gender requirement" in exp]
    assert len(gender_explanations) == 0


def test_get_match_quality_label(mock_medical_matcher):
    """Test match quality label generation"""
    scorer = MatchScorer(medical_matcher=mock_medical_matcher)
    
    assert scorer.get_match_quality_label(0.95) == "Excellent"
    assert scorer.get_match_quality_label(0.90) == "Excellent"
    assert scorer.get_match_quality_label(0.85) == "Good"
    assert scorer.get_match_quality_label(0.70) == "Good"
    assert scorer.get_match_quality_label(0.55) == "Moderate"
    assert scorer.get_match_quality_label(0.40) == "Moderate"
    assert scorer.get_match_quality_label(0.25) == "Poor"
    assert scorer.get_match_quality_label(0.10) == "Poor"


# Integration-like Tests

def test_complete_scoring_workflow(sample_patient_profile, sample_trials):
    """Test complete scoring workflow with realistic data"""
    mock_matcher = Mock()
    
    # Return realistic scores for each trial
    mock_matcher.match_patient_to_trial.side_effect = [
        {
            'match_score': 0.92,
            'original_score': 0.92,
            'explanation': 'Excellent match: Patient profile strongly aligns with trial criteria',
            'inclusion_match': True,
            'exclusion_match': False,
            'exclusion_penalty_applied': False
        },
        {
            'match_score': 0.78,
            'original_score': 0.78,
            'explanation': 'Good match: Patient meets most trial requirements',
            'inclusion_match': True,
            'exclusion_match': False,
            'exclusion_penalty_applied': False
        },
        {
            'match_score': 0.55,
            'original_score': 0.55,
            'explanation': 'Moderate match: Some alignment with trial criteria',
            'inclusion_match': False,
            'exclusion_match': False,
            'exclusion_penalty_applied': False
        }
    ]
    
    scorer = MatchScorer(medical_matcher=mock_matcher)
    results = scorer.score_and_rank_trials(
        patient_profile=sample_patient_profile,
        hard_filtered_trials=sample_trials
    )
    
    # Verify results
    assert len(results) == 3
    
    # Verify ranking (highest first)
    assert results[0].match_score == pytest.approx(92.0)
    assert results[1].match_score == pytest.approx(78.0)
    assert results[2].match_score == pytest.approx(55.0)
    
    # Verify all results have required fields
    for result in results:
        assert result.trial_id
        assert result.title
        assert 0 <= result.match_score <= 100
        assert result.match_percentage.endswith('%')
        assert result.explanation
        assert len(result.key_criteria) > 0
        assert result.location
        
        # Verify visual explanations contain checkmarks or warnings
        has_visual_symbols = any('✅' in exp or '⚠️' in exp for exp in result.key_criteria)
        assert has_visual_symbols
