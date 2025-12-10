# Event Stream Automation Guide

This guide shows how to automate the Zerobus Event Stream deployment across multiple Ignition Gateways.

## Overview

The Zerobus Event Stream setup consists of:
1. **Zerobus Module** - Gateway module (can be automated)
2. **Event Stream** - Project resource (requires Designer, can be templated)
3. **Module Configuration** - API-based (can be automated)

## Automated Deployment

### Quick Start

```bash
# Set environment variables
export DATABRICKS_WORKSPACE="https://your-workspace.cloud.databricks.com"
export ZEROBUS_ENDPOINT="your-workspace-id.zerobus.region.cloud.databricks.com"
export OAUTH_CLIENT_ID="your-client-id"
export OAUTH_CLIENT_SECRET="your-client-secret"
export GATEWAY_URL="http://localhost:8088"

# Run deployment script
./scripts/deploy_eventstream.sh
```

### What Gets Automated

✅ **Module Installation** - Via Gateway Web UI (one-time)  
✅ **Module Configuration** - Via REST API (fully automated)  
⚠️ **Event Stream Creation** - Requires Designer (can be templated)  

## Method 1: Configuration Template (Recommended)

### Export Current Configuration

```bash
# Export your working Event Stream configuration
cd scripts
python3 export_eventstream.py ../eventstream-config.json
```

This creates a JSON template with:
- Tag paths
- Encoder settings
- Buffer configuration
- Script handler code

### Deploy to New Environment

1. **Install Module** (via Web UI or script)
2. **Configure Module** (via REST API)
3. **Import Event Stream** (in Designer using template)

```bash
# Steps 1-2 automated
./scripts/deploy_eventstream.sh

# Step 3: Manual in Designer
# - Create Event Stream using eventstream-config.json as reference
```

## Method 2: Project Export/Import

### Export Entire Project

```bash
# Export project with Event Stream included
curl -X GET "http://source-gateway:8088/data/project-export/YourProject" \
  -u "admin:password" \
  -o project-with-eventstream.json
```

### Import to Target Gateway

```bash
# Import complete project
curl -X POST "http://target-gateway:8088/data/project-import" \
  -u "admin:password" \
  -F "project=@project-with-eventstream.json"
```

**Advantage:** Event Stream is included in project export  
**Disadvantage:** Imports entire project (not just Event Stream)

## Method 3: Infrastructure as Code

### Terraform-Style Deployment

Create a deployment configuration file:

**`deployment-config.yaml`:**
```yaml
gateway:
  url: http://localhost:8088
  
module:
  file: module/build/modules/zerobus-connector-1.0.0.modl
  
databricks:
  workspace: https://e2-demo-field-eng.cloud.databricks.com
  zerobusEndpoint: 1444828305810485.zerobus.us-west-2.cloud.databricks.com
  oauth:
    clientId: ${OAUTH_CLIENT_ID}
    clientSecret: ${OAUTH_CLIENT_SECRET}
  table:
    catalog: ignition_demo
    schema: scada_data
    table: tag_events

eventStream:
  name: ZerobusTagStream
  tagPaths:
    - "[Sample_Tags]Sine/Sine0"
    - "[Sample_Tags]Sine/Sine1"
    - "[Sample_Tags]Realistic/Realistic0"
  buffer:
    debounceMs: 100
    maxWaitMs: 1000
    maxQueueSize: 10000
```

Deploy with:
```bash
./scripts/deploy_from_config.sh deployment-config.yaml
```

## REST API Automation

### Module Configuration API

```bash
# Configure module programmatically
curl -X POST http://localhost:8088/system/zerobus/config \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "workspaceUrl": "https://your-workspace.cloud.databricks.com",
    "zerobusEndpoint": "your-endpoint.zerobus.region.cloud.databricks.com",
    "oauthClientId": "your-client-id",
    "oauthClientSecret": "your-client-secret",
    "targetTable": "ignition_demo.scada_data.tag_events",
    "catalogName": "ignition_demo",
    "schemaName": "scada_data",
    "tableName": "tag_events",
    "batchSize": 50,
    "batchFlushIntervalMs": 500,
    "maxQueueSize": 10000
  }'
```

### Verification

```bash
# Check module health
curl http://localhost:8088/system/zerobus/health

# Check diagnostics
curl http://localhost:8088/system/zerobus/diagnostics
```

## CI/CD Integration

### GitHub Actions Example

**`.github/workflows/deploy-zerobus.yml`:**
```yaml
name: Deploy Zerobus Integration

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build Module
        run: |
          cd module
          ./gradlew clean buildModule
      
      - name: Configure Module
        env:
          GATEWAY_URL: ${{ secrets.GATEWAY_URL }}
          OAUTH_CLIENT_ID: ${{ secrets.OAUTH_CLIENT_ID }}
          OAUTH_CLIENT_SECRET: ${{ secrets.OAUTH_CLIENT_SECRET }}
        run: |
          curl -X POST ${GATEWAY_URL}/system/zerobus/config \
            -H "Content-Type: application/json" \
            -d @config/module-config.json
      
      - name: Verify Deployment
        run: |
          curl ${GATEWAY_URL}/system/zerobus/health
```

