-- AGL Fleet Simulator - Databricks catalog/schema setup
-- Run this in a Databricks SQL Warehouse or notebook before starting the simulator.
--
-- IMPORTANT: Run as a user that has CREATE CATALOG on the metastore (e.g. workspace admin).
-- The app/service principal (agl-demo profile) does not have CREATE CATALOG; run this once
-- in the SQL Editor or with a user profile, then the SP can use the catalog.
--
-- Creates:
--   __CATALOG__              catalog (managed location below)
--   __CATALOG__.__SCHEMA__   schema
--   __CATALOG__.__SCHEMA__.raw_tags  (Bronze - Zerobus writes here)
--   Asset Framework + SDP site schemas (agl_ot, saint_ot, tilt_ot) in same catalog.
--
-- Placeholders __CATALOG__ and __SCHEMA__ are replaced by run_setup_sql.py from env
-- (CATALOG, SCHEMA; defaults agl_demo, ot). After running this, run setup_asset_framework.sql.

-- 0. Catalog and schema (managed location for catalog storage)
CREATE CATALOG IF NOT EXISTS __CATALOG__
  MANAGED LOCATION 'abfss://data@stdbwdaveokdata.dfs.core.windows.net/agl';
CREATE SCHEMA IF NOT EXISTS __CATALOG__.__SCHEMA__
  COMMENT 'OT data from Ignition via Zerobus connector';

