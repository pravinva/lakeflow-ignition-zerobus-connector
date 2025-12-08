#!/bin/bash
#
# Install Event-Driven Zerobus Module
# Run this script to upgrade from polling to real-time tag subscriptions
#

set -e

echo "🚀 Installing Event-Driven Zerobus Module"
echo "=========================================="
echo ""

# Stop Ignition (if running)
echo "1. Stopping Ignition Gateway..."
sudo launchctl stop org.tanukisoftware.wrapper.Ignition-Gateway
sleep 5

# Remove old module
echo "2. Removing old module..."
sudo rm -f /usr/local/ignition/user-lib/modules/com.example.ignition.zerobus*.modl

# Install new module
echo "3. Installing new module..."
sudo cp /Users/pravin.varma/Documents/Demo/lakeflow-ignition-zerobus-connector/module/build/modules/zerobus-connector-1.0.0.modl \
     /usr/local/ignition/user-lib/modules/

# Start Ignition
echo "4. Starting Ignition Gateway..."
sudo launchctl start org.tanukisoftware.wrapper.Ignition-Gateway
echo "   Waiting for Gateway to start (15 seconds)..."
sleep 15

echo ""
echo "✅ Installation complete!"
echo ""
echo "📊 Test with:"
echo "   curl http://localhost:8088/system/zerobus/diagnostics"
echo ""
echo "⚡ EVENT-DRIVEN FEATURES:"
echo "   - Real-time tag change events (no polling delay)"
echo "   - Millisecond latency"
echo "   - Higher throughput (1000s of events/sec)"
echo "   - No missed events"
echo ""

