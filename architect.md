# ARCHITECT.md

## Role

Act as the **software architect** for the Ignition → Zerobus → Databricks solution. Maintain this document as the high‑level design and constraints.

## Objective

Design an edge–cloud pattern where Ignition acts as the OT data hub and Databricks Lakehouse is the scalable historian/analytics layer, connected via Zerobus Ingest.

## High-Level Architecture

**OT / Edge**

- PLCs, RTUs, DCS, SCADA systems on plant networks.
- Ignition Gateway in DMZ / Level 3.5:
  - Connects southbound via OPC‑UA, Modbus, vendor drivers.
  - Exposes tags, alarms, and events as a normalized OT data hub.

**Custom Ignition Module**

- JVM module built with Ignition SDK (Gateway scope).
- Uses Databricks Zerobus Java SDK to push events to Zerobus Ingest.
- Subscribes to configured Ignition tags / MQTT / Sparkplug.

**Cloud / Databricks**

- Zerobus Ingest endpoint (part of Lakeflow Connect).
- Target Delta tables in Unity Catalog:
  - Bronze: raw OT events (asset, tag, ts, value, quality, source).
  - Silver/Gold: curated, joined with asset context and OT semantics.
- Workflows/Jobs for curation, ML, dashboards, and apps.

## Data Model (Initial)

- Core event table (Bronze):

  - `event_time` (timestamp)
  - `asset_id` / `asset_path`
  - `tag_path`
  - `value` (numeric/string)
  - `quality` / `status`
  - `source_system` (e.g. `ignition-gw-01`)
  - Optional: `site`, `line`, `unit`

- Context tables:

  - Asset hierarchy (from Ignition or PI AF).
  - Alarm/event definitions (severity, category, etc.).

## Reliability & Ordering

- Delivery semantics:
  - At-least-once from Ignition → Zerobus → Delta.
  - Idempotency at Delta via composite key (`asset_id`, `tag_path`, `event_time`) and MERGE/DEDUP jobs if needed.
- Failure handling:
  - Zerobus Java SDK retries and backoff.
  - Clear logging/metrics in module for failures and reconnections.

## Security

- Ignition Gateway:
  - Runs in DMZ; outbound TLS to Databricks only.
  - No inbound connections from cloud into OT.
- Databricks:
  - OAuth2 client credentials for Zerobus client.
  - Scoped service principal with write access only to specific tables.
- Network:
  - Prefer private connectivity (VPN/Private Link) where available.
  - Otherwise locked‑down outbound HTTPS to Databricks.

## Deployment Patterns

### Single Gateway

- **Scenario**: Single plant/site with one Ignition Gateway.
- **Configuration**: Module configured to send all tags to one UC table.
- **Pros**: Simple setup, single point of configuration.
- **Cons**: Single point of failure for data collection.

### Multi-Gateway Federation

- **Scenario**: Multiple sites, each with dedicated Ignition Gateway.
- **Configuration**: Each gateway sends to same or different UC tables.
  - Option A: All → single Bronze table (add `site_id` field).
  - Option B: Per-site tables → unified via Silver layer view/merge.
- **Pros**: Site isolation, independent operation.
- **Cons**: Multiple configurations to manage.

### High-Availability

- **Scenario**: Redundant Ignition Gateways (active-standby or active-active).
- **Configuration**: 
  - Both gateways send events (de-duplication handled in Lakehouse).
  - Or: Active gateway only sends (requires external orchestration).
- **Considerations**: Ensure idempotency in Delta merge logic.

## Non-Goals (v1)

- No on-disk buffering in the module (beyond small in‑memory queues).
- No control/command path (write‑back to OT) – telemetry only.
- No advanced schema evolution; assume stable UC schemas for initial targets.
- No on-premise Lakehouse support (cloud Databricks only).

## Performance & Scalability

### Throughput Targets

