-- ============================================================================
-- VitalMatch Clinical Trial Matcher - Database Migration
-- Migration: 001_create_trials_table.sql
-- Description: Create trials table with optimized indexes for RDS PostgreSQL
-- Requirements: TR2, 4.4
-- ============================================================================

-- Drop table if exists (for development/testing purposes)
-- Comment out in production to prevent accidental data loss
-- DROP TABLE IF EXISTS trials CASCADE;

-- ============================================================================
-- Create trials table with all required fields
-- ============================================================================

CREATE TABLE IF NOT EXISTS trials (
    -- Primary identifier from ClinicalTrials.gov (e.g., NCT12345678)
    id TEXT PRIMARY KEY,
    
    -- Basic trial information
    title TEXT NOT NULL,
    condition TEXT NOT NULL,
    
    -- Demographic criteria (structured fields for hard filtering)
    min_age INTEGER,
    max_age INTEGER,
    gender_criteria TEXT,
    
    -- Location information
    location TEXT,
    
    -- Eligibility criteria (unstructured text for AI/NLP processing)
    inclusion_text TEXT,
    exclusion_text TEXT,
    
    -- Audit timestamps
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- Create optimized indexes for query performance
-- ============================================================================

-- Composite index for hard filtering on condition and age range
-- Supports queries like: WHERE condition = 'Diabetes' AND min_age <= 65 AND max_age >= 65
CREATE INDEX IF NOT EXISTS idx_condition_age 
ON trials(condition, min_age, max_age);

-- GIN index for full-text search on location using PostgreSQL's text search
-- Supports queries like: WHERE to_tsvector('english', location) @@ to_tsquery('New York')
CREATE INDEX IF NOT EXISTS idx_location_fulltext 
ON trials USING GIN(to_tsvector('english', location));

-- GIN index for full-text search on inclusion criteria text
-- Enables efficient AI/NLP-based soft filtering on inclusion criteria
CREATE INDEX IF NOT EXISTS idx_inclusion_text_fulltext 
ON trials USING GIN(to_tsvector('english', inclusion_text));

-- GIN index for full-text search on exclusion criteria text
-- Enables efficient AI/NLP-based soft filtering on exclusion criteria
CREATE INDEX IF NOT EXISTS idx_exclusion_text_fulltext 
ON trials USING GIN(to_tsvector('english', exclusion_text));

-- Additional index on gender_criteria for filtering
-- Supports queries like: WHERE gender_criteria IN ('Male', 'All')
CREATE INDEX IF NOT EXISTS idx_gender_criteria 
ON trials(gender_criteria);

-- Index on created_date for data freshness queries
-- Supports queries like: WHERE created_date > NOW() - INTERVAL '7 days'
CREATE INDEX IF NOT EXISTS idx_created_date 
ON trials(created_date DESC);

-- ============================================================================
-- Create trigger for automatic updated_date timestamp
-- ============================================================================

-- Function to update the updated_date timestamp
CREATE OR REPLACE FUNCTION update_updated_date_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_date = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update updated_date on row modification
DROP TRIGGER IF EXISTS update_trials_updated_date ON trials;
CREATE TRIGGER update_trials_updated_date
    BEFORE UPDATE ON trials
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_date_column();

-- ============================================================================
-- Add table comments for documentation
-- ============================================================================

COMMENT ON TABLE trials IS 'Clinical trials data from ClinicalTrials.gov with structured and unstructured eligibility criteria';
COMMENT ON COLUMN trials.id IS 'NCT identifier from ClinicalTrials.gov (e.g., NCT12345678)';
COMMENT ON COLUMN trials.title IS 'Official trial title';
COMMENT ON COLUMN trials.condition IS 'Primary medical condition being studied';
COMMENT ON COLUMN trials.min_age IS 'Minimum age requirement in years';
COMMENT ON COLUMN trials.max_age IS 'Maximum age requirement in years';
COMMENT ON COLUMN trials.gender_criteria IS 'Gender eligibility (Male, Female, All, Other)';
COMMENT ON COLUMN trials.location IS 'Trial location(s) as text';
COMMENT ON COLUMN trials.inclusion_text IS 'Unstructured inclusion criteria text for AI/NLP processing';
COMMENT ON COLUMN trials.exclusion_text IS 'Unstructured exclusion criteria text for AI/NLP processing';
COMMENT ON COLUMN trials.created_date IS 'Timestamp when record was created';
COMMENT ON COLUMN trials.updated_date IS 'Timestamp when record was last updated';

-- ============================================================================
-- Verify indexes were created successfully
-- ============================================================================

-- Query to verify all indexes exist
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'trials'
ORDER BY indexname;

-- ============================================================================
-- Performance optimization settings for PostgreSQL
-- ============================================================================

-- Analyze the table to update statistics for query planner
ANALYZE trials;

-- ============================================================================
-- Migration complete
-- ============================================================================

-- Display success message
DO $$
BEGIN
    RAISE NOTICE 'Migration 001_create_trials_table.sql completed successfully';
    RAISE NOTICE 'Table "trials" created with % indexes', (SELECT COUNT(*) FROM pg_indexes WHERE tablename = 'trials');
END $$;
