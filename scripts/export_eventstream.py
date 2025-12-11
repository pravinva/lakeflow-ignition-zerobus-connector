#!/usr/bin/env python3
"""
Export Ignition Event Stream configuration for automation
This script exports the Event Stream as a project resource
"""

import json
import os
import sys

# Event Stream Configuration Template
# This represents the ZerobusTagStream Event Stream
eventstream_config = {
    "name": "ZerobusTagStream",
    "enabled": True,
    "source": {
        "type": "TagEvent",
        "config": {
            "tagPaths": [
                "[Sample_Tags]Sine/Sine0",
                "[Sample_Tags]Sine/Sine1",
                "[Sample_Tags]Sine/Sine2",
                "[Sample_Tags]Realistic/Realistic0",
                "[Sample_Tags]Realistic/Realistic1"
            ],
            "triggers": {
                "valueChanged": True,
                "qualityChanged": False,
                "timestampChanged": False
            }
        }
    },
    "encoder": {
        "type": "String",
        "encoding": "UTF-8"
    },
    "filter": {
        "enabled": False,
        "script": ""
    },
    "transform": {
        "enabled": False,
        "script": ""
    },
    "buffer": {
        "debounceMs": 100,
        "maxWaitMs": 1000,
        "maxQueueSize": 10000,
        "overflow": "DROP_OLDEST"
    },
    "handlers": [
        {
            "type": "Script",
            "enabled": True,
            "failureMode": "RETRY",
            "retryStrategy": "EXPONENTIAL",
            "retryCount": 3,
            "retryDelayMs": 1000,
            "multiplier": 2,
            "maxDelayMs": 10000,
            "script": """def onEventsReceived(events, state):
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
        if hasattr(response, 'statusCode'):
            logger = system.util.getLogger('EventStream.Zerobus')
            if response.statusCode == 200:
                logger.info('Sent {} events'.format(len(batch)))
    except Exception as e:
        logger = system.util.getLogger('EventStream.Zerobus')
        logger.error('Error: {}'.format(str(e)))
"""
        }
    ]
}

def export_config(output_file):
    """Export Event Stream configuration to JSON file"""
    with open(output_file, 'w') as f:
        json.dump(eventstream_config, f, indent=2)
    print(f"Event Stream configuration exported to: {output_file}")
    print("\nTo import this configuration:")
    print("1. Open Ignition Designer")
    print("2. Go to Event Streams")
    print("3. Import this configuration manually")
    print("\nOr use the automation script: deploy_eventstream.sh")

if __name__ == "__main__":
    output_file = "eventstream-config.json"
    if len(sys.argv) > 1:
        output_file = sys.argv[1]
    
    export_config(output_file)

