"""
Property-Based Tests for Match Score Consistency

This module implements Property 2: Match Score Consistency
Validates Requirements 3.1, 3.2 from the design document.

Property Tests:
1. Higher scores correspond to better criterion alignment
2. Identical profiles produce identical scores
3. Score ordering is transitive

Uses Hypothesis for property-based testing with randomly generated patient profiles
and trial data to ensure scoring consistency across diverse inputs.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, example
from unittest.mock import Mock
from typing import List, Tuple

from src.ai_matching.match_scorer import (
    MatchScorer,
    PatientProfile,
    Trial,
    MatchResult
)


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
        "Heart disease",
        "Asthma",
        "Depression"
    ]
    
    genders = ["Male", "Female", "Other"]
    
    locations = [
        "New York, NY",
        "Boston, MA",
        "Los Angeles, CA",
        "Chicago, IL",
        "Houston, TX"
    ]
    
    medical_histories = [
        "History of smoking, hypertension, no diabetes",
        "Type 2 diabetes, high cholesterol, no heart disease",
        "Asthma, seasonal allergies, no smoking",
        "Previous heart attack, on blood thinners",
        "Depression, anxiety, on medication",
        "No significant medical history",
        "Hypertension controlled with medication"
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
def trial_strategy(draw):
    """
    Generate random but valid trial data for property testing.
    
    Returns:
        Trial with randomized but realistic values
    """
    conditions = [
        "Lung cancer",
        "Breast cancer",
        "Diabetes",
        "Cardiovascular disease",
        "Respiratory disease"
    ]
    
    gender_criteria_options = ["Male", "Female", "All", None]
    
    locations = [
        "Memorial Sloan Kettering, NYC",
        "Massachusetts General Hospital, Boston",
        "Mayo Clinic, Rochester",
        "Johns Hopkins, Baltimore"
    ]
    
    inclusion_texts = [
        "Patients with confirmed diagnosis, age 18-80",
        "Adults with condition, no prior treatment",
        "Patients with smoking history",
        "Confirmed diagnosis within last 6 months"
    ]
    
    exclusion_texts = [
        "Active diabetes, severe heart disease",
        "Pregnancy, severe kidney disease",
        "Recent surgery, active infection",
        None
    ]
    
    # Generate age range
    min_age = draw(st.integers(min_value=18, max_value=60))
    max_age = draw(st.integers(min_value=min_age + 10, max_value=85))
    
    return Trial(
        id=f"NCT{draw(st.integers(min_value=10000000, max_value=99999999))}",
        title=f"Phase {draw(st.integers(min_value=1, max_value=3))} Study",
        condition=draw(st.sampled_from(conditions)),
        min_age=min_age,
        max_age=max_age,
        gender_criteria=draw(st.sampled_from(gender_criteria_options)),
        location=draw(st.sampled_from(locations)),
        inclusion_text=draw(st.sampled_from(inclusion_texts)),
        exclusion_text=draw(st.sampled_from(exclusion_texts))
    )


@st.composite
def trial_list_strategy(draw, min_size=2, max_size=10):
    """
    Generate list of trials for property testing.
    
    Args:
        min_size: Minimum number of trials
        max_size: Maximum number of trials
    
    Returns:
        List of Trial objects
    """
    size = draw(st.integers(min_value=min_size, max_value=max_size))
    return [draw(trial_strategy()) for _ in range(size)]


# Property Test 1: Identical Profiles Produce Identical Scores

@given(
    patient_profile=patient_profile_strategy(),
    trial=trial_strategy()
)
@settings(max_examples=50, deadline=None)
def test_property_identical_profiles_identical_scores(patient_profile, trial):
    """
    Property: Identical patient profiles should produce identical match scores.
    
    This test verifies that the scoring algorithm is deterministic - running
    the same patient profile against the same trial multiple times should
    always produce the same score.
    
    Validates: Requirement 3.1 (consistent match scoring)
    """
    # Create mock medical matcher with fixed score
    mock_matcher = Mock()
    mock_matcher.match_patient_to_trial.return_value = {
        'match_score': 0.85,
        'original_score': 0.85,
        'explanation': 'Test match',
        'inclusion_match': True,
        'exclusion_match': False,
        'exclusion_penalty_applied': False
    }
    
    scorer = MatchScorer(medical_matcher=mock_matcher)
    
    # Score the same trial twice with identical profile
    result1 = scorer.score_and_rank_trials(
        patient_profile=patient_profile,
        hard_filtered_trials=[trial]
    )
    
    result2 = scorer.score_and_rank_trials(
        patient_profile=patient_profile,
        hard_filtered_trials=[trial]
    )
    
    # Verify identical scores
    assert len(result1) == 1
    assert len(result2) == 1
    assert result1[0].match_score == result2[0].match_score
    assert result1[0].match_percentage == result2[0].match_percentage
    assert result1[0].trial_id == result2[0].trial_id


# Property Test 2: Higher Scores Correspond to Better Criterion Alignment

@given(patient_profile=patient_profile_strategy())
@settings(max_examples=50, deadline=None)
def test_property_higher_scores_better_alignment(patient_profile):
    """
    Property: Trials with higher match scores should have better criterion alignment.
    
    This test verifies that when we have multiple trials with different scores,
    the higher-scored trials actually have more matching criteria than lower-scored
    trials.
    
    Validates: Requirements 3.1, 3.2 (match scoring reflects criterion alignment)
    """
    # Create three trials with different match scores
    trials = [
        Trial(
            id="NCT11111111",
            title="Trial A - Low Score",
            condition="Cancer",
            min_age=18,
            max_age=80,
            gender_criteria="All",
            location="New York",
            inclusion_text="Cancer patients",
            exclusion_text=None
        ),
        Trial(
            id="NCT22222222",
            title="Trial B - Medium Score",
            condition="Cancer",
            min_age=18,
            max_age=80,
            gender_criteria="All",
            location="Boston",
            inclusion_text="Cancer patients with history",
            exclusion_text=None
        ),
        Trial(
            id="NCT33333333",
            title="Trial C - High Score",
            condition="Cancer",
            min_age=18,
            max_age=80,
            gender_criteria="All",
            location="Chicago",
            inclusion_text="Cancer patients with specific history",
            exclusion_text=None
        )
    ]
    
    # Create mock matcher that returns increasing scores
    mock_matcher = Mock()
    mock_matcher.match_patient_to_trial.side_effect = [
        {
            'match_score': 0.40,  # Low
            'original_score': 0.40,
            'explanation': 'Low match',
            'inclusion_match': False,
            'exclusion_match': False,
            'exclusion_penalty_applied': False
        },
        {
            'match_score': 0.70,  # Medium
            'original_score': 0.70,
            'explanation': 'Medium match',
            'inclusion_match': True,
            'exclusion_match': False,
            'exclusion_penalty_applied': False
        },
        {
            'match_score': 0.95,  # High
            'original_score': 0.95,
            'explanation': 'High match',
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
    
    # Verify results are ranked by score (highest first)
    assert len(results) == 3
    assert results[0].match_score > results[1].match_score
    assert results[1].match_score > results[2].match_score
    
    # Verify higher scores have more positive criteria (checkmarks)
    checkmarks_high = sum(1 for exp in results[0].key_criteria if '✅' in exp)
    checkmarks_medium = sum(1 for exp in results[1].key_criteria if '✅' in exp)
    checkmarks_low = sum(1 for exp in results[2].key_criteria if '✅' in exp)
    
    # Higher scored trials should have at least as many checkmarks
    assert checkmarks_high >= checkmarks_medium
    assert checkmarks_medium >= checkmarks_low


# Property Test 3: Score Ordering is Transitive

@given(patient_profile=patient_profile_strategy())
@settings(max_examples=50, deadline=None)
def test_property_score_ordering_transitive(patient_profile):
    """
    Property: Score ordering should be transitive.
    
    If Trial A scores higher than Trial B, and Trial B scores higher than Trial C,
    then Trial A must score higher than Trial C.
    
    This ensures consistent ranking across all trials.
    
    Validates: Requirement 3.2 (consistent trial ranking)
    """
    # Create three trials
    trials = [
        Trial(
            id="NCT11111111",
            title="Trial A",
            condition="Cancer",
            min_age=18,
            max_age=80,
            gender_criteria="All",
            location="New York",
            inclusion_text="Cancer patients A",
            exclusion_text=None
        ),
        Trial(
            id="NCT22222222",
            title="Trial B",
            condition="Cancer",
            min_age=18,
            max_age=80,
            gender_criteria="All",
            location="Boston",
            inclusion_text="Cancer patients B",
            exclusion_text=None
        ),
        Trial(
            id="NCT33333333",
            title="Trial C",
            condition="Cancer",
            min_age=18,
            max_age=80,
            gender_criteria="All",
            location="Chicago",
            inclusion_text="Cancer patients C",
            exclusion_text=None
        )
    ]
    
    # Create mock matcher with ordered scores: A > B > C
    mock_matcher = Mock()
    mock_matcher.match_patient_to_trial.side_effect = [
        {
            'match_score': 0.90,  # Trial A
            'original_score': 0.90,
            'explanation': 'High match',
            'inclusion_match': True,
            'exclusion_match': False,
            'exclusion_penalty_applied': False
        },
        {
            'match_score': 0.70,  # Trial B
            'original_score': 0.70,
            'explanation': 'Medium match',
            'inclusion_match': True,
            'exclusion_match': False,
            'exclusion_penalty_applied': False
        },
        {
            'match_score': 0.50,  # Trial C
            'original_score': 0.50,
            'explanation': 'Low match',
            'inclusion_match': False,
            'exclusion_match': False,
            'exclusion_penalty_applied': False
        }
    ]
    
    scorer = MatchScorer(medical_matcher=mock_matcher)
    results = scorer.score_and_rank_trials(
        patient_profile=patient_profile,
        hard_filtered_trials=trials
    )
    
    # Verify transitive ordering: A > B > C
    assert len(results) == 3
    
    score_a = results[0].match_score
    score_b = results[1].match_score
    score_c = results[2].match_score
    
    # A > B and B > C, therefore A > C (transitivity)
    assert score_a > score_b, "Trial A should score higher than Trial B"
    assert score_b > score_c, "Trial B should score higher than Trial C"
    assert score_a > score_c, "Trial A should score higher than Trial C (transitivity)"


# Property Test 4: Score Consistency Across Multiple Runs

@given(
    patient_profile=patient_profile_strategy(),
    trials=trial_list_strategy(min_size=3, max_size=5)
)
@settings(max_examples=30, deadline=None)
def test_property_score_consistency_multiple_runs(patient_profile, trials):
    """
    Property: Running the same scoring multiple times should produce consistent rankings.
    
    This test verifies that the relative ordering of trials remains consistent
    across multiple scoring runs with the same inputs.
    
    Validates: Requirements 3.1, 3.2 (consistent scoring and ranking)
    """
    # Create mock matcher with deterministic scores based on trial ID
    def get_score_for_trial(trial_id):
        """Generate deterministic score based on trial ID"""
        # Use hash of trial ID to generate consistent but varied scores
        hash_val = abs(hash(trial_id))
        return 0.3 + (hash_val % 60) / 100.0  # Scores between 0.3 and 0.9
    
    mock_matcher = Mock()
    
    # First run
    mock_matcher.match_patient_to_trial.side_effect = [
        {
            'match_score': get_score_for_trial(trial.id),
            'original_score': get_score_for_trial(trial.id),
            'explanation': f'Match for {trial.id}',
            'inclusion_match': True,
            'exclusion_match': False,
            'exclusion_penalty_applied': False
        }
        for trial in trials
    ]
    
    scorer = MatchScorer(medical_matcher=mock_matcher)
    results1 = scorer.score_and_rank_trials(
        patient_profile=patient_profile,
        hard_filtered_trials=trials
    )
    
    # Second run with same inputs
    mock_matcher.match_patient_to_trial.side_effect = [
        {
            'match_score': get_score_for_trial(trial.id),
            'original_score': get_score_for_trial(trial.id),
            'explanation': f'Match for {trial.id}',
            'inclusion_match': True,
            'exclusion_match': False,
            'exclusion_penalty_applied': False
        }
        for trial in trials
    ]
    
    results2 = scorer.score_and_rank_trials(
        patient_profile=patient_profile,
        hard_filtered_trials=trials
    )
    
    # Verify same number of results
    assert len(results1) == len(results2)
    
    # Verify same ordering (trial IDs in same order)
    trial_ids_1 = [r.trial_id for r in results1]
    trial_ids_2 = [r.trial_id for r in results2]
    assert trial_ids_1 == trial_ids_2, "Trial ordering should be consistent across runs"
    
    # Verify same scores
    for r1, r2 in zip(results1, results2):
        assert r1.match_score == r2.match_score
        assert r1.trial_id == r2.trial_id


# Property Test 5: Score Monotonicity with Criterion Matches

@given(patient_profile=patient_profile_strategy())
@settings(max_examples=50, deadline=None)
def test_property_score_monotonicity_with_criteria(patient_profile):
    """
    Property: More matching criteria should result in higher or equal scores.
    
    This test verifies that as we increase the number of matching criteria
    (inclusion match, no exclusion violation, etc.), the score should not decrease.
    
    Validates: Requirement 3.1 (match scores reflect criterion alignment)
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
    
    # Test different criterion match scenarios
    scenarios = [
        # Scenario 1: No inclusion match, no exclusion violation
        {
            'match_score': 0.40,
            'original_score': 0.40,
            'explanation': 'Low match',
            'inclusion_match': False,
            'exclusion_match': False,
            'exclusion_penalty_applied': False
        },
        # Scenario 2: Inclusion match, no exclusion violation (should be higher)
        {
            'match_score': 0.75,
            'original_score': 0.75,
            'explanation': 'Good match',
            'inclusion_match': True,
            'exclusion_match': False,
            'exclusion_penalty_applied': False
        },
        # Scenario 3: Inclusion match with exclusion violation (should be lower)
        {
            'match_score': 0.25,
            'original_score': 0.80,
            'explanation': 'Exclusion violated',
            'inclusion_match': True,
            'exclusion_match': True,
            'exclusion_penalty_applied': True
        }
    ]
    
    scores = []
    
    for scenario in scenarios:
        mock_matcher = Mock()
        mock_matcher.match_patient_to_trial.return_value = scenario
        
        scorer = MatchScorer(medical_matcher=mock_matcher)
        results = scorer.score_and_rank_trials(
            patient_profile=patient_profile,
            hard_filtered_trials=[trial]
        )
        
        assert len(results) == 1
        scores.append((results[0].match_score, scenario['inclusion_match'], scenario['exclusion_match']))
    
    # Verify: Inclusion match without exclusion > No inclusion match
    no_inclusion_score = scores[0][0]
    with_inclusion_score = scores[1][0]
    assert with_inclusion_score > no_inclusion_score, \
        "Inclusion match should result in higher score"
    
    # Verify: Exclusion violation results in low score
    exclusion_violated_score = scores[2][0]
    assert exclusion_violated_score < with_inclusion_score, \
        "Exclusion violation should result in lower score"


