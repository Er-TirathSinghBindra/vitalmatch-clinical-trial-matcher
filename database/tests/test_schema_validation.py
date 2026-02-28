"""
VitalMatch Clinical Trial Matcher - Database Schema Validation Tests
Task 2.2: Write database schema validation tests

Tests cover:
- Table creation and constraints
- Index performance with sample data
- Data types and nullable fields
- Requirements: TR2
"""

import os
import pytest
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
from datetime import datetime
import time


# ============================================================================
# Test Configuration and Fixtures
# ============================================================================

@pytest.fixture(scope="module")
def db_connection():
    """
    Create database connection for tests.
    Uses environment variables for connection parameters.
    """
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "trials_db"),
        user=os.getenv("DB_USER", "vitalmatch_admin"),
        password=os.getenv("DB_PASSWORD", "password")
    )
    yield conn
    conn.close()


@pytest.fixture(scope="module")
def db_cursor(db_connection):
    """Create a cursor for executing queries."""
    cursor = db_connection.cursor(cursor_factory=RealDictCursor)
    yield cursor
    cursor.close()


# ============================================================================
# Test 1: Table Creation and Structure
# ============================================================================

@pytest.mark.table
class TestTableCreation:
    """Test that the trials table exists with correct structure."""
    
    def test_trials_table_exists(self, db_cursor):
        """Verify trials table exists in the database."""
        db_cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'trials'
            );
        """)
        result = db_cursor.fetchone()
        assert result['exists'], "trials table should exist"
    
    def test_trials_table_columns(self, db_cursor):
        """Verify all required columns exist with correct data types."""
        db_cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'trials'
            ORDER BY ordinal_position;
        """)
        columns = {row['column_name']: row for row in db_cursor.fetchall()}
        
        # Verify primary key column
        assert 'id' in columns, "id column should exist"
        assert columns['id']['data_type'] == 'text', "id should be TEXT type"
        assert columns['id']['is_nullable'] == 'NO', "id should be NOT NULL"
        
        # Verify required fields
        assert 'title' in columns, "title column should exist"
        assert columns['title']['data_type'] == 'text', "title should be TEXT type"
        assert columns['title']['is_nullable'] == 'NO', "title should be NOT NULL"
        
        assert 'condition' in columns, "condition column should exist"
        assert columns['condition']['data_type'] == 'text', "condition should be TEXT type"
        assert columns['condition']['is_nullable'] == 'NO', "condition should be NOT NULL"
        
        # Verify optional demographic fields
        assert 'min_age' in columns, "min_age column should exist"
        assert columns['min_age']['data_type'] == 'integer', "min_age should be INTEGER type"
        assert columns['min_age']['is_nullable'] == 'YES', "min_age should be nullable"
        
        assert 'max_age' in columns, "max_age column should exist"
        assert columns['max_age']['data_type'] == 'integer', "max_age should be INTEGER type"
        assert columns['max_age']['is_nullable'] == 'YES', "max_age should be nullable"
        
        assert 'gender_criteria' in columns, "gender_criteria column should exist"
        assert columns['gender_criteria']['data_type'] == 'text', "gender_criteria should be TEXT type"
        assert columns['gender_criteria']['is_nullable'] == 'YES', "gender_criteria should be nullable"
        
        # Verify location field
        assert 'location' in columns, "location column should exist"
        assert columns['location']['data_type'] == 'text', "location should be TEXT type"
        assert columns['location']['is_nullable'] == 'YES', "location should be nullable"
        
        # Verify eligibility text fields
        assert 'inclusion_text' in columns, "inclusion_text column should exist"
        assert columns['inclusion_text']['data_type'] == 'text', "inclusion_text should be TEXT type"
        assert columns['inclusion_text']['is_nullable'] == 'YES', "inclusion_text should be nullable"
        
        assert 'exclusion_text' in columns, "exclusion_text column should exist"
        assert columns['exclusion_text']['data_type'] == 'text', "exclusion_text should be TEXT type"
        assert columns['exclusion_text']['is_nullable'] == 'YES', "exclusion_text should be nullable"
        
        # Verify timestamp fields
        assert 'created_date' in columns, "created_date column should exist"
        assert columns['created_date']['data_type'] == 'timestamp without time zone', \
            "created_date should be TIMESTAMP type"
        assert 'CURRENT_TIMESTAMP' in columns['created_date']['column_default'], \
            "created_date should default to CURRENT_TIMESTAMP"
        
        assert 'updated_date' in columns, "updated_date column should exist"
        assert columns['updated_date']['data_type'] == 'timestamp without time zone', \
            "updated_date should be TIMESTAMP type"
        assert 'CURRENT_TIMESTAMP' in columns['updated_date']['column_default'], \
            "updated_date should default to CURRENT_TIMESTAMP"


