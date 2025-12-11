# Databricks notebook source
# MAGIC %md
# MAGIC # Data Quality Checks for Ignition Tag Events
# MAGIC 
# MAGIC **Purpose**: Automated data quality validation
# MAGIC 
# MAGIC **What this notebook does**:
# MAGIC 1. Validates schema compliance
# MAGIC 2. Checks for nulls in required fields
# MAGIC 3. Validates data types
# MAGIC 4. Checks for duplicates
# MAGIC 5. Validates timestamp consistency
# MAGIC 6. Quality score calculation

# COMMAND ----------

# Configuration
CATALOG_NAME = "ignition_demo"
SCHEMA_NAME = "scada_data"
TABLE_NAME = "tag_events"
FULL_TABLE_NAME = f"{CATALOG_NAME}.{SCHEMA_NAME}.{TABLE_NAME}"

# Time window for checks
CHECK_WINDOW_HOURS = 24

print(f"Running data quality checks on: {FULL_TABLE_NAME}")
print(f"Time window: Last {CHECK_WINDOW_HOURS} hours")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 1: Required Fields Not Null

# COMMAND ----------

# DBTITLE 1,Check for Null Required Fields
null_checks = spark.sql(f"""
SELECT 
  'tag_path' as field,
  COUNT(*) as null_count,
  COUNT(*) * 100.0 / (SELECT COUNT(*) FROM {FULL_TABLE_NAME} WHERE event_time >= current_timestamp() - INTERVAL {CHECK_WINDOW_HOURS} HOURS) as null_percentage
FROM {FULL_TABLE_NAME}
WHERE event_time >= current_timestamp() - INTERVAL {CHECK_WINDOW_HOURS} HOURS
  AND tag_path IS NULL

UNION ALL

SELECT 
  'event_time' as field,
  COUNT(*) as null_count,
  COUNT(*) * 100.0 / (SELECT COUNT(*) FROM {FULL_TABLE_NAME} WHERE event_time >= current_timestamp() - INTERVAL {CHECK_WINDOW_HOURS} HOURS) as null_percentage
FROM {FULL_TABLE_NAME}
WHERE event_time >= current_timestamp() - INTERVAL {CHECK_WINDOW_HOURS} HOURS
  AND event_time IS NULL

UNION ALL

SELECT 
  'quality' as field,
  COUNT(*) as null_count,
  COUNT(*) * 100.0 / (SELECT COUNT(*) FROM {FULL_TABLE_NAME} WHERE event_time >= current_timestamp() - INTERVAL {CHECK_WINDOW_HOURS} HOURS) as null_percentage
FROM {FULL_TABLE_NAME}
WHERE event_time >= current_timestamp() - INTERVAL {CHECK_WINDOW_HOURS} HOURS
  AND quality IS NULL

UNION ALL

SELECT 
  'source_system_id' as field,
  COUNT(*) as null_count,
  COUNT(*) * 100.0 / (SELECT COUNT(*) FROM {FULL_TABLE_NAME} WHERE event_time >= current_timestamp() - INTERVAL {CHECK_WINDOW_HOURS} HOURS) as null_percentage
FROM {FULL_TABLE_NAME}
WHERE event_time >= current_timestamp() - INTERVAL {CHECK_WINDOW_HOURS} HOURS
  AND source_system_id IS NULL
""")

display(null_checks)

# Check if any nulls found
null_count = null_checks.filter("null_count > 0").count()
if null_count == 0:
    print("✅ Test PASSED: No nulls in required fields")
else:
    print(f"⚠️ Test FAILED: Found nulls in {null_count} required fields")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 2: At Least One Value Field Populated

# COMMAND ----------

# DBTITLE 1,Records with All Value Fields Null
# MAGIC %sql
# MAGIC SELECT COUNT(*) as records_with_no_values
# MAGIC FROM ignition_demo.scada_data.tag_events
# MAGIC WHERE event_time >= current_timestamp() - INTERVAL 24 HOURS
# MAGIC   AND numeric_value IS NULL
# MAGIC   AND string_value IS NULL
# MAGIC   AND boolean_value IS NULL

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 3: Timestamp Validation

# COMMAND ----------

# DBTITLE 1,Check for Future Timestamps
# MAGIC %sql
# MAGIC SELECT 
# MAGIC   COUNT(*) as future_event_count,
# MAGIC   MAX(event_time) as latest_future_timestamp
# MAGIC FROM ignition_demo.scada_data.tag_events
# MAGIC WHERE event_time > current_timestamp()

