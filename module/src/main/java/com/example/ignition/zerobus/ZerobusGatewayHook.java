package com.example.ignition.zerobus;

import com.example.ignition.zerobus.web.ZerobusConfigResource;
import com.inductiveautomation.ignition.common.licensing.LicenseState;
import com.inductiveautomation.ignition.gateway.model.AbstractGatewayModuleHook;
import com.inductiveautomation.ignition.gateway.model.GatewayContext;
import com.inductiveautomation.ignition.gateway.web.components.AbstractResourceProvider;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * ZerobusGatewayHook - Main entry point for the Ignition-Zerobus connector module.
 * 
 * This module subscribes to Ignition tags and streams their values to Databricks
 * Delta tables via the Zerobus Ingest API using the Databricks Zerobus Java SDK.
 * 
 * Lifecycle:
 * - startup(): Initialize managers, services, and config UI
 * - shutdown(): Gracefully close connections and stop subscriptions
 */
public class ZerobusGatewayHook extends AbstractGatewayModuleHook {
    
    private static final Logger logger = LoggerFactory.getLogger(ZerobusGatewayHook.class);
    
    private GatewayContext gatewayContext;
    private ZerobusClientManager zerobusClientManager;
    private TagSubscriptionService tagSubscriptionService;
    private ConfigModel configModel;
    private ZerobusConfigResource restResource;
    
    /**
     * Module startup - called when the module is installed or Gateway starts.
     */
    @Override
    public void startup(LicenseState licenseState) {
        super.startup(licenseState);
        
        logger.info("Starting Zerobus Gateway Module...");
        
        try {
            this.gatewayContext = this.getContext();
            
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
            
            // Register REST API resource for configuration UI
            this.restResource = new ZerobusConfigResource(gatewayContext, this);
            gatewayContext.getWebResourceManager()
                .addResource("/system/zerobus", restResource);
            
            logger.info("REST API registered at /system/zerobus");
            
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
     */
    @Override
    public void shutdown() {
        logger.info("Shutting down Zerobus Gateway Module...");
        
        try {
            // Unregister REST API
            if (gatewayContext != null && restResource != null) {
                try {
                    gatewayContext.getWebResourceManager()
                        .removeResource("/system/zerobus");
                    logger.info("REST API unregistered");
                } catch (Exception e) {
                    logger.warn("Error unregistering REST API", e);
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
        } finally {
            super.shutdown();
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
         * IMPLEMENTATION REQUIRED (Ignition SDK):
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
         * IMPLEMENTATION REQUIRED (Ignition SDK):
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
}