## Environment Variables

For automation scripts:

```bash
export GATEWAY_URL="http://localhost:8088"
export DATABRICKS_WORKSPACE="https://your-workspace.cloud.databricks.com"
export ZEROBUS_ENDPOINT="endpoint.zerobus.region.cloud.databricks.com"
export OAUTH_CLIENT_ID="your-client-id"
export OAUTH_CLIENT_SECRET="your-client-secret"
export TARGET_TABLE="ignition_demo.scada_data.tag_events"
```

Or use a `.env` file:

```bash
# Load from .env file
source .env
./scripts/deploy_eventstream.sh
```

## Multi-Environment Deployment

### Deploy to Multiple Gateways

```bash
# Define environments
GATEWAYS=(
  "http://dev-gateway:8088"
  "http://staging-gateway:8088"
  "http://prod-gateway:8088"
)

# Deploy to each
for gateway in "${GATEWAYS[@]}"; do
  echo "Deploying to $gateway"
  GATEWAY_URL=$gateway ./scripts/deploy_eventstream.sh
done
```

### Environment-Specific Configurations

```bash
configs/
├── dev-config.json
├── staging-config.json
└── prod-config.json

# Deploy specific config
ENVIRONMENT=prod ./scripts/deploy_from_config.sh
```

## Best Practices

### 1. Version Control

```bash
git/
├── module/                    # Module source code
├── eventstream-config.json    # Event Stream template
├── configs/                   # Environment configs
│   ├── dev.json
│   ├── staging.json
│   └── prod.json
└── scripts/                   # Automation scripts
    ├── deploy_eventstream.sh
    └── export_eventstream.py
```

### 2. Secret Management

**Don't commit secrets!** Use:
- Environment variables
- Secret management tools (Vault, AWS Secrets Manager)
- CI/CD secret stores

```bash
# Bad: secrets in config file
config.json: {"oauthClientSecret": "dosebb27..."}

# Good: reference from environment
config.json: {"oauthClientSecret": "${OAUTH_CLIENT_SECRET}"}
```

### 3. Testing

```bash
# Test in dev first
GATEWAY_URL=http://dev-gateway:8088 ./scripts/deploy_eventstream.sh

# Verify
curl http://dev-gateway:8088/system/zerobus/diagnostics

# Then promote to prod
GATEWAY_URL=http://prod-gateway:8088 ./scripts/deploy_eventstream.sh
```

### 4. Monitoring

```bash
# Add health check script
while true; do
  health=$(curl -s http://localhost:8088/system/zerobus/health)
  echo "$(date): $health"
  sleep 60
done
```

## Troubleshooting Automation

### Module Not Loading

```bash
# Check module file exists
ls -lh module/build/modules/*.modl

# Check Gateway logs
tail -f /usr/local/ignition/logs/wrapper.log | grep -i zerobus
```

### API Calls Failing

```bash
# Test connectivity
curl http://localhost:8088/StatusPing

# Check authentication
curl -v http://localhost:8088/system/zerobus/health
```

### Event Stream Not Creating

Event Streams require Designer - they cannot be created via API. Options:
1. Export/import entire project
2. Create manually once, then version control the project
3. Use Gateway backup/restore

## Complete Example

**Full automated deployment:**

```bash
#!/bin/bash
# complete-deployment.sh

# 1. Build module
cd module && ./gradlew clean buildModule && cd ..

# 2. Install module (manual step - open Web UI)
echo "Install module at: http://localhost:8088/web/config/system.modules"
read -p "Press Enter when installed..."

# 3. Configure module
curl -X POST http://localhost:8088/system/zerobus/config \
  -H "Content-Type: application/json" \
  -d @configs/prod-config.json

# 4. Create Event Stream (manual step - open Designer)
echo "Create Event Stream in Designer using eventstream-config.json"
read -p "Press Enter when created..."

# 5. Verify
curl http://localhost:8088/system/zerobus/diagnostics

# 6. Test
echo "Checking for data in Databricks..."
# Add Databricks SQL query here

echo "Deployment complete!"
```

## Files Included

- **`scripts/export_eventstream.py`** - Export Event Stream config
- **`scripts/deploy_eventstream.sh`** - Automated deployment
- **`eventstream-config.json`** - Event Stream template
- **`configs/`** - Environment-specific configs

## Next Steps

1. Export your working Event Stream: `python3 scripts/export_eventstream.py`
2. Version control the configuration
3. Create environment-specific configs
4. Set up CI/CD pipeline
5. Document your deployment process

## Support

For issues:
- Check Gateway logs
- Run diagnostics: `curl http://localhost:8088/system/zerobus/diagnostics`
- Review docs/EVENT_STREAMS_SETUP.md

