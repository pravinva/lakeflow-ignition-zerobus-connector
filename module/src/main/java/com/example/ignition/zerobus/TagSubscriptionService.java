package com.example.ignition.zerobus;

import com.example.ignition.zerobus.web.TagEventPayload;
import com.inductiveautomation.ignition.gateway.model.GatewayContext;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicLong;

/**
 * TagSubscriptionService - Event-driven tag event processing service.
 * 
 * This service receives tag events from Ignition Event Streams via REST API:
 * - Receives tag events from Event Stream Script handlers
 * - Queues events with backpressure management
 * - Batches events by count and time window
 * - Applies rate limiting
 * - Sends batches to ZerobusClientManager
 * 
 * NOTE: This service does NOT poll tags. It is purely event-driven.
 * Configure Ignition Event Streams with Tag Event sources to push events to this service.
 * See docs/EVENT_STREAMS_SETUP.md for configuration guide.
 */
public class TagSubscriptionService {
    
    private static final Logger logger = LoggerFactory.getLogger(TagSubscriptionService.class);
    
    private final GatewayContext gatewayContext;
    private final ZerobusClientManager zerobusClientManager;
    private final ConfigModel config;
    
    private AtomicBoolean running = new AtomicBoolean(false);
    private BlockingQueue<TagEvent> eventQueue;
    private ScheduledExecutorService scheduledExecutor;
    private ExecutorService workerExecutor;
    
    // Metrics
    private AtomicLong totalEventsReceived = new AtomicLong(0);
    private AtomicLong totalEventsDropped = new AtomicLong(0);
    private AtomicLong totalBatchesFlushed = new AtomicLong(0);
    
    // Rate limiting
    private volatile long lastFlushTime = 0;
    private AtomicLong eventsThisSecond = new AtomicLong(0);
    private volatile long currentSecond = 0;
    
    /**
     * Constructor.
     * 
     * @param gatewayContext Ignition Gateway context
     * @param zerobusClientManager Zerobus client for sending events
     * @param config Configuration model
     */
    public TagSubscriptionService(GatewayContext gatewayContext, 
                                   ZerobusClientManager zerobusClientManager,
                                   ConfigModel config) {
        this.gatewayContext = gatewayContext;
        this.zerobusClientManager = zerobusClientManager;
        this.config = config;
        
        // Initialize event queue with configured max size
        this.eventQueue = new LinkedBlockingQueue<>(config.getMaxQueueSize());
    }
    
    /**
     * Start the tag event processing service.
     * 
     * NOTE: This service is event-driven only. It does not poll tags.
     * Configure Ignition Event Streams to send events to /system/zerobus/ingest endpoint.
     */
    public void start() {
        if (running.get()) {
            logger.warn("TagSubscriptionService already running");
            return;
        }
        
        logger.info("Starting Zerobus Event Processing Service...");
        logger.info("Mode: Event-driven (no polling)");
        logger.info("Listening for events on: POST /system/zerobus/ingest");
        
        try {
            running.set(true);
            
            // Create scheduled executor for periodic flushing
            scheduledExecutor = Executors.newSingleThreadScheduledExecutor(r -> {
                Thread t = new Thread(r, "Zerobus-Flush-Thread");
                t.setDaemon(true);
                return t;
            });
            
            // Schedule periodic flushing of queued events
            scheduledExecutor.scheduleAtFixedRate(
                this::flushBatch,
                config.getBatchFlushIntervalMs(),
                config.getBatchFlushIntervalMs(),
                TimeUnit.MILLISECONDS
            );
            
            logger.info("Event processing service started successfully");
            logger.info("  Event queue capacity: {}", config.getMaxQueueSize());
            logger.info("  Batch size: {}", config.getBatchSize());
            logger.info("  Flush interval: {}ms", config.getBatchFlushIntervalMs());
            logger.info("");
            logger.info("Configure Event Streams in Ignition Designer to push events:");
            logger.info("  Source: Tag Event");
            logger.info("  Handler: Script → POST to http://localhost:8088/system/zerobus/ingest");
            logger.info("  See docs/EVENT_STREAMS_SETUP.md for complete guide");
            
        } catch (Exception e) {
            logger.error("Failed to start event processing service", e);
            running.set(false);
            throw new RuntimeException("Failed to start event processing service", e);
        }
    }
    