-- 1. Bronze: Zerobus landing table - schema matches OTEvent protobuf exactly.
--    Zerobus may auto-create this table, but pre-creating ensures column comments and correct types.
--    Compression: DBR 16+ uses ZSTD by default for new managed tables; we do not set it explicitly.
--    Primary key improves dedup/merge queries.
--    Drop leftover view or table so we can (re)create the table (raw_tags was a compat view; now it's the table).
DROP VIEW IF EXISTS __CATALOG__.__SCHEMA__.raw_tags;
DROP TABLE IF EXISTS __CATALOG__.__SCHEMA__.raw_tags;
CREATE TABLE IF NOT EXISTS __CATALOG__.__SCHEMA__.raw_tags (
  event_id              STRING      NOT NULL  COMMENT 'UUID per event',
  event_time            BIGINT      NOT NULL  COMMENT 'Source timestamp (micros since epoch)',
  tag_path              STRING      NOT NULL  COMMENT 'Full Ignition tag path e.g. [agl_bess]AGL/Australia/NSW/Tomago/Site01/BESS01/Telemetry/SoC_pct',
  tag_provider          STRING      NOT NULL  COMMENT 'Ignition tag provider extracted from path e.g. agl_bess',
  numeric_value         DOUBLE                COMMENT 'Value for numeric tags',
  string_value          STRING                COMMENT 'Value for string tags',
  boolean_value         BOOLEAN               COMMENT 'Value for boolean tags',
  quality               STRING                COMMENT 'Quality string e.g. Good',
  quality_code          INT                   COMMENT 'OPC quality code (192 = Good)',
  source_system         STRING                COMMENT 'Source gateway identifier',
  ingestion_timestamp   BIGINT                COMMENT 'Ingestion timestamp (micros since epoch)',
  data_type             STRING                COMMENT 'Original data type: DOUBLE, STRING, BOOLEAN',
  alarm_state           STRING                COMMENT 'Alarm state if applicable',
  alarm_priority        INT                   COMMENT 'Alarm priority if applicable',
  sdt_compressed        BOOLEAN               COMMENT 'True if survived SDT compression',
  compression_ratio    DOUBLE                COMMENT 'Running ratio at emission; 0 when SDT off',
  sdt_enabled           BOOLEAN               COMMENT 'Gateway config: SDT was on when this event was sent',
  batch_bytes_sent      BIGINT                COMMENT 'Size in bytes of the batch this event was sent in (demo observability)',
  CONSTRAINT raw_tags_pk PRIMARY KEY (event_id)
)
-- NOTE: Do NOT use CLUSTER BY here. Zerobus Ingest rejects stream creation (INTERNAL/1521)
-- on tables with liquid clustering enabled. Add clustering on downstream silver/gold tables instead.
TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true')
COMMENT 'Bronze layer: raw OT tag events from Ignition via Zerobus (matches OTEvent protobuf)';

-- 1b. Enable CDF on raw_tags if table already existed (idempotent).
ALTER TABLE __CATALOG__.__SCHEMA__.raw_tags SET TBLPROPERTIES (delta.enableChangeDataFeed = 'true');

-- 1c. For existing raw_tags created without PK (run once).
-- ALTER TABLE __CATALOG__.__SCHEMA__.raw_tags ADD CONSTRAINT raw_tags_pk PRIMARY KEY (event_id);
--
-- WARNING: Do NOT enable liquid clustering while Zerobus is writing to this table.
-- Zerobus Ingest rejects stream creation (INTERNAL/1521) on CLUSTER BY tables.
-- See onboarding/ZEROBUS_CLUSTER_BY_BUG.md for full compatibility matrix.

-- 2. Asset Framework tables
--    See pipelines/sql/setup_asset_framework.sql for full DDL + seed data.
--    Repeated here so this single script bootstraps everything.

CREATE TABLE IF NOT EXISTS __CATALOG__.__SCHEMA__.asset_templates (
  template_id STRING NOT NULL,
  template_name STRING NOT NULL,
  description STRING,
  base_asset_type STRING NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  CONSTRAINT asset_templates_pk PRIMARY KEY (template_id)
)
TBLPROPERTIES ('delta.feature.allowColumnDefaults' = 'supported');

CREATE TABLE IF NOT EXISTS __CATALOG__.__SCHEMA__.template_attributes (
  attribute_id STRING NOT NULL,
  template_id STRING NOT NULL,
  attribute_name STRING NOT NULL,
  data_type STRING NOT NULL,
  unit STRING,
  default_value STRING,
  is_required BOOLEAN DEFAULT false,
  sort_order INT DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  CONSTRAINT template_attributes_pk PRIMARY KEY (attribute_id),
  CONSTRAINT template_attributes_fk FOREIGN KEY (template_id) REFERENCES __CATALOG__.__SCHEMA__.asset_templates(template_id)
)
TBLPROPERTIES ('delta.feature.allowColumnDefaults' = 'supported');

CREATE TABLE IF NOT EXISTS __CATALOG__.__SCHEMA__.asset_hierarchy (
  asset_id STRING NOT NULL,
  parent_asset_id STRING,
  asset_name STRING NOT NULL,
  asset_type STRING NOT NULL,
  template_id STRING,
  site_name STRING,
  description STRING,
  capacity_mw DOUBLE            COMMENT 'Rated capacity in MW (equipment only)',
  latitude DOUBLE               COMMENT 'GPS latitude for map display',
  longitude DOUBLE              COMMENT 'GPS longitude for map display',
  tag_count INT                 COMMENT 'Number of streaming tags for this asset',
  active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  CONSTRAINT asset_hierarchy_pk PRIMARY KEY (asset_id),
  CONSTRAINT asset_hierarchy_template_fk FOREIGN KEY (template_id) REFERENCES __CATALOG__.__SCHEMA__.asset_templates(template_id)
)
TBLPROPERTIES ('delta.feature.allowColumnDefaults' = 'supported');

CREATE TABLE IF NOT EXISTS __CATALOG__.__SCHEMA__.asset_attribute_values (
  asset_id STRING NOT NULL,
  attribute_id STRING NOT NULL,
  value STRING,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  CONSTRAINT asset_attribute_values_pk PRIMARY KEY (asset_id, attribute_id),
  CONSTRAINT asset_attr_values_asset_fk FOREIGN KEY (asset_id) REFERENCES __CATALOG__.__SCHEMA__.asset_hierarchy(asset_id),
  CONSTRAINT asset_attr_values_attr_fk FOREIGN KEY (attribute_id) REFERENCES __CATALOG__.__SCHEMA__.template_attributes(attribute_id)
)
TBLPROPERTIES ('delta.feature.allowColumnDefaults' = 'supported');

-- 2b. SDT configuration per tag pattern (used by app Compression page tuning panel)
CREATE TABLE IF NOT EXISTS __CATALOG__.__SCHEMA__.sdt_config (
  tag_pattern       STRING      NOT NULL COMMENT 'Glob pattern matching tag names (e.g. */temperature_c)',
  comp_dev          DOUBLE               COMMENT 'Compression deviation (engineering units)',
  comp_dev_percent  DOUBLE               COMMENT 'CompDev as % of tag span',
  comp_max_seconds  INT                  COMMENT 'Max time before forcing an archive event',
  comp_min_seconds  INT                  COMMENT 'Min time between archived events'
)
COMMENT 'Swinging Door Trending compression configuration per tag pattern';
MERGE INTO __CATALOG__.__SCHEMA__.sdt_config AS target
USING (
  SELECT * FROM VALUES
    ('*/temperature_c',  0.5,  NULL, 600, 0),
    ('*/power_kw',       NULL, 1.0,  600, 0),
    ('*/soc_pct',        0.5,  NULL, 600, 0)
  AS defaults(tag_pattern, comp_dev, comp_dev_percent, comp_max_seconds, comp_min_seconds)
) AS source
ON target.tag_pattern = source.tag_pattern
WHEN NOT MATCHED THEN INSERT *;

-- 3. Volume for Python wheels (e.g. agl_analytics) – reference in jobs/apps as:
--    /Volumes/__CATALOG__/__SCHEMA__/wheels/agl_analytics-0.1.0-py3-none-any.whl
CREATE VOLUME IF NOT EXISTS __CATALOG__.__SCHEMA__.wheels
  COMMENT 'Python wheels for jobs and apps (e.g. agl_analytics)';

-- 3b. SDP pipeline schemas: agl_ot, saint_ot, tilt_ot (silver_signal_mapping + silver_asset_registry)
CREATE SCHEMA IF NOT EXISTS __CATALOG__.agl_ot COMMENT 'AGL Silver/Gold for SDP pipeline';
CREATE TABLE IF NOT EXISTS __CATALOG__.agl_ot.silver_asset_registry (
  asset_id STRING,
  parent_asset_id STRING,
  asset_type STRING,
  site STRING,
  display_name STRING,
  active BOOLEAN
) USING DELTA;
CREATE TABLE IF NOT EXISTS __CATALOG__.agl_ot.silver_signal_mapping (
  tag_path STRING,
  asset_id STRING,
  signal_name STRING,
  unit STRING,
  scale DOUBLE,
  offset DOUBLE,
  source_domain STRING,
  active BOOLEAN
) USING DELTA;

CREATE SCHEMA IF NOT EXISTS __CATALOG__.saint_ot COMMENT 'Saint Gobain Silver (placeholder for SDP union)';
CREATE TABLE IF NOT EXISTS __CATALOG__.saint_ot.silver_signal_mapping (
  tag_path STRING,
  asset_id STRING,
  signal_name STRING,
  unit STRING,
  scale DOUBLE,
  offset DOUBLE,
  source_domain STRING,
  active BOOLEAN
) USING DELTA;

CREATE SCHEMA IF NOT EXISTS __CATALOG__.tilt_ot COMMENT 'Tilt Silver (placeholder for SDP union)';
CREATE TABLE IF NOT EXISTS __CATALOG__.tilt_ot.silver_signal_mapping (
  tag_path STRING,
  asset_id STRING,
  signal_name STRING,
  unit STRING,
  scale DOUBLE,
  offset DOUBLE,
  source_domain STRING,
  active BOOLEAN
) USING DELTA;

-- 4. Service Principal grants for Zerobus connector + app
--    Set SP_APPLICATION_ID env or replace __SP_APPLICATION_ID__ in this file.
GRANT USE CATALOG ON CATALOG __CATALOG__ TO `__SP_APPLICATION_ID__`;
GRANT USE SCHEMA ON SCHEMA __CATALOG__.__SCHEMA__ TO `__SP_APPLICATION_ID__`;
GRANT MODIFY, SELECT ON TABLE __CATALOG__.__SCHEMA__.raw_tags TO `__SP_APPLICATION_ID__`;
GRANT MODIFY, SELECT ON TABLE __CATALOG__.__SCHEMA__.asset_templates TO `__SP_APPLICATION_ID__`;
GRANT MODIFY, SELECT ON TABLE __CATALOG__.__SCHEMA__.template_attributes TO `__SP_APPLICATION_ID__`;
GRANT MODIFY, SELECT ON TABLE __CATALOG__.__SCHEMA__.asset_hierarchy TO `__SP_APPLICATION_ID__`;
GRANT MODIFY, SELECT ON TABLE __CATALOG__.__SCHEMA__.asset_attribute_values TO `__SP_APPLICATION_ID__`;
GRANT MODIFY, SELECT ON TABLE __CATALOG__.__SCHEMA__.sdt_config TO `__SP_APPLICATION_ID__`;
GRANT READ VOLUME ON VOLUME __CATALOG__.__SCHEMA__.wheels TO `__SP_APPLICATION_ID__`;
GRANT USE SCHEMA ON SCHEMA __CATALOG__.agl_ot TO `__SP_APPLICATION_ID__`;
GRANT MODIFY, SELECT ON TABLE __CATALOG__.agl_ot.silver_asset_registry TO `__SP_APPLICATION_ID__`;
GRANT MODIFY, SELECT ON TABLE __CATALOG__.agl_ot.silver_signal_mapping TO `__SP_APPLICATION_ID__`;
GRANT USE SCHEMA ON SCHEMA __CATALOG__.saint_ot TO `__SP_APPLICATION_ID__`;
GRANT MODIFY, SELECT ON TABLE __CATALOG__.saint_ot.silver_signal_mapping TO `__SP_APPLICATION_ID__`;
GRANT USE SCHEMA ON SCHEMA __CATALOG__.tilt_ot TO `__SP_APPLICATION_ID__`;
GRANT MODIFY, SELECT ON TABLE __CATALOG__.tilt_ot.silver_signal_mapping TO `__SP_APPLICATION_ID__`;
