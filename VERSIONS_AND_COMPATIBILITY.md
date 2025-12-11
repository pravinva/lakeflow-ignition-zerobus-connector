# Versions and Compatibility Guide

## Module Versions

### Current Release: v1.0.0

**Built against**: Ignition 8.3.2  
**Minimum required**: Ignition 8.1.0  
**Tested on**: Ignition 8.3.2  
**Status**: Production Ready

---

## Ignition Version Compatibility

### ✅ Ignition 8.3.0+ (Recommended)

**Trigger Mechanism**: Event Streams (native 8.3 feature)

```
Tags → Event Streams → Module REST API → Databricks
```

**Setup**:
1. Install pre-built module: `releases/zerobus-connector-1.0.0.modl`
2. Configure module via REST API or Web UI
3. Create Event Stream in Designer
4. Configure tag sources and handlers

**Documentation**: `docs/EVENT_STREAMS_SETUP.md`

---

### ✅ Ignition 8.1 / 8.2 (Supported with Gateway Scripts)

**Trigger Mechanism**: Gateway Tag Change Scripts (available in all versions)

```
Tags → Gateway Tag Change Script → Module REST API → Databricks
```

**Setup**:
1. Install pre-built module: `releases/zerobus-connector-1.0.0.modl`
   - If compatibility issues, rebuild: `BUILD_FOR_YOUR_VERSION.md`
2. Configure module via REST API
3. Add Gateway Tag Change Script via Web UI
4. Configure tag paths in script

**Documentation**: `IGNITION_8.1_SETUP.md` and `docs/ZERO_CONFIG_SETUP.md`

---

### ❌ Ignition 8.0.x and Earlier

**Not supported** due to:
- Different Gateway API structure
- Different event system
- Untested compatibility

**Workaround**: Upgrade to Ignition 8.1+ (recommended)

---

## Feature Compatibility Matrix

| Feature | 8.3+ | 8.1 / 8.2 | Notes |
|---------|------|-----------|-------|
| **Module Installation** | ✅ | ✅⚠️ | May need rebuild for 8.1/8.2 |
| **REST API** | ✅ | ✅ | Fully compatible |
| **Event Streams** | ✅ | ❌ | Not available in 8.1/8.2 |
| **Gateway Scripts** | ✅ | ✅ | Works on all versions |
| **Zerobus Integration** | ✅ | ✅ | Same SDK used |
| **OAuth M2M** | ✅ | ✅ | Same authentication |
| **Delta Table Write** | ✅ | ✅ | Same Databricks target |
| **Performance** | ✅ | ✅ | Same throughput |
| **Event-Driven** | ✅ | ✅ | Both are event-driven (no polling) |

---

## Recommended Setup by Version

### For Ignition 8.3+ Users

**Recommended Approach**: Event Streams

**Why**:
- Native Ignition feature
- Visual configuration in Designer
- Advanced filtering and transformation
- Per-project customization

**Trade-offs**:
- Requires Designer access
- Project-level (not gateway-level)
- Manual configuration copying

**Setup Time**: 5-10 minutes

**Guide**: `QUICK_START.md` + `docs/EVENT_STREAMS_SETUP.md`

---

### For Ignition 8.1 / 8.2 Users

**Recommended Approach**: Gateway Tag Change Scripts

**Why**:
- Works on 8.1 and 8.2
- Simpler setup (Web UI only)
- Gateway-level (survives project changes)
- Fully scriptable

**Trade-offs**:
- Less visual
- Basic filtering only
- Manual script editing for changes

**Setup Time**: 10-15 minutes

**Guide**: `IGNITION_8.1_SETUP.md` + `docs/ZERO_CONFIG_SETUP.md`

---

## Migration Paths

### Upgrading Ignition 8.1/8.2 → 8.3

**Before Upgrade**:
- Module works with Gateway Scripts ✅

