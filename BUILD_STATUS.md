# Build Status - Module Dependencies

**Last Updated:** December 8, 2025  
**Status:** 🟡 **Partial Success - Zerobus SDK Found!**

---

## ✅ Dependency Resolution Progress

### 1. Databricks Zerobus Ingest SDK - FOUND! ✅

**Artifact:**
```gradle
implementation 'com.databricks:zerobus-ingest-sdk:0.1.0'
```

**Location:** Maven Central  
**URL:** https://repo.maven.apache.org/maven2/com/databricks/zerobus-ingest-sdk/0.1.0/

**Status:** ✅ **Available and downloads successfully**

---

### 2. Ignition SDK - NOT YET RESOLVED ⏳

**Problem:** Cannot find correct artifact coordinates in Inductive Automation Nexus

**Tried:**
```gradle
// ❌ Not found
compileOnly "com.inductiveautomation.ignitionsdk:tag-api:8.3.0"
compileOnly "com.inductiveautomation.ignitionsdk:tag-historian:8.3.0"
compileOnly "com.inductiveautomation.ignitionsdk:ignition-common:8.3.0"
compileOnly "com.inductiveautomation.ignitionsdk:gateway-api:8.3.0"
```

**Repository Tried:**
- `https://nexus.inductiveautomation.com/repository/public`
- `https://nexus.inductiveautomation.com/repository/inductiveautomation-releases`

**Compilation Errors:**
The Java source code requires these Ignition classes:
- `com.inductiveautomation.ignition.common.model.values.QualifiedValue`
- `com.inductiveautomation.ignition.common.tags.model.TagPath`
- `com.inductiveautomation.ignition.gateway.model.GatewayContext`
- `com.inductiveautomation.ignition.gateway.model.AbstractGatewayModuleHook`
- And many more...

---

## 🎯 Next Steps to Resolve

### Option 1: Contact Inductive Automation (Recommended)

**Action Required:**
1. Visit Ignition SDK forum: https://forum.inductiveautomation.com
2. Ask for correct Maven coordinates for Ignition 8.3.0 SDK
3. Specifically need:
   - Gateway API
   - Tag API / Tag Management
   - Common libraries

**Alternative:**
- Check Ignition SDK documentation
- Look for official module development guide
- May need SDK account/authentication for Nexus

### Option 2: Use Ignition SDK from Installation

Since you have Ignition 8.3.2 installed at `/usr/local/ignition/`, you could:

```gradle
dependencies {
    // Use JARs from local Ignition installation
    compileOnly fileTree(dir: '/usr/local/ignition/lib/core', include: '*.jar')
    compileOnly fileTree(dir: '/usr/local/ignition/lib/core/gateway', include: '*.jar')
}
```

**Pros:**
- Immediate access to correct SDK version
- Matches your installed Ignition version exactly

**Cons:**
- Not portable (requires Ignition installation)
- Build won't work in CI/CD without Ignition

### Option 3: Download SDK Manually

1. Download Ignition SDK from Inductive Automation website
2. Place JARs in `module/libs/` directory
3. Reference in `build.gradle`:

```gradle
dependencies {
    compileOnly fileTree(dir: 'libs', include: '*.jar')
}
```

---

## 🔧 Current Build Configuration

**File:** `module/build.gradle`

```gradle
repositories {
    mavenCentral()
    maven {
        url = "https://nexus.inductiveautomation.com/repository/public"
    }
}

dependencies {
    // ✅ WORKS - Zerobus SDK
    implementation 'com.databricks:zerobus-ingest-sdk:0.1.0'
    
    // ✅ WORKS - Protobuf
    implementation 'com.google.protobuf:protobuf-java:3.21.12'
    
    // ❌ NOT FOUND - Ignition SDK (commented out)
    // compileOnly "com.inductiveautomation.ignitionsdk:..."
    
    // ✅ WORKS - Logging
    compileOnly 'org.slf4j:slf4j-api:1.7.36'
}
```

---

## 📊 What We Learned

### ✅ Success: Zerobus SDK

The Databricks team has published the Zerobus Ingest SDK to Maven Central as:
- **Artifact ID:** `zerobus-ingest-sdk` (not `zerobus-sdk-java`)
- **Group ID:** `com.databricks`
- **Version:** `0.1.0`

This matches the GitHub repository: https://github.com/databricks/zerobus-sdk-java

### ⏳ Challenge: Ignition SDK

The Ignition SDK artifacts are not straightforward to find in public Nexus:
- May require authentication
- May need different artifact naming
- May need SDK download from Inductive Automation

---

## 🚀 Recommended Immediate Action

**For Pravin (Tester):**

1. **Try Local JARs Approach** (Quick test):
   ```bash
   cd /Users/pravin.varma/Documents/Demo/lakeflow-ignition-zerobus-connector/module
   
   # Add this to build.gradle dependencies:
   # compileOnly fileTree(dir: '/usr/local/ignition/lib/core', include: '*.jar')
   # compileOnly fileTree(dir: '/usr/local/ignition/lib/core/gateway', include: '*.jar')
   
   JAVA_HOME=/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home \
   ./gradlew clean compileJava
   ```

2. **If that works, build the module:**
   ```bash
   ./gradlew buildModule
   ```

3. **Install and test** in your Ignition Gateway!

---

## 📝 Files Updated

- ✅ `build.gradle` - Corrected repository and Zerobus SDK artifact ID
- ✅ Commented out Ignition SDK dependencies (not found)
- ✅ Gradle wrapper generated
- ✅ JDK 17 configured

---

## ✨ Bottom Line

**Good News:** 
- ✅ Zerobus SDK is available and working!
- ✅ Build system configured correctly
- ✅ All other dependencies resolve

**Remaining Issue:**
- ⏳ Need correct Ignition SDK artifact coordinates OR
- ⏳ Use local JARs from your Ignition installation

**Estimated Time to Resolve:** 
- With local JARs: **5 minutes**
- With correct Maven coordinates: **Depends on Inductive Automation response**

---

## 🔗 Resources

- **Zerobus SDK:** https://github.com/databricks/zerobus-sdk-java
- **Ignition Forum:** https://forum.inductiveautomation.com
- **Ignition SDK Guide:** https://docs.inductiveautomation.com/docs/8.1/sdk-documentation
- **Maven Search:** https://search.maven.org/search?q=g:com.inductiveautomation

---

**Next Update:** Once Ignition SDK is resolved and module builds successfully

