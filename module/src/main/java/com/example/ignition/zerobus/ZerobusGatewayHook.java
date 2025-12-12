package com.example.ignition.zerobus;

import com.example.ignition.zerobus.web.TagEventPayload;
import com.example.ignition.zerobus.web.ZerobusConfigResource;
import com.example.ignition.zerobus.web.ZerobusConfigResourceHolder;
import com.inductiveautomation.ignition.common.licensing.LicenseState;
import com.inductiveautomation.ignition.gateway.model.AbstractGatewayModuleHook;
import com.inductiveautomation.ignition.gateway.model.GatewayContext;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * ZerobusGatewayHook - Main entry point for the Ignition-Zerobus connector module.
 * 
 * This module subscribes to Ignition tags and streams their values to Databricks
 * Delta tables via the Zerobus Ingest API using the Databricks Zerobus Java SDK.
 * 
 * Lifecycle (Ignition 8.3.2):
 * - setup(GatewayContext): Initialize context and prepare resources
 * - startup(LicenseState): Start services and activate module
 * - shutdown(): Stop services and cleanup
 */
public class ZerobusGatewayHook extends AbstractGatewayModuleHook {
    
    private static final Logger logger = LoggerFactory.getLogger(ZerobusGatewayHook.class);
    
    private GatewayContext gatewayContext;
    private ZerobusClientManager zerobusClientManager;
    private TagSubscriptionService tagSubscriptionService;
    private ConfigModel configModel;
    private ZerobusConfigResource restResource;
    
    /**
     * Setup - called first during module initialization.
     * Store the gateway context for later use.
     */
    @Override
    public void setup(GatewayContext context) {
        this.gatewayContext = context;
        
        // Register configuration servlet (runtime-select: Ignition 8.1 uses javax.servlet, 8.3+ uses jakarta.servlet)
        try {
            // Create REST resource and set it for servlet use
            this.restResource = new ZerobusConfigResource(context, this);
            ZerobusConfigResourceHolder.set(restResource);
            
            // Register servlet with Ignition's WebResourceManager
            Class<?> servletClass = resolveZerobusServletClass();
            // WebResourceManager is typed to the servlet API of the compiling Ignition SDK (8.3+ = jakarta).
            // We intentionally cast to raw Class to support runtime selection between javax/jakarta servlets.
            @SuppressWarnings({"rawtypes", "unchecked"})
            Class servletClassRaw = (Class) servletClass;
            context.getWebResourceManager().addServlet("zerobus", servletClassRaw);
            
            logger.info("Configuration servlet registered: 'zerobus' → /system/zerobus");
        } catch (Exception e) {
            logger.error("Failed to register configuration servlet", e);
        }
        
        logger.info("Zerobus Gateway Module setup complete");
    }
    
    /**
     * Module startup - called when the module is installed or Gateway starts.
     * NOTE: startup() is abstract in AbstractGatewayModuleHook - do NOT call super.startup()
     */
    @Override
    public void startup(LicenseState licenseState) {
        logger.info("Starting Zerobus Gateway Module...");
        
        try {
            // Initialize configuration model
            this.configModel = new ConfigModel();
            loadConfiguration();
            
            // Initialize Zerobus client manager
            this.zerobusClientManager = new ZerobusClientManager(configModel);
            
            // Initialize tag subscription service
            this.tagSubscriptionService = new TagSubscriptionService(
                gatewayContext, 
                zerobusClientManager, 
                configModel
            );
            
            // Note: REST servlet is registered in setup() method
            
            // Only start services if module is enabled
            if (configModel.isEnabled()) {
                startServices();
            }
            
            logger.info("Zerobus Gateway Module started successfully");
            
        } catch (Exception e) {
            logger.error("Failed to start Zerobus Gateway Module", e);
            throw new RuntimeException("Module startup failed", e);
        }
    }
    
