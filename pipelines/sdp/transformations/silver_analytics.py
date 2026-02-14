"""Silver to Gold analytics - health_scores materialized view.

SDP materialized view that computes per-asset health scores using z-score
anomaly detection on the live stream (enriched_tags). For simulated BESS,
this makes the story clear: we flag when tags deviate from their recent
behaviour. No ML model is used so the baseline is the actual simulator output.
"""

from pyspark import pipelines as dp
from pyspark.sql import functions as F

from agl_analytics.config import site_table, table
from agl_analytics.health import BATTERY_KEY_TAGS, WIND_KEY_TAGS


@dp.materialized_view(
    name="health_scores",
    comment="Per-asset health scores from z-score anomaly detection on live stream",
)
@dp.expect("valid_health_score", "health_score IS NULL OR (health_score >= 0 AND health_score <= 1)")
@dp.expect("has_asset_id", "asset_id IS NOT NULL AND length(trim(asset_id)) > 0")
def health_scores():
    """Materialized view: health scores per asset.

    Uses z-score anomaly detection on the last hour of enriched_tags.
    Health = 1.0 - (anomalous_key_tags / total_key_tags). Deviations
    from recent behaviour (rolling mean/stddev) are flagged; primary_risk_tag
    is the tag with the largest absolute z-score.
    """
    enriched = spark.read.table(table("enriched_tags"))  # noqa: F821
    assets = spark.read.table(site_table("agl_ot", "silver_asset_registry"))  # noqa: F821

    one_hour_ago = F.current_timestamp() - F.expr("INTERVAL 1 HOUR")
    recent = enriched.filter(F.col("window_start") >= one_hour_ago)

    tag_stats = recent.groupBy("asset_id", "signal_name").agg(
        F.avg("avg_value").alias("rolling_mean"),
        F.stddev("avg_value").alias("rolling_stddev"),
        F.last("avg_value").alias("current_value"),
    )

    with_assets = tag_stats.join(
        assets.select("asset_id", "asset_type"), on="asset_id", how="inner"
    )

    wind_tags = F.array([F.lit(t) for t in WIND_KEY_TAGS])
    battery_tags = F.array([F.lit(t) for t in BATTERY_KEY_TAGS])
    key_tags_col = F.when(
        F.col("asset_type") == "wind_turbine", wind_tags
    ).otherwise(battery_tags)

    key_tag_data = with_assets.filter(
        F.array_contains(key_tags_col, F.col("signal_name"))
    )

    zscore_data = key_tag_data.withColumn(
        "zscore",
        F.when(F.col("rolling_stddev") == 0, F.lit(0.0)).otherwise(
            (F.col("current_value") - F.col("rolling_mean"))
            / F.col("rolling_stddev")
        ),
    ).withColumn("is_anomalous", F.abs(F.col("zscore")) > 2.0)

    zscore_agg = zscore_data.groupBy("asset_id").agg(
        F.sum(F.when(F.col("is_anomalous"), 1).otherwise(0)).alias(
            "anomalous_count"
        ),
        F.count("*").alias("total_key_tags"),
        F.max_by("signal_name", F.abs(F.col("zscore"))).alias(
            "primary_risk_tag"
        ),
        F.max(F.abs(F.col("zscore"))).alias("max_zscore"),
        F.collect_list(
            F.when(F.col("is_anomalous"), F.col("signal_name"))
        ).alias("anomaly_tags_raw"),
    )

    zscore_scores = zscore_agg.withColumn(
        "zscore_health",
        F.when(F.col("total_key_tags") == 0, F.lit(1.0)).otherwise(
            1.0 - F.col("anomalous_count") / F.col("total_key_tags")
        ),
    )

    return zscore_scores.select(
        F.current_timestamp().alias("scored_at"),
        "asset_id",
        F.col("zscore_health").alias("health_score"),
        "primary_risk_tag",
        F.concat(
            F.lit("Primary risk: "),
            F.coalesce(F.col("primary_risk_tag"), F.lit("unknown")),
            F.lit(" (z-score: "),
            F.round(F.col("max_zscore"), 1),
            F.lit(")"),
        ).alias("risk_description"),
        F.filter(F.col("anomaly_tags_raw"), lambda x: x.isNotNull()).alias(
            "anomaly_tags"
        ),
        F.lit(None).cast("double").alias("estimated_hours_to_failure"),
    )
