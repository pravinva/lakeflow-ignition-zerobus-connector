# Event Streams Integration Guide

This guide explains how to configure Ignition Event Streams to send tag changes to the Zerobus Connector module.

## Overview

Configure Ignition Event Streams (8.3+) to push tag changes directly to the module. This provides:

- **Event-driven architecture** - Immediate notification when tags change
- **Low latency** - Sub-second from tag change to Databricks
- **Flexibility** - Filter, transform, and batch events in the Designer
- **Better resource utilization** - Only process actual tag changes

## Architecture

```
Ignition Tags
    ↓
Event Stream (Tag Event Source)
    ↓
Optional: Filter Stage
    ↓
Optional: Transform Stage
    ↓
Buffer Stage (batching)
    ↓
Script Handler
    ↓
POST to Zerobus Module REST API
    ↓
Zerobus Connector Module
    ↓
Databricks Delta Table
```

## Prerequisites

- Ignition 8.3.0 or later
- Zerobus Connector Module installed and configured
- Tags to monitor configured in Ignition

## Step 1: Create Event Stream in Designer

1. Open the Ignition Designer
2. Navigate to **Project Browser** → **Event Streams**
3. Right-click and select **New Event Stream**
4. Name it: `ZerobusTagStream`

## Step 2: Configure Tag Event Source

In the Event Stream editor:

1. **Source Stage**:
   - Type: `Tag Event`
   - Click **Configure Source**
   - **Tag Paths**: Add the tags you want to monitor
     ```
     [Sample_Tags]Sine/Sine0
     [Sample_Tags]Sine/Sine1
     [Sample_Tags]Realistic/Realistic0
     [Sample_Tags]Realistic/Realistic1
     ```
   - **Trigger Conditions**:
     - ☑ Value Changed
     - ☑ Quality Changed (optional)
     - ☐ Timestamp Changed (usually not needed)
   - **Scan Class**: Choose appropriate scan class or leave default

2. **Encoder Stage**:
   - Select: `JsonObject` (recommended)
   - Encoding: `UTF-8`

## Step 3: Configure Buffer Stage

The buffer stage controls batching and backpressure:

- **Debounce**: `100` ms (wait time between events before sending batch)
- **Max Wait**: `1000` ms (maximum time before forcing batch send)
- **Max Queue Size**: `10000` (0 for unlimited, but not recommended)
- **Overflow**: `DROP_OLDEST` (drop old events if queue fills)

These settings ensure events are batched for efficiency while maintaining low latency.

## Step 4: Add Script Handler

1. Click **Add Handler** → **Script**
2. Configure the handler:

```python
# Event Stream Script Handler for Zerobus Connector
# Sends tag change events to the module's REST endpoint

def onEventsReceived(events, state):
    """
    Handle events from Event Stream and send to Zerobus module.
    
    IMPORTANT: Function name MUST be 'onEventsReceived' - this is what Ignition calls.
    
    Args:
        events: List of event objects (always a list, even if only one event)
        state: Persistent state dictionary for maintaining state between calls
    """
    import system.net
    import system.util
    
    # Build batch payload
    batch = []
    
    for event in events:
        # Extract tag information
        tag_path = event.metadata.get('tagPath', '')
        tag_provider = event.metadata.get('provider', '')
        quality = event.metadata.get('quality', 'GOOD')
        quality_code = event.metadata.get('qualityCode', 192)
        timestamp_ms = event.metadata.get('timestamp', system.date.now().time)
        value = event.data
        
        # Determine data type
        data_type = 'Unknown'
        if isinstance(value, bool):
            data_type = 'Boolean'
        elif isinstance(value, int):
            data_type = 'Int4'
        elif isinstance(value, long):
            data_type = 'Int8'
        elif isinstance(value, float):
            data_type = 'Float8'
        elif isinstance(value, basestring):
            data_type = 'String'
        
        batch.append({
            'tagPath': tag_path,
            'tagProvider': tag_provider,
            'value': value,
            'quality': quality,
            'qualityCode': quality_code,
            'timestamp': timestamp_ms,
            'dataType': data_type
        })
    
    # Send batch to Zerobus module
    try:
        response = system.net.httpPost(
            url='http://localhost:8088/system/zerobus/ingest/batch',
            contentType='application/json',
            postData=system.util.jsonEncode(batch),
            timeout=10000
        )
        
        if response.statusCode == 200:
            result = system.util.jsonDecode(response.text)
            logger = system.util.getLogger('EventStream.Zerobus')
            logger.info('Batch sent: {} accepted, {} dropped'.format(
                result.get('accepted', 0),
                result.get('dropped', 0)
            ))
        else:
            logger = system.util.getLogger('EventStream.Zerobus')
            logger.warn('Failed to send batch: HTTP {}'.format(response.statusCode))
            
    except Exception as e:
        logger = system.util.getLogger('EventStream.Zerobus')
        logger.error('Error sending batch to Zerobus: {}'.format(str(e)))
```

## Step 5: Configure Handler Failure Handling

In the Script Handler configuration:

- **Enabled**: ☑ Checked
- **Failure Mode**: `RETRY`
- **Retry Strategy**: `EXPONENTIAL`
- **Retry Count**: `3`
- **Retry Delay**: `1` second
- **Multiplier**: `2` (1s, 2s, 4s)
- **Max Delay**: `10000` ms
- **Retry Failure**: `ABORT`

This ensures temporary network issues don't cause data loss.

## Step 6: Test the Event Stream

1. **Save** the Event Stream configuration
2. **Enable** the Event Stream
3. Open the **Test Controls** panel (top right)
4. Click **Run All** to test with sample data
5. Check the **Status** panel for metrics:
   - Events Received
   - Events Filtered
   - Handler Execution times

