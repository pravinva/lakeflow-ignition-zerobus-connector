# Installation Guide - Ignition Zerobus Connector

This guide provides step-by-step instructions for installing and configuring the Ignition Zerobus Connector module.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Databricks Setup](#databricks-setup)
3. [Build the Module](#build-the-module)
4. [Install in Ignition](#install-in-ignition)
5. [Configure the Module](#configure-the-module)
6. [Verify Installation](#verify-installation)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

### Ignition Requirements

- **Ignition Gateway**: Version 8.1.0 or higher
- **License**: Standard or higher (module installation capability)
- **Network**: Outbound HTTPS access to Databricks (port 443)
- **Memory**: Minimum 4GB heap recommended for Gateway
- **OS**: Any OS supported by Ignition (Windows, Linux, macOS)

### Databricks Requirements

- **Workspace**: Active Databricks workspace
- **Lakeflow Connect**: Zerobus Ingest feature enabled (contact Databricks)
- **Unity Catalog**: Enabled and configured
- **Target Table**: Delta table created in Unity Catalog
- **Authentication**: Service principal with write permissions

### Development Requirements (Building from Source)

- **JDK**: Java 11 or higher
- **Gradle**: 7.0+ (or use included wrapper)
- **Git**: For cloning repository

## Databricks Setup

### Step 1: Enable Zerobus Ingest

Contact your Databricks account team to enable Lakeflow Connect / Zerobus Ingest for your workspace.

Verify enablement:
```python
# In a Databricks notebook
dbutils.preview.lakeflow.show_status()
```

### Step 2: Create Target Delta Table

Create a Unity Catalog table to receive OT events:

```sql
CREATE TABLE dev_ot.bronze_ignition_events (
  event_time TIMESTAMP,
  tag_path STRING,
  asset_id STRING,
  asset_path STRING,
  numeric_value DOUBLE,
  string_value STRING,
  boolean_value BOOLEAN,
  integer_value BIGINT,
  value_string STRING,
  quality STRING,
  source_system STRING,
  site STRING,
  line STRING,
  unit STRING,
  tag_description STRING,
  engineering_units STRING
)
USING DELTA
PARTITIONED BY (DATE(event_time))
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);
```

### Step 3: Create Service Principal

1. **Create Service Principal**:
   - Workspace Admin Console → Service Principals
   - Click "Add Service Principal"
   - Name: `ignition-zerobus-connector`
   - Note the Application ID (Client ID)

2. **Generate Client Secret**:
   - Select the service principal
   - Go to "Secrets" tab
   - Click "Generate Secret"
   - **IMPORTANT**: Copy the secret immediately (shown only once)

3. **Grant Permissions**:
   ```sql
   -- Grant write access to target table
   GRANT MODIFY, SELECT ON TABLE dev_ot.bronze_ignition_events 
   TO `ignition-zerobus-connector`;
   
   -- Grant usage on schema
   GRANT USAGE ON SCHEMA dev_ot TO `ignition-zerobus-connector`;
   
   -- Grant usage on catalog
   GRANT USAGE ON CATALOG dev_ot TO `ignition-zerobus-connector`;
   ```

### Step 4: Get Zerobus Endpoint

Your Databricks team will provide the Zerobus Ingest endpoint URL:
```
https://<workspace-url>/api/2.0/lakeflow/ingest/stream/<stream-id>
```

## Build the Module

### Option 1: Download Pre-built Module

Download the latest `.modl` file from the releases page:
```
https://github.com/example/lakeflow-ignition-zerobus-connector/releases
```

### Option 2: Build from Source

```bash
# Clone repository
git clone https://github.com/example/lakeflow-ignition-zerobus-connector.git
cd lakeflow-ignition-zerobus-connector/module

# Build module (Unix/macOS)
./gradlew clean buildModule

# Build module (Windows)
gradlew.bat clean buildModule

# Output location
ls build/modules/zerobus-connector-1.0.0.modl
```

## Install in Ignition

### Step 1: Access Gateway Config

1. Open web browser
2. Navigate to: `http://<gateway-host>:8088/config`
3. Log in with admin credentials

### Step 2: Install Module

1. Navigate to: **Config → System → Modules**
2. Scroll to bottom of page
3. Click **"Install or Upgrade a Module..."**
4. Click **"Choose File"**
5. Select: `zerobus-connector-1.0.0.modl`
6. Click **"Install"**

### Step 3: Restart Gateway

1. A restart prompt will appear
2. Click **"Restart Gateway"**
3. Wait 30-60 seconds for Gateway to restart
4. Refresh the page and log back in

### Step 4: Verify Installation

1. Navigate to: **Config → System → Modules**
2. Find **"Zerobus Connector"** in the module list
3. Status should show: **"Running"**
4. Version should show: **"1.0.0"**

## Configure the Module

### Step 1: Access Configuration Panel

1. In Gateway Config, navigate to: **Config → Zerobus Connector**
   (New menu item added by the module)

### Step 2: Configure Databricks Connection

Enter the following in the **Connection Settings** section:

| Field | Value | Example |
|-------|-------|---------|
| Workspace URL | Your Databricks workspace URL | `https://my-workspace.cloud.databricks.com` |
| Zerobus Endpoint | Zerobus Ingest stream endpoint | `https://my-workspace.cloud.databricks.com/api/2.0/lakeflow/ingest/stream/abc123` |
| OAuth Client ID | Service principal Application ID | `a1b2c3d4-e5f6-7890-abcd-ef1234567890` |
| OAuth Client Secret | Generated client secret | `dasABC123xyz...` |
| Target Table | Unity Catalog table (3-part name) | `dev_ot.bronze_ignition_events` |

### Step 3: Configure Tag Selection

Choose one of three modes:

**Option A: Folder Mode** (Recommended for most cases)
```
Tag Selection Mode: Folder
Tag Folder Path: [default]Conveyor1
Include Subfolders: ✓ (checked)
```

**Option B: Pattern Mode** (For wildcard matching)
```
Tag Selection Mode: Pattern
Tag Path Pattern: [default]Conveyor*/Speed
```

**Option C: Explicit Mode** (For specific tags)
```
Tag Selection Mode: Explicit
Explicit Tag Paths:
  [default]Conveyor1/Speed
  [default]Conveyor1/Temperature
  [default]Tank1/Level
```

### Step 4: Configure Batching (Optional)

Use defaults for initial testing:

```
Batch Size: 500
Batch Flush Interval (ms): 2000
Max Queue Size: 10000
Max Events Per Second: 1000
```

### Step 5: Test Connection

1. Click **"Test Connection"** button
2. Wait 5-10 seconds
3. Look for success message:
   ```
   ✓ Connection test successful! Zerobus endpoint is reachable.
   ```
4. If test fails, see [Troubleshooting](#troubleshooting) section

### Step 6: Enable Module

1. Check the **"Enable Module"** checkbox
2. Leave **"Debug Logging"** unchecked (unless troubleshooting)
3. Click **"Save"**

### Step 7: Monitor Startup

1. Navigate to: **Config → System → Logs**
2. Look for log entries:
   ```
   INFO  [ZerobusGatewayHook] Starting Zerobus Gateway Module...
   INFO  [ZerobusClientManager] Initializing Zerobus client...
   INFO  [ZerobusClientManager] Zerobus client initialized successfully
   INFO  [TagSubscriptionService] Starting TagSubscriptionService...
   INFO  [TagSubscriptionService] Subscribed to 15 tags
   INFO  [ZerobusGatewayHook] Zerobus Gateway Module started successfully
   ```

## Verify Installation

### Step 1: Check Module Diagnostics

1. Navigate to: **Config → Zerobus Connector**
2. Scroll to **Diagnostics** section
3. Click **"Refresh Diagnostics"**
4. Verify status:
   ```
   === Zerobus Module Diagnostics ===
   Module Enabled: true
   
   === Zerobus Client Diagnostics ===
   Initialized: true
   Connected: true
   Total Events Sent: 0
   Total Batches Sent: 0
   Total Failures: 0
   Last Successful Send: Never
   
   === Tag Subscription Service Diagnostics ===
   Running: true
   Subscribed Tags: 15
   Queue Size: 0/10000
   Total Events Received: 0
   Total Events Dropped: 0
   Total Batches Flushed: 0
   Last Flush: Never
   ```

### Step 2: Generate Test Data

1. Open Ignition Designer
2. Navigate to a subscribed tag
3. Change the tag value manually
4. Wait 2-5 seconds (for batch flush)
5. Check diagnostics again - should show events sent

### Step 3: Query Databricks

In a Databricks SQL Warehouse or Notebook:

```sql
-- Check for recent events
SELECT * 
FROM dev_ot.bronze_ignition_events
WHERE event_time > current_timestamp() - INTERVAL 10 MINUTES
ORDER BY event_time DESC
LIMIT 100;

-- Count events by tag
SELECT 
  tag_path,
  COUNT(*) as event_count,
  MAX(event_time) as last_event
FROM dev_ot.bronze_ignition_events
WHERE event_time > current_timestamp() - INTERVAL 1 HOUR
GROUP BY tag_path
ORDER BY event_count DESC;

-- Verify data quality
SELECT 
  quality,
  COUNT(*) as count
FROM dev_ot.bronze_ignition_events
WHERE event_time > current_timestamp() - INTERVAL 1 HOUR
GROUP BY quality;
```

## Troubleshooting

### Issue: Module Won't Install

**Symptoms**: Error during installation, module doesn't appear in list

**Solutions**:
- Verify Ignition version is 8.1.0 or higher
- Check Gateway has adequate memory (increase heap size if needed)
- Review `wrapper.log` for detailed error messages
- Ensure no conflicting modules installed

### Issue: Connection Test Fails

**Symptoms**: "Connection test failed" message

**Solutions**:

1. **Check Databricks URL**:
   - Must include `https://`
   - Must be complete workspace URL
   - Test in browser first

2. **Verify OAuth Credentials**:
   - Client ID format: UUID (e.g., `a1b2c3d4-...`)
   - Client secret: Copy exactly, no extra spaces
   - Regenerate secret if unsure

3. **Check Network Connectivity**:
   ```bash
   # From Ignition Gateway server
   curl -v https://your-workspace.cloud.databricks.com
   ```
   - Should return HTTP 200 or redirect
   - Check firewall rules for outbound HTTPS

4. **Verify Table Permissions**:
   ```sql
   -- Test write permission
   INSERT INTO dev_ot.bronze_ignition_events
   VALUES (current_timestamp(), 'test', null, null, null, 'test', null, null, 'test', 'GOOD', 'test', null, null, null, null, null);
   ```

### Issue: No Data in Delta Table

**Symptoms**: Module running, diagnostics show 0 events sent

**Solutions**:

1. **Verify Module Enabled**: Check "Enable Module" checkbox is selected
2. **Check Tag Subscriptions**: 
   - Diagnostics should show "Subscribed Tags: > 0"
   - If 0, verify tag paths exist in Ignition
3. **Generate Tag Changes**:
   - Tags must change values to generate events
   - Simulate changes in Designer
4. **Check Batch Settings**:
   - Lower `batchFlushIntervalMs` to 500ms for testing
   - Lower `batchSize` to 10 for testing
5. **Review Logs**:
   - Enable "Debug Logging"
   - Check for send errors in Gateway logs

### Issue: High Memory Usage

**Symptoms**: Gateway memory usage increasing, OutOfMemoryError

**Solutions**:

1. **Reduce Queue Size**:
   ```
   Max Queue Size: 5000 (down from 10000)
   ```

2. **Enable Rate Limiting**:
   ```
   Max Events Per Second: 500 (down from 1000)
   ```

3. **Reduce Subscribed Tags**:
   - Be more selective in tag selection
   - Monitor fewer high-frequency tags

4. **Increase Gateway Heap**:
   - Edit `ignition.conf`
   - Increase `-Xmx` value (e.g., `-Xmx4096m`)

### Issue: Events Delayed

**Symptoms**: Events appear in Delta table minutes after tag changes

**Solutions**:

1. **Reduce Flush Interval**:
   ```
   Batch Flush Interval (ms): 500 (down from 2000)
   ```

2. **Reduce Batch Size**:
   ```
   Batch Size: 100 (down from 500)
   ```

3. **Check Network Latency**:
   ```bash
   ping <databricks-workspace>
   ```
   - Should be < 100ms
   - Consider VPN or Private Link for high latency

## Next Steps

1. **Configure Production Settings**: See `README.md` for performance tuning guidelines
2. **Set Up Monitoring**: Create Databricks dashboards for ingestion metrics
3. **Create Silver/Gold Tables**: Build downstream analytics tables
4. **Test Failure Scenarios**: See `tester.md` for test cases
5. **Enable Alerting**: Configure alerts for connection failures

## Support

For assistance:
- Check `README.md` for common configuration patterns
- Review `developer.md` for technical details
- Review `tester.md` for validation procedures
- Open an issue: https://github.com/example/lakeflow-ignition-zerobus-connector/issues

