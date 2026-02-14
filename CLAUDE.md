# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

An **Ignition Gateway Module** (.modl) that streams industrial OT/IIoT tag-change events from Inductive Automation's Ignition platform to Databricks Delta tables via Zerobus (gRPC + protobuf). Replaces the need for Kafka infrastructure.

Two Ignition versions are supported with separate build artifacts:
- **8.1.x** - uses `javax.servlet`, Wicket UI, Java 11 bytecode
- **8.3.x** - uses `jakarta.servlet`, React UI, Java 17 bytecode

## Makefile (recommended entry point)

Run `make help` for a full target listing. All commands run from the repo root.

### End-to-end from scratch (7 steps)

Normal bootstrap order: Databricks first (SP + tables + pipeline + app), then build the Ignition module, then start the gateway. Finish with manual steps in the browser and CLI.

```bash
# Steps 1-4 (automated) — run in this order
make bootstrap-83

# Steps 4b-7 (manual, run after bootstrap completes)
make setup-wizard-83    # Step 4b: Accept EULA + create admin in browser
make configure-83       # Step 5:  Push SP credentials to gateway
make simulate-83        # Step 6:  Start synthetic data generation
make links-83           # Step 7:  Print all URLs for easy navigation
```

| Step | Make target | What happens |
|------|-------------|-------------|
| 1 | `db-create-sp` | Create SP at account level, generate OAuth client secret, assign to workspace, write `[agl-demo]` profile to `~/.databrickscfg`, run UC grants |
| 2 | `db-setup-sql` | Create catalog, schema, `raw_tags` table, asset framework tables, UC volume, SP grants |
| | `db-wheel` | Build + upload `agl_analytics` wheel to UC volume |
| | `db-pipeline` | Create/update the SDP ETL pipeline via SDK (Git-backed) |
| | `db-app-deploy` | Deploy the Databricks App from GitHub via SDK |
| 3 | `build-83` | Docker-build the Ignition 8.3 `.modl` with Zerobus module baked in |
| 4 | `up-83` | Start the Ignition gateway container (fresh volume) |
| 4b | `setup-wizard-83` | **Manual**: complete Ignition first-time setup in browser (EULA, admin user, trial) |
| 5 | `configure-83` | Push SP credentials + Zerobus endpoint config to the running gateway |
| 6 | `simulate-83` | Start AGL Fleet Simulator — synthetic BESS/grid/market/CMMS tag events |
| 7 | `links-83` | Print clickable URLs: workspace, catalog, app, pipeline, gateway |

`make bootstrap-83` runs steps 1–4 in order: `db-all` (1 → 2) then `build-83` (3) then `up-83` (4).

### Full reset (clean Databricks + Ignition, then bootstrap)

To wipe everything and redeploy from a clean state (drop catalog, pipeline, app; destroy gateway volume; then run bootstrap again):

```bash
make db-clean clean-83 bootstrap-83
# then manual: make setup-wizard-83 configure-83 simulate-83 links-83
```

- `db-clean`: Drops catalog CASCADE, deletes SDP pipeline and zerobus app. Use same profile as setup (e.g. `DATABRICKS_PROFILE`).
- `clean-83`: Stops gateway and destroys volume (next start needs setup wizard again).

### Individual targets

#### Gateway lifecycle

| Target | Description |
|--------|-------------|
| `build-83` / `build-81` | Docker-build the `.modl` (no local Ignition needed), copy to `releases/` |
| `up-83` / `up-81` | Fresh start: reset volume + start gateway (module baked in) |
| `start-83` / `start-81` | Start gateway (keep existing volume — preserves wizard setup) |
| `stop-83` / `stop-81` | Stop gateway (keep volume) |
| `clean-83` / `clean-81` | Stop gateway + destroy volume (next start needs wizard again) |
| `logs-83` / `logs-81` | Tail gateway container logs |
| `setup-wizard-83` | Open browser to complete Ignition first-time setup wizard |
| `configure-83` / `configure-81` | Push Databricks/Zerobus config (SP credentials) to running gateway |
| `health-83` / `health-81` | Quick Zerobus health check |
| `diag-83` / `diag-81` | Full Zerobus diagnostics (JSON) |
| `restore-83` / `restore-81` | Restore gateway from `.gwbk` backup (skips setup wizard) |