    /**
     * Module shutdown - called when the module is uninstalled or Gateway stops.
     * NOTE: shutdown() is abstract in AbstractGatewayModuleHook - do NOT call super.shutdown()
     */
    @Override
    public void shutdown() {
        logger.info("Shutting down Zerobus Gateway Module...");
        
        try {
            // Unregister servlet
            if (gatewayContext != null) {
                try {
                    gatewayContext.getWebResourceManager().removeServlet("zerobus");
                    logger.info("Configuration servlet unregistered");
                } catch (Exception e) {
                    logger.warn("Error unregistering servlet: {}", e.getMessage());
                }
            }
            
            // Stop tag subscriptions
            if (tagSubscriptionService != null) {
                tagSubscriptionService.shutdown();
                tagSubscriptionService = null;
            }
            
            // Close Zerobus client
            if (zerobusClientManager != null) {
                zerobusClientManager.shutdown();
                zerobusClientManager = null;
            }
            
            logger.info("Zerobus Gateway Module shut down successfully");
            
        } catch (Exception e) {
            logger.error("Error during module shutdown", e);
        }
    }
    
    /**
     * Start the Zerobus client and tag subscription services.
     */
    private void startServices() throws Exception {
        logger.info("Starting Zerobus services...");
        
        // Initialize Zerobus connection
        zerobusClientManager.initialize();
        
        // Start tag subscriptions
        tagSubscriptionService.start();
        
        logger.info("Zerobus services started");
    }
    
    /**
     * Load configuration from persistent storage.
     * 
     * REQUIRES IMPLEMENTATION: Integrate with Ignition Gateway persistence.
     * 
     * Implementation approach:
     * - Use GatewayContext.getPersistenceInterface()
     * - Read settings from internal database
     * - Populate ConfigModel with saved values
     * 
     * For initial deployment, configuration is set programmatically or via UI.
     */
    private void loadConfiguration() {
        logger.debug("Loading configuration...");
        
        /*
         * IMPLEMENTATION REQUIRED (Ignition SDK 8.3.2):
         * 
         * PersistenceInterface persistence = gatewayContext.getPersistenceInterface();
         * SQuery<SettingsRecord> query = new SQuery<>(SettingsRecord.META);
         * List<SettingsRecord> records = persistence.query(query);
         * 
         * if (!records.isEmpty()) {
         *     SettingsRecord record = records.get(0);
         *     configModel.setWorkspaceUrl(record.getWorkspaceUrl());
         *     configModel.setZerobusEndpoint(record.getZerobusEndpoint());
         *     // ... populate other fields
         * }
         */
        
        logger.debug("Configuration loaded (using defaults until persistence is implemented)");
    }
    
    /**
     * Save configuration to persistent storage.
     * 
     * REQUIRES IMPLEMENTATION: Integrate with Ignition Gateway persistence.
     * 
     * @param newConfig The new configuration to save
     */
    public void saveConfiguration(ConfigModel newConfig) {
        logger.info("Saving configuration...");
        
        /*
         * IMPLEMENTATION REQUIRED (Ignition SDK 8.3.2):
         * 
         * PersistenceInterface persistence = gatewayContext.getPersistenceInterface();
         * 
         * // Update or create settings record
         * SQuery<SettingsRecord> query = new SQuery<>(SettingsRecord.META);
         * List<SettingsRecord> records = persistence.query(query);
         * 
         * SettingsRecord record;
         * if (records.isEmpty()) {
         *     record = SettingsRecord.META.newRecord();
         * } else {
         *     record = records.get(0);
         * }
         * 
         * record.setWorkspaceUrl(newConfig.getWorkspaceUrl());
         * record.setZerobusEndpoint(newConfig.getZerobusEndpoint());
         * // ... set other fields
         * 
         * persistence.save(record);
         */
        
        boolean needsRestart = configModel.requiresRestart(newConfig);
        this.configModel.updateFrom(newConfig);
        
        if (needsRestart && configModel.isEnabled()) {
            try {
                // Restart services with new configuration
                if (tagSubscriptionService != null) {
                    tagSubscriptionService.shutdown();
                }
                if (zerobusClientManager != null) {
                    zerobusClientManager.shutdown();
                }
                
                startServices();
                logger.info("Services restarted with new configuration");
                
            } catch (Exception e) {
                logger.error("Failed to restart services with new configuration", e);
            }
        }
        
        logger.info("Configuration saved successfully");
    }
    
