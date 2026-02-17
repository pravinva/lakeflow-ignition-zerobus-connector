package com.example.ignition.zerobus.pipeline;

import com.example.ignition.zerobus.ConfigModel;
import com.example.ignition.zerobus.PostgresClientManager;
import com.example.ignition.zerobus.ZerobusClientManager;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Objects;

/**
 * Central wiring for the adapter -> buffer -> sink pipeline.
 *
 * Keeps construction decisions (disk spool vs memory, which sink, etc.) outside of services
 * like TagSubscriptionService so those services remain easy to test and reason about.
 */
public final class ZerobusPipelineFactory {

    private static final Logger logger = LoggerFactory.getLogger(ZerobusPipelineFactory.class);

    private ZerobusPipelineFactory() {}

    /**
     * Create pipeline components with support for both Zerobus and PostgreSQL sinks.
     *
     * @param config Configuration model
     * @param zerobusClientManager Zerobus client (may be null if Zerobus sink disabled)
     * @param postgresClientManager PostgreSQL client (may be null if PostgreSQL sink disabled)
     * @return Pipeline components with the appropriate sink configuration
     */
    public static PipelineComponents create(
            ConfigModel config,
            ZerobusClientManager zerobusClientManager,
            PostgresClientManager postgresClientManager) {

        Objects.requireNonNull(config, "config");

        OtEventMapper mapper = new OtEventMapper(config);
        StoreAndForwardBuffer buffer = new StoreAndForwardBuffer(config);
        EventSink sink = createSink(config, zerobusClientManager, postgresClientManager);

        return new PipelineComponents(mapper, buffer, sink);
    }

    /**
     * Backwards-compatible factory method (Zerobus only).
     */
    public static PipelineComponents create(ConfigModel config, ZerobusClientManager clientManager) {
        Objects.requireNonNull(config, "config");
        Objects.requireNonNull(clientManager, "clientManager");
        OtEventMapper mapper = new OtEventMapper(config);
        StoreAndForwardBuffer buffer = new StoreAndForwardBuffer(config);
        EventSink sink = new ZerobusEventSink(clientManager);
        return new PipelineComponents(mapper, buffer, sink);
    }

    /**
     * Create the appropriate sink based on configuration.
     */
    private static EventSink createSink(
            ConfigModel config,
            ZerobusClientManager zerobusClientManager,
            PostgresClientManager postgresClientManager) {

        boolean zerobusEnabled = config.isEnableZerobusSink() && zerobusClientManager != null;
        boolean postgresEnabled = config.isEnablePostgresSink() && postgresClientManager != null;

        logger.info("Creating sink - Zerobus enabled: {}, PostgreSQL enabled: {}", zerobusEnabled, postgresEnabled);

        if (zerobusEnabled && postgresEnabled) {
            // Both sinks enabled - use CompositeSink
            logger.info("Creating CompositeSink with Zerobus and PostgreSQL");
            return CompositeSink.builder()
                    .addSink("Zerobus", new ZerobusEventSink(zerobusClientManager))
                    .addSink("PostgreSQL", new PostgresEventSink(postgresClientManager))
                    .build();
        } else if (zerobusEnabled) {
            // Only Zerobus
            logger.info("Creating ZerobusEventSink");
            return new ZerobusEventSink(zerobusClientManager);
        } else if (postgresEnabled) {
            // Only PostgreSQL
            logger.info("Creating PostgresEventSink");
            return new PostgresEventSink(postgresClientManager);
        } else {
            // Neither enabled - this shouldn't happen due to validation, but provide a no-op sink
            logger.warn("No sinks enabled - creating no-op sink");
            return new NoOpSink();
        }
    }

    /**
     * No-op sink for when no sinks are enabled.
     */
    private static class NoOpSink implements EventSink {
        @Override
        public boolean isReady() {
            return false;
        }

        @Override
        public boolean tryEnsureReady() {
            return false;
        }

        @Override
        public boolean send(java.util.List<com.example.ignition.zerobus.proto.OTEvent> events) {
            logger.warn("NoOpSink: discarding {} events (no sinks configured)", events != null ? events.size() : 0);
            return false;
        }
    }

    public static final class PipelineComponents {
        public final OtEventMapper mapper;
        public final StoreAndForwardBuffer buffer;
        public final EventSink sink;

        public PipelineComponents(OtEventMapper mapper, StoreAndForwardBuffer buffer, EventSink sink) {
            this.mapper = Objects.requireNonNull(mapper, "mapper");
            this.buffer = Objects.requireNonNull(buffer, "buffer");
            this.sink = Objects.requireNonNull(sink, "sink");
        }
    }
}
