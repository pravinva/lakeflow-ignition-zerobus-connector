# Databricks notebook source
# MAGIC %md
# MAGIC # Setup Databricks for Ignition Zerobus Connector
# MAGIC 
# MAGIC **Purpose**: Create catalog, schema, table, and grant permissions to Service Principal
# MAGIC 
# MAGIC **Prerequisites**:
# MAGIC - Admin access to Databricks workspace
# MAGIC - Service Principal created in Account Console
# MAGIC - Service Principal UUID (not the client ID!)
# MAGIC 
# MAGIC **What this notebook does**:
# MAGIC 1. Creates Unity Catalog (if doesn't exist)
# MAGIC 2. Creates schema (if doesn't exist)
# MAGIC 3. Creates Delta table with proper schema
# MAGIC 4. Enables Zerobus on the table
# MAGIC 5. Grants permissions to Service Principal
# MAGIC 6. Verifies setup

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration
# MAGIC 
# MAGIC Update these values for your environment:

# COMMAND ----------

# Configuration
CATALOG_NAME = "ignition_demo"
SCHEMA_NAME = "scada_data"
TABLE_NAME = "tag_events"

# Service Principal UUID (NOT the client ID!)
# Get this from: Account Console → Service Principals → UUID column
SERVICE_PRINCIPAL_UUID = "your-service-principal-uuid-here"  # e.g., "52393ed8-ea22-4830-a6ef-6b6545e6be5f"

# Full table name
FULL_TABLE_NAME = f"{CATALOG_NAME}.{SCHEMA_NAME}.{TABLE_NAME}"

