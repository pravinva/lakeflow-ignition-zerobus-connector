# Creating Second Event Stream: zerobus_gateway

This guide shows how to create the second Event Stream for testing with Ramp tags.

## Steps in Ignition Designer

### 1. Create New Event Stream

1. Open **Ignition Designer**
2. Go to **Project Browser** → **Event Streams**
3. Right-click → **New Event Stream**
4. **Name:** `zerobus_gateway`

### 2. Configure Source

Click on **Source** stage:

- **Type:** `Tag Event`
- **Tag Paths:** Add these tags:
  ```
  [Sample_Tags]Ramp/Ramp0
  [Sample_Tags]Ramp/Ramp1
  [Sample_Tags]Ramp/Ramp2
  [Sample_Tags]Ramp/Ramp3
  ```

- **Trigger Conditions:**
  - ☑ **Value Changed**
  - ☐ Quality Changed
  - ☐ Timestamp Changed

### 3. Configure Encoder

Click on **Encoder** stage:

- **Type:** `String`
- **Encoding:** `UTF-8`

### 4. Configure Buffer

Click on **Buffer** stage:

- **Debounce:** `100` ms
- **Max Wait:** `1000` ms
- **Max Queue Size:** `10000`
- **Overflow:** `DROP_OLDEST`

### 5. Add Script Handler

Click **Add Handler** → **Script**

**Copy this script:**

```python
def onEventsReceived(events, state):
    """
    Handler for zerobus_gateway Event Stream
    Sends Ramp tag events to Zerobus module
    """
    import system.net
    import system.util
    
    batch = []
    for event in events:
        batch.append({
            'tagPath': str(event.metadata.get('tagPath', '')),
            'tagProvider': str(event.metadata.get('provider', '')),
            'value': event.data,
            'quality': str(event.metadata.get('quality', 'GOOD')),
            'qualityCode': int(event.metadata.get('qualityCode', 192)),
            'timestamp': long(event.metadata.get('timestamp', system.date.now().time)),
            'dataType': type(event.data).__name__
        })
    
    try:
        response = system.net.httpPost(
            url='http://localhost:8088/system/zerobus/ingest/batch',
            contentType='application/json',
            postData=system.util.jsonEncode(batch),
            timeout=10000
        )
        if hasattr(response, 'statusCode') and response.statusCode == 200:
            logger = system.util.getLogger('EventStream.ZerobusGateway')
            logger.info('Sent {} Ramp events'.format(len(batch)))
    except Exception as e:
        logger = system.util.getLogger('EventStream.ZerobusGateway')
        logger.error('Error: {}'.format(str(e)))
```

### 6. Configure Handler Failure Handling

In Script Handler settings:

- **Enabled:** ☑ Checked
- **Failure Mode:** `RETRY`
- **Retry Strategy:** `EXPONENTIAL`
- **Retry Count:** `3`
- **Retry Delay:** `1` second
- **Multiplier:** `2`
- **Max Delay:** `10000` ms
- **Retry Failure:** `ABORT`

### 7. Save and Enable

1. Click **Save** (floppy disk icon)
2. Toggle **Enabled** (switch at top right)

## Verify

### In Designer Status Panel

You should see:
- **Events Received:** Incrementing
- **Handler 1 (Script) Execution:** Showing times
- **No errors** in Test Results

### Check Module Diagnostics

```bash
curl http://localhost:8088/system/zerobus/diagnostics
```

Should show increased events from both Event Streams:
- Original: Sine + Realistic tags (from ZerobusTagStream)
- New: Ramp tags (from zerobus_gateway)

### Check Databricks

```sql
SELECT 
  tag_path,
  numeric_value,
  quality,
  event_time
FROM ignition_demo.scada_data.tag_events
WHERE tag_path LIKE '%Ramp%'
ORDER BY event_time DESC
LIMIT 100;
```

You should see Ramp tag data flowing!

## Comparison: Two Event Streams

| Event Stream | Tags | Purpose |
|--------------|------|---------|
| **ZerobusTagStream** | Sine, Realistic | Original test stream |
| **zerobus_gateway** | Ramp | Second test stream |

Both send to the same Zerobus module and Databricks table.

## Monitoring Both Streams

### Event Stream Metrics

In Designer, each Event Stream shows separate metrics:

1. **ZerobusTagStream:**
   - Events from Sine and Realistic tags
   
2. **zerobus_gateway:**
   - Events from Ramp tags

### Combined Module Diagnostics

```bash
# Total events from both streams
curl http://localhost:8088/system/zerobus/diagnostics
```

### Separate Logs

Check Gateway logs for separate loggers:

```bash
# Original stream
tail -f /usr/local/ignition/logs/wrapper.log | grep "EventStream.Zerobus"

# New stream
tail -f /usr/local/ignition/logs/wrapper.log | grep "EventStream.ZerobusGateway"
```

## Quick Copy-Paste Script

**Script file location:** `configs/zerobus_gateway_handler.py`

**View script:**
```bash
cat configs/zerobus_gateway_handler.py
```

**Or copy from here:**
See Step 5 above for the complete script.

## Testing

1. **Create the Event Stream** (follow steps above)
2. **Enable it**
3. **Wait 10 seconds**
4. **Check diagnostics:**
   ```bash
   curl http://localhost:8088/system/zerobus/diagnostics | grep "Total Events"
   ```
5. **Query Databricks:**
   ```sql
   SELECT tag_path, COUNT(*) as event_count
   FROM ignition_demo.scada_data.tag_events
   WHERE event_time >= current_timestamp() - INTERVAL 5 MINUTES
   GROUP BY tag_path
   ORDER BY event_count DESC;
   ```

You should see events from both Ramp and Sine/Realistic tags!

## Cleanup

To remove the test Event Stream later:

1. Designer → Event Streams
2. Right-click `zerobus_gateway`
3. Delete

The module will continue processing events from the original Event Stream.