#### Databricks

| Target | Description |
|--------|-------------|
| `db-create-sp` | Create service principal + OAuth secret + workspace assignment + grants + write profile |
| `db-setup-sql` | Create catalog, schema, tables, volume, SP grants (auto-reads `SP_APPLICATION_ID` from profile) |
| `db-wheel` | Build + upload `agl_analytics` wheel to UC volume |
| `db-pipeline` | Create/update SDP pipeline via SDK (Git folder in workspace) |
| `db-app-deploy` | Deploy Databricks App from GitHub via SDK |
| `db-bundle` | Deploy + start app via Asset Bundle (`databricks.yml`) |
| `db-all` | Full Databricks setup: `db-create-sp` -> `db-setup-sql` -> `db-wheel` -> `db-pipeline` -> `db-app-deploy` |

#### Simulator

| Target | Description |
|--------|-------------|
| `simulate-83` / `simulate-81` | Start AGL Fleet Simulator against the gateway (runs until Ctrl+C) |
| `simulate-dry-run` | Generate events without sending (10 ticks) |

Override with: `SIM_SITES=5 SIM_UNITS=4 SIM_INTERVAL=500 make simulate-83`

#### Links

| Target | Description |
|--------|-------------|
| `links-83` | Print all URLs: workspace, catalog explorer, apps, pipelines, gateway health/diagnostics |

### Overridable variables

All have sensible defaults; override at invocation or export in your shell.

| Variable | Default | Used by |
|----------|---------|---------|
| `DATABRICKS_PROFILE` | `daveok` | SDK operations (setup SQL, pipeline, app deploy, wheel upload) |
| `SP_PROFILE_NAME` | `agl-demo` | SP profile in `~/.databrickscfg`; used by `configure-*` (needs M2M creds) |
| `SP_NAME` | `ignition-zerobus-agl` | Service principal display name |
| `CATALOG` | `agl_demo` | Unity Catalog catalog name |
| `SCHEMA` | `ot` | Unity Catalog schema name |
| `WAREHOUSE_ID` | `e65d34bf5b095b0f` | SQL warehouse for statement execution |
| `REPO_PATH` | `/Users/david.okeeffe@databricks.com/...` | Workspace path for pipeline Git folder |
| `PIPELINE_NAME` | `[production] agl-etl` | SDP pipeline display name |
| `ZEROBUS_ENDPOINT` | `7405607216190670.zerobus.eastus2.azuredatabricks.net` | Zerobus gRPC endpoint |
| `PORT_83` / `PORT_81` | `7088` / `8097` | Host port for Ignition gateway |
| `SIM_SITES` | `3` | Number of sites (1-5) |
| `SIM_UNITS` | `2` | BESS units per site (1-8) |
| `SIM_INTERVAL` | `1000` | Tick interval in ms |
| `SIM_TICKS` | `0` | Number of ticks (0 = infinite) |

### Authentication

Three profiles are involved (`~/.databrickscfg`):

- **`daveok`** (`DATABRICKS_PROFILE`) — your personal SSO. Used for SDK operations: creating tables, deploying pipelines, uploading wheels.
- **`agl-demo`** (`SP_PROFILE_NAME`) — service principal OAuth M2M. Used by `configure-*` (pushes `client_id`/`client_secret` to the gateway). Auto-created by `db-create-sp`.
- **`ACCOUNT-*`** — auto-detected. Used by `db-create-sp` to create the SP at the account level. Re-authenticate with: `databricks auth login --host https://accounts.azuredatabricks.net --account-id <id>`.

