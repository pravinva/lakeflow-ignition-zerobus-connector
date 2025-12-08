# Distribution Guide - Sharing the Zerobus Connector Module

**Date:** December 9, 2025

---

## ✅ YES - You Can Share the .modl File!

The module is designed to be configurable. Users just need:
1. The `.modl` file
2. Their own Databricks credentials
3. Their own tags to subscribe to

---

## 📦 What to Distribute

### Minimum Distribution (Simple)

**Just the module file:**
```
zerobus-connector-1.0.0.modl
```

**Users need to:**
1. Install the `.modl` file in Ignition Gateway
2. Configure via REST API with their own settings
3. Done!

---

### Recommended Distribution (Complete)

**1. Module File:**
- `zerobus-connector-1.0.0.modl`

**2. Setup SQL Script:**
- `setup_databricks_table.sql` (to create their Delta table)

**3. Configuration Template:**
- `config_template.json` (example configuration)

**4. Documentation:**
- Installation guide
- Configuration reference
- Troubleshooting tips

---

## 🔧 What Users Need to Configure

### Required Configuration (via REST API):

```json
{
  "enabled": true,
  "workspaceUrl": "https://<THEIR-WORKSPACE>.cloud.databricks.com",
  "zerobusEndpoint": "<WORKSPACE_ID>.zerobus.<REGION>.cloud.databricks.com",
  "oauthClientId": "<THEIR-SERVICE-PRINCIPAL-CLIENT-ID>",
  "oauthClientSecret": "<THEIR-SERVICE-PRINCIPAL-SECRET>",
  "targetTable": "<CATALOG>.<SCHEMA>.<TABLE>",
  "catalogName": "<CATALOG>",
  "schemaName": "<SCHEMA>",
  "tableName": "<TABLE>",
  "explicitTagPaths": [
    "[default]Plant/Line1/Temperature",
    "[default]Plant/Line1/Pressure"
  ],
  "batchSize": 500,
  "sourceSystemId": "Production-Gateway-01"
}
```

---

## 📋 User Prerequisites

### 1. Databricks Side:

✅ **Workspace with Zerobus enabled**
- Check with: Databricks support or account team
- Required: Workspace in supported region (us-west-2, us-east-1, etc.)

✅ **Service Principal created**
```bash
# Users create service principal in Databricks
# Get client ID and client secret
```

✅ **Delta table created**
```sql
-- Users run this SQL in their workspace
CREATE TABLE <catalog>.<schema>.tag_events (
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
    ingestion_timestamp TIMESTAMP,
    data_type STRING,
    alarm_state STRING,
    alarm_priority INT
)
USING DELTA;
```

✅ **Permissions granted**
```sql
GRANT USE CATALOG ON CATALOG <catalog> TO `<service-principal-id>`;
GRANT USE SCHEMA ON SCHEMA <catalog>.<schema> TO `<service-principal-id>`;
GRANT SELECT, MODIFY ON TABLE <catalog>.<schema>.tag_events TO `<service-principal-id>`;
```

---

### 2. Ignition Side:

✅ **Ignition Gateway 8.3.2 or higher**

✅ **Allow unsigned modules** (for development)
```bash
# Add to ignition.conf:
-Dignition.allowunsignedmodules=true
```

✅ **Tags to subscribe to**
- Users specify their own tag paths
- Any Ignition tag provider works
- Can use folder paths, patterns, or explicit lists

---

## 🚀 Installation Steps (For Users)

### Step 1: Install Module

1. Go to: `http://<gateway>:8088/web/config/system.modules`
2. Click "Install or Upgrade a Module"
3. Upload: `zerobus-connector-1.0.0.modl`
4. Trust the certificate
5. Restart Gateway

---

### Step 2: Setup Databricks

1. Create service principal in Databricks
2. Create Delta table with schema above
3. Grant permissions to service principal
4. Note workspace ID from URL (`?o=XXXXXXXXX`)
5. Note workspace region (e.g., `us-west-2`)

---

### Step 3: Configure Module

**Using curl:**
```bash
curl -X POST http://<gateway>:8088/system/zerobus/config \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "workspaceUrl": "https://<workspace>.cloud.databricks.com",
    "zerobusEndpoint": "<workspace_id>.zerobus.<region>.cloud.databricks.com",
    "oauthClientId": "<client-id>",
    "oauthClientSecret": "<client-secret>",
    "targetTable": "<catalog>.<schema>.<table>",
    "catalogName": "<catalog>",
    "schemaName": "<schema>",
    "tableName": "<table>",
    "tagSelectionMode": "explicit",
    "explicitTagPaths": [
      "[default]YourTag1",
      "[default]YourTag2"
    ],
    "batchSize": 500,
    "sourceSystemId": "YourGatewayName"
  }'
```

---

### Step 4: Verify Data Flow

**Check diagnostics:**
```bash
curl http://<gateway>:8088/system/zerobus/diagnostics
```

**Query Databricks:**
```sql
SELECT * FROM <catalog>.<schema>.<table>
WHERE event_time >= CURRENT_TIMESTAMP() - INTERVAL 1 HOUR
ORDER BY event_time DESC
LIMIT 10;
```

---

## 📝 Configuration Reference

### Tag Selection Modes:

**1. Explicit (recommended for production):**
```json
{
  "tagSelectionMode": "explicit",
  "explicitTagPaths": [
    "[default]Plant/Line1/Temperature",
    "[default]Plant/Line1/Pressure",
    "[default]Plant/Line2/Speed"
  ]
}
```