# Property Test 6: Score Bounds

@given(
    patient_profile=patient_profile_strategy(),
    trial=trial_strategy()
)
@settings(max_examples=50, deadline=None)
def test_property_score_bounds(patient_profile, trial):
    """
    Property: All match scores should be within valid bounds (0-100).
    
    This test verifies that the scoring algorithm never produces scores
    outside the valid range, regardless of input.
    
    Validates: Requirement 3.1 (valid match percentages)
    """
    # Test with various score values from mock
    test_scores = [0.0, 0.25, 0.50, 0.75, 1.0]
    
    for test_score in test_scores:
        mock_matcher = Mock()
        mock_matcher.match_patient_to_trial.return_value = {
            'match_score': test_score,
            'original_score': test_score,
            'explanation': f'Test score {test_score}',
            'inclusion_match': True,
            'exclusion_match': False,
            'exclusion_penalty_applied': False
        }
        
        scorer = MatchScorer(medical_matcher=mock_matcher)
        results = scorer.score_and_rank_trials(
            patient_profile=patient_profile,
            hard_filtered_trials=[trial]
        )
        
        assert len(results) == 1
        
        # Verify score is within bounds
        assert 0 <= results[0].match_score <= 100, \
            f"Score {results[0].match_score} is outside valid range [0, 100]"
        
        # Verify percentage string is correctly formatted
        assert results[0].match_percentage.endswith('%')
        percentage_value = int(results[0].match_percentage[:-1])
        assert 0 <= percentage_value <= 100


