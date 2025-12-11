#!/bin/bash

# Automated Event Forwarder Installation Script
# This script installs the gateway event forwarder as an alternative to Event Streams

set -e

GATEWAY_URL="${GATEWAY_URL:-http://localhost:8088}"
GATEWAY_USER="${GATEWAY_USER:-admin}"
GATEWAY_PASS="${GATEWAY_PASS:-password}"

echo "============================================"
echo "Event Forwarder Installation Script"
echo "============================================"
echo ""
echo "Gateway URL: $GATEWAY_URL"
echo "Gateway User: $GATEWAY_USER"
echo ""

# Step 1: Check if Gateway is running
echo "[1/5] Checking Gateway connection..."
if curl -s -f "$GATEWAY_URL/StatusPing" > /dev/null; then
    echo "✓ Gateway is accessible"
else
    echo "✗ Cannot connect to Gateway at $GATEWAY_URL"
    exit 1
fi

# Step 2: Install Zerobus module
echo ""
echo "[2/5] Installing Zerobus Connector module..."
MODULE_PATH="$(dirname "$0")/../module/build/modules/zerobus-connector-1.0.0.modl"

if [ ! -f "$MODULE_PATH" ]; then
    echo "✗ Module file not found: $MODULE_PATH"
    echo "Run: cd module && ./gradlew buildModule"
    exit 1
fi

# Upload module via Gateway API
AUTH=$(echo -n "${GATEWAY_USER}:${GATEWAY_PASS}" | base64)

echo "Uploading module..."
curl -X POST "$GATEWAY_URL/system/modules/upload" \
  -H "Authorization: Basic $AUTH" \
  -F "file=@${MODULE_PATH}" \
  --silent --show-error

echo "✓ Module uploaded"

# Step 3: Install Gateway startup script
echo ""
echo "[3/5] Installing Gateway startup script..."
SCRIPT_PATH="$(dirname "$0")/gateway_event_forwarder.py"

if [ ! -f "$SCRIPT_PATH" ]; then
    echo "✗ Script file not found: $SCRIPT_PATH"
    exit 1
fi

# Note: This would require a Gateway API call to install the script
# For now, provide manual instructions
echo ""
echo "MANUAL STEP REQUIRED:"
echo "1. Open Gateway web interface: $GATEWAY_URL"
echo "2. Go to: Config > Scripting > Gateway Event Scripts"
echo "3. Add a 'Startup' script"
echo "4. Copy contents from: $SCRIPT_PATH"
echo "5. Save and restart Gateway"
echo ""
read -p "Press Enter when you've completed this step..."

# Step 4: Configure module
echo ""
echo "[4/5] Configuring Zerobus module..."

# Create configuration JSON
cat > /tmp/zerobus_config.json << 'EOF'
{
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
}
EOF

echo "Configuration template created at: /tmp/zerobus_config.json"
echo "Edit this file with your Databricks credentials, then run:"
echo ""
echo "  curl -X POST $GATEWAY_URL/system/zerobus/config \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d @/tmp/zerobus_config.json"
echo ""
read -p "Press Enter after configuring..."

# Step 5: Test connection
echo ""
echo "[5/5] Testing setup..."
echo "Checking module health..."
curl -s "$GATEWAY_URL/system/zerobus/health" | python -m json.tool || echo "Health check failed"

echo ""
echo "Checking diagnostics..."
curl -s "$GATEWAY_URL/system/zerobus/diagnostics"

echo ""
echo "============================================"
echo "Installation Complete!"
echo "============================================"
echo ""
echo "Next steps:"
echo "1. Verify data is flowing to Databricks"
echo "2. Monitor Gateway logs: tail -f /usr/local/ignition/logs/wrapper.log"
echo "3. Check diagnostics: curl $GATEWAY_URL/system/zerobus/diagnostics"
echo ""