    /**
     * Test connection to Zerobus with current configuration.
     * Used by the config UI to validate settings.
     */
    public boolean testConnection() {
        logger.info("Testing Zerobus connection...");
        
        try {
            ZerobusClientManager testClient = new ZerobusClientManager(configModel);
            testClient.initialize();
            boolean success = testClient.testConnection();
            testClient.shutdown();
            
            logger.info("Connection test " + (success ? "succeeded" : "failed"));
            return success;
            
        } catch (Exception e) {
            logger.error("Connection test failed", e);
            return false;
        }
    }
    
    /**
     * Get module identifier.
     */
    @Override
    public boolean isFreeModule() {
        return false; // Requires Ignition license
    }
    
    /**
     * Get configuration model for UI access.
     */
    public ConfigModel getConfigModel() {
        return configModel;
    }
    
    /**
     * Get the gateway context.
     */
    public GatewayContext getGatewayContext() {
        return gatewayContext;
    }
    
    /**
     * Get Zerobus client manager.
     */
    public ZerobusClientManager getZerobusClientManager() {
        return zerobusClientManager;
    }
    
    /**
     * Get diagnostics information.
     */
    public String getDiagnostics() {
        return getDiagnosticsInfo();
    }
    
    /**
     * Get diagnostics information.
     */
    public String getDiagnosticsInfo() {
        StringBuilder info = new StringBuilder();
        info.append("=== Zerobus Module Diagnostics ===\n");
        info.append("Module Enabled: ").append(configModel.isEnabled()).append("\n");
        
        if (zerobusClientManager != null) {
            info.append("\n").append(zerobusClientManager.getDiagnostics());
        }
        
        if (tagSubscriptionService != null) {
            info.append("\n").append(tagSubscriptionService.getDiagnostics());
        }
        
        return info.toString();
    }
    
    /**
     * Ingest a single tag event from Event Streams.
     * 
     * @param payload Tag event payload from Event Streams
     * @return true if event was accepted, false if queue is full
     */
    public boolean ingestTagEvent(TagEventPayload payload) {
        if (tagSubscriptionService == null) {
            logger.warn("Cannot ingest event: tag subscription service not initialized");
            return false;
        }
        
        if (!configModel.isEnabled()) {
            logger.warn("Cannot ingest event: module is disabled");
            return false;
        }
        
        return tagSubscriptionService.ingestEvent(payload);
    }
    
    /**
     * Ingest a batch of tag events from Event Streams.
     * 
     * @param payloads Array of tag event payloads from Event Streams
     * @return number of events accepted
     */
    public int ingestTagEventBatch(TagEventPayload[] payloads) {
        if (tagSubscriptionService == null) {
            logger.warn("Cannot ingest batch: tag subscription service not initialized");
            return 0;
        }
        
        if (!configModel.isEnabled()) {
            logger.warn("Cannot ingest batch: module is disabled");
            return 0;
        }
        
        return tagSubscriptionService.ingestEventBatch(payloads);
    }

    /**
     * Select the correct servlet implementation for the running Ignition version.
     *
     * Ignition 8.1 / Jetty EE8 uses javax.servlet.*
     * Ignition 8.3 / Jetty EE10 uses jakarta.servlet.*
     */
    private Class<?> resolveZerobusServletClass() throws ClassNotFoundException {
        ClassLoader cl = getClass().getClassLoader();

        // Prefer jakarta on 8.3+
        if (classExists("jakarta.servlet.http.HttpServlet", cl)) {
            return Class.forName("com.example.ignition.zerobus.web.servlet83.ZerobusConfigServletJakarta", true, cl);
        }

        // Fallback to javax on 8.1/8.2
        if (classExists("javax.servlet.http.HttpServlet", cl)) {
            return Class.forName("com.example.ignition.zerobus.web.servlet81.ZerobusConfigServletJavax", true, cl);
        }

        throw new ClassNotFoundException("No supported servlet API found (neither jakarta.servlet nor javax.servlet)");
    }

    private static boolean classExists(String fqcn, ClassLoader cl) {
        try {
            Class.forName(fqcn, false, cl);
            return true;
        } catch (Throwable ignored) {
            return false;
        }
    }
}
