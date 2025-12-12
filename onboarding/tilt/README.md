# Tilt Renewables - End-to-End Onboarding Pack (Bronze → Silver → Gold)

This pack is a **reference end-to-end implementation** for a renewables operator (Tilt-style) using this connector.

## What you get

- **Bronze (fixed ingestion contract)**: One Delta table whose schema matches `module/src/main/proto/ot_event.proto` exactly.
- **Silver (renewables-first model)**: Normalized “fleet telemetry” views/tables (asset registry, normalized events, 1-min aggregates, state changes).
- **Gold (example outputs)**: Daily fleet KPIs + example derived metrics scaffolding.

## End-to-end flow

1. **Ignition** emits tag-change events (8.3+: Event Streams, 8.1/8.2: Gateway Tag Change Script)
2. Events are POSTed to the module: `/system/zerobus/ingest/batch`
3. Module batches + streams via **Databricks Zerobus** into **Bronze** (`ot_events_bronze`)
4. **Silver** transforms Bronze into renewables-friendly normalized telemetry
5. **Gold** produces dashboard/ML-ready tables (example templates)

## What stays fixed vs flexible

- **Fixed**: Bronze table schema **must** match `ot_event.proto` (columns + types + order).
- **Flexible**:
  - which tags you ingest (per customer/site)
  - how you map tags into renewables concepts (Silver mapping tables)
  - business KPIs and ML features (Gold)

## How to run (Databricks)

Run the SQL scripts in order:

1. `databricks/sql/00_prereqs_and_permissions.sql`
2. `databricks/sql/01_bronze__ot_events_v1.sql`
3. `databricks/sql/02_silver__asset_registry.sql`
4. `databricks/sql/03_silver__signal_mapping.sql`
5. `databricks/sql/04_silver__normalize_events.sql`
6. `databricks/sql/05_silver__aggregates_1min.sql`
7. `databricks/sql/06_silver__state_changes.sql`
8. `databricks/sql/07_gold__daily_kpis.sql`
9. `databricks/sql/08_gold__example_features.sql`

## How to configure the Ignition module (per site gateway)

Each site/gateway sets:

- `targetTable`: `{{catalog}}.{{schema}}.ot_events_bronze`
- `sourceSystemId`: a stable identifier like `tilt-<site>-ignition`

Everything else is standard Databricks workspace + service principal configuration.

## Notes for a first renewables customer

- Start by ingesting a small tag set per site (10–50 signals) to validate end-to-end.
- Use the `silver_signal_mapping` table to quickly map each tag to:
  - `site`, `asset_type`, `asset_id`, `signal`, `unit`
- Once mapping is stable, expand ingestion to a full fleet.


