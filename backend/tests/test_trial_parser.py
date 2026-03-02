"""
Integration tests for Trial Parser
Requirements: TR5
"""

import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data_ingestion.trial_parser import TrialParser


class TestTrialParser(unittest.TestCase):
    """Test cases for trial data parser"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.parser = TrialParser()
        
        # Sample API response data
        self.sample_study = {
            'protocolSection': {
                'identificationModule': {
                    'nctId': 'NCT12345678',
                    'officialTitle': 'Phase II Study of Drug X in NSCLC Patients',
                    'briefTitle': 'Drug X for Lung Cancer'
                },
                'conditionsModule': {
                    'conditions': ['Non-Small Cell Lung Cancer', 'NSCLC']
                },
                'eligibilityModule': {
                    'minimumAge': '18 Years',
                    'maximumAge': '75 Years',
                    'sex': 'ALL',
                    'eligibilityCriteria': '''
                        Inclusion Criteria:
                        - Diagnosed with NSCLC
                        - Age 18-75 years
                        - History of smoking
                        
                        Exclusion Criteria:
                        - Active infection
                        - Pregnant or nursing
                    '''
                },
                'contactsLocationsModule': {
                    'locations': [
                        {
                            'city': 'New York',
                            'state': 'New York',
                            'country': 'United States'
                        },
                        {
                            'city': 'Boston',
                            'state': 'Massachusetts',
                            'country': 'United States'
                        }
                    ]
                }
            }
        }
    
    def test_parse_complete_trial(self):
        """Test parsing a complete trial with all fields"""
        trial = self.parser.parse_trial(self.sample_study)
        
        self.assertIsNotNone(trial)
        self.assertEqual(trial['id'], 'NCT12345678')
        self.assertEqual(trial['title'], 'Phase II Study of Drug X in NSCLC Patients')
        self.assertIn('Non-Small Cell Lung Cancer', trial['condition'])
        self.assertEqual(trial['min_age'], 18)
        self.assertEqual(trial['max_age'], 75)
        self.assertEqual(trial['gender_criteria'], 'All')
        self.assertIn('New York', trial['location'])
        self.assertIn('smoking', trial['inclusion_text'])
        self.assertIn('infection', trial['exclusion_text'])
    
    def test_parse_trial_missing_nct_id(self):
        """Test that trials without NCT ID are skipped"""
        study = {'protocolSection': {'identificationModule': {}}}
        trial = self.parser.parse_trial(study)
        
        self.assertIsNone(trial)
    
    def test_parse_trial_missing_title(self):
        """Test that trials without title are skipped"""
        study = {
            'protocolSection': {
                'identificationModule': {'nctId': 'NCT12345678'},
                'conditionsModule': {'conditions': ['Test']}
            }
        }
        trial = self.parser.parse_trial(study)
        
        self.assertIsNone(trial)
    
    def test_parse_trial_missing_condition(self):
        """Test that trials without condition are skipped"""
        study = {
            'protocolSection': {
                'identificationModule': {
                    'nctId': 'NCT12345678',
                    'officialTitle': 'Test Trial'
                }
            }
        }
        trial = self.parser.parse_trial(study)
        
        self.assertIsNone(trial)
    
    def test_parse_age_years(self):
        """Test parsing age in years"""
        self.assertEqual(self.parser._parse_age('18 Years'), 18)
        self.assertEqual(self.parser._parse_age('65 Years'), 65)
        self.assertEqual(self.parser._parse_age('100 Years'), 100)
    
    def test_parse_age_months(self):
        """Test parsing age in months"""
        self.assertEqual(self.parser._parse_age('6 Months'), 0)  # 6 months = 0 years
        self.assertEqual(self.parser._parse_age('24 Months'), 2)  # 24 months = 2 years
        self.assertEqual(self.parser._parse_age('36 Months'), 3)  # 36 months = 3 years
    
    def test_parse_age_invalid(self):
        """Test parsing invalid age strings"""
        self.assertIsNone(self.parser._parse_age('N/A'))
        self.assertIsNone(self.parser._parse_age(''))
        self.assertIsNone(self.parser._parse_age(None))
        self.assertIsNone(self.parser._parse_age('Invalid'))
    
    def test_extract_gender_mapping(self):
        """Test gender criteria mapping"""
        protocol = {'eligibilityModule': {'sex': 'MALE'}}
        self.assertEqual(self.parser._extract_gender(protocol), 'Male')
        
        protocol = {'eligibilityModule': {'sex': 'FEMALE'}}
        self.assertEqual(self.parser._extract_gender(protocol), 'Female')
        
        protocol = {'eligibilityModule': {'sex': 'ALL'}}
        self.assertEqual(self.parser._extract_gender(protocol), 'All')
        
        protocol = {'eligibilityModule': {'sex': 'BOTH'}}
        self.assertEqual(self.parser._extract_gender(protocol), 'All')
    
    def test_extract_locations_multiple(self):
        """Test extracting multiple locations"""
        protocol = {
            'contactsLocationsModule': {
                'locations': [
                    {'city': 'New York', 'state': 'NY', 'country': 'United States'},
                    {'city': 'Boston', 'state': 'MA', 'country': 'United States'},
                    {'city': 'London', 'state': '', 'country': 'United Kingdom'}
                ]
            }
        }
        
        location = self.parser._extract_locations(protocol)
        
        self.assertIsNotNone(location)
        self.assertIn('New York', location)
        self.assertIn('Boston', location)
        self.assertIn('London', location)
        self.assertIn('United Kingdom', location)
    
    def test_extract_locations_missing(self):
        """Test handling missing locations"""
        protocol = {'contactsLocationsModule': {}}
        location = self.parser._extract_locations(protocol)
        
        self.assertIsNone(location)
    
    def test_extract_criteria_sections(self):
        """Test extracting inclusion and exclusion criteria sections"""
        criteria_text = '''
        Inclusion Criteria:
        - Must be 18 years or older
        - Diagnosed with condition
        
        Exclusion Criteria:
        - Pregnant or nursing
        - Active infection
        '''
        
        inclusion = self.parser._extract_criteria_section(criteria_text, 'inclusion')
        exclusion = self.parser._extract_criteria_section(criteria_text, 'exclusion')
        
        self.assertIsNotNone(inclusion)
        self.assertIn('18 years', inclusion)
        self.assertIn('Diagnosed', inclusion)
        
        self.assertIsNotNone(exclusion)
        self.assertIn('Pregnant', exclusion)
        self.assertIn('infection', exclusion)
    
    def test_parse_multiple_trials(self):
        """Test parsing multiple trials"""
        studies = [
            self.sample_study,
            {
                'protocolSection': {
                    'identificationModule': {
                        'nctId': 'NCT87654321',
                        'officialTitle': 'Another Trial'
                    },
                    'conditionsModule': {
                        'conditions': ['Diabetes']
                    }
                }
            },
            {
                'protocolSection': {
                    'identificationModule': {}  # Missing NCT ID - should be skipped
                }
            }
        ]
        
        trials = self.parser.parse_trials(studies)
        
        # Should parse 2 trials (third one is skipped due to missing NCT ID)
        self.assertEqual(len(trials), 2)
        self.assertEqual(trials[0]['id'], 'NCT12345678')
        self.assertEqual(trials[1]['id'], 'NCT87654321')
    
    def test_title_truncation(self):
        """Test that very long titles are truncated"""
        long_title = 'A' * 600  # 600 characters
        study = {
            'protocolSection': {
                'identificationModule': {
                    'nctId': 'NCT12345678',
                    'officialTitle': long_title
                },
                'conditionsModule': {
                    'conditions': ['Test']
                }
            }
        }
        
        trial = self.parser.parse_trial(study)
        
        self.assertIsNotNone(trial)
        self.assertLessEqual(len(trial['title']), 500)
        self.assertTrue(trial['title'].endswith('...'))
    
    def test_fallback_to_brief_title(self):
        """Test fallback to brief title when official title is missing"""
        study = {
            'protocolSection': {
                'identificationModule': {
                    'nctId': 'NCT12345678',
                    'briefTitle': 'Brief Title Only'
                },
                'conditionsModule': {
                    'conditions': ['Test']
                }
            }
        }
        
        trial = self.parser.parse_trial(study)
        
        self.assertIsNotNone(trial)
        self.assertEqual(trial['title'], 'Brief Title Only')


if __name__ == '__main__':
    unittest.main()
