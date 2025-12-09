# Ignition Zerobus Connector - User Handover Guide

**Version**: 1.0.0  
**Status**: ✅ Production Ready  
**Last Updated**: December 9, 2024

---

## 📋 Table of Contents

- [What This Module Does](#what-this-module-does)
- [Quick Start (5 Minutes)](#quick-start-5-minutes)
- [Prerequisites](#prerequisites)
- [Installation Steps](#installation-steps)
- [Configuration](#configuration)
- [Verification](#verification)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)
- [Advanced Configuration](#advanced-configuration)
- [Support & Documentation](#support--documentation)

---

## What This Module Does

The **Ignition Zerobus Connector** streams SCADA tag data from your Ignition Gateway directly to Databricks Delta tables in real-time.

### Key Benefits

✅ **Real-Time Data Flow**: 100ms latency - events arrive in Databricks as they happen  
✅ **Event-Based**: Only sends data when values actually change (optional)  
✅ **Zero Infrastructure**: No Kafka, no message brokers - direct to Delta tables  
✅ **Secure**: OAuth 2.0 M2M authentication with Service Principals  
✅ **Reliable**: Automatic retry, zero data loss, proven stable  
✅ **Simple**: 3-step installation, REST API configuration

### Data Flow

```
Ignition Tags → Module (100ms polling) → Databricks Zerobus → Delta Table
```

---

## Quick Start (5 Minutes)

### Step 1: Download & Install Module

1. **Download** the `.modl` file from the GitHub releases page
2. **Navigate** to Ignition Gateway: `http://your-gateway:8088`
3. **Go to**: `Config → System → Modules`
4. **Click**: "Install or Upgrade a Module"
5. **Upload**: `zerobus-connector-1.0.0.modl`
6. **Click**: "Install"
7. **Restart** the gateway when prompted

### Step 2: Configure Module

Run this command (replace credentials with yours):

```bash
curl -X POST http://your-gateway:8088/system/zerobus/config \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "workspaceUrl": "https://your-workspace.cloud.databricks.com",
    "zerobusEndpoint": "your-workspace-id.zerobus.region.cloud.databricks.com",
    "oauthClientId": "your-service-principal-client-id",
    "oauthClientSecret": "your-service-principal-secret",
    "targetTable": "ignition_demo.scada_data.tag_events",
    "tagSelectionMode": "explicit",
    "explicitTagPaths": [
      "[Sample_Tags]Sine/Sine0",
      "[Sample_Tags]Sine/Sine1"
    ],
    "onlyOnChange": true
  }'
```

### Step 3: Verify It's Working

```bash
curl http://your-gateway:8088/system/zerobus/diagnostics
```

**Look for:**
- `Running: true`
- `Stream State: OPENED`
- `Total Events Sent: > 0` (increasing)
- `Total Failures: 0`

**That's it!** Your data is now flowing to Databricks! 🎉

---

## Prerequisites

### 1. Ignition Gateway

- **Version**: 8.3.0 or later (tested on 8.3.2)
- **Access**: Gateway admin credentials
- **Network**: Outbound HTTPS access to Databricks (port 443)
- **Note**: Module uses Jakarta Servlet API (compatible with Ignition 8.3.x)

### 2. Databricks Workspace

- **Workspace URL**: e.g., `https://your-workspace.cloud.databricks.com`
- **Unity Catalog**: Enabled
- **Service Principal**: Created with OAuth credentials
- **Delta Table**: Created and accessible

### 3. Databricks Setup

#### A. Get Zerobus Endpoint

Your Zerobus endpoint format:
```
<workspace-id>.zerobus.<region>.cloud.databricks.com
```

**Example**: `1444828305810485.zerobus.us-west-2.cloud.databricks.com`

To find your workspace ID:
1. Go to your Databricks workspace
2. Look at the URL: `https://adb-<workspace-id>.cloud.databricks.com`
3. Use that workspace ID

#### B. Create Service Principal

**Option 1: Using Databricks CLI**
```bash
databricks service-principals create \
  --display-name "ignition-zerobus-connector"
```

**Option 2: Using Web UI**
1. Go to: **Account Console → Service Principals**
2. Click **"Add Service Principal"**
3. Name: `ignition-zerobus-connector`
4. **Generate OAuth Secret** - save the Client ID and Secret!

#### C. Create Delta Table

```sql
CREATE TABLE IF NOT EXISTS ignition_demo.scada_data.tag_events (
  tag_path STRING,
  value STRING,
  quality STRING,
  timestamp TIMESTAMP,
  source_system_id STRING,
  ingestion_timestamp TIMESTAMP
)
USING DELTA
LOCATION 's3://your-bucket/ignition/tag_events';
```

#### D. Grant Permissions

**Important**: Use the Service Principal's **UUID** (not the display name) for permissions:

```sql
-- Replace 'your-sp-uuid' with actual UUID like: 6ff2b11b-fdb8-4c2c-9360-ed105d5f6dcb

-- Grant catalog access
GRANT USE CATALOG ON CATALOG ignition_demo 
TO `your-sp-uuid`;

-- Grant schema access
GRANT USE SCHEMA ON SCHEMA ignition_demo.scada_data 
TO `your-sp-uuid`;

-- Grant table modify (required for writing)
GRANT MODIFY ON TABLE ignition_demo.scada_data.tag_events 
TO `your-sp-uuid`;

-- Grant table select (required for Zerobus to read table metadata)
GRANT SELECT ON TABLE ignition_demo.scada_data.tag_events 
TO `your-sp-uuid`;
```

**Verify permissions:**
```sql
SHOW GRANTS ON TABLE ignition_demo.scada_data.tag_events;
```

---

## Installation Steps

### Detailed Installation

#### 1. Stop Ignition (Optional - for command-line install)

**Linux:**
```bash
sudo systemctl stop ignition
```

**macOS:**
```bash
sudo launchctl unload /Library/LaunchDaemons/com.inductiveautomation.ignition.plist
```

**Windows:**
```powershell
Stop-Service Ignition-Gateway
```

#### 2. Install Module

**Option A: Web UI (Recommended)**
1. Navigate to: `http://your-gateway:8088`
2. Login with admin credentials
3. Go to: `Config → System → Modules`
4. Click: "Install or Upgrade a Module"
5. Browse and select: `zerobus-connector-1.0.0.modl`
6. Click: "Install"
7. Restart gateway when prompted

**Option B: Command Line**
```bash
# Copy module to Ignition directory
sudo cp zerobus-connector-1.0.0.modl /path/to/ignition/user-lib/modules/

# Restart Ignition
sudo systemctl start ignition  # Linux
```

#### 3. Verify Installation

Check the Gateway Status page:
```
Config → System → Modules
```

Look for:
- **Name**: Zerobus Connector
- **Version**: 1.0.0
- **Status**: ✅ Running

---

## Configuration

### Required Configuration Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `enabled` | Enable/disable module | `true` |
| `workspaceUrl` | Databricks workspace URL | `https://your-workspace.cloud.databricks.com` |
| `zerobusEndpoint` | Zerobus ingestion endpoint | `your-workspace-id.zerobus.region.cloud.databricks.com` |
| `oauthClientId` | Service Principal Client ID | `your-service-principal-client-id` |
| `oauthClientSecret` | Service Principal Secret | `your-service-principal-secret` |
| `targetTable` | Fully qualified table name | `ignition_demo.scada_data.tag_events` |
| `tagSelectionMode` | How to select tags | `explicit` / `folder` / `pattern` |

### Tag Selection Modes

#### Mode 1: Explicit (Recommended)

Specify exact tag paths:

```json
{
  "tagSelectionMode": "explicit",
  "explicitTagPaths": [
    "[default]Compressor/Pressure",
    "[default]Compressor/Temperature",
    "[default]Compressor/Running"
  ]
}
```

**⚠️ Important**: Tag paths must include the full folder structure as shown in Ignition Designer Tag Browser:
- ✅ Correct: `[Sample_Tags]Realistic/Realistic0`
- ❌ Wrong: `[Sample_Tags]Realistic0`

#### Mode 2: Folder

Subscribe to all tags in a folder:

```json
{
  "tagSelectionMode": "folder",
  "tagFolderPath": "[default]Compressor",
  "includeSubfolders": true
}
```

#### Mode 3: Pattern

Use wildcards to match tags:

```json
{
  "tagSelectionMode": "pattern",
  "tagPathPattern": "[default]*/Temperature"
}
```

### Optional Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `batchSize` | `10` | Events per batch |
| `batchFlushIntervalMs` | `1000` | Max ms between flushes |
| `maxQueueSize` | `10000` | Max events in queue |
| `onlyOnChange` | `false` | Only send when values change |
| `debugLogging` | `false` | Enable verbose logging |
| `sourceSystemId` | `"ignition-gateway"` | Source identifier in Delta table |

### Complete Configuration Example

```json
{
  "enabled": true,
  
  "workspaceUrl": "https://your-workspace.cloud.databricks.com",
  "zerobusEndpoint": "your-workspace-id.zerobus.region.cloud.databricks.com",
  "oauthClientId": "your-service-principal-client-id",
  "oauthClientSecret": "your-service-principal-secret",
  
  "catalogName": "your_catalog",
  "schemaName": "your_schema",
  "tableName": "tag_events",
  "targetTable": "your_catalog.your_schema.tag_events",
  
  "tagSelectionMode": "explicit",
  "explicitTagPaths": [
    "[Sample_Tags]Sine/Sine0",
    "[Sample_Tags]Realistic/Realistic0",
    "[Sample_Tags]Realistic/Realistic1"
  ],
  
  "batchSize": 10,
  "batchFlushIntervalMs": 1000,
  "maxQueueSize": 10000,
  "maxEventsPerSecond": 10000,
  
  "onlyOnChange": true,
  "debugLogging": false,
  
  "sourceSystemId": "ignition-gateway-local"
}
```

---

## Verification

### Check Module Status

**Web UI:**
1. Navigate to: `Config → System → Status`
2. Look for: "Zerobus Connector"
3. Status should be: ✅ Running

**Diagnostics API:**
```bash
curl http://your-gateway:8088/system/zerobus/diagnostics
```

### Expected Output

```
=== Zerobus Module Diagnostics ===
Module Enabled: true

=== Zerobus Client Diagnostics ===
Initialized: true
Connected: true
Stream ID: d8611db9-e8e2-40e2-b215-0c72da63d2d7
Stream State: OPENED
Total Events Sent: 150
Total Batches Sent: 15
Total Failures: 0
Last Acked Offset: 145
Last Successful Send: 2 seconds ago

=== Tag Subscription Service Diagnostics ===
Running: true
Subscribed Tags: 3
Queue Size: 5/10000
Total Events Received: 155
Total Events Dropped: 0
Total Batches Flushed: 15
Last Flush: 2 seconds ago
```

### What Each Metric Means

✅ **Good Indicators:**
- `Stream State: OPENED` - Connected to Databricks
- `Total Events Sent` - Increasing over time
- `Total Failures: 0` - No errors
- `Total Events Dropped: 0` - No data loss
- `Last Successful Send: < 5 seconds` - Real-time streaming

⚠️ **Warning Signs:**
- `Stream State: CLOSED` - Connection issue
- `Total Failures > 0` - Authentication or network errors
- `Total Events Dropped > 0` - Queue full, increase `maxQueueSize`
- `Last Successful Send: > 60 seconds` - Stalled connection

### Verify Data in Databricks

```sql
-- Check recent events
SELECT * FROM ignition_demo.scada_data.tag_events
ORDER BY ingestion_timestamp DESC
LIMIT 10;

-- Count events by source
SELECT source_system_id, COUNT(*) as event_count
FROM ignition_demo.scada_data.tag_events
GROUP BY source_system_id;

-- Check data freshness
SELECT 
  MAX(ingestion_timestamp) as latest_event,
  DATEDIFF(SECOND, MAX(ingestion_timestamp), CURRENT_TIMESTAMP()) as seconds_ago
FROM ignition_demo.scada_data.tag_events;
```

---

## Monitoring

### REST API Endpoints

#### GET /system/zerobus/diagnostics

Returns real-time operational metrics.

```bash
curl http://your-gateway:8088/system/zerobus/diagnostics
```

#### POST /system/zerobus/config

Update configuration.

```bash
curl -X POST http://your-gateway:8088/system/zerobus/config \
  -H "Content-Type: application/json" \
  -d @config.json
```

### Log Files

**Location**: `/var/log/ignition/wrapper.log` (Linux) or `C:\Program Files\Ignition\logs\wrapper.log` (Windows)

**View Zerobus logs:**
```bash
tail -f /var/log/ignition/wrapper.log | grep Zerobus
```

**Enable debug logging:**
```json
{
  "debugLogging": true
}
```

### Key Metrics to Monitor

| Metric | What to Monitor | Alert Threshold |
|--------|----------------|-----------------|
| Stream State | Should be `OPENED` | Alert if `CLOSED` > 5 min |
| Total Failures | Should be `0` | Alert if > 0 |
| Total Events Dropped | Should be `0` | Alert if > 100 |
| Queue Size | Should be < 80% of max | Alert if > 8000 (default maxQueueSize: 10000) |
| Last Successful Send | Should be < 5 seconds | Alert if > 60 seconds |

---

## Troubleshooting

### Problem: Module Won't Start

**Symptoms:** Module status shows "Error" or "Failed to Load"

**Solutions:**
1. Check Ignition version (8.3.x required)
2. Review logs: `tail -100 /var/log/ignition/wrapper.log | grep Zerobus`
3. Verify module file integrity
4. Check for conflicting modules
5. Restart gateway: `sudo systemctl restart ignition`

### Problem: Can't Connect to Databricks

**Symptoms:** `Stream State: CLOSED` or `Initialized: false` or OAuth errors

**Solutions:**
1. **Verify Service Principal has all required permissions:**
   ```sql
   -- Grant catalog access
   GRANT USE CATALOG ON CATALOG your_catalog TO `service-principal-uuid`;
   
   -- Grant schema access
   GRANT USE SCHEMA ON SCHEMA your_catalog.your_schema TO `service-principal-uuid`;
   
   -- Grant table modify (for writing)
   GRANT MODIFY ON TABLE your_catalog.your_schema.tag_events TO `service-principal-uuid`;
   
   -- Grant table select (for reading metadata)
   GRANT SELECT ON TABLE your_catalog.your_schema.tag_events TO `service-principal-uuid`;
   ```
   
   **Note**: Use the Service Principal's UUID (e.g., `6ff2b11b-fdb8-4c2c-9360-ed105d5f6dcb`), not the display name.

2. **Verify Service Principal is added to workspace:**
   - Go to: **Workspace Settings → Identity and Access → Service Principals**
   - Confirm the Service Principal is listed and has **Workspace access** enabled

3. **Check network connectivity:**
   ```bash
   # From Ignition server
   curl -v https://your-workspace.cloud.databricks.com
   ping workspace-id.zerobus.region.cloud.databricks.com
   ```

4. **Check Zerobus endpoint format:**
   - Correct: `1444828305810485.zerobus.us-west-2.cloud.databricks.com`
   - Wrong: `https://...` or `/api/...`

### Problem: No Events Being Sent

**Symptoms:** `Total Events Sent: 0` despite tags changing

**Solutions:**
1. **Verify tags are subscribed:**
   ```bash
   curl http://your-gateway:8088/system/zerobus/diagnostics | grep "Subscribed Tags"
   ```
   Should show: `Subscribed Tags: N` (N > 0)

2. **Check tag paths are correct:**
   - Use Ignition Designer Tag Browser to verify exact path structure
   - **Must include folder structure**: `[Provider]Folder/TagName`
   - Common mistakes:
     - ❌ Missing folder: `[Sample_Tags]Sine0` 
     - ✅ Correct with folder: `[Sample_Tags]Sine/Sine0`
     - ❌ Wrong provider: `[default]Sample_Tags/Sine0`
     - ✅ Correct provider: `[Sample_Tags]Sine/Sine0`

3. **Verify tags are changing:**
   - If `onlyOnChange: true`, events only sent when values change
   - Try `onlyOnChange: false` for testing

4. **Enable debug logging:**
   ```json
   {
     "debugLogging": true
   }
   ```
   Then check logs for polling activity.

### Problem: Events Dropped

**Symptoms:** `Total Events Dropped > 0`

**Solutions:**
1. **Increase queue size:**
   ```json
   {
     "maxQueueSize": 50000
   }
   ```

2. **Increase batch size (faster flushing):**
   ```json
   {
     "batchSize": 50
   }
   ```

3. **Decrease flush interval:**
   ```json
   {
     "batchFlushIntervalMs": 500
   }
   ```

4. **Enable onlyOnChange (reduce events):**
   ```json
   {
     "onlyOnChange": true
   }
   ```

### Problem: High Latency

**Symptoms:** `Last Successful Send` > 10 seconds

**Solutions:**
1. **Decrease flush interval:**
   ```json
   {
     "batchFlushIntervalMs": 500
   }
   ```

2. **Decrease batch size:**
   ```json
   {
     "batchSize": 5
   }
   ```

3. **Check network latency:**
   ```bash
   ping workspace-id.zerobus.region.cloud.databricks.com
   ```

4. **Check Databricks workspace performance**

### Getting Help

If you're still experiencing issues:

1. **Collect diagnostics:**
   ```bash
   curl http://your-gateway:8088/system/zerobus/diagnostics > diagnostics.txt
   tail -500 /var/log/ignition/wrapper.log | grep Zerobus > logs.txt
   ```

2. **Check GitHub Issues**: [github.com/your-org/lakeflow-ignition-zerobus-connector/issues](https://github.com/pravinva/lakeflow-ignition-zerobus-connector/issues)

3. **Contact Support**: Include diagnostics and logs

---

## Advanced Configuration

### Performance Testing Results

**Tested on Ignition 8.3.2 (December 2024):**

| Configuration | Tags | Throughput | Queue | Dropped | Result |
|--------------|------|------------|-------|---------|--------|
| Low Volume | 3 tags @ 1Hz | 6 events/sec | 0.03% | 0 | ✅ Stable |
| Medium Volume | 20 tags @ 1Hz | 20 events/sec | 6-14% | 0 | ✅ Stable |
| Stress Test | 20 tags continuous | 600 events/30sec | <15% | 0 | ✅ Stable |

**Bug Fix Applied (December 2024):**
- Fixed synchronized deadlock causing queue overflow
- Before: 10,000/10,000 queue, 5,000+ drops, 0 throughput
- After: <15% queue usage, 0 drops, continuous streaming

### Production Deployment Configurations

#### 1. Low Volume (< 1,000 events/sec)

**Use Case**: Small plant, monitoring 100-500 tags

```json
{
  "batchSize": 50,
  "batchFlushIntervalMs": 500,
  "maxQueueSize": 10000,
  "onlyOnChange": true
}
```

#### 2. Medium Volume (1,000-5,000 events/sec)

**Use Case**: Medium facility, 500-1,000 tags

```json
{
  "batchSize": 100,
  "batchFlushIntervalMs": 500,
  "maxQueueSize": 50000,
  "maxEventsPerSecond": 10000,
  "onlyOnChange": true
}
```

#### 3. High Volume Single Gateway (5,000-10,000 events/sec)

**Use Case**: Large facility, 1,000-3,000 tags, one gateway

```json
{
  "tagSelectionMode": "folder",
  "tagFolderPath": "[default]Production",
  "includeSubfolders": true,
  "batchSize": 100,
  "batchFlushIntervalMs": 200,
  "maxQueueSize": 100000,
  "maxEventsPerSecond": 15000,
  "onlyOnChange": true
}
```

**JVM Tuning Required** - Add to `ignition.conf`:
```bash
wrapper.java.additional.100=-Xms4G
wrapper.java.additional.101=-Xmx8G
```

#### 4. Multi-Gateway Architecture (10,000+ events/sec)

**Use Case**: Multiple sites or very large facility

**Gateway 1 Configuration:**
```json
{
  "sourceSystemId": "ignition-gateway-site-A",
  "batchSize": 100,
  "batchFlushIntervalMs": 500,
  "maxQueueSize": 50000,
  "onlyOnChange": true
}
```

**Gateway 2 Configuration:**
```json
{
  "sourceSystemId": "ignition-gateway-site-B",
  "batchSize": 100,
  "batchFlushIntervalMs": 500,
  "maxQueueSize": 50000,
  "onlyOnChange": true
}
```

**All gateways write to the same Delta table.**

**Scaling Table:**

| Target Throughput | Architecture | # Gateways | Tags per Gateway |
|-------------------|--------------|------------|------------------|
| < 5K events/sec | Single Gateway | 1 | 500-1,000 |
| 5K-10K events/sec | Single Gateway (tuned) | 1 | 1,000-3,000 |
| 10K-30K events/sec | Multi-Gateway | 3-6 | 500-1,000 each |
| 30K-100K events/sec | Multi-Gateway | 10-20 | 500-1,000 each |

### Monitoring at Scale

**Health Check Queries:**

```sql
-- Ingestion rate per gateway (last minute)
SELECT 
  source_system,
  COUNT(*) as events,
  COUNT(*) / 60.0 as events_per_sec
FROM ignition_demo.scada_data.tag_events
WHERE ingestion_timestamp > current_timestamp() - INTERVAL 1 MINUTE
GROUP BY source_system;

-- Data quality by gateway
SELECT 
  source_system,
  quality,
  COUNT(*) as count
FROM ignition_demo.scada_data.tag_events
WHERE ingestion_timestamp > current_timestamp() - INTERVAL 1 HOUR
GROUP BY source_system, quality;

-- Latest data freshness
SELECT 
  source_system,
  MAX(ingestion_timestamp) as latest_event,
  DATEDIFF(SECOND, MAX(ingestion_timestamp), CURRENT_TIMESTAMP()) as seconds_ago
FROM ignition_demo.scada_data.tag_events
GROUP BY source_system;
```

**Alert Thresholds:**

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| Queue Size | > 70% | > 90% | Increase batch size or add gateway |
| Dropped Events | > 0 | > 100 | Increase queue size |
| Last Send | > 5 sec | > 30 sec | Check network/Databricks |
| Data Lag | > 2 min | > 5 min | Check gateway status |

### Best Practices

**1. Use `onlyOnChange: true` in Production**
- Reduces data volume by 10-100x
- Lowers costs (compute, storage, network)
- Only sends meaningful changes

**2. Set Appropriate Scan Classes**
- Critical alarms: 100ms
- Process values: 1 second
- Slow-changing values: 5-10 seconds
- Static values: Don't subscribe

**3. Tag Selection Strategy**
- Use `folder` mode for organized tag structures
- Use `explicit` mode for specific critical tags
- Avoid `pattern` mode with broad wildcards (performance)

**4. Monitor Gateway Health**
```bash
# Add to cron for automated checks
*/5 * * * * curl -s http://localhost:8088/system/zerobus/diagnostics | \
  grep -E "Queue Size|Dropped" | \
  mail -s "Zerobus Status" ops@company.com
```

**5. Test Configuration Changes**
- Always test in dev/staging environment first
- Monitor queue depth and dropped events after changes
- Gradually increase tag count to find limits

### Disabling Module Temporarily

```json
{
  "enabled": false
}
```

Or via Ignition Web UI:
1. Go to: `Config → System → Modules`
2. Find: "Zerobus Connector"
3. Click: "Disable"

---

## Support & Documentation

### Documentation

- **Main README**: [../README.md](../README.md)
- **Quick Start**: [QUICKSTART.md](QUICKSTART.md)
- **Installation Guide**: [INSTALLATION.md](INSTALLATION.md)
- **Event-Based Documentation**: [EVENT_VS_POLLING_FINAL.md](EVENT_VS_POLLING_FINAL.md)
- **Architecture**: [architect.md](architect.md)
- **Developer Guide**: [developer.md](developer.md)
- **Testing Guide**: [tester.md](tester.md)

### Examples

- **Configuration Examples**: [../examples/example-config.json](../examples/example-config.json)
- **SQL Examples**: [../examples/create-delta-table.sql](../examples/create-delta-table.sql)
- **Setup Scripts**: [../setup/](../setup/)

### Support Channels

- **GitHub Issues**: [Report bugs or request features](https://github.com/pravinva/lakeflow-ignition-zerobus-connector/issues)
- **GitHub Discussions**: [Ask questions or share experiences](https://github.com/pravinva/lakeflow-ignition-zerobus-connector/discussions)
- **Databricks Support**: Contact your Databricks representative

### Release Notes

See [GitHub Releases](https://github.com/pravinva/lakeflow-ignition-zerobus-connector/releases) for:
- Version history
- Bug fixes
- New features
- Upgrade instructions

---

## Summary

### What You Should Know

✅ **Installation**: 3 steps - download, install, configure  
✅ **Configuration**: REST API or configuration file  
✅ **Verification**: Diagnostics endpoint + Databricks queries  
✅ **Monitoring**: REST API, logs, and key metrics  
✅ **Troubleshooting**: Common issues and solutions

### Next Steps

1. **Install** the module in your Ignition Gateway
2. **Configure** with your Databricks credentials
3. **Verify** data is flowing using diagnostics
4. **Monitor** regularly to ensure reliability
5. **Optimize** configuration based on your use case

### Need Help?

- Check the [troubleshooting section](#troubleshooting)
- Review the [documentation](#support--documentation)
- Open an [issue on GitHub](https://github.com/pravinva/lakeflow-ignition-zerobus-connector/issues)

---

**Happy Streaming!** 🚀

*For questions or feedback, contact the development team or open a GitHub issue.*

