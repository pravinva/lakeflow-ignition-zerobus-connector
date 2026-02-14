package com.example.ignition.zerobus;

import com.databricks.zerobus.AccountOidcHelper;
import com.databricks.zerobus.BearerTokenStubFactory;
import com.databricks.zerobus.ZerobusSdk;
import com.databricks.zerobus.ZerobusStream;
import com.databricks.zerobus.TableProperties;
import com.databricks.zerobus.StreamConfigurationOptions;
import com.databricks.zerobus.IngestRecordResponse;
import com.databricks.zerobus.ZerobusException;
import com.databricks.zerobus.NonRetriableException;
import com.example.ignition.zerobus.proto.OTEvent;
import com.example.ignition.zerobus.pipeline.OtEventMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.Instant;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.Locale;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ThreadLocalRandom;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicLong;

/**
 * ZerobusClientManager - Manages Databricks Zerobus SDK integration.
 * 
 * Responsibilities:
 * - Initialize Zerobus SDK with OAuth credentials
 * - Manage stream lifecycle
 * - Send batched events to Zerobus Ingest
 * - Handle retries, backoff, and error logging
 * - Provide diagnostics and metrics
 */
public class ZerobusClientManager {
    
    private static final Logger logger = LoggerFactory.getLogger(ZerobusClientManager.class);
    
    private final ConfigModel config;
    private AtomicBoolean initialized = new AtomicBoolean(false);
    private AtomicBoolean connected = new AtomicBoolean(false);
    
    // Metrics
    private AtomicLong totalEventsSent = new AtomicLong(0);
    private AtomicLong totalBatchesSent = new AtomicLong(0);
    private AtomicLong totalBytesSent = new AtomicLong(0);
    private AtomicLong totalFailures = new AtomicLong(0);
    private volatile long lastSuccessfulSendTime = 0;
    private volatile long lastAckedOffset = 0;
    private volatile String lastError = null;

    // Error classification / backoff state
    private enum ErrorClass {
        NONE,
        AUTH,
        TRANSIENT,
        NON_RETRIABLE
    }

    private volatile ErrorClass lastErrorClass = ErrorClass.NONE;
    private volatile long lastErrorAtMs = 0L;
    private final AtomicInteger consecutiveFailures = new AtomicInteger(0);
    private final AtomicLong nextRetryAtMs = new AtomicLong(0L);
    private final AtomicLong lastAuthFailureMs = new AtomicLong(0L);

    // Circuit breaker: stop attempting sends after repeated non-retriable errors.
    // Opens after NON_RETRIABLE_TRIP_COUNT consecutive non-retriable failures, stays open for
    // NON_RETRIABLE_COOLDOWN_MS before allowing one probe attempt.
    private static final int NON_RETRIABLE_TRIP_COUNT = 3;
    private static final long NON_RETRIABLE_COOLDOWN_MS = 10L * 60_000L; // 10 minutes
    private volatile boolean circuitOpen = false;
    private volatile long circuitOpenedAtMs = 0L;
    private volatile String circuitOpenReason = null;

    // Zerobus SDK objects - volatile to prevent race between ensureConnected() and shutdown()
    private volatile ZerobusSdk zerobusSdk;
    private volatile ZerobusStream<OTEvent> zerobusStream;
    private volatile TableProperties<OTEvent> tableProperties;
    private volatile StreamConfigurationOptions streamOptions;

    // Reconnect throttling to avoid hot-looping when the remote service is down.
    private final AtomicLong lastReconnectAttemptMs = new AtomicLong(0);
    private final Object reconnectLock = new Object();

    private void recordSuccess() {
        consecutiveFailures.set(0);
        lastErrorClass = ErrorClass.NONE;
        nextRetryAtMs.set(0L);
        if (circuitOpen) {
            logger.info("Circuit breaker closed - connection recovered after non-retriable error");
            circuitOpen = false;
            circuitOpenReason = null;
        }
        // Keep lastError/lastErrorAtMs as historical breadcrumbs.
    }

