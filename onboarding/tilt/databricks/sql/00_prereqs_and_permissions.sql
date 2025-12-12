-- Tilt Renewables onboarding - prerequisites & permissions
--
-- Replace placeholders:
--   {{catalog}}  : Unity Catalog catalog name (e.g., tilt_ot)
--   {{schema}}   : schema/database name (e.g., bronze)
--   {{sp}}       : service principal name or id used by the Ignition module

CREATE CATALOG IF NOT EXISTS {{catalog}};
CREATE SCHEMA IF NOT EXISTS {{catalog}}.{{schema}};

-- Minimal grants for ingestion into the target schema/table.
GRANT USE CATALOG ON CATALOG {{catalog}} TO `{{sp}}`;
GRANT USE SCHEMA ON SCHEMA {{catalog}}.{{schema}} TO `{{sp}}`;


