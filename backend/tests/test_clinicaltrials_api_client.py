"""
Integration tests for ClinicalTrials.gov API Client
Requirements: TR5
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import requests
from datetime import datetime, timedelta

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data_ingestion.clinicaltrials_api_client import ClinicalTrialsAPIClient


class TestClinicalTrialsAPIClient(unittest.TestCase):
    """Test cases for ClinicalTrials.gov API client"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = ClinicalTrialsAPIClient(timeout=10)
    
    def tearDown(self):
        """Clean up after tests"""
        self.client.close()
    
    @patch('data_ingestion.clinicaltrials_api_client.requests.Session.get')
    def test_fetch_trials_with_mock_response(self, mock_get):
        """Test fetching trials with mocked API response"""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'studies': [
                {
                    'protocolSection': {
                        'identificationModule': {
                            'nctId': 'NCT12345678',
                            'officialTitle': 'Test Trial 1'
                        }
                    }
                },
                {
                    'protocolSection': {
                        'identificationModule': {
                            'nctId': 'NCT87654321',
                            'officialTitle': 'Test Trial 2'
                        }
                    }
                }
            ],
            'nextPageToken': None
        }
        mock_get.return_value = mock_response
        
        # Fetch trials
        trials = self.client.fetch_trials(max_pages=1)
        
        # Assertions
        self.assertEqual(len(trials), 2)
        self.assertEqual(trials[0]['protocolSection']['identificationModule']['nctId'], 'NCT12345678')
        self.assertEqual(trials[1]['protocolSection']['identificationModule']['nctId'], 'NCT87654321')
        
        # Verify API was called
        mock_get.assert_called_once()
    
    @patch('data_ingestion.clinicaltrials_api_client.requests.Session.get')
    def test_fetch_trials_with_pagination(self, mock_get):
        """Test pagination handling"""
        # Mock first page
        mock_response_1 = Mock()
        mock_response_1.status_code = 200
        mock_response_1.json.return_value = {
            'studies': [{'protocolSection': {'identificationModule': {'nctId': 'NCT00001'}}}],
            'nextPageToken': 'page2'
        }
        
        # Mock second page
        mock_response_2 = Mock()
        mock_response_2.status_code = 200
        mock_response_2.json.return_value = {
            'studies': [{'protocolSection': {'identificationModule': {'nctId': 'NCT00002'}}}],
            'nextPageToken': None
        }
        
        mock_get.side_effect = [mock_response_1, mock_response_2]
        
        # Fetch trials
        trials = self.client.fetch_trials()
        
        # Assertions
        self.assertEqual(len(trials), 2)
        self.assertEqual(mock_get.call_count, 2)
    
    @patch('data_ingestion.clinicaltrials_api_client.requests.Session.get')
    def test_retry_on_timeout(self, mock_get):
        """Test retry logic on timeout"""
        # Mock timeout on first attempt, success on second
        mock_get.side_effect = [
            requests.exceptions.Timeout("Connection timeout"),
            Mock(status_code=200, json=lambda: {'studies': [], 'nextPageToken': None})
        ]
        
        # Fetch trials (should retry and succeed)
        trials = self.client.fetch_trials()
        
        # Assertions
        self.assertEqual(len(trials), 0)
        self.assertEqual(mock_get.call_count, 2)
    
    @patch('data_ingestion.clinicaltrials_api_client.requests.Session.get')
    def test_retry_on_http_error(self, mock_get):
        """Test retry logic on HTTP 500 error"""
        # Mock 500 error on first attempt, success on second
        error_response = Mock()
        error_response.status_code = 500
        error_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Server error", response=error_response)
        
        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {'studies': [], 'nextPageToken': None}
        
        mock_get.side_effect = [error_response, success_response]
        
        # Fetch trials (should retry and succeed)
        trials = self.client.fetch_trials()
        
        # Assertions
        self.assertEqual(len(trials), 0)
        self.assertEqual(mock_get.call_count, 2)
    
    @patch('data_ingestion.clinicaltrials_api_client.requests.Session.get')
    def test_no_retry_on_client_error(self, mock_get):
        """Test that client errors (4xx) are not retried"""
        # Mock 404 error
        error_response = Mock()
        error_response.status_code = 404
        error_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Not found", response=error_response)
        
        mock_get.return_value = error_response
        
        # Fetch trials (should raise exception without retry)
        with self.assertRaises(requests.exceptions.HTTPError):
            self.client.fetch_trials()
        
        # Should only be called once (no retry)
        self.assertEqual(mock_get.call_count, 1)
    
    @patch('data_ingestion.clinicaltrials_api_client.requests.Session.get')
    def test_max_retries_exceeded(self, mock_get):
        """Test that max retries are respected"""
        # Mock timeout on all attempts
        mock_get.side_effect = requests.exceptions.Timeout("Connection timeout")
        
        # Fetch trials (should fail after max retries)
        with self.assertRaises(requests.RequestException):
            self.client.fetch_trials()
        
        # Should be called MAX_RETRIES times
        self.assertEqual(mock_get.call_count, ClinicalTrialsAPIClient.MAX_RETRIES)
    
    def test_build_query_params_with_date(self):
        """Test query parameter building with date filter"""
        updated_since = datetime(2024, 1, 1)
        params = self.client._build_query_params(None, 1000, updated_since)
        
        self.assertEqual(params['format'], 'json')
        self.assertEqual(params['pageSize'], 1000)
        self.assertIn('AREA[LastUpdatePostDate]RANGE[2024-01-01,MAX]', params['query.term'])
    
    def test_build_query_params_with_query(self):
        """Test query parameter building with search query"""
        params = self.client._build_query_params('diabetes', 1000, None)
        
        self.assertEqual(params['format'], 'json')
        self.assertEqual(params['pageSize'], 1000)
        self.assertEqual(params['query.term'], 'diabetes')
    
    def test_fetch_recent_trials(self):
        """Test fetch_recent_trials helper method"""
        with patch.object(self.client, 'fetch_trials') as mock_fetch:
            mock_fetch.return_value = []
            
            self.client.fetch_recent_trials(days=7)
            
            # Verify fetch_trials was called with updated_since parameter
            mock_fetch.assert_called_once()
            call_args = mock_fetch.call_args
            self.assertIn('updated_since', call_args[1])
    
    def test_fetch_trials_by_condition(self):
        """Test fetch_trials_by_condition helper method"""
        with patch.object(self.client, 'fetch_trials') as mock_fetch:
            mock_fetch.return_value = []
            
            self.client.fetch_trials_by_condition('Diabetes', max_trials=500)
            
            # Verify fetch_trials was called with correct query
            mock_fetch.assert_called_once()
            call_args = mock_fetch.call_args
            self.assertIn('query', call_args[1])
            self.assertIn('Diabetes', call_args[1]['query'])


if __name__ == '__main__':
    unittest.main()
