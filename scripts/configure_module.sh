#!/bin/bash
# Configure Zerobus Module via REST API

CONFIG_FILE="module_config.json"

# Create configuration
cat > "$CONFIG_FILE" <<'EOF'
{
  "enabled": true,
  "workspaceUrl": "https://your-workspace.cloud.databricks.com",
  "zerobusEndpoint": "WORKSPACE_ID.zerobus.REGION.cloud.databricks.com",
  "oauthClientId": "YOUR_CLIENT_ID",
  "oauthClientSecret": "YOUR_CLIENT_SECRET",
  "catalogName": "ignition_demo",
  "schemaName": "scada_data",
  "tableName": "tag_events",
  "targetTable": "ignition_demo.scada_data.tag_events",
  "tagSelectionMode": "explicit",
  "explicitTagPaths": [],
  "batchSize": 100,
  "batchFlushIntervalMs": 5000,
  "maxQueueSize": 10000,
  "maxEventsPerSecond": 10000,
  "onlyOnChange": false,
  "sourceSystemId": "ignition-gateway-001",
  "debugLogging": false
}
EOF

echo "Configuring Zerobus Module..."
echo ""

# Send configuration
RESPONSE=$(curl -s -X POST http://localhost:8088/system/zerobus/config \
  -H "Content-Type: application/json" \
  -d @"$CONFIG_FILE")

echo "Response: $RESPONSE"
echo ""

# Wait a bit
sleep 3

# Check status
echo "Checking module status..."
curl -s http://localhost:8088/system/zerobus/diagnostics

# Clean up
rm -f "$CONFIG_FILE"

echo ""
echo ""
echo "Configuration complete!"
echo ""
echo "Module should now be:"
echo "  - Enabled: true"
echo "  - Connected to Databricks"
echo "  - Ready to receive events from Event Streams"

