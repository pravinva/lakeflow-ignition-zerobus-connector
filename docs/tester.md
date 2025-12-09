# TESTER.md

## Role

Act as the **QA engineer**. Define and maintain test plans and scenarios for the Ignition → Zerobus → Databricks integration.

## Test Objectives

- Verify end‑to‑end event flow:
  - Tag change in Ignition → row in Delta via Zerobus.
- Validate robustness:
  - Network glitches, auth failures, restarts.
- Confirm configuration behaves as expected:
  - Tag selection, batching, enable/disable toggles.

## Test Environment

- **Ignition Dev Gateway**
  - Trial or non‑production license.
  - Demo/simulated tags (e.g. Ramp, Sine, Boolean toggles).
- **Databricks**
  - Workspace with Zerobus Ingest enabled.
  - Test Delta table in UC (e.g. `dev_ot.bronze_ignition_events`).
  - Service principal / OAuth client with write access only.
- **Module**
  - Latest `.modl` built from `main` or feature branch.

## Functional Test Cases

### 1. Basic Connectivity

**Steps**

1. Install module on dev Ignition Gateway.
2. Open config UI and enter:
   - Zerobus endpoint.
   - OAuth credentials.
   - Target UC table.
3. Click “Test connection”.

**Expected**

- Clear success message in UI or logs.
- No uncaught exceptions in Ignition logs.

### 2. Simple Ingestion

**Steps**

1. Configure module to subscribe to 2–3 demo tags.
2. Set small batch interval (e.g. 1–2 seconds).
3. Let it run for a few minutes.
4. In Databricks, query the target Delta table.

**Expected**

- Rows exist for each subscribed tag.
- Timestamps reasonably match Ignition event times.
- Values and quality flags match Ignition.

### 3. Configuration Changes

**Steps**

1. Change batch size / interval settings in UI.
2. Save and apply configuration.
3. Generate additional tag changes.
4. Observe logs and Delta contents.

**Expected**

- Module applies new settings without restart (if supported).
- No data loss during reconfiguration.
- Batch sizes reflect updated settings.

### 4. Enable / Disable

**Steps**

1. Toggle module “enabled” flag off.
2. Generate tag changes in Ignition.
3. Toggle “enabled” back on.
4. Generate more tag changes.
5. Query Delta.

**Expected**

- No new rows during disabled period.
- New rows appear again once enabled.

## Resilience & Negative Tests

### 5. Network Loss

**Steps**

1. Start module in normal state.
2. Temporarily block outbound traffic from Ignition to Zerobus endpoint (e.g. firewall rule or host override).
3. Keep generating tag changes.
4. Restore network connectivity.

**Expected**

- Module logs show connection errors and retries.
- Module does not crash.
- On restore, ingestion resumes.
- Acceptable behavior for events during outage (documented as either lost or retried).

### 6. Invalid Credentials

**Steps**

1. Enter invalid OAuth client secret in config.
2. Trigger “Test connection” or wait for normal sends.

**Expected**

- Clear auth error messages in logs/diagnostics.
- No partial or malformed data in Delta.
- Module remains running but in “error” state until credentials are fixed.

### 7. High-Frequency / Load

**Steps**

1. Configure many tags (e.g. tens or low hundreds) at higher update rates.
2. Run for a defined period (e.g. 10–30 minutes).
3. Monitor:
   - Ignition Gateway CPU/memory.
   - Module logs.
   - Row counts and ingest rate in Delta.

**Expected**

- Ingestion throughput is stable and within target ranges.
- No runaway resource usage on Ignition.
- No frequent failures from Zerobus (rate limits, timeouts, etc.).

## Regression & Automation

- Maintain a small automated suite (where possible):
  - Scripted checks in Databricks for:
    - Row presence.
    - Schema validation.
    - Basic latency metrics (event_time vs ingestion_time).
- Manual regression triggers:
  - Any change in:
    - Zerobus SDK version.
    - Ignition SDK version.
    - Module config model or mapping logic.

## Test Exit Criteria (v1)

- All functional tests pass.
- Resilience tests acceptable and documented.
- No P1/P2 bugs in logs during a multi-hour soak run.

