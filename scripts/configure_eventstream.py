#!/usr/bin/env python3
"""
Configure Existing Event Stream
Modifies Event Stream configuration directly in project files
"""

import json
import sys
import argparse
from pathlib import Path
import shutil
from datetime import datetime

def generate_handler_script(gateway_url, stream_name):
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

def find_project_path(ignition_data_dir, project_name):
    """Find project directory in Ignition data"""
    project_path = Path(ignition_data_dir) / "projects" / project_name
    if not project_path.exists():
        return None
    return project_path

def find_eventstream_dir(project_path, stream_name):
    """Find Event Stream directory"""
    # Primary location
    eventstream_dir = project_path / "com.inductiveautomation.eventstream" / "event-streams" / stream_name
    
    if eventstream_dir.exists():
        return eventstream_dir
    
    # Search for it
    for path in project_path.rglob(f"event-streams/{stream_name}"):
        if path.is_dir():
            return path
    
    return None

def configure_eventstream(project_path, stream_name, tag_paths, gateway_url,
                         debounce_ms, max_wait_ms, max_queue_size):
    """Configure Event Stream in project files"""
    
    # Find Event Stream directory
    stream_dir = find_eventstream_dir(project_path, stream_name)
    
    if not stream_dir:
        print(f"✗ Event Stream '{stream_name}' not found in project")
        print(f"  Please create it first in Designer:")
        print(f"    1. Open Designer")
        print(f"    2. Event Streams → Right-click → New Event Stream")
        print(f"    3. Name: {stream_name}")
        print(f"    4. Save (don't configure anything)")
        print(f"    5. Re-run this script")
        return False
    
    print(f"✓ Found Event Stream: {stream_dir}")
    
    # Create config.json with proper structure
    config = {
        "enabled": True,
        "source": {
            "type": "ignition.tagEvent",
            "config": {
                "paths": tag_paths,
                "changeTypes": ["VALUE"],
                "skipInitialValues": False
            }
        },
        "sourceEncoder": {
            "type": "ignition.string",
            "properties": {
                "encoding": "UTF-8"
            }
        },
        "handlers": [
            {
                "enabled": True,
                "type": "ignition.script",
                "config": {
                    "userCode": generate_handler_script(gateway_url, stream_name)
                },
                "failureStrategy": {
                    "type": "RETRY",
                    "retryPolicy": {
                        "type": "EXPONENTIAL",
                        "retryCount": 3,
                        "delayMs": 1000,
                        "maxDelayMs": 10000,
                        "multiplier": 2,
                        "abort": True
                    }
                }
            }
        ],
        "batch": {
            "debounceMs": debounce_ms,
            "maxWaitMs": max_wait_ms,
            "maxQueueSize": max_queue_size,
            "overflow": "DROP_OLDEST"
        },
        "filter": {
            "enabled": False,
            "userCode": "\treturn True"
        },
        "transform": {
            "enabled": False,
            "userCode": "\treturn event.data"
        },
        "transformEncoder": {
            "type": "ignition.jsonObject",
            "properties": {
                "encoding": "UTF-8"
            }
        },
        "onError": {
            "enabled": False,
            "userCode": ""
        }
    }
    
    config_path = stream_dir / "config.json"
    
    # Backup existing file
    if config_path.exists():
        backup_path = config_path.with_suffix('.json.backup')
        shutil.copy2(config_path, backup_path)
        print(f"✓ Backed up existing config: {backup_path}")
    
    # Write configuration
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✓ Configured Event Stream: {config_path}")
    
    # Update resource.json metadata
    resource_path = stream_dir / "resource.json"
    resource_data = {
        "scope": "G",
        "version": 1,
        "restricted": False,
        "overridable": True,
        "files": ["config.json"],
        "attributes": {
            "lastModification": {
                "actor": "Script",
                "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            }
        }
    }
    
    with open(resource_path, 'w') as f:
        json.dump(resource_data, f, indent=2)
    
    print(f"✓ Updated resource metadata")
    
    return True

def main():
    parser = argparse.ArgumentParser(
        description='Configure Event Stream directly in project files',
        epilog="""
Example:
  %(prog)s --name zerobus_gateway \\
    --project ZerobusDemo \\
    --tag-file configs/ramp_tags.txt \\
    --ignition-data /usr/local/ignition/data

Steps:
  1. Create empty Event Stream in Designer (just the name)
  2. Save and close Designer
  3. Run this script to configure it
  4. Open Designer - Event Stream is fully configured!
        """
    )
    
    parser.add_argument('--name', required=True,
                       help='Event Stream name (must exist in project)')
    parser.add_argument('--project', required=True,
                       help='Ignition project name')
    parser.add_argument('--ignition-data', default='/usr/local/ignition/data',
                       help='Ignition data directory (default: /usr/local/ignition/data)')
    
    tag_group = parser.add_mutually_exclusive_group(required=True)
    tag_group.add_argument('--tags', nargs='+',
                          help='Tag paths (space-separated)')
    tag_group.add_argument('--tag-file',
                          help='File with tag paths (one per line)')
    
    parser.add_argument('--gateway-url', default='http://localhost:8088',
                       help='Gateway URL for handler (default: http://localhost:8088)')
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
    
    if not tag_paths:
        print("✗ No tag paths specified", file=sys.stderr)
        sys.exit(1)
    
    print("=" * 70)
    print("Event Stream Configuration")
    print("=" * 70)
    print(f"Project: {args.project}")
    print(f"Stream: {args.name}")
    print(f"Tags: {len(tag_paths)}")
    print(f"Ignition Data: {args.ignition_data}")
    print("")
    
    # Find project
    project_path = find_project_path(args.ignition_data, args.project)
    if not project_path:
        print(f"✗ Project '{args.project}' not found in {args.ignition_data}/projects")
        print("")
        print("Available projects:")
        projects_dir = Path(args.ignition_data) / "projects"
        if projects_dir.exists():
            for p in projects_dir.iterdir():
                if p.is_dir():
                    print(f"  - {p.name}")
        sys.exit(1)
    
    print(f"✓ Found project: {project_path}")
    
    # Configure Event Stream
    success = configure_eventstream(
        project_path,
        args.name,
        tag_paths,
        args.gateway_url,
        args.debounce,
        args.max_wait,
        args.max_queue_size
    )
    
    if success:
        print("")
        print("=" * 70)
        print("✓ Configuration Complete!")
        print("=" * 70)
        print("")
        print("Next steps:")
        print("  1. Open Designer (or refresh if already open)")
        print(f"  2. Go to Event Streams → {args.name}")
        print("  3. Verify configuration:")
        print(f"     - Source: {len(tag_paths)} tags")
        print(f"     - Encoder: String (UTF-8)")
        print(f"     - Buffer: {args.debounce}ms debounce, {args.max_wait}ms max wait")
        print(f"     - Handler: Script (configured)")
        print("  4. Enable the Event Stream")
        print("")
        print("Tags configured:")
        for i, tag in enumerate(tag_paths[:5]):
            print(f"  - {tag}")
        if len(tag_paths) > 5:
            print(f"  ... and {len(tag_paths) - 5} more")
        print("")
    else:
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✗ Cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

