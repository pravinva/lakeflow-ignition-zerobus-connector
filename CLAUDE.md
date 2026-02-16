# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

An **Ignition Gateway Module** (.modl) that streams industrial OT/IIoT tag-change events from Inductive Automation's Ignition platform to Databricks Delta tables via Zerobus (gRPC + protobuf). Replaces the need for Kafka infrastructure.

Two Ignition versions are supported with separate build artifacts:
- **8.1.x** - uses `javax.servlet`, Wicket UI, Java 11 bytecode
- **8.3.x** - uses `jakarta.servlet`, React UI, Java 17 bytecode

## Partner sensitivity (public repo)

This repository is **public**. Databricks and AVEVA are partners. Any AVEVA-related content must use a **soft touch**:
- **Do not commit**: Internal competitive analysis, gap analyses, or partner-sensitive documents
- **Public-facing**: Do not name AVEVA. Use generic terms: "other platforms", "traditional historians", "legacy OT systems"
- **Tone**: Factual, capability-focused. Lead with what we offer; avoid criticising any specific vendor

## Makefile (recommended entry point)

Run `make help` for a full target listing. All commands run from the repo root.

### End-to-end from scratch

```bash
# Steps 1-4 (automated)
make bootstrap-83

# Steps 4b-8 (manual, run after bootstrap completes)
make setup-wizard-83    # Step 4b: Accept EULA + create admin in browser
make configure-83       # Step 5:  Push SP credentials to gateway
make simulate-83        # Step 6:  Start synthetic data generation
make links-83           # Step 7:  Print all URLs for easy navigation
make db-train-health-model  # Step 8 (optional): Train health model, register in UC
```

| Step | Make target | What happens |
|------|-------------|-------------|
| 1 | `db-create-sp` | Create SP at account level, generate OAuth secret, assign to workspace, write `[agl-demo]` profile to `~/.databrickscfg`, run UC grants |
| 2 | `db-setup-sql` | Create catalog, schema, `raw_tags` table, asset framework tables, UC volume, SP grants |
| | `db-wheel` | Build + upload `agl_analytics` wheel to UC volume |
| | `db-pipeline` | Create/update the SDP ETL pipeline via SDK (Git-backed) |
| | `db-app-deploy` | Deploy the Databricks App from GitHub via SDK |
| 3 | `build-83` | Docker-build the Ignition 8.3 `.modl` with Zerobus module baked in |
| 4 | `up-83` | Start the Ignition gateway container (fresh volume) |
| 4b | `setup-wizard-83` | **Manual**: complete Ignition first-time setup in browser (EULA, admin user, trial) |
| 5 | `configure-83` | Push SP credentials + Zerobus endpoint config to the running gateway |
| 6 | `simulate-83` | Start AGL Fleet Simulator - synthetic BESS/grid/market/CMMS tag events |
| 7 | `links-83` | Print clickable URLs: workspace, catalog, app, pipeline, gateway |
| 8 | `db-train-health-model` | (optional) Create/run training job, register health model in UC |

### Full reset

```bash
make db-clean clean-83 bootstrap-83
# then: make setup-wizard-83 configure-83 simulate-83 links-83
```

### Key individual targets

| Category | Targets |
|----------|---------|
| Build | `build-83`, `build-81` |
| Gateway | `up-83`, `start-83`, `stop-83`, `clean-83`, `logs-83` |
| Configure | `configure-83`, `health-83`, `diag-83`, `test-connection-83` |
| Databricks | `db-create-sp`, `db-setup-sql`, `db-wheel`, `db-pipeline`, `db-app-deploy`, `db-all` |
| Simulator | `simulate-83`, `simulate-dry-run` |

Override with env vars: `SIM_SITES=5 SIM_UNITS=4 SIM_INTERVAL=500 make simulate-83`

### Overridable variables

Set in `.env` (copy from `.env.example`) and source before make: `set -a && source .env && set +a`

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABRICKS_WAREHOUSE_ID` | `e4082fdb7ea19a15` | SQL warehouse ID |
| `WORKSPACE_ID` | `7405616025546271` | Used to derive `ZEROBUS_ENDPOINT` |
| `DATABRICKS_REGION` | `australiaeast` | Region for Zerobus endpoint |
| `DATABRICKS_CONFIG_PROFILE` | `daveok` | Your personal SSO profile |
| `SP_PROFILE_NAME` | `agl-demo` | SP profile (auto-created by `db-create-sp`) |
| `CATALOG` | `agl_demo` | Unity Catalog catalog |
| `SCHEMA` | `ot` | Unity Catalog schema |
| `REPO_PATH` | `/Users/david.okeeffe@databricks.com/...` | Workspace path for pipeline Git folder |

## Testing

### Java tests (Ignition module)

Requires JDK 17 and local Ignition SDK jars. Run from `module/`:

```bash
# 8.1 SDK
cd module && ./gradlew test -PignitionHome=/usr/local/ignition8.1 -PbuildForIgnitionVersion=8.1.50

