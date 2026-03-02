"""
Match Scoring Algorithm

This module implements the match scoring algorithm that combines hard filter results
with AI soft matching scores to produce ranked trial recommendations with visual
explanations.

Key Features:
- Combines hard filter results with AI soft matching scores
- Converts match scores (0-1) to percentages (0-100%)
- Generates visual explanations with checkmarks (✅) and warnings (⚠️)
- Ranks trials by match score (highest first)
- Returns top 3-5 matches only
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from .medical_matcher import MedicalMatcher, MedicalMatcherError

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class MatchScorerError(Exception):
    """Custom exception for match scorer errors"""
    pass


@dataclass
class PatientProfile:
    """Patient profile data structure"""
    condition: str
    age: int
    gender: str
    location: str
    distance_miles: int
    medical_history: str


@dataclass
class Trial:
    """Trial data structure"""
    id: str
    title: str
    condition: str
    min_age: Optional[int]
    max_age: Optional[int]
    gender_criteria: Optional[str]
    location: str
    inclusion_text: str
    exclusion_text: Optional[str]


@dataclass
class MatchResult:
    """Match result data structure"""
    trial_id: str
    title: str
    match_score: float  # 0-100 percentage
    match_percentage: str  # Formatted string like "92%"
    explanation: str
    key_criteria: List[str]  # Visual explanations with ✅ and ⚠️
    location: str
    distance_miles: Optional[float]


class MatchScorer:
    """
    Match scoring algorithm that combines hard filters with AI soft matching.
    
    This class:
    - Takes trials that passed hard filters
    - Uses MedicalMatcher to score each trial against patient profile
    - Converts scores to percentages
    - Generates visual explanations
    - Ranks and returns top 3-5 matches
    """
    
    # Score thresholds for match quality
    EXCELLENT_THRESHOLD = 0.9  # >90% = excellent match
    GOOD_THRESHOLD = 0.7       # 70-90% = good match
    MODERATE_THRESHOLD = 0.4   # 40-70% = moderate match
    # <40% = poor match
    
    # Result limits
    MIN_RESULTS = 3
    MAX_RESULTS = 5
    
    def __init__(self, medical_matcher: Optional[MedicalMatcher] = None):
        """
        Initialize MatchScorer with MedicalMatcher.
        
        Args:
            medical_matcher: Optional MedicalMatcher instance (creates new if None)
        
        Raises:
            MatchScorerError: If initialization fails
        """
        try:
            self.medical_matcher = medical_matcher or MedicalMatcher()
            logger.info("MatchScorer initialized successfully")
        except MedicalMatcherError as e:
            logger.error(f"Failed to initialize MatchScorer: {str(e)}")
            raise MatchScorerError(f"MatchScorer initialization failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error initializing MatchScorer: {str(e)}")
            raise MatchScorerError(f"Unexpected initialization error: {str(e)}")
    
    def score_and_rank_trials(
        self,
        patient_profile: PatientProfile,
        hard_filtered_trials: List[Trial]
    ) -> List[MatchResult]:
        """
        Score and rank trials, returning top 3-5 matches.
        
        This method:
        1. Validates inputs
        2. Scores each trial using MedicalMatcher
        3. Converts scores to percentages
        4. Generates visual explanations
        5. Ranks by score (highest first)
        6. Returns top 3-5 matches
        
        Args:
            patient_profile: Patient profile data
            hard_filtered_trials: List of trials that passed hard filters
        
        Returns:
            List of MatchResult objects (top 3-5 matches, ranked by score)
        
        Raises:
            MatchScorerError: If scoring fails or input is invalid
        """
        try:
            # Validate inputs
            self._validate_inputs(patient_profile, hard_filtered_trials)
            
            if not hard_filtered_trials:
                logger.info("No trials to score (empty list)")
                return []
            
            logger.info(f"Scoring {len(hard_filtered_trials)} trials")
            
            # Score each trial
            scored_trials = []
            for trial in hard_filtered_trials:
                try:
                    match_result = self._score_single_trial(patient_profile, trial)
                    scored_trials.append(match_result)
                except Exception as e:
                    logger.warning(f"Failed to score trial {trial.id}: {str(e)}")
                    # Continue with other trials
                    continue
            
            if not scored_trials:
                logger.warning("No trials were successfully scored")
                return []
            
            # Sort by match score (highest first)
            scored_trials.sort(key=lambda x: x.match_score, reverse=True)
            
            # Return top 3-5 matches
            top_matches = scored_trials[:self.MAX_RESULTS]
            
            # Ensure we return at least MIN_RESULTS if available
            if len(top_matches) < self.MIN_RESULTS and len(scored_trials) >= self.MIN_RESULTS:
                top_matches = scored_trials[:self.MIN_RESULTS]
            
            logger.info(f"Returning {len(top_matches)} top matches")
            return top_matches
            
        except MatchScorerError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during scoring: {str(e)}")
            raise MatchScorerError(f"Unexpected scoring error: {str(e)}")
    
    def _validate_inputs(
        self,
        patient_profile: PatientProfile,
        hard_filtered_trials: List[Trial]
    ) -> None:
        """
        Validate input parameters.
        
        Args:
            patient_profile: Patient profile data
            hard_filtered_trials: List of trials
        
        Raises:
            MatchScorerError: If inputs are invalid
        """
        if not isinstance(patient_profile, PatientProfile):
            raise MatchScorerError("patient_profile must be a PatientProfile instance")
        
        if not isinstance(hard_filtered_trials, list):
            raise MatchScorerError("hard_filtered_trials must be a list")
        
        # Validate patient profile fields
        if not patient_profile.medical_history or not patient_profile.medical_history.strip():
            raise MatchScorerError("patient_profile.medical_history cannot be empty")
        
        if not patient_profile.condition or not patient_profile.condition.strip():
            raise MatchScorerError("patient_profile.condition cannot be empty")
    
    def _score_single_trial(
        self,
        patient_profile: PatientProfile,
        trial: Trial
    ) -> MatchResult:
        """
        Score a single trial against patient profile.
        
        Args:
            patient_profile: Patient profile data
            trial: Trial to score
        
        Returns:
            MatchResult with score and visual explanations
        
        Raises:
            MatchScorerError: If scoring fails
        """
        try:
            # Use MedicalMatcher to get AI score
            match_data = self.medical_matcher.match_patient_to_trial(
                patient_medical_history=patient_profile.medical_history,
                trial_inclusion_criteria=trial.inclusion_text,
                trial_exclusion_criteria=trial.exclusion_text
            )
            
            # Convert score (0-1) to percentage (0-100)
            match_score_percentage = match_data['match_score'] * 100
            
            # Generate visual explanations
            key_criteria = self._generate_visual_explanations(
                patient_profile=patient_profile,
                trial=trial,
                match_data=match_data
            )
            
            # Create match result
            return MatchResult(
                trial_id=trial.id,
                title=trial.title,
                match_score=match_score_percentage,
                match_percentage=f"{int(match_score_percentage)}%",
                explanation=match_data['explanation'],
                key_criteria=key_criteria,
                location=trial.location,
                distance_miles=None  # Distance calculation not implemented yet
            )
            
        except MedicalMatcherError as e:
            logger.error(f"MedicalMatcher error for trial {trial.id}: {str(e)}")
            raise MatchScorerError(f"Failed to score trial {trial.id}: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error scoring trial {trial.id}: {str(e)}")
            raise MatchScorerError(f"Unexpected error scoring trial {trial.id}: {str(e)}")
    
    def _generate_visual_explanations(
        self,
        patient_profile: PatientProfile,
        trial: Trial,
        match_data: Dict[str, Any]
    ) -> List[str]:
        """
        Generate visual explanations with checkmarks and warnings.
        
        Args:
            patient_profile: Patient profile data
            trial: Trial being scored
            match_data: Match data from MedicalMatcher
        
        Returns:
            List of visual explanation strings with ✅ and ⚠️ symbols
        """
        explanations = []
        
        # Age criteria explanation
        age_explanation = self._generate_age_explanation(patient_profile, trial)
        if age_explanation:
            explanations.append(age_explanation)
        
        # Gender criteria explanation
        gender_explanation = self._generate_gender_explanation(patient_profile, trial)
        if gender_explanation:
            explanations.append(gender_explanation)
        
        # Location criteria explanation
        location_explanation = self._generate_location_explanation(patient_profile, trial)
        if location_explanation:
            explanations.append(location_explanation)
        
        # Inclusion criteria explanation
        if match_data['inclusion_match']:
            explanations.append(
                f"✅ Inclusion criteria: Patient profile matches trial requirements"
            )
        else:
            explanations.append(
                f"⚠️ Inclusion criteria: Partial match with trial requirements"
            )
        
        # Exclusion criteria explanation
        if match_data['exclusion_match']:
            explanations.append(
                f"⚠️ Exclusion concern: Patient may meet some exclusion criteria"
            )
        elif match_data.get('exclusion_penalty_applied'):
            explanations.append(
                f"⚠️ Exclusion violation: Patient meets exclusion criteria"
            )
        else:
            explanations.append(
                f"✅ Exclusion criteria: No exclusion concerns identified"
            )
        
        # Overall match quality explanation
        match_score = match_data['match_score']
        quality_explanation = self._generate_quality_explanation(match_score)
        if quality_explanation:
            explanations.append(quality_explanation)
        
        return explanations
    
    def _generate_age_explanation(
        self,
        patient_profile: PatientProfile,
        trial: Trial
    ) -> Optional[str]:
        """Generate age criteria explanation"""
        if trial.min_age is not None and trial.max_age is not None:
            if trial.min_age <= patient_profile.age <= trial.max_age:
                return f"✅ Age requirement: {trial.min_age}-{trial.max_age} (patient: {patient_profile.age})"
            else:
                return f"⚠️ Age requirement: {trial.min_age}-{trial.max_age} (patient: {patient_profile.age})"
        elif trial.min_age is not None:
            if patient_profile.age >= trial.min_age:
                return f"✅ Age requirement: {trial.min_age}+ (patient: {patient_profile.age})"
            else:
                return f"⚠️ Age requirement: {trial.min_age}+ (patient: {patient_profile.age})"
        elif trial.max_age is not None:
            if patient_profile.age <= trial.max_age:
                return f"✅ Age requirement: up to {trial.max_age} (patient: {patient_profile.age})"
            else:
                return f"⚠️ Age requirement: up to {trial.max_age} (patient: {patient_profile.age})"
        return None
    
    def _generate_gender_explanation(
        self,
        patient_profile: PatientProfile,
        trial: Trial
    ) -> Optional[str]:
        """Generate gender criteria explanation"""
        if trial.gender_criteria and trial.gender_criteria.lower() not in ['all', 'both', 'any']:
            if trial.gender_criteria.lower() == patient_profile.gender.lower():
                return f"✅ Gender requirement: {trial.gender_criteria} (patient: {patient_profile.gender})"
            else:
                return f"⚠️ Gender requirement: {trial.gender_criteria} (patient: {patient_profile.gender})"
        return None
    
    def _generate_location_explanation(
        self,
        patient_profile: PatientProfile,
        trial: Trial
    ) -> Optional[str]:
        """Generate location criteria explanation"""
        if trial.location:
            # Simple location match (distance calculation not implemented)
            return f"✅ Location: {trial.location}"
        return None
    
    def _generate_quality_explanation(self, match_score: float) -> Optional[str]:
        """Generate overall match quality explanation"""
        if match_score >= self.EXCELLENT_THRESHOLD:
            return "✅ Excellent match: Strong alignment with trial criteria"
        elif match_score >= self.GOOD_THRESHOLD:
            return "✅ Good match: Solid alignment with trial criteria"
        elif match_score >= self.MODERATE_THRESHOLD:
            return "⚠️ Moderate match: Some alignment with trial criteria"
        else:
            return "⚠️ Poor match: Limited alignment with trial criteria"
    
    def get_match_quality_label(self, match_score: float) -> str:
        """
        Get human-readable match quality label.
        
        Args:
            match_score: Match score (0-1)
        
        Returns:
            Quality label string
        """
        if match_score >= self.EXCELLENT_THRESHOLD:
            return "Excellent"
        elif match_score >= self.GOOD_THRESHOLD:
            return "Good"
        elif match_score >= self.MODERATE_THRESHOLD:
            return "Moderate"
        else:
            return "Poor"