    private void recordFailure(Throwable t) {
        long now = System.currentTimeMillis();
        ErrorClass cls = classify(t);
        lastErrorClass = cls;
        lastErrorAtMs = now;
        lastError = t != null ? t.getClass().getSimpleName() + ": " + safeMsg(t) : "Unknown failure";

        int fails = consecutiveFailures.incrementAndGet();
        if (cls == ErrorClass.AUTH) {
            lastAuthFailureMs.set(now);
        }
        // Trip circuit breaker on repeated non-retriable errors
        if (cls == ErrorClass.NON_RETRIABLE && fails >= NON_RETRIABLE_TRIP_COUNT && !circuitOpen) {
            circuitOpen = true;
            circuitOpenedAtMs = now;
            circuitOpenReason = lastError;
            logger.error("Circuit breaker OPEN after {} consecutive non-retriable errors. "
                    + "Sends will be skipped for {}min. Reason: {}",
                    fails, NON_RETRIABLE_COOLDOWN_MS / 60_000L, circuitOpenReason);
        }
        long backoffMs = computeBackoffMs(cls, fails);
        nextRetryAtMs.set(now + backoffMs);
    }

    private static String safeMsg(Throwable t) {
        String m = t.getMessage();
        return m != null ? m : "";
    }

    private static ErrorClass classify(Throwable t) {
        if (t == null) return ErrorClass.TRANSIENT;

        // Unwrap common wrapper exceptions
        Throwable root = t;
        while (root instanceof java.util.concurrent.ExecutionException
                || root instanceof java.util.concurrent.CompletionException) {
            Throwable c = root.getCause();
            if (c == null) break;
            root = c;
        }

        // Auth/token detection by message is allowed for any exception type (SDKs sometimes throw "retriable"
        // exception types for auth failures, but we still want to avoid hot-looping).
        //
        // IMPORTANT: Some SDKs put the important auth hint only in a nested cause message, so scan the cause chain.
        String msg = "";
        Throwable scan = root;
        int depth = 0;
        while (scan != null && depth < 8) {
            String m = safeMsg(scan);
            if (m != null && !m.isEmpty()) {
                msg = (msg + "\n" + m).toLowerCase(Locale.ROOT);
            }
            scan = scan.getCause();
            depth++;
        }
        // AUTH classification:
        // Only classify as AUTH when we see explicit authorization/credential signals.
        // NOTE: Do NOT classify generic "token" failures as AUTH. In practice, transient network issues can surface
        // as "failed to get token" and we don't want to mislead operators or apply long AUTH backoff.
        if (msg.contains("unauthorized") || msg.contains("forbidden") || msg.contains("401") || msg.contains("403")
                || msg.contains("invalid_client") || msg.contains("invalid grant") || msg.contains("invalid_grant")
                || msg.contains("client secret") || msg.contains("client_secret")) {
            return ErrorClass.AUTH;
        }

        // Zerobus SDK sometimes throws "Failed to get Zerobus token" without indicating whether it's auth vs network.
        // Treat it as TRANSIENT unless the message also includes explicit auth signals above.
        if (msg.contains("failed to get zerobus token")) {
            return ErrorClass.TRANSIENT;
        }

        // NonRetriableException from the SDK generally means "operator action required" (bad table, schema, etc).
        if (root instanceof NonRetriableException) {
            return ErrorClass.NON_RETRIABLE;
        }

        // ZerobusException is treated as transient by default (SDK indicates retriable).
        if (root instanceof ZerobusException) {
            return ErrorClass.TRANSIENT;
        }

        // Network-ish failures (timeouts, IO, etc) should back off and retry.
        Throwable cur = root;
        while (cur != null) {
            String n = cur.getClass().getName();
            if (cur instanceof java.io.IOException
                    || cur instanceof java.net.SocketTimeoutException
                    || cur instanceof java.net.ConnectException
                    || n.contains("Timeout")
                    || n.contains("SSL")
                    || n.contains("UnknownHost")
                    || n.contains("Socket")) {
                return ErrorClass.TRANSIENT;
            }
            cur = cur.getCause();
        }

        // Default: unexpected, but we still treat as transient to avoid losing data; operator can inspect diagnostics.
        return ErrorClass.TRANSIENT;
    }