# 8.3 SDK
cd module && ./gradlew test -PignitionHome=/usr/local/ignition -PbuildForIgnitionVersion=8.3.2

# Single test class
cd module && ./gradlew test --tests "*.SwingDoorCompressorTest" -PignitionHome=/usr/local/ignition -PbuildForIgnitionVersion=8.3.2
```

### Python tests (SDP pipeline)

```bash
# Install dev dependencies and run tests
cd pipelines/sdp && uv sync --extra dev && uv run pytest

# Single test file
cd pipelines/sdp && uv run pytest tests/test_health.py -v

# With coverage
cd pipelines/sdp && uv run pytest --cov=src --cov-report=term-missing

# Lint with ruff
cd pipelines/sdp && uv run ruff check src/ tests/
```

## Build commands (Gradle, manual)

Prefer `make build-83` / `make build-81` which use Docker and need no local install.

```bash
cd module && ./gradlew buildModule81   # Build 8.1.x
cd module && ./gradlew buildModule83   # Build 8.3.x
cd module && ./gradlew signModule83    # Sign (requires signing env vars)
```

Build outputs: `module/build-user-8.1/modules/` or `module/build-user-8.3/modules/` (also copied to `releases/`).

## Architecture

### Dual-version build system

Gradle uses conditional source exclusion for version-specific artifacts:
- 8.3 builds exclude `ZerobusGatewayHook.java`, `ZerobusSettings.java` (Wicket-based)
- 8.1 builds exclude `ZerobusGatewayHook83.java`, `ZerobusSettings83.java` (React-based)
- Separate build directories (`build-user-8.1/`, `build-user-8.3/`) prevent cross-contamination

### Event pipeline (compression - mapper - buffer - sink)

Code under `module/src/main/java/com/example/ignition/zerobus/`:

1. **Entry points**:
   - `TagSubscriptionService` - in-JVM tag change callbacks (direct subscriptions mode)
   - HTTP POST to `/system/zerobus/ingest[/batch]` - external JSON producers (Event Streams mode)

2. **Compression** (`compression/SwingDoorCompressor`) - Swinging Door Trending (SDT) algorithm reduces data volume by filtering redundant points within a configurable deviation band. Stateful per-tag compressor with max archive interval.

3. **Mapper** (`pipeline/OtEventMapper`) - converts `TagEvent` to protobuf `OTEvent` (schema: `src/main/proto/ot_event.proto`)

4. **Buffer** (`pipeline/StoreAndForwardBuffer`) - memory or disk-backed (`saf/DiskSpool`) with high/low watermark backpressure

5. **Sink** (`pipeline/ZerobusEventSink` -> `ZerobusClientManager`) - gRPC stream to Databricks Zerobus

### Servlet compatibility layer

`web/ZerobusServletHandler` holds shared request parsing. Version-specific dispatchers:
- `web/servlet81/` - `javax.servlet`
- `web/servlet83/` - `jakarta.servlet`

### Configuration

`ConfigModel` is the runtime configuration POJO. Settings persist via Ignition's PersistentRecord system (Gateway DB). `ZerobusSettings` (8.1) and `ZerobusSettings83` (8.3) manage the UI.

## Repository layout

- `module/` - Ignition module source + Gradle build (the main code)
- `demo/` - Databricks demo application (quick start: `cd demo && npm run demo:start`)
  - `frontend/` - React 18 + Vite + Tailwind dashboard
  - `backend/` - Express API server
  - `simulator/` - Tag simulator + Zerobus publisher
  - `app/` - Databricks Apps config (app.yaml, build/start scripts)
- `pipelines/sdp/` - SDP ETL pipeline (Python + SQL)
- `releases/` - Signed .modl artifacts
- `examples/` - Demo simulations (tag configs + timer scripts)
- `onboarding/` - Databricks/Ignition setup scripts
- `docker/` - Dockerfile.build-modl + Gateway docker-compose files

## API endpoints

All under `/system/zerobus`: `GET /health`, `GET /diagnostics`, `POST /config`, `POST /test-connection`, `POST /ingest`, `POST /ingest/batch`

## Configuring the Ignition Gateway

### Automated (recommended)

```bash
make configure-83      # Push Databricks config to 8.3 gateway
```

`make configure-*` sets `authMode` to `service_principal` and uses workspace-level M2M OAuth.

### Verifying the connection

```bash
make test-connection-83   # Validate auth from inside Ignition
make health-83            # Quick health check
make diag-83              # Full diagnostics (JSON)
```

### Full config push

**IMPORTANT**: `POST /system/zerobus/config` REPLACES the entire config - it does NOT merge. Always send complete config or use `setup_gateway()` which does GET-then-merge.

## Common pitfalls

1. **"Failed to get Zerobus token"** - Check that `workspaceUrl` and `zerobusEndpoint` point to the **same workspace ID**.

2. **Error 1521 (stream creation failed)** - Zerobus does not support tables with `CLUSTER BY`. Fix: `ALTER TABLE ... CLUSTER BY NONE`.

3. **SP needs UC grants** - The service principal needs `USE CATALOG`, `USE SCHEMA`, `MODIFY`, and `SELECT` on `raw_tags`.

4. **Schema is `ot`, not `bronze`** - Target table is `${CATALOG}.${SCHEMA}.raw_tags` (default: `agl_demo.ot.raw_tags`).

5. **Docker build requires correct IGNITION_HOME** - For 8.3: `--build-arg IGNITION_HOME=/usr/local/bin/ignition` (not `/usr/local/ignition`).

6. **Ignition caches modules in volume** - After rebuilding, you must `docker compose down -v` then `up -d` and redo setup wizard.

7. **Setup wizard after volume reset** - Open http://localhost:7088 and complete: EULA -> admin user (`admin`/`password`) -> Standard Trial -> Finish.

## Troubleshooting

### raw_throughput not updating (CDF / pipeline)

`raw_throughput` is populated by the SDP pipeline reading CDF from `raw_tags`. If empty:

1. Enable CDF: `ALTER TABLE agl_demo.ot.raw_tags SET TBLPROPERTIES (delta.enableChangeDataFeed = 'true');`
2. Verify: `SHOW TBLPROPERTIES agl_demo.ot.raw_tags ('delta.enableChangeDataFeed');`
3. Ensure pipeline is **Running** (Workflows -> Lakeflow Pipelines -> `[production] agl-etl`)

### Dashboard shows nothing

The dashboard shows metrics for events in the **last 5-10 minutes**:

1. **Time window** - Generate fresh events: `make simulate-83`
2. **Catalog/schema mismatch** - Ensure app env `APP_TARGET_CATALOG`/`APP_TARGET_SCHEMA` match gateway config
3. **SQL errors** - Check Databricks App backend logs

### Check SP and secret

```bash
make db-check-sp   # Verify [agl-demo] profile and OAuth secret
```

### Repo sync conflict (Conflict pulling from remote)

If `make db-repo-sync` or `db-all` fails with `BadRequest: Conflict pulling from remote. Conflicting files: ...`, the workspace repo has local changes that conflict with the remote branch. Resolve in Databricks: open **Workspace → Repos** → your repo, then **Pull** (or switch branch) and choose **Take all incoming changes** to overwrite local, or resolve conflicts manually. Then re-run `make db-repo-sync`.

### Zerobus endpoint format

- **Azure**: `<workspace-id>.zerobus.<region>.azuredatabricks.net`
- **AWS**: `<workspace-id>.zerobus.<region>.cloud.databricks.com`

Extract workspace ID from URL: `adb-7405617163765305` -> `7405617163765305`

## Redeploy to a new workspace

1. Update `~/.databrickscfg` `[daveok]` host to new workspace URL
2. Create SQL warehouse; note the ID
3. Clone this repo in workspace (Repos); note the path
4. Run:
   ```bash
   make db-create-sp
   DATABRICKS_WAREHOUSE_ID=<id> make db-setup-sql
   make db-wheel
   REPO_PATH=/Repos/... make db-pipeline
   make db-app-deploy
   make build-83 up-83
   # then: make setup-wizard-83 configure-83 simulate-83 links-83
   ```
5. Set `WORKSPACE_ID`, `DATABRICKS_REGION` in `.env`
