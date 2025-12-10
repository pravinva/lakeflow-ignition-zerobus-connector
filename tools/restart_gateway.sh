#!/bin/bash
# Restart Ignition Gateway to pick up Event Stream config changes

echo "Restarting Ignition Gateway..."
sudo /usr/local/ignition/ignition.sh restart

echo ""
echo "Waiting for Gateway to start..."
sleep 10

echo "Testing Gateway..."
curl -s http://localhost:8088/system/zerobus/diagnostics | head -20

echo ""
echo "✓ Gateway restarted. Now:"
echo "  1. Open Designer"
echo "  2. Event Streams → zerobus_automation"
echo "  3. Should see all tags and handler configured"
echo "  4. Enable the Event Stream"

