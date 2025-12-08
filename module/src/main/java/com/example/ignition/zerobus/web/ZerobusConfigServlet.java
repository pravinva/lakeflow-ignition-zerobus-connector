package com.example.ignition.zerobus.web;

import com.example.ignition.zerobus.ConfigModel;
import com.example.ignition.zerobus.ZerobusGatewayHook;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.PrintWriter;

/**
 * ZerobusConfigServlet - HTTP Servlet for module configuration.
 * 
 * Routes:
 * - GET  /system/zerobus/config         -> getConfiguration()
 * - POST /system/zerobus/config         -> saveConfiguration()
 * - POST /system/zerobus/test-connection -> testConnection()
 * - GET  /system/zerobus/diagnostics    -> getDiagnostics()
 * - GET  /system/zerobus/health         -> healthCheck()
 */
public class ZerobusConfigServlet extends HttpServlet {
    
    private static final Logger logger = LoggerFactory.getLogger(ZerobusConfigServlet.class);
    private static final long serialVersionUID = 1L;
    
    // Static reference to hook (set by GatewayHook before servlet registration)
    private static ZerobusGatewayHook staticHook;
    
    private ZerobusGatewayHook hook;
    private ObjectMapper objectMapper;
    
    /**
     * No-arg constructor - Required by servlet container.
     */
    public ZerobusConfigServlet() {
        this.hook = staticHook;
        this.objectMapper = new ObjectMapper();
        
        if (this.hook == null) {
            logger.error("ZerobusGatewayHook not set! Call setHook() before servlet registration.");
        }
    }
    
    /**
     * Constructor with hook injection - Used by GatewayHook.
     * 
     * @param hook The ZerobusGatewayHook instance
     */
    public ZerobusConfigServlet(ZerobusGatewayHook hook) {
        this.hook = hook;
        this.objectMapper = new ObjectMapper();
        logger.info("ZerobusConfigServlet created with injected hook");
    }
    
    /**
     * Set the static hook reference before servlet registration.
     * Must be called by GatewayHook before addServlet().
     * 
     * @param hook The ZerobusGatewayHook instance
     */
    public static void setHook(ZerobusGatewayHook hook) {
        staticHook = hook;
    }
    
    @Override
    protected void doGet(HttpServletRequest req, HttpServletResponse resp) 
            throws ServletException, IOException {
        
        String pathInfo = req.getPathInfo();
        logger.info("GET request - pathInfo: {}, requestURI: {}", pathInfo, req.getRequestURI());
        
        // Normalize path - remove leading /zerobus if present
        String normalizedPath = pathInfo;
        if (pathInfo != null && pathInfo.startsWith("/zerobus")) {
            normalizedPath = pathInfo.substring("/zerobus".length());
        }
        
        // If path is empty or just "/", show index/config
        if (normalizedPath == null || normalizedPath.isEmpty() || "/".equals(normalizedPath)) {
            normalizedPath = "/config";
        }
        
        logger.info("Normalized path: {}", normalizedPath);
        
        resp.setContentType("application/json");
        resp.setCharacterEncoding("UTF-8");
        
        try {
            if ("/config".equals(normalizedPath)) {
                // GET /system/zerobus/config - Get current configuration
                handleGetConfig(resp);
                
            } else if ("/diagnostics".equals(normalizedPath)) {
                // GET /system/zerobus/diagnostics - Get diagnostics info
                handleGetDiagnostics(resp);
                
            } else if ("/health".equals(normalizedPath)) {
                // GET /system/zerobus/health - Health check
                handleHealthCheck(resp);
                
            } else {
                resp.setStatus(HttpServletResponse.SC_NOT_FOUND);
                writeJson(resp, "{\"error\": \"Endpoint not found: " + normalizedPath + "\"}");
            }
            
        } catch (Exception e) {
            logger.error("Error handling GET request: " + pathInfo, e);
            resp.setStatus(HttpServletResponse.SC_INTERNAL_SERVER_ERROR);
            writeJson(resp, "{\"error\": \"" + e.getMessage() + "\"}");
        }
    }
    
    @Override
    protected void doPost(HttpServletRequest req, HttpServletResponse resp) 
            throws ServletException, IOException {
        
        String pathInfo = req.getPathInfo();
        logger.info("POST request - pathInfo: {}, requestURI: {}", pathInfo, req.getRequestURI());
        
        // Normalize path - remove leading /zerobus if present
        String normalizedPath = pathInfo;
        if (pathInfo != null && pathInfo.startsWith("/zerobus")) {
            normalizedPath = pathInfo.substring("/zerobus".length());
        }
        
        logger.info("Normalized path: {}", normalizedPath);
        
        resp.setContentType("application/json");
        resp.setCharacterEncoding("UTF-8");
        
        try {
            if ("/config".equals(normalizedPath)) {
                // POST /system/zerobus/config - Save configuration
                handleSaveConfig(req, resp);
                
            } else if ("/test-connection".equals(normalizedPath)) {
                // POST /system/zerobus/test-connection - Test Databricks connection
                handleTestConnection(resp);
                
            } else {
                resp.setStatus(HttpServletResponse.SC_NOT_FOUND);
                writeJson(resp, "{\"error\": \"Endpoint not found: " + normalizedPath + "\"}");
            }
            
        } catch (Exception e) {
            logger.error("Error handling POST request: " + pathInfo, e);
            resp.setStatus(HttpServletResponse.SC_INTERNAL_SERVER_ERROR);
            writeJson(resp, "{\"error\": \"" + e.getMessage() + "\"}");
        }
    }
    
