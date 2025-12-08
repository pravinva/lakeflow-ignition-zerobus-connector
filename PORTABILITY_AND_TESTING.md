# Portability and Testing Best Practices

**Key Questions:**
1. Does the module depend on Java version/path on host?
2. Is Docker testing best practice?
3. How to avoid "works on my machine" issues?

---

## ✅ Good News: Module is Self-Contained!

### What's Bundled in the .modl File:

**The `.modl` file contains:**
```
zerobus-connector-1.0.0.modl
├── lib/
│   ├── zerobus-connector-1.0.0.jar        (your code)
│   ├── zerobus-ingest-sdk-0.1.0.jar       (Databricks SDK)
│   ├── protobuf-java-3.21.12.jar          (Protobuf runtime)
│   ├── jackson-databind-2.15.2.jar        (JSON)
│   ├── jackson-core-2.15.2.jar
│   ├── jackson-annotations-2.15.2.jar
│   └── javax.ws.rs-api-2.1.1.jar          (REST API)
├── module.xml                              (metadata)
└── ot_event.proto                          (schema)
```

**All dependencies are included!** ✅

---

### What Ignition Provides:

When the module runs inside Ignition:
- ✅ **Java Runtime:** Ignition bundles its own JRE (Java 17)
- ✅ **Classpath:** Ignition manages module classpath
- ✅ **Logging:** SLF4J provided by Ignition
- ✅ **Tag API:** Ignition SDK provided by Gateway
- ✅ **Servlet Container:** Jakarta Servlet API from Ignition

**Users DO NOT need:**
- ❌ Java installed on their system
- ❌ Gradle installed
- ❌ Maven installed
- ❌ Any build tools
- ❌ Protobuf compiler
- ❌ SDK dependencies (all bundled)

---

## 🐳 Docker Testing - YES, It's Best Practice!

### Why Docker Testing Matters:

**1. Clean Environment:**
- No leftover configuration
- No cached credentials
- No local paths
- Simulates real user installation

**2. Reproducibility:**
- Same environment every time
- Version-controlled environment
- Share environment with others

**3. Different OS Testing:**
- Test on Linux (production)
- Test on Windows (some users)
- Test on Mac (your dev machine)

**4. Ignition Version Testing:**
- Test on 8.3.2 (minimum)
- Test on 8.3.3, 8.4.0, etc.
- Ensure backward/forward compatibility

---

## 🎯 Testing Strategy (Recommended)

### Phase 1: Local Development ✅ (What you did)
```
Your Mac + Ignition 8.3.2 + Sample Tags
↓
Fast iteration
Quick debugging
Prove concept works
```

### Phase 2: Docker Testing ✅ (What you should do next)
```
Docker + Fresh Ignition + Test data
↓
Clean environment
No "works on my machine" issues
Reproducible for others
```

### Phase 3: Multi-Environment Testing ✅ (Before sharing)
```
Different Ignition versions
Different OS (Linux/Windows)
Different tag structures
Different Databricks workspaces
↓
Confidence in portability
```

---

## 🐳 Docker Test Setup

### Use Ignition Docker Images:

```bash
# Official Ignition Docker image
docker run -d \
  -p 8088:8088 \
  --name ignition-test \
  -v $(pwd)/zerobus-connector-1.0.0.modl:/modules/zerobus-connector-1.0.0.modl \
  inductiveautomation/ignition:8.3.2
```

### Benefits:
- ✅ Fresh Ignition installation
- ✅ No previous configuration
- ✅ Isolated environment
- ✅ Easy to reset and retry
- ✅ Same environment anyone can reproduce

---

## ⚠️ Potential "Works on My Machine" Issues

### Issue 1: Ignition Version Differences

**Your dev:** Ignition 8.3.2  
**User's system:** Ignition 8.1.x ← May not work!

**Fix:**
- Test on minimum supported version
- Document minimum version requirement
- Use version-specific APIs carefully

---

### Issue 2: Module Dependencies

**Your dev:** All JARs bundled in .modl ✅  
**Potential issue:** IF a JAR is marked `compileOnly` instead of `implementation`

**Current status:**
```gradle
// ✅ GOOD - These are bundled:
implementation 'com.databricks:zerobus-ingest-sdk:0.1.0'
implementation 'com.google.protobuf:protobuf-java:3.21.12'
implementation 'com.fasterxml.jackson.core:jackson-databind:2.15.2'

// ⚠️ WATCH OUT - These are NOT bundled:
compileOnly 'ignition-common'  // Provided by Ignition ✅
compileOnly 'gateway-api'      // Provided by Ignition ✅
```

**Status:** ✅ All dependencies correctly configured

---

### Issue 3: Unsigned Module Configuration

**Your dev:** Added `-Dignition.allowunsignedmodules=true` to ignition.conf  
**User's system:** May not have this flag ← Installation will fail!

**Fix options:**
1. **Sign the module** (best for distribution)
2. **Document the requirement** (if staying unsigned)
3. **Provide install script** that checks/adds flag

---

