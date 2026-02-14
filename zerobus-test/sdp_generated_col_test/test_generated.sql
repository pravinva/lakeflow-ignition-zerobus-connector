-- Test A: Can SDP streaming tables use GENERATED ALWAYS AS?
-- Expected: likely fails -- SDP infers schema from SELECT, not from DDL column defs.
-- If it somehow works, this would mean the Delta writer feature 'generatedColumns'
-- is used, bumping the protocol to writer v4.

CREATE OR REFRESH STREAMING TABLE test_generated (
  event_id              STRING,
  event_time            BIGINT,
  tag_path              STRING,
  event_day             DATE GENERATED ALWAYS AS (CAST(FROM_UNIXTIME(event_time / 1000000) AS DATE))
)
AS SELECT
  event_id,
  event_time,
  tag_path
FROM STREAM(agl_demo.ot.zerobus_events)
LIMIT 100;
