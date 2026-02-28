"""
Data Ingestion Module
Handles fetching and processing clinical trial data from ClinicalTrials.gov
"""

from .clinicaltrials_api_client import ClinicalTrialsAPIClient

__all__ = ['ClinicalTrialsAPIClient']
