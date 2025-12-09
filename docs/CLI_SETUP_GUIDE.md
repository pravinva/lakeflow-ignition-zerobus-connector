# CLI Setup Guide (Event Streams Alternative)

Since Ignition Event Streams require the Designer GUI, this guide provides **CLI-friendly alternatives** for automated deployment.

## Problem

Event Streams are **project resources** that can only be configured in the Ignition Designer, not via CLI.

## Solutions

### Option 1: Gateway Startup Script (Recommended for Automation)

Use a Gateway-level script to subscribe to tags and forward events to the Zerobus module.

#### Advantages
- ✅ No Designer required
- ✅ Can be scripted/automated
- ✅ Works at Gateway level (all projects)
- ✅ Easier to version control

#### Disadvantages
- ❌ Less flexible than Event Streams (no transforms/filters)
- ❌ Requires Gateway restart to update

#### Installation

1. **Copy the startup script:**
   ```bash
   cp scripts/gateway_event_forwarder.py /tmp/
   ```

2. **Install via Gateway Web Interface:**
   ```bash
   # Open browser
   open http://localhost:8088
   
   # Navigate to:
   # Config > Scripting > Gateway Event Scripts > Startup Scripts
   # Click "Add Script"
   # Paste contents of gateway_event_forwarder.py
   # Save
   ```

3. **Restart Gateway:**
   ```bash
   sudo launchctl stop com.inductiveautomation.ignition
   sudo launchctl start com.inductiveautomation.ignition
   ```

4. **Verify:**
   ```bash
   tail -f /usr/local/ignition/logs/wrapper.log | grep Zerobus
   ```

### Option 2: Project Export/Import

Create Event Stream once, then export and import to other environments.

#### Step 1: Create Event Stream in Designer (One Time)

Follow the standard Event Streams setup in Designer (see `EVENT_STREAMS_SETUP.md`)

#### Step 2: Export Project

```bash
#!/bin/bash

GATEWAY="http://localhost:8088"
PROJECT="YourProject"
USER="admin"
PASS="password"

# Export project as resource JSON
curl -X GET "${GATEWAY}/data/project-export/${PROJECT}" \
  -u "${USER}:${PASS}" \
  -H "Accept: application/json" \
  -o project-export.json

echo "Project exported to: project-export.json"
```

#### Step 3: Import to Other Gateways

```bash
#!/bin/bash

TARGET_GATEWAY="http://target-gateway:8088"
USER="admin"
PASS="password"

# Import project
curl -X POST "${TARGET_GATEWAY}/data/project-import" \
  -u "${USER}:${PASS}" \
  -H "Content-Type: multipart/form-data" \
  -F "project=@project-export.json"

echo "Project imported"
```

### Option 3: REST API Configuration (Module Only)

Configure the Zerobus module itself via REST API:

```bash
#!/bin/bash

GATEWAY="http://localhost:8088"

# Configure module
curl -X POST "${GATEWAY}/system/zerobus/config" \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "workspaceUrl": "https://your-workspace.cloud.databricks.com",
    "zerobusEndpoint": "https://your-workspace.cloud.databricks.com/api/2.0/zerobus",
    "oauthClientId": "your-client-id",
    "oauthClientSecret": "your-client-secret",
    "targetCatalog": "ignition_demo",
    "targetSchema": "scada_data",
    "targetTable": "tag_events",
    "batchSize": 100,
    "batchFlushIntervalMs": 1000,
    "maxQueueSize": 10000,
    "maxEventsPerSecond": 10000
  }'

# Test connection
curl "${GATEWAY}/system/zerobus/test-connection"

# Check health
curl "${GATEWAY}/system/zerobus/health"

# Get diagnostics
curl "${GATEWAY}/system/zerobus/diagnostics"
```

## Complete Automation Script

Use the provided installation script:

```bash
# Set environment variables
export GATEWAY_URL="http://localhost:8088"
export GATEWAY_USER="admin"
export GATEWAY_PASS="password"

# Run installation
./scripts/install_event_forwarder.sh
```

