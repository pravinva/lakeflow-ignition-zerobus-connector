package com.example.ignition.zerobus.compression;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

public class CompressionMetricsTest {

    private CompressionMetrics metrics;

    @BeforeEach
    void setUp() {
        metrics = new CompressionMetrics();
    }

    @Test
    void countersStartAtZero() {
        assertEquals(0, metrics.getEventsReceived());
        assertEquals(0, metrics.getEventsEmitted());
        assertEquals(0, metrics.getEventsSuppressed());
        assertEquals(0, metrics.getHeartbeatEmissions());
        assertEquals(0, metrics.getQualityBreaks());
        assertEquals(0, metrics.getNonNumericPassthrough());
    }

    @Test
    void incrementCounters() {
        metrics.incrementReceived();
        metrics.incrementReceived();
        metrics.incrementEmitted();
        metrics.incrementSuppressed();
        metrics.incrementHeartbeat();
        metrics.incrementQualityBreak();
        metrics.incrementNonNumericPassthrough();

        assertEquals(2, metrics.getEventsReceived());
        assertEquals(1, metrics.getEventsEmitted());
        assertEquals(1, metrics.getEventsSuppressed());
        assertEquals(1, metrics.getHeartbeatEmissions());
        assertEquals(1, metrics.getQualityBreaks());
        assertEquals(1, metrics.getNonNumericPassthrough());
    }

    @Test
    void compressionRatioZeroWhenNoEvents() {
        assertEquals(0.0, metrics.getCompressionRatio());
    }

    @Test
    void compressionRatioCalculation() {
        // 10 received, 8 suppressed = 80% compression
        for (int i = 0; i < 10; i++) {
            metrics.incrementReceived();
        }
        for (int i = 0; i < 8; i++) {
            metrics.incrementSuppressed();
        }

        assertEquals(80.0, metrics.getCompressionRatio(), 0.01);
    }

    @Test
    void resetClearsAllCounters() {
        metrics.incrementReceived();
        metrics.incrementEmitted();
        metrics.incrementSuppressed();
        metrics.incrementHeartbeat();
        metrics.incrementQualityBreak();
        metrics.incrementNonNumericPassthrough();

        metrics.reset();

        assertEquals(0, metrics.getEventsReceived());
        assertEquals(0, metrics.getEventsEmitted());
        assertEquals(0, metrics.getEventsSuppressed());
        assertEquals(0, metrics.getHeartbeatEmissions());
        assertEquals(0, metrics.getQualityBreaks());
        assertEquals(0, metrics.getNonNumericPassthrough());
        assertEquals(0.0, metrics.getCompressionRatio());
    }

    @Test
    void diagnosticStringContainsAllFields() {
        metrics.incrementReceived();
        metrics.incrementEmitted();
        String diag = metrics.toDiagnosticString();

        assertTrue(diag.contains("received=1"));
        assertTrue(diag.contains("emitted=1"));
        assertTrue(diag.contains("suppressed=0"));
        assertTrue(diag.contains("heartbeats=0"));
        assertTrue(diag.contains("qualityBreaks=0"));
        assertTrue(diag.contains("nonNumericPassthrough=0"));
    }
}
