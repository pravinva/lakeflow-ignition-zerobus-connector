# Setup for Ignition 8.1 / 8.2

**For customers running Ignition 8.1 or 8.2**

---

## ⚠️ Important: Event Streams Not Available

**Event Streams were introduced in Ignition 8.3.0**

If you're running Ignition 8.1 or 8.2:
- ❌ Event Streams don't exist
- ✅ Use **Gateway Tag Change Script** instead
- ✅ Same functionality, different trigger

---

## Quick Setup (10 Minutes)

### Step 1: Rebuild Module for 8.1

```bash
cd module
./gradlew clean buildModule

# Module will be at: build/modules/zerobus-connector-1.0.0.modl
```

### Step 2: Install Module

**Via Web UI:**
1. Go to: `http://gateway:8088/web/config/system.modules`
2. Click **Install or Upgrade a Module**
3. Upload: `zerobus-connector-1.0.0.modl`
4. Wait for Gateway restart

### Step 3: Configure Module

```bash
curl -X POST http://gateway:8088/system/zerobus/config \
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
    "sourceSystemId": "ignition-gateway-001"
  }'
```

### Step 4: Add Gateway Tag Change Script

**In Gateway Web Interface:**

1. Go to: `http://gateway:8088/web/config/scripting.gateway-event`
2. Click **"Tag Change Scripts"** tab
3. Click **"+"** to add new script
4. Fill in:
   - **Name**: `ZerobusForwarder`
   - **Tag Paths**: Your tags (e.g., `[default]Equipment/**`)
   - **Script**: Copy from below

**Script to paste:**

```python
import system.net
import system.util

# Configuration
GATEWAY_URL = "http://localhost:8088"
BATCH_SIZE = 50
BATCH_INTERVAL_MS = 500

# Initialize batch storage
if 'batch' not in state:
    state['batch'] = []
    state['lastFlush'] = system.date.now()

# Add event to batch
event_data = {
    'tagPath': str(tagPath),
    'tagProvider': str(tagPath.source) if hasattr(tagPath, 'source') else 'default',
    'value': newValue.value,
    'quality': str(newValue.quality),
    'qualityCode': int(newValue.quality.getIntValue()),
    'timestamp': long(newValue.timestamp.time),
    'dataType': type(newValue.value).__name__
}

state['batch'].append(event_data)

# Check if should flush
now = system.date.now()
time_since_flush = system.date.secondsBetween(state['lastFlush'], now) * 1000

should_flush = (
    len(state['batch']) >= BATCH_SIZE or 
    time_since_flush >= BATCH_INTERVAL_MS
)

if should_flush and len(state['batch']) > 0:
    try:
        response = system.net.httpPost(
            url=GATEWAY_URL + '/system/zerobus/ingest/batch',
            contentType='application/json',
            postData=system.util.jsonEncode(state['batch']),
            timeout=10000
        )
        
        if hasattr(response, 'statusCode') and response.statusCode == 200:
            logger = system.util.getLogger('Gateway.ZerobusForwarder')
            logger.info('Sent {} events'.format(len(state['batch'])))
        
        # Clear batch
        state['batch'] = []
        state['lastFlush'] = now
        
    except Exception as e:
        logger = system.util.getLogger('Gateway.ZerobusForwarder')
        logger.error('Error sending batch: {}'.format(str(e)))
```

5. Click **Save**

### Step 5: Verify

```bash
# Check module
curl http://gateway:8088/system/zerobus/diagnostics

# Should show:
# Total Events Received: (increasing)
# Total Events Sent: (increasing)
```

---

## Comparison: 8.1 vs 8.3

| Feature | Ignition 8.1/8.2 | Ignition 8.3+ |
|---------|------------------|---------------|
| **Module** | ✅ Works | ✅ Works |
| **Event Trigger** | Gateway Tag Change Script | Event Streams |
| **Configuration** | Web UI (Gateway Scripts) | Designer (Event Streams) |
| **Automation** | Manual script paste | Automated via scripts |
| **Flexibility** | Basic | Advanced (filters, transforms) |
| **Setup Time** | 10 minutes | 5 minutes |
| **Maintenance** | Gateway-level (easier) | Project-level |

---

## Full Documentation

See **[docs/ZERO_CONFIG_SETUP.md](docs/ZERO_CONFIG_SETUP.md)** for complete Gateway Script setup.

---

## Recommendation for 8.1 Customers

**Use Gateway Tag Change Script:**
- ✅ Works on 8.1, 8.2, and 8.3
- ✅ Simpler setup (no Designer needed)
- ✅ Gateway-level (survives project changes)
- ✅ Same performance and reliability

**When to upgrade to 8.3:**
- If you want Event Streams features (filters, transforms)
- If you want Designer-based configuration
- If you want automated Event Stream deployment

---

## Need Help?

- **8.1 Setup**: [docs/ZERO_CONFIG_SETUP.md](docs/ZERO_CONFIG_SETUP.md)
- **General Guide**: [USER_GUIDE.md](USER_GUIDE.md)
- **Quick Start**: [QUICK_START.md](QUICK_START.md)

