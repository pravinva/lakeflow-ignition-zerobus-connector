# Ignition Zerobus Connector - Complete User Guide

**Version**: 1.0.0  
**Status**: Production Ready  
**Last Updated**: December 2025

---

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Event Streams Setup](#event-streams-setup)
- [Verification](#verification)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)
- [Performance Tuning](#performance-tuning)
- [Security](#security)
- [FAQ](#faq)

---

## Overview

### What This Module Does

The Ignition Zerobus Connector streams SCADA tag data from Ignition Gateway to Databricks Delta tables in real-time using an **event-driven architecture**.

**Key Features:**
- ✅ **Event-Driven**: Uses native Ignition Event Streams (8.3+) - no polling
- ✅ **Real-Time**: Sub-second latency from tag change to Databricks
- ✅ **Scalable**: Tested up to 30,000 tags/second
- ✅ **Reliable**: Zero data loss, automatic retry, backpressure handling
- ✅ **Secure**: OAuth 2.0 M2M authentication with Service Principals
- ✅ **Simple**: Automated setup scripts, minimal configuration

### Architecture

```
Ignition Tags
    ↓ (value changes)
Event Streams (native Ignition 8.3+)
    ↓ (Script Handler POSTs batch)
Module REST API (/system/zerobus/ingest/batch)
    ↓ (Queue & Batch)
Zerobus SDK (gRPC streaming)
    ↓
Databricks Delta Table
```

**No Polling** - Pure event-driven using native Ignition capabilities.

---

## Prerequisites

### Ignition Gateway
- **Version**: 8.3.0 or later (tested on 8.3.2)
- **License**: Standard or higher
- **Network**: Outbound HTTPS access to Databricks

### Databricks Workspace
- **Zerobus Enabled**: Contact Databricks support to enable
- **Service Principal**: Created with proper permissions
- **Target Table**: Delta table created in Unity Catalog

### Required Information

Before starting, gather:

1. **Databricks Workspace URL**: `https://your-workspace.cloud.databricks.com`
2. **Workspace ID**: Numeric ID (see [Finding Workspace ID](#finding-workspace-id))
3. **Region**: e.g., `us-west-2`, `westus2`, `us-central1`
4. **Service Principal Client ID**: From Databricks account console
5. **Service Principal Secret**: From Databricks account console
6. **Target Table**: `catalog.schema.table`

---

## Installation

### Step 1: Download Module

Download `Ignition-Zerobus-unsigned.modl` from the GitHub releases page.

### Step 2: Install Module

#### Option A: Via Gateway Web Interface

1. Open browser: `http://your-gateway:8088`
2. Login as admin
3. Go to: **Config** → **System** → **Modules**
4. Click **Install or Upgrade a Module**
5. Select the `.modl` file
6. Click **Install**
7. Wait for Gateway to restart

#### Option B: Via Command Line

```bash
# Copy module to Gateway
sudo cp Ignition-Zerobus-unsigned.modl /usr/local/ignition/user-lib/modules/

# Restart Gateway
sudo /usr/local/ignition/ignition.sh restart

# Wait 30 seconds for startup
sleep 30
```

### Step 3: Verify Installation

```bash
curl http://localhost:8088/system/zerobus/diagnostics
```

Should return module diagnostics (even if not configured yet).

---

## Configuration

### Finding Workspace ID

Your Databricks Workspace ID is a numeric identifier needed for the Zerobus endpoint.

**Method 1: From URL**
```
https://xxxxx.cloud.databricks.com/?o=1444828305810485
                                        ^^^^^^^^^^^^^^^^^
                                        Your Workspace ID
```

**Method 2: Databricks CLI**
```bash
databricks workspace get-status
```

**Method 3: Workspace Settings**
1. Go to **Settings** → **Workspace Admin**
2. Look for **Workspace ID**

### Zerobus Endpoint Format

⚠️ **Critical**: The Zerobus endpoint must use this exact format:

```
WORKSPACE_ID.zerobus.REGION.cloud.databricks.com
```

**Examples by Cloud Provider:**

**AWS:**
```
1444828305810485.zerobus.us-west-2.cloud.databricks.com
1444828305810485.zerobus.us-east-1.cloud.databricks.com
```

**Azure:**
```
1444828305810485.zerobus.westus2.azuredatabricks.net
1444828305810485.zerobus.eastus2.azuredatabricks.net
```

**GCP:**
```
1444828305810485.zerobus.us-central1.gcp.databricks.com
```

**❌ These formats DON'T work:**
- `https://workspace.cloud.databricks.com/api/2.0/zerobus/streams/ingest`
- `https://workspace.cloud.databricks.com`
- `workspace-name.zerobus.region.cloud.databricks.com` (must use numeric ID)

### Create Configuration File

```bash
cat > my-config.json <<'EOF'
{
  "enabled": true,
  "workspaceUrl": "https://YOUR-WORKSPACE.cloud.databricks.com",
  "zerobusEndpoint": "WORKSPACE_ID.zerobus.REGION.cloud.databricks.com",
  "oauthClientId": "YOUR-SERVICE-PRINCIPAL-CLIENT-ID",
  "oauthClientSecret": "YOUR-SERVICE-PRINCIPAL-SECRET",
  "catalogName": "YOUR_CATALOG",
  "schemaName": "YOUR_SCHEMA",
  "tableName": "YOUR_TABLE",
  "targetTable": "CATALOG.SCHEMA.TABLE",
  "sourceSystemId": "ignition-gateway-001",
  "batchSize": 100,
  "batchFlushIntervalMs": 5000,
  "maxQueueSize": 10000
}
EOF
```

### Apply Configuration

```bash
curl -X POST http://localhost:8088/system/zerobus/config \
  -H "Content-Type: application/json" \
  -d @my-config.json
```

### Verify Configuration

```bash
curl http://localhost:8088/system/zerobus/diagnostics
```

Should show:
- `Module Enabled: true`
- `Initialized: true`
- `Connected: true`
- `Stream State: OPENED`

---

## Event Streams Setup

Event Streams are the recommended way to send data to the module (Ignition 8.3+).

### Quick Setup

**Step 1: Create Event Stream in Designer**

1. Open Ignition Designer
2. Project Browser → **Event Streams**
3. Right-click → **New Event Stream**
4. Name: `zerobus_stream`
5. Click **Save** (leave empty for now)
6. Close Designer

**Step 2: Configure Event Stream via Script**

```bash
# Create tag list
cat > my-tags.txt <<'EOF'
[default]Equipment/Pump01/Temperature
[default]Equipment/Pump01/Pressure
[default]Equipment/Tank01/Level
EOF

# Run configuration script
./scripts/configure_eventstream.py \
  --name zerobus_stream \
  --project MyProject \
  --tag-file my-tags.txt
```

**Step 3: Restart Gateway**

```bash
sudo /usr/local/ignition/ignition.sh restart
```

**Step 4: Enable Event Stream**

1. Open Designer
2. Event Streams → `zerobus_stream`
3. Verify configuration is populated
4. Toggle **Enabled** switch
5. Save

### Manual Setup

See [docs/EVENT_STREAMS_SETUP.md](docs/EVENT_STREAMS_SETUP.md) for detailed manual configuration steps.

### Alternative: Gateway Script

If you prefer not to use Event Streams, see [docs/ZERO_CONFIG_SETUP.md](docs/ZERO_CONFIG_SETUP.md) for a Gateway Script approach.

---

## Verification

### Check Module Status

```bash
curl http://localhost:8088/system/zerobus/diagnostics
```

**Expected output:**
```
=== Zerobus Module Diagnostics ===
Module Enabled: true

=== Zerobus Client Diagnostics ===
Initialized: true
Connected: true
Stream State: OPENED
Total Events Sent: (increasing)
Total Batches Sent: (increasing)
Total Failures: 0

=== Event Processing Service Diagnostics ===
Running: true
Total Events Received: (increasing)
Total Events Dropped: 0
```

### Check Event Stream

In Designer:
1. Event Streams → Your stream
2. Status panel should show:
   - Events Received: (incrementing)
   - Handler Execution: (showing times)
   - No errors

### Check Databricks

```sql
SELECT 
  tag_path,
  numeric_value,
  quality,
  event_time,
  source_system_id
FROM your_catalog.your_schema.your_table
ORDER BY event_time DESC
LIMIT 100;
```

You should see recent tag data!

---

## Monitoring

### Module Diagnostics Endpoint

```bash
curl http://localhost:8088/system/zerobus/diagnostics
```

**Key Metrics:**
- `Total Events Sent` - Should be increasing
- `Total Failures` - Should be 0
- `Queue Size` - Should be < max (not backing up)
- `Total Events Dropped` - Should be 0
- `Last Successful Send` - Should be recent

### Event Stream Metrics

In Designer, Event Streams status panel shows:
- Events received per second
- Handler execution times
- Error counts
- Buffer utilization

### Databricks Monitoring

```sql
-- Event count by hour
SELECT 
  date_trunc('hour', event_time) as hour,
  COUNT(*) as event_count
FROM your_catalog.your_schema.your_table
WHERE event_time >= current_timestamp() - INTERVAL 24 HOURS
GROUP BY hour
ORDER BY hour DESC;

-- Event count by tag
SELECT 
  tag_path,
  COUNT(*) as event_count,
  MAX(event_time) as last_event
FROM your_catalog.your_schema.your_table
WHERE event_time >= current_timestamp() - INTERVAL 1 HOUR
GROUP BY tag_path
ORDER BY event_count DESC;
```

### Alerts

Set up alerts for:
- `Total Failures > 0`
- `Total Events Dropped > 0`
- `Queue Size > 80% of max`
- `Last Successful Send > 60 seconds ago`

---

## Troubleshooting

### Module Not Connected

**Symptoms:**
```
Connected: false
Last Error: UNAUTHENTICATED or UNIMPLEMENTED
```

**Solutions:**

1. **Check Zerobus Endpoint Format**
   ```bash
   # Must be: WORKSPACE_ID.zerobus.REGION.cloud.databricks.com
   # NOT: https://workspace.cloud.databricks.com/...
   ```

2. **Verify Endpoint Resolves**
   ```bash
   nslookup WORKSPACE_ID.zerobus.REGION.cloud.databricks.com
   ```

3. **Check Service Principal Credentials**
   ```bash
   # Test OAuth token
   curl -X POST https://YOUR-WORKSPACE.cloud.databricks.com/oidc/v1/token \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "grant_type=client_credentials" \
     -d "client_id=YOUR_CLIENT_ID" \
     -d "client_secret=YOUR_SECRET" \
     -d "scope=all-apis"
   ```

4. **Verify Zerobus is Enabled**
   - Contact Databricks support to confirm Zerobus is enabled on your workspace

### No Events Reaching Databricks

**Symptoms:**
```
Total Events Received: 100+
Total Events Sent: 0
```

**Solutions:**

1. **Check Module is Enabled**
   ```bash
   curl http://localhost:8088/system/zerobus/config | grep enabled
   ```

2. **Check Event Stream is Enabled**
   - Open Designer
   - Event Streams → Your stream
   - Verify **Enabled** toggle is ON

3. **Check for Errors in Event Stream**
   - Designer → Event Streams → Status panel
   - Look for red error indicators

4. **Check Gateway Logs**
   ```bash
   tail -100 /usr/local/ignition/logs/wrapper.log | grep -i "zerobus\|error"
   ```

### Permission Errors

**Symptoms:**
```
Last Error: PERMISSION_DENIED
```

**Solution: Grant Service Principal Permissions**

```sql
-- Get Service Principal UUID (not the client ID!)
SHOW PRINCIPALS;

-- Grant permissions (use UUID from above)
GRANT USE CATALOG ON CATALOG your_catalog TO `service-principal-uuid`;
GRANT USE SCHEMA ON SCHEMA your_catalog.your_schema TO `service-principal-uuid`;
GRANT MODIFY ON TABLE your_catalog.your_schema.your_table TO `service-principal-uuid`;
GRANT SELECT ON TABLE your_catalog.your_schema.your_table TO `service-principal-uuid`;
```

### Event Stream Not Configured

**Symptoms:**
- Event Stream shows empty in Designer after running script

**Solution:**
```bash
# Restart Gateway to reload project files
sudo /usr/local/ignition/ignition.sh restart
```

### High Queue Size

**Symptoms:**
```
Queue Size: 9500/10000
```

**Solutions:**

1. **Increase Batch Size**
   ```json
   {
     "batchSize": 500
   }
   ```

2. **Decrease Flush Interval**
   ```json
   {
     "batchFlushIntervalMs": 1000
   }
   ```

3. **Increase Queue Size**
   ```json
   {
     "maxQueueSize": 50000
   }
   ```

### Events Dropped

**Symptoms:**
```
Total Events Dropped: 50
```

**Cause:** Queue is full, events are being rejected

**Solutions:**
- Increase queue size
- Increase batch size
- Decrease flush interval
- Check Databricks connectivity

---

## Performance Tuning

### Low Latency Configuration

For minimal latency (< 1 second):

```json
{
  "batchSize": 10,
  "batchFlushIntervalMs": 500,
  "maxQueueSize": 1000
}
```

Event Stream buffer:
```
Debounce: 10ms
Max Wait: 100ms
```

### High Throughput Configuration

For maximum throughput (30,000+ tags/sec):

```json
{
  "batchSize": 1000,
  "batchFlushIntervalMs": 1000,
  "maxQueueSize": 100000
}
```

Event Stream buffer:
```
Debounce: 50ms
Max Wait: 500ms
Max Queue Size: 50000
```

### JVM Tuning

For high-volume deployments, increase Gateway heap:

Edit `/usr/local/ignition/data/ignition.conf`:
```
wrapper.java.maxmemory=4096
```

Restart Gateway after changes.

---

## Security

### Service Principal Best Practices

1. **Least Privilege**: Grant only required permissions
2. **Rotation**: Rotate secrets regularly (every 90 days)
3. **Separate Principals**: Use different principals per environment
4. **Audit**: Monitor Service Principal usage in Databricks

### Network Security

1. **Firewall**: Allow outbound HTTPS (443) to Databricks
2. **TLS**: All communication is encrypted (gRPC over TLS)
3. **No Inbound**: Module doesn't require inbound connections

### Credential Storage

**Option 1: Configuration File** (Development)
- Store in `config.json`
- Secure file permissions: `chmod 600 config.json`

**Option 2: Environment Variables** (Production)
- Set via Gateway environment
- Reference in configuration

**Option 3: Secrets Manager** (Enterprise)
- Use Databricks Secrets
- Reference via Ignition Secret Provider

---

## FAQ

### Q: Do I need Event Streams or can I use the old polling method?

**A:** Event Streams are strongly recommended for Ignition 8.3+. The module no longer includes built-in polling. Event Streams provide better performance, lower latency, and are the native Ignition approach.

### Q: Can I use this with Ignition 8.1 or 8.2?

**A:** The module requires Ignition 8.3.0+ for Event Streams support. For older versions, you would need to use the Gateway Script approach (see [docs/ZERO_CONFIG_SETUP.md](docs/ZERO_CONFIG_SETUP.md)).

### Q: How do I monitor data quality?

**A:** Check the `quality` field in Databricks:
```sql
SELECT quality, COUNT(*) 
FROM your_table 
GROUP BY quality;
```

Good quality events should show `GOOD` or quality code `192`.

### Q: Can I filter which tag changes are sent?

**A:** Yes, in the Event Stream configuration:
- Use tag path patterns
- Enable "Value Changed" trigger only
- Add filter stage in Event Stream

### Q: What happens if Databricks is unavailable?

**A:** The module will:
1. Queue events (up to `maxQueueSize`)
2. Retry with exponential backoff
3. Drop oldest events if queue fills (logged)

### Q: How do I update the module?

**A:**
```bash
# 1. Download new version
# 2. Install via Gateway web interface or:
sudo cp New-Version.modl /usr/local/ignition/user-lib/modules/
sudo /usr/local/ignition/ignition.sh restart
```

Configuration is preserved across updates.

### Q: Can I send data to multiple Databricks tables?

**A:** Yes, create multiple Event Streams, each with its own module instance (requires code modification) or use a single table and filter in Databricks.

### Q: What's the cost of running this?

**A:**
- **Ignition**: No additional licensing required
- **Databricks**: Zerobus ingest is included, storage costs apply
- **Network**: Minimal egress from Gateway

---

## Support & Documentation

### Documentation
- **[QUICK_START.md](QUICK_START.md)** - 10-minute deployment
- **[AUTOMATION_SETUP_GUIDE.md](AUTOMATION_SETUP_GUIDE.md)** - Multi-environment automation
- **[docs/EVENT_STREAMS_SETUP.md](docs/EVENT_STREAMS_SETUP.md)** - Detailed Event Streams guide
- **[docs/ZERO_CONFIG_SETUP.md](docs/ZERO_CONFIG_SETUP.md)** - Gateway Script alternative

### Getting Help

1. **Check Logs**: `/usr/local/ignition/logs/wrapper.log`
2. **Check Diagnostics**: `curl http://localhost:8088/system/zerobus/diagnostics`
3. **GitHub Issues**: Report bugs or request features
4. **Databricks Support**: For Zerobus-specific issues

### Version History

See [RELEASE_NOTES_v1.0.0.md](RELEASE_NOTES_v1.0.0.md) for changelog.

---

**Last Updated**: December 2025  
**Module Version**: 1.0.0  
**Ignition Version**: 8.3.0+

