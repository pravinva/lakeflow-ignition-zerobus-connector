package com.example.ignition.zerobus.web;

import com.example.ignition.zerobus.ConfigModel;
import com.example.ignition.zerobus.ConfigPanel;
import com.example.ignition.zerobus.ZerobusGatewayHook;
import com.inductiveautomation.ignition.gateway.model.GatewayContext;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Configuration & diagnostics helper for Zerobus Connector.
 *
 * IMPORTANT (Ignition 8.1/8.2): Do not use JAX-RS annotations here.
 * Many 8.1/8.2 Gateways do not ship a JAX-RS API/runtime on the module classpath, which can cause the module to fail
 * during class loading and appear as "not registering".
 *
 * HTTP endpoints are served via servlet implementations selected at runtime:
 * - Ignition 8.1/8.2: `web.servlet81.ZerobusConfigServletJavax`
 * - Ignition 8.3+:    `web.servlet83.ZerobusConfigServletJakarta`
 */
public class ZerobusConfigResource {
    
    private static final Logger logger = LoggerFactory.getLogger(ZerobusConfigResource.class);
    
    private final GatewayContext context;
    private final ZerobusGatewayHook gatewayHook;
    private final ConfigPanel configPanel;
    
    /**
     * Constructor.
     * 
     * @param context Gateway context
     * @param gatewayHook Module hook instance
     */
    public ZerobusConfigResource(GatewayContext context, ZerobusGatewayHook gatewayHook) {
        this.context = context;
        this.gatewayHook = gatewayHook;
        this.configPanel = new ConfigPanel(gatewayHook);
    }
    
    /**
     * Get the gateway hook instance.
     * 
     * @return Gateway hook
     */
    public ZerobusGatewayHook getGatewayHook() {
        return gatewayHook;
    }
    
    /**
     * Get the current module configuration.
     */
    public ConfigModel getConfiguration() {
        try {
            return gatewayHook.getConfigModel();
        } catch (Exception e) {
            logger.error("Error getting configuration", e);
            return null;
        }
    }
    
    /**
     * Save new configuration.
     *
     * @param config New configuration
     * @return true if saved successfully
     */
    public boolean saveConfiguration(ConfigModel config) {
        try {
            // Validate configuration
            java.util.List<String> errors = config.validate();
            if (!errors.isEmpty()) {
                String errorMsg = String.join(", ", errors);
                logger.warn("Configuration validation failed: {}", errorMsg);
                return false;
            }
            
            // Save configuration
            boolean success = configPanel.saveConfiguration();
            configPanel.updateConfiguration(config);
            
            if (success) {
                logger.info("Configuration saved successfully");
                return true;
            } else {
                logger.error("Failed to save configuration");
                return false;
            }
            
        } catch (Exception e) {
            logger.error("Error saving configuration", e);
            return false;
        }
    }
    
    /**
     * Test connection to Databricks.
     *
     * @return true if successful
     */
    public boolean testConnection() {
        try {
            return configPanel.testConnection();
        } catch (Exception e) {
            logger.error("Error testing connection", e);
            return false;
        }
    }
    
    /**
     * Get module diagnostics information.
     *
     * @return Diagnostics as plain text
     */
    public String getDiagnostics() {
        try {
            String diagnostics = configPanel.refreshDiagnostics();
            
            if (diagnostics == null || diagnostics.isEmpty()) {
                diagnostics = "No diagnostics available";
            }
            
            return diagnostics;
        } catch (Exception e) {
            logger.error("Error getting diagnostics", e);
            return "Error: " + e.getMessage();
        }
    }
    
    /**
     * Lightweight health check helper.
     */
    public boolean healthCheck() {
        try {
            return gatewayHook.getConfigModel() != null;
        } catch (Exception e) {
            logger.error("Health check failed", e);
            return false;
        }
    }
}

