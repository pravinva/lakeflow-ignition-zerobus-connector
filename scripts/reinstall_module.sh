#!/bin/bash

# Script to uninstall old module and install new event-driven module
set -e

MODULE_PATH="/Users/pravin.varma/Documents/Demo/lakeflow-ignition-zerobus-connector/module/build/modules/zerobus-connector-1.0.0.modl"
USER_LIB_MODULES="/usr/local/ignition/user-lib/modules"

echo "========================================="
echo "Zerobus Module Reinstallation"
echo "========================================="
echo ""

# Step 1: Stop Ignition
echo "[1/5] Stopping Ignition Gateway..."
sudo launchctl stop com.inductiveautomation.ignition
sleep 3

# Step 2: Remove old module files
echo "[2/5] Removing old module files..."
if [ -d "$USER_LIB_MODULES" ]; then
    sudo find "$USER_LIB_MODULES" -name "*zerobus*.modl" -delete
    echo "✓ Old module files removed"
else
    echo "⚠ Module directory not found"
fi

# Step 3: Copy new module
echo "[3/5] Installing new event-driven module..."
if [ -f "$MODULE_PATH" ]; then
    sudo cp "$MODULE_PATH" "$USER_LIB_MODULES/"
    sudo chown pravin.varma:wheel "$USER_LIB_MODULES/zerobus-connector-1.0.0.modl"
    sudo chmod 644 "$USER_LIB_MODULES/zerobus-connector-1.0.0.modl"
    echo "✓ New module copied"
else
    echo "✗ Module file not found: $MODULE_PATH"
    exit 1
fi

# Step 4: Clear module cache
echo "[4/5] Clearing module cache..."
if [ -d "/usr/local/ignition/.moduleconfig" ]; then
    sudo rm -rf /usr/local/ignition/.moduleconfig/zerobus* 2>/dev/null || true
    echo "✓ Cache cleared"
fi

# Step 5: Start Ignition
echo "[5/5] Starting Ignition Gateway..."
sudo launchctl start com.inductiveautomation.ignition
sleep 10

echo ""
echo "========================================="
echo "Installation Complete!"
echo "========================================="
echo ""
echo "Checking module status..."
sleep 5

# Check if module loaded
curl -s http://localhost:8088/system/zerobus/health 2>/dev/null | python -m json.tool || echo "Module not responding yet, wait a moment..."

echo ""
echo "To view logs:"
echo "  tail -f /usr/local/ignition/logs/wrapper.log | grep Zerobus"
echo ""

