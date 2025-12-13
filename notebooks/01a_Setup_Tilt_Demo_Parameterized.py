# Databricks notebook source
# MAGIC %md
# MAGIC # 01a - Tilt Demo Setup (Parameterized, Notebook)
# MAGIC
# MAGIC This notebook replaces running the parameterized SQL files in the SQL editor.
# MAGIC
# MAGIC It creates (based on widgets):
# MAGIC - Unity Catalog catalog + schema
# MAGIC - Bronze table: `{{catalog}}.{{schema}}.ot_events_bronze` (protobuf contract)
# MAGIC - Grants to your Service Principal (`{{sp}}`)
# MAGIC
# MAGIC ## Inputs
# MAGIC - `catalog`: e.g. `ignition_demo`
# MAGIC - `schema`: e.g. `tilt_ot`
# MAGIC - `sp`: Service Principal identifier accepted by UC grants (name or Application ID)

# COMMAND ----------
dbutils.widgets.text("catalog", "ignition_demo", "Catalog")
dbutils.widgets.text("schema", "tilt_ot", "Schema")
dbutils.widgets.text("sp", "pravin_zerobus", "Service Principal (name or app id)")
dbutils.widgets.dropdown("run_verify", "true", ["true", "false"], "Run verification queries")

# COMMAND ----------
def _bool(v: str) -> bool:
    return str(v).strip().lower() == "true"

catalog = dbutils.widgets.get("catalog").strip()
schema = dbutils.widgets.get("schema").strip()
sp = dbutils.widgets.get("sp").strip()
run_verify = _bool(dbutils.widgets.get("run_verify"))

bronze = f"{catalog}.{schema}.ot_events_bronze"
print("Catalog:", catalog)
print("Schema:", schema)
print("SP:", sp)
print("Bronze:", bronze)

# COMMAND ----------
# MAGIC %md
# MAGIC ## Create catalog + schema

# COMMAND ----------
spark.sql(f"CREATE CATALOG IF NOT EXISTS {catalog}")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}")

# COMMAND ----------
# MAGIC %md
# MAGIC ## Create Bronze table (fixed ingestion contract)
# MAGIC Must match `module/src/main/proto/ot_event.proto` (names + types + order).

# COMMAND ----------
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {bronze} (
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
""")

# COMMAND ----------
# MAGIC %md
# MAGIC ## Grants (minimum for ingestion)

# COMMAND ----------
def _grant(stmt: str):
    try:
        spark.sql(stmt)
        print("OK:", stmt)
    except Exception as e:
        print("FAILED:", stmt)
        print(str(e)[:600])
        raise

_grant(f"GRANT USE CATALOG ON CATALOG {catalog} TO `{sp}`")
_grant(f"GRANT USE SCHEMA ON SCHEMA {catalog}.{schema} TO `{sp}`")
_grant(f"GRANT SELECT, MODIFY ON TABLE {bronze} TO `{sp}`")

# COMMAND ----------
# MAGIC %md
# MAGIC ## Optional verification

# COMMAND ----------
if run_verify:
    display(spark.sql(f"SHOW SCHEMAS IN {catalog}"))
    display(spark.sql(f"SHOW TABLES IN {catalog}.{schema}"))
    display(spark.sql(f"DESCRIBE TABLE {bronze}"))
    display(spark.sql(f"SHOW GRANTS ON TABLE {bronze}"))


