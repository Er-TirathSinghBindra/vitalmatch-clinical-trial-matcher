"""
Hard Filter Engine
SQL-based filtering for clinical trials using PostgreSQL
Requirements: TR4, 2.1, 2.2, US2
"""

import logging
import time
import psycopg2
from psycopg2 import sql, extras
from typing import Dict, List, Optional, Any, Tuple
from contextlib import contextmanager
from dataclasses import dataclass
import math

logger = logging.getLogger(__name__)


@dataclass
class PatientProfile:
    """Patient profile for trial matching"""
    condition: str
    age: int
    gender: str  # Male, Female, Other, All
    location: str  # City, State format
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    distance_miles: int = 50
    medical_history: Optional[str] = None


@dataclass
class FilterResult:
    """Result of hard filtering operation"""
    trials: List[Dict[str, Any]]
    total_count: int
    filtered_count: int
    processing_time_ms: float
    filters_applied: List[str]


class HardFilterEngine:
    """
    SQL-based hard filtering engine for clinical trials
    Filters trials by age, gender, location, and condition
    """
    
    def __init__(
        self,
        host: str,
        database: str,
        user: str,
        password: str,
        port: int = 5432
    ):
        """
        Initialize hard filter engine
        
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
            'sslmode': 'require'
        }
    
    @contextmanager
    def get_connection(self):
        """Get database connection with automatic cleanup"""
        conn = None
        try:
            conn = psycopg2.connect(**self.connection_params)
            yield conn
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def filter_trials(self, patient: PatientProfile) -> FilterResult:
        """
        Filter trials using SQL-based hard criteria
        
        Args:
            patient: Patient profile with filtering criteria
            
        Returns:
            FilterResult with filtered trials and metadata
        """
        start_time = time.time()
        filters_applied = []
        
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cursor:
                # Get total count before filtering
                cursor.execute("SELECT COUNT(*) as count FROM trials")
                total_count = cursor.fetchone()['count']
                
                # Build and execute filter query
                query, params = self._build_filter_query(patient, filters_applied)
                
                logger.info(f"Executing hard filter query with filters: {filters_applied}")
                cursor.execute(query, params)
                
                trials = [dict(row) for row in cursor.fetchall()]
                filtered_count = len(trials)
        
        processing_time_ms = (time.time() - start_time) * 1000
        
        logger.info(
            f"Hard filtering complete: {total_count} -> {filtered_count} trials "
            f"in {processing_time_ms:.2f}ms"
        )
        
        return FilterResult(
            trials=trials,
            total_count=total_count,
            filtered_count=filtered_count,
            processing_time_ms=processing_time_ms,
            filters_applied=filters_applied
        )
    
    def _build_filter_query(
        self,
        patient: PatientProfile,
        filters_applied: List[str]
    ) -> Tuple[sql.Composed, List[Any]]:
        """
        Build optimized SQL query with all hard filters
        
        Args:
            patient: Patient profile
            filters_applied: List to append filter names to
            
        Returns:
            Tuple of (SQL query, parameters)
        """
        # Base query
        query_parts = ["SELECT * FROM trials WHERE 1=1"]
        params = []
        
        # Filter by condition (fuzzy match using ILIKE for partial matching)
        if patient.condition:
            query_parts.append("AND LOWER(condition) LIKE LOWER(%s)")
            params.append(f'%{patient.condition}%')
            filters_applied.append("condition_fuzzy")
        
        # Filter by age range
        if patient.age is not None:
            query_parts.append(
                "AND (min_age IS NULL OR min_age <= %s) "
                "AND (max_age IS NULL OR max_age >= %s)"
            )
            params.extend([patient.age, patient.age])
            filters_applied.append("age_range")
        
        # Filter by gender
        if patient.gender:
            query_parts.append(
                "AND (gender_criteria IS NULL OR "
                "gender_criteria = 'All' OR "
                "LOWER(gender_criteria) = LOWER(%s))"
            )
            params.append(patient.gender)
            filters_applied.append("gender")
        
        # Filter by location - make it optional and more flexible
        if patient.location:
            # Use simple ILIKE for more flexible location matching
            # This will match if location contains any part of the search term
            query_parts.append(
                "AND (location IS NULL OR LOWER(location) LIKE LOWER(%s))"
            )
            params.append(f'%{patient.location}%')
            filters_applied.append("location_flexible")
        
        # Combine query parts
        query_str = " ".join(query_parts)
        
        # Add ordering and limit
        query_str += " ORDER BY created_date DESC LIMIT 1000"
        
        return sql.SQL(query_str), params
    
    def filter_by_age(
        self,
        patient_age: int,
        trials: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter trials by age range
        
        Args:
            patient_age: Patient's age in years
            trials: Optional list of trials to filter (if None, queries database)
            
        Returns:
            List of trials matching age criteria
        """
        if trials is not None:
            # Filter in-memory trials
            return [
                trial for trial in trials
                if self._matches_age_criteria(trial, patient_age)
            ]
        
        # Query database
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cursor:
                query = sql.SQL("""
                    SELECT * FROM trials
                    WHERE (min_age IS NULL OR min_age <= %s)
                    AND (max_age IS NULL OR max_age >= %s)
                """)
                cursor.execute(query, (patient_age, patient_age))
                return [dict(row) for row in cursor.fetchall()]
    
    def filter_by_gender(
        self,
        patient_gender: str,
        trials: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter trials by gender criteria
        
        Args:
            patient_gender: Patient's gender (Male, Female, Other)
            trials: Optional list of trials to filter
            
        Returns:
            List of trials matching gender criteria
        """
        if trials is not None:
            return [
                trial for trial in trials
                if self._matches_gender_criteria(trial, patient_gender)
            ]
        
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cursor:
                query = sql.SQL("""
                    SELECT * FROM trials
                    WHERE gender_criteria IS NULL
                    OR gender_criteria = 'All'
                    OR LOWER(gender_criteria) = LOWER(%s)
                """)
                cursor.execute(query, (patient_gender,))
                return [dict(row) for row in cursor.fetchall()]
    
    def filter_by_location(
        self,
        location: str,
        distance_miles: int = 50,
        trials: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter trials by location using text search
        
        Args:
            location: Location string (city, state)
            distance_miles: Maximum distance in miles
            trials: Optional list of trials to filter
            
        Returns:
            List of trials matching location criteria
        """
        if trials is not None:
            # Simple text matching for in-memory filtering
            location_lower = location.lower()
            return [
                trial for trial in trials
                if trial.get('location') and location_lower in trial['location'].lower()
            ]
        
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cursor:
                query = sql.SQL("""
                    SELECT * FROM trials
                    WHERE to_tsvector('english', location) @@ plainto_tsquery('english', %s)
                """)
                cursor.execute(query, (location,))
                return [dict(row) for row in cursor.fetchall()]
    
    def filter_by_condition(
        self,
        condition: str,
        fuzzy: bool = False,
        trials: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter trials by medical condition
        
        Args:
            condition: Medical condition
            fuzzy: If True, use fuzzy matching; if False, exact match
            trials: Optional list of trials to filter
            
        Returns:
            List of trials matching condition
        """
        if trials is not None:
            condition_lower = condition.lower()
            if fuzzy:
                return [
                    trial for trial in trials
                    if condition_lower in trial.get('condition', '').lower()
                ]
            else:
                return [
                    trial for trial in trials
                    if trial.get('condition', '').lower() == condition_lower
                ]
        
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cursor:
                if fuzzy:
                    query = sql.SQL("""
                        SELECT * FROM trials
                        WHERE LOWER(condition) LIKE LOWER(%s)
                    """)
                    cursor.execute(query, (f'%{condition}%',))
                else:
                    query = sql.SQL("""
                        SELECT * FROM trials
                        WHERE LOWER(condition) = LOWER(%s)
                    """)
                    cursor.execute(query, (condition,))
                
                return [dict(row) for row in cursor.fetchall()]
    
    def calculate_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """
        Calculate distance between two coordinates using Haversine formula
        
        Args:
            lat1, lon1: First coordinate
            lat2, lon2: Second coordinate
            
        Returns:
            Distance in miles
        """
        # Earth radius in miles
        R = 3959.0
        
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2)
        c = 2 * math.asin(math.sqrt(a))
        
        distance = R * c
        return distance
    
    def _matches_age_criteria(self, trial: Dict[str, Any], age: int) -> bool:
        """Check if trial matches age criteria"""
        min_age = trial.get('min_age')
        max_age = trial.get('max_age')
        
        if min_age is not None and age < min_age:
            return False
        if max_age is not None and age > max_age:
            return False
        
        return True
    
    def _matches_gender_criteria(self, trial: Dict[str, Any], gender: str) -> bool:
        """Check if trial matches gender criteria"""
        trial_gender = trial.get('gender_criteria')
        
        if trial_gender is None or trial_gender == 'All':
            return True
        
        return trial_gender.lower() == gender.lower()
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics for monitoring
        
        Returns:
            Dictionary with statistics
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cursor:
                stats = {}
                
                # Total trials
                cursor.execute("SELECT COUNT(*) as count FROM trials")
                stats['total_trials'] = cursor.fetchone()['count']
                
                # Trials by gender criteria
                cursor.execute("""
                    SELECT gender_criteria, COUNT(*) as count
                    FROM trials
                    GROUP BY gender_criteria
                """)
                stats['by_gender'] = {row['gender_criteria']: row['count'] 
                                     for row in cursor.fetchall()}
                
                # Trials with age criteria
                cursor.execute("""
                    SELECT 
                        COUNT(*) FILTER (WHERE min_age IS NOT NULL) as with_min_age,
                        COUNT(*) FILTER (WHERE max_age IS NOT NULL) as with_max_age,
                        COUNT(*) FILTER (WHERE min_age IS NULL AND max_age IS NULL) as no_age_criteria
                    FROM trials
                """)
                stats['age_criteria'] = dict(cursor.fetchone())
                
                return stats
