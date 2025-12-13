# lakeflow-ignition-zerobus-connector

Ignition Gateway module that streams tag-change events to Databricks Delta via Zerobus (gRPC/protobuf).

## Directory structure (cleaned)

```
module/                         # Ignition module source + Gradle build
releases/
  zerobus-connector-1.0.0.modl  # prebuilt module artifact
scripts/
  configure_gateway.py          # interactive config push (prompts for secret)
onboarding/
  databricks/
    01_create_tables.py         # create Bronze table + Silver scaffolding
  ignition/
    8.1.50/
      config/zerobus_config_direct_explicit.json.example
      gateway_scripts/tag_change_forwarder_http.py   # optional fallback mode
      README.md
    8.3.2/
      config/zerobus_config_direct_explicit.json.example
      config/zerobus_config_event_streams.json.example
      README.md
```

## Onboarding (happy path)

### 1) Databricks: create the Bronze table

- Import + run `onboarding/databricks/01_create_tables.py` in Databricks.
- This creates **Bronze**: `ot_events_bronze` (schema matches `module/src/main/proto/ot_event.proto`).

### 2) Install the module (.modl)

Use the prebuilt artifact:
- `releases/zerobus-connector-1.0.0.modl`

If you need to rebuild, see **Build the module** below.

### 3) Install/upgrade in Ignition

- Gateway UI → Config → Modules → Install/Upgrade → upload the `.modl`.

### 4) Configure + start streaming (direct subscription mode)

**No Designer required.** This mode is configured entirely via `configure_gateway.py` + JSON.

```bash
python3 scripts/configure_gateway.py \
  --gateway-url http://localhost:8099 \
  --config onboarding/ignition/8.1.50/config/zerobus_config_direct_explicit.json.example
```

Verify:

```bash
curl -sS http://localhost:8099/system/zerobus/diagnostics | head -n 120
```

## Direct subscription vs Tag Change Script vs Event Streams (when to use which)

You have three supported ways to get tag events into the module:

### Option A — **Direct subscription (recommended)**

**What it is**
- The module subscribes to tags via the Ignition Gateway TagManager.
- No Gateway scripts, no Event Streams, and no HTTP hop between script→module.

**Use this when**
- You want the simplest, most reliable setup.
- You want one place to manage tag selection (module config).
- You don’t need per-project scripting/transforms.

**Designer required?** No.

**Example**
- Configure explicit tag paths (direct mode):

```bash
python3 scripts/configure_gateway.py \
  --gateway-url http://localhost:8099 \
  --config onboarding/ignition/8.1.50/config/zerobus_config_direct_explicit.json.example
```

### Option B — **Gateway Tag Change Script → HTTP ingest (fallback/advanced)**

**What it is**
- Ignition runs a Tag Change script; the script POSTs events to:
  - `POST /system/zerobus/ingest/batch`

**Use this when**
- You want to attach **custom logic** at the source (filtering, enrichment, mapping).
- You want **project-scoped control** (different scripts per project).
- You can’t (or don’t want to) manage tag lists in module config.

**Designer required?** No (this is a Gateway Event Script).

**Example**
- Use the script template:
  - `onboarding/ignition/8.1.50/gateway_scripts/tag_change_forwarder_http.py`
- Paste it into a Gateway Tag Change Script (Designer → Project → Gateway Events → Tag Change).

### Option C — **Event Streams → HTTP ingest (Ignition 8.3+)**

**What it is**
- Ignition Event Streams (Designer) POSTs events to the module’s ingest endpoint.

**Use this when**
- You want Designer-managed pipelines with transforms/filters per project.

**Designer required?** Yes (Event Streams are configured in Designer).

**Example**

1) Configure the module (Event Streams config):

```bash
python3 scripts/configure_gateway.py \
  --gateway-url http://localhost:8099 \
  --config onboarding/ignition/8.3.2/config/zerobus_config_event_streams.json.example
```

