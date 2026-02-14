package com.example.ignition.zerobus.compression;

/**
 * Swinging Door Trending (SDT) compressor for a single tag.
 *
 * Maintains a "pivot" (last transmitted point) and upper/lower slope bounds
 * forming a corridor. Each new point either tightens the corridor (suppressed)
 * or breaks it (previous held point emitted, pivot resets). Only applies to
 * numeric tags - booleans/strings should bypass this compressor.
 *
 * Thread-safety: instances are NOT thread-safe. External synchronization
 * (e.g., ConcurrentHashMap per-tag isolation) is expected.
 */
public class SwingDoorCompressor {

    /** Absolute deviation band (+/-) around a linear interpolation corridor. */
    private final double deviation;

    /** Maximum interval (ms) between transmitted points (heartbeat). */
    private final long maxIntervalMs;

    // --- Pivot state (last transmitted point) ---
    private double pivotValue;
    private long pivotTimestampMs;
    private boolean hasPivot;

    // --- Corridor slopes ---
    private double upperSlope;
    private double lowerSlope;

    // --- Held point (last suppressed candidate, emitted on corridor break) ---
    private double heldValue;
    private long heldTimestampMs;
    private String heldQuality;
    private boolean hasHeld;

    // --- Quality tracking ---
    private String lastQuality;

    public SwingDoorCompressor(double deviation, long maxIntervalMs) {
        if (deviation < 0) {
            throw new IllegalArgumentException("deviation must be >= 0");
        }
        if (maxIntervalMs <= 0) {
            throw new IllegalArgumentException("maxIntervalMs must be > 0");
        }
        this.deviation = deviation;
        this.maxIntervalMs = maxIntervalMs;
    }

    /**
     * Accept a new data point and decide what to do with it.
     *
     * @param value       numeric value
     * @param timestampMs epoch millis
     * @param quality     quality string (e.g., "Good_NonSpecific")
     * @return result indicating what the caller should do
     */
    public Result accept(double value, long timestampMs, String quality) {
        // NaN / Infinity always emit immediately and reset
        if (Double.isNaN(value) || Double.isInfinite(value)) {
            emitHeldAndReset(value, timestampMs, quality);
            return Result.emit(value, timestampMs, quality);
        }

        // First point ever: set as pivot, emit
        if (!hasPivot) {
            setPivot(value, timestampMs, quality);
            return Result.emit(value, timestampMs, quality);
        }

        // Quality change: emit held (if any), emit current, reset
        if (!qualityEquals(quality, lastQuality)) {
            Result result;
            if (hasHeld) {
                result = Result.emitHeld(heldValue, heldTimestampMs, heldQuality);
            } else {
                result = Result.emit(value, timestampMs, quality);
            }
            // Whether we emitted held or current, we reset pivot to current
            setPivot(value, timestampMs, quality);
            hasHeld = false;
            if (result.type == ResultType.EMIT_HELD) {
                // Caller should emit the held event, then also process current.
                // We hold current as next candidate.
                heldValue = value;
                heldTimestampMs = timestampMs;
                heldQuality = quality;
                hasHeld = true;
            }
            return result;
        }

        long dt = timestampMs - pivotTimestampMs;

        // Duplicate or out-of-order timestamp
        if (dt <= 0) {
            return Result.suppress();
        }

        // Heartbeat: max interval exceeded
        if (dt >= maxIntervalMs) {
            Result result;
            if (hasHeld) {
                result = Result.emitHeld(heldValue, heldTimestampMs, heldQuality);
                hasHeld = false;
                // Set held as new pivot, then hold current
                setPivot(result.value, result.timestampMs, result.quality);
                heldValue = value;
                heldTimestampMs = timestampMs;
                heldQuality = quality;
                hasHeld = true;
                recalculateSlopes(heldValue, heldTimestampMs);
            } else {
                setPivot(value, timestampMs, quality);
                result = Result.emit(value, timestampMs, quality);
            }
            return result;
        }

        // Calculate slopes from pivot +/- deviation to current point
        double slopeUpper = (value - (pivotValue + deviation)) / dt;
        double slopeLower = (value - (pivotValue - deviation)) / dt;

        if (!hasHeld) {
            // Second point after pivot: initialize corridor
            upperSlope = slopeUpper;
            lowerSlope = slopeLower;
            heldValue = value;
            heldTimestampMs = timestampMs;
            heldQuality = quality;
            hasHeld = true;
            lastQuality = quality;
            return Result.suppress();
        }

        // Check if doors have crossed (corridor broken)
        double newUpper = Math.min(upperSlope, slopeUpper);
        double newLower = Math.max(lowerSlope, slopeLower);

        if (newUpper < newLower) {
            // Corridor broken: emit held, set held as new pivot, hold current
            Result result = Result.emitHeld(heldValue, heldTimestampMs, heldQuality);
            setPivot(heldValue, heldTimestampMs, heldQuality);
            heldValue = value;
            heldTimestampMs = timestampMs;
            heldQuality = quality;
            hasHeld = true;
            recalculateSlopes(value, timestampMs);
            return result;
        }

        // Tighten corridor, hold current
        upperSlope = newUpper;
        lowerSlope = newLower;
        heldValue = value;
        heldTimestampMs = timestampMs;
        heldQuality = quality;
        lastQuality = quality;
        return Result.suppress();
    }

    /**
     * Reset the compressor state (e.g., on config change or tag unsubscribe).
     */
    public void reset() {
        hasPivot = false;
        hasHeld = false;
        lastQuality = null;
        upperSlope = 0;
        lowerSlope = 0;
    }

    private void setPivot(double value, long timestampMs, String quality) {
        pivotValue = value;
        pivotTimestampMs = timestampMs;
        lastQuality = quality;
        hasPivot = true;
        upperSlope = Double.POSITIVE_INFINITY;
        lowerSlope = Double.NEGATIVE_INFINITY;
    }

    private void recalculateSlopes(double value, long timestampMs) {
        long dt = timestampMs - pivotTimestampMs;
        if (dt <= 0) {
            upperSlope = Double.POSITIVE_INFINITY;
            lowerSlope = Double.NEGATIVE_INFINITY;
            return;
        }
        upperSlope = (value - (pivotValue + deviation)) / dt;
        lowerSlope = (value - (pivotValue - deviation)) / dt;
    }

    private void emitHeldAndReset(double value, long timestampMs, String quality) {
        // NaN/Inf path: just reset pivot to this point
        setPivot(value, timestampMs, quality);
        hasHeld = false;
    }

    private static boolean qualityEquals(String a, String b) {
        if (a == null && b == null) return true;
        if (a == null || b == null) return false;
        return a.equals(b);
    }

    // --- Result types ---

    public enum ResultType {
        /** Emit the current event as-is. */
        EMIT,
        /** Suppress (drop) the current event. */
        SUPPRESS,
        /** Emit the previously held event; current is now held. */
        EMIT_HELD
    }

    public static class Result {
        public final ResultType type;
        public final double value;
        public final long timestampMs;
        public final String quality;

        private Result(ResultType type, double value, long timestampMs, String quality) {
            this.type = type;
            this.value = value;
            this.timestampMs = timestampMs;
            this.quality = quality;
        }

        static Result emit(double value, long timestampMs, String quality) {
            return new Result(ResultType.EMIT, value, timestampMs, quality);
        }

        static Result suppress() {
            return new Result(ResultType.SUPPRESS, 0, 0, null);
        }

        static Result emitHeld(double value, long timestampMs, String quality) {
            return new Result(ResultType.EMIT_HELD, value, timestampMs, quality);
        }
    }
}
