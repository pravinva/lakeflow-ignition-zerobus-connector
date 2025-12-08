# Testing Setup Guide

## Ignition Docker Environment Setup

### Prerequisites

✅ Docker Desktop installed and running
✅ Docker Compose installed (`brew install docker-compose`)

### Step 1: Start Docker Desktop

Ensure Docker Desktop is running before proceeding:

```bash
open -a Docker
```

Wait for Docker Desktop to fully start (check the menu bar icon).

### Step 2: Launch Ignition Standard Architecture

Navigate to the Ignition examples directory and start the containers:

```bash
cd /Users/pravin.varma/Documents/Demo/ignition-examples/standard
docker-compose up -d
```

This will start:
- **Ignition Gateway** on port 8088
- **MariaDB Database** on port 3306

### Step 3: Access Ignition Gateway

Once containers are running, access the gateway at:

**URL:** http://gateway.localtest.me:8088

**Default Credentials:**
- Username: `admin`
- Password: `password`

### Step 4: Configure Simulator Devices

Ignition includes three built-in simulators for generating test SCADA data:

#### 1. Generic Simulator

The most versatile simulator with various tag types:

**Read-Only Tags:**
- `ReadOnlyBoolean1`, `ReadOnlyBoolean2` - Static boolean values
- `ReadOnlyInteger1-5` - Static integer values (1-5)
- `ReadOnlyFloat1`, `ReadOnlyFloat2` - Static float values
- `ReadOnlyString1`, `ReadOnlyString2` - Static strings

**Writable Tags:**
- `WriteableBoolean1`, `WriteableBoolean2` - Persistent boolean tags
- `WriteableInteger1`, `WriteableInteger2` - Persistent integer tags
- `WriteableFloat1`, `WriteableFloat2` - Persistent float tags
- `WriteableDouble1`, `WriteableDouble2` - Persistent double tags
- `WriteableString1`, `WriteableString2` - Persistent string tags

**Dynamic Tags:**

| Tag Type  | Tags Available | Behavior                                    |
|-----------|----------------|---------------------------------------------|
| Random    | RandomInteger1-2, RandomBoolean1-2, etc. | Values change randomly at fixed intervals |
| Sine      | Sine0-9        | Sine wave oscillation (e.g., -100 to 100 over 60s) |
| Ramp      | Ramp0-9        | Linear increase from low to high, then reset |
| Realistic | Realistic0-9   | Simulates realistic process variable drift |

**Example Simulator Tags for Zerobus Testing:**

```
Sine0        # -100 to 100, 60 second period (good for temperature)
Sine1        # -10 to 10, 10 second period (good for pressure deviation)
Ramp0        # 0 to 1000, 75 seconds (good for production counter)
Ramp1        # 0 to 100, 10 seconds (good for tank level %)
Realistic0   # Random walk, 5 second updates (good for flow rate)
RandomInteger1 # Random int, 1 second updates (good for status codes)
WriteableBoolean1 # Manual control flag
```

#### 2. Allen Bradley SLC Simulator

Mimics Allen-Bradley SLC PLC structure for realistic industrial testing.

#### 3. Dairy Demo Simulator

Includes realistic industrial tags:
- Compressor tags
- Tank level tags
- Motor status tags
- ControlLogix-like structure

### Step 5: Create Device Connection

In Ignition Gateway:

1. Navigate to **Config → OPC UA → Device Connections**
2. Click **Create new Device**
3. Select **Simulators → Generic Simulator**
4. Name it `TestSimulator`
5. Click **Create New Device**

### Step 6: Configure Tags for Zerobus Module

Create a tag folder structure for testing:

```
TestSimulator/
├── Process/
│   ├── Temperature (→ Sine0)
│   ├── Pressure (→ Sine1)
│   ├── FlowRate (→ Realistic0)
│   └── TankLevel (→ Ramp1)
├── Production/
│   ├── Counter (→ Ramp0)
│   └── Status (→ RandomInteger1)
└── Control/
    ├── StartButton (→ WriteableBoolean1)
    └── StopButton (→ WriteableBoolean2)
```

