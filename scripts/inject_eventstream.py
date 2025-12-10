#!/usr/bin/env python3
"""
Inject Event Stream into Ignition Project JSON
This script automates Event Stream creation by modifying project JSON
"""

import json
import sys
import argparse
from pathlib import Path

def create_eventstream_resource():
    """Create Event Stream resource structure for Ignition project"""
    return {
        "scope": "A",
        "version": 1,
        "restricted": False,
        "overridable": True,
        "files": [
            "resource.json"
        ],
        "attributes": {
            "lastModification": {
                "actor": "admin",
                "timestamp": "2025-12-10T13:00:00Z"
            },
            "lastModificationSignature": ""
        }
    }

def create_eventstream_config(tag_paths, gateway_url="http://localhost:8088"):
    """Create Event Stream configuration"""
    return {
        "name": "ZerobusTagStream",
        "enabled": True,
        "source": {
            "type": "tag-event",
            "config": {
                "tagPaths": tag_paths,
                "triggers": {
                    "value": True,
                    "quality": False,
                    "timestamp": False
                }
            }
        },
        "encoder": {
            "type": "string",
            "config": {
                "charset": "UTF-8"
            }
        },
        "stages": {
            "filter": {
                "enabled": False
            },
            "transform": {
                "enabled": False
            }
        },
        "buffer": {
            "debounce": 100,
            "maxWait": 1000,
            "maxQueueSize": 10000,
            "overflow": "DROP_OLDEST"
        },
        "handlers": [
            {
                "type": "script",
                "enabled": True,
                "config": {
                    "script": f"""def onEventsReceived(events, state):
    import system.net
    import system.util
    
    batch = []
    for event in events:
        batch.append({{
            'tagPath': str(event.metadata.get('tagPath', '')),
            'tagProvider': str(event.metadata.get('provider', '')),
            'value': event.data,
            'quality': str(event.metadata.get('quality', 'GOOD')),
            'qualityCode': int(event.metadata.get('qualityCode', 192)),
            'timestamp': long(event.metadata.get('timestamp', system.date.now().time)),
            'dataType': type(event.data).__name__
        }})
    
    try:
        response = system.net.httpPost(
            url='{gateway_url}/system/zerobus/ingest/batch',
            contentType='application/json',
            postData=system.util.jsonEncode(batch),
            timeout=10000
        )
        if hasattr(response, 'statusCode') and response.statusCode == 200:
            logger = system.util.getLogger('EventStream.Zerobus')
            logger.info('Sent {{}} events'.format(len(batch)))
    except Exception as e:
        logger = system.util.getLogger('EventStream.Zerobus')
        logger.error('Error: {{}}'.format(str(e)))
"""
                },
                "failureMode": {
                    "mode": "RETRY",
                    "retryStrategy": "EXPONENTIAL",
                    "retryCount": 3,
                    "retryDelay": 1000,
                    "multiplier": 2.0,
                    "maxDelay": 10000,
                    "retryFailure": "ABORT"
                }
            }
        ]
    }

def inject_eventstream(project_json_path, tag_paths, output_path=None, gateway_url="http://localhost:8088"):
    """
    Inject Event Stream into Ignition project JSON
    
    Args:
        project_json_path: Path to exported project.json
        tag_paths: List of tag paths to monitor
        output_path: Output path (default: same as input with .modified.json)
        gateway_url: Gateway URL for script handler
    """
    print(f"Reading project: {project_json_path}")
    
    with open(project_json_path, 'r') as f:
        project = json.load(f)
    
    # Ensure resources section exists
    if 'resources' not in project:
        project['resources'] = {}
    
    # Create event-streams folder if it doesn't exist
    if 'event-streams' not in project['resources']:
        project['resources']['event-streams'] = {
            "scope": "A",
            "version": 1,
            "restricted": False,
            "overridable": True,
            "files": [],
            "attributes": {
                "lastModification": {
                    "actor": "admin",
                    "timestamp": "2025-12-10T13:00:00Z"
                }
            },
            "resources": {}
        }
    
    # Add ZerobusTagStream resource
    eventstream_name = "ZerobusTagStream"
    
    if 'resources' not in project['resources']['event-streams']:
        project['resources']['event-streams']['resources'] = {}
    
    project['resources']['event-streams']['resources'][eventstream_name] = {
        "scope": "A",
        "version": 1,
        "restricted": False,
        "overridable": True,
        "files": ["resource.json"],
        "attributes": {
            "lastModification": {
                "actor": "admin",
                "timestamp": "2025-12-10T13:00:00Z"
            }
        },
        "data": create_eventstream_config(tag_paths, gateway_url)
    }
    
    # Write output
    if output_path is None:
        output_path = Path(project_json_path).parent / f"{Path(project_json_path).stem}.modified.json"
    
    with open(output_path, 'w') as f:
        json.dump(project, f, indent=2)
    
    print(f"✓ Event Stream injected successfully")
    print(f"✓ Output written to: {output_path}")
    print(f"\nTo deploy:")
    print(f"  curl -X POST 'http://gateway:8088/data/project-import' \\")
    print(f"    -u 'admin:password' \\")
    print(f"    -F 'project=@{output_path}'")
    
    return output_path

def main():
    parser = argparse.ArgumentParser(
        description='Inject Event Stream into Ignition project JSON for automation'
    )
    parser.add_argument('project_json', help='Path to exported project.json file')
    parser.add_argument('--tags', nargs='+', required=True,
                      help='Tag paths to monitor (e.g., [Sample_Tags]Sine/Sine0)')
    parser.add_argument('--output', '-o', help='Output file path')
    parser.add_argument('--gateway-url', default='http://localhost:8088',
                      help='Gateway URL for script handler (default: http://localhost:8088)')
    
    args = parser.parse_args()
    
    inject_eventstream(
        args.project_json,
        args.tags,
        args.output,
        args.gateway_url
    )

if __name__ == "__main__":
    main()

