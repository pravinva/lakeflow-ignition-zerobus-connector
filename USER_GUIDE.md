# Ignition Zerobus Connector - Complete User Guide

**Version**: 1.0.0  
**Status**: Production Ready  
**Last Updated**: December 2025

---

## 🎯 Choose Your Setup Path

**This guide covers both Ignition 8.1/8.2 and 8.3+ setups.**

### Quick Decision

| Your Ignition Version | Setup Method | Guide Section |
|----------------------|--------------|---------------|
| **8.3+** | Event Streams | [8.3+ Setup](#setup-for-ignition-83) |
| **8.1 or 8.2** | Gateway Scripts | [8.1/8.2 Setup](#setup-for-ignition-8182) |

---

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Installation (Common for Both Versions)](#installation-common-for-both-versions)
- [Setup for Ignition 8.3+](#setup-for-ignition-83)
- [Setup for Ignition 8.1/8.2](#setup-for-ignition-8182)
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
- ✅ **Event-Driven**: No polling, instant tag change notification
- ✅ **Real-Time**: Sub-second latency from tag change to Databricks
- ✅ **Scalable**: Tested up to 30,000 tags/second
- ✅ **Reliable**: Zero data loss, automatic retry, backpressure handling
- ✅ **Secure**: OAuth 2.0 M2M authentication with Service Principals
- ✅ **Universal**: Works with Ignition 8.1, 8.2, and 8.3+

### Architecture Comparison

#### Ignition 8.3+ (Event Streams)

```
Ignition Tags
    ↓ (value changes)
Event Streams (native Ignition 8.3+ feature)
    ↓ (Script Handler POSTs batch)
Module REST API (/system/zerobus/ingest/batch)
    ↓ (Queue & Batch)
Zerobus SDK (gRPC streaming)
    ↓
Databricks Delta Table
```

**Benefits**:
- Visual configuration in Designer
- Advanced filtering and transformation
- Per-project customization

#### Ignition 8.1/8.2 (Gateway Scripts)

```
Ignition Tags
    ↓ (value changes)
Gateway Tag Change Script (built-in feature)
    ↓ (Script POSTs batch)
Module REST API (/system/zerobus/ingest/batch)
    ↓ (Queue & Batch)
Zerobus SDK (gRPC streaming)
    ↓
Databricks Delta Table
```

**Benefits**:
- Works on 8.1, 8.2, and 8.3
- Simpler setup (Web UI only)
- Gateway-level (survives project changes)
- Fully scriptable

**Both approaches are event-driven with identical performance!**

---

## Prerequisites

### Ignition Gateway

| Requirement | 8.3+ | 8.1/8.2 |
|-------------|------|---------|
| **Minimum Version** | 8.3.0 | 8.1.0 |
| **License** | Standard or higher | Standard or higher |
| **Network** | Outbound HTTPS to Databricks | Outbound HTTPS to Databricks |
| **Trigger Mechanism** | Event Streams | Gateway Tag Change Scripts |

### Databricks Workspace

**Same for all versions:**
- **Zerobus Enabled**: Contact Databricks support to enable
- **Service Principal**: Created with proper permissions
- **Target Table**: Delta table created in Unity Catalog

### Required Information

Gather before starting:

1. **Databricks Workspace URL**: `https://your-workspace.cloud.databricks.com`
2. **Workspace ID**: Numeric ID (see [docs/WORKSPACE_ID_GUIDE.md](docs/WORKSPACE_ID_GUIDE.md))
3. **Region**: e.g., `us-west-2`, `westus2`, `us-central1`
4. **Service Principal Client ID**: From Databricks account console
5. **Service Principal Secret**: From Databricks account console
6. **Target Table**: `catalog.schema.table`
7. **Tag Paths**: List of tags to monitor (e.g., `[Sample_Tags]Sine/Sine0`)

---

## Installation (Common for Both Versions)

### Step 1: Download Module

Download the pre-built module:

```bash
# From GitHub
https://github.com/pravinva/lakeflow-ignition-zerobus-connector/raw/main/releases/zerobus-connector-1.0.0.modl
```

Or use `curl`:

```bash
curl -L -o zerobus-connector-1.0.0.modl \
  https://github.com/pravinva/lakeflow-ignition-zerobus-connector/raw/main/releases/zerobus-connector-1.0.0.modl
```

### Step 2: Install Module

**Via Gateway Web Interface:**

1. Open browser: `http://your-gateway:8088`
2. Login as admin
3. Go to: **Config** → **System** → **Modules**
4. Click **Install or Upgrade a Module**
5. Select `zerobus-connector-1.0.0.modl`
6. Click **Install**
7. Wait for Gateway to restart (1-2 minutes)

### Step 3: Verify Module Loaded

```bash
curl http://your-gateway:8088/system/zerobus/health
```

**Expected response:**
```json
{
  "status": "ok",
  "moduleLoaded": true,
  "version": "1.0.0"
}
```

### Step 4: Configure Module (Same for Both Versions)

**Option A: Via REST API (Recommended)**

```bash
curl -X POST http://your-gateway:8088/system/zerobus/config \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "workspaceUrl": "https://your-workspace.cloud.databricks.com",
    "zerobusEndpoint": "WORKSPACE_ID.zerobus.REGION.cloud.databricks.com",
    "oauthClientId": "YOUR_CLIENT_ID",
    "oauthClientSecret": "YOUR_SECRET",
    "catalogName": "your_catalog",
    "schemaName": "your_schema",
    "tableName": "your_table",
    "targetTable": "catalog.schema.table",
    "sourceSystemId": "ignition-gateway-001",
    "batchSize": 50,
    "batchFlushIntervalMs": 500,
    "maxQueueSize": 10000
  }'
```

**Option B: Via Web UI**

1. Go to: `http://your-gateway:8088/web/config/zerobus`
2. Fill in configuration form
3. Click **Save**

---

## Setup for Ignition 8.3+

### Overview

**Use Event Streams** - native Ignition 8.3 feature for event-driven data ingestion.

**Setup Time**: 5-10 minutes

### Step 1: Create Event Stream in Designer

1. Open Ignition Designer
2. **Project Browser** → Right-click **Event Streams** → **New Event Stream**
3. **Name**: `ZerobusTagStream`

### Step 2: Configure Source

1. **Source Type**: `Tag Event`
2. **Tag Paths**: Add your tags
   ```
   [Sample_Tags]Sine/Sine0
   [Sample_Tags]Sine/Sine1
   [Sample_Tags]Realistic/Realistic0
   ```
3. **Trigger Conditions**:
   - ☑ Value Changed
   - ☑ Quality Changed (optional)
4. **Scan Class**: Default or choose appropriate

### Step 3: Configure Encoder

1. **Type**: `String` (important - not JsonObject!)
2. **Encoding**: `UTF-8`

### Step 4: Configure Buffer

1. **Debounce**: `100` ms
2. **Capacity**: `1000` events
3. **Overflow Strategy**: `Block`

### Step 5: Add Script Handler

1. Click **Add Handler**
2. **Type**: `Script`
3. **Name**: `SendToZerobus`
4. **Script** (copy this):

```python
def onEventsReceived(events, state):
    """
    Send batched events to Zerobus module.
    This function is automatically called by Ignition Event Streams.
    """
    import system.net
    import system.util
    
    # Build batch payload
    batch = []
    for event in events:
        try:
            # Extract event metadata
            event_metadata = event.getMetadata()
            tag_path = str(event_metadata.get('tagPath', ''))
            tag_provider = str(event_metadata.get('provider', 'default'))
            
            # Extract qualified value
            qv = event.getValue()
            
            payload = {
                'tagPath': tag_path,
                'tagProvider': tag_provider,
                'value': qv.value,
                'quality': str(qv.quality),
                'qualityCode': int(qv.quality.getIntValue()),
                'timestamp': long(qv.timestamp.time),
                'dataType': type(qv.value).__name__
            }
            
            batch.append(payload)
        except Exception as e:
            logger = system.util.getLogger('EventStreams.Zerobus')
            logger.error('Error processing event: {}'.format(str(e)))
    
    # Send batch to module
    if batch:
        try:
            response = system.net.httpPost(
                url='http://localhost:8088/system/zerobus/ingest/batch',
                contentType='application/json',
                postData=system.util.jsonEncode(batch),
                timeout=10000
            )
            
            if hasattr(response, 'statusCode') and response.statusCode == 200:
                logger = system.util.getLogger('EventStreams.Zerobus')
                logger.info('Sent {} events to Zerobus'.format(len(batch)))
            else:
                logger = system.util.getLogger('EventStreams.Zerobus')
                logger.warn('Failed to send batch: HTTP {}'.format(
                    response.statusCode if hasattr(response, 'statusCode') else 'unknown'))
                
        except Exception as e:
            logger = system.util.getLogger('EventStreams.Zerobus')
            logger.error('Error sending batch: {}'.format(str(e)))
```

5. **Save** the Event Stream
6. **Enable** the Event Stream

### Step 6: Verify (see [Verification](#verification) section)

**Detailed Guide**: See [docs/EVENT_STREAMS_SETUP.md](docs/EVENT_STREAMS_SETUP.md)

---

## Setup for Ignition 8.1/8.2

### Overview

**Use Gateway Tag Change Scripts** - built-in Ignition feature available in all versions.

**Setup Time**: 10-15 minutes

### Step 1: Add Gateway Tag Change Script

**Via Gateway Web UI:**

1. Go to: `http://your-gateway:8088/web/config/scripting.gateway-event`
2. Click **Tag Change Scripts** tab
3. Click **"+"** to add new script
4. Fill in:
   - **Name**: `ZerobusTagForwarder`
   - **Enabled**: ☑ Yes

### Step 2: Configure Tag Paths

**In the Tag Paths section, add your tags:**

```
[Sample_Tags]Sine/Sine0
[Sample_Tags]Sine/Sine1
[Sample_Tags]Realistic/Realistic0
```

**Tips:**
- Include provider name: `[Sample_Tags]`
- Include folder path: `Sine/Sine0`
- Use wildcards: `[Sample_Tags]Sine/**` (all tags in Sine folder)

### Step 3: Add Script Code

**Copy and paste this complete script:**

```python
"""
Gateway Tag Change Script - Forwards tag changes to Zerobus module.
Ignition automatically calls tagChange() function when subscribed tags change.
"""

# Configuration
ZEROBUS_ENDPOINT = "http://localhost:8088/system/zerobus/ingest/batch"
BATCH_SIZE = 50
BATCH_TIMEOUT_MS = 1000

# Initialize global state (persists across function calls)
if 'event_batch' not in globals():
    event_batch = []
    last_flush_time = system.date.now()
    logger = system.util.getLogger('Gateway.ZerobusForwarder')
    logger.info('Zerobus Gateway Tag Forwarder initialized')

def tagChange(tagPath, tagValue, qualifiedValue, initialChange):
    """
    Called by Ignition when any subscribed tag changes.
    
    Args:
        tagPath: Full tag path
        tagValue: New tag value
        qualifiedValue: QualifiedValue object with value, quality, timestamp
        initialChange: True on first read (skip to avoid duplicates)
    """
    global event_batch, last_flush_time, logger
    
    # Skip initial values on startup
    if initialChange:
        return
    
    try:
        # Create event payload
        event = {
            'tagPath': str(tagPath),
            'tagProvider': tagPath.getSource() if hasattr(tagPath, 'getSource') else 'default',
            'value': tagValue,
            'quality': str(qualifiedValue.quality.getName()),
            'qualityCode': qualifiedValue.quality.getIntValue(),
            'timestamp': long(qualifiedValue.timestamp.getTime()),
            'dataType': type(tagValue).__name__
        }
        
        # Add to batch
        event_batch.append(event)
        
        # Check if should flush
        should_flush = False
        
        # Flush if batch size reached
        if len(event_batch) >= BATCH_SIZE:
            should_flush = True
        
        # Flush if timeout exceeded
        time_since_flush = system.date.secondsBetween(last_flush_time, system.date.now())
        if time_since_flush * 1000 >= BATCH_TIMEOUT_MS:
            should_flush = True
        
        if should_flush:
            flush_batch()
            
    except Exception as e:
        logger.error('Error processing tag change: {}'.format(str(e)))

def flush_batch():
    """Send batched events to Zerobus module"""
    global event_batch, last_flush_time, logger
    
    if not event_batch:
        return
    
    batch_to_send = list(event_batch)  # Copy
    event_batch = []  # Clear immediately
    last_flush_time = system.date.now()
    
    try:
        response = system.net.httpPost(
            url=ZEROBUS_ENDPOINT,
            contentType='application/json',
            postData=system.util.jsonEncode(batch_to_send),
            timeout=10000
        )
        
        if hasattr(response, 'statusCode') and response.statusCode == 200:
            logger.info('Sent {} events to Zerobus'.format(len(batch_to_send)))
        else:
            logger.warn('Failed to send batch: HTTP {}'.format(
                response.statusCode if hasattr(response, 'statusCode') else 'unknown'))
            # Re-add to batch on failure
            event_batch.extend(batch_to_send)
            
    except Exception as e:
        logger.error('Error sending batch: {}'.format(str(e)))
        # Re-add to batch on failure
        event_batch.extend(batch_to_send)
```

### Step 4: Save and Test

1. Click **Save**
2. Script will start immediately
3. Check Gateway logs for confirmation:
   ```bash
   tail -f /usr/local/ignition/logs/wrapper.log | grep "Gateway.ZerobusForwarder"
   ```

**Expected log output:**
```
INFO  | Gateway.ZerobusForwarder | Zerobus Gateway Tag Forwarder initialized
INFO  | Gateway.ZerobusForwarder | Sent 50 events to Zerobus
```

### Step 5: Verify (see [Verification](#verification) section)

**Detailed Guide**: See [docs/ZERO_CONFIG_SETUP.md](docs/ZERO_CONFIG_SETUP.md)

---

## Verification

### Check Module Status

```bash
curl http://your-gateway:8088/system/zerobus/diagnostics
```

**Expected response:**
```json
{
  "moduleVersion": "1.0.0",
  "enabled": true,
  "zerobusConnected": true,
  "totalEventsReceived": 1250,
  "totalEventsSent": 1250,
  "totalEventsFailed": 0,
  "queueSize": 0,
  "lastEventTime": "2025-12-11T12:30:45.123Z"
}
```

**Key indicators:**
- ✅ `zerobusConnected: true` - Module connected to Databricks
- ✅ `totalEventsReceived` > 0 - Events arriving from Event Streams/Gateway Script
- ✅ `totalEventsSent` > 0 - Events sent to Databricks
- ✅ `queueSize` < maxQueueSize - No backpressure

### Check Databricks Table

**In Databricks SQL Editor or Notebook:**

```sql
SELECT *
FROM your_catalog.your_schema.your_table
ORDER BY event_time DESC
LIMIT 100;
```

**Expected results:**
- Recent timestamps (within last minute)
- Tag paths matching your configuration
- Value, quality, and timestamp populated

### Troubleshooting Connection Issues

#### Module Not Connected

```json
{
  "zerobusConnected": false
}
```

**Fixes:**
1. Check Zerobus endpoint format: `WORKSPACE_ID.zerobus.REGION.cloud.databricks.com`
2. Verify Service Principal credentials
3. Check network connectivity to Databricks
4. Review Gateway logs: `/usr/local/ignition/logs/wrapper.log`

#### No Events Received

**For Ignition 8.3+ (Event Streams):**
1. Check Event Stream is enabled in Designer
2. Verify tag paths are correct
3. Check Event Stream diagnostics in Designer
4. Look for errors in Event Stream logs

**For Ignition 8.1/8.2 (Gateway Scripts):**
1. Check script is enabled: `Config → Scripting → Gateway Event Scripts`
2. Verify tag paths are correct (include provider and folder)
3. Check Gateway logs for script errors
4. Test with simple tag like `[Sample_Tags]Sine/Sine0`

---

## Monitoring

### Real-Time Diagnostics

**Check every 5 seconds:**
```bash
watch -n 5 'curl -s http://localhost:8088/system/zerobus/diagnostics | jq'
```

### Gateway Logs

**For Ignition 8.3+ (Event Streams):**
```bash
tail -f /usr/local/ignition/logs/wrapper.log | grep "EventStreams.Zerobus"
```

**For Ignition 8.1/8.2 (Gateway Scripts):**
```bash
tail -f /usr/local/ignition/logs/wrapper.log | grep "Gateway.ZerobusForwarder"
```

### Databricks Monitoring

```sql
-- Recent events count
SELECT COUNT(*), MAX(event_time) as latest
FROM your_catalog.your_schema.your_table
WHERE event_time > CURRENT_TIMESTAMP() - INTERVAL 5 MINUTES;

-- Events by tag
SELECT tag_path, COUNT(*) as event_count
FROM your_catalog.your_schema.your_table
WHERE event_time > CURRENT_TIMESTAMP() - INTERVAL 1 HOUR
GROUP BY tag_path
ORDER BY event_count DESC;
```

---

## Performance Tuning

### Batch Size

**Optimal values:**
- High-frequency tags (> 1 Hz): `batchSize: 100-200`
- Low-frequency tags (< 1 Hz): `batchSize: 20-50`

### Flush Interval

**Optimal values:**
- Real-time priority: `batchFlushIntervalMs: 250-500`
- Throughput priority: `batchFlushIntervalMs: 1000-2000`

### Queue Size

**Optimal values:**
- Normal load: `maxQueueSize: 10000`
- High load (30k tags/sec): `maxQueueSize: 50000-100000`

### For Event Streams (8.3+)

**Debounce setting:**
- High-frequency: 50-100 ms
- Low-frequency: 200-500 ms

### For Gateway Scripts (8.1/8.2)

**Script configuration:**
```python
BATCH_SIZE = 50        # Events per batch
BATCH_TIMEOUT_MS = 500 # Max wait time
```

---

## Security

### Service Principal Permissions

**Required permissions in Databricks:**

```sql
-- Grant access to catalog
GRANT USE CATALOG ON CATALOG your_catalog TO `SERVICE_PRINCIPAL_UUID`;

-- Grant access to schema
GRANT USE SCHEMA ON SCHEMA your_catalog.your_schema TO `SERVICE_PRINCIPAL_UUID`;

-- Grant modify on table
GRANT MODIFY ON TABLE your_catalog.your_schema.your_table TO `SERVICE_PRINCIPAL_UUID`;

-- Grant select (for validation)
GRANT SELECT ON TABLE your_catalog.your_schema.your_table TO `SERVICE_PRINCIPAL_UUID`;
```

**Find Service Principal UUID:**
```sql
SELECT user_name, user_id 
FROM system.access.users 
WHERE user_name LIKE '%your_sp_name%';
```

### OAuth Credentials

**Store securely:**
- Use environment variables or secure vault
- Never commit to version control
- Rotate regularly (90 days)

---

## FAQ

### Which setup should I use?

- **Ignition 8.3+**: Use Event Streams (recommended) or Gateway Scripts
- **Ignition 8.1/8.2**: Use Gateway Scripts (only option)

### Can I use both Event Streams and Gateway Scripts?

Yes, but not recommended. They will send duplicate events to Databricks.

### What's the performance difference?

None. Both approaches deliver identical performance (30,000+ events/sec).

### Can I migrate from Gateway Scripts to Event Streams?

Yes. When you upgrade to Ignition 8.3:
1. Create Event Stream with same tags
2. Test Event Stream
3. Disable Gateway Script

### Do I need to rebuild the module?

No. The pre-built module works with Ignition 8.1+. Only rebuild if you encounter compatibility issues (see [BUILD_FOR_YOUR_VERSION.md](BUILD_FOR_YOUR_VERSION.md)).

### How do I update tag paths?

**For Event Streams (8.3+):**
- Edit Event Stream in Designer → Source → Tag Paths

**For Gateway Scripts (8.1/8.2):**
- Gateway Web UI → Config → Scripting → Gateway Event Scripts → Edit script → Tag Paths

### What if my tags aren't sending data?

1. Check tag paths include provider: `[Sample_Tags]`
2. Include folder structure: `Sine/Sine0`
3. Verify tags exist in tag browser
4. Check module diagnostics: `totalEventsReceived` should increase

---

## Additional Resources

### Documentation
- **[IGNITION_8.1_SETUP.md](IGNITION_8.1_SETUP.md)** - Complete 8.1/8.2 setup
- **[QUICK_START.md](QUICK_START.md)** - Quick 8.3+ setup
- **[docs/EVENT_STREAMS_SETUP.md](docs/EVENT_STREAMS_SETUP.md)** - Event Streams details
- **[docs/ZERO_CONFIG_SETUP.md](docs/ZERO_CONFIG_SETUP.md)** - Gateway Scripts details
- **[VERSIONS_AND_COMPATIBILITY.md](VERSIONS_AND_COMPATIBILITY.md)** - Compatibility matrix
- **[onboarding/tilt/README.md](onboarding/tilt/README.md)** - Renewables end-to-end (Bronze → Silver → Gold)

### Support
- GitHub Issues: https://github.com/pravinva/lakeflow-ignition-zerobus-connector/issues
- Databricks Support: For Zerobus enablement and questions

---

**Last Updated**: December 2025  
**Module Version**: 1.0.0  
**Compatible with**: Ignition 8.1.0+