### Step 7: Install Zerobus Module

Once the module is built (`.modl` file):

1. In Ignition Gateway, go to **Config → System → Modules**
2. Click **Install or Upgrade a Module**
3. Upload the `.modl` file
4. Restart the Gateway when prompted

### Step 8: Configure Zerobus Connection

After module installation:

1. Navigate to the Zerobus module configuration page
2. Enter:
   - **Zerobus Endpoint**: Your Databricks workspace URL
   - **OAuth Client ID**: Service principal client ID
   - **OAuth Client Secret**: Service principal secret
   - **Target UC Table**: e.g., `dev_ot.bronze_ignition_events`
3. Configure tag subscriptions:
   - Select tag folders or individual tags
   - Set batch size (e.g., 100-500 events)
   - Set batch interval (e.g., 2-5 seconds)
4. Click **Test Connection** to verify
5. Enable the module

### Step 9: Monitor Data Flow

**In Ignition:**
- Check module diagnostics for send success/failure counts
- Monitor Gateway logs: **Status → Logs → Wrapper Log**

**In Databricks:**
```sql
-- Check recent events
SELECT * 
FROM dev_ot.bronze_ignition_events 
ORDER BY event_time DESC 
LIMIT 100;

-- Check ingestion rate
SELECT 
  DATE_TRUNC('minute', event_time) as minute,
  COUNT(*) as event_count,
  COUNT(DISTINCT tag_path) as unique_tags
FROM dev_ot.bronze_ignition_events
WHERE event_time >= CURRENT_TIMESTAMP - INTERVAL 1 HOUR
GROUP BY DATE_TRUNC('minute', event_time)
ORDER BY minute DESC;
```

## Testing Scenarios

### Scenario 1: Basic Connectivity (Test Case 1 from tester.md)

1. Start Ignition with simulators
2. Configure and enable Zerobus module
3. Verify connection test succeeds
4. Check Gateway logs for errors

**Expected:** Clean connection, no exceptions

### Scenario 2: Simple Ingestion (Test Case 2 from tester.md)

1. Subscribe to 2-3 simulator tags (e.g., Sine0, Ramp1, Realistic0)
2. Set small batch interval (2 seconds)
3. Let run for 5 minutes
4. Query Delta table

**Expected:** Rows exist for each tag, timestamps match, values correct

### Scenario 3: High-Frequency Load (Test Case 7 from tester.md)

1. Subscribe to 20-50 simulator tags
2. Use fast-updating tags (Random and Realistic series)
3. Run for 30 minutes
4. Monitor CPU/memory and ingestion rate

**Expected:** Stable throughput, no resource issues

## Docker Commands Reference

```bash
# Start the environment
cd /Users/pravin.varma/Documents/Demo/ignition-examples/standard
docker-compose up -d

# View logs
docker-compose logs -f gateway
docker-compose logs -f db

# Check container status
docker-compose ps

# Stop the environment
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v

# Restart gateway only
docker-compose restart gateway
```

## Troubleshooting

### Docker Desktop Not Starting

- Check if Docker Desktop app is running in menu bar
- Try: `killall Docker && open -a Docker`
- Check Docker Desktop settings for resource allocation

### Ignition Gateway Not Accessible

- Verify containers are running: `docker-compose ps`
- Check port conflicts: `lsof -i :8088`
- Review gateway logs: `docker-compose logs gateway`

### Module Installation Fails

- Check Ignition version compatibility (minimum 8.1.x)
- Verify module is signed correctly
- Check Gateway logs for specific error messages

### No Data in Databricks

- Verify OAuth credentials are correct
- Check Zerobus endpoint URL
- Ensure UC table exists and has correct permissions
- Review module diagnostic logs in Ignition

## References

- [Ignition Simulators Documentation](https://www.docs.inductiveautomation.com/docs/7.9/opc-ua-and-device-connections/simulators)
- [Ignition Docker Examples](https://github.com/thirdgen88/ignition-examples)
- [Databricks Zerobus Ingest](https://docs.databricks.com/en/ingestion/zerobus/index.html)