# Example-based tests to complement property tests

def test_example_perfect_match():
    """
    Example: Perfect match scenario (score = 1.0 = 100%)
    """
    patient = PatientProfile(
        condition="Lung cancer",
        age=65,
        gender="Male",
        location="New York",
        distance_miles=50,
        medical_history="Smoking history, hypertension"
    )
    
    trial = Trial(
        id="NCT12345678",
        title="Perfect Match Trial",
        condition="Lung cancer",
        min_age=18,
        max_age=80,
        gender_criteria="Male",
        location="New York",
        inclusion_text="Lung cancer with smoking history",
        exclusion_text=None
    )
    
    mock_matcher = Mock()
    mock_matcher.match_patient_to_trial.return_value = {
        'match_score': 1.0,
        'original_score': 1.0,
        'explanation': 'Perfect match',
        'inclusion_match': True,
        'exclusion_match': False,
        'exclusion_penalty_applied': False
    }
    
    scorer = MatchScorer(medical_matcher=mock_matcher)
    results = scorer.score_and_rank_trials(
        patient_profile=patient,
        hard_filtered_trials=[trial]
    )
    
    assert len(results) == 1
    assert results[0].match_score == 100.0
    assert results[0].match_percentage == "100%"


def test_example_no_match():
    """
    Example: No match scenario (score = 0.0 = 0%)
    """
    patient = PatientProfile(
        condition="Lung cancer",
        age=65,
        gender="Male",
        location="New York",
        distance_miles=50,
        medical_history="No relevant history"
    )
    
    trial = Trial(
        id="NCT12345678",
        title="No Match Trial",
        condition="Breast cancer",
        min_age=18,
        max_age=50,
        gender_criteria="Female",
        location="California",
        inclusion_text="Breast cancer patients",
        exclusion_text="Male gender"
    )
    
    mock_matcher = Mock()
    mock_matcher.match_patient_to_trial.return_value = {
        'match_score': 0.0,
        'original_score': 0.0,
        'explanation': 'No match',
        'inclusion_match': False,
        'exclusion_match': True,
        'exclusion_penalty_applied': True
    }
    
    scorer = MatchScorer(medical_matcher=mock_matcher)
    results = scorer.score_and_rank_trials(
        patient_profile=patient,
        hard_filtered_trials=[trial]
    )
    
    assert len(results) == 1
    assert results[0].match_score == 0.0
    assert results[0].match_percentage == "0%"