## Build commands (Gradle, manual)

All Gradle commands run from `module/`. Requires JDK 17 and local Ignition SDK jars. Prefer `make build-83` / `make build-81` which use Docker and need no local install.

```bash
# Build 8.1.x module
cd module && ./gradlew buildModule81

# Build 8.3.x module
cd module && ./gradlew buildModule83

# Run tests (must specify which Ignition SDK to compile against)
cd module && ./gradlew test -PignitionHome=/usr/local/ignition8.1 -PbuildForIgnitionVersion=8.1.50
cd module && ./gradlew test -PignitionHome=/usr/local/ignition -PbuildForIgnitionVersion=8.3.2

# Sign modules (requires signing properties - see build.gradle for env vars)
cd module && ./gradlew signModule81
cd module && ./gradlew signModule83
```

Build outputs land in `module/build-user-8.1/modules/` or `module/build-user-8.3/modules/` and are also copied to `releases/`.

## Architecture

### Dual-version build system

The Gradle build uses conditional source exclusion to produce version-specific artifacts from a single source tree:
- 8.3 builds exclude `ZerobusGatewayHook.java`, `ZerobusSettings.java` (Wicket-based)
- 8.1 builds exclude `ZerobusGatewayHook83.java`, `ZerobusSettings83.java` (React-based)
- Separate build directories (`build-user-8.1/`, `build-user-8.3/`) prevent cross-contamination

### Event pipeline (mapper - buffer - sink)

All code under `module/src/main/java/com/example/ignition/zerobus/`:

1. **Entry points** - events arrive via either:
   - `TagSubscriptionService` - in-JVM tag change callbacks from Ignition TagManager (direct subscriptions mode)
   - HTTP POST to `/system/zerobus/ingest[/batch]` - external JSON producers (Event Streams mode)

2. **Mapper** (`pipeline/OtEventMapper`) - converts internal `TagEvent` to protobuf `OTEvent` (schema: `src/main/proto/ot_event.proto`)

3. **Buffer** (`pipeline/StoreAndForwardBuffer`) - memory or disk-backed (`saf/DiskSpool`) with high/low watermark backpressure. Commits only after successful send (at-least-once semantics).

4. **Sink** (`pipeline/ZerobusEventSink` -> `ZerobusClientManager`) - gRPC/protobuf stream to Databricks Zerobus endpoint

### Servlet compatibility layer

`web/ZerobusServletHandler` holds shared request parsing/routing. The servlet dispatchers are version-specific:
- `web/servlet81/` - `javax.servlet` implementation
- `web/servlet83/` - `jakarta.servlet` implementation

### Configuration

`ConfigModel` is the runtime configuration POJO. Settings are persisted via Ignition's PersistentRecord system (Gateway internal DB), not config files. `ZerobusSettings` (8.1) and `ZerobusSettings83` (8.3) manage the UI.

### Key build properties

- `-PignitionHome=...` or `IGNITION_HOME` - path to local Ignition install (for SDK jars)
- `-PbuildForIgnitionVersion=...` - Ignition version to compile against
- `-PmoduleId=...` - override module ID (changing ID means Ignition treats it as a different module)
- Signing env vars: `MODULE_SIGNER_JAR`, `SIGNING_KEYSTORE`, `SIGNING_STOREPASS`, `SIGNING_ALIAS`, `SIGNING_KEYPASS`

## Repository layout

- `module/` - Ignition module source + Gradle build (the main code)
- `demo/` - Databricks demo application (frontend, backend, simulator, Databricks Apps config)
  - `demo/frontend/` - React 18 + Vite + Tailwind CSS dashboard
  - `demo/backend/` - Express API server with Databricks SQL connector
  - `demo/simulator/` - Ignition tag simulator + Zerobus publisher
  - `demo/app/` - Databricks Apps deployment config (app.yaml, build/start scripts)
