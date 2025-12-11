# Complete Automation Setup Guide

## Overview

This guide shows how to deploy the Ignition-Zerobus connector to **any** Ignition Gateway and Databricks workspace with minimal manual steps.

## Prerequisites

- Ignition Gateway 8.3.0+ installed
- Databricks workspace with Zerobus enabled
- Service Principal with proper permissions
- Python 3.6+ on the deployment machine

## Quick Start (3 Steps)

### Step 1: Install Module
```bash
# Copy module to Gateway
sudo cp Ignition-Zerobus-unsigned.modl /usr/local/ignition/user-lib/modules/

# Restart Gateway
sudo /usr/local/ignition/ignition.sh restart
```

### Step 2: Create Event Stream
```bash
# In Designer: Event Streams → New Event Stream → Name: "my_stream" → Save
```

### Step 3: Run Automation
```bash
# Configure Event Stream
./scripts/configure_eventstream.py \
  --name my_stream \
  --project MyProject \
  --tag-file my_tags.txt

# Configure Module
./configure_module.sh
```

**Done!** Data flows from tags → Databricks.

---

## Detailed Setup for New Environments

### 1. Gather Required Information

Before starting automation, collect these details:

#### Ignition Gateway
- **Gateway URL**: `http://gateway-host:8088` (default port 8088)
- **Project Name**: Name of your Ignition project
- **Gateway Install Path**: Usually `/usr/local/ignition/` (macOS/Linux) or `C:\Program Files\Inductive Automation\Ignition\` (Windows)

#### Databricks Workspace
- **Workspace URL**: `https://your-workspace.cloud.databricks.com`
- **Workspace ID**: Numeric ID (see below how to find)
- **Region**: e.g., `us-west-2`, `westus2`, `us-central1`
- **Service Principal Client ID**: From Databricks account console
- **Service Principal Secret**: From Databricks account console

#### Target Table
- **Catalog**: e.g., `ignition_demo`
- **Schema**: e.g., `scada_data`
- **Table**: e.g., `tag_events`

#### Tags to Monitor
- List of tag paths to stream to Databricks

---

### 2. Find Your Databricks Workspace ID

#### Method 1: From Workspace URL
When logged into Databricks, check the URL:
```
https://xxxxx.cloud.databricks.com/?o=1444828305810485
                                        ^^^^^^^^^^^^^^^^^
                                        This is your Workspace ID
```

#### Method 2: From Workspace Settings
1. Go to **Settings** → **Workspace Admin**
2. Look for **Workspace ID** in the details

#### Method 3: Using Databricks CLI
```bash
databricks workspace get-status
```

Look for `workspace_id` in the output.

---

### 3. Configure Module for Your Environment

Create a configuration file for your environment:

```bash
cat > configs/my-environment-config.json <<'EOF'
{
  "enabled": true,
  "workspaceUrl": "https://YOUR-WORKSPACE.cloud.databricks.com",
  "zerobusEndpoint": "WORKSPACE_ID.zerobus.REGION.cloud.databricks.com",
  "oauthClientId": "YOUR-SERVICE-PRINCIPAL-CLIENT-ID",
  "oauthClientSecret": "YOUR-SERVICE-PRINCIPAL-SECRET",
  "catalogName": "YOUR_CATALOG",
  "schemaName": "YOUR_SCHEMA",
  "tableName": "YOUR_TABLE",
  "targetTable": "YOUR_CATALOG.YOUR_SCHEMA.YOUR_TABLE",
  "tagSelectionMode": "folder",
  "tagFolderPath": "[default]",
  "batchSize": 100,
  "batchFlushIntervalMs": 5000,
  "maxQueueSize": 10000,
  "sourceSystemId": "ignition-gateway-YOUR-ENV"
}
EOF
```

#### ⚠️ Critical: Zerobus Endpoint Format

The `zerobusEndpoint` must follow this exact format:

```
WORKSPACE_ID.zerobus.REGION.cloud.databricks.com
```