## Step 7: Verify Data in Databricks

Query your Databricks table to confirm events are arriving:

```sql
SELECT 
  tag_path,
  numeric_value,
  quality,
  event_time,
  ingestion_timestamp
FROM ignition_demo.scada_data.tag_events
WHERE event_time >= current_timestamp() - INTERVAL 5 MINUTES
ORDER BY event_time DESC
LIMIT 100;
```

## Monitoring and Diagnostics

### Event Stream Metrics

View metrics in the Designer:
- **Status panel** in Event Stream editor
- **Test Controls** panel for manual testing

View metrics on Gateway:
- Navigate to: **Gateway** → **Config** → **Status** → **Services** → **Event Streams**
- View throughput, queue sizes, and error counts

### Module Diagnostics

Check module health:

```bash
curl http://localhost:8088/system/zerobus/diagnostics
```

Expected output:
```
=== Zerobus Module Diagnostics ===
Module Enabled: true

=== Zerobus Client Diagnostics ===
Initialized: true
Connected: true
Stream ID: stream_xxxxx

=== Tag Subscription Service Diagnostics ===
Running: true
Subscribed Tags: 0
Queue Size: 0/10000
Total Events Received: 1234
Total Events Dropped: 0
Total Batches Flushed: 45
```

Note: The module receives events via REST API from Event Streams.

## Optional: Add Filter Stage

To reduce event volume, add filtering:

```python
def filter(event, state):
    """
    Filter events before sending to Zerobus.
    Return True to keep event, False to drop it.
    """
    # Only process GOOD quality tags
    if event.metadata.get('quality', '') != 'GOOD':
        return False
    
    # Only process numeric values within range
    value = event.data
    if isinstance(value, (int, long, float)):
        if value < 0 or value > 10000:
            return False  # Out of range
    
    # Apply deadband (only send if changed by > 1%)
    tag_path = event.metadata.get('tagPath', '')
    last_value = state.get(tag_path, None)
    
    if last_value is not None:
        if isinstance(value, (int, long, float)):
            change_percent = abs((value - last_value) / last_value) if last_value != 0 else 1
            if change_percent < 0.01:  # Less than 1% change
                return False
    
    # Store value for next comparison
    state[tag_path] = value
    
    return True
```

## Optional: Add Transform Stage

To enrich or modify event data:

```python
def transform(event, state):
    """
    Transform event data before sending to Zerobus.
    Return modified event object.
    """
    # Add custom metadata
    event.data = {
        'original_value': event.data,
        'unit': 'PSI',  # Add engineering units
        'location': 'Plant A',  # Add location
        'equipment_id': 'PUMP-001'  # Add equipment ID
    }
    
    return event
```

## Performance Tuning

### For High-Frequency Tags (> 1000 events/sec)

Buffer settings:
- **Debounce**: `50` ms (faster batching)
- **Max Wait**: `500` ms (more frequent flushes)
- **Max Queue Size**: `50000` (larger buffer)

### For Low-Frequency Tags (< 100 events/sec)

Buffer settings:
- **Debounce**: `500` ms (more batching)
- **Max Wait**: `5000` ms (less frequent flushes)
- **Max Queue Size**: `5000` (smaller buffer)

### For Mixed Workloads

Create **multiple Event Streams**:
- One for high-frequency tags (fast-changing values)
- One for low-frequency tags (slow-changing values)
- Separate buffer tuning for each

## Troubleshooting

### Event Stream Not Receiving Events

Check:
1. Tag paths are correct (include provider and folder structure)
2. Tags exist and are readable
3. Trigger conditions are appropriate
4. Event Stream is enabled

### Events Not Reaching Zerobus Module

Check:
1. Module is installed and enabled
2. Gateway URL is correct (`http://localhost:8088`)
3. Script handler has no syntax errors
4. Check Gateway logs: `/usr/local/ignition/logs/wrapper.log`

### High Dropped Event Count

Solutions:
1. Increase `Max Queue Size` in buffer
2. Increase module queue size in configuration
3. Reduce event frequency with filters
4. Check Databricks connectivity (slow writes back up queue)

### Script Handler Errors

Common issues:
- **Import errors**: Ensure `system.net`, `system.util` are imported
- **Timeout errors**: Increase timeout in `httpPost` call
- **JSON encoding errors**: Ensure all values are JSON-serializable

Check logs:
- **Designer**: Console panel (Ctrl+Shift+C)
- **Gateway**: System → Console → Scripting

## Performance Optimization

### For High-Volume Deployments

When processing 10,000+ events/second:

1. **Increase Buffer Size**
   - Max Queue Size: 50,000+
   - Debounce: 50ms
   - Max Wait: 500ms

2. **Increase Module Batch Size**
   ```json
   {
     "batchSize": 1000,
     "batchFlushIntervalMs": 1000,
     "maxQueueSize": 100000
   }
   ```

3. **Tune JVM Heap**
   - Increase Gateway memory: 4GB+
   - Monitor GC pauses

4. **Multiple Event Streams**
   - Separate streams by criticality
   - Independent buffer tuning
   - Load distribution

## Support

For issues or questions:
- Check module diagnostics: `GET /system/zerobus/diagnostics`
- Check Gateway logs: `/usr/local/ignition/logs/wrapper.log`
- Review Event Stream metrics in Designer
- Contact support with diagnostics output

## Related Documentation

- [Ignition Event Streams Official Guide](https://docs.inductiveautomation.com/docs/8.3/ignition-modules/event-streams)
- [Module Configuration Guide](../README.md)
- [Handover Guide](HANDOVER.md)

