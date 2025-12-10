#!/usr/bin/env python3
"""
Generic Event Stream Creator
Creates Event Stream configuration from command-line inputs
"""

import json
import sys
import argparse

def create_handler_script(gateway_url, stream_name):
    """Generate handler script with parameters"""
    logger_name = f"EventStream.{stream_name.replace('_', '').replace('-', '')}"
    
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
            logger = system.util.getLogger('{logger_name}')
            logger.info('Sent {{}} events'.format(len(batch)))
    except Exception as e:
        logger = system.util.getLogger('{logger_name}')
        logger.error('Error: {{}}'.format(str(e)))"""

def create_eventstream_config(name, tag_paths, gateway_url, debounce_ms, max_wait_ms, max_queue_size, batch_size):
    """Create Event Stream configuration"""
    return {
        "name": name,
        "description": f"Event Stream for {name}",
        "enabled": True,
        "source": {
            "type": "Tag Event",
            "tagPaths": tag_paths,
            "triggers": {
                "value": True,
                "quality": False,
                "timestamp": False
            }
        },
        "encoder": {
            "type": "String",
            "encoding": "UTF-8"
        },
        "filter": {
            "enabled": False
        },
        "transform": {
            "enabled": False
        },
        "buffer": {
            "debounceMs": debounce_ms,
            "maxWaitMs": max_wait_ms,
            "maxQueueSize": max_queue_size,
            "overflow": "DROP_OLDEST"
        },
        "handler": {
            "type": "Script",
            "enabled": True,
            "failureMode": {
                "mode": "RETRY",
                "strategy": "EXPONENTIAL",
                "retryCount": 3,
                "retryDelay": 1000,
                "multiplier": 2,
                "maxDelay": 10000
            },
            "script": create_handler_script(gateway_url, name)
        }
    }

def main():
    parser = argparse.ArgumentParser(
        description='Create Event Stream configuration for Zerobus',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create Event Stream with specific tags
  %(prog)s --name zerobus_gateway \\
    --tags "[Sample_Tags]Ramp/Ramp0" "[Sample_Tags]Ramp/Ramp1" \\
    --output configs/zerobus_gateway.json
  
  # Create with custom buffer settings
  %(prog)s --name production_stream \\
    --tags "[default]Equipment/Pump*/Temperature" \\
    --debounce 50 --max-wait 500 \\
    --batch-size 100
  
  # Use tag file
  %(prog)s --name my_stream --tag-file tags.txt
        """
    )
    
    # Required arguments
    parser.add_argument('--name', required=True,
                       help='Event Stream name (e.g., zerobus_gateway)')
    
    # Tag specification (mutually exclusive)
    tag_group = parser.add_mutually_exclusive_group(required=True)
    tag_group.add_argument('--tags', nargs='+',
                          help='Tag paths to monitor (space-separated)')
    tag_group.add_argument('--tag-file',
                          help='File containing tag paths (one per line)')
    
    # Optional arguments
    parser.add_argument('--gateway-url', default='http://localhost:8088',
                       help='Gateway URL (default: http://localhost:8088)')
    parser.add_argument('--debounce', type=int, default=100,
                       help='Buffer debounce in ms (default: 100)')
    parser.add_argument('--max-wait', type=int, default=1000,
                       help='Buffer max wait in ms (default: 1000)')
    parser.add_argument('--max-queue-size', type=int, default=10000,
                       help='Buffer max queue size (default: 10000)')
    parser.add_argument('--batch-size', type=int, default=50,
                       help='Batch size hint (default: 50)')
    parser.add_argument('--output', '-o',
                       help='Output file path (default: configs/<name>.json)')
    parser.add_argument('--script-output',
                       help='Separate script output file (optional)')
    
    args = parser.parse_args()
    
    # Read tags
    if args.tag_file:
        with open(args.tag_file, 'r') as f:
            tag_paths = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    else:
        tag_paths = args.tags
    
    if not tag_paths:
        print("Error: No tag paths specified", file=sys.stderr)
        sys.exit(1)
    
    print(f"Creating Event Stream: {args.name}")
    print(f"  Tags: {len(tag_paths)}")
    print(f"  Gateway: {args.gateway_url}")
    print(f"  Buffer: debounce={args.debounce}ms, maxWait={args.max_wait}ms")
    
    # Create configuration
    config = create_eventstream_config(
        args.name,
        tag_paths,
        args.gateway_url,
        args.debounce,
        args.max_wait,
        args.max_queue_size,
        args.batch_size
    )
    
    # Determine output path
    if args.output:
        output_path = args.output
    else:
        output_path = f"../configs/{args.name}.json"
    
    # Write configuration
    with open(output_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✓ Configuration written to: {output_path}")
    
    # Write script separately if requested
    if args.script_output:
        with open(args.script_output, 'w') as f:
            f.write(config['handler']['script'])
        print(f"✓ Handler script written to: {args.script_output}")
    
    # Print instructions
    print("")
    print("=" * 60)
    print("To use this configuration:")
    print("=" * 60)
    print("")
    print("1. Open Ignition Designer")
    print("2. Go to Event Streams")
    print("3. Create new Event Stream:")
    print(f"   - Name: {args.name}")
    print("   - Copy settings from: {output_path}")
    print("")
    print("Quick reference:")
    print(f"  Source: Tag Event → {len(tag_paths)} tags")
    print(f"  Encoder: String (UTF-8)")
    print(f"  Buffer: {args.debounce}ms debounce, {args.max_wait}ms max wait")
    print("  Handler: Script (see configuration file)")
    print("")
    print("Handler script can be copied from:")
    print(f"  {output_path} (in 'handler.script' field)")
    print("")
    
    # Show first few tags
    print("Tags to monitor:")
    for i, tag in enumerate(tag_paths[:5]):
        print(f"  - {tag}")
    if len(tag_paths) > 5:
        print(f"  ... and {len(tag_paths) - 5} more")
    print("")

if __name__ == "__main__":
    main()