# COMMAND ----------

# DBTITLE 1,Check Ingest Time >= Event Time
# MAGIC %sql
# MAGIC SELECT 
# MAGIC   COUNT(*) as invalid_timestamp_order,
# MAGIC   MIN(tag_path) as example_tag
# MAGIC FROM ignition_demo.scada_data.tag_events
# MAGIC WHERE event_time >= current_timestamp() - INTERVAL 24 HOURS
# MAGIC   AND ingest_time < event_time

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 4: Duplicate Detection

# COMMAND ----------

# DBTITLE 1,Check for Exact Duplicates
# MAGIC %sql
# MAGIC SELECT 
# MAGIC   tag_path,
# MAGIC   event_time,
# MAGIC   COUNT(*) as duplicate_count
# MAGIC FROM ignition_demo.scada_data.tag_events
# MAGIC WHERE event_time >= current_timestamp() - INTERVAL 24 HOURS
# MAGIC GROUP BY tag_path, event_time
# MAGIC HAVING COUNT(*) > 1
# MAGIC ORDER BY duplicate_count DESC
# MAGIC LIMIT 20

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 5: Data Type Consistency

# COMMAND ----------

# DBTITLE 1,Verify Data Type Field Matches Actual Value
# MAGIC %sql
# MAGIC SELECT 
# MAGIC   data_type,
# MAGIC   SUM(CASE WHEN numeric_value IS NOT NULL THEN 1 ELSE 0 END) as has_numeric,
# MAGIC   SUM(CASE WHEN string_value IS NOT NULL THEN 1 ELSE 0 END) as has_string,
# MAGIC   SUM(CASE WHEN boolean_value IS NOT NULL THEN 1 ELSE 0 END) as has_boolean,
# MAGIC   COUNT(*) as total
# MAGIC FROM ignition_demo.scada_data.tag_events
# MAGIC WHERE event_time >= current_timestamp() - INTERVAL 24 HOURS
# MAGIC GROUP BY data_type
# MAGIC ORDER BY total DESC

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 6: Quality Code Validation

# COMMAND ----------

# DBTITLE 1,Validate Quality Code Ranges
# MAGIC %sql
# MAGIC SELECT 
# MAGIC   quality,
# MAGIC   quality_code,
# MAGIC   COUNT(*) as count,
# MAGIC   CASE 
# MAGIC     WHEN quality = 'GOOD' AND quality_code = 192 THEN '✅ Valid'
# MAGIC     WHEN quality = 'BAD' AND quality_code != 192 THEN '✅ Valid'
# MAGIC     WHEN quality = 'UNCERTAIN' AND quality_code != 192 THEN '✅ Valid'
# MAGIC     ELSE '⚠️ Unexpected combination'
# MAGIC   END as validation_status
# MAGIC FROM ignition_demo.scada_data.tag_events
# MAGIC WHERE event_time >= current_timestamp() - INTERVAL 24 HOURS
# MAGIC GROUP BY quality, quality_code
# MAGIC ORDER BY count DESC

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 7: Source System Validation

# COMMAND ----------

# DBTITLE 1,Verify Source System IDs
# MAGIC %sql
# MAGIC SELECT 
# MAGIC   source_system_id,
# MAGIC   COUNT(*) as event_count,
# MAGIC   MIN(event_time) as first_seen,
# MAGIC   MAX(event_time) as last_seen,
# MAGIC   CASE 
# MAGIC     WHEN source_system_id IS NULL THEN '❌ Null'
# MAGIC     WHEN source_system_id = '' THEN '❌ Empty'
# MAGIC     WHEN LENGTH(source_system_id) < 5 THEN '⚠️ Too short'
# MAGIC     ELSE '✅ Valid'
# MAGIC   END as validation_status
# MAGIC FROM ignition_demo.scada_data.tag_events
# MAGIC WHERE event_time >= current_timestamp() - INTERVAL 24 HOURS
# MAGIC GROUP BY source_system_id
# MAGIC ORDER BY event_count DESC

# COMMAND ----------

# MAGIC %md
# MAGIC ## Test 8: Tag Path Format Validation

# COMMAND ----------