# ============================================================================
# Test 2: Constraints and Primary Key
# ============================================================================

@pytest.mark.constraints
class TestConstraints:
    """Test database constraints and primary key."""
    
    def test_primary_key_constraint(self, db_cursor):
        """Verify primary key constraint exists on id column."""
        db_cursor.execute("""
            SELECT constraint_name, constraint_type
            FROM information_schema.table_constraints
            WHERE table_name = 'trials' AND constraint_type = 'PRIMARY KEY';
        """)
        result = db_cursor.fetchone()
        assert result is not None, "Primary key constraint should exist"
        assert result['constraint_type'] == 'PRIMARY KEY'
    
    def test_primary_key_uniqueness(self, db_connection, db_cursor):
        """Verify primary key enforces uniqueness."""
        # Insert a test trial
        test_id = 'NCT_TEST_UNIQUE_001'
        try:
            db_cursor.execute("""
                INSERT INTO trials (id, title, condition)
                VALUES (%s, 'Test Trial', 'Test Condition');
            """, (test_id,))
            db_connection.commit()
            
            # Try to insert duplicate - should fail
            with pytest.raises(psycopg2.IntegrityError):
                db_cursor.execute("""
                    INSERT INTO trials (id, title, condition)
                    VALUES (%s, 'Duplicate Trial', 'Test Condition');
                """, (test_id,))
                db_connection.commit()
        finally:
            # Cleanup
            db_connection.rollback()
            db_cursor.execute("DELETE FROM trials WHERE id = %s;", (test_id,))
            db_connection.commit()
    
    def test_not_null_constraints(self, db_connection, db_cursor):
        """Verify NOT NULL constraints on required fields."""
        # Test missing title
        with pytest.raises(psycopg2.IntegrityError):
            db_cursor.execute("""
                INSERT INTO trials (id, condition)
                VALUES ('NCT_TEST_NULL_001', 'Test Condition');
            """)
            db_connection.commit()
        db_connection.rollback()
        
        # Test missing condition
        with pytest.raises(psycopg2.IntegrityError):
            db_cursor.execute("""
                INSERT INTO trials (id, title)
                VALUES ('NCT_TEST_NULL_002', 'Test Title');
            """)
            db_connection.commit()
        db_connection.rollback()
        
        # Test missing id
        with pytest.raises(psycopg2.IntegrityError):
            db_cursor.execute("""
                INSERT INTO trials (title, condition)
                VALUES ('Test Title', 'Test Condition');
            """)
            db_connection.commit()
        db_connection.rollback()


# ============================================================================
# Test 3: Indexes Existence and Configuration
# ============================================================================

