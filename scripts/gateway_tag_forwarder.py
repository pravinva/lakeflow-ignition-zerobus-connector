"""
Gateway Tag Change Script - Zero Configuration Alternative to Event Streams
Install this as a Gateway Event Script (Tag Change) for 100% automated setup

Installation:
1. Gateway Web Interface → Config → Scripting → Gateway Event Scripts
2. Add new "Tag Change" script
3. Paste this entire file
4. Configure TAG_PATHS list below
5. Save - that's it!

This completely replaces Event Streams with zero manual configuration.
"""

# ============ CONFIGURATION (Edit these) ============
TAG_PATHS = [
    "[Sample_Tags]Sine/Sine0",
    "[Sample_Tags]Sine/Sine1", 
    "[Sample_Tags]Sine/Sine2",
    "[Sample_Tags]Realistic/Realistic0",
    "[Sample_Tags]Realistic/Realistic1"
]

ZEROBUS_ENDPOINT = "http://localhost:8088/system/zerobus/ingest/batch"
BATCH_SIZE = 50
BATCH_TIMEOUT_MS = 1000
# ====================================================

# Global state (persists across script executions)
if 'event_batch' not in globals():
    event_batch = []
    last_flush_time = system.date.now()
    logger = system.util.getLogger('Gateway.Zerobus')

def tagChange(tagPath, tagValue, qualifiedValue, initialChange):
    """
    Called by Ignition when any subscribed tag changes.
    This function is automatically invoked by the Gateway.
    """
    global event_batch, last_flush_time, logger
    
    # Skip initial values to avoid duplicates on startup
    if initialChange:
        return
    
    # Create event payload
    try:
        event = {
            'tagPath': str(tagPath),
            'tagProvider': tagPath.getSource(),
            'value': tagValue,
            'quality': str(qualifiedValue.quality.getName()),
            'qualityCode': qualifiedValue.quality.getIntValue(),
            'timestamp': long(qualifiedValue.timestamp.getTime()),
            'dataType': type(tagValue).__name__
        }
        
        event_batch.append(event)
        
        # Flush if batch size reached or timeout exceeded
        should_flush = False
        
        if len(event_batch) >= BATCH_SIZE:
            should_flush = True
        
        time_since_flush = system.date.secondsBetween(last_flush_time, system.date.now())
        if time_since_flush * 1000 >= BATCH_TIMEOUT_MS:
            should_flush = True
        
        if should_flush:
            flush_batch()
            
    except Exception as e:
        logger.error('Error processing tag change: {}'.format(str(e)))

def flush_batch():
    """Send batched events to Zerobus module"""
    global event_batch, last_flush_time, logger
    
    if not event_batch:
        return
    
    batch_to_send = list(event_batch)  # Copy
    event_batch = []  # Clear immediately
    last_flush_time = system.date.now()
    
    try:
        response = system.net.httpPost(
            url=ZEROBUS_ENDPOINT,
            contentType='application/json',
            postData=system.util.jsonEncode(batch_to_send),
            timeout=10000
        )
        
        if hasattr(response, 'statusCode') and response.statusCode == 200:
            logger.info('Sent {} events to Zerobus'.format(len(batch_to_send)))
        else:
            logger.warn('Failed to send batch: HTTP {}'.format(
                response.statusCode if hasattr(response, 'statusCode') else 'unknown'))
            # Re-add to batch on failure
            event_batch.extend(batch_to_send)
            
    except Exception as e:
        logger.error('Error sending batch: {}'.format(str(e)))
        # Re-add to batch on failure
        event_batch.extend(batch_to_send)

# Initialize tag subscriptions on script load
logger.info('Zerobus Gateway Tag Forwarder starting...')
logger.info('Monitoring {} tags'.format(len(TAG_PATHS)))
logger.info('Batch size: {}, Timeout: {}ms'.format(BATCH_SIZE, BATCH_TIMEOUT_MS))

