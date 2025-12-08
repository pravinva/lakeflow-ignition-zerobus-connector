-- Databricks Testing Environment Setup for Ignition Zerobus Connector
-- Workspace: e2-demo-field-eng.cloud.databricks.com
-- User: pravin.varma@databricks.com

-- ============================================================
-- Step 1: Create Schema for OT Data
-- ============================================================

CREATE SCHEMA IF NOT EXISTS main.ignition_ot_test
COMMENT 'Testing schema for Ignition → Zerobus → Databricks integration'
LOCATION 'dbfs:/user/pravin.varma/ignition_ot_test';

-- ============================================================
-- Step 2: Create Bronze Layer Table for Raw OT Events
-- ============================================================

CREATE TABLE IF NOT EXISTS main.ignition_ot_test.bronze_events (
  event_time TIMESTAMP COMMENT 'Event timestamp from Ignition tag',
  tag_path STRING COMMENT 'Full Ignition tag path',
  asset_id STRING COMMENT 'Asset identifier extracted from tag path',
  asset_path STRING COMMENT 'Asset hierarchy path',
  numeric_value DOUBLE COMMENT 'Numeric tag value',
  string_value STRING COMMENT 'String tag value',
  boolean_value BOOLEAN COMMENT 'Boolean tag value',
  integer_value BIGINT COMMENT 'Integer tag value',
  value_string STRING COMMENT 'Value as string for all types',
  quality STRING COMMENT 'Data quality: GOOD, BAD, UNCERTAIN, UNKNOWN',
  source_system STRING COMMENT 'Source Ignition Gateway identifier',
  site STRING COMMENT 'Site/location identifier',
  line STRING COMMENT 'Production line identifier',
  unit STRING COMMENT 'Equipment unit identifier',
  tag_description STRING COMMENT 'Tag description/metadata',
  engineering_units STRING COMMENT 'Engineering units (PSI, RPM, °C, etc.)',
  ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP() COMMENT 'Databricks ingestion timestamp'
)
USING DELTA
PARTITIONED BY (DATE(event_time))
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.checkpoint.writeStatsAsJson' = 'true',
  'delta.checkpoint.writeStatsAsStruct' = 'true',
  'delta.logRetentionDuration' = 'interval 30 days',
  'delta.deletedFileRetentionDuration' = 'interval 7 days',
  'comment' = 'Bronze layer: Raw OT events from Ignition via Zerobus Ingest'
);

-- ============================================================
-- Step 3: Create Silver Layer Table for Cleansed Events
-- ============================================================

CREATE TABLE IF NOT EXISTS main.ignition_ot_test.silver_events (
  event_time TIMESTAMP,
  tag_path STRING,
  asset_id STRING,
  asset_path STRING,
  value DOUBLE COMMENT 'Cleansed numeric value',
  quality STRING,
  source_system STRING,
  site STRING,
  line STRING,
  unit STRING,
  engineering_units STRING,
  is_valid BOOLEAN COMMENT 'Data quality validation flag',
  processed_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
USING DELTA
PARTITIONED BY (DATE(event_time))
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'comment' = 'Silver layer: Cleansed and validated OT events'
);

-- ============================================================
-- Step 4: Create Gold Layer Aggregated Metrics Table
-- ============================================================

CREATE TABLE IF NOT EXISTS main.ignition_ot_test.gold_tag_metrics (
  window_start TIMESTAMP,
  window_end TIMESTAMP,
  tag_path STRING,
  asset_id STRING,
  avg_value DOUBLE,
  min_value DOUBLE,
  max_value DOUBLE,
  stddev_value DOUBLE,
  event_count BIGINT,
  quality_good_pct DOUBLE,
  last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
USING DELTA
PARTITIONED BY (DATE(window_start))
TBLPROPERTIES (
  'comment' = 'Gold layer: Aggregated tag metrics for analytics'
);

-- ============================================================
-- Step 5: Create View for Easy Querying
-- ============================================================

CREATE OR REPLACE VIEW main.ignition_ot_test.vw_recent_events AS
SELECT 
  event_time,
  tag_path,
  asset_id,
  COALESCE(
    CAST(numeric_value AS STRING),
    string_value,
    CAST(boolean_value AS STRING),
    CAST(integer_value AS STRING)
  ) as value,
  quality,
  source_system,
  ingestion_timestamp,
  ROUND((UNIX_TIMESTAMP(ingestion_timestamp) - UNIX_TIMESTAMP(event_time)), 2) as latency_seconds
FROM main.ignition_ot_test.bronze_events
WHERE event_time >= CURRENT_TIMESTAMP() - INTERVAL 1 HOUR
ORDER BY event_time DESC;

-- ============================================================
-- Step 6: Grant Permissions (for service principals)
-- ============================================================

-- Note: When you create OAuth service principal, grant these permissions:
-- GRANT CREATE, MODIFY, SELECT, READ_METADATA 
-- ON SCHEMA main.ignition_ot_test 
-- TO SERVICE_PRINCIPAL '<client-id>';

-- GRANT MODIFY, SELECT 
-- ON TABLE main.ignition_ot_test.bronze_events 
-- TO SERVICE_PRINCIPAL '<client-id>';

-- ============================================================
-- Step 7: Test Queries
-- ============================================================

-- Check recent events
SELECT * FROM main.ignition_ot_test.vw_recent_events LIMIT 10;

-- Check ingestion statistics
SELECT 
  DATE_TRUNC('minute', event_time) as minute,
  COUNT(*) as event_count,
  COUNT(DISTINCT tag_path) as unique_tags,
  COUNT(DISTINCT asset_id) as unique_assets
FROM main.ignition_ot_test.bronze_events
WHERE event_time >= CURRENT_TIMESTAMP() - INTERVAL 1 HOUR
GROUP BY DATE_TRUNC('minute', event_time)
ORDER BY minute DESC;

-- Check data quality distribution
SELECT 
  quality,
  COUNT(*) as count,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM main.ignition_ot_test.bronze_events
WHERE event_time >= CURRENT_TIMESTAMP() - INTERVAL 1 DAY
GROUP BY quality;

-- Check latency
SELECT 
  AVG(UNIX_TIMESTAMP(ingestion_timestamp) - UNIX_TIMESTAMP(event_time)) as avg_latency_seconds,
  MAX(UNIX_TIMESTAMP(ingestion_timestamp) - UNIX_TIMESTAMP(event_time)) as max_latency_seconds,
  MIN(UNIX_TIMESTAMP(ingestion_timestamp) - UNIX_TIMESTAMP(event_time)) as min_latency_seconds
FROM main.ignition_ot_test.bronze_events
WHERE event_time >= CURRENT_TIMESTAMP() - INTERVAL 1 HOUR;

