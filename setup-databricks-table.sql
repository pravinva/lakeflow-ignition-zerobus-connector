-- Setup script for Databricks Delta table
-- Run this in Databricks SQL Warehouse or Notebook

-- Create catalog if needed (or use existing)
-- CREATE CATALOG IF NOT EXISTS ignition_ot;

-- Create schema for OT data
CREATE SCHEMA IF NOT EXISTS main.ignition_ot
COMMENT 'Operational Technology data from Ignition Gateway';

-- Create Bronze layer table for raw OT events
CREATE TABLE IF NOT EXISTS main.ignition_ot.bronze_events (
  event_time TIMESTAMP COMMENT 'Timestamp when tag value changed',
  tag_path STRING COMMENT 'Full Ignition tag path',
  asset_id STRING COMMENT 'Asset identifier',
  asset_path STRING COMMENT 'Asset hierarchy path',
  numeric_value DOUBLE COMMENT 'Numeric value for analog tags',
  string_value STRING COMMENT 'String value for text tags',
  boolean_value BOOLEAN COMMENT 'Boolean value for digital tags',
  integer_value BIGINT COMMENT 'Integer value for counter tags',
  value_string STRING COMMENT 'Value as string (all types)',
  quality STRING COMMENT 'Ignition quality code',
  source_system STRING COMMENT 'Source Gateway identifier',
  site STRING COMMENT 'Site/location (optional)',
  line STRING COMMENT 'Production line (optional)',
  unit STRING COMMENT 'Equipment unit (optional)',
  tag_description STRING COMMENT 'Tag description (optional)',
  engineering_units STRING COMMENT 'Engineering units (optional)'
)
USING DELTA
PARTITIONED BY (DATE(event_time))
COMMENT 'Raw OT events from Ignition Gateway via Zerobus Ingest'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);

-- Optimize table for common queries
OPTIMIZE main.ignition_ot.bronze_events
ZORDER BY (tag_path, source_system);

-- Grant permissions (replace with your service principal name)
-- GRANT MODIFY, SELECT ON TABLE main.ignition_ot.bronze_events TO `ignition-service-principal`;
-- GRANT USAGE ON SCHEMA main.ignition_ot TO `ignition-service-principal`;
-- GRANT USAGE ON CATALOG main TO `ignition-service-principal`;

SELECT 'Table main.ignition_ot.bronze_events created successfully!' as status;

