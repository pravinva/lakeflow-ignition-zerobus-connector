-- ============================================================================
-- FIELD-ENG WORKSPACE SETUP FOR ZEROBUS CONNECTOR
-- ============================================================================
-- Workspace: e2-demo-field-eng.cloud.databricks.com
-- Service Principal: 15cc0f97-26e7-4fc9-9f0a-e5b48c7dec9d
-- Run this in Databricks SQL Editor
-- ============================================================================

-- Step 1: Create Catalog
CREATE CATALOG IF NOT EXISTS ignition_demo;

-- Step 2: Create Schema
CREATE SCHEMA IF NOT EXISTS ignition_demo.scada_data;

-- Step 3: Create Table
CREATE TABLE IF NOT EXISTS ignition_demo.scada_data.tag_events (
    event_id STRING COMMENT 'Unique event identifier',
    event_time TIMESTAMP COMMENT 'Event timestamp from Ignition tag',
    tag_path STRING COMMENT 'Full Ignition tag path (e.g., [default]TestSimulator/Sine0)',
    tag_provider STRING COMMENT 'Ignition tag provider name',
    numeric_value DOUBLE COMMENT 'Numeric tag value',
    string_value STRING COMMENT 'String tag value',
    boolean_value BOOLEAN COMMENT 'Boolean tag value',
    quality STRING COMMENT 'Tag quality: GOOD, BAD, UNCERTAIN',
    quality_code INT COMMENT 'Numeric quality code from Ignition',
    source_system STRING COMMENT 'Source Ignition Gateway identifier',
    ingestion_timestamp TIMESTAMP COMMENT 'Databricks ingestion time',
    data_type STRING COMMENT 'Original data type from Ignition tag',
    alarm_state STRING COMMENT 'Alarm state if tag is in alarm',
    alarm_priority INT COMMENT 'Alarm priority level'
)
USING DELTA
COMMENT 'Real-time SCADA tag events from Ignition Gateway via Zerobus'
TBLPROPERTIES (
    'delta.enableChangeDataFeed' = 'true',
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true'
);

-- Step 4: Create View for Recent Events
CREATE OR REPLACE VIEW ignition_demo.scada_data.vw_recent_tags AS
SELECT 
    event_time,
    tag_path,
    tag_provider,
    COALESCE(
        CAST(numeric_value AS STRING),
        string_value,
        CAST(boolean_value AS STRING)
    ) AS value,
    quality,
    source_system,
    ingestion_timestamp,
    data_type,
    alarm_state
FROM ignition_demo.scada_data.tag_events
WHERE event_time >= CURRENT_TIMESTAMP() - INTERVAL 1 HOUR
ORDER BY event_time DESC;

-- Step 5: Grant Permissions to Service Principal
-- Replace with actual service principal name if different
GRANT USE CATALOG ON CATALOG ignition_demo TO `15cc0f97-26e7-4fc9-9f0a-e5b48c7dec9d`;
GRANT USE SCHEMA ON SCHEMA ignition_demo.scada_data TO `15cc0f97-26e7-4fc9-9f0a-e5b48c7dec9d`;
GRANT SELECT, MODIFY ON TABLE ignition_demo.scada_data.tag_events TO `15cc0f97-26e7-4fc9-9f0a-e5b48c7dec9d`;

-- Step 6: Verify Permissions
SHOW GRANTS ON TABLE ignition_demo.scada_data.tag_events;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Check catalog exists
SHOW CATALOGS LIKE 'ignition_demo';

-- Check schema exists
SHOW SCHEMAS IN ignition_demo;

-- Check table exists
SHOW TABLES IN ignition_demo.scada_data;

-- Check table structure
DESCRIBE TABLE ignition_demo.scada_data.tag_events;

-- Test query (should return 0 rows initially)
SELECT COUNT(*) FROM ignition_demo.scada_data.tag_events;

-- ============================================================================
-- NOTES:
-- ============================================================================
-- After running this script:
-- 1. The Ignition module should connect successfully
-- 2. Data should start flowing within 30-60 seconds
-- 3. Query the view to see recent data:
--    SELECT * FROM ignition_demo.scada_data.vw_recent_tags LIMIT 10;
-- ============================================================================