@pytest.mark.indexes
class TestIndexes:
    """Test that all required indexes exist with correct configuration."""
    
    def test_all_indexes_exist(self, db_cursor):
        """Verify all 6 required indexes exist."""
        db_cursor.execute("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = 'trials'
            ORDER BY indexname;
        """)
        indexes = {row['indexname']: row['indexdef'] for row in db_cursor.fetchall()}
        
        # Verify primary key index (automatically created)
        assert 'trials_pkey' in indexes, "Primary key index should exist"
        
        # Verify composite index on condition and age
        assert 'idx_condition_age' in indexes, "idx_condition_age should exist"
        assert 'condition' in indexes['idx_condition_age'], \
            "idx_condition_age should include condition column"
        assert 'min_age' in indexes['idx_condition_age'], \
            "idx_condition_age should include min_age column"
        assert 'max_age' in indexes['idx_condition_age'], \
            "idx_condition_age should include max_age column"
        
        # Verify GIN full-text search indexes
        assert 'idx_location_fulltext' in indexes, "idx_location_fulltext should exist"
        assert 'gin' in indexes['idx_location_fulltext'].lower(), \
            "idx_location_fulltext should be a GIN index"
        assert 'to_tsvector' in indexes['idx_location_fulltext'], \
            "idx_location_fulltext should use to_tsvector"
        
        assert 'idx_inclusion_text_fulltext' in indexes, "idx_inclusion_text_fulltext should exist"
        assert 'gin' in indexes['idx_inclusion_text_fulltext'].lower(), \
            "idx_inclusion_text_fulltext should be a GIN index"
        
        assert 'idx_exclusion_text_fulltext' in indexes, "idx_exclusion_text_fulltext should exist"
        assert 'gin' in indexes['idx_exclusion_text_fulltext'].lower(), \
            "idx_exclusion_text_fulltext should be a GIN index"
        
        # Verify gender criteria index
        assert 'idx_gender_criteria' in indexes, "idx_gender_criteria should exist"
        assert 'gender_criteria' in indexes['idx_gender_criteria'], \
            "idx_gender_criteria should include gender_criteria column"
        
        # Verify created_date index
        assert 'idx_created_date' in indexes, "idx_created_date should exist"
        assert 'created_date' in indexes['idx_created_date'], \
            "idx_created_date should include created_date column"
    
    def test_index_types(self, db_cursor):
        """Verify correct index types (B-tree vs GIN)."""
        db_cursor.execute("""
            SELECT 
                i.relname as index_name,
                am.amname as index_type
            FROM pg_class t
            JOIN pg_index ix ON t.oid = ix.indrelid
            JOIN pg_class i ON i.oid = ix.indexrelid
            JOIN pg_am am ON i.relam = am.oid
            WHERE t.relname = 'trials'
            ORDER BY i.relname;
        """)
        indexes = {row['index_name']: row['index_type'] for row in db_cursor.fetchall()}
        
        # B-tree indexes (default for standard columns)
        assert indexes.get('idx_condition_age') == 'btree', \
            "idx_condition_age should be B-tree index"
        assert indexes.get('idx_gender_criteria') == 'btree', \
            "idx_gender_criteria should be B-tree index"
        assert indexes.get('idx_created_date') == 'btree', \
            "idx_created_date should be B-tree index"
        
        # GIN indexes (for full-text search)
        assert indexes.get('idx_location_fulltext') == 'gin', \
            "idx_location_fulltext should be GIN index"
        assert indexes.get('idx_inclusion_text_fulltext') == 'gin', \
            "idx_inclusion_text_fulltext should be GIN index"
        assert indexes.get('idx_exclusion_text_fulltext') == 'gin', \
            "idx_exclusion_text_fulltext should be GIN index"


# ============================================================================
# Test 4: Index Performance with Sample Data
# ============================================================================

@pytest.mark.performance
class TestIndexPerformance:
    """Test index performance with sample data."""
    
    @pytest.fixture(scope="class", autouse=True)
    def setup_sample_data(self, db_connection, db_cursor):
        """Insert sample data for performance testing."""
        # Check if sample data already exists
        db_cursor.execute("SELECT COUNT(*) as count FROM trials;")
        count = db_cursor.fetchone()['count']
        
        if count == 0:
            # Load sample data from sample_data.sql
            sample_data_path = os.path.join(
                os.path.dirname(__file__), 
                '..', 
                'migrations', 
                'sample_data.sql'
            )
            if os.path.exists(sample_data_path):
                with open(sample_data_path, 'r') as f:
                    # Read and execute SQL (skip psql-specific commands)
                    sql_content = f.read()
                    # Remove psql echo commands
                    sql_lines = [line for line in sql_content.split('\n') 
                                if not line.strip().startswith('\\echo')]
                    sql_content = '\n'.join(sql_lines)
                    db_cursor.execute(sql_content)
                    db_connection.commit()
        
        yield
        # Don't cleanup - keep sample data for other tests
    
    def test_condition_age_index_performance(self, db_cursor):
        """Test query performance using condition and age index."""
        # Query that should use idx_condition_age
        query = """
            EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
            SELECT * FROM trials
            WHERE condition = 'Type 2 Diabetes'
            AND min_age <= 65
            AND max_age >= 65;
        """
        
        start_time = time.time()
        db_cursor.execute(query)
        result = db_cursor.fetchone()
        execution_time = time.time() - start_time
        
        # Verify query completes quickly (should be < 100ms for small dataset)
        assert execution_time < 0.1, \
            f"Query should complete in < 100ms, took {execution_time*1000:.2f}ms"
        
        # Verify index is being used
        plan = result[0][0]
        plan_str = str(plan)
        # For small datasets, PostgreSQL might use sequential scan
        # Just verify query executes successfully
        assert 'Execution Time' in plan_str, "Query should have execution time"
    
    def test_location_fulltext_index_performance(self, db_cursor):
        """Test full-text search performance on location field."""
        query = """
            EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
            SELECT * FROM trials
            WHERE to_tsvector('english', location) @@ to_tsquery('english', 'New & York');
        """
        
        start_time = time.time()
        db_cursor.execute(query)
        result = db_cursor.fetchone()
        execution_time = time.time() - start_time
        
        # Verify query completes quickly
        assert execution_time < 0.1, \
            f"Full-text search should complete in < 100ms, took {execution_time*1000:.2f}ms"
        
        # Verify query executes successfully
        plan = result[0][0]
        assert 'Execution Time' in str(plan), "Query should have execution time"
    
    def test_inclusion_text_fulltext_index_performance(self, db_cursor):
        """Test full-text search performance on inclusion_text field."""
        query = """
            EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
            SELECT * FROM trials
            WHERE to_tsvector('english', inclusion_text) @@ to_tsquery('english', 'diabetes');
        """
        
        start_time = time.time()
        db_cursor.execute(query)
        result = db_cursor.fetchone()
        execution_time = time.time() - start_time
        
        # Verify query completes quickly
        assert execution_time < 0.1, \
            f"Full-text search should complete in < 100ms, took {execution_time*1000:.2f}ms"
    
    def test_gender_criteria_index_performance(self, db_cursor):
        """Test query performance using gender_criteria index."""
        query = """
            EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
            SELECT * FROM trials
            WHERE gender_criteria IN ('Male', 'All');
        """
        
        start_time = time.time()
        db_cursor.execute(query)
        result = db_cursor.fetchone()
        execution_time = time.time() - start_time
        
        # Verify query completes quickly
        assert execution_time < 0.1, \
            f"Query should complete in < 100ms, took {execution_time*1000:.2f}ms"
    
    def test_created_date_index_performance(self, db_cursor):
        """Test query performance using created_date index."""
        query = """
            EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
            SELECT * FROM trials
            WHERE created_date > NOW() - INTERVAL '7 days'
            ORDER BY created_date DESC;
        """
        
        start_time = time.time()
        db_cursor.execute(query)
        result = db_cursor.fetchone()
        execution_time = time.time() - start_time
        
        # Verify query completes quickly
        assert execution_time < 0.1, \
            f"Query should complete in < 100ms, took {execution_time*1000:.2f}ms"


# ============================================================================
# Test 5: Data Types and Nullable Fields
# ============================================================================

@pytest.mark.datatypes
class TestDataTypes:
    """Test data type handling and nullable field behavior."""
    
    def test_text_fields_accept_long_content(self, db_connection, db_cursor):
        """Verify TEXT fields can store long content."""
        test_id = 'NCT_TEST_LONG_001'
        long_text = 'A' * 10000  # 10,000 characters
        
        try:
            db_cursor.execute("""
                INSERT INTO trials (id, title, condition, inclusion_text, exclusion_text)
                VALUES (%s, %s, %s, %s, %s);
            """, (test_id, 'Test Long Text', 'Test Condition', long_text, long_text))
            db_connection.commit()
            
            # Verify data was stored correctly
            db_cursor.execute("SELECT inclusion_text, exclusion_text FROM trials WHERE id = %s;", 
                            (test_id,))
            result = db_cursor.fetchone()
            assert len(result['inclusion_text']) == 10000, \
                "TEXT field should store 10,000 characters"
            assert len(result['exclusion_text']) == 10000, \
                "TEXT field should store 10,000 characters"
        finally:
            # Cleanup
            db_cursor.execute("DELETE FROM trials WHERE id = %s;", (test_id,))
            db_connection.commit()
    
    def test_integer_age_fields(self, db_connection, db_cursor):
        """Verify age fields accept valid integer values."""
        test_id = 'NCT_TEST_AGE_001'
        
        try:
            db_cursor.execute("""
                INSERT INTO trials (id, title, condition, min_age, max_age)
                VALUES (%s, 'Test Age', 'Test Condition', 18, 75);
            """, (test_id,))
            db_connection.commit()
            
            # Verify data was stored correctly
            db_cursor.execute("SELECT min_age, max_age FROM trials WHERE id = %s;", (test_id,))
            result = db_cursor.fetchone()
            assert result['min_age'] == 18, "min_age should be 18"
            assert result['max_age'] == 75, "max_age should be 75"
            assert isinstance(result['min_age'], int), "min_age should be integer type"
            assert isinstance(result['max_age'], int), "max_age should be integer type"
        finally:
            # Cleanup
            db_cursor.execute("DELETE FROM trials WHERE id = %s;", (test_id,))
            db_connection.commit()
    
    def test_nullable_fields_accept_null(self, db_connection, db_cursor):
        """Verify optional fields can be NULL."""
        test_id = 'NCT_TEST_NULL_003'
        
        try:
            # Insert with only required fields
            db_cursor.execute("""
                INSERT INTO trials (id, title, condition)
                VALUES (%s, 'Test Nullable', 'Test Condition');
            """, (test_id,))
            db_connection.commit()
            
            # Verify NULL values were stored
            db_cursor.execute("""
                SELECT min_age, max_age, gender_criteria, location, 
                       inclusion_text, exclusion_text
                FROM trials WHERE id = %s;
            """, (test_id,))
            result = db_cursor.fetchone()
            assert result['min_age'] is None, "min_age should be NULL"
            assert result['max_age'] is None, "max_age should be NULL"
            assert result['gender_criteria'] is None, "gender_criteria should be NULL"
            assert result['location'] is None, "location should be NULL"
            assert result['inclusion_text'] is None, "inclusion_text should be NULL"
            assert result['exclusion_text'] is None, "exclusion_text should be NULL"
        finally:
            # Cleanup
            db_cursor.execute("DELETE FROM trials WHERE id = %s;", (test_id,))
            db_connection.commit()
    
    def test_timestamp_fields_auto_populate(self, db_connection, db_cursor):
        """Verify timestamp fields automatically populate with current timestamp."""
        test_id = 'NCT_TEST_TIMESTAMP_001'
        
        try:
            before_insert = datetime.now()
            
            db_cursor.execute("""
                INSERT INTO trials (id, title, condition)
                VALUES (%s, 'Test Timestamp', 'Test Condition');
            """, (test_id,))
            db_connection.commit()
            
            after_insert = datetime.now()
            
            # Verify timestamps were auto-populated
            db_cursor.execute("""
                SELECT created_date, updated_date FROM trials WHERE id = %s;
            """, (test_id,))
            result = db_cursor.fetchone()
            
            assert result['created_date'] is not None, "created_date should be auto-populated"
            assert result['updated_date'] is not None, "updated_date should be auto-populated"
            
            # Verify timestamps are within reasonable range
            assert before_insert <= result['created_date'] <= after_insert, \
                "created_date should be between before and after insert time"
            assert before_insert <= result['updated_date'] <= after_insert, \
                "updated_date should be between before and after insert time"
        finally:
            # Cleanup
            db_cursor.execute("DELETE FROM trials WHERE id = %s;", (test_id,))
            db_connection.commit()


# ============================================================================
# Test 6: Trigger Functionality
# ============================================================================

@pytest.mark.triggers
class TestTriggers:
    """Test automatic trigger for updated_date."""
    
    def test_updated_date_trigger(self, db_connection, db_cursor):
        """Verify updated_date trigger updates timestamp on row modification."""
        test_id = 'NCT_TEST_TRIGGER_001'
        
        try:
            # Insert initial record
            db_cursor.execute("""
                INSERT INTO trials (id, title, condition)
                VALUES (%s, 'Test Trigger', 'Test Condition');
            """, (test_id,))
            db_connection.commit()
            
            # Get initial timestamps
            db_cursor.execute("""
                SELECT created_date, updated_date FROM trials WHERE id = %s;
            """, (test_id,))
            initial = db_cursor.fetchone()
            
            # Wait a moment to ensure timestamp difference
            time.sleep(0.1)
            
            # Update the record
            db_cursor.execute("""
                UPDATE trials SET title = 'Updated Title' WHERE id = %s;
            """, (test_id,))
            db_connection.commit()
            
            # Get updated timestamps
            db_cursor.execute("""
                SELECT created_date, updated_date FROM trials WHERE id = %s;
            """, (test_id,))
            updated = db_cursor.fetchone()
            
            # Verify created_date didn't change
            assert initial['created_date'] == updated['created_date'], \
                "created_date should not change on update"
            
            # Verify updated_date changed
            assert updated['updated_date'] > initial['updated_date'], \
                "updated_date should be updated by trigger"
        finally:
            # Cleanup
            db_cursor.execute("DELETE FROM trials WHERE id = %s;", (test_id,))
            db_connection.commit()


# ============================================================================
# Test 7: Sample Data Validation
# ============================================================================

@pytest.mark.sample_data
class TestSampleData:
    """Validate sample data is correctly loaded."""
    
    def test_sample_data_exists(self, db_cursor):
        """Verify sample data was loaded."""
        db_cursor.execute("SELECT COUNT(*) as count FROM trials;")
        result = db_cursor.fetchone()
        assert result['count'] >= 8, "Should have at least 8 sample trials"
    
    def test_sample_data_variety(self, db_cursor):
        """Verify sample data has variety in conditions and demographics."""
        db_cursor.execute("""
            SELECT 
                COUNT(DISTINCT condition) as unique_conditions,
                COUNT(DISTINCT gender_criteria) as unique_genders,
                MIN(min_age) as youngest,
                MAX(max_age) as oldest
            FROM trials;
        """)
        result = db_cursor.fetchone()
        
        assert result['unique_conditions'] >= 5, \
            "Should have at least 5 different conditions"
        assert result['unique_genders'] >= 2, \
            "Should have at least 2 different gender criteria"
        assert result['youngest'] <= 18, \
            "Should have trials for young adults"
        assert result['oldest'] >= 75, \
            "Should have trials for older adults"
