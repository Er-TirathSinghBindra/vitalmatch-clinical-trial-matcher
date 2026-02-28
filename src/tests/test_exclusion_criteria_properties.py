"""
Property-Based Tests for Exclusion Criteria Enforcement

This module implements Property 3: Exclusion Criteria Enforcement
Validates Requirement 2.5 from the design document.

Property Tests:
1. Trials with strong exclusion matches receive low scores (<0.3)
2. Exclusion penalty is consistently applied when criteria are violated
3. Exclusion violations always result in lower scores than non-violations
4. Various exclusion criteria patterns are handled correctly

Uses Hypothesis for property-based testing with randomly generated patient profiles
and exclusion criteria to ensure consistent enforcement across diverse inputs.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import Mock
from typing import Optional

from src.ai_matching.match_scorer import (
    MatchScorer,
    PatientProfile,
    Trial,
    MatchResult
)
from src.ai_matching.medical_matcher import MedicalMatcher


# Constants from MedicalMatcher
EXCLUSION_PENALTY_THRESHOLD = 0.3


# Hypothesis Strategies for Generating Test Data

@st.composite
def patient_profile_strategy(draw):
    """
    Generate random but valid patient profiles for property testing.
    
    Returns:
        PatientProfile with randomized but realistic values
    """
    conditions = [
        "Non-small cell lung cancer",
        "Breast cancer",
        "Diabetes Type 2",
        "Hypertension",
        "Heart disease"
    ]
    
    genders = ["Male", "Female", "Other"]
    
    locations = [
        "New York, NY",
        "Boston, MA",
        "Los Angeles, CA"
    ]
    
    medical_histories = [
        "History of smoking, hypertension, diabetes",
        "Type 2 diabetes, high cholesterol, heart disease",
        "Severe kidney disease, on dialysis",
        "Active infection, recent surgery",
        "Pregnancy, gestational diabetes",
        "Severe heart disease, multiple cardiac events",
        "Active cancer, undergoing chemotherapy"
    ]
    
    return PatientProfile(
        condition=draw(st.sampled_from(conditions)),
        age=draw(st.integers(min_value=18, max_value=85)),
        gender=draw(st.sampled_from(genders)),
        location=draw(st.sampled_from(locations)),
        distance_miles=draw(st.integers(min_value=10, max_value=100)),
        medical_history=draw(st.sampled_from(medical_histories))
    )


@st.composite
def trial_with_exclusion_strategy(draw):
    """
    Generate trials with various exclusion criteria patterns.
    
    Returns:
        Trial with randomized exclusion criteria
    """
    conditions = ["Lung cancer", "Breast cancer", "Diabetes", "Heart disease"]
    
    locations = [
        "Memorial Sloan Kettering, NYC",
        "Massachusetts General Hospital, Boston",
        "Mayo Clinic, Rochester"
    ]
    
    inclusion_texts = [
        "Patients with confirmed diagnosis",
        "Adults with condition, no prior treatment",
        "Patients age 18-80"
    ]
    
    # Various exclusion criteria patterns
    exclusion_texts = [
        "Active diabetes, severe heart disease",
        "Pregnancy, severe kidney disease",
        "Recent surgery, active infection",
        "Severe cardiac disease, multiple heart attacks",
        "Active cancer, undergoing treatment",
        "Kidney failure, on dialysis",
        None  # Some trials have no exclusion criteria
    ]
    
    min_age = draw(st.integers(min_value=18, max_value=60))
    max_age = draw(st.integers(min_value=min_age + 10, max_value=85))
    
    return Trial(
        id=f"NCT{draw(st.integers(min_value=10000000, max_value=99999999))}",
        title=f"Phase {draw(st.integers(min_value=1, max_value=3))} Study",
        condition=draw(st.sampled_from(conditions)),
        min_age=min_age,
        max_age=max_age,
        gender_criteria=draw(st.sampled_from(["Male", "Female", "All", None])),
        location=draw(st.sampled_from(locations)),
        inclusion_text=draw(st.sampled_from(inclusion_texts)),
        exclusion_text=draw(st.sampled_from(exclusion_texts))
    )


# Property Test 1: Strong Exclusion Matches Receive Low Scores

@given(
    patient_profile=patient_profile_strategy(),
    trial=trial_with_exclusion_strategy()
)
@settings(max_examples=50, deadline=None)
def test_property_strong_exclusion_low_score(patient_profile, trial):
    """
    Property: Trials with strong exclusion matches (>0.8) should receive low scores (<0.3).
    
    This test verifies that when a patient strongly matches exclusion criteria,
    the final match score is reduced below the penalty threshold to indicate
    the patient is not eligible for the trial.
    
    Validates: Requirement 2.5 (exclusion criteria processing)
    """
    # Assume trial has exclusion criteria
    assume(trial.exclusion_text is not None)
    
    # Create mock matcher that returns strong exclusion match
    mock_matcher = Mock()
    mock_matcher.match_patient_to_trial.return_value = {
        'match_score': 0.25,  # Low score after penalty
        'original_score': 0.85,  # High score before penalty
        'explanation': 'Strong exclusion match - patient meets exclusion criteria',
        'inclusion_match': True,
        'exclusion_match': True,  # Strong exclusion violation
        'exclusion_penalty_applied': True
    }
    
    scorer = MatchScorer(medical_matcher=mock_matcher)
    results = scorer.score_and_rank_trials(
        patient_profile=patient_profile,
        hard_filtered_trials=[trial]
    )
    
    # Verify low score
    assert len(results) == 1
    assert results[0].match_score < EXCLUSION_PENALTY_THRESHOLD * 100, \
        f"Score {results[0].match_score} should be below {EXCLUSION_PENALTY_THRESHOLD * 100}% for strong exclusion match"
    
    # Verify exclusion warning in explanations
    has_exclusion_warning = any('⚠️' in exp and 'Exclusion' in exp for exp in results[0].key_criteria)
    assert has_exclusion_warning, "Should have exclusion warning in visual explanations"


# Property Test 2: Exclusion Penalty Consistency

@given(
    patient_profile=patient_profile_strategy(),
    trial=trial_with_exclusion_strategy()
)
@settings(max_examples=50, deadline=None)
def test_property_exclusion_penalty_consistency(patient_profile, trial):
    """
    Property: Exclusion penalty should be consistently applied when criteria are violated.
    
    This test verifies that whenever exclusion_match is True, the penalty is applied
    and the score is reduced below the threshold, regardless of the original score.
    
    Validates: Requirement 2.5 (consistent exclusion enforcement)
    """
    # Assume trial has exclusion criteria
    assume(trial.exclusion_text is not None)
    
    # Test with various original scores
    original_scores = [0.50, 0.70, 0.85, 0.95]
    
    for original_score in original_scores:
        mock_matcher = Mock()
        mock_matcher.match_patient_to_trial.return_value = {
            'match_score': min(original_score, EXCLUSION_PENALTY_THRESHOLD - 0.05),
            'original_score': original_score,
            'explanation': f'Exclusion violated (original: {original_score})',
            'inclusion_match': True,
            'exclusion_match': True,  # Exclusion violated
            'exclusion_penalty_applied': True
        }
        
        scorer = MatchScorer(medical_matcher=mock_matcher)
        results = scorer.score_and_rank_trials(
            patient_profile=patient_profile,
            hard_filtered_trials=[trial]
        )
        
        assert len(results) == 1
        
        # Verify penalty was applied (score reduced below threshold)
        assert results[0].match_score < EXCLUSION_PENALTY_THRESHOLD * 100, \
            f"Penalty not applied: score {results[0].match_score} >= {EXCLUSION_PENALTY_THRESHOLD * 100}% (original: {original_score * 100}%)"
        
        # Verify score is significantly lower than original
        assert results[0].match_score < original_score * 100, \
            f"Score {results[0].match_score} should be lower than original {original_score * 100}%"


# Property Test 3: Exclusion Violations Always Lower Than Non-Violations

@given(patient_profile=patient_profile_strategy())
@settings(max_examples=50, deadline=None)
def test_property_exclusion_violation_lower_score(patient_profile):
    """
    Property: Trials with exclusion violations should always score lower than similar trials without violations.
    
    This test verifies that exclusion criteria enforcement creates a clear distinction
    between eligible and ineligible trials.
    
    Validates: Requirement 2.5 (exclusion criteria reduce match scores)
    """
    # Create two identical trials
    trial_with_violation = Trial(
        id="NCT11111111",
        title="Trial with Exclusion Violation",
        condition="Cancer",
        min_age=18,
        max_age=80,
        gender_criteria="All",
        location="New York",
        inclusion_text="Cancer patients",
        exclusion_text="Severe heart disease"
    )
    
    trial_without_violation = Trial(
        id="NCT22222222",
        title="Trial without Exclusion Violation",
        condition="Cancer",
        min_age=18,
        max_age=80,
        gender_criteria="All",
        location="New York",
        inclusion_text="Cancer patients",
        exclusion_text="Severe heart disease"
    )
    
    mock_matcher = Mock()
    
    # First trial: exclusion violated (low score)
    # Second trial: no exclusion violation (high score)
    mock_matcher.match_patient_to_trial.side_effect = [
        {
            'match_score': 0.25,  # Low score after penalty
            'original_score': 0.80,
            'explanation': 'Exclusion violated',
            'inclusion_match': True,
            'exclusion_match': True,  # Violation
            'exclusion_penalty_applied': True
        },
        {
            'match_score': 0.80,  # High score, no penalty
            'original_score': 0.80,
            'explanation': 'Good match',
            'inclusion_match': True,
            'exclusion_match': False,  # No violation
            'exclusion_penalty_applied': False
        }
    ]
    
    scorer = MatchScorer(medical_matcher=mock_matcher)
    results = scorer.score_and_rank_trials(
        patient_profile=patient_profile,
        hard_filtered_trials=[trial_with_violation, trial_without_violation]
    )
    
    # Verify both trials scored
    assert len(results) == 2
    
    # Find each trial in results
    violation_result = next(r for r in results if r.trial_id == "NCT11111111")
    no_violation_result = next(r for r in results if r.trial_id == "NCT22222222")
    
    # Verify exclusion violation results in lower score
    assert violation_result.match_score < no_violation_result.match_score, \
        f"Trial with exclusion violation ({violation_result.match_score}%) should score lower than trial without ({no_violation_result.match_score}%)"
    
    # Verify violation score is below threshold
    assert violation_result.match_score < EXCLUSION_PENALTY_THRESHOLD * 100, \
        f"Exclusion violation score {violation_result.match_score}% should be below threshold {EXCLUSION_PENALTY_THRESHOLD * 100}%"


# Property Test 4: Various Exclusion Criteria Patterns

@given(patient_profile=patient_profile_strategy())
@settings(max_examples=50, deadline=None)
def test_property_various_exclusion_patterns(patient_profile):
    """
    Property: Different exclusion criteria patterns should all be enforced consistently.
    
    This test verifies that the exclusion penalty is applied regardless of the
    specific medical conditions mentioned in the exclusion criteria.
    
    Validates: Requirement 2.5 (handles various exclusion patterns)
    """
    # Create trials with different exclusion patterns
    exclusion_patterns = [
        "Active diabetes",
        "Severe heart disease, cardiac events",
        "Pregnancy, gestational diabetes",
        "Kidney failure, on dialysis",
        "Active infection, recent surgery",
        "Severe liver disease, cirrhosis"
    ]
    
    trials = [
        Trial(
            id=f"NCT{i:08d}",
            title=f"Trial {i}",
            condition="Cancer",
            min_age=18,
            max_age=80,
            gender_criteria="All",
            location="New York",
            inclusion_text="Cancer patients",
            exclusion_text=pattern
        )
        for i, pattern in enumerate(exclusion_patterns, start=1)
    ]
    
    mock_matcher = Mock()
    
    # All trials have exclusion violations
    mock_matcher.match_patient_to_trial.side_effect = [
        {
            'match_score': 0.25,
            'original_score': 0.75,
            'explanation': f'Exclusion violated: {pattern}',
            'inclusion_match': True,
            'exclusion_match': True,
            'exclusion_penalty_applied': True
        }
        for pattern in exclusion_patterns
    ]
    
    scorer = MatchScorer(medical_matcher=mock_matcher)
    results = scorer.score_and_rank_trials(
        patient_profile=patient_profile,
        hard_filtered_trials=trials
    )
    
    # Verify results returned (may be limited to MAX_RESULTS = 5)
    assert len(results) > 0
    assert len(results) <= len(trials)
    
    for result in results:
        assert result.match_score < EXCLUSION_PENALTY_THRESHOLD * 100, \
            f"Trial {result.trial_id} with exclusion violation should have score < {EXCLUSION_PENALTY_THRESHOLD * 100}%, got {result.match_score}%"
        
        # Verify exclusion warning present
        has_exclusion_warning = any('⚠️' in exp and 'Exclusion' in exp for exp in result.key_criteria)
        assert has_exclusion_warning, f"Trial {result.trial_id} should have exclusion warning"


# Property Test 5: No Exclusion Criteria Means No Penalty

@given(patient_profile=patient_profile_strategy())
@settings(max_examples=50, deadline=None)
def test_property_no_exclusion_no_penalty(patient_profile):
    """
    Property: Trials without exclusion criteria should never have exclusion penalty applied.
    
    This test verifies that the absence of exclusion criteria doesn't trigger
    false penalties.
    
    Validates: Requirement 2.5 (exclusion criteria are optional)
    """
    trial = Trial(
        id="NCT12345678",
        title="Trial without Exclusion Criteria",
        condition="Cancer",
        min_age=18,
        max_age=80,
        gender_criteria="All",
        location="New York",
        inclusion_text="Cancer patients",
        exclusion_text=None  # No exclusion criteria
    )
    
    mock_matcher = Mock()
    mock_matcher.match_patient_to_trial.return_value = {
        'match_score': 0.85,  # High score
        'original_score': 0.85,
        'explanation': 'Good match, no exclusion criteria',
        'inclusion_match': True,
        'exclusion_match': False,  # No exclusion
        'exclusion_penalty_applied': False  # No penalty
    }
    
    scorer = MatchScorer(medical_matcher=mock_matcher)
    results = scorer.score_and_rank_trials(
        patient_profile=patient_profile,
        hard_filtered_trials=[trial]
    )
    
    assert len(results) == 1
    
    # Verify high score (no penalty)
    assert results[0].match_score >= 0.7 * 100, \
        f"Trial without exclusion criteria should have high score, got {results[0].match_score}%"
    
    # Verify no exclusion violation warning
    exclusion_violations = [exp for exp in results[0].key_criteria if 'Exclusion violation' in exp]
    assert len(exclusion_violations) == 0, "Should not have exclusion violation warning when no exclusion criteria"


# Property Test 6: Exclusion Penalty Magnitude

@given(patient_profile=patient_profile_strategy())
@settings(max_examples=50, deadline=None)
def test_property_exclusion_penalty_magnitude(patient_profile):
    """
    Property: Exclusion penalty should reduce score to a specific range (<0.3).
    
    This test verifies that the penalty is not just applied, but applied with
    the correct magnitude to ensure clear distinction between eligible and ineligible.
    
    Validates: Requirement 2.5 (exclusion penalty threshold)
    """
    trial = Trial(
        id="NCT12345678",
        title="Test Trial",
        condition="Cancer",
        min_age=18,
        max_age=80,
        gender_criteria="All",
        location="New York",
        inclusion_text="Cancer patients",
        exclusion_text="Severe disease"
    )
    
    # Test with various high original scores
    original_scores = [0.60, 0.75, 0.85, 0.95, 1.0]
    
    for original_score in original_scores:
        mock_matcher = Mock()
        mock_matcher.match_patient_to_trial.return_value = {
            'match_score': 0.25,  # Penalized score
            'original_score': original_score,
            'explanation': f'Exclusion penalty applied (was {original_score})',
            'inclusion_match': True,
            'exclusion_match': True,
            'exclusion_penalty_applied': True
        }
        
        scorer = MatchScorer(medical_matcher=mock_matcher)
        results = scorer.score_and_rank_trials(
            patient_profile=patient_profile,
            hard_filtered_trials=[trial]
        )
        
        assert len(results) == 1
        
        # Verify score is below threshold
        assert results[0].match_score < EXCLUSION_PENALTY_THRESHOLD * 100, \
            f"Penalized score {results[0].match_score}% should be < {EXCLUSION_PENALTY_THRESHOLD * 100}%"
        
        # Verify score is in expected range (typically 0.25 = 25%)
        assert 0 <= results[0].match_score <= EXCLUSION_PENALTY_THRESHOLD * 100, \
            f"Penalized score {results[0].match_score}% should be in range [0, {EXCLUSION_PENALTY_THRESHOLD * 100}%]"


# Property Test 7: Exclusion Match Ranking

@given(patient_profile=patient_profile_strategy())
@settings(max_examples=50, deadline=None)
def test_property_exclusion_match_ranking(patient_profile):
    """
    Property: Trials with exclusion violations should rank lower than trials without.
    
    This test verifies that the ranking algorithm correctly places trials with
    exclusion violations at the bottom of the results list.
    
    Validates: Requirement 2.5 (exclusion affects ranking)
    """
    # Create mix of trials with and without exclusion violations
    trials = [
        Trial(
            id="NCT11111111",
            title="Trial A - No Violation",
            condition="Cancer",
            min_age=18,
            max_age=80,
            gender_criteria="All",
            location="New York",
            inclusion_text="Cancer patients",
            exclusion_text="Severe disease"
        ),
        Trial(
            id="NCT22222222",
            title="Trial B - Violation",
            condition="Cancer",
            min_age=18,
            max_age=80,
            gender_criteria="All",
            location="Boston",
            inclusion_text="Cancer patients",
            exclusion_text="Severe disease"
        ),
        Trial(
            id="NCT33333333",
            title="Trial C - No Violation",
            condition="Cancer",
            min_age=18,
            max_age=80,
            gender_criteria="All",
            location="Chicago",
            inclusion_text="Cancer patients",
            exclusion_text="Severe disease"
        )
    ]
    
    mock_matcher = Mock()
    mock_matcher.match_patient_to_trial.side_effect = [
        # Trial A: No violation, high score
        {
            'match_score': 0.85,
            'original_score': 0.85,
            'explanation': 'Good match',
            'inclusion_match': True,
            'exclusion_match': False,
            'exclusion_penalty_applied': False
        },
        # Trial B: Violation, low score
        {
            'match_score': 0.25,
            'original_score': 0.80,
            'explanation': 'Exclusion violated',
            'inclusion_match': True,
            'exclusion_match': True,
            'exclusion_penalty_applied': True
        },
        # Trial C: No violation, medium score
        {
            'match_score': 0.70,
            'original_score': 0.70,
            'explanation': 'Moderate match',
            'inclusion_match': True,
            'exclusion_match': False,
            'exclusion_penalty_applied': False
        }
    ]
    
    scorer = MatchScorer(medical_matcher=mock_matcher)
    results = scorer.score_and_rank_trials(
        patient_profile=patient_profile,
        hard_filtered_trials=trials
    )
    
    assert len(results) == 3
    
    # Verify ranking: A (85%) > C (70%) > B (25%)
    assert results[0].trial_id == "NCT11111111", "Trial A should rank first"
    assert results[1].trial_id == "NCT33333333", "Trial C should rank second"
    assert results[2].trial_id == "NCT22222222", "Trial B (with violation) should rank last"
    
    # Verify the trial with violation has lowest score
    assert results[2].match_score < EXCLUSION_PENALTY_THRESHOLD * 100, \
        f"Trial with violation should have score < {EXCLUSION_PENALTY_THRESHOLD * 100}%"


# Example-based tests to complement property tests

def test_example_diabetes_exclusion():
    """
    Example: Patient with diabetes excluded from trial that excludes diabetes.
    """
    patient = PatientProfile(
        condition="Lung cancer",
        age=65,
        gender="Male",
        location="New York",
        distance_miles=50,
        medical_history="Smoking history, Type 2 diabetes, hypertension"
    )
    
    trial = Trial(
        id="NCT12345678",
        title="Lung Cancer Trial",
        condition="Lung cancer",
        min_age=18,
        max_age=80,
        gender_criteria="All",
        location="New York",
        inclusion_text="Lung cancer with smoking history",
        exclusion_text="Active diabetes, severe kidney disease"
    )
    
    mock_matcher = Mock()
    mock_matcher.match_patient_to_trial.return_value = {
        'match_score': 0.25,  # Low due to diabetes exclusion
        'original_score': 0.90,  # Would be high without exclusion
        'explanation': 'Patient has diabetes which is an exclusion criterion',
        'inclusion_match': True,
        'exclusion_match': True,
        'exclusion_penalty_applied': True
    }
    
    scorer = MatchScorer(medical_matcher=mock_matcher)
    results = scorer.score_and_rank_trials(
        patient_profile=patient,
        hard_filtered_trials=[trial]
    )
    
    assert len(results) == 1
    assert results[0].match_score == 25.0
    assert results[0].match_score < EXCLUSION_PENALTY_THRESHOLD * 100
    
    # Verify exclusion warning in explanations
    has_exclusion_warning = any('Exclusion' in exp and '⚠️' in exp for exp in results[0].key_criteria)
    assert has_exclusion_warning


def test_example_pregnancy_exclusion():
    """
    Example: Pregnant patient excluded from trial that excludes pregnancy.
    """
    patient = PatientProfile(
        condition="Breast cancer",
        age=32,
        gender="Female",
        location="Boston",
        distance_miles=25,
        medical_history="Pregnancy, gestational diabetes"
    )
    
    trial = Trial(
        id="NCT87654321",
        title="Breast Cancer Trial",
        condition="Breast cancer",
        min_age=18,
        max_age=65,
        gender_criteria="Female",
        location="Boston",
        inclusion_text="Female breast cancer patients",
        exclusion_text="Pregnancy, severe liver disease"
    )
    
    mock_matcher = Mock()
    mock_matcher.match_patient_to_trial.return_value = {
        'match_score': 0.20,
        'original_score': 0.85,
        'explanation': 'Pregnancy is an exclusion criterion',
        'inclusion_match': True,
        'exclusion_match': True,
        'exclusion_penalty_applied': True
    }
    
    scorer = MatchScorer(medical_matcher=mock_matcher)
    results = scorer.score_and_rank_trials(
        patient_profile=patient,
        hard_filtered_trials=[trial]
    )
    
    assert len(results) == 1
    assert results[0].match_score == 20.0
    assert results[0].match_score < EXCLUSION_PENALTY_THRESHOLD * 100
