"""
Database Storage Layer
Handles storing clinical trial data in RDS PostgreSQL via RDS Proxy
Requirements: TR2, TR5, 4.4
"""

import logging
import psycopg2
from psycopg2 import sql, extras
from typing import Dict, List, Optional, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class DatabaseStorage:
    """Storage layer for clinical trial data in PostgreSQL"""
    
    BATCH_SIZE = 100  # Records per batch insert
    
    def __init__(
        self,
        host: str,
        database: str,
        user: str,
        password: str,
        port: int = 5432
    ):
        """
        Initialize database storage
        
        Args:
            host: Database host (RDS Proxy endpoint)
            database: Database name
            user: Database username
            password: Database password
            port: Database port (default: 5432)
        """
        self.connection_params = {
            'host': host,
            'database': database,
            'user': user,
            'password': password,
            'port': port,
            'connect_timeout': 10,
            'sslmode': 'require'  # Require SSL for RDS connections
        }
        self._connection = None
    
    @contextmanager
    def get_connection(self):
        """
        Get database connection with automatic cleanup
        
        Yields:
            psycopg2 connection object
        """
        conn = None
        try:
            conn = psycopg2.connect(**self.connection_params)
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def store_trials(self, trials: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Store trials in database with batch processing
        
        Args:
            trials: List of trial dictionaries
            
        Returns:
            Dictionary with counts: {'inserted': N, 'updated': M, 'failed': K}
        """
        if not trials:
            logger.info("No trials to store")
            return {'inserted': 0, 'updated': 0, 'failed': 0}
        
        logger.info(f"Storing {len(trials)} trials in batches of {self.BATCH_SIZE}")
        
        total_inserted = 0
        total_updated = 0
        total_failed = 0
        
        # Process in batches
        for i in range(0, len(trials), self.BATCH_SIZE):
            batch = trials[i:i + self.BATCH_SIZE]
            batch_num = (i // self.BATCH_SIZE) + 1
            
            try:
                result = self._store_batch(batch)
                total_inserted += result['inserted']
                total_updated += result['updated']
                total_failed += result['failed']
                
                logger.info(
                    f"Batch {batch_num}: "
                    f"inserted={result['inserted']}, "
                    f"updated={result['updated']}, "
                    f"failed={result['failed']}"
                )
            except Exception as e:
                logger.error(f"Failed to store batch {batch_num}: {e}")
                total_failed += len(batch)
        
        logger.info(
            f"Storage complete: "
            f"inserted={total_inserted}, "
            f"updated={total_updated}, "
            f"failed={total_failed}"
        )
        
        return {
            'inserted': total_inserted,
            'updated': total_updated,
            'failed': total_failed
        }
    
    def _store_batch(self, trials: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Store a batch of trials using upsert (INSERT ... ON CONFLICT UPDATE)
        
        Args:
            trials: List of trial dictionaries
            
        Returns:
            Dictionary with counts: {'inserted': N, 'updated': M, 'failed': K}
        """
        inserted = 0
        updated = 0
        failed = 0
        
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                for trial in trials:
                    try:
                        result = self._upsert_trial(cursor, trial)
                        if result == 'inserted':
                            inserted += 1
                        elif result == 'updated':
                            updated += 1
                    except Exception as e:
                        logger.error(f"Failed to store trial {trial.get('id')}: {e}")
                        failed += 1
        
        return {'inserted': inserted, 'updated': updated, 'failed': failed}
    
    def _upsert_trial(self, cursor, trial: Dict[str, Any]) -> str:
        """
        Insert or update a single trial using parameterized query
        
        Args:
            cursor: Database cursor
            trial: Trial dictionary
            
        Returns:
            'inserted' or 'updated'
        """
        # SQL query with parameterized values to prevent SQL injection
        query = sql.SQL("""
            INSERT INTO trials (
                id, title, condition, min_age, max_age, 
                gender_criteria, location, inclusion_text, exclusion_text
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (id) DO UPDATE SET
                title = EXCLUDED.title,
                condition = EXCLUDED.condition,
                min_age = EXCLUDED.min_age,
                max_age = EXCLUDED.max_age,
                gender_criteria = EXCLUDED.gender_criteria,
                location = EXCLUDED.location,
                inclusion_text = EXCLUDED.inclusion_text,
                exclusion_text = EXCLUDED.exclusion_text,
                updated_date = CURRENT_TIMESTAMP
            RETURNING (xmax = 0) AS inserted
        """)
        
        # Execute with parameterized values
        cursor.execute(query, (
            trial.get('id'),
            trial.get('title'),
            trial.get('condition'),
            trial.get('min_age'),
            trial.get('max_age'),
            trial.get('gender_criteria'),
            trial.get('location'),
            trial.get('inclusion_text'),
            trial.get('exclusion_text')
        ))
        
        # Check if it was an insert or update
        result = cursor.fetchone()
        return 'inserted' if result[0] else 'updated'
    
    def get_trial_count(self) -> int:
        """
        Get total number of trials in database
        
        Returns:
            Number of trials
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM trials")
                count = cursor.fetchone()[0]
                return count
    
    def get_trial_by_id(self, trial_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a single trial by ID
        
        Args:
            trial_id: NCT ID
            
        Returns:
            Trial dictionary or None if not found
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT * FROM trials WHERE id = %s",
                    (trial_id,)
                )
                result = cursor.fetchone()
                return dict(result) if result else None
    
    def delete_trial(self, trial_id: str) -> bool:
        """
        Delete a trial by ID
        
        Args:
            trial_id: NCT ID
            
        Returns:
            True if deleted, False if not found
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM trials WHERE id = %s",
                    (trial_id,)
                )
                return cursor.rowcount > 0
    
    def test_connection(self) -> bool:
        """
        Test database connection
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    return result[0] == 1
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