- `pipelines/` - Databricks data processing SQL
  - `pipelines/sql/` - Core SQL scripts (Bronze setup, Silver transforms, Gold metrics)
  - `pipelines/sites/` - Per-customer site SQL packs + dashboard/Genie prompts
- `releases/` - canonical signed .modl artifacts
- `examples/` - end-to-end demo simulations (Ignition tag configs + timer scripts for various customer sites)
- `onboarding/` - Databricks/Ignition setup guides
- `docker/` - Dockerfile.build-modl + Ignition Gateway docker-compose files

## Deploy the Databricks App from Git

Prefer Make targets (see Makefile section above):

```bash
make db-app-deploy     # Deploy app from GitHub via SDK
make db-app-start      # Start the app
# or
make db-bundle         # Deploy + start via Asset Bundle (databricks.yml)
```

Manual alternative: `databricks bundle deploy -t production` then `databricks bundle run zerobus_ignition_agl -t production`.

Bundle: `databricks.yml` at repo root. Variables: `catalog`, `schema`, `warehouse_id` (lookup "Serverless Starter Warehouse"). See `demo/app/README.md`.

**Pipeline (AGL ETL):** Not in the bundle. Use `make db-pipeline` or run manually: `onboarding/databricks/deploy_pipeline_sdk.py --repo-path /Repos/<user>@databricks.com/lakeflow-ignition-zerobus-connector`. See `pipelines/sdp/README.md`.

## API endpoints

All under `/system/zerobus`: `GET /health`, `GET /diagnostics`, `POST /config`, `POST /test-connection`, `POST /ingest`, `POST /ingest/batch`

## Current working environment (daveok workspace)

**IMPORTANT** — previous agent sessions misdiagnosed auth failures. The credentials below are verified working (2026-02-13). If you see `Failed to get Zerobus token`, check the workspace URL and endpoint match first — it is almost certainly a config mismatch, not a credential problem.

| Setting | Value |
|---------|-------|
| Workspace URL | `https://adb-7405607216190670.10.azuredatabricks.net` |
| Workspace ID | `7405607216190670` |
| Region | `eastus2` |
| Zerobus Endpoint | `7405607216190670.zerobus.eastus2.azuredatabricks.net` |
| Service Principal ID | `66c066ad-d5a9-496f-8da5-6d7bc2f5d954` |
| SP Display Name | `ignition-zerobus-agl` |
| Target Table | `${var.catalog}.${var.schema}.raw_tags` (e.g. agl_demo.ot.raw_tags) |
| Databricks CLI Profile | `agl-demo` (in `~/.databrickscfg`, OAuth M2M) |
| SQL Warehouse | `e65d34bf5b095b0f` (Serverless Starter Warehouse) |

Credentials are in `.env` (gitignored) and `~/.databrickscfg` under the `[agl-demo]` profile.

### Zerobus endpoint format

The endpoint follows `<workspace-id>.zerobus.<region>.<cloud-domain>`:
- **Azure**: `<workspace-id>.zerobus.<region>.azuredatabricks.net`
- **AWS**: `<workspace-id>.zerobus.<region>.cloud.databricks.com`

Extract the workspace ID from the URL: `adb-7405607216190670` → `7405607216190670`.

### Double-check before configure (stream creation / Error 1521)

When Zerobus shows **Initialized: false, Connected: false** and **Stream creation failed (INTERNAL / 1521)**, verify:

**Quick check:** `curl -s http://localhost:7088/system/zerobus/config` — ensure `targetTable` is `catalog.schema.raw_tags`.

