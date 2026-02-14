"""Health scoring module - z-score based anomaly detection.

Implements FR-201 from APP-PRD.md: Z-score based anomaly detection per asset.
"""

# Key monitoring tags per asset type (from APP-PRD.md FR-105)
# These map to signal_name in silver_signal_mapping
WIND_KEY_TAGS = [
    "nacelle/temperature_c",
    "generator/power_kw",
    "grid/frequency_hz",
    "rotor/wind_speed_ms",
]

# AGL BESS key tags (match silver_signal_mapping signal_name values)
BATTERY_KEY_TAGS = [
    "max_rack_temp_c",       # Battery rack temperature
    "soc_pct",               # State of charge
    "ambient_temp_c",        # Ambient temperature
    "bess_active_power_mw",  # Active power output
]

# Alternative tag names for PRD-schema compatibility (when using raw_tags directly)
BATTERY_KEY_TAGS_PRD = [
    "battery/temperature_c",
    "battery/soc_pct",
    "thermal/coolant_temp_c",
    "inverter/efficiency_pct",
]


def compute_zscore(value: float, mean: float, stddev: float) -> float:
    """Compute z-score for a value given mean and standard deviation.

    Args:
        value: Current value to score
        mean: Rolling mean for the tag
        stddev: Rolling standard deviation for the tag

    Returns:
        Z-score. Returns 0.0 if stddev is 0 to avoid division by zero.
    """
    if stddev == 0.0:
        return 0.0
    return (value - mean) / stddev


def is_anomalous(zscore: float, threshold: float = 2.0) -> bool:
    """Check if a z-score indicates an anomaly.

    Args:
        zscore: The z-score to check
        threshold: Threshold for anomaly detection (default 2.0 = 2 sigma)

    Returns:
        True if abs(zscore) > threshold, indicating anomaly.
    """
    return abs(zscore) > threshold


def compute_health_score(anomalous_count: int, total_tag_count: int) -> float:
    """Compute health score based on anomalous tag ratio.

    Health score = 1.0 - (anomalous_count / total_tag_count), clamped to [0.0, 1.0].

    Args:
        anomalous_count: Number of tags currently anomalous
        total_tag_count: Total number of key tags being monitored

    Returns:
        Health score from 0.0 (critical) to 1.0 (healthy).
    """
    if total_tag_count == 0:
        return 1.0
    ratio = anomalous_count / total_tag_count
    score = 1.0 - ratio
    return max(0.0, min(1.0, score))


def identify_primary_risk_tag(tag_zscores: dict[str, float]) -> tuple[str, float]:
    """Identify the tag with the highest absolute z-score deviation.

    Args:
        tag_zscores: Dictionary mapping tag names to their z-scores

    Returns:
        Tuple of (tag_name, zscore) for the tag with highest abs(zscore).
        Returns ("", 0.0) if dict is empty.
    """
    if not tag_zscores:
        return ("", 0.0)

    primary_tag = max(tag_zscores.keys(), key=lambda t: abs(tag_zscores[t]))
    return (primary_tag, tag_zscores[primary_tag])


def generate_risk_description(
    primary_tag: str,
    zscore: float,
    current_value: float,
    expected_range: tuple[float, float],
) -> str:
    """Generate a human-readable risk description.

    Args:
        primary_tag: Name of the tag driving the risk
        zscore: Z-score of the primary tag
        current_value: Current value of the tag
        expected_range: Tuple of (min, max) expected values

    Returns:
        Human-readable description string.
    """
    direction = "above" if zscore > 0 else "below"
    return (
        f"Primary risk: {primary_tag} at {current_value:.1f} "
        f"(expected {expected_range[0]:.0f}-{expected_range[1]:.0f}, "
        f"z-score: {zscore:.1f}, {direction} normal range)"
    )


def get_key_tags(asset_type: str) -> list[str]:
    """Get the key monitoring tags for an asset type.

    Args:
        asset_type: Type of asset ("wind_turbine" or "battery")

    Returns:
        List of key tag names to monitor for this asset type.
        Returns empty list for unknown asset types.
    """
    if asset_type == "wind_turbine":
        return WIND_KEY_TAGS.copy()
    elif asset_type == "battery":
        return BATTERY_KEY_TAGS.copy()
    return []
