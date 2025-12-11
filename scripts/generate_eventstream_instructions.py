#!/usr/bin/env python3
"""
Generate Event Stream Setup Instructions
Creates copy-paste ready configuration from inputs
"""

import argparse
import sys

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
        logger.error('Error: {{}}'.format(str(e)))"""

def main():
    parser = argparse.ArgumentParser(description='Generate Event Stream setup instructions')
    parser.add_argument('--name', required=True, help='Event Stream name')
    parser.add_argument('--tags', nargs='+', help='Tag paths')
    parser.add_argument('--tag-file', help='File with tag paths')
    parser.add_argument('--gateway-url', default='http://localhost:8088')
    parser.add_argument('--debounce', type=int, default=100)
    parser.add_argument('--max-wait', type=int, default=1000)
    parser.add_argument('--max-queue-size', type=int, default=10000)
    
    args = parser.parse_args()
    
    # Read tags
    if args.tag_file:
        with open(args.tag_file, 'r') as f:
            tag_paths = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    elif args.tags:
        tag_paths = args.tags
    else:
        print("Error: Specify --tags or --tag-file", file=sys.stderr)
        sys.exit(1)
    
    # Generate instructions
    print("=" * 70)
    print(f"Event Stream Setup: {args.name}")
    print("=" * 70)
    print("")
    print("STEP 1: Create Event Stream in Designer")
    print("-" * 70)
    print("1. Open Ignition Designer")
    print("2. Project Browser → Event Streams")
    print("3. Right-click → New Event Stream")
    print(f"4. Name: {args.name}")
    print("")
    
    print("STEP 2: Configure Source (Tag Event)")
    print("-" * 70)
    print("Click Source stage, then:")
    print("  Type: Tag Event")
    print("  Tag Paths (copy these):")
    for tag in tag_paths:
        print(f"    {tag}")
    print("  Triggers: ☑ Value Changed")
    print("")
    
    print("STEP 3: Configure Encoder")
    print("-" * 70)
    print("Click Encoder stage, then:")
    print("  Type: String")
    print("  Encoding: UTF-8")
    print("")
    
    print("STEP 4: Configure Buffer")
    print("-" * 70)
    print("Click Buffer stage, then:")
    print(f"  Debounce: {args.debounce} ms")
    print(f"  Max Wait: {args.max_wait} ms")
    print(f"  Max Queue Size: {args.max_queue_size}")
    print("  Overflow: DROP_OLDEST")
    print("")
    
    print("STEP 5: Add Script Handler")
    print("-" * 70)
    print("Click 'Add Handler' → Script, then:")
    print("  Failure Mode: RETRY")
    print("  Retry Strategy: EXPONENTIAL")
    print("  Retry Count: 3")
    print("")
    print("Copy this script:")
    print("")
    print("```python")
    print(generate_handler_script(args.gateway_url, args.name))
    print("```")
    print("")
    
    print("STEP 6: Save and Enable")
    print("-" * 70)
    print("1. Click Save")
    print("2. Toggle 'Enabled' switch")
    print("")
    
    print("STEP 7: Verify")
    print("-" * 70)
    print("Check Status panel in Designer - should see:")
    print("  Events Received: (incrementing)")
    print("  Handler Execution: (showing times)")
    print("")
    print("Check module:")
    print(f"  curl {args.gateway_url}/system/zerobus/diagnostics")
    print("")
    print("=" * 70)
    print(f"Setup complete for: {args.name}")
    print("=" * 70)

if __name__ == "__main__":
    main()

