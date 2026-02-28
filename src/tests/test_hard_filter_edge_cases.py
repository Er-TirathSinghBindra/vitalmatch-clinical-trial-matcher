"""
Unit Tests for Hard Filter Engine Edge Cases
Tests specific edge cases and boundary conditions
Requirements: 2.1, 2.2
"""

import pytest
import os
import sys
from typing import Dict, Any, List

# Import the hard filter engine
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from hard_filter.filter_engine import HardFilterEngine, PatientProfile


# Database connection parameters
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_NAME = os.getenv('DB_NAME', 'vitalmatch_test')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')
DB_PORT = int(os.getenv('DB_PORT', '5432'))


@pytest.fixture
def engine():
    """Create hard filter engine for testing"""
    return HardFilterEngine(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT
    )


@pytest.fixture
def insert_trial(engine):
    """Fixture to insert and cleanup test trials"""
    inserted_ids = []
    
    def _insert(trial: Dict[str, Any]):
        with engine.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO trials (
                        id, title, condition, min_age, max_age,
                        gender_criteria, location, inclusion_text, exclusion_text
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """, (
                    trial['id'], trial['title'], trial['condition'],
                    trial['min_age'], trial['max_age'], trial['gender_criteria'],
                    trial['location'], trial['inclusion_text'], trial['exclusion_text']
                ))
            conn.commit()
        inserted_ids.append(trial['id'])
        return trial['id']
    
    yield _insert
    
    # Cleanup
    with engine.get_connection() as conn:
        with conn.cursor() as cursor:
            for trial_id in inserted_ids:
                cursor.execute("DELETE FROM trials WHERE id = %s", (trial_id,))
        conn.commit()


# ============================================================================
# Edge Case Tests: Missing Age Criteria
# ============================================================================

def test_trial_with_no_age_criteria_matches_all_ages(engine, insert_trial):
    """Test that trials with NULL min_age and max_age match any patient age"""
    trial = {
        'id': 'NCT00000001',
        'title': 'No Age Restriction Trial',
        'condition': 'Diabetes',
        'min_age': None,
        'max_age': None,
        'gender_criteria': 'All',
        'location': 'New York, NY',
        'inclusion_text': 'All ages welcome',
        'exclusion_text': 'None'
    }
    insert_trial(trial)
    
    # Test with various ages
    for age in [18, 25, 50, 75, 90]:
        results = engine.filter_by_age(age)
        trial_ids = [t['id'] for t in results]
        assert trial['id'] in trial_ids, \
            f"Trial with no age criteria should match age {age}"


def test_trial_with_only_min_age(engine, insert_trial):
    """Test trial with min_age but no max_age"""
    trial = {
        'id': 'NCT00000002',
        'title': 'Min Age Only Trial',
        'condition': 'Diabetes',
        'min_age': 50,
        'max_age': None,
        'gender_criteria': 'All',
        'location': 'New York, NY',
        'inclusion_text': 'Age 50 and above',
        'exclusion_text': 'None'
    }
    insert_trial(trial)
    
    # Should match ages >= 50
    results = engine.filter_by_age(50)
    assert trial['id'] in [t['id'] for t in results]
    
    results = engine.filter_by_age(75)
    assert trial['id'] in [t['id'] for t in results]
    
    # Should NOT match ages < 50
    results = engine.filter_by_age(49)
    assert trial['id'] not in [t['id'] for t in results]


def test_trial_with_only_max_age(engine, insert_trial):
    """Test trial with max_age but no min_age"""
    trial = {
        'id': 'NCT00000003',
        'title': 'Max Age Only Trial',
        'condition': 'Diabetes',
        'min_age': None,
        'max_age': 65,
        'gender_criteria': 'All',
        'location': 'New York, NY',
        'inclusion_text': 'Age 65 and below',
        'exclusion_text': 'None'
    }
    insert_trial(trial)
    
    # Should match ages <= 65
    results = engine.filter_by_age(65)
    assert trial['id'] in [t['id'] for t in results]
    
    results = engine.filter_by_age(30)
    assert trial['id'] in [t['id'] for t in results]
    
    # Should NOT match ages > 65
    results = engine.filter_by_age(66)
    assert trial['id'] not in [t['id'] for t in results]


def test_age_boundary_exact_match(engine, insert_trial):
    """Test exact boundary conditions for age"""
    trial = {
        'id': 'NCT00000004',
        'title': 'Age Boundary Trial',
        'condition': 'Diabetes',
        'min_age': 40,
        'max_age': 60,
        'gender_criteria': 'All',
        'location': 'New York, NY',
        'inclusion_text': 'Ages 40-60',
        'exclusion_text': 'None'
    }
    insert_trial(trial)
    
    # Exact boundaries should match
    results = engine.filter_by_age(40)
    assert trial['id'] in [t['id'] for t in results], "min_age boundary should match"
    
    results = engine.filter_by_age(60)
    assert trial['id'] in [t['id'] for t in results], "max_age boundary should match"
    
    # Just outside boundaries should NOT match
    results = engine.filter_by_age(39)
    assert trial['id'] not in [t['id'] for t in results], "Below min_age should not match"
    
    results = engine.filter_by_age(61)
    assert trial['id'] not in [t['id'] for t in results], "Above max_age should not match"


# ============================================================================
# Edge Case Tests: Gender Criteria
# ============================================================================

def test_trial_with_all_gender_matches_any_gender(engine, insert_trial):
    """Test that trials with 'All' gender criteria match any patient gender"""
    trial = {
        'id': 'NCT00000005',
        'title': 'All Genders Trial',
        'condition': 'Diabetes',
        'min_age': None,
        'max_age': None,
        'gender_criteria': 'All',
        'location': 'New York, NY',
        'inclusion_text': 'All genders',
        'exclusion_text': 'None'
    }
    insert_trial(trial)
    
    # Should match all genders
    for gender in ['Male', 'Female', 'Other']:
        results = engine.filter_by_gender(gender)
        trial_ids = [t['id'] for t in results]
        assert trial['id'] in trial_ids, \
            f"Trial with 'All' gender should match {gender}"


def test_trial_with_null_gender_matches_any_gender(engine, insert_trial):
    """Test that trials with NULL gender criteria match any patient gender"""
    trial = {
        'id': 'NCT00000006',
        'title': 'Null Gender Trial',
        'condition': 'Diabetes',
        'min_age': None,
        'max_age': None,
        'gender_criteria': None,
        'location': 'New York, NY',
        'inclusion_text': 'No gender restriction',
        'exclusion_text': 'None'
    }
    insert_trial(trial)
    
    # Should match all genders
    for gender in ['Male', 'Female', 'Other']:
        results = engine.filter_by_gender(gender)
        trial_ids = [t['id'] for t in results]
        assert trial['id'] in trial_ids, \
            f"Trial with NULL gender should match {gender}"


def test_trial_with_specific_gender_only_matches_that_gender(engine, insert_trial):
    """Test that trials with specific gender only match that gender"""
    trial = {
        'id': 'NCT00000007',
        'title': 'Female Only Trial',
        'condition': 'Breast Cancer',
        'min_age': None,
        'max_age': None,
        'gender_criteria': 'Female',
        'location': 'New York, NY',
        'inclusion_text': 'Female patients only',
        'exclusion_text': 'Male patients'
    }
    insert_trial(trial)
    
    # Should match Female
    results = engine.filter_by_gender('Female')
    assert trial['id'] in [t['id'] for t in results]
    
    # Should NOT match Male or Other
    results = engine.filter_by_gender('Male')
    assert trial['id'] not in [t['id'] for t in results]
    
    results = engine.filter_by_gender('Other')
    assert trial['id'] not in [t['id'] for t in results]


def test_gender_matching_is_case_insensitive(engine, insert_trial):
    """Test that gender matching is case-insensitive"""
    trial = {
        'id': 'NCT00000008',
        'title': 'Case Test Trial',
        'condition': 'Diabetes',
        'min_age': None,
        'max_age': None,
        'gender_criteria': 'MALE',
        'location': 'New York, NY',
        'inclusion_text': 'Male patients',
        'exclusion_text': 'None'
    }
    insert_trial(trial)
    
    # Should match regardless of case
    for gender_variant in ['Male', 'male', 'MALE', 'MaLe']:
        results = engine.filter_by_gender(gender_variant)
        trial_ids = [t['id'] for t in results]
        assert trial['id'] in trial_ids, \
            f"Gender matching should be case-insensitive for {gender_variant}"


# ============================================================================
# Edge Case Tests: Location
# ============================================================================

def test_location_with_null_value(engine, insert_trial):
    """Test trials with NULL location"""
    trial = {
        'id': 'NCT00000009',
        'title': 'No Location Trial',
        'condition': 'Diabetes',
        'min_age': None,
        'max_age': None,
        'gender_criteria': 'All',
        'location': None,
        'inclusion_text': 'Virtual trial',
        'exclusion_text': 'None'
    }
    insert_trial(trial)
    
    # Location filter should not return trials with NULL location
    results = engine.filter_by_location('New York')
    trial_ids = [t['id'] for t in results]
    assert trial['id'] not in trial_ids, \
        "Trial with NULL location should not match location filter"


def test_location_partial_match(engine, insert_trial):
    """Test location matching with partial strings"""
    trial = {
        'id': 'NCT00000010',
        'title': 'NYC Trial',
        'condition': 'Diabetes',
        'min_age': None,
        'max_age': None,
        'gender_criteria': 'All',
        'location': 'Memorial Sloan Kettering, New York, NY',
        'inclusion_text': 'NYC location',
        'exclusion_text': 'None'
    }
    insert_trial(trial)
    
    # Should match various location queries
    for location_query in ['New York', 'NY', 'Memorial']:
        results = engine.filter_by_location(location_query)
        trial_ids = [t['id'] for t in results]
        assert trial['id'] in trial_ids, \
            f"Location should match partial query: {location_query}"


def test_location_case_insensitive(engine, insert_trial):
    """Test that location matching is case-insensitive"""
    trial = {
        'id': 'NCT00000011',
        'title': 'Location Case Trial',
        'condition': 'Diabetes',
        'min_age': None,
        'max_age': None,
        'gender_criteria': 'All',
        'location': 'Boston Medical Center, Boston, MA',
        'inclusion_text': 'Boston location',
        'exclusion_text': 'None'
    }
    insert_trial(trial)
    
    # Should match regardless of case
    for location_variant in ['Boston', 'boston', 'BOSTON', 'BoStOn']:
        results = engine.filter_by_location(location_variant)
        trial_ids = [t['id'] for t in results]
        assert trial['id'] in trial_ids, \
            f"Location matching should be case-insensitive for {location_variant}"


# ============================================================================
# Edge Case Tests: Empty Results
# ============================================================================

def test_no_matching_trials_returns_empty_list(engine):
    """Test that no matches returns empty list, not error"""
    # Query for non-existent condition
    results = engine.filter_by_condition('NonExistentCondition12345')
    assert isinstance(results, list), "Should return list"
    assert len(results) == 0, "Should return empty list when no matches"


def test_filter_with_impossible_criteria(engine, insert_trial):
    """Test filtering with criteria that can't be satisfied"""
    trial = {
        'id': 'NCT00000012',
        'title': 'Narrow Criteria Trial',
        'condition': 'Diabetes',
        'min_age': 50,
        'max_age': 60,
        'gender_criteria': 'Female',
        'location': 'New York, NY',
        'inclusion_text': 'Narrow criteria',
        'exclusion_text': 'None'
    }
    insert_trial(trial)
    
    # Patient that doesn't match
    patient = PatientProfile(
        condition='Diabetes',
        age=70,  # Outside age range
        gender='Female',
        location='New York, NY',
        distance_miles=50
    )
    
    result = engine.filter_trials(patient)
    assert trial['id'] not in [t['id'] for t in result.trials], \
        "Trial should not match patient outside age range"


def test_empty_database_returns_empty_results(engine):
    """Test that empty database returns empty results gracefully"""
    # This assumes test database might be empty
    patient = PatientProfile(
        condition='RareCondition999',
        age=50,
        gender='Male',
        location='Unknown City',
        distance_miles=50
    )
    
    result = engine.filter_trials(patient)
    assert isinstance(result.trials, list), "Should return list"
    assert result.total_count >= 0, "Total count should be non-negative"
    assert result.filtered_count >= 0, "Filtered count should be non-negative"


# ============================================================================
# Edge Case Tests: Condition Matching
# ============================================================================

def test_condition_exact_match_case_insensitive(engine, insert_trial):
    """Test exact condition matching is case-insensitive"""
    trial = {
        'id': 'NCT00000013',
        'title': 'Condition Case Trial',
        'condition': 'Type 2 Diabetes',
        'min_age': None,
        'max_age': None,
        'gender_criteria': 'All',
        'location': 'New York, NY',
        'inclusion_text': 'Diabetes patients',
        'exclusion_text': 'None'
    }
    insert_trial(trial)
    
    # Should match regardless of case
    for condition_variant in ['Type 2 Diabetes', 'type 2 diabetes', 'TYPE 2 DIABETES']:
        results = engine.filter_by_condition(condition_variant, fuzzy=False)
        trial_ids = [t['id'] for t in results]
        assert trial['id'] in trial_ids, \
            f"Condition matching should be case-insensitive for {condition_variant}"


def test_condition_fuzzy_match(engine, insert_trial):
    """Test fuzzy condition matching"""
    trial = {
        'id': 'NCT00000014',
        'title': 'Fuzzy Condition Trial',
        'condition': 'Non-Small Cell Lung Cancer',
        'min_age': None,
        'max_age': None,
        'gender_criteria': 'All',
        'location': 'New York, NY',
        'inclusion_text': 'Lung cancer patients',
        'exclusion_text': 'None'
    }
    insert_trial(trial)
    
    # Fuzzy match should find partial matches
    results = engine.filter_by_condition('Lung Cancer', fuzzy=True)
    trial_ids = [t['id'] for t in results]
    assert trial['id'] in trial_ids, "Fuzzy match should find 'Lung Cancer' in condition"
    
    # Exact match should NOT find it
    results = engine.filter_by_condition('Lung Cancer', fuzzy=False)
    trial_ids = [t['id'] for t in results]
    assert trial['id'] not in trial_ids, "Exact match should not find partial condition"


# ============================================================================
# Edge Case Tests: Distance Calculation
# ============================================================================

def test_distance_calculation_same_location(engine):
    """Test distance calculation for same location"""
    distance = engine.calculate_distance(40.7128, -74.0060, 40.7128, -74.0060)
    assert distance == 0.0, "Distance to same location should be 0"


def test_distance_calculation_symmetry(engine):
    """Test that distance calculation is symmetric"""
    # New York to Los Angeles
    dist1 = engine.calculate_distance(40.7128, -74.0060, 34.0522, -118.2437)
    # Los Angeles to New York
    dist2 = engine.calculate_distance(34.0522, -118.2437, 40.7128, -74.0060)
    
    assert abs(dist1 - dist2) < 0.01, "Distance should be symmetric"


def test_distance_calculation_positive(engine):
    """Test that distance is always positive for different locations"""
    # New York to Boston
    distance = engine.calculate_distance(40.7128, -74.0060, 42.3601, -71.0589)
    assert distance > 0, "Distance between different locations should be positive"
    assert distance < 300, "Distance NY to Boston should be reasonable (~215 miles)"


def test_distance_calculation_known_distance(engine):
    """Test distance calculation against known distance"""
    # New York (40.7128, -74.0060) to Philadelphia (39.9526, -75.1652)
    # Known distance: approximately 95 miles
    distance = engine.calculate_distance(40.7128, -74.0060, 39.9526, -75.1652)
    assert 90 < distance < 100, f"NY to Philadelphia should be ~95 miles, got {distance}"
