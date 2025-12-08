package com.example.ignition.zerobus;

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
     * In a full implementation, this would read from Gateway settings records.
     */
    private void loadConfiguration() {
        // TODO: Load from Gateway persistent storage
        // For now, using defaults or environment variables
        logger.debug("Loading configuration...");
        
        // This would typically use GatewayContext.getPersistenceInterface()
        // to read saved settings from the internal database
        
        logger.debug("Configuration loaded");
    }
    
    /**
     * Save configuration to persistent storage.
     */
    public void saveConfiguration(ConfigModel newConfig) {
        // TODO: Save to Gateway persistent storage
        logger.info("Saving configuration...");
        
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