    private long computeBackoffMs(ErrorClass cls, int failures) {
        // Exponential backoff with jitter, capped. Config retryBackoffMs serves as the transient base.
        long base = Math.max(250L, config.getRetryBackoffMs());
        long max = 60_000L; // cap transient backoff at 60s
        long jitter = ThreadLocalRandom.current().nextLong(0, 250L);

        switch (cls) {
            case AUTH: {
                // Avoid hot loops on auth: start at 30s, cap at 10m
                long authBase = Math.max(30_000L, base);
                long exp = authBase * (1L << Math.min(10, Math.max(0, failures - 1))); // up to ~512x
                return Math.min(exp, 10L * 60_000L) + jitter;
            }
            case NON_RETRIABLE: {
                // Operator action required; don't keep pounding. Retry rarely just in case it was transient.
                return (5L * 60_000L) + jitter; // 5 minutes
            }
            case TRANSIENT:
            default: {
                long exp = base * (1L << Math.min(6, Math.max(0, failures - 1))); // up to 64x
                return Math.min(exp, max) + jitter;
            }
        }
    }
    
    /**
     * Constructor.
     * 
     * @param config Configuration model with connection details
     */
    public ZerobusClientManager(ConfigModel config) {
        this.config = config;
    }
    
    /**
     * Initialize the Zerobus SDK and create a stream.
     * 
     * @throws Exception if initialization fails
     */
    public void initialize() throws Exception {
        if (initialized.get()) {
            logger.warn("ZerobusClientManager already initialized");
            return;
        }
        
        logger.info("Initializing Zerobus client...");
        logger.info("  Workspace URL: {}", config.getWorkspaceUrl());
        logger.info("  Zerobus Endpoint: {}", config.getZerobusEndpoint());
        logger.info("  Target Table: {}", config.getTargetTable());
        
        try {
            // Validate configuration
            List<String> errors = config.validate();
            if (!errors.isEmpty()) {
                throw new IllegalArgumentException("Invalid configuration: " + String.join(", ", errors));
            }
            
            // Initialize Zerobus SDK
            logger.info("Creating ZerobusSdk instance...");
            this.zerobusSdk = new ZerobusSdk(
                config.getZerobusEndpoint(),
                config.getWorkspaceUrl()
            );
            
            // If bearer token mode, inject custom stub factory that bypasses M2M OAuth
            if (config.isBearerTokenMode()) {
                logger.info("Auth mode: bearer_token - injecting custom token supplier");
                BearerTokenStubFactory.inject(zerobusSdk, () -> config.getBearerToken());
            } else if (config.getAccountId() != null && !config.getAccountId().isEmpty()) {
                logger.info("Auth mode: service_principal with account-level OIDC (accountId={})",
                        config.getAccountId());
                AccountOidcHelper.configure(zerobusSdk, config.getAccountId(),
                        config.getOauthClientId(), config.getOauthClientSecret());
            } else {
                logger.info("Auth mode: service_principal - using SDK M2M OAuth");
            }
            
            // Configure table properties
            this.tableProperties = new TableProperties<>(
                config.getTargetTable(),
                OTEvent.getDefaultInstance()
            );
            
            // Configure stream options
            this.streamOptions = StreamConfigurationOptions.builder()
                .setMaxInflightRecords(config.getMaxQueueSize())
                .setRecovery(true)
                .setRecoveryTimeoutMs((int) config.getConnectionTimeoutMs())
                .setRecoveryBackoffMs((int) config.getRetryBackoffMs())
                .setRecoveryRetries(config.getMaxRetries())
                .setFlushTimeoutMs((int) config.getRequestTimeoutMs())
                .setServerLackOfAckTimeoutMs((int) config.getRequestTimeoutMs())
                .setAckCallback(this::handleAcknowledgment)
                .build();
            
            // Create stream
            logger.info("Creating Zerobus stream...");
            // In bearer_token mode the custom stub factory handles auth; pass placeholder
            // credentials since the SDK requires non-null params.
            String streamClientId = config.isBearerTokenMode() ? "bearer-token-mode" : config.getOauthClientId();
            String streamClientSecret = config.isBearerTokenMode() ? "unused" : config.getOauthClientSecret();
            CompletableFuture<ZerobusStream<OTEvent>> streamFuture = zerobusSdk.createStream(
                tableProperties,
                streamClientId,
                streamClientSecret,
                streamOptions
            );
            
            // Wait for stream creation (with timeout)
            this.zerobusStream = streamFuture.get(
                config.getConnectionTimeoutMs(),
                TimeUnit.MILLISECONDS
            );
            
            initialized.set(true);
            connected.set(true);
            
            logger.info("Zerobus client initialized successfully");
            logger.info("  Stream ID: {}", zerobusStream.getStreamId());
            logger.info("  Stream State: {}", zerobusStream.getState());
            
        } catch (Exception e) {
            logger.error("Failed to initialize Zerobus client", e);
            lastError = e.getMessage();
            throw e;
        }
    }
    
