## Ignition Zerobus Connector

**Version**: `1.0.0`  
**Purpose**: Stream Ignition tag-change events to Databricks Delta tables via Zerobus (gRPC + protobuf).  
**Ignition compatibility**: 8.1.x and 8.3.x (requires different `.modl` artifacts due to `module.xml` compatibility checks).  
**Ingestion modes**:
- **Direct subscriptions (recommended)**: module subscribes to tags via the Gateway TagManager.
- **Gateway Tag Change Script → HTTP ingest**: script posts JSON to module endpoints.
- **Event Streams → HTTP ingest (8.3+)**: Designer pipeline posts to module endpoints.

## Table of contents

- [Choose your setup path](#choose-your-setup-path)
- [Architecture](#architecture)
- [Repository layout](#repository-layout)
- [Release artifacts (two `.modl` files)](#release-artifacts-two-modl-files)
- [Quick start](#quick-start)
- [Configuration](#configuration)
- [Ingestion modes (when to use which)](#ingestion-modes-when-to-use-which)
- [API endpoints](#api-endpoints)
- [Monitoring & troubleshooting](#monitoring--troubleshooting)
- [Build the module (optional)](#build-the-module-optional)
- [Code flow & structure](#code-flow--structure)

## Choose your setup path

| Your Ignition version | Recommended path | Optional paths |
|---|---|---|
| **8.1.50** (port `8099` in our local setup) | **Direct subscriptions** | Gateway Tag Change Script |
| **8.3.2** (port `8088` in our local setup) | **Direct subscriptions** | Event Streams, Gateway Tag Change Script |

Versioned onboarding guides:
- `onboarding/ignition/8.1.50/README.md`
- `onboarding/ignition/8.3.2/README.md`

## Architecture

### Common data path (all modes)

```
Ignition tags  →  Zerobus Connector module  →  Zerobus (gRPC/protobuf)  →  Databricks Delta (Bronze)
                   (batching + rate limit)
```

### Trigger mechanisms (what changes by mode)

**Direct subscriptions (recommended)**

```
Tags → Gateway TagManager subscriptions → module queue/batcher → Zerobus → Delta
```

**Gateway Tag Change Script → HTTP ingest**

```
Tags → Gateway Tag Change Script → POST /system/zerobus/ingest/batch → module → Zerobus → Delta
```

**Event Streams (Ignition 8.3+) → HTTP ingest**

```
Tags → Event Streams (Designer) → POST /system/zerobus/ingest/batch → module → Zerobus → Delta
```

### Gateway → Zerobus → Databricks: what’s the transport?

There are **two hops**:

#### 1) Ignition Gateway → Zerobus Connector module

This hop is either **in-process** (no network) or **HTTP/JSON**, depending on ingestion mode:

- **Direct subscriptions (recommended)**: the module subscribes to tags via the Gateway TagManager and receives `TagChangeEvent`s as **in-JVM callbacks** (no HTTP, no gRPC).
- **Gateway Tag Change Script**: a Gateway script **POSTs JSON** to:
  - `POST /system/zerobus/ingest` (single event)
  - `POST /system/zerobus/ingest/batch` (array of events)
- **Event Streams (Ignition 8.3+)**: Event Streams **POSTs JSON** to the same ingest endpoints.

#### 2) Zerobus Connector module → Databricks

This hop is always **Zerobus ingest over gRPC + protobuf**:

- The module converts tag events to protobuf (`module/src/main/proto/ot_event.proto`) and streams over **gRPC** to the Databricks Zerobus endpoint.
- Authentication uses **OAuth2 client credentials** (service principal).

## Repository layout

```
module/                              # Ignition module source + Gradle build
releases/
  zerobus-connector-1.0.0.modl        # for Ignition 8.1.x
  zerobus-connector-1.0.0-ignition-8.3.modl  # for Ignition 8.3.x
scripts/
  configure_gateway.py                # interactive config push (prompts for secret)
onboarding/
  databricks/
    01_create_tables.py               # creates Bronze table + minimal scaffolding
  ignition/
    8.1.50/
      config/zerobus_config_direct_explicit.json.example
      gateway_scripts/tag_change_forwarder_http.py
      README.md
    8.3.2/
      config/zerobus_config_direct_explicit.json.example
      config/zerobus_config_event_streams.json.example
      README.md
```

## Release artifacts (two `.modl` files)

There are **two** prebuilt module packages under `releases/`:

- **`releases/zerobus-connector-1.0.0.modl`**:
  - **Install on**: Ignition **8.1.x** (and 8.2.x if you run it)
  - **Why**: the packaged `module.xml` sets `<requiredIgnitionVersion>` to `8.1.0`

- **`releases/zerobus-connector-1.0.0-ignition-8.3.modl`**:
  - **Install on**: Ignition **8.3.x**
  - **Why**: the packaged `module.xml` sets `<requiredIgnitionVersion>` to `8.3.0`

### What’s different between them?

Ignition enforces compatibility based on `module.xml` during install. Because 8.3 refuses modules whose `requiredIgnitionVersion` is below 8.3, we ship two `.modl` artifacts.

The **runtime behavior and code are the same**; the important differences are:

- **`module.xml` gate**: different `<requiredIgnitionVersion>` value, produced by the Gradle `-PminIgnitionVersion=...` build flag.
- **Servlet API at runtime**:
  - Ignition 8.1 uses **`javax.servlet`**
  - Ignition 8.3 uses **`jakarta.servlet`**
  - The module includes both servlet implementations and selects the right one at runtime via `module/src/main/java/com/example/ignition/zerobus/web/ZerobusConfigServlet.java`.

## Quick start

### 1) Databricks: create the Bronze table

- Import + run `onboarding/databricks/01_create_tables.py` in Databricks.
- The Bronze schema matches `module/src/main/proto/ot_event.proto`.

### 2) Install the module (.modl)

- **Ignition 8.1.x**: install `releases/zerobus-connector-1.0.0.modl`
- **Ignition 8.3.x**: install `releases/zerobus-connector-1.0.0-ignition-8.3.modl`

Gateway UI → Config → Modules → Install/Upgrade → upload the `.modl`.

### 3) Configure (no Designer required)

Use `scripts/configure_gateway.py` (it prompts for `oauthClientSecret` securely).

**Ignition 8.1.50 example (gateway on `8099`)**

```bash
python3 scripts/configure_gateway.py \
  --gateway-url http://localhost:8099 \
  --config onboarding/ignition/8.1.50/config/zerobus_config_direct_explicit.json.example
```

**Ignition 8.3.2 example (gateway on `8088`)**

```bash
python3 scripts/configure_gateway.py \
  --gateway-url http://localhost:8088 \
  --config onboarding/ignition/8.3.2/config/zerobus_config_direct_explicit.json.example
```

### 4) Verify

```bash
curl -sS http://localhost:8099/system/zerobus/diagnostics | egrep 'Module Enabled|Initialized|Connected|Total Events Received|Total Events Sent|Direct Subscriptions|Last Flush'
```

## Configuration

Config files are templates (`*.json.example`) and should not hardcode secrets. The configure script asks for missing values interactively and posts to:
- `POST /system/zerobus/config`

Key fields:
- **Databricks**: `workspaceUrl`, `zerobusEndpoint`, `oauthClientId`, `oauthClientSecret`, `targetTable`
- **Source identity**: `sourceSystemId` (gateway/site identifier; shows up in Bronze)
- **Tag selection**:
  - `tagSelectionMode: "explicit"`
  - `explicitTagPaths: ["[provider]Folder/Tag", ...]`
- **Batching**: `batchSize`, `batchFlushIntervalMs`, `maxQueueSize`, `maxEventsPerSecond`

## Ingestion modes (when to use which)

### Option A — Direct subscriptions (recommended)

- **What**: module subscribes via Gateway TagManager and receives tag change events directly.
- **Where configured**: module config (`tagSelectionMode`, `explicitTagPaths`).
- **Designer required**: no.
- **Use when**: you want the simplest, lowest-overhead, easiest-to-operate setup.

### Option B — Gateway Tag Change Script → HTTP ingest

- **What**: a Gateway Tag Change Script posts events to the module.
- **Where configured**: Ignition scripting + module enabled.
- **Designer required**: no (Gateway event scripts are configured in the Gateway scope).
- **Use when**: you need custom logic at source (filter/enrich/mapping) or want script-driven control.
- **Script template**: `onboarding/ignition/8.1.50/gateway_scripts/tag_change_forwarder_http.py`

### Option C — Event Streams (Ignition 8.3+) → HTTP ingest

- **What**: Event Streams posts to the module ingest endpoints.
- **Where configured**: Designer (Event Streams) + module enabled.
- **Designer required**: yes.
- **Use when**: you want Designer-managed pipelines with transformations/filters per project.
- **Config template**: `onboarding/ignition/8.3.2/config/zerobus_config_event_streams.json.example`

### Important: don’t double-ingest

Run **only one** of: direct subscriptions, tag-change script, or event streams for the same tags (otherwise you’ll create duplicates).

## API endpoints

All endpoints are under `/system/zerobus`:
- `GET /health`
- `GET /diagnostics`
- `POST /config`
- `POST /test-connection`
- `POST /ingest` (single JSON event)
- `POST /ingest/batch` (JSON array of events)

## Monitoring & troubleshooting

### First place to look

`GET /system/zerobus/diagnostics` shows:
- Zerobus connected/initialized state
- total events received/sent
- queue size and flush cadence
- subscription count

### Common issues

- **Module won’t install on 8.3**: you likely uploaded the 8.1 artifact. Use `releases/zerobus-connector-1.0.0-ignition-8.3.modl`.
- **Events not increasing**:
  - verify the tag paths exist and are changing
  - check `Direct Subscriptions: N tags` is non-zero
  - set `debugLogging: true` temporarily (then reconfigure)
- **Sample_Tags show `Error_Configuration` or OPC UA flaps**:
  - if running both gateways locally, avoid OPC UA port collisions and mismatched endpoints
  - example fix: point the 8.3 OPC UA connection at `opc.tcp://localhost:62542` (8.3’s OPC UA server)
- **`Target table must be in format catalog.schema.table`**:
  - ensure there are exactly 3 dot-separated parts and the table name does not contain extra dots

## Build the module (optional)

### Requirements

- **JDK 17** (Gradle/tooling)
- Ignition installs for SDK jars:
  - 8.1: `/usr/local/ignition8.1`
  - 8.3: `/usr/local/ignition`

### Build the 8.1 module artifact

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

### Build the 8.3 module artifact

```bash
cd module
JAVA_HOME=/opt/homebrew/opt/openjdk@17 PATH=/opt/homebrew/opt/openjdk@17/bin:$PATH \
  ./gradlew buildModule \
    -PignitionHome=/usr/local/ignition \
    -PbuildForIgnitionVersion=8.3.2 \
    -PminIgnitionVersion=8.3.0
```

Output:
- `module/build/modules/zerobus-connector-1.0.0-ignition-8.3.modl`

## Code flow & structure

### Key classes

- **`module/src/main/java/com/example/ignition/zerobus/ZerobusGatewayHook.java`**: module lifecycle; loads/saves config; starts/stops services; registers HTTP endpoints under `/system/zerobus/*`.
- **`module/src/main/java/com/example/ignition/zerobus/TagSubscriptionService.java`**: tag event processing:
  - direct mode subscriptions via TagManager
  - HTTP ingest queueing via `/ingest` and `/ingest/batch`
  - batching + rate limiting + flush loop
- **`module/src/main/java/com/example/ignition/zerobus/ZerobusClientManager.java`**: manages Zerobus client; converts events to protobuf and streams to Databricks.
- **Servlet compatibility layer**:
  - `.../web/ZerobusConfigServlet.java` selects `javax` vs `jakarta` servlet implementation at runtime.
  - `.../web/ZerobusServletHandler.java` holds shared request parsing and routing.
- **Schema**: `module/src/main/proto/ot_event.proto`

### End-to-end data flow

**Direct subscriptions**
1) Tag change event → `TagSubscriptionService` listener  
2) Convert to internal `TagEvent` → queue  
3) Flush loop batches → `ZerobusClientManager`  
4) Protobuf (OTEvent) → Zerobus stream → Delta

**HTTP ingest (Tag Change Script / Event Streams)**
1) Producer POSTs JSON → `/system/zerobus/ingest` or `/ingest/batch`  
2) Handler parses + enqueues `TagEvent`s  
3) Batching + streaming as above