**Examples by Cloud Provider:**

**AWS:**
```
1444828305810485.zerobus.us-west-2.cloud.databricks.com
1444828305810485.zerobus.us-east-1.cloud.databricks.com
1444828305810485.zerobus.eu-west-1.cloud.databricks.com
```

**Azure:**
```
1444828305810485.zerobus.westus2.azuredatabricks.net
1444828305810485.zerobus.eastus2.azuredatabricks.net
```

**GCP:**
```
1444828305810485.zerobus.us-central1.gcp.databricks.com
1444828305810485.zerobus.europe-west1.gcp.databricks.com
```

**Common Mistakes (These DON'T Work):**
- ❌ `https://workspace.cloud.databricks.com/api/2.0/zerobus/streams/ingest`
- ❌ `https://workspace.cloud.databricks.com`
- ❌ `workspace.cloud.databricks.com`
- ❌ `workspace-name.zerobus.region.cloud.databricks.com` (must be numeric workspace ID)

---

### 4. Customize the Configuration Script

Edit `configure_module.sh` to load your environment config:

```bash
#!/bin/bash
# Configure Zerobus Module for Your Environment

# Usage: ./configure_module.sh <environment>
# Example: ./configure_module.sh production

ENVIRONMENT=${1:-development}
CONFIG_FILE="configs/${ENVIRONMENT}-config.json"

if [ ! -f "$CONFIG_FILE" ]; then
  echo "Error: Configuration file not found: $CONFIG_FILE"
  echo "Available configs:"
  ls -1 configs/*-config.json 2>/dev/null || echo "  (none)"
  exit 1
fi

echo "=========================================="
echo "Configuring Zerobus Module"
echo "Environment: $ENVIRONMENT"
echo "Config: $CONFIG_FILE"
echo "=========================================="
echo ""

# Read configuration
WORKSPACE_URL=$(jq -r '.workspaceUrl' "$CONFIG_FILE")
ZEROBUS_ENDPOINT=$(jq -r '.zerobusEndpoint' "$CONFIG_FILE")
CATALOG=$(jq -r '.catalogName' "$CONFIG_FILE")
SCHEMA=$(jq -r '.schemaName' "$CONFIG_FILE")
TABLE=$(jq -r '.tableName' "$CONFIG_FILE")

echo "Target: $CATALOG.$SCHEMA.$TABLE"
echo "Zerobus: $ZEROBUS_ENDPOINT"
echo ""

# Send configuration to Gateway
RESPONSE=$(curl -s -X POST http://localhost:8088/system/zerobus/config \
  -H "Content-Type: application/json" \
  -d @"$CONFIG_FILE")

echo "Response: $RESPONSE"
echo ""

# Wait for initialization
echo "Waiting for Zerobus to initialize..."
sleep 10

# Check status
echo "Checking module status..."
curl -s http://localhost:8088/system/zerobus/diagnostics

echo ""
echo "=========================================="
echo "Configuration complete!"
echo "=========================================="
```

Make it executable:
```bash
chmod +x configure_module.sh
```

---

### 5. Configure Event Stream Automation

Create a tag file for your environment:

```bash
# configs/production-tags.txt
[default]Equipment/Pump01/Temperature
[default]Equipment/Pump01/Pressure
[default]Equipment/Pump01/FlowRate
[default]Equipment/Pump02/Temperature
[default]Equipment/Pump02/Pressure
[default]Equipment/Tank01/Level
[default]Equipment/Tank01/Temperature
[default]Process/Line01/Speed
[default]Process/Line01/Status
```

#### Customize Event Stream Script

The `configure_eventstream.py` script accepts these parameters:

**Required:**
- `--name`: Event Stream name (must exist in project)
- `--project`: Ignition project name
- `--tags` OR `--tag-file`: Tag paths to monitor

**Optional:**
- `--gateway-url`: Gateway URL (default: http://localhost:8088)
- `--ignition-data`: Ignition data directory (default: /usr/local/ignition/data)
- `--debounce`: Buffer debounce ms (default: 100)
- `--max-wait`: Buffer max wait ms (default: 1000)
- `--max-queue-size`: Queue size (default: 10000)

**Example for different environments:**

```bash
# Development
./scripts/configure_eventstream.py \
  --name dev_stream \
  --project MyProject \
  --tag-file configs/dev-tags.txt \
  --gateway-url http://localhost:8088 \
  --debounce 100 \
  --max-wait 1000

# Production (faster batching)
./scripts/configure_eventstream.py \
  --name prod_stream \
  --project MyProject \
  --tag-file configs/production-tags.txt \
  --gateway-url http://prod-gateway:8088 \
  --debounce 50 \
  --max-wait 500

# Remote Gateway
./scripts/configure_eventstream.py \
  --name remote_stream \
  --project RemoteProject \
  --tag-file configs/remote-tags.txt \
  --gateway-url http://remote-gateway.example.com:8088 \
  --ignition-data /opt/ignition/data
```

---

## Complete Deployment Workflow

### For a New Environment

#### Step 1: Prepare Configuration Files

```bash
# Create configs directory
mkdir -p configs

# Create module configuration
cat > configs/production-config.json <<'EOF'
{
  "enabled": true,
  "workspaceUrl": "https://prod-workspace.cloud.databricks.com",
  "zerobusEndpoint": "9876543210987654.zerobus.us-east-1.cloud.databricks.com",
  "oauthClientId": "abcd1234-5678-90ab-cdef-1234567890ab",
  "oauthClientSecret": "dapi...",
  "catalogName": "production",
  "schemaName": "iot_data",
  "tableName": "sensor_events",
  "targetTable": "production.iot_data.sensor_events",
  "sourceSystemId": "ignition-prod-001"
}
EOF

# Create tag list
cat > configs/production-tags.txt <<'EOF'
[default]Equipment/Pump01/Temperature
[default]Equipment/Pump01/Pressure
[default]Equipment/Pump02/Temperature
[default]Equipment/Tank01/Level
EOF
```

#### Step 2: Install Module

```bash
# Copy module to Gateway
scp Ignition-Zerobus-unsigned.modl admin@prod-gateway:/tmp/

# SSH to Gateway
ssh admin@prod-gateway

# Install module
sudo cp /tmp/Ignition-Zerobus-unsigned.modl /usr/local/ignition/user-lib/modules/

# Restart Gateway
sudo /usr/local/ignition/ignition.sh restart

# Wait for startup
sleep 30

# Verify module loaded
curl http://localhost:8088/system/zerobus/diagnostics
```

#### Step 3: Create Event Stream in Designer

```
1. Open Designer
2. Connect to: http://prod-gateway:8088
3. Open Project: "ProductionProject"
4. Go to: Project Browser → Event Streams
5. Right-click → New Event Stream
6. Name: "prod_stream"
7. Click Save (leave everything else empty)
8. Close Designer
```

#### Step 4: Configure Event Stream

```bash
# From your local machine or deployment server
./scripts/configure_eventstream.py \
  --name prod_stream \
  --project ProductionProject \
  --tag-file configs/production-tags.txt \
  --gateway-url http://prod-gateway:8088 \
  --ignition-data /usr/local/ignition/data

# Or if running on the Gateway itself
./scripts/configure_eventstream.py \
  --name prod_stream \
  --project ProductionProject \
  --tag-file configs/production-tags.txt
```

#### Step 5: Configure Module

```bash
# Apply module configuration
./configure_module.sh production

# Or manually:
curl -X POST http://prod-gateway:8088/system/zerobus/config \
  -H "Content-Type: application/json" \
  -d @configs/production-config.json
```

#### Step 6: Verify

```bash
# Check module status
curl http://prod-gateway:8088/system/zerobus/diagnostics

# Should show:
# - Module Enabled: true
# - Initialized: true
# - Connected: true
# - Stream State: OPENED
# - Total Events Sent: (increasing)
```

#### Step 7: Verify in Databricks

```sql
SELECT 
  tag_path,
  numeric_value,
  event_time,
  source_system_id
FROM production.iot_data.sensor_events
ORDER BY event_time DESC
LIMIT 100;
```

---

## Multi-Environment Setup

### Directory Structure

```
lakeflow-ignition-zerobus-connector/
├── configs/
│   ├── development-config.json
│   ├── development-tags.txt
│   ├── staging-config.json
│   ├── staging-tags.txt
│   ├── production-config.json
│   └── production-tags.txt
├── scripts/
│   ├── configure_eventstream.py
│   └── deploy.sh
├── configure_module.sh
└── Ignition-Zerobus-unsigned.modl
```

### Create Deployment Script

```bash
#!/bin/bash
# deploy.sh - Complete deployment automation

set -e

ENVIRONMENT=$1
PROJECT_NAME=$2
STREAM_NAME=$3
GATEWAY_HOST=${4:-localhost}

if [ -z "$ENVIRONMENT" ] || [ -z "$PROJECT_NAME" ] || [ -z "$STREAM_NAME" ]; then
  echo "Usage: ./deploy.sh <environment> <project-name> <stream-name> [gateway-host]"
  echo ""
  echo "Example:"
  echo "  ./deploy.sh production ProductionProject prod_stream prod-gateway"
  echo "  ./deploy.sh development DevProject dev_stream localhost"
  exit 1
fi

CONFIG_FILE="configs/${ENVIRONMENT}-config.json"
TAG_FILE="configs/${ENVIRONMENT}-tags.txt"
GATEWAY_URL="http://${GATEWAY_HOST}:8088"

echo "=========================================="
echo "Deploying Zerobus Connector"
echo "=========================================="
echo "Environment: $ENVIRONMENT"
echo "Project: $PROJECT_NAME"
echo "Stream: $STREAM_NAME"
echo "Gateway: $GATEWAY_URL"
echo ""

# Validate files exist
if [ ! -f "$CONFIG_FILE" ]; then
  echo "Error: Config file not found: $CONFIG_FILE"
  exit 1
fi

if [ ! -f "$TAG_FILE" ]; then
  echo "Error: Tag file not found: $TAG_FILE"
  exit 1
fi

# Step 1: Configure Event Stream
echo "[1/2] Configuring Event Stream..."
python3 scripts/configure_eventstream.py \
  --name "$STREAM_NAME" \
  --project "$PROJECT_NAME" \
  --tag-file "$TAG_FILE" \
  --gateway-url "$GATEWAY_URL"

echo ""

# Step 2: Configure Module
echo "[2/2] Configuring Module..."
curl -s -X POST "${GATEWAY_URL}/system/zerobus/config" \
  -H "Content-Type: application/json" \
  -d @"$CONFIG_FILE"

echo ""
echo ""

# Wait for initialization
echo "Waiting for Zerobus to initialize..."
sleep 10

# Verify
echo "Verifying deployment..."
curl -s "${GATEWAY_URL}/system/zerobus/diagnostics"

echo ""
echo "=========================================="
echo "✓ Deployment Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Open Designer"
echo "  2. Go to Event Streams → $STREAM_NAME"
echo "  3. Enable the Event Stream"
echo "  4. Check Databricks for incoming data"
```

Make it executable:
```bash
chmod +x deploy.sh
```

### Deploy to Different Environments

```bash
# Development
./deploy.sh development DevProject dev_stream localhost

# Staging
./deploy.sh staging StagingProject staging_stream staging-gateway

# Production
./deploy.sh production ProductionProject prod_stream prod-gateway.example.com
```

---

## Customization Reference

### Module Configuration Fields

| Field | Description | Example |
|-------|-------------|---------|
| `enabled` | Enable/disable module | `true` |
| `workspaceUrl` | Databricks workspace URL | `https://your-workspace.cloud.databricks.com` |
| `zerobusEndpoint` | Zerobus gRPC endpoint | `WORKSPACE_ID.zerobus.REGION.cloud.databricks.com` |
| `oauthClientId` | Service Principal client ID | `abcd1234-...` |
| `oauthClientSecret` | Service Principal secret | `dapi...` |
| `catalogName` | Target catalog | `ignition_demo` |
| `schemaName` | Target schema | `scada_data` |
| `tableName` | Target table | `tag_events` |
| `targetTable` | Full table name | `catalog.schema.table` |
| `sourceSystemId` | Identifier for this Gateway | `ignition-gateway-001` |
| `batchSize` | Events per batch | `100` (default), `500` (high throughput) |
| `batchFlushIntervalMs` | Flush interval | `5000` (default), `1000` (low latency) |
| `maxQueueSize` | Internal queue size | `10000` (default), `100000` (high volume) |

### Event Stream Script Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `--name` | Event Stream name (must exist) | `my_stream` |
| `--project` | Ignition project name | `MyProject` |
| `--tags` | Tag paths (space-separated) | `"[default]Tag1" "[default]Tag2"` |
| `--tag-file` | File with tag paths | `configs/tags.txt` |
| `--gateway-url` | Gateway URL | `http://gateway:8088` |
| `--ignition-data` | Ignition data directory | `/usr/local/ignition/data` |
| `--debounce` | Buffer debounce (ms) | `100` |
| `--max-wait` | Buffer max wait (ms) | `1000` |
| `--max-queue-size` | Queue size | `10000` |

---

## Troubleshooting

### Event Stream Not Configured

**Problem:** Designer shows empty Event Stream after running script.

**Solution:** Restart Gateway to reload project files:
```bash
sudo /usr/local/ignition/ignition.sh restart
```

### Module Not Connecting

**Problem:** `Connected: false` in diagnostics.

**Check:**
1. Zerobus endpoint format is correct (numeric workspace ID)
2. Service Principal credentials are valid
3. Service Principal has permissions on table
4. Region matches your workspace

**Verify endpoint:**
```bash
# Should resolve
nslookup WORKSPACE_ID.zerobus.REGION.cloud.databricks.com
```

### Permission Errors

**Problem:** `UNAUTHENTICATED` or `PERMISSION_DENIED`

**Solution:** Grant permissions to Service Principal:
```sql
GRANT USE CATALOG ON CATALOG your_catalog TO `service-principal-uuid`;
GRANT USE SCHEMA ON SCHEMA your_catalog.your_schema TO `service-principal-uuid`;
GRANT MODIFY ON TABLE your_catalog.your_schema.your_table TO `service-principal-uuid`;
GRANT SELECT ON TABLE your_catalog.your_schema.your_table TO `service-principal-uuid`;
```

---

## Production Checklist

- [ ] Module installed and enabled
- [ ] Event Stream created in Designer
- [ ] Event Stream configured via script
- [ ] Module configured with correct Zerobus endpoint
- [ ] Service Principal permissions granted
- [ ] Event Stream enabled in Designer
- [ ] Data flowing to Databricks (verified in SQL)
- [ ] Monitoring set up (queue depth, failures)
- [ ] Backup configuration files stored securely
- [ ] Documentation updated with environment details

---

## Summary

**Key Points for New Environments:**

1. **Zerobus Endpoint:** Must be `WORKSPACE_ID.zerobus.REGION.cloud.databricks.com`
2. **Event Stream:** Create empty in Designer, configure via script
3. **Module Config:** Apply via REST API or script
4. **Automation:** Use provided scripts with environment-specific configs

**Time to Deploy:**
- Manual: ~30 minutes per environment
- Automated: ~5 minutes per environment (after setup)

**Files to Customize:**
- `configs/<env>-config.json` - Module configuration
- `configs/<env>-tags.txt` - Tag list
- `deploy.sh` - Complete deployment script

