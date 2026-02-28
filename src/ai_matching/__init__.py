"""
AI Matching Module for VitalMatch Clinical Trial Matcher

This module provides AI-powered soft filtering using Amazon Bedrock
to match patient medical histories with clinical trial eligibility criteria.
"""

from .bedrock_client import BedrockClient, BedrockError
from .medical_matcher import (
    MedicalMatcher,
    MedicalMatcherError,
    normalize_medical_term,
    get_common_medical_synonyms
)
from .match_scorer import (
    MatchScorer,
    MatchScorerError,
    PatientProfile,
    Trial,
    MatchResult
)

__all__ = [
    'BedrockClient',
    'BedrockError',
    'MedicalMatcher',
    'MedicalMatcherError',
    'normalize_medical_term',
    'get_common_medical_synonyms',
    'MatchScorer',
    'MatchScorerError',
    'PatientProfile',
    'Trial',
    'MatchResult'
]