    /**
     * Shutdown the Zerobus client and close the stream.
     */
    public void shutdown() {
        // IMPORTANT: shutdown must never block Ignition gateway shutdown on network/auth/service health.
        // Historically, zerobusStream.flush()/close() can block for a long time if the sink is down.

        if (!initialized.get()) {
            return;
        }

        logger.info("Shutting down Zerobus client...");

        // Serialize with reconnect/sends and detach references first.
        final ZerobusStream<OTEvent> streamToClose;
        synchronized (reconnectLock) {
            streamToClose = this.zerobusStream;
            this.zerobusStream = null;
            this.zerobusSdk = null;
            connected.set(false);
            initialized.set(false);
        }

        if (streamToClose == null) {
            logger.info("Zerobus client shut down successfully");
            return;
        }

        // Bound shutdown time to keep gateway stop/restart responsive even if configured timeouts are large.
        final long timeoutMs = Math.min(
                Math.max(250L, config.getRequestTimeoutMs()),
                5_000L
        );

        try {
            // Best-effort close in a bounded-time background thread.
            Thread t = new Thread(() -> {
                try {
                    // Do NOT flush here. Store-and-forward guarantees we can resend after restart.
                    streamToClose.close();
                } catch (Throwable closeErr) {
                    logger.warn("Error while closing Zerobus stream (ignored during shutdown)", closeErr);
                }
            }, "Zerobus-Stream-Close");
            t.setDaemon(true);
            t.start();
            t.join(timeoutMs);
            if (t.isAlive()) {
                // We can't force-stop safely; allow JVM shutdown to proceed.
                t.interrupt();
                logger.warn("Timed out closing Zerobus stream after {}ms; proceeding with gateway shutdown", timeoutMs);
            }
        } catch (InterruptedException ie) {
            Thread.currentThread().interrupt();
            logger.warn("Interrupted while shutting down Zerobus client; proceeding", ie);
        } catch (Throwable t) {
            logger.warn("Unexpected error during Zerobus client shutdown; proceeding", t);
        }

        logger.info("Zerobus client shut down successfully");
    }
    
    /**
     * Send a batch of events to Zerobus Ingest.
     * 
     * @param events List of TagEvent objects to send
     * @return true if successful, false otherwise
     */
    public boolean sendEvents(List<TagEvent> events) {
        if (events == null || events.isEmpty()) {
            logger.debug("No events to send");
            return true;
        }
        // Back-compat wrapper: map TagEvent -> OTEvent and send as normalized events.
        OtEventMapper mapper = new OtEventMapper(config);
        List<OTEvent> batch = new ArrayList<>(events.size());
        for (TagEvent te : events) {
            batch.add(mapper.map(te));
        }
        return sendOtEvents(batch);
    }

