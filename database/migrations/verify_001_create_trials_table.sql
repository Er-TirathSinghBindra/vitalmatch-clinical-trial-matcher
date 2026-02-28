-- ============================================================================
-- VitalMatch Clinical Trial Matcher - Migration Verification
-- Verification Script: verify_001_create_trials_table.sql
-- Description: Verify that the trials table and indexes were created correctly
-- ============================================================================

\echo '============================================================================'
\echo 'Verifying Migration 001: Create Trials Table'
\echo '============================================================================'
\echo ''

-- Check if table exists
\echo 'Checking if trials table exists...'
SELECT 
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_name = 'trials'
        ) THEN '✓ Table "trials" exists'
        ELSE '✗ Table "trials" NOT FOUND'
    END AS table_status;

\echo ''

-- Display table structure
\echo 'Table Structure:'
\d trials

\echo ''

-- Check all columns exist
\echo 'Verifying all required columns...'
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'trials'
ORDER BY ordinal_position;

\echo ''

-- Check indexes
\echo 'Verifying indexes...'
SELECT 
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'trials'
ORDER BY indexname;

\echo ''

-- Count indexes
\echo 'Index Summary:'
SELECT 
    COUNT(*) as total_indexes,
    COUNT(CASE WHEN indexdef LIKE '%USING gin%' THEN 1 END) as gin_indexes,
    COUNT(CASE WHEN indexdef LIKE '%USING btree%' OR indexdef NOT LIKE '%USING%' THEN 1 END) as btree_indexes
FROM pg_indexes
WHERE tablename = 'trials';

\echo ''

-- Check trigger exists
\echo 'Verifying trigger for updated_date...'
SELECT 
    trigger_name,
    event_manipulation,
    action_statement
FROM information_schema.triggers
WHERE event_object_table = 'trials';

\echo ''

-- Check function exists
\echo 'Verifying update_updated_date_column function...'
SELECT 
    routine_name,
    routine_type,
    data_type
FROM information_schema.routines
WHERE routine_name = 'update_updated_date_column';

\echo ''

-- Test insert and update to verify trigger works
\echo 'Testing trigger functionality...'
\echo 'Inserting test record...'

INSERT INTO trials (
    id, 
    title, 
    condition, 
    min_age, 
    max_age, 
    gender_criteria, 
    location, 
    inclusion_text, 
    exclusion_text
) VALUES (
    'NCT_TEST_001',
    'Test Trial for Verification',
    'Test Condition',
    18,
    65,
    'All',
    'Test Location, USA',
    'Test inclusion criteria',
    'Test exclusion criteria'
) ON CONFLICT (id) DO NOTHING;

\echo 'Checking timestamps...'
SELECT 
    id,
    created_date,
    updated_date,
    CASE 
        WHEN created_date IS NOT NULL AND updated_date IS NOT NULL 
        THEN '✓ Timestamps set correctly'
        ELSE '✗ Timestamp issue detected'
    END AS timestamp_status
FROM trials
WHERE id = 'NCT_TEST_001';

\echo ''
\echo 'Updating test record to verify trigger...'

-- Wait a moment to ensure timestamp difference
SELECT pg_sleep(1);

UPDATE trials 
SET title = 'Test Trial for Verification - Updated'
WHERE id = 'NCT_TEST_001';

\echo 'Verifying updated_date changed...'
SELECT 
    id,
    created_date,
    updated_date,
    CASE 
        WHEN updated_date > created_date 
        THEN '✓ Trigger working: updated_date > created_date'
        ELSE '✗ Trigger issue: updated_date not updated'
    END AS trigger_status
FROM trials
WHERE id = 'NCT_TEST_001';

\echo ''
\echo 'Cleaning up test record...'
DELETE FROM trials WHERE id = 'NCT_TEST_001';

\echo ''

-- Test full-text search indexes
\echo 'Testing full-text search indexes...'
\echo 'Inserting test data for full-text search...'

INSERT INTO trials (
    id, 
    title, 
    condition, 
    location, 
    inclusion_text, 
    exclusion_text
) VALUES (
    'NCT_TEST_FTS_001',
    'Full-Text Search Test',
    'Diabetes',
    'New York, NY, USA',
    'Patients with history of smoking and hypertension',
    'Patients with severe kidney disease'
) ON CONFLICT (id) DO NOTHING;

\echo 'Testing location full-text search...'
EXPLAIN (ANALYZE, BUFFERS) 
SELECT id, title, location 
FROM trials 
WHERE to_tsvector('english', location) @@ to_tsquery('New & York');

\echo ''
\echo 'Testing inclusion_text full-text search...'
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, title, inclusion_text 
FROM trials 
WHERE to_tsvector('english', inclusion_text) @@ to_tsquery('smoking & history');

\echo ''
\echo 'Cleaning up test record...'
DELETE FROM trials WHERE id = 'NCT_TEST_FTS_001';

\echo ''

-- Display table statistics
\echo 'Table Statistics:'
SELECT 
    schemaname,
    tablename,
    n_live_tup as row_count,
    n_dead_tup as dead_rows,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables
WHERE tablename = 'trials';

\echo ''
\echo '============================================================================'
\echo 'Verification Complete!'
\echo '============================================================================'
\echo ''
\echo 'Expected Results:'
\echo '  - Table "trials" exists with 11 columns'
\echo '  - 7 indexes created (1 primary key + 6 additional indexes)'
\echo '  - 3 GIN indexes for full-text search'
\echo '  - Trigger "update_trials_updated_date" exists'
\echo '  - Function "update_updated_date_column" exists'
\echo '  - Timestamps automatically set on insert/update'
\echo ''
