def onEventsReceived(events, state):
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
            logger = system.util.getLogger('EventStream.zerobusgateway')
            logger.info('Sent {} events'.format(len(batch)))
    except Exception as e:
        logger = system.util.getLogger('EventStream.zerobusgateway')
        logger.error('Error: {}'.format(str(e)))