    /**
     * Send a batch of normalized OT events (preferred API).
     */
    public boolean sendOtEvents(List<OTEvent> events) {
        // Circuit breaker: skip sends entirely when open, allow a probe after cooldown
        if (circuitOpen) {
            long elapsed = System.currentTimeMillis() - circuitOpenedAtMs;
            if (elapsed < NON_RETRIABLE_COOLDOWN_MS) {
                // Still in cooldown - silently drop without logging every call
                return false;
            }
            // Cooldown expired - allow one probe attempt through
            logger.info("Circuit breaker cooldown expired; allowing probe attempt");
        }

        if (!ensureConnected()) {
            logger.warn("Cannot send events - client not initialized or not connected");
            return false;
        }
        if (events == null || events.isEmpty()) {
            return true;
        }
        logger.debug("Sending batch of {} OT events to Zerobus", events.size());

        // Compute batch size (bytes) before adding batch_bytes_sent so the metric is payload size.
        long batchBytes = 0;
        for (OTEvent event : events) {
            batchBytes += event.getSerializedSize();
        }
        // Rebuild events with batch_bytes_sent set so it lands in raw_tags (Delta) for demo observability.
        List<OTEvent> eventsWithBatchSize = new ArrayList<>(events.size());
        for (OTEvent event : events) {
            eventsWithBatchSize.add(event.toBuilder().setBatchBytesSent(batchBytes).build());
        }
        events = eventsWithBatchSize;

        // Capture local reference to avoid TOCTOU race with shutdown() nulling the field.
        final ZerobusStream<OTEvent> stream = this.zerobusStream;
        if (stream == null) {
            logger.warn("Cannot send events - stream was closed during send");
            connected.set(false);
            return false;
        }

        try {
            List<CompletableFuture<Void>> futures = new ArrayList<>();
            for (OTEvent event : events) {
                futures.add(stream.ingestRecord(event));
            }
            CompletableFuture<Void> allFutures = CompletableFuture.allOf(futures.toArray(new CompletableFuture[0]));
            allFutures.get(config.getRequestTimeoutMs(), TimeUnit.MILLISECONDS);
            stream.flush();

            totalEventsSent.addAndGet(events.size());
            totalBatchesSent.incrementAndGet();
            totalBytesSent.addAndGet(batchBytes);
            lastSuccessfulSendTime = System.currentTimeMillis();
            recordSuccess();
            return true;
        } catch (NonRetriableException e) {
            recordFailure(e);
            if (lastErrorClass == ErrorClass.AUTH) {
                logger.error("Auth/token error sending events to Zerobus (will back off)", e);
            } else {
                logger.error("Non-retriable error sending events to Zerobus (operator action likely required)", e);
            }
            totalFailures.incrementAndGet();
            connected.set(false);
            return false;
        } catch (ZerobusException e) {
            recordFailure(e);
            logger.warn("Retriable error sending events to Zerobus (will retry with backoff)", e);
            totalFailures.incrementAndGet();
            // Recovery will be attempted by ensureConnected() after backoff.
            return false;
        } catch (Exception e) {
            recordFailure(e);
            logger.error("Unexpected error sending events to Zerobus (will retry with backoff)", e);
            totalFailures.incrementAndGet();
            connected.set(false);
            // Recovery will be attempted by ensureConnected() after backoff.
            return false;
        }
    }

    /**
     * Best-effort: ensure the client is connected, attempting recovery/reinitialize with throttling.
     * This prevents the system from getting "stuck" in a disconnected state after a transient failure.
     */
    private boolean ensureConnected() {
        // If module is disabled, do not attempt to connect.
        if (!config.isEnabled()) {
            return false;
        }

        if (initialized.get() && connected.get()) {
            return true;
        }

        synchronized (reconnectLock) {
            if (initialized.get() && connected.get()) {
                return true;
            }

            long now = System.currentTimeMillis();
            long retryAt = nextRetryAtMs.get();
            if (retryAt > 0 && now < retryAt) {
                return false;
            }
            long last = lastReconnectAttemptMs.get();
            long minInterval = 250L; // lightweight guard against tight loops; real backoff is nextRetryAtMs
            if ((now - last) < minInterval) {
                return false;
            }
            lastReconnectAttemptMs.set(now);

            try {
                // If we have a stream but are disconnected, try stream recovery first.
                if (initialized.get() && !connected.get() && zerobusStream != null && zerobusSdk != null) {
                    attemptRecovery();
                    if (connected.get()) {
                        recordSuccess();
                        return true;
                    }
                }

                // Fallback: full reinitialize.
                try {
                    shutdown();
                } catch (Exception ignored) {
                    // shutdown is best-effort
                }
                initialize();
                if (connected.get()) {
                    recordSuccess();
                }
                return connected.get();
            } catch (Exception e) {
                recordFailure(e);
                connected.set(false);
                return false;
            }
        }
    }
    
    /**
     * Last error message from the most recent failure (e.g. testConnection or send).
     * Exposed so callers can include it in API responses.
     */
    public String getLastError() {
        return lastError;
    }

