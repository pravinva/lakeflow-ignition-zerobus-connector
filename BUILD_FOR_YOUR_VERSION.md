# Building for Your Ignition Version

## Pre-Built Module (Recommended for 8.3+)

**For Ignition 8.3.x users**: Use the pre-built module in `releases/`

```bash
# Download and install
releases/zerobus-connector-1.0.0.modl
```

**Compatibility**: Built against 8.3.2, requires minimum 8.1.0+

---

## For Ignition 8.1 / 8.2 Customers

The pre-built module **may work** on 8.1/8.2, but if you encounter compatibility issues, rebuild it on your system:

### Quick Rebuild

```bash
#!/bin/bash
# Run this on your Ignition 8.1/8.2 Gateway server

cd module

# Set Java (adjust path for your system)
export JAVA_HOME="/path/to/jdk-17"
export PATH="$JAVA_HOME/bin:$PATH"

# Update build.gradle to use your Ignition version
# Edit: buildForIgnitionVersion = '8.1.x'  (match your version)

# Build
./gradlew clean buildModule

# Module will be at:
# build/modules/zerobus-connector-1.0.0.modl
```

### Detailed Steps

#### Step 1: Install JDK 17

```bash
# macOS
brew install openjdk@17

# Linux
sudo apt install openjdk-17-jdk  # Ubuntu/Debian
sudo yum install java-17-openjdk-devel  # RHEL/CentOS

# Windows
# Download from https://adoptium.net/
```

#### Step 2: Update build.gradle

Edit `module/build.gradle`:

```gradle
ext {
    // Change this to match your Ignition installation version
    buildForIgnitionVersion = '8.1.x'  // e.g., '8.1.17'
    
    // This stays at 8.1.0 (minimum required version)
    minIgnitionVersion = '8.1.0'
    
    slf4jVersion = '1.7.36'
    protobufVersion = '3.21.12'
}
```

Also update the JAR paths to match your Ignition installation:

```gradle
dependencies {
    // Update these paths if your Ignition is installed elsewhere
    compileOnly files("/usr/local/ignition/lib/core/gateway/gateway-api-${buildForIgnitionVersion}.jar")
    compileOnly files("/usr/local/ignition/lib/core/gateway/gateway-api-web-${buildForIgnitionVersion}.jar")
    compileOnly files("/usr/local/ignition/lib/core/gateway/gateway-web-${buildForIgnitionVersion}.jar")
    
    // ... rest of dependencies ...
}
```

#### Step 3: Build

```bash
cd module

# On macOS with Homebrew JDK
export JAVA_HOME="/opt/homebrew/opt/openjdk@17"
export PATH="$JAVA_HOME/bin:$PATH"

# On Linux
export JAVA_HOME="/usr/lib/jvm/java-17-openjdk-amd64"
export PATH="$JAVA_HOME/bin:$PATH"

# On Windows
set JAVA_HOME=C:\Program Files\Eclipse Adoptium\jdk-17
set PATH=%JAVA_HOME%\bin;%PATH%

# Build the module
./gradlew clean buildModule

# On Windows
gradlew.bat clean buildModule
```

#### Step 4: Verify

```bash
ls -lah build/modules/zerobus-connector-1.0.0.modl

# Should show:
# zerobus-connector-1.0.0.modl  (~15-20 MB)
```

#### Step 5: Install

Upload `build/modules/zerobus-connector-1.0.0.modl` to your Ignition Gateway:

```
http://your-gateway:8088/web/config/system.modules
→ Install or Upgrade a Module
→ Choose file: zerobus-connector-1.0.0.modl
→ Install
```

---

## Troubleshooting Build Issues

### Cannot find gateway-api JARs

**Error:**
```
Cannot expand ZIP '/usr/local/ignition/lib/core/gateway/gateway-api-8.x.x.jar' as it does not exist.
```

**Fix:**
```bash
# Find your Ignition JARs
find /usr/local/ignition -name "gateway-api*.jar"
find /opt/ignition -name "gateway-api*.jar"  # Alternative path
find /Program\ Files/Inductive\ Automation -name "gateway-api*.jar"  # Windows

# Update build.gradle with the correct version number
```

### Java version mismatch

**Error:**
```
Unsupported class file major version
```

**Fix:**
```bash
# Verify Java 17 is being used
java -version  # Should show "17.x.x"

# If wrong version, set JAVA_HOME correctly
export JAVA_HOME="/path/to/jdk-17"
```

### Out of memory during build

**Error:**
```
java.lang.OutOfMemoryError: Java heap space
```

**Fix:**
```bash
# Increase Gradle memory
export GRADLE_OPTS="-Xmx2048m"
./gradlew clean buildModule
```

---

## Module Compatibility Matrix

| Ignition Version | Pre-Built Module | Rebuild Required? | Notes |
|------------------|------------------|-------------------|-------|
| 8.3.0 - 8.3.x | ✅ Works | ❌ No | Recommended |
| 8.2.x | ⚠️ May work | ✅ If issues | Test first |
| 8.1.x | ⚠️ May work | ✅ If issues | Test first |
| 8.0.x | ❌ Unknown | ✅ Yes | Not tested |
| 7.9.x | ❌ Not compatible | ❌ N/A | Event APIs different |

---

## Why the Pre-Built Module Works Across Versions

The module is built against Ignition 8.3.2 but declares a minimum version of 8.1.0 because:

1. **API Stability**: Core Gateway APIs haven't changed significantly
2. **Runtime JARs**: Module uses JARs provided by the Gateway at runtime
3. **No Version-Specific Features**: Code doesn't use 8.3-specific APIs

However:
- **Servlet API**: Changed from `javax` to `jakarta` in 8.3
- **Some APIs**: May have method signature changes

If you encounter `NoSuchMethodError` or `ClassNotFoundException`, rebuild for your version.

---

## Testing Compatibility

After installing the module:

```bash
# Check module loaded
curl http://gateway:8088/system/zerobus/health

# Should return:
# {"status": "ok", "moduleLoaded": true, ...}

# If you get errors, check Gateway logs
tail -f /usr/local/ignition/logs/wrapper.log | grep -i zerobus
```

---

## Need Help?

- **Module loads but doesn't work**: Check `USER_GUIDE.md` for configuration
- **Build fails**: Post issue with full error log
- **Compatibility question**: Check Ignition version first: Gateway Web UI → System → About

---

## Quick Reference

### Pre-Built Module Location
```
releases/zerobus-connector-1.0.0.modl
```

### Build Command
```bash
cd module && ./gradlew clean buildModule
```

### Output Location
```
module/build/modules/zerobus-connector-1.0.0.modl
```