    /**
     * Shutdown the event processing service.
     */
    public void shutdown() {
        if (!running.get()) {
            return;
        }
        
        logger.info("Shutting down event processing service...");
        
        running.set(false);
        
        try {
            // Flush any remaining events
            flushBatch();
            
            // Shutdown executors
            if (scheduledExecutor != null) {
                scheduledExecutor.shutdown();
                if (!scheduledExecutor.awaitTermination(5, TimeUnit.SECONDS)) {
                    scheduledExecutor.shutdownNow();
                }
            }
            
            if (workerExecutor != null && !workerExecutor.isShutdown()) {
                workerExecutor.shutdown();
                if (!workerExecutor.awaitTermination(5, TimeUnit.SECONDS)) {
                    workerExecutor.shutdownNow();
                }
            }
            
            logger.info("Event processing service shut down successfully");
            
        } catch (Exception e) {
            logger.error("Error shutting down event processing service", e);
        }
    }
    
    
    
    
    
    /**
     * Subscribe to a single tag using Ignition Tag API (event-driven).
     * 
     * @param tagPath The tag path to subscribe to
     */
    
    /**
     * Flush a batch of events to Zerobus.
     * 
     * Note: Not synchronized - uses thread-safe queue operations.
     * Multiple threads can call this concurrently without blocking each other.
     */
    private void flushBatch() {
        if (eventQueue.isEmpty()) {
            return;
        }
        
        try {
            List<TagEvent> batch = new ArrayList<>();
            eventQueue.drainTo(batch, config.getBatchSize());
            
            if (batch.isEmpty()) {
                return;
            }
            
            logger.debug("Flushing batch of {} events", batch.size());
            
            boolean success = zerobusClientManager.sendEvents(batch);
            
            if (success) {
                totalBatchesFlushed.incrementAndGet();
                lastFlushTime = System.currentTimeMillis();
                
                if (config.isDebugLogging()) {
                    logger.debug("Batch sent successfully: {} events", batch.size());
                }
            } else {
                logger.warn("Failed to send batch of {} events", batch.size());
            }
            
        } catch (Exception e) {
            logger.error("Error flushing batch", e);
        }
    }
    
    /**
     * Check if the rate limit allows processing this event.
     * 
     * @return true if within rate limit
     */
    private boolean checkRateLimit() {
        long now = System.currentTimeMillis() / 1000; // Current second
        
        if (now != currentSecond) {
            // New second - reset counter
            currentSecond = now;
            eventsThisSecond.set(0);
        }
        
        long count = eventsThisSecond.incrementAndGet();
        return count <= config.getMaxEventsPerSecond();
    }
    
    
    /**
     * Get diagnostics information.
     * 
     * @return Diagnostics string
     */
    public String getDiagnostics() {
        StringBuilder sb = new StringBuilder();
        sb.append("=== Event Processing Service Diagnostics ===\n");
        sb.append("Running: ").append(running.get()).append("\n");
        sb.append("Mode: Event-driven (Event Streams integration)\n");
        sb.append("Queue Size: ").append(eventQueue.size())
            .append("/").append(config.getMaxQueueSize()).append("\n");
        sb.append("Total Events Received: ").append(totalEventsReceived.get()).append("\n");
        sb.append("Total Events Dropped: ").append(totalEventsDropped.get()).append("\n");
        sb.append("Total Batches Flushed: ").append(totalBatchesFlushed.get()).append("\n");
        
        if (lastFlushTime > 0) {
            long secondsAgo = (System.currentTimeMillis() - lastFlushTime) / 1000;
            sb.append("Last Flush: ").append(secondsAgo).append(" seconds ago\n");
        } else {
            sb.append("Last Flush: Never\n");
        }
        
        return sb.toString();
    }
    