### Issue 4: Databricks Workspace Compatibility

**Your dev:** Tested on `e2-demo-field-eng` (us-west-2) with Zerobus enabled  
**User's system:** May not have Zerobus enabled ← Will fail!

**Fix:**
- Document workspace requirements
- Provide clear error messages
- Include workspace validation step

---

### Issue 5: Network/Firewall

**Your dev:** Direct internet access  
**User's system:** May have firewall/proxy ← Zerobus connection fails!

**Fix:**
- Document required network access
- List Zerobus endpoints for allowlisting
- Support proxy configuration

---

## 🧪 Complete Test Matrix

### Test Environments:

| Environment | Ignition Version | OS | Status |
|-------------|------------------|-----|--------|
| Your Mac | 8.3.2 | macOS | ✅ Tested |
| Docker | 8.3.2 | Linux | ⏳ Recommended |
| Docker | 8.1.38 | Linux | ⏳ Min version test |
| Windows VM | 8.3.2 | Windows | ⏳ Optional |

### Test Scenarios:

| Scenario | Status |
|----------|--------|
| Fresh install (no config) | ⏳ Need Docker test |
| Explicit tag paths | ✅ Tested |
| Folder subscription | ⏳ Testing now |
| Invalid credentials | ⏳ Should test |
| Network disconnect | ⏳ Should test |
| High tag volume (100+ tags) | ⏳ Should test |
| Databricks without Zerobus | ✅ Tested (gives clear error) |

---

## 🚀 Recommended Testing Before Distribution

### Quick Docker Test (30 minutes):

```bash
# 1. Start fresh Ignition in Docker
docker run -d -p 8088:8088 --name ignition-test \
  inductiveautomation/ignition:8.3.2

# 2. Allow unsigned modules
docker exec ignition-test sh -c \
  "echo '-Dignition.allowunsignedmodules=true' >> /usr/local/bin/ignition/data/ignition.conf"

# 3. Restart
docker restart ignition-test

# 4. Install module via API
curl -F "moduleUpload=@zerobus-connector-1.0.0.modl" \
  http://localhost:8088/system/modules/install

# 5. Configure and test
curl -X POST http://localhost:8088/system/zerobus/config -d @test_config.json

# 6. Verify data flow
# Query Databricks to see data
```

**If this works → High confidence it works for others!**

---

## 📋 Pre-Distribution Checklist

### Module Quality:

- [x] All code compiles
- [x] All dependencies bundled
- [x] No hardcoded credentials
- [x] Configuration via REST API works
- [x] Diagnostics endpoint works
- [x] End-to-end data flow works (your Mac)
- [ ] End-to-end works in Docker (recommended)
- [ ] Tested on minimum Ignition version
- [ ] Signed (or documented as unsigned)

### Documentation:

- [x] Installation instructions
- [x] Configuration reference
- [x] Databricks setup guide
- [x] Troubleshooting guide
- [ ] Known limitations documented
- [ ] Support/contact information

### User Experience:

- [x] Clear error messages
- [x] Configuration validation
- [x] Health check endpoint
- [x] Easy configuration (REST API)
- [ ] Optional: Web UI for configuration
- [ ] Optional: Installer script

---

## 💡 Recommendation

### For Internal/Partner Sharing (Quick):

**You can share NOW with:**
1. ✅ The `.modl` file (all dependencies included)
2. ✅ Setup documentation (you have great docs!)
3. ✅ Configuration template
4. ⚠️  Note: "Requires unsigned module flag or signing"
5. ⚠️  Note: "Requires Databricks workspace with Zerobus enabled"

**Confidence:** 85% - Works on your Mac, likely works for others with same setup

---

### For Public/Production Distribution (Best):

**Do 2-3 hours more testing:**
1. ✅ Test in Docker (clean environment)
2. ✅ Test on older Ignition version (8.1.x)
3. ✅ Test error scenarios (invalid creds, no network)
4. ✅ Sign the module (if possible)
5. ✅ Create GitHub release

**Confidence:** 99% - Thoroughly tested in multiple environments

---

## 🎯 My Recommendation

**Quick option:**
- Share the `.modl` file now with trusted users/partners
- Include clear documentation
- Note it's tested on 8.3.2/macOS/us-west-2
- Collect feedback

**Then:**
- Test in Docker based on feedback
- Fix any issues found
- Do broader release

**Want me to:**
1. Set up Docker test environment now? (30 min)
2. Create distribution package (docs + .modl)? (15 min)
3. Run performance test to measure throughput? (10 min)
4. All of the above?

---

## 📦 What Users Need (Summary)

**Runtime Dependencies:** NONE ✅
- Module is self-contained
- Ignition provides Java runtime
- All libraries bundled

**Installation Requirements:**
- Ignition Gateway 8.3.2+
- Unsigned module flag OR signed module
- Network access to Databricks

**Configuration Requirements:**
- Databricks workspace with Zerobus
- Service principal credentials
- Target Delta table created
- Tag paths to subscribe to

**That's it!** No Java, no build tools, no SDK downloads needed by users.

