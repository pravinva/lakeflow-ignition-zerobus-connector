# DEVELOPER.md

## Role

Act as the **implementation engineer**. Use this document to plan and track the Ignition module and Zerobus integration work.

## Goal

Build an Ignition Gateway module that streams selected tags/events into Databricks Delta tables via Zerobus Ingest using the Databricks Zerobus Java SDK.

## Tech Stack

- **Language**: Java 17+ (compatible with Ignition 8.1+)
- **Platform**: Ignition Gateway module (Gateway scope)
- **SDKs**:
  - [Ignition SDK](https://github.com/inductiveautomation/ignition-sdk-examples) - Module framework, UI, tag APIs
  - [Databricks Zerobus SDK for Java](https://github.com/databricks/zerobus-sdk-java) v0.1.0 - Zerobus Ingest client
- **Build**: Gradle 8.x with Protobuf plugin
- **Repositories**:
  - [Inductive Automation Nexus](https://nexus.inductiveautomation.com/repository/inductiveautomation-releases) - Ignition SDK artifacts
  - Maven Central - Zerobus SDK and dependencies

## Project Layout (Proposed)

- `module/`
  - `src/main/java/com/example/ignition/zerobus/`
    - `ZerobusGatewayHook.java` – module lifecycle.
    - `ZerobusClientManager.java` – wraps Zerobus Java SDK.
    - `TagSubscriptionService.java` – subscribes to Ignition tags.
    - `ConfigModel.java` – POJO for settings.
    - `ConfigPanel.java` – Gateway config UI.
  - `src/main/resources/`
    - `module.xml`
    - `simplemodule.properties`
- `docs/`
  - `ARCHITECT.md`
  - `DEVELOPER.md`
  - `TESTER.md`

## Implementation Plan

### 1. Bootstrap Ignition Module

- Clone Ignition SDK example repo and create a new Gateway-scope module project.
- Implement `ZerobusGatewayHook` with:
  - `startup()` and `shutdown()` methods.
  - Registration of config panel.
- Build `.modl` and verify:
  - Module installs in a dev Ignition Gateway.
  - Basic log message on startup/shutdown.

### 2. Integrate Zerobus Java SDK

**Gradle Dependency** (already configured):
```gradle
implementation 'com.databricks:zerobus-sdk-java:0.1.0'
```

**Implement `ZerobusClientManager`**:

Key Zerobus SDK classes to use:
- `ZerobusSdk` - Main SDK entry point
- `ZerobusStream<RecordType>` - Active ingestion stream
- `TableProperties<RecordType>` - Target table configuration
- `StreamConfigurationOptions` - Stream behavior settings

```java
import com.databricks.zerobus.ZerobusSdk;
import com.databricks.zerobus.ZerobusStream;
import com.databricks.zerobus.TableProperties;
import com.databricks.zerobus.StreamConfigurationOptions;
import com.example.ignition.zerobus.proto.OTEvent;

public class ZerobusClientManager {
    private ZerobusSdk sdk;
    private ZerobusStream<OTEvent> stream;
    
    // Initialize SDK with endpoints
    public void initialize(String workspaceUrl, String zerobusEndpoint) {
        this.sdk = new ZerobusSdk(zerobusEndpoint, workspaceUrl);
    }
    
    // Create stream with OAuth credentials and table name
    public void createStream(String clientId, String clientSecret, 
                            String tableName) throws Exception {
        TableProperties<OTEvent> tableProps = new TableProperties<>(
            tableName, 
            OTEvent.getDefaultInstance()
        );
        
        StreamConfigurationOptions options = StreamConfigurationOptions.builder()
            .setMaxInflightRecords(50000)  // Backpressure threshold
            .setRecovery(true)             // Auto-recovery on failure
            .setRecoveryRetries(3)         // Max recovery attempts
            .setFlushTimeoutMs(300000)     // 5 minute flush timeout
            .setAckCallback(response -> {
                // Track durability offset
                long offset = response.getDurabilityAckUpToOffset();
                logger.debug("Records acknowledged up to offset: {}", offset);
            })
            .build();
        
        this.stream = sdk.createStream(tableProps, clientId, clientSecret, options)
            .get(); // Wait for stream to be ready
    }
    
    // Ingest single event
    public void ingestEvent(OTEvent event) throws Exception {
        stream.ingestRecord(event).get(); // Returns CompletableFuture
    }
    
    // Graceful shutdown
    public void shutdown() throws Exception {
        if (stream != null) {
            stream.flush();  // Flush pending records
            stream.close();  // Close stream
        }
    }
}
```

**Error Handling**:
- `ZerobusException` - Retriable errors (network, temporary issues)
- `NonRetriableException` - Fatal errors (auth failure, missing table)

### 3. Tag Subscription

- Implement `TagSubscriptionService`:
  - Accepts:
    - List/pattern of tag paths to subscribe.
    - Reference to `ZerobusClientManager`.
  - Subscribes to tags using Ignition Tag APIs.
  - Handles value/quality/timestamp updates.
  - Batches records:
    - By count (e.g. 100–1000) and/or time window (e.g. 1–5 seconds).
  - Calls `sendEvents` on batch.

### 4. Schema & Mapping

**Protobuf Schema** (already defined in `src/main/proto/ot_event.proto`):

The `OTEvent` message includes:
- `event_time` - Timestamp in milliseconds since Unix epoch
- `tag_path` - Full Ignition tag path
- `asset_id`, `asset_path` - Asset hierarchy info
- `value` - Union type (numeric, string, boolean, integer)
- `quality` - Enum (GOOD, BAD, UNCERTAIN, UNKNOWN)
- `source_system` - Gateway identifier
- Optional fields: `site`, `line`, `unit`, `engineering_units`

**Mapping Ignition Tags to OTEvent**:

```java
import com.inductiveautomation.ignition.common.sqltags.model.types.DataQuality;
import com.inductiveautomation.ignition.common.model.values.QualifiedValue;
import com.example.ignition.zerobus.proto.OTEvent;
import com.example.ignition.zerobus.proto.Quality;

public class EventMapper {
    private final String sourceSystem;
    
    public OTEvent mapTagEvent(String tagPath, QualifiedValue qv) {
        OTEvent.Builder builder = OTEvent.newBuilder()
            .setEventTime(qv.getTimestamp().getTime())
            .setTagPath(tagPath)
            .setSourceSystem(sourceSystem)
            .setQuality(mapQuality(qv.getQuality()));
        
        // Extract asset info from tag path
        // Example: "[default]Site1/Line2/Asset3/TagName" -> "Asset3"
        String assetId = extractAssetId(tagPath);
        if (assetId != null) {
            builder.setAssetId(assetId);
            builder.setAssetPath(extractAssetPath(tagPath));
        }
        
        // Map value based on data type
        Object value = qv.getValue();
        if (value instanceof Number) {
            builder.setNumericValue(((Number) value).doubleValue());
        } else if (value instanceof Boolean) {
            builder.setBooleanValue((Boolean) value);
        } else if (value instanceof String) {
            builder.setStringValue((String) value);
        }
        
        // Always include string representation
        builder.setValueString(String.valueOf(value));
        
        return builder.build();
    }
    
    private Quality mapQuality(DataQuality dq) {
        if (dq.isGood()) return Quality.QUALITY_GOOD;
        if (dq.isBad()) return Quality.QUALITY_BAD;
        if (dq.isUncertain()) return Quality.QUALITY_UNCERTAIN;
        return Quality.QUALITY_UNKNOWN;
    }
    
    private String extractAssetId(String tagPath) {
        // Parse tag path convention: [provider]site/line/asset/tag
        // Implementation depends on your naming convention
        return null; // TODO: Implement based on tag structure
    }
}
```

**Protobuf Compilation**:

Gradle automatically compiles `.proto` files using the Protobuf plugin:
```bash
./gradlew generateProto
```

Generated Java classes appear in `build/generated/source/proto/main/java/`.

### 5. Configuration UI

- Implement `ConfigModel` for:
  - Zerobus endpoint / workspace URL.
  - OAuth client ID / secret (or token provider).
  - Target `catalog.schema.table`.
  - Tag selection (folder/pattern or explicit list).
  - Batch size / flush interval.
  - Enable/disable flag.
- Implement `ConfigPanel` in Gateway Web UI:
  - Simple form backing `ConfigModel`.
  - “Test connection” button to:
    - Attempt a small Zerobus write.
    - Report success/failure.

### 6. Logging & Diagnostics

- Standard logging:
  - Module startup/shutdown.
  - Zerobus connection established/lost.
  - Batch send success/failure counts.
- Optional diagnostics endpoint:
  - Number of events sent.
  - Last error, last successful send time.

### 7. Hardening (v1)

- Timeouts and retry configuration (read from settings).
- Graceful shutdown of Zerobus client and tag subscriptions.
- Guardrails on tag count / rate to avoid overloading Ignition.

## Build & Deployment

### Build Commands

**Compile Java code**:
```bash
./gradlew compileJava
```

**Generate protobuf classes**:
```bash
./gradlew generateProto
```

**Run tests**:
```bash
./gradlew test
```

**Build module (.modl file)**:
```bash
./gradlew buildModule
```

Output: `build/modules/zerobus-connector-1.0.0.modl`

### Module Structure

The `.modl` file is a ZIP containing:
```
zerobus-connector-1.0.0.modl
├── module.xml               # Module descriptor
├── lib/
│   ├── zerobus-connector-1.0.0.jar    # Your module code
│   ├── zerobus-sdk-java-0.1.0.jar     # Databricks SDK
│   ├── protobuf-java-3.21.12.jar      # Protobuf runtime
│   └── (other dependencies)
```

### Installation

1. **Upload to Ignition Gateway**:
   - Navigate to: Config → System → Modules
   - Click "Install or Upgrade a Module"
   - Select the `.modl` file
   - Click "Install"

2. **Restart Gateway** when prompted

3. **Verify Installation**:
   - Check module appears in installed modules list
   - Review Gateway logs: Status → Logs → Wrapper Log
   - Look for startup messages from `ZerobusGatewayHook`

### Logging Configuration

The Zerobus SDK uses SLF4J (already provided by Ignition):

```java
private static final Logger logger = LoggerFactory.getLogger(ZerobusClientManager.class);
```

**Adjust log levels** in Gateway Config → System → Logging:
- `com.databricks.zerobus` - DEBUG for SDK details
- `com.example.ignition.zerobus` - INFO for module events

### Delta Table Setup

**Create target table in Databricks**:

```sql
CREATE TABLE IF NOT EXISTS dev_ot.bronze_ignition_events (
  event_time TIMESTAMP,
  tag_path STRING,
  asset_id STRING,
  asset_path STRING,
  numeric_value DOUBLE,
  string_value STRING,
  boolean_value BOOLEAN,
  integer_value BIGINT,
  value_string STRING,
  quality STRING,
  source_system STRING,
  site STRING,
  line STRING,
  unit STRING,
  tag_description STRING,
  engineering_units STRING
)
USING DELTA
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'delta.autoOptimize.optimizeWrite' = 'true'
);
```

**Enable Zerobus Ingest** on the workspace (contact Databricks support if needed).

### OAuth Service Principal

Create OAuth credentials in Databricks:

1. **Account Console** → Settings → Service Principals
2. Create new service principal
3. Generate **OAuth Secret**
4. Grant permissions on target table:
   ```sql
   GRANT MODIFY, SELECT ON TABLE dev_ot.bronze_ignition_events 
   TO SERVICE_PRINCIPAL '<client-id>';
   ```

## References

### Official Documentation

- **Zerobus SDK**: https://github.com/databricks/zerobus-sdk-java
  - API Reference, examples, best practices
  - Version: 0.1.0 (Public Preview)
  
- **Ignition SDK**: 
  - Examples: https://github.com/inductiveautomation/ignition-sdk-examples
  - Nexus Repository: https://nexus.inductiveautomation.com/repository/inductiveautomation-releases
  - SDK Guide: https://docs.inductiveautomation.com/docs/8.1/sdk-documentation
  
- **Databricks Lakeflow Connect**:
  - Zerobus Ingest documentation
  - Unity Catalog permissions guide

### Key Dependencies

| Dependency | Version | Source |
|------------|---------|--------|
| Ignition SDK | 8.3.0 | Inductive Automation Nexus |
| Zerobus SDK Java | 0.1.0 | Maven Central |
| Protobuf Java | 3.21.12 | Maven Central |
| SLF4J API | 1.7.36 | Provided by Ignition |

### Module Architecture

```
Ignition Gateway
├── Tag Subscription Service
│   └── Monitors selected tags
│       └── Emits TagChangeEvent
├── Event Mapper
│   └── TagChangeEvent → OTEvent (protobuf)
├── Zerobus Client Manager
│   ├── ZerobusSdk instance
│   ├── ZerobusStream<OTEvent>
│   └── Async ingestion via CompletableFuture
└── Configuration UI
    └── Gateway web interface panel
```

## Developer Checklist

- [ ] **Local dev env**: JDK 17+, Gradle 8.x
- [ ] **Clone repos**: 
  - [ ] Ignition SDK examples for reference
  - [ ] Zerobus SDK Java for API understanding
- [ ] **Dev Ignition Gateway**: 
  - [ ] Docker container running (see TESTING_SETUP.md)
  - [ ] Generic Simulator configured with demo tags
- [ ] **Databricks workspace**:
  - [ ] Zerobus Ingest enabled
  - [ ] Test Delta table created
  - [ ] OAuth credentials generated
  - [ ] Service principal has write permissions
- [ ] **Build & Test**:
  - [ ] Protobuf compiles without errors
  - [ ] Module builds successfully (.modl created)
  - [ ] Unit tests pass
  - [ ] Module installs in dev gateway
  - [ ] Connection test succeeds
- [ ] **End-to-end validation**:
  - [ ] Configure module with test credentials
  - [ ] Subscribe to simulator tags
  - [ ] Generate tag value changes
  - [ ] Verify data appears in Delta table
  - [ ] Check timestamps, values, quality flags match