- **Tag Update Rate**: Support up to 10,000 tags per gateway with update rates of 1-10 Hz.
- **Batch Processing**: Configurable batching (100-1000 events or 1-5 second windows).
- **Network**: Assume 10-100 Mbps available bandwidth for outbound traffic.

### Resource Constraints

- **Gateway Memory**: Module should use < 500 MB heap for typical deployments.
- **CPU**: Minimal CPU impact on Ignition Gateway (< 5% sustained).
- **Buffering**: In-memory queue up to 10,000 events before backpressure/drop strategy.

## Monitoring & Observability

### Module Metrics (Exposed via Ignition)

- Event throughput (events/second sent to Zerobus).
- Success/failure counts per batch.
- Current queue depth.
- Last successful connection timestamp.
- Retry attempts and backoff status.

### Databricks Side

- Zerobus Ingest metrics (built-in):
  - Ingestion rate, lag, error rates.
- Custom monitoring:
  - Row counts by hour/day in Bronze tables.
  - Data quality checks (missing values, out-of-range timestamps).
  - End-to-end latency (event_time vs ingestion_time).

## Dependencies & Prerequisites

### Ignition Requirements

- **Minimum Version**: Ignition 8.1.x or higher (SDK compatibility).
- **Gateway Scope**: Module runs in Gateway scope only.
- **License**: Standard or higher (module installation capability).

### Databricks Requirements

- **Lakeflow Connect**: Zerobus Ingest feature enabled.
- **Unity Catalog**: Target tables must be UC-managed.
- **Cluster/SQL Warehouse**: For downstream processing and queries.
- **Authentication**: OAuth2 M2M (machine-to-machine) credentials.

### Network Requirements

- **Outbound HTTPS**: Gateway → Databricks (port 443).
- **Latency**: < 100ms preferred for consistent performance.
- **Bandwidth**: Min 10 Mbps sustained.

## Open Questions & Recommendations

### 1. Aggregation Strategy

**Question**: How much aggregation (if any) should happen in Ignition vs Lakehouse?

**Recommendation**: 
- **Edge (Ignition)**: Minimal aggregation – primarily raw event forwarding.
  - Rationale: Preserve raw fidelity; leverage Lakehouse compute for flexible aggregation.
  - Exception: Optional pre-filtering (tag quality, value change deadband).
- **Lakehouse**: All statistical aggregations, rollups, and analytics.
  - Silver layer: 1-minute, 1-hour aggregates.
  - Gold layer: Shift summaries, KPIs, ML features.

### 2. Rate Limiting

**Question**: Do we need per-site throttling / rate limiting in the module?

**Recommendation**: 
- **Yes**, implement configurable rate limits:
  - Max events per second (default: 1000/sec).
  - Max queue depth (default: 10,000 events).
  - Backpressure strategy: Drop oldest events with warning log.
- **Purpose**: Protect Ignition Gateway from memory exhaustion and Zerobus from rate limit rejections.

### 3. Ignition Compatibility

**Question**: What is the minimum Ignition version and module compatibility matrix?

**Recommendation**:
- **Minimum**: Ignition 8.1.0 (stable SDK, tag APIs).
- **Target**: Ignition 8.1.x - 8.2.x (long-term support versions).
- **Testing Matrix**:
  - Primary: Latest 8.1.x LTS release.
  - Secondary: Latest 8.2.x release.
- **Module Signing**: Use Inductive Automation module signing for production.

## Future Enhancements (Beyond v1)

- **Sparkplug B Support**: Native MQTT Sparkplug payload handling.
- **On-Disk Buffering**: Local persistence for outage recovery (SQLite or file-based).
- **Schema Evolution**: Dynamic schema detection and UC schema evolution handling.
- **Multi-Workspace**: Support sending to multiple Databricks workspaces.
- **Advanced Filtering**: CEL (Common Expression Language) for complex tag filtering.
- **Bi-directional**: Command/control path (Lakehouse → Ignition) for closed-loop optimization.

