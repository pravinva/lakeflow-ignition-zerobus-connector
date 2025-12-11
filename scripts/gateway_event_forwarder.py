"""
Gateway Startup Script: Event Stream Alternative
This script can be added to Gateway > System > Scripts > Startup Scripts
to forward tag changes to Zerobus without using Event Streams.

Location: Gateway Web Interface > Config > Scripting > Startup Scripts
"""

from com.inductiveautomation.ignition.common.script import JythonExecManager
from com.inductiveautomation.ignition.common.tags.model.event import TagChangeListener
import system.net
import system.util

# Configuration
ZEROBUS_ENDPOINT = "http://localhost:8088/system/zerobus/ingest/batch"
TAG_PATHS = [
    "[Sample_Tags]Sine/Sine0",
    "[Sample_Tags]Sine/Sine1", 
    "[Sample_Tags]Realistic/Realistic0",
    "[Sample_Tags]Realistic/Realistic1"
]
BATCH_SIZE = 100
BATCH_TIMEOUT_MS = 1000

# Global batch buffer
event_batch = []
last_flush_time = system.date.now()

def flush_batch():
    """Send batched events to Zerobus module"""
    global event_batch, last_flush_time
    
    if not event_batch:
        return
    
    try:
        response = system.net.httpPost(
            url=ZEROBUS_ENDPOINT,
            contentType='application/json',
            postData=system.util.jsonEncode(event_batch),
            timeout=10000
        )
        
        if response.statusCode == 200:
            result = system.util.jsonDecode(response.text)
            print "[Zerobus] Batch sent: {} accepted, {} dropped".format(
                result.get('accepted', 0),
                result.get('dropped', 0)
            )
        else:
            print "[Zerobus] Failed to send batch: HTTP {}".format(response.statusCode)
        
        # Clear batch after successful send
        event_batch = []
        last_flush_time = system.date.now()
        
    except Exception as e:
        print "[Zerobus] Error sending batch: {}".format(str(e))

def on_tag_change(tag_path, value, quality, timestamp):
    """Handle tag change event"""
    global event_batch, last_flush_time
    
    # Create event payload
    event = {
        'tagPath': str(tag_path),
        'tagProvider': tag_path.getSource(),
        'value': value,
        'quality': quality.getName(),
        'qualityCode': quality.getIntValue(),
        'timestamp': timestamp.getTime(),
        'dataType': type(value).__name__
    }
    
    # Add to batch
    event_batch.append(event)
    
    # Check if we should flush
    should_flush = False
    
    # Flush if batch size reached
    if len(event_batch) >= BATCH_SIZE:
        should_flush = True
    
    # Flush if timeout reached
    time_since_flush = system.date.secondsBetween(last_flush_time, system.date.now())
    if time_since_flush * 1000 >= BATCH_TIMEOUT_MS:
        should_flush = True
    
    if should_flush:
        flush_batch()

# Subscribe to tags
def subscribe_to_tags():
    """Subscribe to configured tags"""
    tag_manager = system.tag
    
    for tag_path in TAG_PATHS:
        try:
            # Subscribe with callback
            system.tag.subscribe(
                tagPath=tag_path,
                callback=lambda event: on_tag_change(
                    event.tagPath,
                    event.value.value,
                    event.value.quality,
                    event.value.timestamp
                )
            )
            print "[Zerobus] Subscribed to: {}".format(tag_path)
        except Exception as e:
            print "[Zerobus] Failed to subscribe to {}: {}".format(tag_path, str(e))
    
    print "[Zerobus] Tag subscription complete. {} tags subscribed.".format(len(TAG_PATHS))

# Initialize on startup
print "[Zerobus] Starting tag forwarder..."
subscribe_to_tags()
print "[Zerobus] Tag forwarder started successfully"

