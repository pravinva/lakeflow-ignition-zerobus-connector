# ✅ Databricks Setup Complete!

**Date:** December 8, 2025  
**Workspace:** e2-demo-field-eng.cloud.databricks.com  
**User:** pravin.varma@databricks.com

---

## 🎉 Successfully Created

### Catalog Structure

```
lakeflow_ignition/                  ← Dedicated catalog for this project
└── ot_data/                        ← Schema for OT (Operational Technology) data
    ├── bronze_events               ← Main table for Ignition events
    └── vw_recent_events            ← View for last hour of data
```

### Resources Created

| Resource Type | Full Name | Description |
|---------------|-----------|-------------|
| **Catalog** | `lakeflow_ignition` | Dedicated catalog for Lakeflow Ignition project |
| **Schema** | `lakeflow_ignition.ot_data` | Operational Technology data schema |
| **Table** | `lakeflow_ignition.ot_data.bronze_events` | Bronze layer: Raw events from Ignition |
| **View** | `lakeflow_ignition.ot_data.vw_recent_events` | Last 1 hour of events with latency calc |

---

## 📋 Table Schema

**Table:** `lakeflow_ignition.ot_data.bronze_events`

| Column | Type | Description |
|--------|------|-------------|
| `event_time` | TIMESTAMP | Event timestamp from Ignition tag |
| `tag_path` | STRING | Full Ignition tag path |
| `asset_id` | STRING | Asset identifier |
| `asset_path` | STRING | Asset hierarchy path |
| `numeric_value` | DOUBLE | Numeric tag value |
| `string_value` | STRING | String tag value |
| `boolean_value` | BOOLEAN | Boolean tag value |
| `integer_value` | BIGINT | Integer tag value |
| `value_string` | STRING | Value as string (all types) |
| `quality` | STRING | Data quality: GOOD/BAD/UNCERTAIN/UNKNOWN |
| `source_system` | STRING | Source Ignition Gateway ID |
| `site` | STRING | Site/location identifier |
| `line` | STRING | Production line |
| `unit` | STRING | Equipment unit |
| `tag_description` | STRING | Tag description/metadata |
| `engineering_units` | STRING | Engineering units (PSI, RPM, °C) |
| `ingestion_timestamp` | TIMESTAMP | Databricks ingestion time |

**Features:**
- ✅ Delta table format
- ✅ Change Data Feed enabled
- ✅ Auto-optimize write enabled
- ✅ Permissions granted to account users

---

## 🔧 Configuration for Ignition Module

Copy these exact values into your Ignition Zerobus module configuration:

```
Workspace URL:    https://e2-demo-field-eng.cloud.databricks.com
Zerobus Endpoint: e2-demo-field-eng.zerobus.cloud.databricks.com
Target Table:     lakeflow_ignition.ot_data.bronze_events
```

---

## 🔍 Verify Setup

### In Databricks SQL Editor

**View catalog:**
```
https://e2-demo-field-eng.cloud.databricks.com/explore/data/lakeflow_ignition
```

**Query the table:**
```sql
-- Check if table exists and is empty
SELECT COUNT(*) FROM lakeflow_ignition.ot_data.bronze_events;

-- View table schema
DESCRIBE EXTENDED lakeflow_ignition.ot_data.bronze_events;

-- Test the view (will be empty until data flows)
SELECT * FROM lakeflow_ignition.ot_data.vw_recent_events;
```

### Via Databricks CLI

```bash
# List catalogs
databricks catalogs list | grep lakeflow

# List schemas
databricks schemas list --catalog-name lakeflow_ignition

# List tables
databricks tables list --catalog-name lakeflow_ignition --schema-name ot_data
```

---

## 📊 Monitoring Queries

Once Ignition starts sending data, use these queries:

### Check Recent Events
```sql
SELECT 
  event_time,
  tag_path,
  value,
  quality,
  latency_seconds
FROM lakeflow_ignition.ot_data.vw_recent_events
ORDER BY event_time DESC
LIMIT 10;
```

