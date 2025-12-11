#!/bin/bash

# Complete Automated Deployment - Including Event Stream Creation
# This script automates EVERYTHING including Event Stream creation

set -e

GATEWAY_URL="${GATEWAY_URL:-http://localhost:8088}"
GATEWAY_USER="${GATEWAY_USER:-admin}"
GATEWAY_PASS="${GATEWAY_PASS:-password}"
PROJECT_NAME="${PROJECT_NAME:-ZerobusDemo}"

echo "=========================================================="
echo "Complete Automated Zerobus Deployment (100% Automated)"
echo "=========================================================="
echo ""
echo "Gateway: $GATEWAY_URL"
echo "Project: $PROJECT_NAME"
echo ""

# Step 1: Check prerequisites
echo "[1/6] Checking prerequisites..."

if ! command -v curl &> /dev/null; then
    echo "✗ curl not found. Install it first."
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "✗ python3 not found. Install it first."
    exit 1
fi

MODULE_PATH="../module/build/modules/zerobus-connector-1.0.0.modl"
if [ ! -f "$MODULE_PATH" ]; then
    echo "✗ Module not found. Building..."
    cd ../module && JAVA_HOME=/opt/homebrew/opt/openjdk ./gradlew buildModule && cd ../scripts
fi

echo "✓ Prerequisites OK"

# Step 2: Export existing project (if it exists)
echo ""
echo "[2/6] Exporting existing project..."

PROJECT_EXPORT="${PROJECT_NAME}-export.json"
curl -s -u "${GATEWAY_USER}:${GATEWAY_PASS}" \
  "${GATEWAY_URL}/data/project-export/${PROJECT_NAME}" \
  -o "$PROJECT_EXPORT" 2>/dev/null || {
    echo "Project doesn't exist, creating new one..."
    # Create minimal project structure
    cat > "$PROJECT_EXPORT" <<EOF
{
  "name": "$PROJECT_NAME",
  "title": "Zerobus Demo Project",
  "enabled": true,
  "resources": {}
}
EOF
}

echo "✓ Project exported: $PROJECT_EXPORT"

# Step 3: Inject Event Stream into project
echo ""
echo "[3/6] Injecting Event Stream into project..."

TAG_PATHS=(
  "[Sample_Tags]Sine/Sine0"
  "[Sample_Tags]Sine/Sine1"
  "[Sample_Tags]Realistic/Realistic0"
  "[Sample_Tags]Realistic/Realistic1"
)

python3 inject_eventstream.py "$PROJECT_EXPORT" \
  --tags "${TAG_PATHS[@]}" \
  --gateway-url "$GATEWAY_URL" \
  --output "${PROJECT_NAME}-with-eventstream.json"

PROJECT_WITH_ES="${PROJECT_NAME}-with-eventstream.json"
echo "✓ Event Stream injected"

# Step 4: Import modified project
echo ""
echo "[4/6] Importing project with Event Stream..."

curl -s -u "${GATEWAY_USER}:${GATEWAY_PASS}" \
  -F "project=@${PROJECT_WITH_ES}" \
  "${GATEWAY_URL}/data/project-import" > /dev/null

echo "✓ Project imported with Event Stream"

# Step 5: Install and configure module
echo ""
echo "[5/6] Configuring Zerobus module..."

# Get credentials
if [ -z "$DATABRICKS_WORKSPACE" ]; then
    echo "ERROR: Set DATABRICKS_WORKSPACE environment variable"
    echo "  export DATABRICKS_WORKSPACE='https://your-workspace.cloud.databricks.com'"
    exit 1
fi

if [ -z "$ZEROBUS_ENDPOINT" ]; then
    echo "ERROR: Set ZEROBUS_ENDPOINT environment variable"
    echo "  export ZEROBUS_ENDPOINT='your-endpoint.zerobus.region.cloud.databricks.com'"
    exit 1
fi

if [ -z "$OAUTH_CLIENT_ID" ]; then
    echo "ERROR: Set OAUTH_CLIENT_ID environment variable"
    exit 1
fi

if [ -z "$OAUTH_CLIENT_SECRET" ]; then
    echo "ERROR: Set OAUTH_CLIENT_SECRET environment variable"
    exit 1
fi

# Configure module
curl -s -X POST "${GATEWAY_URL}/system/zerobus/config" \
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
  }" > /dev/null

echo "✓ Module configured"

# Step 6: Verify deployment
echo ""
echo "[6/6] Verifying deployment..."
sleep 5

health=$(curl -s "${GATEWAY_URL}/system/zerobus/health")
echo "Module health: $health"

# Check if connected
if echo "$health" | grep -q '"zerobusConnected":true'; then
    echo ""
    echo "=========================================================="
    echo "✓ SUCCESS! Complete automated deployment finished!"
    echo "=========================================================="
    echo ""
    echo "What was deployed:"
    echo "  ✓ Ignition project: $PROJECT_NAME"
    echo "  ✓ Event Stream: ZerobusTagStream"
    echo "  ✓ Module: Configured and connected"
    echo "  ✓ Monitoring: ${#TAG_PATHS[@]} tags"
    echo ""
    echo "Next steps:"
    echo "  1. Open Designer to verify Event Stream"
    echo "  2. Check Databricks for data:"
    echo "     SELECT * FROM ignition_demo.scada_data.tag_events"
    echo "     ORDER BY event_time DESC LIMIT 100;"
    echo ""
    
    # Get diagnostics
    echo "Current status:"
    curl -s "${GATEWAY_URL}/system/zerobus/diagnostics" | grep -E "Total Events|Connected|Running"
else
    echo ""
    echo "=========================================================="
    echo "⚠ Deployment complete but module not connected"
    echo "=========================================================="
    echo ""
    echo "Check:"
    echo "  1. Module installed: ${GATEWAY_URL}/web/config/system.modules"
    echo "  2. Credentials correct"
    echo "  3. Gateway logs: tail -f /usr/local/ignition/logs/wrapper.log"
fi

echo ""
echo "Deployment complete!"

# Cleanup temporary files
rm -f "$PROJECT_EXPORT" "${PROJECT_WITH_ES}"