print(f"Target Table: {FULL_TABLE_NAME}")
print(f"Service Principal UUID: {SERVICE_PRINCIPAL_UUID}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 1: Create Catalog

# COMMAND ----------

# DBTITLE 1,Create Catalog (if not exists)
spark.sql(f"""
CREATE CATALOG IF NOT EXISTS {CATALOG_NAME}
COMMENT 'Catalog for Ignition SCADA data via Zerobus'
""")

print(f"✅ Catalog '{CATALOG_NAME}' ready")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 2: Create Schema

# COMMAND ----------

# DBTITLE 1,Create Schema (if not exists)
spark.sql(f"""
CREATE SCHEMA IF NOT EXISTS {CATALOG_NAME}.{SCHEMA_NAME}
COMMENT 'Schema for tag events from Ignition'
""")

print(f"✅ Schema '{CATALOG_NAME}.{SCHEMA_NAME}' ready")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 3: Create Table with Zerobus Enabled

# COMMAND ----------

# DBTITLE 1,Create Delta Table with Zerobus
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {FULL_TABLE_NAME} (
  -- Tag identification
  tag_path STRING COMMENT 'Full tag path from Ignition (e.g., [default]Equipment/Pump01/Temperature)',
  tag_provider STRING COMMENT 'Tag provider name',
  tag_name STRING COMMENT 'Tag name without path',
  
  -- Value fields
  numeric_value DOUBLE COMMENT 'Numeric value for analog tags',
  string_value STRING COMMENT 'String value for string/text tags',
  boolean_value BOOLEAN COMMENT 'Boolean value for digital tags',
  
  -- Quality
  quality STRING COMMENT 'Tag quality (GOOD, BAD, UNCERTAIN)',
  quality_code INT COMMENT 'Numeric quality code',
  
  -- Metadata
  data_type STRING COMMENT 'Original data type (Int4, Float8, String, Boolean, etc)',
  source_system_id STRING COMMENT 'Identifier for the source Ignition Gateway',
  
  -- Timestamps
  event_time TIMESTAMP COMMENT 'When the tag value changed',
  ingest_time TIMESTAMP COMMENT 'When the event was ingested to Databricks',
  
  -- Partition key
  event_date DATE COMMENT 'Partition key - date of event_time'
)
USING DELTA
PARTITIONED BY (event_date)
TBLPROPERTIES (
  'delta.enableZerobus' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true',
  'description' = 'Real-time tag events from Ignition SCADA via Zerobus'
)
COMMENT 'OT/SCADA tag events streamed from Ignition Gateway'
""")

print(f"✅ Table '{FULL_TABLE_NAME}' created with Zerobus enabled")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 4: Grant Permissions to Service Principal
# MAGIC 
# MAGIC ⚠️ **Important**: Use the Service Principal UUID, not the client ID!

# COMMAND ----------

# DBTITLE 1,Grant USE CATALOG
spark.sql(f"""
GRANT USE CATALOG ON CATALOG {CATALOG_NAME} 
TO `{SERVICE_PRINCIPAL_UUID}`
""")
print(f"✅ Granted USE CATALOG on {CATALOG_NAME}")

# COMMAND ----------

# DBTITLE 1,Grant USE SCHEMA
spark.sql(f"""
GRANT USE SCHEMA ON SCHEMA {CATALOG_NAME}.{SCHEMA_NAME} 
TO `{SERVICE_PRINCIPAL_UUID}`
""")
print(f"✅ Granted USE SCHEMA on {CATALOG_NAME}.{SCHEMA_NAME}")

# COMMAND ----------

# DBTITLE 1,Grant MODIFY (for writing data)
spark.sql(f"""
GRANT MODIFY ON TABLE {FULL_TABLE_NAME} 
TO `{SERVICE_PRINCIPAL_UUID}`
""")
print(f"✅ Granted MODIFY on {FULL_TABLE_NAME}")

# COMMAND ----------

# DBTITLE 1,Grant SELECT (for reading data)
spark.sql(f"""
GRANT SELECT ON TABLE {FULL_TABLE_NAME} 
TO `{SERVICE_PRINCIPAL_UUID}`
""")
print(f"✅ Granted SELECT on {FULL_TABLE_NAME}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 5: Verify Setup

# COMMAND ----------

# DBTITLE 1,Verify Table Properties
table_properties = spark.sql(f"SHOW TBLPROPERTIES {FULL_TABLE_NAME}").collect()

print("Table Properties:")
for prop in table_properties:
    if 'zerobus' in prop.key.lower() or 'optimize' in prop.key.lower():
        print(f"  {prop.key}: {prop.value}")

# Check if Zerobus is enabled
zerobus_enabled = any(prop.key == 'delta.enableZerobus' and prop.value == 'true' for prop in table_properties)
if zerobus_enabled:
    print("\n✅ Zerobus is ENABLED on this table")
else:
    print("\n⚠️ Zerobus is NOT enabled - check table properties")

# COMMAND ----------

# DBTITLE 1,Verify Permissions
grants = spark.sql(f"SHOW GRANTS ON TABLE {FULL_TABLE_NAME}").collect()

print(f"\nGrants on {FULL_TABLE_NAME}:")
for grant in grants:
    if SERVICE_PRINCIPAL_UUID in str(grant):
        print(f"  ✅ {grant.privilege}")

# COMMAND ----------

# DBTITLE 1,Table Schema
display(spark.sql(f"DESCRIBE {FULL_TABLE_NAME}"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Step 6: Test Insert (Optional)

# COMMAND ----------

# DBTITLE 1,Insert Test Record
from datetime import datetime
from pyspark.sql import Row

# Create test record
test_data = [
    Row(
        tag_path="[default]Test/TestTag",
        tag_provider="default",
        tag_name="TestTag",
        numeric_value=123.45,
        string_value=None,
        boolean_value=None,
        quality="GOOD",
        quality_code=192,
        data_type="Float8",
        source_system_id="setup-notebook-test",
        event_time=datetime.now(),
        ingest_time=datetime.now(),
        event_date=datetime.now().date()
    )
]

# Insert
df = spark.createDataFrame(test_data)
df.write.format("delta").mode("append").saveAsTable(FULL_TABLE_NAME)

print("✅ Test record inserted")

# COMMAND ----------

# DBTITLE 1,Verify Test Record
display(spark.sql(f"""
SELECT * FROM {FULL_TABLE_NAME}
WHERE source_system_id = 'setup-notebook-test'
ORDER BY ingest_time DESC
"""))

# COMMAND ----------

# MAGIC %md
# MAGIC ## ✅ Setup Complete!
# MAGIC 
# MAGIC ### Next Steps:
# MAGIC 
# MAGIC 1. **Note your Workspace ID**: Check URL or workspace settings
# MAGIC 2. **Build Zerobus Endpoint**: `WORKSPACE_ID.zerobus.REGION.cloud.databricks.com`
# MAGIC 3. **Configure Ignition Module**: Use Service Principal client ID and secret
# MAGIC 4. **Create Event Stream**: In Ignition Designer
# MAGIC 5. **Start Streaming**: Enable Event Stream
# MAGIC 
# MAGIC ### Information for Module Configuration:
# MAGIC 
# MAGIC ```json
# MAGIC {
# MAGIC   "workspaceUrl": "https://your-workspace.cloud.databricks.com",
# MAGIC   "zerobusEndpoint": "WORKSPACE_ID.zerobus.REGION.cloud.databricks.com",
# MAGIC   "catalogName": "ignition_demo",
# MAGIC   "schemaName": "scada_data",
# MAGIC   "tableName": "tag_events"
# MAGIC }
# MAGIC ```
# MAGIC 
# MAGIC Run **02_Monitor_Data_Flow** notebook to verify data is arriving!