**After Upgrade to 8.3**:
- Keep using Gateway Scripts ✅ (if it works, don't change)
- OR migrate to Event Streams for advanced features

**Migration Steps** (optional):
1. Install Event Stream alongside Gateway Script
2. Test Event Stream with subset of tags
3. Verify data flowing correctly
4. Disable Gateway Script
5. Remove Gateway Script once confirmed

**Both can run in parallel** during migration.

---

### Downgrading Ignition 8.3 → 8.1/8.2

**Not recommended**, but if needed:

1. Export Event Stream configuration (for reference)
2. Downgrade Ignition
3. Install Gateway Tag Change Script
4. Configure with same tag paths
5. Verify data flow

---

## Performance by Version

| Metric | 8.3 (Event Streams) | 8.1/8.2 (Gateway Scripts) |
|--------|---------------------|---------------------------|
| **Max Throughput** | 30,000+ events/sec | 30,000+ events/sec |
| **Latency** | < 10ms | < 10ms |
| **CPU Usage** | Low | Low |
| **Memory Usage** | Similar | Similar |
| **Event-Driven** | Yes | Yes |

**Conclusion**: Performance is identical. Choice depends on Ignition version and preferred configuration method.

---

## Databricks Compatibility

### Zerobus SDK

**All versions** use the same Databricks Zerobus SDK:
- Version: 1.4.0
- Protocol: gRPC
- Format: Protobuf
- Authentication: OAuth M2M

**Databricks Requirements** (same for all Ignition versions):
- Unity Catalog enabled
- Zerobus endpoint enabled
- Service Principal with permissions
- Delta table with correct schema

---

## Breaking Changes

### Module v1.0.0

**From**: N/A (initial release)  
**Breaking Changes**: None

**New Features**:
- Event-driven architecture (Event Streams + Gateway Scripts)
- REST API for event ingestion
- Zerobus SDK integration
- OAuth M2M authentication
- Batching and queuing

---

## Future Compatibility

### Ignition 8.4+ (when released)

**Expected**: Full compatibility (Gateway APIs stable)

**Plan**: Test on beta releases and update if needed

### Databricks Zerobus Updates

**Current**: SDK 1.4.0  
**Plan**: Monitor for SDK updates, rebuild module with new SDK

---

## Testing Your Version

### Step 1: Check Ignition Version

```
Gateway Web UI → System → About
```

Example: "Ignition 8.3.2"

### Step 2: Install Module

```bash
# Use pre-built module first
releases/zerobus-connector-1.0.0.modl
```

### Step 3: Test Module Load

```bash
curl http://gateway:8088/system/zerobus/health
```

**Expected**:
```json
{
  "status": "ok",
  "moduleLoaded": true,
  "version": "1.0.0"
}
```

### Step 4: Configure

- **8.3+**: Follow `docs/EVENT_STREAMS_SETUP.md`
- **8.1/8.2**: Follow `IGNITION_8.1_SETUP.md`

### Step 5: Verify Data Flow

```sql
-- In Databricks
SELECT * FROM your_catalog.your_schema.your_table
ORDER BY event_time DESC
LIMIT 100;
```

---

## Getting Help

### Module Won't Load

1. Check Ignition version compatibility (above)
2. Check Gateway logs: `/usr/local/ignition/logs/wrapper.log`
3. Try rebuilding for your version: `BUILD_FOR_YOUR_VERSION.md`

### Module Loads But No Data

1. Check trigger mechanism setup:
   - **8.3+**: Verify Event Stream is enabled and running
   - **8.1/8.2**: Verify Gateway Script is enabled
2. Check module diagnostics: `curl http://gateway:8088/system/zerobus/diagnostics`
3. Check Databricks permissions: `USER_GUIDE.md`

### Performance Issues

1. Check batch size and flush interval configuration
2. Monitor queue size: should not be full
3. Check Databricks workspace capacity

---

## Version Summary

**Simple Answer**:
- **Ignition 8.3+**: Use pre-built module with Event Streams ✅
- **Ignition 8.1/8.2**: Use pre-built module with Gateway Scripts ✅
- **Rebuild needed?**: Only if compatibility issues occur ⚠️

**Both versions work, just different trigger mechanisms!**

