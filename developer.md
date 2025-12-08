# DEVELOPER.md

## Role

Act as the **implementation engineer**. Use this document to plan and track the Ignition module and Zerobus integration work.

## Goal

Build an Ignition Gateway module that streams selected tags/events into Databricks Delta tables via Zerobus Ingest using the Databricks Zerobus Java SDK.

## Tech Stack

- Language: Java (JDK compatible with Ignition SDK).
- Platform: Ignition Gateway module (Gateway scope).
- SDKs:
  - Ignition SDK (module skeleton, UI, tag APIs).
  - Databricks `zerobus-sdk-java` for Zerobus Ingest client.
- Build: Gradle or Maven (match Ignition SDK examples).

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

- Add `zerobus-sdk-java` dependency (Maven coordinates) to build.
- Implement `ZerobusClientManager`:
  - Reads config (endpoint, OAuth credentials, UC table, protobuf schema).
  - Initializes Zerobus client on startup.
  - Provides `sendEvents(List<EventRecord>)` for ingestion.
  - Handles retries, backoff, and logging via SDK.

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

- Define a protobuf message schema for OT events (matching UC target table).
- Implement mapper:
  - Ignition tag event → Protobuf message:
    - `event_time` ← Ignition timestamp.
    - `tag_path` ← Ignition tag path.
    - `value` ← tag value (handle numeric/string/boolean).
    - `quality` ← Ignition quality → string/int enum.
    - Optional: asset/site fields (from naming convention or tag metadata).
- Ensure type conversions and null handling are robust.

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

## Developer Checklist

- [ ] Local dev env: JDK, Ignition SDK, Zerobus Java SDK.
- [ ] Dev Ignition Gateway running with demo tags.
- [ ] Test Databricks workspace + Zerobus test table + credentials.
- [ ] End-to-end: value change in Ignition appears in Delta table.