1. **No CLUSTER BY (liquid clustering)** — Zerobus Ingest **does not support** tables with `CLUSTER BY`. Stream creation fails immediately with 1521. Fix: `ALTER TABLE ... CLUSTER BY NONE`. The DDL in `setup_databricks.sql` no longer uses CLUSTER BY. See `module/SCHEMA_ALIGNMENT.md` for the full isolation test results.
2. **Workspace ID match** — `workspaceUrl` and `zerobusEndpoint` must be the **same workspace**.
   - `workspaceUrl` comes from the **[agl-demo]** profile `host` in `~/.databrickscfg` (e.g. `https://adb-7405607216190670.10.azuredatabricks.net`).
   - `zerobusEndpoint` comes from Makefile `ZEROBUS_ENDPOINT` (e.g. `7405607216190670.zerobus.eastus2.azuredatabricks.net`).
   - Extract IDs: URL `adb-7405607216190670` → `7405607216190670`; endpoint first segment → `7405607216190670`. They must match.
   - `make configure-83` now validates this and fails with a clear error if they differ.
3. **Target table** — Must exist and be writable: `agl_demo.ot.raw_tags` (or your `CATALOG.SCHEMA.raw_tags`). After `db-clean`, run `make db-setup-sql` so the table and SP grants exist before configuring the gateway.
4. **Schema match** — The Delta table schema (column names, order, types) must match the OTEvent protobuf exactly for Zerobus to accept the stream; mismatch can cause INTERNAL/1521. See `module/SCHEMA_ALIGNMENT.md`. Timestamps are **microseconds** (BIGINT) in both proto and table; Java mapper sends micros.
5. **SP credentials** — Gateway uses `oauthClientId` / `oauthClientSecret` from the **[agl-demo]** profile. Ensure `client_id` and `client_secret` are set and the SP has UC grants on the table.

### Check SP and secret

- **Make:** `make db-check-sp` — Prints `[agl-demo]` host, client_id, and whether client_secret is set; then verifies the secret by calling the workspace as the SP (`current_user.me()`). Exits 0 only if the profile exists and the OAuth secret works.
- **Manual — profile:** Inspect `~/.databrickscfg`. Under `[agl-demo]` you should have `host`, `client_id`, and `client_secret` (same as the SP’s Application ID and OAuth secret from account Settings → Identity → Service principals).
- **Manual — test secret:** `databricks auth env --profile agl-demo` — Prints env vars for a token; if the secret is wrong or expired, the command fails.
- **Manual — SP in workspace:** In the workspace go to **Settings → Identity and access → Service principals** and find the principal whose Application ID matches `client_id` in `[agl-demo]` (e.g. `ignition-zerobus-agl`). Account-level SPs are under the account console **Settings → Identity and access → Service principals**.

### Common pitfalls (save yourself 30 minutes)

1. **"Failed to get Zerobus token"** — Does NOT always mean bad credentials. Check that `workspaceUrl` and `zerobusEndpoint` point to the **same workspace ID**. A previous config pointed endpoint to workspace `984752964297111` (az-field-east) while the SP only had access to `7405607216190670` (daveok).

2. **SP needs UC grants** — The service principal needs `USE CATALOG`, `USE SCHEMA`, `MODIFY`, and `SELECT` on `raw_tags`. Run the GRANTs in `examples/agl_fleet/setup_databricks.sql`.

3. **Schema is `ot`, not `bronze`** — Target table is `${var.catalog}.${var.schema}.raw_tags` (default ot). The `bronze` schema does not exist.

4. **Docker build requires `IGNITION_HOME=/usr/local/bin/ignition`** — The default in the Dockerfile is `/usr/local/ignition` which doesn't exist in the 8.3 image. Always pass `--build-arg IGNITION_HOME=/usr/local/bin/ignition`.

5. **Docker build version must match image** — The `8.3` tag currently resolves to `8.3.3`. Use `--build-arg BUILD_FOR_IGNITION_VERSION=8.3.3`, not `8.3.2`.

6. **Ignition caches modules in its volume** — After rebuilding a `.modl`, you must `docker compose down -v` (remove the volume) then `up -d` and redo the setup wizard. A simple `restart` will NOT load the new module.

