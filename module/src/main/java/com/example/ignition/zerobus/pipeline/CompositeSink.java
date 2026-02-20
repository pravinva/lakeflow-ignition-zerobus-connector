package com.example.ignition.zerobus.pipeline;

import com.example.ignition.zerobus.proto.OTEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.ArrayList;
import java.util.List;

/**
 * CompositeSink - Wrapper that sends events to multiple sinks in parallel.
 *
 * Sends events to all enabled sinks, logging failures per sink.
 * Returns true if at least one sink successfully received the events.
 */
public final class CompositeSink implements EventSink {

    private static final Logger logger = LoggerFactory.getLogger(CompositeSink.class);

    private final List<NamedSink> sinks;

    /**
     * A sink with a name for logging purposes.
     */
    private record NamedSink(String name, EventSink sink) {}

    private CompositeSink(List<NamedSink> sinks) {
        this.sinks = new ArrayList<>(sinks);
    }

    /**
     * Builder for creating a CompositeSink with named sinks.
     */
    public static class Builder {
        private final List<NamedSink> sinks = new ArrayList<>();

        public Builder addSink(String name, EventSink sink) {
            if (sink != null) {
                sinks.add(new NamedSink(name, sink));
            }
            return this;
        }

        public CompositeSink build() {
            if (sinks.isEmpty()) {
                throw new IllegalStateException("CompositeSink requires at least one sink");
            }
            return new CompositeSink(sinks);
        }
    }

    public static Builder builder() {
        return new Builder();
    }

    @Override
    public boolean isReady() {
        // Ready if ANY sink is ready
        for (NamedSink ns : sinks) {
            if (ns.sink.isReady()) {
                return true;
            }
        }
        return false;
    }

    @Override
    public boolean tryEnsureReady() {
        boolean anyReady = false;
        for (NamedSink ns : sinks) {
            try {
                if (ns.sink.tryEnsureReady()) {
                    anyReady = true;
                }
            } catch (Exception e) {
                logger.warn("Failed to ensure {} sink is ready: {}", ns.name, e.getMessage());
            }
        }
        return anyReady;
    }

    @Override
    public boolean send(List<OTEvent> events) {
        if (events == null || events.isEmpty()) {
            return true;
        }

        boolean anySuccess = false;
        List<String> failures = new ArrayList<>();

        for (NamedSink ns : sinks) {
            try {
                boolean success = ns.sink.send(events);
                if (success) {
                    anySuccess = true;
                    logger.debug("Successfully sent {} events to {} sink", events.size(), ns.name);
                } else {
                    failures.add(ns.name);
                    logger.warn("Failed to send {} events to {} sink (returned false)", events.size(), ns.name);
                }
            } catch (Exception e) {
                failures.add(ns.name);
                logger.error("Exception sending {} events to {} sink: {}", events.size(), ns.name, e.getMessage(), e);
            }
        }

        if (!failures.isEmpty()) {
            logger.warn("Sink failures: {}", failures);
        }

        // Return true if at least one sink succeeded
        return anySuccess;
    }

    /**
     * Get the number of configured sinks.
     */
    public int getSinkCount() {
        return sinks.size();
    }

    /**
     * Get the names of configured sinks.
     */
    public List<String> getSinkNames() {
        List<String> names = new ArrayList<>();
        for (NamedSink ns : sinks) {
            names.add(ns.name);
        }
        return names;
    }
}
