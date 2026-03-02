"""
Property-Based Tests for Hard Filter Engine
Tests hard filter accuracy using Hypothesis
Requirements: 2.1, 2.2
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from hypothesis import HealthCheck
from typing import Dict, Any, List
import os
import psycopg2
from psycopg2 import extras

# Import the hard filter engine
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from hard_filter.filter_engine import HardFilterEngine, PatientProfile


# Database connection parameters (from environment or defaults for testing)
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_NAME = os.getenv('DB_NAME', 'vitalmatch_test')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')
DB_PORT = int(os.getenv('DB_PORT', '5432'))


# ============================================================================
# Test Data Generators (Strategies)
# ============================================================================

@st.composite
def patient_profile_strategy(draw):
    """Generate random patient profiles for testing"""
    conditions = [
        'Diabetes', 'Lung Cancer', 'Breast Cancer', 'Heart Disease',
        'Hypertension', 'Asthma', 'COPD', 'Alzheimer Disease'
    ]
    
    genders = ['Male', 'Female', 'Other']
    
    locations = [
        'New York, NY', 'Los Angeles, CA', 'Chicago, IL',
        'Houston, TX', 'Boston, MA', 'Seattle, WA'
    ]
    
    return PatientProfile(
        condition=draw(st.sampled_from(conditions)),
        age=draw(st.integers(min_value=18, max_value=90)),
        gender=draw(st.sampled_from(genders)),
        location=draw(st.sampled_from(locations)),
        distance_miles=draw(st.integers(min_value=10, max_value=100))
    )


@st.composite
def trial_data_strategy(draw):
    """Generate random trial data for testing"""
    conditions = [
        'Diabetes', 'Lung Cancer', 'Breast Cancer', 'Heart Disease',
        'Hypertension', 'Asthma', 'COPD', 'Alzheimer Disease'
    ]
    
    genders = ['Male', 'Female', 'All', None]
    
    locations = [
        'Memorial Sloan Kettering, New York, NY',
        'UCLA Medical Center, Los Angeles, CA',
        'Mayo Clinic, Rochester, MN',
        'Johns Hopkins, Baltimore, MD'
    ]
    
    # Generate age range
    min_age = draw(st.one_of(st.none(), st.integers(min_value=18, max_value=65)))
    if min_age is not None:
        max_age = draw(st.one_of(st.none(), st.integers(min_value=min_age, max_value=90)))
    else:
        max_age = draw(st.one_of(st.none(), st.integers(min_value=18, max_value=90)))
    
    return {
        'id': f'NCT{draw(st.integers(min_value=10000000, max_value=99999999))}',
        'title': f'Study of {draw(st.sampled_from(conditions))}',
        'condition': draw(st.sampled_from(conditions)),
        'min_age': min_age,
        'max_age': max_age,
        'gender_criteria': draw(st.sampled_from(genders)),
        'location': draw(st.sampled_from(locations)),
        'inclusion_text': 'Patients with confirmed diagnosis',
        'exclusion_text': 'Pregnant women excluded'
    }


# ============================================================================
# Helper Functions
# ============================================================================

def create_test_engine():
    """Create a hard filter engine for testing"""
    return HardFilterEngine(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT
    )


def insert_test_trials(trials: List[Dict[str, Any]]):
    """Insert test trials into database"""
    engine = create_test_engine()
    
    with engine.get_connection() as conn:
        with conn.cursor() as cursor:
            for trial in trials:
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


def cleanup_test_trials(trial_ids: List[str]):
    """Remove test trials from database"""
    engine = create_test_engine()
    
    with engine.get_connection() as conn:
        with conn.cursor() as cursor:
            for trial_id in trial_ids:
                cursor.execute("DELETE FROM trials WHERE id = %s", (trial_id,))
        conn.commit()


# ============================================================================
# Property Tests
# ============================================================================

@pytest.mark.property
@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture]
)
@given(
    patient=patient_profile_strategy(),
    trials=st.lists(trial_data_strategy(), min_size=5, max_size=20)
)
def test_hard_filter_accuracy_property(patient, trials):
    """
    Property 1: Hard Filter Accuracy
    Validates: Requirements 2.1, 2.2
    
    Property: All returned trials MUST meet ALL hard criteria:
    - Age: min_age <= patient_age <= max_age (or NULL)
    - Gender: gender_criteria matches patient gender or is 'All' or NULL
    - Condition: exact match (case-insensitive)
    - Location: contains patient location text
    """
    # Setup: Insert test trials
    trial_ids = [trial['id'] for trial in trials]
    insert_test_trials(trials)
    
    try:
        # Execute: Run hard filter
        engine = create_test_engine()
        result = engine.filter_trials(patient)
        
        # Verify: All returned trials meet hard criteria
        for trial in result.trials:
            # Age criteria check
            if trial['min_age'] is not None:
                assert trial['min_age'] <= patient.age, \
                    f"Trial {trial['id']} min_age {trial['min_age']} > patient age {patient.age}"
            
            if trial['max_age'] is not None:
                assert trial['max_age'] >= patient.age, \
                    f"Trial {trial['id']} max_age {trial['max_age']} < patient age {patient.age}"
            
            # Gender criteria check
            if trial['gender_criteria'] is not None and trial['gender_criteria'] != 'All':
                assert trial['gender_criteria'].lower() == patient.gender.lower(), \
                    f"Trial {trial['id']} gender {trial['gender_criteria']} != patient gender {patient.gender}"
            
            # Condition criteria check
            assert trial['condition'].lower() == patient.condition.lower(), \
                f"Trial {trial['id']} condition {trial['condition']} != patient condition {patient.condition}"
            
            # Location criteria check (if location filter was applied)
            if 'location' in result.filters_applied or 'location_text' in result.filters_applied:
                assert trial['location'] is not None, \
                    f"Trial {trial['id']} has NULL location but location filter was applied"
    
    finally:
        # Cleanup: Remove test trials
        cleanup_test_trials(trial_ids)


@pytest.mark.property
@settings(
    max_examples=30,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow]
)
@given(
    age=st.integers(min_value=18, max_value=90),
    min_age=st.one_of(st.none(), st.integers(min_value=18, max_value=65)),
    max_age=st.one_of(st.none(), st.integers(min_value=30, max_value=90))
)
def test_age_boundary_conditions(age, min_age, max_age):
    """
    Property: Age boundary conditions
    Tests edge cases for age filtering
    """
    # Skip invalid age ranges
    if min_age is not None and max_age is not None and min_age > max_age:
        assume(False)
    
    # Create test trial
    trial = {
        'id': f'NCT{age}{min_age or 0}{max_age or 0}',
        'title': 'Age Boundary Test',
        'condition': 'Test Condition',
        'min_age': min_age,
        'max_age': max_age,
        'gender_criteria': 'All',
        'location': 'Test Location, NY',
        'inclusion_text': 'Test inclusion',
        'exclusion_text': 'Test exclusion'
    }
    
    insert_test_trials([trial])
    
    try:
        engine = create_test_engine()
        
        # Test if trial should match
        should_match = True
        if min_age is not None and age < min_age:
            should_match = False
        if max_age is not None and age > max_age:
            should_match = False
        
        # Filter by age
        results = engine.filter_by_age(age)
        trial_ids = [t['id'] for t in results]
        
        if should_match:
            assert trial['id'] in trial_ids, \
                f"Trial with min_age={min_age}, max_age={max_age} should match age={age}"
        else:
            assert trial['id'] not in trial_ids, \
                f"Trial with min_age={min_age}, max_age={max_age} should NOT match age={age}"
    
    finally:
        cleanup_test_trials([trial['id']])


@pytest.mark.property
@settings(
    max_examples=20,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow]
)
@given(
    patient_gender=st.sampled_from(['Male', 'Female', 'Other']),
    trial_gender=st.sampled_from(['Male', 'Female', 'All', None])
)
def test_gender_filtering_property(patient_gender, trial_gender):
    """
    Property: Gender filtering
    Tests all gender combinations
    """
    trial = {
        'id': f'NCT{hash((patient_gender, trial_gender)) % 100000000}',
        'title': 'Gender Test',
        'condition': 'Test Condition',
        'min_age': None,
        'max_age': None,
        'gender_criteria': trial_gender,
        'location': 'Test Location, NY',
        'inclusion_text': 'Test inclusion',
        'exclusion_text': 'Test exclusion'
    }
    
    insert_test_trials([trial])
    
    try:
        engine = create_test_engine()
        results = engine.filter_by_gender(patient_gender)
        trial_ids = [t['id'] for t in results]
        
        # Determine if trial should match
        should_match = (
            trial_gender is None or
            trial_gender == 'All' or
            trial_gender.lower() == patient_gender.lower()
        )
        
        if should_match:
            assert trial['id'] in trial_ids, \
                f"Trial with gender={trial_gender} should match patient gender={patient_gender}"
        else:
            assert trial['id'] not in trial_ids, \
                f"Trial with gender={trial_gender} should NOT match patient gender={patient_gender}"
    
    finally:
        cleanup_test_trials([trial['id']])


@pytest.mark.property
@settings(max_examples=20, deadline=None)
@given(
    location=st.sampled_from(['New York', 'Los Angeles', 'Chicago', 'Boston'])
)
def test_location_distance_calculation(location):
    """
    Property: Location distance calculations
    Tests Haversine distance formula
    """
    engine = create_test_engine()
    
    # Test coordinates (approximate)
    coords = {
        'New York': (40.7128, -74.0060),
        'Los Angeles': (34.0522, -118.2437),
        'Chicago': (41.8781, -87.6298),
        'Boston': (42.3601, -71.0589)
    }
    
    lat1, lon1 = coords[location]
    
    # Calculate distance to itself (should be 0)
    distance = engine.calculate_distance(lat1, lon1, lat1, lon1)
    assert distance == 0.0, "Distance to same location should be 0"
    
    # Calculate distance to other locations (should be positive)
    for other_location, (lat2, lon2) in coords.items():
        if other_location != location:
            distance = engine.calculate_distance(lat1, lon1, lat2, lon2)
            assert distance > 0, f"Distance from {location} to {other_location} should be positive"
            
            # Distance should be symmetric
            reverse_distance = engine.calculate_distance(lat2, lon2, lat1, lon1)
            assert abs(distance - reverse_distance) < 0.01, \
                "Distance calculation should be symmetric"