7. **Setup wizard after volume reset** — Ignition 8.3 does not support auto-commissioning. After `down -v`, open http://localhost:7088 in a browser and complete: EULA → admin user (`admin`/`password`) → Standard Trial → Finish.

## Configuring the Ignition Gateway

### Automated (recommended)

```bash
make configure-83      # Push Databricks config to 8.3 gateway
make configure-81      # Push Databricks config to 8.1 gateway
```

`make configure-*` (and any script using `setup_gateway()`) **forces the simplistic happy path**: it sets `authMode` to `service_principal` and `accountId` to empty, so the module uses the Zerobus SDK’s built-in workspace-level M2M OAuth. Any previously saved account-level OIDC or bearer-token settings are cleared.

Manual alternative:

```bash
cd examples/agl_fleet
uv run --extra setup agl-sim --setup-only --profile agl-demo \
    --zerobus-endpoint 7405607216190670.zerobus.eastus2.azuredatabricks.net \
    --gateway http://localhost:7088
```

### Full config push (connection + demo batching in one request)

**IMPORTANT**: `POST /system/zerobus/config` REPLACES the entire config — it does NOT merge. If you POST batching settings without connection fields, you will blank out the workspace/endpoint/credentials. Always send the complete config in a single request, or use the `setup_gateway()` Python function which does GET-then-merge correctly.

```bash
curl -s -X POST http://localhost:7088/system/zerobus/config \
  -H 'Content-Type: application/json' \
  -d '{
    "enabled": true,
    "workspaceUrl": "https://adb-7405607216190670.10.azuredatabricks.net",
    "zerobusEndpoint": "7405607216190670.zerobus.eastus2.azuredatabricks.net",
    "oauthClientId": "66c066ad-d5a9-496f-8da5-6d7bc2f5d954",
    "oauthClientSecret": "<your-oauth-client-secret>",
    "targetTable": "${var.catalog}.${var.schema}.raw_tags",
    "enableDirectSubscriptions": false,
    "batchSize": 1000,
    "batchFlushIntervalMs": 500,
    "maxQueueSize": 50000,
    "maxEventsPerSecond": 5000,
    "enableStoreAndForward": false,
    "retryBackoffMs": 500,
    "connectionTimeoutMs": 10000,
    "requestTimeoutMs": 30000
  }'
```

### Verifying the connection

After pushing config, validate auth **from inside Ignition** (same code path as stream creation):

- **Test Connection button** — In the Zerobus config page (Config → Zerobus), click **Test Connection**. A successful test means the SP and config are valid for Zerobus from inside the gateway.
- **CLI:** `make test-connection-83` (or `test-connection-81`) — POSTs to `/system/zerobus/test-connection`, parses the JSON response (`success`, `message`), and exits 0 only when the test succeeds.

Quick health and diagnostics:

```bash
make health-83         # Quick health check
make diag-83           # Full diagnostics (JSON)

# Manual alternative:
curl -s http://localhost:7088/system/zerobus/health
curl -s http://localhost:7088/system/zerobus/diagnostics
```

## Docker-based build (corrected for 8.3)

Prefer `make build-83` which wraps the Docker build with correct args and copies to `releases/`.

Manual alternative:

```bash
DOCKER_BUILDKIT=1 docker build --no-cache -f docker/Dockerfile.build-modl \
  --target out \
  --build-arg IGNITION_TAG=8.3 \
  --build-arg IGNITION_HOME=/usr/local/bin/ignition \
  --build-arg BUILD_FOR_IGNITION_VERSION=8.3.3 \
  --build-arg MIN_IGNITION_VERSION=8.3.0 \
  --output type=local,dest=./docker-out/8.3 .

# Copy to releases
cp docker-out/8.3/*.modl releases/

# Deploy (requires volume reset to pick up new module)
cd docker/ignition-gateway
docker compose -f docker-compose.83.yml down -v
docker compose -f docker-compose.83.yml up -d
# Then: make setup-wizard-83, then make configure-83
```