    /**
     * Test the connection to Zerobus.
     *
     * @return empty on success, or the error message on failure
     */
    public Optional<String> testConnection() {
        logger.info("Testing Zerobus connection...");
        try {
            // Create a temporary SDK instance for testing
            ZerobusSdk testSdk = new ZerobusSdk(
                config.getZerobusEndpoint(),
                config.getWorkspaceUrl()
            );
            
            // Inject custom auth if needed
            if (config.isBearerTokenMode()) {
                BearerTokenStubFactory.inject(testSdk, () -> config.getBearerToken());
            } else if (config.getAccountId() != null && !config.getAccountId().isEmpty()) {
                AccountOidcHelper.configure(testSdk, config.getAccountId(),
                        config.getOauthClientId(), config.getOauthClientSecret());
            }
            
            TableProperties<OTEvent> testTableProps = new TableProperties<>(
                config.getTargetTable(),
                OTEvent.getDefaultInstance()
            );
            
            StreamConfigurationOptions testOptions = StreamConfigurationOptions.builder()
                .setMaxInflightRecords(100)
                .setRecovery(false)
                .setFlushTimeoutMs(10000)
                .build();
            
            // Try to create a stream
            String testClientId = config.isBearerTokenMode() ? "bearer-token-mode" : config.getOauthClientId();
            String testClientSecret = config.isBearerTokenMode() ? "unused" : config.getOauthClientSecret();
            CompletableFuture<ZerobusStream<OTEvent>> streamFuture = testSdk.createStream(
                testTableProps,
                testClientId,
                testClientSecret,
                testOptions
            );
            
            ZerobusStream<OTEvent> testStream = streamFuture.get(10, TimeUnit.SECONDS);
            
            // Close the test stream
            testStream.close();
            
            logger.info("Connection test successful");
            return Optional.empty();
            
        } catch (NonRetriableException e) {
            logger.error("Connection test failed with non-retriable error", e);
            lastError = e.getMessage();
            return Optional.ofNullable(e.getMessage()).or(() -> Optional.of(e.getClass().getSimpleName()));
        } catch (Exception e) {
            logger.error("Connection test failed", e);
            lastError = e.getMessage();
            return Optional.ofNullable(e.getMessage()).or(() -> Optional.of(e.getClass().getSimpleName()));
        }
    }
    
    /**
     * Attempt to recover a failed stream.
     */
    private void attemptRecovery() {
        if (!initialized.get() || zerobusStream == null) {
            logger.warn("Cannot attempt recovery - not initialized");
            return;
        }
        
        logger.info("Attempting stream recovery...");
        
        try {
            // Use SDK's recreateStream to recover
            CompletableFuture<ZerobusStream<OTEvent>> recoveryFuture = 
                zerobusSdk.recreateStream(zerobusStream);
            
            // Wait for recovery
            this.zerobusStream = recoveryFuture.get(
                config.getConnectionTimeoutMs(),
                TimeUnit.MILLISECONDS
            );
            
            connected.set(true);
            logger.info("Stream recovery successful");
            logger.info("  Stream ID: {}", zerobusStream.getStreamId());
            logger.info("  Stream State: {}", zerobusStream.getState());
            
        } catch (Exception e) {
            logger.error("Stream recovery failed", e);
            recordFailure(e);
            connected.set(false);
        }
    }
    
    /**
     * Handle acknowledgment callback from Zerobus server.
     * 
     * @param response The acknowledgment response
     */
    private void handleAcknowledgment(IngestRecordResponse response) {
        long offset = response.getDurabilityAckUpToOffset();
        this.lastAckedOffset = offset;
        
        if (config.isDebugLogging()) {
            logger.debug("Received acknowledgment up to offset: {}", offset);
        }
    }
    
    /**
     * Convert a TagEvent to OTEvent protobuf message.
     * 
     * @param event The tag event to convert
     * @return OTEvent protobuf message
     */
    // TagEvent -> OTEvent mapping moved to pipeline.OtEventMapper to keep clean adapter->sink separation.
    