## Comparison: Event Streams vs Gateway Script

| Feature | Event Streams | Gateway Script |
|---------|---------------|----------------|
| Setup Method | Designer GUI | Web UI or API |
| Configuration | Per-project | Gateway-wide |
| Filters | Yes (Python) | Manual in script |
| Transforms | Yes (Python) | Manual in script |
| Batching | Built-in | Manual in script |
| Monitoring | Designer metrics | Gateway logs |
| CLI Friendly | No | Partial |
| Version Control | Project export | Script file |

## Recommended Approach for Production

**Hybrid approach:**

1. **Development:** Use Event Streams in Designer (most flexible)
2. **Staging/Prod:** Export project or use Gateway script (automation)

### Development (Event Streams)
```bash
# In Designer
- Create Event Stream with Tag Event source
- Add filters, transforms as needed
- Test and iterate quickly
- Export project when ready
```

### Production (Automated)
```bash
# Import project OR use Gateway script
./scripts/install_event_forwarder.sh

# Configure via API
curl -X POST http://gateway:8088/system/zerobus/config \
  -H "Content-Type: application/json" \
  -d @config.json

# Monitor
curl http://gateway:8088/system/zerobus/diagnostics
```

## Gateway Startup Script Configuration

The Gateway startup script (`gateway_event_forwarder.py`) can be customized:

### Tag Selection

```python
# Edit tag list
TAG_PATHS = [
    "[Sample_Tags]Sine/Sine0",
    "[Sample_Tags]Realistic/Realistic0",
    # Add more tags...
]
```

### Batch Settings

```python
# Adjust batching
BATCH_SIZE = 100          # Events per batch
BATCH_TIMEOUT_MS = 1000   # Max wait time
```

### Filtering

Add filtering logic:

```python
def on_tag_change(tag_path, value, quality, timestamp):
    # Only process GOOD quality
    if quality.getName() != "GOOD":
        return
    
    # Only process values in range
    if isinstance(value, (int, float)):
        if value < 0 or value > 10000:
            return
    
    # Continue with normal processing...
```

## Troubleshooting

### Script Not Running

Check Gateway logs:
```bash
tail -f /usr/local/ignition/logs/wrapper.log | grep Zerobus
```

### Events Not Reaching Module

Test REST endpoint:
```bash
curl -X POST http://localhost:8088/system/zerobus/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "tagPath": "[Sample_Tags]Sine/Sine0",
    "tagProvider": "Sample_Tags",
    "value": 42.5,
    "quality": "GOOD",
    "qualityCode": 192,
    "timestamp": 1234567890000,
    "dataType": "Float8"
  }'
```

### Module Not Responding

Check module status:
```bash
# Health check
curl http://localhost:8088/system/zerobus/health

# Diagnostics
curl http://localhost:8088/system/zerobus/diagnostics
```

## API Reference

### Module Configuration

```bash
# Get current config
GET /system/zerobus/config

# Update config
POST /system/zerobus/config
Content-Type: application/json
{...}

# Test connection
POST /system/zerobus/test-connection

# Health check
GET /system/zerobus/health

# Diagnostics
GET /system/zerobus/diagnostics
```

### Event Ingestion

```bash
# Single event
POST /system/zerobus/ingest
Content-Type: application/json
{
  "tagPath": "...",
  "value": ...,
  "quality": "...",
  "timestamp": ...
}

# Batch events
POST /system/zerobus/ingest/batch
Content-Type: application/json
[
  {...},
  {...}
]
```

## Files

- `scripts/gateway_event_forwarder.py` - Gateway startup script
- `scripts/install_event_forwarder.sh` - Automated installation
- `docs/EVENT_STREAMS_SETUP.md` - Event Streams GUI guide (alternative)

## Next Steps

1. Choose your approach (Gateway script or Event Streams)
2. Install and configure
3. Test event flow
4. Monitor in production

For GUI-based Event Streams setup, see: `docs/EVENT_STREAMS_SETUP.md`

