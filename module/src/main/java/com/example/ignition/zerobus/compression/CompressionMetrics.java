package com.example.ignition.zerobus.compression;

import java.util.concurrent.atomic.AtomicLong;

/**
 * Thread-safe counters for SDT compression statistics.
 */
public class CompressionMetrics {

    private final AtomicLong eventsReceived = new AtomicLong();
    private final AtomicLong eventsEmitted = new AtomicLong();
    private final AtomicLong eventsSuppressed = new AtomicLong();
    private final AtomicLong heartbeatEmissions = new AtomicLong();
    private final AtomicLong qualityBreaks = new AtomicLong();
    private final AtomicLong nonNumericPassthrough = new AtomicLong();

    public void incrementReceived() {
        eventsReceived.incrementAndGet();
    }

    public void incrementEmitted() {
        eventsEmitted.incrementAndGet();
    }

    public void incrementSuppressed() {
        eventsSuppressed.incrementAndGet();
    }

    public void incrementHeartbeat() {
        heartbeatEmissions.incrementAndGet();
    }

    public void incrementQualityBreak() {
        qualityBreaks.incrementAndGet();
    }

    public void incrementNonNumericPassthrough() {
        nonNumericPassthrough.incrementAndGet();
    }

    public long getEventsReceived() {
        return eventsReceived.get();
    }

    public long getEventsEmitted() {
        return eventsEmitted.get();
    }

    public long getEventsSuppressed() {
        return eventsSuppressed.get();
    }

    public long getHeartbeatEmissions() {
        return heartbeatEmissions.get();
    }

    public long getQualityBreaks() {
        return qualityBreaks.get();
    }

    public long getNonNumericPassthrough() {
        return nonNumericPassthrough.get();
    }

    /**
     * Returns the compression ratio as a percentage (0-100).
     * A ratio of 90% means 90% of events were suppressed.
     * Returns 0.0 if no events have been received.
     */
    public double getCompressionRatio() {
        long received = eventsReceived.get();
        if (received == 0) {
            return 0.0;
        }
        long suppressed = eventsSuppressed.get();
        return (suppressed * 100.0) / received;
    }

    /**
     * Reset all counters to zero.
     */
    public void reset() {
        eventsReceived.set(0);
        eventsEmitted.set(0);
        eventsSuppressed.set(0);
        heartbeatEmissions.set(0);
        qualityBreaks.set(0);
        nonNumericPassthrough.set(0);
    }

    /**
     * Format a human-readable diagnostics string.
     */
    public String toDiagnosticString() {
        return String.format(
            "SDT Compression: received=%d, emitted=%d, suppressed=%d (%.1f%%), " +
            "heartbeats=%d, qualityBreaks=%d, nonNumericPassthrough=%d",
            eventsReceived.get(),
            eventsEmitted.get(),
            eventsSuppressed.get(),
            getCompressionRatio(),
            heartbeatEmissions.get(),
            qualityBreaks.get(),
            nonNumericPassthrough.get()
        );
    }
}
