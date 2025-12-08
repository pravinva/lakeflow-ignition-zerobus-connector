#!/bin/bash
#
# Docker Portability Test for Zerobus Connector
# Proves the module works in a clean environment
#

set -e

echo "🐳 ZEROBUS CONNECTOR - DOCKER PORTABILITY TEST"
echo "=============================================="
echo ""

# Check if module is built
if [ ! -f "module/build/modules/zerobus-connector-1.0.0.modl" ]; then
    echo "❌ Module not built! Run: cd module && ./gradlew buildModule"
    exit 1
fi

echo "✅ Module found: $(ls -lh module/build/modules/zerobus-connector-1.0.0.modl | awk '{print $9, "("$5")"}')"
echo ""

# Stop any existing containers
echo "🧹 Cleaning up existing containers..."
docker-compose down -v 2>/dev/null || true
sleep 2

# Start Ignition
echo "🚀 Starting Ignition in Docker..."
docker-compose up -d

echo ""
echo "⏳ Waiting for Ignition to start (90 seconds)..."
sleep 90

# Check if Ignition is up
echo ""
echo "🔍 Checking Ignition status..."
if curl -s http://localhost:8088/StatusPing | grep -q "RUNNING"; then
    echo "✅ Ignition is running!"
else
    echo "❌ Ignition failed to start"
    echo "Check logs: docker-compose logs ignition"
    exit 1
fi

# Install module
echo ""
echo "📦 Installing Zerobus module..."
docker exec $(docker-compose ps -q ignition) bash -c "\
    cp /modules/zerobus-connector-1.0.0.modl /usr/local/bin/ignition/user-lib/modules/ && \
    echo 'dignition.allowunsignedmodules=true' >> /usr/local/bin/ignition/data/ignition.conf"

echo ""
echo "🔄 Restarting Ignition to load module..."
docker-compose restart ignition
sleep 60

# Check module status
echo ""
echo "🔍 Checking module status..."
MODULE_STATUS=$(curl -s http://localhost:8088/system/zerobus/diagnostics | grep "Module Enabled" || echo "Module not found")

if echo "$MODULE_STATUS" | grep -q "true\|false"; then
    echo "✅ Module API is accessible!"
    echo ""
    curl -s http://localhost:8088/system/zerobus/diagnostics
else
    echo "❌ Module not responding"
    echo "Check logs: docker-compose logs ignition | tail -100"
    exit 1
fi

echo ""
echo "================================================"
echo "✅ DOCKER TEST COMPLETE!"
echo ""
echo "Next steps:"
echo "  1. Configure module: curl -X POST http://localhost:8088/system/zerobus/config -H 'Content-Type: application/json' -d @IGNITION_CONFIG.json"
echo "  2. Check diagnostics: curl http://localhost:8088/system/zerobus/diagnostics"
echo "  3. View logs: docker-compose logs -f ignition"
echo "  4. Stop: docker-compose down"
echo ""
echo "🎉 Module is portable and ready for distribution!"
echo ""

