# Zerobus Ignition AGL – Databricks App

React + FastAPI app for the Zerobus/Ignition AGL demo: OT tag streaming and asset framework UI.

## Deploy from Git

The app is managed by a **Databricks Asset Bundle** at the repo root. Deploy with the right variables; your Git workflow (e.g. CI or Repo) runs the frontend build.

### Deploy

From the **repo root** with the desired target and variables:

```bash
databricks bundle deploy -t dev
```

Uses the `dev` target in `databricks.yml` (profile `agl-demo`, catalog `agl_demo`, schema `ot`). Override variables per target or with `--var` if needed.

**Build:** Git will build the frontend (e.g. in CI run `databricks bundle run build -t dev` before deploy, or run `cd demo/app && npm ci && npm run build` in your pipeline). The bundle defines a `build` script you can run from the repo root: `databricks bundle run build -t dev`.

### Start the app

In the workspace UI or:

```bash
databricks bundle run zerobus_ignition_agl -t dev
```

### Bundle configuration

- **Bundle:** `databricks.yml` at repo root.
- **Variables:** `catalog`, `schema`, `DATABRICKS_WAREHOUSE_ID` (lookup: "Serverless Starter Warehouse"). Override in a target or via `--var`.

### Local development

- **Frontend:** `npm run dev` from `demo/app`.
- **Backend:** `uv run uvicorn backend.main:app --reload` from `demo/app`.
- **Run as Databricks app locally:** From repo root, `databricks apps run-local` (see [Databricks Apps run-local](https://docs.databricks.com/en/dev-tools/databricks-apps/run-local.html)).

### Backend tests

From `demo/app`:

- **Unit tests (no Databricks):** `uv run pytest backend/tests/` — runs compression layer-building and other unit tests; integration tests are skipped when Databricks env is not set.
- **Integration tests (real `agl_demo.ot.raw_tags`):** From repo root, copy `.env.example` to `.env` and set `DATABRICKS_CONFIG_PROFILE=daveok` and `DATABRICKS_WAREHOUSE_ID`. Run `databricks auth login --host https://adb-<workspace-id>.11.azuredatabricks.net` and choose profile `daveok`. If tests still skip with "auth failed", set `DATABRICKS_HOST` in `.env` to that same URL (or leave it unset to use the profile host). Source before tests: `set -a && source .env && set +a`, then from `demo/app`: `uv run pytest backend/tests/ -m integration`. Ensure `raw_tags` has recent data (e.g. run `make simulate-83` first).

By default, pytest skips integration tests when the warehouse or auth is missing. Run only unit tests with: `uv run pytest backend/tests/ -m "not integration"`.

### Schema: `sdt_enabled` (SDT on/off from Ignition)

The connector sends a per-event **`sdt_enabled`** flag (gateway config: SDT compression was on when the event was sent). The dashboard uses it to show "Gateway: SDT on/off". If your `raw_tags` table was created before this column existed, add it once:

```sql
ALTER TABLE your_catalog.your_schema.raw_tags
ADD COLUMN sdt_enabled BOOLEAN COMMENT 'Gateway config: SDT was on when this event was sent';
```

New setups (e.g. `examples/agl_fleet/setup_databricks.sql`) include `sdt_enabled` in the table DDL.

### Troubleshooting: 503 when opening the app

If you see **"Failed to load resource: 503"** (e.g. on `dashboard` or the main document) when opening the app or the Logs tab:

1. **Cold start** – The app container may still be starting. Wait 10–20 seconds and refresh the page.
2. **Check app status** – In the Apps UI, confirm the app is **Running** (not Starting or Error).
3. **Check application logs** – On the app’s **Logs** tab (or append `/logz` to the app URL), look for Python tracebacks or "Application startup complete". Crashes after startup will show there.
4. **Redeploy** – If the app is in Error, redeploy and start again: `databricks bundle deploy -t production` then start the app from the UI or `databricks bundle run zerobus_ignition_agl -t production`.