# DBTITLE 1,Check Tag Path Format
# MAGIC %sql
# MAGIC SELECT 
# MAGIC   tag_path,
# MAGIC   tag_provider,
# MAGIC   COUNT(*) as count,
# MAGIC   CASE 
# MAGIC     WHEN tag_path LIKE '[%]%' THEN '✅ Valid format'
# MAGIC     ELSE '⚠️ Missing provider brackets'
# MAGIC   END as validation_status
# MAGIC FROM ignition_demo.scada_data.tag_events
# MAGIC WHERE event_time >= current_timestamp() - INTERVAL 24 HOURS
# MAGIC GROUP BY tag_path, tag_provider
# MAGIC HAVING validation_status != '✅ Valid format'
# MAGIC ORDER BY count DESC
# MAGIC LIMIT 20

# COMMAND ----------

# MAGIC %md
# MAGIC ## Overall Data Quality Score

# COMMAND ----------

# DBTITLE 1,Calculate Quality Score
from pyspark.sql.functions import col, when, count, sum as _sum, lit

df = spark.sql(f"""
SELECT * FROM {FULL_TABLE_NAME}
WHERE event_time >= current_timestamp() - INTERVAL {CHECK_WINDOW_HOURS} HOURS
""")

total_records = df.count()

if total_records == 0:
    print("⚠️ No records found in the specified time window")
else:
    # Calculate various quality metrics
    quality_metrics = df.select(
        # Required fields populated
        (count(when(col("tag_path").isNotNull(), 1)) / total_records * 100).alias("tag_path_populated_pct"),
        (count(when(col("event_time").isNotNull(), 1)) / total_records * 100).alias("event_time_populated_pct"),
        
        # At least one value field populated
        (count(when(
            col("numeric_value").isNotNull() | 
            col("string_value").isNotNull() | 
            col("boolean_value").isNotNull(), 1
        )) / total_records * 100).alias("value_populated_pct"),
        
        # Quality is GOOD
        (count(when(col("quality") == "GOOD", 1)) / total_records * 100).alias("good_quality_pct"),
        
        # No future timestamps
        (count(when(col("event_time") <= lit(spark.sql("SELECT current_timestamp()").collect()[0][0]), 1)) / total_records * 100).alias("valid_timestamp_pct"),
        
        # Valid ingest time order
        (count(when(col("ingest_time") >= col("event_time"), 1)) / total_records * 100).alias("valid_ingest_order_pct")
    ).first()
    
    # Calculate overall score (average of all metrics)
    scores = [
        quality_metrics["tag_path_populated_pct"],
        quality_metrics["event_time_populated_pct"],
        quality_metrics["value_populated_pct"],
        quality_metrics["good_quality_pct"],
        quality_metrics["valid_timestamp_pct"],
        quality_metrics["valid_ingest_order_pct"]
    ]
    
    overall_score = sum(scores) / len(scores)
    
    print(f"📊 Data Quality Metrics (Last {CHECK_WINDOW_HOURS} hours)")
    print(f"{'='*60}")
    print(f"Total Records: {total_records:,}")
    print(f"")
    print(f"Individual Scores:")
    print(f"  Tag Path Populated:     {quality_metrics['tag_path_populated_pct']:.2f}%")
    print(f"  Event Time Populated:   {quality_metrics['event_time_populated_pct']:.2f}%")
    print(f"  Value Field Populated:  {quality_metrics['value_populated_pct']:.2f}%")
    print(f"  Good Quality:           {quality_metrics['good_quality_pct']:.2f}%")
    print(f"  Valid Timestamp:        {quality_metrics['valid_timestamp_pct']:.2f}%")
    print(f"  Valid Ingest Order:     {quality_metrics['valid_ingest_order_pct']:.2f}%")
    print(f"")
    print(f"{'='*60}")
    print(f"Overall Data Quality Score: {overall_score:.2f}%")
    print(f"{'='*60}")
    
    if overall_score >= 95:
        print("✅ EXCELLENT - Data quality is very high")
    elif overall_score >= 85:
        print("✅ GOOD - Data quality is acceptable")
    elif overall_score >= 70:
        print("⚠️ FAIR - Some data quality issues detected")
    else:
        print("❌ POOR - Significant data quality issues require attention")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🔍 Recommendations
# MAGIC 
# MAGIC Based on the quality checks above:
# MAGIC 
# MAGIC 1. **If nulls in required fields**: Check Event Stream handler script
# MAGIC 2. **If timestamp issues**: Check system time synchronization
# MAGIC 3. **If duplicates**: Check Event Stream debounce settings
# MAGIC 4. **If low good quality %**: Investigate tag quality in Ignition
# MAGIC 5. **If data type mismatches**: Review tag configuration in Ignition
# MAGIC 
# MAGIC Run this notebook daily to track quality trends over time!

