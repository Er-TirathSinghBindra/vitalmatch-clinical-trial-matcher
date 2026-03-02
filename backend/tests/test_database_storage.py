"""
Integration tests for Database Storage Layer
Requirements: TR5

Note: These tests require a test database to be available.
Set environment variables for test database connection:
- TEST_DB_HOST
- TEST_DB_NAME
- TEST_DB_USER
- TEST_DB_PASSWORD
"""

import unittest
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data_ingestion.database_storage import DatabaseStorage


class TestDatabaseStorage(unittest.TestCase):
    """Test cases for database storage layer"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test database connection"""
        # Check if test database credentials are available
        cls.db_host = os.environ.get('TEST_DB_HOST')
        cls.db_name = os.environ.get('TEST_DB_NAME', 'trials_db_test')
        cls.db_user = os.environ.get('TEST_DB_USER', 'postgres')
        cls.db_password = os.environ.get('TEST_DB_PASSWORD')
        
        if not cls.db_host or not cls.db_password:
            raise unittest.SkipTest(
                "Test database credentials not available. "
                "Set TEST_DB_HOST and TEST_DB_PASSWORD environment variables."
            )
        
        cls.storage = DatabaseStorage(
            host=cls.db_host,
            database=cls.db_name,
            user=cls.db_user,
            password=cls.db_password
        )
        
        # Test connection
        if not cls.storage.test_connection():
            raise unittest.SkipTest("Cannot connect to test database")
    
    def setUp(self):
        """Set up test fixtures"""
        # Sample trial data
        self.sample_trial = {
            'id': 'NCT99999999',
            'title': 'Test Trial for Unit Testing',
            'condition': 'Test Condition',
            'min_age': 18,
            'max_age': 65,
            'gender_criteria': 'All',
            'location': 'Test City, Test State',
            'inclusion_text': 'Test inclusion criteria',
            'exclusion_text': 'Test exclusion criteria'
        }
    
    def tearDown(self):
        """Clean up after each test"""
        # Delete test trial if it exists
        try:
            self.storage.delete_trial('NCT99999999')
        except:
            pass
    
    def test_connection(self):
        """Test database connection"""
        result = self.storage.test_connection()
        self.assertTrue(result)
    
    def test_store_single_trial(self):
        """Test storing a single trial"""
        result = self.storage.store_trials([self.sample_trial])
        
        self.assertEqual(result['inserted'], 1)
        self.assertEqual(result['updated'], 0)
        self.assertEqual(result['failed'], 0)
    
    def test_upsert_trial(self):
        """Test upserting (insert then update) a trial"""
        # First insert
        result1 = self.storage.store_trials([self.sample_trial])
        self.assertEqual(result1['inserted'], 1)
        
        # Update the same trial
        updated_trial = self.sample_trial.copy()
        updated_trial['title'] = 'Updated Test Trial'
        
        result2 = self.storage.store_trials([updated_trial])
        self.assertEqual(result2['inserted'], 0)
        self.assertEqual(result2['updated'], 1)
        
        # Verify the update
        retrieved = self.storage.get_trial_by_id('NCT99999999')
        self.assertEqual(retrieved['title'], 'Updated Test Trial')
    
    def test_store_multiple_trials(self):
        """Test storing multiple trials"""
        trials = [
            self.sample_trial,
            {
                'id': 'NCT88888888',
                'title': 'Second Test Trial',
                'condition': 'Test Condition 2',
                'min_age': 20,
                'max_age': 70,
                'gender_criteria': 'Male',
                'location': 'Another City',
                'inclusion_text': 'Inclusion 2',
                'exclusion_text': 'Exclusion 2'
            }
        ]
        
        result = self.storage.store_trials(trials)
        
        self.assertEqual(result['inserted'], 2)
        self.assertEqual(result['failed'], 0)
        
        # Clean up second trial
        self.storage.delete_trial('NCT88888888')
    
    def test_get_trial_by_id(self):
        """Test retrieving a trial by ID"""
        # Store trial first
        self.storage.store_trials([self.sample_trial])
        
        # Retrieve it
        trial = self.storage.get_trial_by_id('NCT99999999')
        
        self.assertIsNotNone(trial)
        self.assertEqual(trial['id'], 'NCT99999999')
        self.assertEqual(trial['title'], 'Test Trial for Unit Testing')
        self.assertEqual(trial['min_age'], 18)
        self.assertEqual(trial['max_age'], 65)
    
    def test_get_nonexistent_trial(self):
        """Test retrieving a trial that doesn't exist"""
        trial = self.storage.get_trial_by_id('NCT00000000')
        self.assertIsNone(trial)
    
    def test_delete_trial(self):
        """Test deleting a trial"""
        # Store trial first
        self.storage.store_trials([self.sample_trial])
        
        # Verify it exists
        trial = self.storage.get_trial_by_id('NCT99999999')
        self.assertIsNotNone(trial)
        
        # Delete it
        deleted = self.storage.delete_trial('NCT99999999')
        self.assertTrue(deleted)
        
        # Verify it's gone
        trial = self.storage.get_trial_by_id('NCT99999999')
        self.assertIsNone(trial)
    
    def test_delete_nonexistent_trial(self):
        """Test deleting a trial that doesn't exist"""
        deleted = self.storage.delete_trial('NCT00000000')
        self.assertFalse(deleted)
    
    def test_batch_processing(self):
        """Test batch processing with large number of trials"""
        # Create 250 test trials (more than batch size of 100)
        trials = []
        for i in range(250):
            trials.append({
                'id': f'NCT{i:08d}',
                'title': f'Test Trial {i}',
                'condition': 'Test Condition',
                'min_age': 18,
                'max_age': 65,
                'gender_criteria': 'All',
                'location': 'Test Location',
                'inclusion_text': 'Test inclusion',
                'exclusion_text': 'Test exclusion'
            })
        
        # Store all trials
        result = self.storage.store_trials(trials)
        
        self.assertEqual(result['inserted'], 250)
        self.assertEqual(result['failed'], 0)
        
        # Clean up
        for i in range(250):
            self.storage.delete_trial(f'NCT{i:08d}')
    
    def test_handle_missing_optional_fields(self):
        """Test storing trial with missing optional fields"""
        minimal_trial = {
            'id': 'NCT99999999',
            'title': 'Minimal Trial',
            'condition': 'Test Condition',
            'min_age': None,
            'max_age': None,
            'gender_criteria': None,
            'location': None,
            'inclusion_text': None,
            'exclusion_text': None
        }
        
        result = self.storage.store_trials([minimal_trial])
        
        self.assertEqual(result['inserted'], 1)
        self.assertEqual(result['failed'], 0)
        
        # Verify it was stored correctly
        trial = self.storage.get_trial_by_id('NCT99999999')
        self.assertIsNotNone(trial)
        self.assertEqual(trial['title'], 'Minimal Trial')
        self.assertIsNone(trial['min_age'])
    
    def test_sql_injection_prevention(self):
        """Test that parameterized queries prevent SQL injection"""
        malicious_trial = {
            'id': 'NCT99999999',
            'title': "'; DROP TABLE trials; --",
            'condition': 'Test Condition',
            'min_age': 18,
            'max_age': 65,
            'gender_criteria': 'All',
            'location': 'Test Location',
            'inclusion_text': 'Test inclusion',
            'exclusion_text': 'Test exclusion'
        }
        
        # This should store safely without executing the SQL injection
        result = self.storage.store_trials([malicious_trial])
        
        self.assertEqual(result['inserted'], 1)
        
        # Verify the malicious string was stored as data, not executed
        trial = self.storage.get_trial_by_id('NCT99999999')
        self.assertIsNotNone(trial)
        self.assertEqual(trial['title'], "'; DROP TABLE trials; --")
        
        # Verify table still exists by getting count
        count = self.storage.get_trial_count()
        self.assertGreaterEqual(count, 1)


if __name__ == '__main__':
    unittest.main()
