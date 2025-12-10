#!/bin/bash
# Quick reinstall script
echo "🛑 Stopping Ignition..."
sudo pkill -9 -f ignition
sleep 3

echo "🗑️  Removing old module..."
sudo rm -f /usr/local/ignition/user-lib/modules/zerobus-connector-*.modl

echo "📥 Installing fixed module..."
sudo cp /Users/pravin.varma/Documents/Demo/lakeflow-ignition-zerobus-connector/module/build/modules/zerobus-connector-1.0.0.modl /usr/local/ignition/user-lib/modules/

echo "🚀 Starting Ignition..."
sudo launchctl start org.tanukisoftware.wrapper.Ignition-Gateway

echo "⏳ Waiting 30 seconds..."
sleep 30

echo "✅ Ready! Now run:"
echo "   curl -X POST http://localhost:8088/system/zerobus/config -H 'Content-Type: application/json' -d '{...}'"