2) Configure Event Streams to send to one of:
- **Batch (recommended)**: `POST http://<gateway-host>:<port>/system/zerobus/ingest/batch` (JSON array)
- **Single event**: `POST http://<gateway-host>:<port>/system/zerobus/ingest` (single JSON object)

### Important: don’t double-ingest

Run **only one** of:
- Direct subscription
- Tag Change Script
- Event Streams

If you enable more than one for the same tags, you’ll ingest duplicates.

## Bronze → Silver: what to do after ingestion

Typical Silver steps once Bronze is flowing:
- **mapping**: a mapping table from `tag_path` → (`asset_id`, `signal_name`, `unit`, `scale`, `offset`)
- **normalization**: unify `numeric/string/boolean` into a consistent long-form telemetry view/table
- **quality + dedupe**: filter bad quality, dedupe by (`source_system`, `tag_path`, `event_time`, `event_id`)
- **windowed aggregates**: 1m/5m rollups per asset/signal
- **state changes**: derive transitions (run/stop/fault) from telemetry

The notebook includes minimal Silver scaffolding you can extend.

## Build the module (optional)

Builds a single `.modl` intended to work on Ignition **8.1.x** and **8.3.x**.

### Requirements
- **JDK 17** available locally (Gradle runs on it)
- An Ignition install directory to compile against:
  - Ignition 8.1 example: `/usr/local/ignition8.1`
  - Ignition 8.3 example: `/usr/local/ignition`

### Build command (recommended: build against 8.1.50)

```bash
cd module
JAVA_HOME=/opt/homebrew/opt/openjdk@17 PATH=/opt/homebrew/opt/openjdk@17/bin:$PATH \
  ./gradlew buildModule \
    -PignitionHome=/usr/local/ignition8.1 \
    -PbuildForIgnitionVersion=8.1.50 \
    -PminIgnitionVersion=8.1.0
```

Output:
- `module/build/modules/zerobus-connector-1.0.0.modl`

### Compile-check against Ignition 8.3 (optional)

```bash
cd module
JAVA_HOME=/opt/homebrew/opt/openjdk@17 PATH=/opt/homebrew/opt/openjdk@17/bin:$PATH \
  ./gradlew compileJava -PignitionHome=/usr/local/ignition -PbuildForIgnitionVersion=8.3.2
```

## Code structure & data flow (high level)

### Key classes
- **`module/src/main/java/com/example/ignition/zerobus/ZerobusGatewayHook.java`**: module lifecycle; loads config, starts/stops services, registers HTTP endpoints under `/system/zerobus/*`.
- **`module/src/main/java/com/example/ignition/zerobus/TagSubscriptionService.java`**: event processing:
  - **Direct mode**: subscribes to configured tag paths via Gateway TagManager and receives `TagChangeEvent`s.
  - **HTTP ingest mode**: accepts events via `/ingest` and `/ingest/batch`.
  - Queues events, applies rate limiting, flushes batches.
- **`module/src/main/java/com/example/ignition/zerobus/ZerobusClientManager.java`**: Zerobus SDK client; converts `TagEvent` → protobuf (`OTEvent`) and streams to Databricks; tracks diagnostics.
- **`module/src/main/proto/ot_event.proto`**: protobuf schema; Bronze table columns/types must match this contract.

### End-to-end flow

**Direct subscription mode**
1. Ignition TagManager emits tag change → `TagSubscriptionService` listener
2. `TagSubscriptionService` converts to `TagEvent` and queues
3. Flush thread builds a batch and calls `ZerobusClientManager.sendEvents(...)`
4. `ZerobusClientManager` converts to protobuf and streams over Zerobus (gRPC) to Databricks Delta

**HTTP ingest mode (Tag Change Script or Event Streams)**
1. External producer POSTs JSON to `/system/zerobus/ingest` or `/system/zerobus/ingest/batch`
2. `TagSubscriptionService` converts payload(s) to `TagEvent`, queues, batches, and streams as above


