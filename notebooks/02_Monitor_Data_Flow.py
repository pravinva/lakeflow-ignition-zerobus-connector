# Databricks notebook source
# MAGIC %md
# MAGIC # Monitor Ignition Data Flow
# MAGIC 
# MAGIC **Purpose**: Real-time monitoring of tag events from Ignition
# MAGIC 
# MAGIC **What this notebook does**:
# MAGIC 1. Shows recent tag events
# MAGIC 2. Displays data flow rate
# MAGIC 3. Checks data quality
# MAGIC 4. Shows tag statistics
# MAGIC 5. Provides diagnostic queries

# COMMAND ----------

# MAGIC %md
# MAGIC ## Configuration

# COMMAND ----------

# Configuration
CATALOG_NAME = "ignition_demo"
SCHEMA_NAME = "scada_data"
TABLE_NAME = "tag_events"
FULL_TABLE_NAME = f"{CATALOG_NAME}.{SCHEMA_NAME}.{TABLE_NAME}"

print(f"Monitoring: {FULL_TABLE_NAME}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Current Status

# COMMAND ----------

# DBTITLE 1,Recent Events (Last 100)
# MAGIC %sql
# MAGIC SELECT 
# MAGIC   tag_path,
# MAGIC   numeric_value,
# MAGIC   string_value,
# MAGIC   boolean_value,
# MAGIC   quality,
# MAGIC   event_time,
# MAGIC   source_system_id
# MAGIC FROM ignition_demo.scada_data.tag_events
# MAGIC ORDER BY event_time DESC
# MAGIC LIMIT 100

# COMMAND ----------

# DBTITLE 1,Data Flow Rate (Events per Minute - Last Hour)
# MAGIC %sql
# MAGIC SELECT 
# MAGIC   date_trunc('minute', event_time) as minute,
# MAGIC   COUNT(*) as event_count
# MAGIC FROM ignition_demo.scada_data.tag_events
# MAGIC WHERE event_time >= current_timestamp() - INTERVAL 1 HOUR
# MAGIC GROUP BY date_trunc('minute', event_time)
# MAGIC ORDER BY minute DESC

# COMMAND ----------

# DBTITLE 1,Total Events by Source System
# MAGIC %sql
# MAGIC SELECT 
# MAGIC   source_system_id,
# MAGIC   COUNT(*) as total_events,
# MAGIC   MIN(event_time) as first_event,
# MAGIC   MAX(event_time) as last_event,
# MAGIC   COUNT(DISTINCT tag_path) as unique_tags
# MAGIC FROM ignition_demo.scada_data.tag_events
# MAGIC GROUP BY source_system_id
# MAGIC ORDER BY total_events DESC

# COMMAND ----------

# MAGIC %md
# MAGIC ## Tag Statistics

# COMMAND ----------

# DBTITLE 1,Most Active Tags (Last Hour)
# MAGIC %sql
# MAGIC SELECT 
# MAGIC   tag_path,
# MAGIC   COUNT(*) as event_count,
# MAGIC   AVG(numeric_value) as avg_value,
# MAGIC   MIN(numeric_value) as min_value,
# MAGIC   MAX(numeric_value) as max_value,
# MAGIC   MAX(event_time) as last_event
# MAGIC FROM ignition_demo.scada_data.tag_events
# MAGIC WHERE event_time >= current_timestamp() - INTERVAL 1 HOUR
# MAGIC   AND numeric_value IS NOT NULL
# MAGIC GROUP BY tag_path
# MAGIC ORDER BY event_count DESC
# MAGIC LIMIT 20

# COMMAND ----------

# DBTITLE 1,Tag Value Distribution
# MAGIC %sql
# MAGIC SELECT 
# MAGIC   tag_path,
# MAGIC   data_type,
# MAGIC   COUNT(*) as total_events,
# MAGIC   COUNT(DISTINCT numeric_value) as unique_numeric_values,
# MAGIC   COUNT(DISTINCT string_value) as unique_string_values,
# MAGIC   COUNT(DISTINCT boolean_value) as unique_boolean_values
# MAGIC FROM ignition_demo.scada_data.tag_events
# MAGIC WHERE event_time >= current_timestamp() - INTERVAL 1 HOUR
# MAGIC GROUP BY tag_path, data_type
# MAGIC ORDER BY total_events DESC

# COMMAND ----------

# MAGIC %md
# MAGIC ## Data Quality

# COMMAND ----------

# DBTITLE 1,Quality Distribution
# MAGIC %sql
# MAGIC SELECT 
# MAGIC   quality,
# MAGIC   COUNT(*) as event_count,
# MAGIC   COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () as percentage
# MAGIC FROM ignition_demo.scada_data.tag_events
# MAGIC WHERE event_time >= current_timestamp() - INTERVAL 1 HOUR
# MAGIC GROUP BY quality
# MAGIC ORDER BY event_count DESC

# COMMAND ----------

# DBTITLE 1,Bad Quality Events
# MAGIC %sql
# MAGIC SELECT 
# MAGIC   tag_path,
# MAGIC   quality,
# MAGIC   quality_code,
# MAGIC   numeric_value,
# MAGIC   event_time,
# MAGIC   source_system_id
# MAGIC FROM ignition_demo.scada_data.tag_events
# MAGIC WHERE quality != 'GOOD'
# MAGIC   AND event_time >= current_timestamp() - INTERVAL 1 HOUR
# MAGIC ORDER BY event_time DESC
# MAGIC LIMIT 100

# COMMAND ----------

# MAGIC %md
# MAGIC ## Latency Analysis

# COMMAND ----------

# DBTITLE 1,Ingest Latency (event_time to ingest_time)
# MAGIC %sql
# MAGIC SELECT 
# MAGIC   tag_path,
# MAGIC   AVG(unix_timestamp(ingest_time) - unix_timestamp(event_time)) as avg_latency_seconds,
# MAGIC   MIN(unix_timestamp(ingest_time) - unix_timestamp(event_time)) as min_latency_seconds,
# MAGIC   MAX(unix_timestamp(ingest_time) - unix_timestamp(event_time)) as max_latency_seconds,
# MAGIC   COUNT(*) as event_count
# MAGIC FROM ignition_demo.scada_data.tag_events
# MAGIC WHERE event_time >= current_timestamp() - INTERVAL 1 HOUR
# MAGIC GROUP BY tag_path
# MAGIC ORDER BY avg_latency_seconds DESC

# COMMAND ----------

# MAGIC %md
# MAGIC ## Time Series Visualization

# COMMAND ----------

# DBTITLE 1,Tag Values Over Time (Last Hour)
# MAGIC %sql
# MAGIC SELECT 
# MAGIC   event_time,
# MAGIC   tag_path,
# MAGIC   numeric_value
# MAGIC FROM ignition_demo.scada_data.tag_events
# MAGIC WHERE event_time >= current_timestamp() - INTERVAL 1 HOUR
# MAGIC   AND numeric_value IS NOT NULL
# MAGIC ORDER BY event_time

# COMMAND ----------

# MAGIC %md
# MAGIC ## Diagnostic Queries

# COMMAND ----------

# DBTITLE 1,Events Per Second (Real-time Rate)
# MAGIC %sql
# MAGIC SELECT 
# MAGIC   COUNT(*) / (UNIX_TIMESTAMP(MAX(event_time)) - UNIX_TIMESTAMP(MIN(event_time))) as events_per_second,
# MAGIC   COUNT(*) as total_events,
# MAGIC   MIN(event_time) as window_start,
# MAGIC   MAX(event_time) as window_end
# MAGIC FROM ignition_demo.scada_data.tag_events
# MAGIC WHERE event_time >= current_timestamp() - INTERVAL 5 MINUTES

# COMMAND ----------

# DBTITLE 1,Check for Gaps in Data
# MAGIC %sql
# MAGIC WITH time_series AS (
# MAGIC   SELECT 
# MAGIC     tag_path,
# MAGIC     event_time,
# MAGIC     LAG(event_time) OVER (PARTITION BY tag_path ORDER BY event_time) as prev_event_time
# MAGIC   FROM ignition_demo.scada_data.tag_events
# MAGIC   WHERE event_time >= current_timestamp() - INTERVAL 1 HOUR
# MAGIC )
# MAGIC SELECT 
# MAGIC   tag_path,
# MAGIC   event_time,
# MAGIC   prev_event_time,
# MAGIC   UNIX_TIMESTAMP(event_time) - UNIX_TIMESTAMP(prev_event_time) as gap_seconds
# MAGIC FROM time_series
# MAGIC WHERE UNIX_TIMESTAMP(event_time) - UNIX_TIMESTAMP(prev_event_time) > 60  -- Gaps > 1 minute
# MAGIC ORDER BY gap_seconds DESC
# MAGIC LIMIT 20

# COMMAND ----------

# DBTITLE 1,Table Size and Partitions
# MAGIC %sql
# MAGIC DESCRIBE DETAIL ignition_demo.scada_data.tag_events

# COMMAND ----------

# MAGIC %md
# MAGIC ## Summary Dashboard

# COMMAND ----------

# DBTITLE 1,Overall Health Check
# MAGIC %sql
# MAGIC SELECT 
# MAGIC   '📊 Total Events' as metric,
# MAGIC   FORMAT_NUMBER(COUNT(*), 0) as value
# MAGIC FROM ignition_demo.scada_data.tag_events
# MAGIC 
# MAGIC UNION ALL
# MAGIC 
# MAGIC SELECT 
# MAGIC   '🏷️ Unique Tags' as metric,
# MAGIC   FORMAT_NUMBER(COUNT(DISTINCT tag_path), 0) as value
# MAGIC FROM ignition_demo.scada_data.tag_events
# MAGIC 
# MAGIC UNION ALL
# MAGIC 
# MAGIC SELECT 
# MAGIC   '⏱️ Latest Event' as metric,
# MAGIC   CAST(MAX(event_time) as STRING) as value
# MAGIC FROM ignition_demo.scada_data.tag_events
# MAGIC 
# MAGIC UNION ALL
# MAGIC 
# MAGIC SELECT 
# MAGIC   '📈 Events (Last Hour)' as metric,
# MAGIC   FORMAT_NUMBER(COUNT(*), 0) as value
# MAGIC FROM ignition_demo.scada_data.tag_events
# MAGIC WHERE event_time >= current_timestamp() - INTERVAL 1 HOUR
# MAGIC 
# MAGIC UNION ALL
# MAGIC 
# MAGIC SELECT 
# MAGIC   '✅ Good Quality %' as metric,
# MAGIC   CONCAT(ROUND(SUM(CASE WHEN quality = 'GOOD' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2), '%') as value
# MAGIC FROM ignition_demo.scada_data.tag_events
# MAGIC WHERE event_time >= current_timestamp() - INTERVAL 1 HOUR
# MAGIC 
# MAGIC UNION ALL
# MAGIC 
# MAGIC SELECT 
# MAGIC   '⚡ Avg Latency (sec)' as metric,
# MAGIC   CAST(ROUND(AVG(UNIX_TIMESTAMP(ingest_time) - UNIX_TIMESTAMP(event_time)), 2) as STRING) as value
# MAGIC FROM ignition_demo.scada_data.tag_events
# MAGIC WHERE event_time >= current_timestamp() - INTERVAL 1 HOUR

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🔧 Troubleshooting
# MAGIC 
# MAGIC ### No Data Showing?
# MAGIC 
# MAGIC 1. **Check Module Status**:
# MAGIC    ```bash
# MAGIC    curl http://gateway:8088/system/zerobus/diagnostics
# MAGIC    ```
# MAGIC 
# MAGIC 2. **Verify Event Stream is Enabled** in Ignition Designer
# MAGIC 
# MAGIC 3. **Check Module Logs**:
# MAGIC    ```bash
# MAGIC    tail -f /usr/local/ignition/logs/wrapper.log | grep -i zerobus
# MAGIC    ```
# MAGIC 
# MAGIC 4. **Verify Table Permissions**: Service Principal has MODIFY and SELECT
# MAGIC 
# MAGIC 5. **Check Zerobus Endpoint Format**: Must be `WORKSPACE_ID.zerobus.REGION.cloud.databricks.com`
# MAGIC 
# MAGIC ### Low Event Rate?
# MAGIC 
# MAGIC - Increase Event Stream buffer max wait time
# MAGIC - Check Gateway logs for dropped events
# MAGIC - Verify tags are actually changing values
# MAGIC 
# MAGIC ### High Latency?
# MAGIC 
# MAGIC - Reduce module batch flush interval
# MAGIC - Reduce Event Stream debounce time
# MAGIC - Check network connectivity

