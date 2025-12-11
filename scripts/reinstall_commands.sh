#!/bin/bash
# Manual commands to reinstall the module
# Run these commands one by one in your terminal

echo "Run these commands:"
echo ""
echo "# 1. Stop Ignition"
echo "sudo launchctl stop com.inductiveautomation.ignition"
echo ""
echo "# 2. Remove old module"
echo "sudo rm -f /usr/local/ignition/user-lib/modules/*zerobus*.modl"
echo ""
echo "# 3. Copy new module"
echo "sudo cp /Users/pravin.varma/Documents/Demo/lakeflow-ignition-zerobus-connector/module/build/modules/zerobus-connector-1.0.0.modl /usr/local/ignition/user-lib/modules/"
echo ""
echo "# 4. Set permissions"
echo "sudo chown pravin.varma:wheel /usr/local/ignition/user-lib/modules/zerobus-connector-1.0.0.modl"
echo "sudo chmod 644 /usr/local/ignition/user-lib/modules/zerobus-connector-1.0.0.modl"
echo ""
echo "# 5. Start Ignition"
echo "sudo launchctl start com.inductiveautomation.ignition"
echo ""
echo "# 6. Wait and check"
echo "sleep 15"
echo "curl http://localhost:8088/system/zerobus/health"