    /**
     * Get diagnostics information for monitoring.
     * 
     * @return Diagnostics string
     */
    private static final ZoneId AEDT_ZONE = ZoneId.of("Australia/Sydney");
    private static final DateTimeFormatter AEDT_FMT =
            DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss z").withZone(AEDT_ZONE);

    private String formatTimestamp(long epochMs) {
        long secondsAgo = (System.currentTimeMillis() - epochMs) / 1000;
        String aedt = AEDT_FMT.format(Instant.ofEpochMilli(epochMs));
        return secondsAgo + " seconds ago (" + aedt + ")";
    }

    public String getDiagnostics() {
        StringBuilder sb = new StringBuilder();
        sb.append("=== Zerobus Client Diagnostics ===\n");
        sb.append("Initialized: ").append(initialized.get()).append("\n");
        sb.append("Connected: ").append(connected.get()).append("\n");
        
        ZerobusStream<OTEvent> stream = this.zerobusStream;
        if (stream != null) {
            sb.append("Stream ID: ").append(stream.getStreamId()).append("\n");
            sb.append("Stream State: ").append(stream.getState()).append("\n");
        }
        
        sb.append("Total Events Sent: ").append(totalEventsSent.get()).append("\n");
        sb.append("Total Batches Sent: ").append(totalBatchesSent.get()).append("\n");
        sb.append("Total Bytes Sent: ").append(totalBytesSent.get()).append("\n");
        sb.append("Total Failures: ").append(totalFailures.get()).append("\n");
        sb.append("Last Acked Offset: ").append(lastAckedOffset).append("\n");
        
        if (lastSuccessfulSendTime > 0) {
            sb.append("Last Successful Send: ").append(formatTimestamp(lastSuccessfulSendTime)).append("\n");
        } else {
            sb.append("Last Successful Send: Never\n");
        }
        
        if (lastError != null) {
            sb.append("Last Error: ").append(lastError).append("\n");
        }

        sb.append("Last Error Class: ").append(lastErrorClass).append("\n");
        if (lastErrorAtMs > 0) {
            sb.append("Last Error At: ").append(formatTimestamp(lastErrorAtMs)).append("\n");
        }
        sb.append("Consecutive Failures: ").append(consecutiveFailures.get()).append("\n");
        if (circuitOpen) {
            long remainMs = NON_RETRIABLE_COOLDOWN_MS - (System.currentTimeMillis() - circuitOpenedAtMs);
            sb.append("Circuit Breaker: OPEN (sends blocked)\n");
            sb.append("Circuit Open Reason: ").append(circuitOpenReason).append("\n");
            if (remainMs > 0) {
                sb.append("Circuit Cooldown Remaining: ").append(remainMs / 1000).append(" seconds\n");
            } else {
                sb.append("Circuit Cooldown Remaining: expired (will probe on next send)\n");
            }
        } else {
            sb.append("Circuit Breaker: closed\n");
        }
        long retryAt = nextRetryAtMs.get();
        if (retryAt > 0) {
            long ms = retryAt - System.currentTimeMillis();
            if (ms > 0) {
                sb.append("Next Retry In: ").append(ms / 1000).append(" seconds\n");
            } else {
                sb.append("Next Retry In: now\n");
            }
        }

        sb.append("Diagnostics Generated: ").append(AEDT_FMT.format(Instant.now())).append("\n");

        return sb.toString();
    }
    
    // Metric getters
    
    public long getTotalEventsSent() {
        return totalEventsSent.get();
    }
    
    public long getTotalBatchesSent() {
        return totalBatchesSent.get();
    }

    public long getTotalBytesSent() {
        return totalBytesSent.get();
    }
    
    public long getTotalFailures() {
        return totalFailures.get();
    }
    
    public boolean isInitialized() {
        return initialized.get();
    }
    
    public boolean isConnected() {
        return connected.get();
    }
    
    /**
     * @return true if the sink is currently ready to send without needing reconnection attempts.
     */
    public boolean isReadyToSend() {
        return initialized.get() && connected.get();
    }

    /**
     * Best-effort: attempt to connect/recover subject to backoff state. Safe to call frequently.
     */
    public boolean tryEnsureConnected() {
        return ensureConnected();
    }

    public String getStreamId() {
        return zerobusStream != null ? zerobusStream.getStreamId() : null;
    }
}
