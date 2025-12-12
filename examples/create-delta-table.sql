-- Create Delta Table for Ignition OT Events (Zerobus Ingest Contract)
-- This script creates the target Unity Catalog table for receiving Zerobus events.
--
-- IMPORTANT:
-- The table schema MUST match `module/src/main/proto/ot_event.proto` exactly.
-- Column names, types, and order must match or Zerobus will reject ingestion.

-- ============================================================================
-- Bronze Layer: Raw OT Events (Fixed schema)
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS dev_ot.bronze;

CREATE TABLE IF NOT EXISTS dev_ot.bronze.ot_events_bronze (
  event_id STRING COMMENT 'Unique event identifier',
  event_time TIMESTAMP COMMENT 'Timestamp when the tag value changed',
  tag_path STRING COMMENT 'Full Ignition tag path (e.g., [default]Conveyor1/Speed)',
  tag_provider STRING COMMENT 'Ignition tag provider (e.g., default)',
  numeric_value DOUBLE COMMENT 'Numeric value (if applicable)',
  string_value STRING COMMENT 'String value (if applicable)',
  boolean_value BOOLEAN COMMENT 'Boolean value (if applicable)',
  quality STRING COMMENT 'Quality as string',
  quality_code INT COMMENT 'Ignition numeric quality code',
  source_system STRING COMMENT 'Source Ignition Gateway identifier (sourceSystemId)',
  ingestion_timestamp BIGINT COMMENT 'Ingestion timestamp (epoch micros, client-set)',
  data_type STRING COMMENT 'Original data type',
  alarm_state STRING COMMENT 'Alarm state (optional)',
  alarm_priority INT COMMENT 'Alarm priority (optional)'
)
USING DELTA
PARTITIONED BY (DATE(event_time))
COMMENT 'Raw OT events from Ignition via Zerobus (protobuf-aligned contract)'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);

-- ============================================================================
-- Create indexes for common query patterns
-- ============================================================================

-- Z-order optimize for common filters
OPTIMIZE dev_ot.bronze.ot_events_bronze
ZORDER BY (source_system, tag_path);

-- ============================================================================
-- Silver Layer: Aggregated Events (example)
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS dev_ot.silver;

CREATE TABLE IF NOT EXISTS dev_ot.silver.ot_events_1min (
  window_start TIMESTAMP COMMENT '1-minute window start time',
  window_end TIMESTAMP COMMENT '1-minute window end time',
  tag_path STRING,
  tag_provider STRING,
  source_system STRING,
  
  -- Numeric aggregations
  min_value DOUBLE COMMENT 'Minimum value in window',
  max_value DOUBLE COMMENT 'Maximum value in window',
  avg_value DOUBLE COMMENT 'Average value in window',
  last_value DOUBLE COMMENT 'Last value in window',
  
  -- Statistics
  event_count BIGINT COMMENT 'Number of events in window',
  good_quality_count BIGINT COMMENT 'Number of events with GOOD quality',
  quality_percentage DOUBLE COMMENT 'Percentage of events with GOOD quality'
)
USING DELTA
PARTITIONED BY (DATE(window_start))
COMMENT '1-minute aggregated OT events (example)'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);

-- Example aggregation refresh (run as a job, or convert to a view)
INSERT OVERWRITE dev_ot.silver.ot_events_1min
SELECT
  window.start AS window_start,
  window.end AS window_end,
  tag_path,
  tag_provider,
  source_system,
  MIN(numeric_value) AS min_value,
  MAX(numeric_value) AS max_value,
  AVG(numeric_value) AS avg_value,
  max_by(numeric_value, event_time) AS last_value,
  COUNT(*) AS event_count,
  SUM(CASE WHEN quality_code = 192 THEN 1 ELSE 0 END) AS good_quality_count,
  (SUM(CASE WHEN quality_code = 192 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) AS quality_percentage
FROM dev_ot.bronze.ot_events_bronze
WHERE numeric_value IS NOT NULL
GROUP BY window(event_time, '1 minute'), tag_path, tag_provider, source_system;

-- ============================================================================
-- Grant Permissions
-- ============================================================================

-- Grant write access to service principal
GRANT MODIFY, SELECT ON TABLE dev_ot.bronze.ot_events_bronze
TO `ignition-zerobus-connector`;

GRANT MODIFY, SELECT ON TABLE dev_ot.silver.ot_events_1min
TO `ignition-zerobus-connector`;

-- Grant usage on schema and catalog
GRANT USAGE ON SCHEMA dev_ot.bronze TO `ignition-zerobus-connector`;
GRANT USAGE ON SCHEMA dev_ot.silver TO `ignition-zerobus-connector`;
GRANT USAGE ON CATALOG dev_ot TO `ignition-zerobus-connector`;

-- ============================================================================
-- Create View for Easy Querying
-- ============================================================================

CREATE OR REPLACE VIEW dev_ot.v_latest_tag_values AS
SELECT 
  tag_path,
  COALESCE(
    CAST(numeric_value AS STRING),
    string_value,
    CAST(boolean_value AS STRING)
  ) AS current_value,
  quality,
  event_time AS last_update,
  source_system
FROM (
  SELECT *,
    ROW_NUMBER() OVER (PARTITION BY tag_path ORDER BY event_time DESC) AS rn
  FROM dev_ot.bronze.ot_events_bronze
) WHERE rn = 1;

-- Grant access to view
GRANT SELECT ON VIEW dev_ot.v_latest_tag_values TO `ignition-zerobus-connector`;

-- ============================================================================
-- Example Queries
-- ============================================================================

-- Query 1: Recent events (last 10 minutes)
-- SELECT * FROM dev_ot.bronze.ot_events_bronze
-- WHERE event_time > current_timestamp() - INTERVAL 10 MINUTES
-- ORDER BY event_time DESC
-- LIMIT 100;

-- Query 2: Event count by tag (last hour)
-- SELECT 
--   tag_path,
--   COUNT(*) as event_count,
--   AVG(numeric_value) as avg_value,
--   MAX(event_time) as last_event
-- FROM dev_ot.bronze.ot_events_bronze
-- WHERE event_time > current_timestamp() - INTERVAL 1 HOUR
--   AND numeric_value IS NOT NULL
-- GROUP BY tag_path
-- ORDER BY event_count DESC;

-- Query 3: Data quality summary
-- SELECT 
--   DATE(event_time) as event_date,
--   quality,
--   COUNT(*) as event_count,
--   COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY DATE(event_time)) as percentage
-- FROM dev_ot.bronze.ot_events_bronze
-- WHERE event_time > current_timestamp() - INTERVAL 7 DAYS
-- GROUP BY DATE(event_time), quality
-- ORDER BY event_date DESC, event_count DESC;

-- Query 4: Current tag values
-- SELECT * FROM dev_ot.v_latest_tag_values
-- ORDER BY last_update DESC
-- LIMIT 100;

