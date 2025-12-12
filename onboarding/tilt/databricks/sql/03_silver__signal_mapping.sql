-- Tilt Renewables onboarding - Silver: signal mapping (the flexibility lever)
--
-- Purpose:
--   Map raw Ignition tag paths (and/or patterns) into renewables concepts:
--     site, asset_type, asset_id, signal_name, unit, and "signal_role".
--
-- Why this table exists:
--   You usually *don't* control customer tag naming across plants/OEMs.
--   Instead of forcing connector schema changes, you normalize in Silver
--   using this mapping table.
--
-- Replace placeholders:
--   {{catalog}}  : Unity Catalog catalog name
--   {{schema}}   : schema/database name

CREATE TABLE IF NOT EXISTS {{catalog}}.{{schema}}.silver_signal_mapping (
  -- Identity / tenancy
  source_system STRING,   -- matches module config sourceSystemId (can be NULL for "all")

  -- Matching
  match_type STRING,      -- 'exact' | 'prefix' | 'regex'
  match_value STRING,     -- exact tag_path OR prefix OR regex

  -- Normalized dimensions
  site STRING,
  asset_type STRING,      -- WIND_TURBINE | SOLAR_INVERTER | BESS_RACK | SUBSTATION | OTHER
  asset_id STRING,
  signal_name STRING,     -- e.g. ACTIVE_POWER_KW, WIND_SPEED_MS, SOC_PCT
  unit STRING,            -- e.g. kW, m/s, %

  -- Optional: role used by Gold/ML templates
  -- Examples: ACTIVE_POWER, AVAILABILITY, CURTAILMENT_ACTIVE, ALARM_STATE, HEALTH
  signal_role STRING,

  -- Operational
  enabled BOOLEAN,
  notes STRING
)
USING DELTA;

-- Optional seed examples (safe to delete)
-- INSERT INTO {{catalog}}.{{schema}}.silver_signal_mapping
-- SELECT * FROM VALUES
--   ('tilt-siteA-ignition','prefix','[default]SiteA/Wind/Turbine07/Power', 'SiteA','WIND_TURBINE','T07','ACTIVE_POWER_KW','kW','ACTIVE_POWER', true, 'example'),
--   ('tilt-siteA-ignition','prefix','[default]SiteA/Wind/Turbine07/WindSpeed', 'SiteA','WIND_TURBINE','T07','WIND_SPEED_MS','m/s','WIND_SPEED', true, 'example'),
--   ('tilt-siteB-ignition','prefix','[default]SiteB/Solar/Inverter12/ACPower', 'SiteB','SOLAR_INVERTER','INV12','ACTIVE_POWER_KW','kW','ACTIVE_POWER', true, 'example'),
--   ('tilt-siteC-ignition','prefix','[default]SiteC/BESS/Rack03/SOC', 'SiteC','BESS_RACK','RACK03','SOC_PCT','%','SOC', true, 'example')
-- AS (source_system, match_type, match_value, site, asset_type, asset_id, signal_name, unit, signal_role, enabled, notes);


