#!/bin/bash
set -e

echo "========================================="
echo "Installing Fixed Zerobus Module"
echo "========================================="
echo ""

echo "🔧 This module includes the critical fix:"
echo "   - firstPoll changed from static to instance variable"
echo "   - getMountManager() calls removed"
echo "   - Gradle duplicate handling configured"
echo ""

echo "📦 Module location:"
echo "   /Users/pravin.varma/Documents/Demo/lakeflow-ignition-zerobus-connector/module/build/modules/zerobus-connector-1.0.0.modl"
echo ""

echo "🛑 Step 1: Stopping Ignition..."
sudo pkill -9 -f ignition 2>/dev/null || echo "   (Ignition not running)"
sleep 3

echo "🗑️  Step 2: Removing old module..."
sudo rm -f /usr/local/ignition/user-lib/modules/zerobus-connector-*.modl

echo "📥 Step 3: Installing new module..."
sudo cp /Users/pravin.varma/Documents/Demo/lakeflow-ignition-zerobus-connector/module/build/modules/zerobus-connector-1.0.0.modl /usr/local/ignition/user-lib/modules/
ls -lh /usr/local/ignition/user-lib/modules/zerobus-connector-*.modl

echo "🚀 Step 4: Starting Ignition..."
sudo launchctl start org.tanukisoftware.wrapper.Ignition-Gateway

echo "⏳ Waiting 30 seconds for Ignition to start..."
for i in {30..1}; do
    echo -ne "   $i seconds remaining...\r"
    sleep 1
done
echo ""

echo "✅ Installation complete!"
echo ""
echo "🔍 Next steps:"
echo "   1. Configure the module:"
echo "      curl -X POST http://localhost:8088/system/zerobus/config -H 'Content-Type: application/json' -d @config.json"
echo ""
echo "   2. Check logs for 'FIRST POLL EXECUTING':"
echo "      tail -100 /usr/local/ignition/logs/wrapper.log | grep 'FIRST POLL'"
echo ""
echo "   3. Verify diagnostics:"
echo "      curl -s http://localhost:8088/system/zerobus/diagnostics"
echo ""
echo "See DEBUG_SESSION_RESULTS.md for detailed testing instructions."

