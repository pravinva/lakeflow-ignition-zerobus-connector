-- Create Delta Table for Ignition OT Events
-- This script creates the target Unity Catalog table for receiving Zerobus events

-- ============================================================================
-- Bronze Layer: Raw OT Events
-- ============================================================================

CREATE TABLE IF NOT EXISTS dev_ot.bronze_ignition_events (
  -- Event metadata
  event_time TIMESTAMP COMMENT 'Timestamp when the tag value changed',
  tag_path STRING COMMENT 'Full Ignition tag path (e.g., [default]Conveyor1/Speed)',
  
  -- Asset information
  asset_id STRING COMMENT 'Asset identifier (extracted from tag path or metadata)',
  asset_path STRING COMMENT 'Asset hierarchy path (e.g., Plant1/Line2/Conveyor1)',
  
  -- Tag values (one of these will be populated based on data type)
  numeric_value DOUBLE COMMENT 'Numeric value for analog/integer tags',
  string_value STRING COMMENT 'String value for text tags',
  boolean_value BOOLEAN COMMENT 'Boolean value for digital tags',
  integer_value BIGINT COMMENT 'Integer value for counter/discrete tags',
  value_string STRING COMMENT 'Value as string (for consistency across all types)',
  
  -- Data quality
  quality STRING COMMENT 'Ignition quality code (GOOD, BAD, UNCERTAIN)',
  
  -- Source identification
  source_system STRING COMMENT 'Source Ignition Gateway identifier',
  site STRING COMMENT 'Site/location identifier (optional)',
  line STRING COMMENT 'Production line identifier (optional)',
  unit STRING COMMENT 'Equipment unit identifier (optional)',
  
  -- Additional metadata
  tag_description STRING COMMENT 'Tag description from Ignition (optional)',
  engineering_units STRING COMMENT 'Engineering units (e.g., PSI, RPM, °C) (optional)'
)
USING DELTA
PARTITIONED BY (DATE(event_time))
COMMENT 'Raw OT events from Ignition Gateway via Zerobus Ingest'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true',
  'delta.logRetentionDuration' = '30 days',
  'delta.deletedFileRetentionDuration' = '7 days'
);

-- ============================================================================
-- Create indexes for common query patterns
-- ============================================================================

-- Z-order optimize for common filters
OPTIMIZE dev_ot.bronze_ignition_events
ZORDER BY (tag_path, asset_id, source_system);

-- ============================================================================
-- Silver Layer: Aggregated Events
-- ============================================================================

CREATE TABLE IF NOT EXISTS dev_ot.silver_ignition_events_1min (
  window_start TIMESTAMP COMMENT '1-minute window start time',
  window_end TIMESTAMP COMMENT '1-minute window end time',
  tag_path STRING,
  asset_id STRING,
  asset_path STRING,
  source_system STRING,
  
  -- Numeric aggregations
  min_value DOUBLE COMMENT 'Minimum value in window',
  max_value DOUBLE COMMENT 'Maximum value in window',
  avg_value DOUBLE COMMENT 'Average value in window',
  first_value DOUBLE COMMENT 'First value in window',
  last_value DOUBLE COMMENT 'Last value in window',
  sum_value DOUBLE COMMENT 'Sum of values in window',
  
  -- Statistics
  event_count BIGINT COMMENT 'Number of events in window',
  good_quality_count BIGINT COMMENT 'Number of events with GOOD quality',
  bad_quality_count BIGINT COMMENT 'Number of events with BAD quality',
  quality_percentage DOUBLE COMMENT 'Percentage of events with GOOD quality',
  
  -- Additional metadata
  site STRING,
  line STRING,
  unit STRING,
  engineering_units STRING
)
USING DELTA
PARTITIONED BY (DATE(window_start))
COMMENT '1-minute aggregated OT events'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);

-- ============================================================================
-- Grant Permissions
-- ============================================================================

-- Grant write access to service principal
GRANT MODIFY, SELECT ON TABLE dev_ot.bronze_ignition_events 
TO `ignition-zerobus-connector`;

GRANT MODIFY, SELECT ON TABLE dev_ot.silver_ignition_events_1min 
TO `ignition-zerobus-connector`;

-- Grant usage on schema and catalog
GRANT USAGE ON SCHEMA dev_ot TO `ignition-zerobus-connector`;
GRANT USAGE ON CATALOG dev_ot TO `ignition-zerobus-connector`;

-- ============================================================================
-- Create View for Easy Querying
-- ============================================================================

CREATE OR REPLACE VIEW dev_ot.v_latest_tag_values AS
SELECT 
  tag_path,
  asset_id,
  asset_path,
  COALESCE(
    CAST(numeric_value AS STRING),
    string_value,
    CAST(boolean_value AS STRING),
    CAST(integer_value AS STRING)
  ) AS current_value,
  quality,
  event_time AS last_update,
  source_system,
  engineering_units
FROM (
  SELECT *,
    ROW_NUMBER() OVER (PARTITION BY tag_path ORDER BY event_time DESC) AS rn
  FROM dev_ot.bronze_ignition_events
) WHERE rn = 1;

-- Grant access to view
GRANT SELECT ON VIEW dev_ot.v_latest_tag_values TO `ignition-zerobus-connector`;

-- ============================================================================
-- Example Queries
-- ============================================================================

-- Query 1: Recent events (last 10 minutes)
-- SELECT * FROM dev_ot.bronze_ignition_events
-- WHERE event_time > current_timestamp() - INTERVAL 10 MINUTES
-- ORDER BY event_time DESC
-- LIMIT 100;

-- Query 2: Event count by tag (last hour)
-- SELECT 
--   tag_path,
--   COUNT(*) as event_count,
--   AVG(numeric_value) as avg_value,
--   MAX(event_time) as last_event
-- FROM dev_ot.bronze_ignition_events
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
-- FROM dev_ot.bronze_ignition_events
-- WHERE event_time > current_timestamp() - INTERVAL 7 DAYS
-- GROUP BY DATE(event_time), quality
-- ORDER BY event_date DESC, event_count DESC;

-- Query 4: Current tag values
-- SELECT * FROM dev_ot.v_latest_tag_values
-- ORDER BY last_update DESC
-- LIMIT 100;

