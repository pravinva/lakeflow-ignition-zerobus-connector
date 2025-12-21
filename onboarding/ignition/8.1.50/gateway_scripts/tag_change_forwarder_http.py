"""
Ignition 8.1.x Gateway Tag Change Script (HTTP ingest)

Use this only if you want to keep "Gateway Tag Change Script -> Module /ingest/batch" mode.
If you're using the module's **direct tag subscription** mode, you do NOT need this script.

Ignition 8.1 Tag Change script locals (verified from Ignition 8.1.50 common.jar):
  initialChange, event, newValue, currentValue, previousValue, executionCount
"""

import system.net
import system.util
import system.date

GATEWAY_URL = "http://localhost:8099"
INGEST_URL = GATEWAY_URL + "/system/zerobus/ingest/batch"

HTTP_TIMEOUT_MS = 10000

logger = system.util.getLogger("Gateway.ZerobusForwarder")

if not initialChange:
    try:
        tag_path_str = str(event.getTagPath())

        tag_provider = "default"
        if tag_path_str.startswith("[") and "]" in tag_path_str:
            tag_provider = tag_path_str[1:tag_path_str.index("]")]

        qv = currentValue
        value = getattr(qv, "value", qv)

        quality_obj = getattr(qv, "quality", None)
        quality_str = str(quality_obj) if quality_obj is not None else "GOOD"

        ts_obj = getattr(qv, "timestamp", None)
        ts_ms = long(ts_obj.getTime()) if ts_obj is not None and hasattr(ts_obj, "getTime") else long(system.date.now().getTime())

        payload = [{
            "tagPath": tag_path_str,
            "tagProvider": tag_provider,
            "value": value,
            "quality": quality_str,
            "qualityCode": 192,
            "timestamp": ts_ms,
            "dataType": type(value).__name__,
        }]

        client = system.net.httpClient(timeout=HTTP_TIMEOUT_MS)
        resp = client.post(
            INGEST_URL,
            data=system.util.jsonEncode(payload),
            headers={"Content-Type": "application/json"},
        )

        if resp.good:
            logger.info("Sent 1 event: %s" % tag_path_str)
        else:
            logger.warn("Send failed: HTTP %s %s" % (resp.statusCode, resp.text))

    except Exception as e:
        logger.error("Error in tag script: %s" % e)