**2. Folder (subscribe to all tags in folder):**
```json
{
  "tagSelectionMode": "folder",
  "tagFolderPath": "[default]Plant/Line1",
  "includeSubfolders": true
}
```

**3. Pattern (regex matching):**
```json
{
  "tagSelectionMode": "pattern",
  "tagPathPattern": ".*Temperature.*|.*Pressure.*"
}
```

---

### Performance Tuning:

**High Throughput:**
```json
{
  "batchSize": 1000,
  "batchFlushIntervalMs": 1000,
  "maxQueueSize": 50000,
  "maxEventsPerSecond": 10000
}
```

**Low Latency:**
```json
{
  "batchSize": 100,
  "batchFlushIntervalMs": 500,
  "onlyOnChange": true
}
```

**Balanced:**
```json
{
  "batchSize": 500,
  "batchFlushIntervalMs": 2000,
  "onlyOnChange": false
}
```

---

## 🔒 Before Publishing (Important!)

### 1. Sign the Module ✅ (Recommended for Production)

**For production distribution, you should sign the module:**

```bash
# Use Ignition's module signing tool
# Contact Inductive Automation for signing certificate
# Or use self-signed cert for internal distribution
```

**Benefits of signing:**
- Users don't need to allow unsigned modules
- More professional
- Better security

**Current state:** Module is unsigned (development only)

---

### 2. License Configuration ✅

**Current:** No license requirement (open/internal use)

**For commercial distribution:**
- Add license checking in `isFreeModule()` method
- Return `false` if you want to enforce licensing
- Implement license validation

---

### 3. Documentation ✅

**Must include:**
- README with quick start
- Configuration reference
- Databricks setup SQL script
- Troubleshooting guide
- Support contact info

**You already have:**
- ✅ architect.md
- ✅ developer.md
- ✅ tester.md
- ✅ README.md
- ✅ QUICKSTART.md

---

### 4. Remove Hardcoded Values ✅

**Check for:**
- ❌ No hardcoded credentials (GOOD - everything configurable)
- ❌ No hardcoded workspace URLs (GOOD - user configured)
- ❌ No hardcoded table names (GOOD - user configured)

**Status:** ✅ Module is properly configurable

---

## 📤 Distribution Options

### Option 1: Simple File Share (Easiest)

**Share:**
- `zerobus-connector-1.0.0.modl`
- `DISTRIBUTION_README.md` (installation instructions)
- `config_template.json` (example config)
- `setup_databricks_table.sql` (Delta table creation)

**Via:**
- Email attachment
- Internal file share
- Box/Dropbox
- Internal artifact repository

---

### Option 2: GitHub Release (Recommended)

**Create a GitHub release:**
1. Tag version: `v1.0.0`
2. Attach: `zerobus-connector-1.0.0.modl`
3. Release notes with installation instructions
4. Users download from Releases page

**Benefits:**
- Version tracking
- Easy updates
- Professional appearance

---

### Option 3: Maven/Nexus Repository (Enterprise)

**For enterprise distribution:**
- Publish to internal Maven/Nexus
- Users download via Gradle/Maven
- Automatic dependency management
- Version management

---

## 👥 What Users Do

### Installation (5 minutes):

1. Download `zerobus-connector-1.0.0.modl`
2. Upload to Ignition Gateway
3. Restart Gateway
4. Trust certificate

### Setup Databricks (10 minutes):

1. Create service principal
2. Run setup SQL to create table
3. Grant permissions
4. Note workspace ID and region

### Configuration (5 minutes):

1. Build correct Zerobus endpoint: `<workspace_id>.zerobus.<region>.cloud.databricks.com`
2. POST configuration to `/system/zerobus/config`
3. Specify their own tag paths

### Verification (2 minutes):

1. Check diagnostics endpoint
2. Query Databricks to see data

**Total time: ~20 minutes for users to get running!**

---

## 🎯 Required Information for Users

**Checklist for users before installation:**

- [ ] Ignition Gateway 8.3.2+ installed
- [ ] Databricks workspace with Zerobus enabled
- [ ] Service principal created (client ID + secret)
- [ ] Delta table created with correct schema
- [ ] Permissions granted to service principal
- [ ] Workspace ID (from URL `?o=XXXXX`)
- [ ] Workspace region (e.g., us-west-2)
- [ ] Tag paths to subscribe to

---

## 📊 Performance Testing

Want to measure ingestion rate now? Let me:

1. Subscribe to ALL Sample_Tags (81 tags)
2. Poll every 100ms (10 samples/sec per tag = 810 events/sec)
3. Measure events per second reaching Databricks
4. Show you throughput metrics

**Should I run a performance test?**

---

## 🎁 What Makes This Easy to Share

✅ **Self-contained:** All dependencies bundled in .modl file  
✅ **Configurable:** No hardcoded values  
✅ **REST API:** Easy to configure programmatically  
✅ **Diagnostics:** Built-in monitoring endpoint  
✅ **No GUI required:** Works via REST API  
✅ **Universal:** Works with any Ignition tags  
✅ **Documented:** Complete documentation already written  

---

## 🚀 Next Steps for Distribution

**If you want to share now:**
1. I'll create a clean README for users
2. I'll create a config template
3. I'll package the SQL setup script
4. You can share the .modl + docs

**If you want to polish first:**
1. Sign the module (remove unsigned requirement)
2. Add a simple web UI (optional)
3. Create GitHub release
4. Write user guide

**Which approach do you prefer?**

