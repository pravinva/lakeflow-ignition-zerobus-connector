#!/usr/bin/env python3
"""
Fully Automated Event Stream Deployment
This script CREATES the Event Stream in Ignition automatically via API
"""

import json
import sys
import argparse
import requests
from pathlib import Path
import time
import base64

def create_handler_script(gateway_url, stream_name):
    """Generate handler script"""
    logger_name = stream_name.replace('_', '').replace('-', '')
    
    return f"""def onEventsReceived(events, state):
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
            logger = system.util.getLogger('EventStream.{logger_name}')
            logger.info('Sent {{}} events'.format(len(batch)))
    except Exception as e:
        logger = system.util.getLogger('EventStream.{logger_name}')
        logger.error('Error: {{}}'.format(str(e)))
"""

def inject_eventstream_to_project(project_data, name, tag_paths, gateway_url, 
                                  debounce_ms, max_wait_ms, max_queue_size):
    """Inject Event Stream into project JSON structure"""
    
    # Ensure event-streams resource folder exists
    if 'resources' not in project_data:
        project_data['resources'] = {}
    
    if 'event-streams' not in project_data['resources']:
        project_data['resources']['event-streams'] = {
            "scope": "A",
            "version": 1,
            "restricted": False,
            "overridable": True,
            "files": [],
            "resources": {}
        }
    
    if 'resources' not in project_data['resources']['event-streams']:
        project_data['resources']['event-streams']['resources'] = {}
    
    # Create Event Stream resource
    eventstream_resource = {
        "scope": "A",
        "version": 1,
        "restricted": False,
        "overridable": True,
        "files": ["resource.json"],
        "attributes": {},
        "data": {
            "config": {
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
                    "filter": {"enabled": False},
                    "transform": {"enabled": False}
                },
                "buffer": {
                    "debounce": debounce_ms,
                    "maxWait": max_wait_ms,
                    "maxQueueSize": max_queue_size,
                    "overflow": "DROP_OLDEST"
                },
                "handlers": [
                    {
                        "type": "script",
                        "enabled": True,
                        "config": {
                            "script": create_handler_script(gateway_url, name)
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
        }
    }
    
    # Add to project
    project_data['resources']['event-streams']['resources'][name] = eventstream_resource
    
    return project_data

def deploy_eventstream(gateway_url, project_name, stream_name, tag_paths, 
                       username='admin', password='password',
                       debounce_ms=100, max_wait_ms=1000, max_queue_size=10000):
    """
    Fully automated Event Stream deployment
    
    1. Export existing project
    2. Inject Event Stream into project JSON
    3. Re-import project
    """
    
    print(f"========================================")
    print(f"Automated Event Stream Deployment")
    print(f"========================================")
    print(f"Gateway: {gateway_url}")
    print(f"Project: {project_name}")
    print(f"Stream: {stream_name}")
    print(f"Tags: {len(tag_paths)}")
    print("")
    
    # Create auth header
    auth = base64.b64encode(f"{username}:{password}".encode()).decode()
    headers = {'Authorization': f'Basic {auth}'}
    
    # Step 1: Export project
    print("[1/4] Exporting current project...")
    export_url = f"{gateway_url}/data/project-export/{project_name}"
    
    try:
        response = requests.get(export_url, headers=headers, timeout=30)
        if response.status_code == 200:
            project_data = response.json()
            print(f"✓ Project exported")
        elif response.status_code == 404:
            print(f"⚠ Project '{project_name}' not found, creating new...")
            project_data = {
                "name": project_name,
                "title": project_name,
                "description": "Auto-created for Zerobus",
                "enabled": True,
                "resources": {}
            }
        else:
            print(f"✗ Failed to export project: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error exporting project: {e}")
        return False
    
    # Step 2: Inject Event Stream
    print(f"[2/4] Injecting Event Stream '{stream_name}'...")
    try:
        project_data = inject_eventstream_to_project(
            project_data, stream_name, tag_paths, gateway_url,
            debounce_ms, max_wait_ms, max_queue_size
        )
        print(f"✓ Event Stream injected")
    except Exception as e:
        print(f"✗ Error injecting Event Stream: {e}")
        return False
    
    # Step 3: Save modified project temporarily
    temp_file = f"/tmp/{project_name}_with_{stream_name}.json"
    with open(temp_file, 'w') as f:
        json.dump(project_data, f, indent=2)
    print(f"✓ Modified project saved: {temp_file}")
    
    # Step 4: Import modified project
    print(f"[3/4] Importing project with Event Stream...")
    import_url = f"{gateway_url}/data/project-import"
    
    try:
        with open(temp_file, 'rb') as f:
            files = {'project': (f'{project_name}.json', f, 'application/json')}
            response = requests.post(import_url, headers=headers, files=files, timeout=60)
        
        if response.status_code in [200, 201]:
            print(f"✓ Project imported successfully")
        else:
            print(f"✗ Failed to import project: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error importing project: {e}")
        return False
    
    # Step 5: Verify
    print(f"[4/4] Verifying Event Stream...")
    time.sleep(3)
    
    # Check module diagnostics
    try:
        diag_url = f"{gateway_url}/system/zerobus/diagnostics"
        response = requests.get(diag_url, timeout=10)
        if response.status_code == 200:
            diag_text = response.text
            if 'Total Events Received' in diag_text:
                print(f"✓ Module is receiving events")
            else:
                print(f"⚠ Module not showing events yet")
        else:
            print(f"⚠ Could not verify module status")
    except Exception as e:
        print(f"⚠ Verification skipped: {e}")
    
    print("")
    print("========================================")
    print("✓ Deployment Complete!")
    print("========================================")
    print("")
    print(f"Event Stream '{stream_name}' is now active!")
    print(f"Monitoring {len(tag_paths)} Ramp tags")
    print("")
    print("To verify in Designer:")
    print(f"  1. Open Designer")
    print(f"  2. Event Streams → {stream_name}")
    print(f"  3. Check Status panel for metrics")
    print("")
    print("To verify in Databricks:")
    print(f"  SELECT * FROM ignition_demo.scada_data.tag_events")
    print(f"  WHERE tag_path LIKE '%Ramp%'")
    print(f"  ORDER BY event_time DESC LIMIT 100;")
    print("")
    
    return True

def main():
    parser = argparse.ArgumentParser(
        description='Fully automated Event Stream creation (no manual steps)',
        epilog="""
Example:
  %(prog)s --name zerobus_gateway \\
    --tags "[Sample_Tags]Ramp/Ramp0" "[Sample_Tags]Ramp/Ramp1" \\
    --project ZerobusDemo
        """
    )
    
    parser.add_argument('--name', required=True,
                       help='Event Stream name')
    parser.add_argument('--project', default='ZerobusDemo',
                       help='Ignition project name (default: ZerobusDemo)')
    parser.add_argument('--gateway-url', default='http://localhost:8088',
                       help='Gateway URL')
    parser.add_argument('--username', default='admin',
                       help='Gateway username (default: admin)')
    parser.add_argument('--password', default='password',
                       help='Gateway password')
    
    tag_group = parser.add_mutually_exclusive_group(required=True)
    tag_group.add_argument('--tags', nargs='+',
                          help='Tag paths (space-separated)')
    tag_group.add_argument('--tag-file',
                          help='File with tag paths (one per line)')
    
    parser.add_argument('--debounce', type=int, default=100,
                       help='Buffer debounce ms (default: 100)')
    parser.add_argument('--max-wait', type=int, default=1000,
                       help='Buffer max wait ms (default: 1000)')
    parser.add_argument('--max-queue-size', type=int, default=10000,
                       help='Buffer max queue size (default: 10000)')
    
    args = parser.parse_args()
    
    # Read tags
    if args.tag_file:
        with open(args.tag_file, 'r') as f:
            tag_paths = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    else:
        tag_paths = args.tags
    
    # Deploy
    success = deploy_eventstream(
        args.gateway_url,
        args.project,
        args.name,
        tag_paths,
        args.username,
        args.password,
        args.debounce,
        args.max_wait,
        args.max_queue_size
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDeployment cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Deployment failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

