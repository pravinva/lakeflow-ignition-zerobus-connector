package com.example.ignition.zerobus.web;

import com.example.ignition.zerobus.ConfigModel;
import com.example.ignition.zerobus.ConfigPanel;
import com.example.ignition.zerobus.ZerobusGatewayHook;
import com.inductiveautomation.ignition.gateway.model.GatewayContext;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.ws.rs.*;
import javax.ws.rs.core.MediaType;
import javax.ws.rs.core.Response;

/**
 * REST API resource for Zerobus Connector configuration.
 * 
 * Provides HTTP endpoints for the React configuration UI.
 * 
 * Endpoints:
 * - GET  /system/zerobus/config         - Get current configuration
 * - POST /system/zerobus/config         - Save configuration
 * - POST /system/zerobus/test-connection - Test Databricks connection
 * - GET  /system/zerobus/diagnostics    - Get diagnostics info
 */
@Path("/system/zerobus")
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
     * GET /system/zerobus/config
     * 
     * Get the current module configuration.
     * 
     * @return Current configuration as JSON
     */
    @GET
    @Path("/config")
    @Produces(MediaType.APPLICATION_JSON)
    public Response getConfiguration() {
        logger.debug("GET /system/zerobus/config");
        
        try {
            ConfigModel config = gatewayHook.getConfigModel();
            
            if (config == null) {
                return Response.status(Response.Status.INTERNAL_SERVER_ERROR)
                    .entity("{\"error\": \"Configuration not initialized\"}")
                    .build();
            }
            
            return Response.ok(config).build();
            
        } catch (Exception e) {
            logger.error("Error getting configuration", e);
            return Response.status(Response.Status.INTERNAL_SERVER_ERROR)
                .entity("{\"error\": \"" + e.getMessage() + "\"}")
                .build();
        }
    }
    
    /**
     * POST /system/zerobus/config
     * 
     * Save new configuration.
     * 
     * @param config New configuration
     * @return Response indicating success or failure
     */
    @POST
    @Path("/config")
    @Consumes(MediaType.APPLICATION_JSON)
    @Produces(MediaType.APPLICATION_JSON)
    public Response saveConfiguration(ConfigModel config) {
        logger.info("POST /system/zerobus/config");
        
        try {
            // Validate configuration
            java.util.List<String> errors = config.validate();
            if (!errors.isEmpty()) {
                String errorMsg = String.join(", ", errors);
                logger.warn("Configuration validation failed: {}", errorMsg);
                
                return Response.status(Response.Status.BAD_REQUEST)
                    .entity("{\"error\": \"Validation failed\", \"details\": \"" + errorMsg + "\"}")
                    .build();
            }
            
            // Save configuration
            boolean success = configPanel.saveConfiguration();
            configPanel.updateConfiguration(config);
            
            if (success) {
                logger.info("Configuration saved successfully");
                return Response.ok()
                    .entity("{\"message\": \"Configuration saved successfully\", \"success\": true}")
                    .build();
            } else {
                logger.error("Failed to save configuration");
                return Response.status(Response.Status.INTERNAL_SERVER_ERROR)
                    .entity("{\"error\": \"Failed to save configuration\", \"success\": false}")
                    .build();
            }
            
        } catch (Exception e) {
            logger.error("Error saving configuration", e);
            return Response.status(Response.Status.INTERNAL_SERVER_ERROR)
                .entity("{\"error\": \"" + e.getMessage() + "\", \"success\": false}")
                .build();
        }
    }
    
    /**
     * POST /system/zerobus/test-connection
     * 
     * Test connection to Databricks.
     * 
     * @return Response indicating connection test result
     */
    @POST
    @Path("/test-connection")
    @Produces(MediaType.APPLICATION_JSON)
    public Response testConnection() {
        logger.info("POST /system/zerobus/test-connection");
        
        try {
            boolean success = configPanel.testConnection();
            
            if (success) {
                logger.info("Connection test successful");
                return Response.ok()
                    .entity("{\"success\": true, \"message\": \"Connection test successful! Databricks endpoint is reachable and credentials are valid.\"}")
                    .build();
            } else {
                logger.warn("Connection test failed");
                return Response.status(Response.Status.BAD_REQUEST)
                    .entity("{\"success\": false, \"message\": \"Connection test failed. Check Gateway logs for details.\"}")
                    .build();
            }
            
        } catch (Exception e) {
            logger.error("Error testing connection", e);
            return Response.status(Response.Status.INTERNAL_SERVER_ERROR)
                .entity("{\"success\": false, \"message\": \"Connection test error: " + e.getMessage() + "\"}")
                .build();
        }
    }
    
    /**
     * GET /system/zerobus/diagnostics
     * 
     * Get module diagnostics information.
     * 
     * @return Diagnostics as plain text
     */
    @GET
    @Path("/diagnostics")
    @Produces(MediaType.TEXT_PLAIN)
    public Response getDiagnostics() {
        logger.debug("GET /system/zerobus/diagnostics");
        
        try {
            String diagnostics = configPanel.refreshDiagnostics();
            
            if (diagnostics == null || diagnostics.isEmpty()) {
                diagnostics = "No diagnostics available";
            }
            
            return Response.ok(diagnostics).build();
            
        } catch (Exception e) {
            logger.error("Error getting diagnostics", e);
            return Response.status(Response.Status.INTERNAL_SERVER_ERROR)
                .entity("Error: " + e.getMessage())
                .build();
        }
    }
    
    /**
     * GET /system/zerobus/health
     * 
     * Health check endpoint.
     * 
     * @return Health status
     */
    @GET
    @Path("/health")
    @Produces(MediaType.APPLICATION_JSON)
    public Response healthCheck() {
        logger.debug("GET /system/zerobus/health");
        
        try {
            boolean enabled = gatewayHook.getConfigModel().isEnabled();
            
            return Response.ok()
                .entity("{\"status\": \"ok\", \"enabled\": " + enabled + "}")
                .build();
                
        } catch (Exception e) {
            logger.error("Health check failed", e);
            return Response.status(Response.Status.INTERNAL_SERVER_ERROR)
                .entity("{\"status\": \"error\", \"message\": \"" + e.getMessage() + "\"}")
                .build();
        }
    }
}