    /**
     * Ingest a single tag event from Event Streams.
     * This method is called by the REST endpoint when Event Streams sends tag events.
     * 
     * @param payload Tag event payload from Event Streams
     * @return true if event was accepted, false if queue is full
     */
    public boolean ingestEvent(TagEventPayload payload) {
        if (!running.get()) {
            logger.warn("Cannot ingest event: service not running");
            return false;
        }
        
        try {
            // Convert payload to TagEvent
            TagEvent event = convertPayloadToEvent(payload);
            
            // Try to add to queue
            boolean accepted = eventQueue.offer(event);
            
            if (accepted) {
                totalEventsReceived.incrementAndGet();
                logger.debug("Event accepted from Event Stream: {}", payload.getTagPath());
            } else {
                totalEventsDropped.incrementAndGet();
                logger.warn("Event queue full, dropped event from: {}", payload.getTagPath());
            }
            
            return accepted;
            
        } catch (Exception e) {
            logger.error("Error ingesting event from Event Streams", e);
            return false;
        }
    }
    
    /**
     * Ingest a batch of tag events from Event Streams.
     * This method is called by the REST endpoint when Event Streams sends batched tag events.
     * 
     * @param payloads Array of tag event payloads from Event Streams
     * @return number of events accepted
     */
    public int ingestEventBatch(TagEventPayload[] payloads) {
        if (!running.get()) {
            logger.warn("Cannot ingest batch: service not running");
            return 0;
        }
        
        int accepted = 0;
        
        for (TagEventPayload payload : payloads) {
            try {
                TagEvent event = convertPayloadToEvent(payload);
                
                if (eventQueue.offer(event)) {
                    accepted++;
                    totalEventsReceived.incrementAndGet();
                } else {
                    totalEventsDropped.incrementAndGet();
                    logger.warn("Event queue full, dropped event from batch: {}", payload.getTagPath());
                }
                
            } catch (Exception e) {
                logger.error("Error processing event from batch: {}", payload.getTagPath(), e);
            }
        }
        
        logger.debug("Batch ingestion: {} of {} events accepted", accepted, payloads.length);
        return accepted;
    }
    
    /**
     * Convert TagEventPayload from Event Streams to internal TagEvent.
     * 
     * @param payload TagEventPayload from Event Streams
     * @return TagEvent for internal processing
     */
    private TagEvent convertPayloadToEvent(TagEventPayload payload) {
        // Extract timestamp (Event Streams provides it in milliseconds)
        long timestampMs = payload.getTimestamp() != null ? payload.getTimestamp() : System.currentTimeMillis();
        Date timestamp = new Date(timestampMs);
        
        // Extract quality
        String quality = payload.getQuality() != null ? payload.getQuality() : "GOOD";
        
        // Create TagEvent using simple constructor
        // The ZerobusClientManager will extract additional metadata during protobuf conversion
        return new TagEvent(
            payload.getTagPath(),
            payload.getValue(),
            quality,
            timestamp
        );
    }
    
    /**
     * Determine the data type from the value object.
     * 
     * @param value The value object
     * @return String representation of the data type
     */
    private String determineDataType(Object value) {
        if (value == null) {
            return "NULL";
        } else if (value instanceof Boolean) {
            return "Boolean";
        } else if (value instanceof Integer) {
            return "Int4";
        } else if (value instanceof Long) {
            return "Int8";
        } else if (value instanceof Float) {
            return "Float4";
        } else if (value instanceof Double) {
            return "Float8";
        } else if (value instanceof String) {
            return "String";
        } else {
            return value.getClass().getSimpleName();
        }
    }
}

