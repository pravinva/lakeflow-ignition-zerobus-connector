package com.example.ignition.zerobus.compression;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

public class SwingDoorCompressorTest {

    private SwingDoorCompressor compressor;

    @BeforeEach
    void setUp() {
        // deviation=0.5, heartbeat=300s
        compressor = new SwingDoorCompressor(0.5, 300_000);
    }

    @Test
    void firstEventAlwaysEmitted() {
        SwingDoorCompressor.Result r = compressor.accept(10.0, 1000, "Good");
        assertEquals(SwingDoorCompressor.ResultType.EMIT, r.type);
        assertEquals(10.0, r.value);
        assertEquals(1000, r.timestampMs);
    }

    @Test
    void linearSignalSuppressed() {
        // With deviation=0.5, a perfectly linear signal (0,1,2,3,...) should
        // suppress all intermediate points because they fall within the corridor.
        compressor.accept(0.0, 1000, "Good"); // pivot (EMIT)

        // Points 1..4 are linear - all should be suppressed
        for (int i = 1; i <= 4; i++) {
            SwingDoorCompressor.Result r = compressor.accept(
                (double) i, 1000 + i * 1000, "Good"
            );
            assertEquals(SwingDoorCompressor.ResultType.SUPPRESS, r.type,
                "Linear point " + i + " should be suppressed");
        }
    }

    @Test
    void stepChangeBreaksCorridor() {
        compressor.accept(0.0, 1000, "Good"); // pivot

        // Flat values within deviation
        SwingDoorCompressor.Result r1 = compressor.accept(0.0, 2000, "Good");
        assertEquals(SwingDoorCompressor.ResultType.SUPPRESS, r1.type);

        SwingDoorCompressor.Result r2 = compressor.accept(0.0, 3000, "Good");
        assertEquals(SwingDoorCompressor.ResultType.SUPPRESS, r2.type);

        // Big step change breaks corridor - should emit held
        SwingDoorCompressor.Result r3 = compressor.accept(10.0, 4000, "Good");
        assertEquals(SwingDoorCompressor.ResultType.EMIT_HELD, r3.type);
        // The held point should be the last flat value (0.0 at 3000)
        assertEquals(0.0, r3.value);
        assertEquals(3000, r3.timestampMs);
    }

    @Test
    void heartbeatForcesEmission() {
        compressor = new SwingDoorCompressor(0.5, 5000); // 5s heartbeat

        compressor.accept(10.0, 1000, "Good"); // pivot

        // Suppress a point
        SwingDoorCompressor.Result r1 = compressor.accept(10.1, 2000, "Good");
        assertEquals(SwingDoorCompressor.ResultType.SUPPRESS, r1.type);

        // After heartbeat interval, should emit held
        SwingDoorCompressor.Result r2 = compressor.accept(10.2, 7000, "Good");
        assertEquals(SwingDoorCompressor.ResultType.EMIT_HELD, r2.type);
        // Held was the last suppressed: 10.1 at 2000
        assertEquals(10.1, r2.value);
        assertEquals(2000, r2.timestampMs);
    }

    @Test
    void qualityChangeResetsCompressor() {
        compressor.accept(10.0, 1000, "Good"); // pivot

        SwingDoorCompressor.Result r1 = compressor.accept(10.1, 2000, "Good");
        assertEquals(SwingDoorCompressor.ResultType.SUPPRESS, r1.type);

        // Quality change should trigger emit of held
        SwingDoorCompressor.Result r2 = compressor.accept(10.2, 3000, "Bad");
        assertEquals(SwingDoorCompressor.ResultType.EMIT_HELD, r2.type);
        assertEquals(10.1, r2.value);
        assertEquals(2000, r2.timestampMs);
    }

    @Test
    void duplicateTimestampsSuppressed() {
        compressor.accept(10.0, 1000, "Good"); // pivot

        SwingDoorCompressor.Result r = compressor.accept(10.5, 1000, "Good");
        assertEquals(SwingDoorCompressor.ResultType.SUPPRESS, r.type);
    }

    @Test
    void nanEmittedImmediately() {
        compressor.accept(10.0, 1000, "Good"); // pivot

        SwingDoorCompressor.Result r = compressor.accept(Double.NaN, 2000, "Good");
        assertEquals(SwingDoorCompressor.ResultType.EMIT, r.type);
        assertTrue(Double.isNaN(r.value));
    }

    @Test
    void infinityEmittedImmediately() {
        compressor.accept(10.0, 1000, "Good"); // pivot

        SwingDoorCompressor.Result r = compressor.accept(Double.POSITIVE_INFINITY, 2000, "Good");
        assertEquals(SwingDoorCompressor.ResultType.EMIT, r.type);
        assertTrue(Double.isInfinite(r.value));
    }

    @Test
    void resetClearsState() {
        compressor.accept(10.0, 1000, "Good");
        compressor.accept(10.1, 2000, "Good");

        compressor.reset();

        // After reset, next event should be emitted as a new pivot
        SwingDoorCompressor.Result r = compressor.accept(50.0, 5000, "Good");
        assertEquals(SwingDoorCompressor.ResultType.EMIT, r.type);
        assertEquals(50.0, r.value);
    }

    @Test
    void invalidDeviationThrows() {
        assertThrows(IllegalArgumentException.class, () ->
            new SwingDoorCompressor(-1.0, 300_000)
        );
    }

    @Test
    void invalidMaxIntervalThrows() {
        assertThrows(IllegalArgumentException.class, () ->
            new SwingDoorCompressor(0.5, 0)
        );
    }
}
