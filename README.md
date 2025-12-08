# Lakeflow Ignition Zerobus Connector

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Ignition](https://img.shields.io/badge/ignition-8.1%2B-orange.svg)](https://inductiveautomation.com/)
[![Zerobus SDK](https://img.shields.io/badge/zerobus--sdk--java-0.1.0-green.svg)](https://github.com/databricks/zerobus-sdk-java)

Ignition Gateway module that streams OT (Operational Technology) data from Ignition tags directly into Databricks Delta tables using [Zerobus Ingest](https://github.com/databricks/zerobus-sdk-java).

## Overview

This module enables real-time streaming of SCADA/OT data from Inductive Automation's Ignition platform to Databricks Lakehouse, creating a bridge between industrial automation systems and cloud-based analytics.

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│  PLCs / SCADA   │────────▶│  Ignition GW     │────────▶│  Databricks     │
│  (Modbus, OPC)  │         │  + Zerobus Module│         │  Delta Tables   │
└─────────────────┘         └──────────────────┘         └─────────────────┘
                                     │                             │
                                     │                             ▼
                                     │                    ┌─────────────────┐
                                     │                    │  ML / Analytics │
                                     │                    │  Dashboards     │
                                     └────────────────────│  IoT Platform   │
                                                         └─────────────────┘
```

## Features

- ✅ Real-time tag change streaming to Delta tables
- ✅ Configurable tag selection (folder-based or explicit paths)
- ✅ Automatic batching and backpressure management
- ✅ OAuth2 authentication with service principals
- ✅ Stream recovery and retry logic via Zerobus SDK
- ✅ Web-based configuration UI in Ignition Gateway
- ✅ Support for multiple data types (numeric, string, boolean)
- ✅ Quality code mapping (Good, Bad, Uncertain)
- ✅ Asset hierarchy extraction from tag paths

## Architecture

See [architect.md](architect.md) for detailed architecture, security model, and deployment patterns.

**Key Components:**
- **Tag Subscription Service** - Monitors Ignition tags for value changes
- **Event Mapper** - Converts tag events to Protobuf messages
- **Zerobus Client Manager** - Manages streaming to Databricks via [Zerobus SDK](https://github.com/databricks/zerobus-sdk-java)
- **Configuration UI** - Gateway web interface for module settings

## Prerequisites

### Ignition

- **Version**: 8.1.x or higher
- **License**: Standard or higher (for module installation)
- **Network**: Outbound HTTPS to Databricks (port 443)

### Databricks

- **Lakeflow Connect**: Zerobus Ingest enabled (contact Databricks support)
- **Unity Catalog**: Target Delta table in UC
- **Service Principal**: OAuth2 credentials with write permissions
- **Workspace**: E2 or higher (for Zerobus support)

### Development

- **JDK**: 17+ (OpenJDK or Oracle)
- **Gradle**: 8.x (included via wrapper)
- **Docker**: For local Ignition testing (optional but recommended)

## Quick Start

### 1. Build the Module

```bash
cd module
./gradlew buildModule
```

Output: `build/modules/zerobus-connector-1.0.0.modl`

### 2. Install in Ignition

1. Access Ignition Gateway: `http://your-gateway:8088`
2. Navigate to: **Config → System → Modules**
3. Click **Install or Upgrade a Module**
4. Upload `zerobus-connector-1.0.0.modl`
5. Restart Gateway when prompted

### 3. Create Delta Table

In Databricks SQL Editor:

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
  unit STRING
)
USING DELTA;
```

### 4. Configure OAuth Service Principal

```sql
-- Grant permissions to service principal
GRANT MODIFY, SELECT ON TABLE dev_ot.bronze_ignition_events 
TO SERVICE_PRINCIPAL '<your-client-id>';
```

### 5. Configure the Module

In Ignition Gateway:
1. Navigate to the Zerobus module configuration page
2. Enter:
   - **Workspace URL**: `https://<workspace-id>.cloud.databricks.com`
   - **Zerobus Endpoint**: `<workspace-id>.zerobus.<region>.cloud.databricks.com`
   - **OAuth Client ID**: Your service principal client ID
   - **OAuth Client Secret**: Your service principal secret
   - **Target Table**: `dev_ot.bronze_ignition_events`
3. Configure tag subscriptions
4. Click **Test Connection**
5. Enable the module

### 6. Verify Data Flow

Query data in Databricks:

```sql
SELECT * 
FROM dev_ot.bronze_ignition_events 
ORDER BY event_time DESC 
LIMIT 100;
```

## Documentation

### For Team Members

- 📐 **[architect.md](architect.md)** - System architecture, design decisions, deployment patterns
- 💻 **[developer.md](developer.md)** - Implementation guide, API references, build instructions
- 🧪 **[tester.md](tester.md)** - Test cases, quality assurance procedures
- 🔧 **[TESTING_SETUP.md](TESTING_SETUP.md)** - Local testing with Docker and Ignition simulators

### Official Resources

- **Zerobus SDK for Java**: https://github.com/databricks/zerobus-sdk-java
  - API documentation, examples, error handling
  - Current version: 0.1.0 (Public Preview)
  
- **Ignition SDK**:
  - Examples: https://github.com/inductiveautomation/ignition-sdk-examples
  - Nexus Repository: https://nexus.inductiveautomation.com/repository/inductiveautomation-releases
  - Documentation: https://docs.inductiveautomation.com/docs/8.1/sdk-documentation
  
- **Databricks Lakeflow Connect**:
  - Contact your Databricks account team for Zerobus enablement

## Local Testing with Docker

We provide a complete Docker-based testing environment using [Ignition Docker examples](https://github.com/thirdgen88/ignition-examples):

```bash
# Clone Ignition examples
cd /path/to/Demo
git clone https://github.com/thirdgen88/ignition-examples.git

# Start Ignition Gateway with database
cd ignition-examples/standard
docker-compose up -d

# Access at http://gateway.localtest.me:8088
# Username: admin / Password: password
```

The Ignition Gateway includes three built-in simulators for generating test data:
- **Generic Simulator** - Sine waves, ramps, random values
- **Allen Bradley SLC Simulator** - SLC PLC structure
- **Dairy Demo Simulator** - Industrial equipment tags

See [TESTING_SETUP.md](TESTING_SETUP.md) for detailed setup and testing procedures.

## Configuration Options

### Module Settings

| Setting | Description | Default |
|---------|-------------|---------|
| Workspace URL | Databricks workspace URL | Required |
| Zerobus Endpoint | Zerobus gRPC endpoint | Required |
| OAuth Client ID | Service principal client ID | Required |
| OAuth Client Secret | Service principal secret | Required |
| Target Table | UC table (catalog.schema.table) | Required |
| Tag Selection | Folders or explicit tag paths | None |
| Batch Size | Max events per batch | 500 |
| Batch Interval | Flush interval (seconds) | 5 |
| Max Inflight Records | Backpressure threshold | 50,000 |
| Enable Stream Recovery | Auto-recover on failures | true |
| Recovery Retries | Max recovery attempts | 3 |

### Stream Configuration

Powered by the [Zerobus SDK for Java](https://github.com/databricks/zerobus-sdk-java):

```java
StreamConfigurationOptions options = StreamConfigurationOptions.builder()
    .setMaxInflightRecords(50000)      // Backpressure threshold
    .setRecovery(true)                 // Enable auto-recovery
    .setRecoveryRetries(3)             // Max recovery attempts
    .setFlushTimeoutMs(300000)         // 5 minute flush timeout
    .setServerLackOfAckTimeoutMs(60000) // 1 minute ack timeout
    .build();
```

## Monitoring

### In Ignition

- **Module Diagnostics**: View events sent, success/failure counts
- **Gateway Logs**: Status → Logs → Wrapper Log
- **Stream State**: Monitor connection status and recovery events

### In Databricks

```sql
-- Check ingestion rate
SELECT 
  DATE_TRUNC('minute', event_time) as minute,
  COUNT(*) as event_count,
  COUNT(DISTINCT tag_path) as unique_tags
FROM dev_ot.bronze_ignition_events
WHERE event_time >= CURRENT_TIMESTAMP - INTERVAL 1 HOUR
GROUP BY 1
ORDER BY 1 DESC;

-- Check data quality
SELECT 
  quality,
  COUNT(*) as count,
  COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () as percentage
FROM dev_ot.bronze_ignition_events
WHERE event_time >= CURRENT_TIMESTAMP - INTERVAL 1 DAY
GROUP BY quality;
```

## Troubleshooting

### Module Won't Install
- Verify Ignition version ≥ 8.1.0
- Check Gateway logs for specific errors
- Ensure module signature is valid

### Connection Test Fails
- Verify OAuth credentials are correct
- Check Zerobus endpoint URL format
- Ensure network allows outbound HTTPS to Databricks
- Verify service principal has permissions on target table

### No Data in Delta Table
- Check module is enabled and stream state is OPENED
- Review Gateway logs for ingestion errors
- Verify tag subscriptions are configured
- Check tags are actually changing values
- Query `SHOW TABLES` to confirm table exists

### Performance Issues
- Adjust batch size and interval for your throughput
- Monitor `maxInflightRecords` and backpressure warnings
- Check Ignition Gateway CPU/memory usage
- Review Zerobus Ingest metrics in Databricks

## Contributing

This is an internal project for Ignition-to-Databricks integration. For issues or enhancements:

1. Review [developer.md](developer.md) for implementation details
2. Run full test suite from [tester.md](tester.md)
3. Ensure all tests pass before committing
4. Update documentation as needed

## License

Apache 2.0 - See [LICENSE](LICENSE) for details.

## Dependencies

### Runtime Dependencies

- [Databricks Zerobus SDK for Java](https://github.com/databricks/zerobus-sdk-java) v0.1.0 - Apache 2.0
- Protocol Buffers Java v3.21.12 - BSD 3-Clause
- Ignition SDK v8.3.0 - Inductive Automation License

### Build Dependencies

- Gradle Protobuf Plugin v0.9.4
- JUnit Jupiter v5.9.2
- Mockito v5.1.1

### Repositories

- **Maven Central** - Zerobus SDK, Protobuf
- **Inductive Automation Nexus** - Ignition SDK artifacts
  - Releases: https://nexus.inductiveautomation.com/repository/inductiveautomation-releases
  - Third-party: https://nexus.inductiveautomation.com/repository/inductiveautomation-thirdparty

## Acknowledgments

- **Inductive Automation** for the Ignition platform and SDK
- **Databricks** for Zerobus Ingest and the [Zerobus SDK for Java](https://github.com/databricks/zerobus-sdk-java)
- **thirdgen88** for [Ignition Docker examples](https://github.com/thirdgen88/ignition-examples)

## Support

For issues related to:
- **Zerobus SDK**: https://github.com/databricks/zerobus-sdk-java/issues
- **Ignition SDK**: https://forum.inductiveautomation.com/
- **This Module**: Contact your team's Databricks or Ignition administrator
