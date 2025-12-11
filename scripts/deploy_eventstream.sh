#!/bin/bash

# Automated Event Stream Deployment Script
# This script sets up the complete Zerobus Event Stream integration

set -e

GATEWAY_URL="${GATEWAY_URL:-http://localhost:8088}"
MODULE_PATH="../module/build/modules/zerobus-connector-1.0.0.modl"
CONFIG_FILE="../eventstream-config.json"

echo "=================================================="
echo "Zerobus Event Stream Automated Deployment"
echo "=================================================="
echo ""
echo "Gateway: $GATEWAY_URL"
echo ""

# Step 1: Install Module
echo "[1/4] Installing Zerobus Module..."
if [ -f "$MODULE_PATH" ]; then
    echo "✓ Module found: $MODULE_PATH"
    echo ""
    echo "Please install via Gateway Web UI:"
    echo "  1. Open: ${GATEWAY_URL}/web/config/system.modules"
    echo "  2. Click 'Install or Upgrade a Module'"
    echo "  3. Upload: $MODULE_PATH"
    echo ""
    read -p "Press Enter when module is installed..."
else
    echo "✗ Module not found. Build it first:"
    echo "  cd module && ./gradlew buildModule"
    exit 1
fi

# Step 2: Configure Module
echo ""
echo "[2/4] Configuring Zerobus Module..."

# Get Databricks credentials from environment or prompt
if [ -z "$DATABRICKS_WORKSPACE" ]; then
    read -p "Databricks Workspace URL: " DATABRICKS_WORKSPACE
fi
if [ -z "$ZEROBUS_ENDPOINT" ]; then
    read -p "Zerobus Endpoint: " ZEROBUS_ENDPOINT
fi
if [ -z "$OAUTH_CLIENT_ID" ]; then
    read -p "OAuth Client ID: " OAUTH_CLIENT_ID
fi
if [ -z "$OAUTH_CLIENT_SECRET" ]; then
    read -sp "OAuth Client Secret: " OAUTH_CLIENT_SECRET
    echo ""
fi

# Configure module
curl -X POST "${GATEWAY_URL}/system/zerobus/config" \
  -H "Content-Type: application/json" \
  -d "{
    \"enabled\": true,
    \"workspaceUrl\": \"${DATABRICKS_WORKSPACE}\",
    \"zerobusEndpoint\": \"${ZEROBUS_ENDPOINT}\",
    \"oauthClientId\": \"${OAUTH_CLIENT_ID}\",
    \"oauthClientSecret\": \"${OAUTH_CLIENT_SECRET}\",
    \"targetTable\": \"ignition_demo.scada_data.tag_events\",
    \"catalogName\": \"ignition_demo\",
    \"schemaName\": \"scada_data\",
    \"tableName\": \"tag_events\",
    \"tagSelectionMode\": \"explicit\",
    \"explicitTagPaths\": [\"[Sample_Tags]Sine/Sine0\"],
    \"batchSize\": 50,
    \"batchFlushIntervalMs\": 500,
    \"maxQueueSize\": 10000
  }" > /dev/null 2>&1

echo "✓ Module configured"

# Verify connection
sleep 3
health=$(curl -s "${GATEWAY_URL}/system/zerobus/health")
echo "Module status: $health"

# Step 3: Event Stream Instructions
echo ""
echo "[3/4] Event Stream Setup (Manual)"
echo ""
echo "Event Stream configuration has been exported to:"
echo "  $CONFIG_FILE"
echo ""
echo "To create the Event Stream in Designer:"
echo ""
echo "1. Open Ignition Designer"
echo "2. Go to: Event Streams (in Project Browser)"
echo "3. Right-click → New Event Stream"
echo "4. Name: ZerobusTagStream"
echo ""
echo "5. Configure Source:"
echo "   - Type: Tag Event"
echo "   - Tag Paths: Add your tags (e.g., [Sample_Tags]Sine/Sine0)"
echo "   - Triggers: ☑ Value Changed"
echo ""
echo "6. Configure Encoder:"
echo "   - Type: String"
echo "   - Encoding: UTF-8"
echo ""
echo "7. Configure Buffer:"
echo "   - Debounce: 100 ms"
echo "   - Max Wait: 1000 ms"
echo "   - Max Queue Size: 10000"
echo ""
echo "8. Add Handler → Script"
echo "   - Copy script from: docs/EVENT_STREAMS_SETUP.md (line 93)"
echo "   - Or use the script in: $CONFIG_FILE"
echo ""
echo "9. Set Handler Failure Mode:"
echo "   - Failure Mode: RETRY"
echo "   - Retry Strategy: EXPONENTIAL"
echo "   - Retry Count: 3"
echo ""
echo "10. Save and Enable the Event Stream"
echo ""
read -p "Press Enter when Event Stream is configured..."

# Step 4: Verify
echo ""
echo "[4/4] Verifying Setup..."
sleep 5

diagnostics=$(curl -s "${GATEWAY_URL}/system/zerobus/diagnostics")
echo ""
echo "=== Module Diagnostics ==="
echo "$diagnostics"
echo ""

# Check if events are flowing
events_received=$(echo "$diagnostics" | grep "Total Events Received" | grep -o '[0-9]\+' | head -1)

if [ -n "$events_received" ] && [ "$events_received" -gt 0 ]; then
    echo "=================================================="
    echo "✓ SUCCESS! Data is flowing to Databricks!"
    echo "=================================================="
    echo ""
    echo "Events received: $events_received"
    echo ""
    echo "Check Databricks with:"
    echo "  SELECT * FROM ignition_demo.scada_data.tag_events"
    echo "  ORDER BY event_time DESC LIMIT 100;"
else
    echo "=================================================="
    echo "⚠ Setup complete, but no events yet"
    echo "=================================================="
    echo ""
    echo "Troubleshooting:"
    echo "1. Check Event Stream is enabled in Designer"
    echo "2. Verify tags exist and are changing"
    echo "3. Check Gateway logs: tail -f /usr/local/ignition/logs/wrapper.log"
    echo "4. Run diagnostics: curl ${GATEWAY_URL}/system/zerobus/diagnostics"
fi

echo ""
echo "Deployment complete!"
echo ""