### Ingestion Rate
```sql
SELECT 
  DATE_TRUNC('minute', event_time) as minute,
  COUNT(*) as event_count,
  COUNT(DISTINCT tag_path) as unique_tags,
  COUNT(DISTINCT asset_id) as unique_assets
FROM lakeflow_ignition.ot_data.bronze_events
WHERE event_time >= CURRENT_TIMESTAMP() - INTERVAL 1 HOUR
GROUP BY 1
ORDER BY 1 DESC;
```

### Data Quality Distribution
```sql
SELECT 
  quality,
  COUNT(*) as count,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM lakeflow_ignition.ot_data.bronze_events
WHERE event_time >= CURRENT_TIMESTAMP() - INTERVAL 1 HOUR
GROUP BY quality;
```

### Average Latency
```sql
SELECT 
  AVG(UNIX_TIMESTAMP(ingestion_timestamp) - UNIX_TIMESTAMP(event_time)) as avg_latency_seconds,
  MAX(UNIX_TIMESTAMP(ingestion_timestamp) - UNIX_TIMESTAMP(event_time)) as max_latency_seconds
FROM lakeflow_ignition.ot_data.bronze_events
WHERE event_time >= CURRENT_TIMESTAMP() - INTERVAL 1 HOUR;
```

### Tag List
```sql
SELECT DISTINCT 
  tag_path,
  COUNT(*) as event_count,
  MIN(event_time) as first_seen,
  MAX(event_time) as last_seen
FROM lakeflow_ignition.ot_data.bronze_events
GROUP BY tag_path
ORDER BY event_count DESC;
```

---

## 🔐 OAuth Service Principal (Next Step)

You still need to create an OAuth service principal for the Ignition module to authenticate.

### Steps:

1. **Create Service Principal**
   - Go to Account Console → Service Principals
   - Click "Add Service Principal"
   - Name: `ignition-zerobus-connector`
   - Click "Generate Secret"

2. **Save Credentials**
   - **Client ID** (UUID format): `<save this>`
   - **Client Secret** (starts with `dapi`): `<save this>`

3. **Grant Permissions**
   ```sql
   GRANT USE CATALOG ON CATALOG lakeflow_ignition TO SERVICE_PRINCIPAL '<client-id>';
   GRANT USE SCHEMA ON SCHEMA lakeflow_ignition.ot_data TO SERVICE_PRINCIPAL '<client-id>';
   GRANT MODIFY, SELECT ON TABLE lakeflow_ignition.ot_data.bronze_events TO SERVICE_PRINCIPAL '<client-id>';
   ```

---

## 🧪 Testing Workflow

Once your Ignition module is installed:

1. **Configure Module** with above credentials
2. **Subscribe to simulator tags**:
   - `[default]TestSimulator/Sine0`
   - `[default]TestSimulator/Ramp1`
   - `[default]TestSimulator/Realistic0`

3. **Enable module** and wait 30 seconds

4. **Verify data in Databricks**:
   ```sql
   SELECT * FROM lakeflow_ignition.ot_data.vw_recent_events LIMIT 10;
   ```

5. **Expected Results**:
   - ✅ Rows appear within 30 seconds
   - ✅ `event_time` matches simulator timestamps
   - ✅ `quality` = "GOOD"
   - ✅ `tag_path` shows correct paths
   - ✅ `latency_seconds` < 5

---

## 📝 Files Created

Setup scripts (in repo):
- ✅ `setup_lakeflow_catalog.py` - Creates catalog and schema
- ✅ `fix_table.py` - Creates table and view
- ✅ `DATABRICKS_SETUP_COMPLETE.md` - This file

---

## ✨ Summary

**Status:** 🟢 **Ready for Ignition Module Testing!**

- ✅ Catalog `lakeflow_ignition` created
- ✅ Schema `ot_data` created  
- ✅ Table `bronze_events` created (17 columns)
- ✅ View `vw_recent_events` created
- ✅ Permissions granted
- ⏳ Need OAuth service principal

**Next:** Create OAuth service principal, then configure Ignition module!

---

**Questions?**
- View in Databricks: https://e2-demo-field-eng.cloud.databricks.com/explore/data/lakeflow_ignition
- Workspace: https://e2-demo-field-eng.cloud.databricks.com