    /**
     * Handle GET /config - Return current configuration.
     */
    private void handleGetConfig(HttpServletResponse resp) throws IOException {
        try {
            ConfigModel config = hook.getConfigModel();
            String json = objectMapper.writeValueAsString(config);
            resp.setStatus(HttpServletResponse.SC_OK);
            writeJson(resp, json);
        } catch (Exception e) {
            logger.error("Error getting configuration", e);
            resp.setStatus(HttpServletResponse.SC_INTERNAL_SERVER_ERROR);
            writeJson(resp, "{\"error\": \"Failed to get configuration: " + e.getMessage() + "\"}");
        }
    }
    
    /**
     * Handle POST /config - Save new configuration.
     */
    private void handleSaveConfig(HttpServletRequest req, HttpServletResponse resp) 
            throws IOException {
        try {
            // Read JSON body
            String jsonBody = readRequestBody(req);
            
            // Parse to ConfigModel
            ConfigModel config = objectMapper.readValue(jsonBody, ConfigModel.class);
            
            // Save configuration via hook
            hook.saveConfiguration(config);
            
            // Return success
            resp.setStatus(HttpServletResponse.SC_OK);
            writeJson(resp, "{\"success\": true, \"message\": \"Configuration saved successfully\"}");
            
        } catch (Exception e) {
            logger.error("Error saving configuration", e);
            resp.setStatus(HttpServletResponse.SC_INTERNAL_SERVER_ERROR);
            writeJson(resp, "{\"error\": \"Failed to save configuration: " + e.getMessage() + "\"}");
        }
    }
    
    /**
     * Handle POST /test-connection - Test Databricks connection.
     */
    private void handleTestConnection(HttpServletResponse resp) throws IOException {
        try {
            // Test connection via Zerobus client manager
            boolean success = hook.getZerobusClientManager().testConnection();
            
            if (success) {
                resp.setStatus(HttpServletResponse.SC_OK);
                writeJson(resp, "{\"success\": true, \"message\": \"Connection test successful\"}");
            } else {
                resp.setStatus(HttpServletResponse.SC_BAD_REQUEST);
                writeJson(resp, "{\"success\": false, \"message\": \"Connection test failed\"}");
            }
            
        } catch (Exception e) {
            logger.error("Error testing connection", e);
            resp.setStatus(HttpServletResponse.SC_INTERNAL_SERVER_ERROR);
            writeJson(resp, "{\"error\": \"Connection test failed: " + e.getMessage() + "\"}");
        }
    }
    
    /**
     * Handle GET /diagnostics - Return diagnostics information.
     */
    private void handleGetDiagnostics(HttpServletResponse resp) throws IOException {
        try {
            // Get diagnostics from hook
            String diagnostics = hook.getDiagnostics();
            
            resp.setContentType("text/plain");
            resp.setStatus(HttpServletResponse.SC_OK);
            resp.getWriter().write(diagnostics);
            
        } catch (Exception e) {
            logger.error("Error getting diagnostics", e);
            resp.setStatus(HttpServletResponse.SC_INTERNAL_SERVER_ERROR);
            writeJson(resp, "{\"error\": \"Failed to get diagnostics: " + e.getMessage() + "\"}");
        }
    }
    
    /**
     * Handle GET /health - Health check endpoint.
     */
    private void handleHealthCheck(HttpServletResponse resp) throws IOException {
        try {
            resp.setStatus(HttpServletResponse.SC_OK);
            writeJson(resp, "{\"status\": \"ok\", \"module\": \"Zerobus Connector\", \"version\": \"1.0.0\"}");
        } catch (Exception e) {
            logger.error("Error in health check", e);
            resp.setStatus(HttpServletResponse.SC_INTERNAL_SERVER_ERROR);
            writeJson(resp, "{\"error\": \"Health check failed: " + e.getMessage() + "\"}");
        }
    }
    
    /**
     * Read request body as string.
     */
    private String readRequestBody(HttpServletRequest req) throws IOException {
        StringBuilder sb = new StringBuilder();
        try (BufferedReader reader = req.getReader()) {
            String line;
            while ((line = reader.readLine()) != null) {
                sb.append(line);
            }
        }
        return sb.toString();
    }
    
    /**
     * Write JSON response.
     */
    private void writeJson(HttpServletResponse resp, String json) throws IOException {
        try (PrintWriter writer = resp.getWriter()) {
            writer.write(json);
            writer.flush();
        }
    }
}
