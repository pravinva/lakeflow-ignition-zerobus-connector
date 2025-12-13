-- Tilt Renewables onboarding - ONE-SHOT demo setup (Ignition demo defaults)
--
-- Creates:
--   - Catalog: ignition_demo
--   - Schema : tilt_ot
--   - Bronze table: ignition_demo.tilt_ot.ot_events_bronze  (protobuf-aligned contract)
--   - Grants for your Service Principal
--
-- REQUIRED: Replace ONLY this value:
--   {{sp}} : your Databricks Service Principal identifier (name OR Application ID, whichever your workspace accepts)
--
-- Example:
--   {{sp}} = pravin_zerobus
--   OR
--   {{sp}} = 52393ed8-ea22-4830-a6ef-6b6545e6be5f
--
-- Note: Some workspaces require the Application ID (UUID) form. Prefer UUID.
--
-- IMPORTANT:
-- The Bronze schema MUST match `module/src/main/proto/ot_event.proto` exactly (names + types + order).

-- ============================================================================
-- 1) Catalog + schema
-- ============================================================================

CREATE CATALOG IF NOT EXISTS ignition_demo;
CREATE SCHEMA IF NOT EXISTS ignition_demo.tilt_ot;

-- ============================================================================
-- 2) Bronze table (fixed ingestion contract)
-- ============================================================================

CREATE TABLE IF NOT EXISTS ignition_demo.tilt_ot.ot_events_bronze (
  event_id STRING,
  event_time TIMESTAMP,
  tag_path STRING,
  tag_provider STRING,
  numeric_value DOUBLE,
  string_value STRING,
  boolean_value BOOLEAN,
  quality STRING,
  quality_code INT,
  source_system STRING,
  ingestion_timestamp BIGINT,
  data_type STRING,
  alarm_state STRING,
  alarm_priority INT
)
USING DELTA
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
)
COMMENT 'Tilt demo: raw OT events from Ignition via Zerobus (protobuf contract)';

-- ============================================================================
-- 3) Grants (minimum for ingestion)
-- ============================================================================

GRANT USE CATALOG ON CATALOG ignition_demo TO `{{sp}}`;
GRANT USE SCHEMA  ON SCHEMA ignition_demo.tilt_ot TO `{{sp}}`;
GRANT SELECT, MODIFY ON TABLE ignition_demo.tilt_ot.ot_events_bronze TO `{{sp}}`;

-- ============================================================================
-- 4) Quick checks
-- ============================================================================

SHOW SCHEMAS IN ignition_demo;
SHOW TABLES IN ignition_demo.tilt_ot;
DESCRIBE TABLE ignition_demo.tilt_ot.ot_events_bronze;
SHOW GRANTS ON TABLE ignition_demo.tilt_ot.ot_events_bronze;


