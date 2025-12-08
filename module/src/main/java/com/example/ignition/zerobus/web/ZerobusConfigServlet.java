package com.example.ignition.zerobus.web;

import com.example.ignition.zerobus.ConfigModel;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.PrintWriter;

/**
 * ZerobusConfigServlet - HTTP Servlet wrapper for ZerobusConfigResource.
 * 
 * This servlet wraps the JAX-RS resource to make it compatible with 
 * Ignition 8.3.2's WebResourceManager which only accepts servlets.
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
    
    // Static reference to resource (set by GatewayHook before servlet registration)
    private static ZerobusConfigResource staticResource;
    
    private ZerobusConfigResource resource;
    private ObjectMapper objectMapper;
    
    /**
     * No-arg constructor - Required by servlet container.
     * Gets resource from static reference set by GatewayHook.
     */
    public ZerobusConfigServlet() {
        this.resource = staticResource;
        this.objectMapper = new ObjectMapper();
        
        if (this.resource == null) {
            logger.error("ZerobusConfigResource not set! Call setResource() before servlet registration.");
        }
    }
    
    /**
     * Set the static resource reference before servlet registration.
     * Must be called by GatewayHook before addServlet().
     * 
     * @param resource The ZerobusConfigResource instance
     */
    public static void setResource(ZerobusConfigResource resource) {
        staticResource = resource;
    }
    
    @Override
    protected void doGet(HttpServletRequest req, HttpServletResponse resp) 
            throws ServletException, IOException {
        
        String pathInfo = req.getPathInfo();
        logger.debug("GET request: {}", pathInfo);
        
        resp.setContentType("application/json");
        resp.setCharacterEncoding("UTF-8");
        
        try {
            if ("/config".equals(pathInfo)) {
                // GET /system/zerobus/config - Get current configuration
                handleGetConfig(resp);
                
            } else if ("/diagnostics".equals(pathInfo)) {
                // GET /system/zerobus/diagnostics - Get diagnostics info
                handleGetDiagnostics(resp);
                
            } else if ("/health".equals(pathInfo)) {
                // GET /system/zerobus/health - Health check
                handleHealthCheck(resp);
                
            } else {
                resp.setStatus(HttpServletResponse.SC_NOT_FOUND);
                writeJson(resp, "{\"error\": \"Endpoint not found: " + pathInfo + "\"}");
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
        logger.debug("POST request: {}", pathInfo);
        
        resp.setContentType("application/json");
        resp.setCharacterEncoding("UTF-8");
        
        try {
            if ("/config".equals(pathInfo)) {
                // POST /system/zerobus/config - Save configuration
                handleSaveConfig(req, resp);
                
            } else if ("/test-connection".equals(pathInfo)) {
                // POST /system/zerobus/test-connection - Test Databricks connection
                handleTestConnection(resp);
                
            } else {
                resp.setStatus(HttpServletResponse.SC_NOT_FOUND);
                writeJson(resp, "{\"error\": \"Endpoint not found: " + pathInfo + "\"}");
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
        javax.ws.rs.core.Response jaxrsResponse = resource.getConfiguration();
        
        if (jaxrsResponse.getStatus() == 200) {
            ConfigModel config = (ConfigModel) jaxrsResponse.getEntity();
            String json = objectMapper.writeValueAsString(config);
            resp.setStatus(HttpServletResponse.SC_OK);
            writeJson(resp, json);
        } else {
            resp.setStatus(jaxrsResponse.getStatus());
            writeJson(resp, jaxrsResponse.getEntity().toString());
        }
    }
    
    /**
     * Handle POST /config - Save new configuration.
     */
    private void handleSaveConfig(HttpServletRequest req, HttpServletResponse resp) 
            throws IOException {
        
        // Read JSON body
        String jsonBody = readRequestBody(req);
        
        // Parse to ConfigModel
        ConfigModel config = objectMapper.readValue(jsonBody, ConfigModel.class);
        
        // Call resource method
        javax.ws.rs.core.Response jaxrsResponse = resource.saveConfiguration(config);
        
        // Return response
        resp.setStatus(jaxrsResponse.getStatus());
        
        if (jaxrsResponse.getEntity() != null) {
            writeJson(resp, jaxrsResponse.getEntity().toString());
        } else {
            writeJson(resp, "{\"success\": " + (jaxrsResponse.getStatus() == 200) + "}");
        }
    }
    
    /**
     * Handle POST /test-connection - Test Databricks connection.
     */
    private void handleTestConnection(HttpServletResponse resp) throws IOException {
        javax.ws.rs.core.Response jaxrsResponse = resource.testConnection();
        
        resp.setStatus(jaxrsResponse.getStatus());
        
        if (jaxrsResponse.getEntity() != null) {
            writeJson(resp, jaxrsResponse.getEntity().toString());
        } else {
            writeJson(resp, "{\"success\": " + (jaxrsResponse.getStatus() == 200) + "}");
        }
    }
    
    /**
     * Handle GET /diagnostics - Return diagnostics information.
     */
    private void handleGetDiagnostics(HttpServletResponse resp) throws IOException {
        javax.ws.rs.core.Response jaxrsResponse = resource.getDiagnostics();
        
        if (jaxrsResponse.getStatus() == 200) {
            resp.setContentType("text/plain");
            resp.setStatus(HttpServletResponse.SC_OK);
            String diagnostics = jaxrsResponse.getEntity().toString();
            resp.getWriter().write(diagnostics);
        } else {
            resp.setStatus(jaxrsResponse.getStatus());
            writeJson(resp, "{\"error\": \"Failed to get diagnostics\"}");
        }
    }
    
    /**
     * Handle GET /health - Health check endpoint.
     */
    private void handleHealthCheck(HttpServletResponse resp) throws IOException {
        javax.ws.rs.core.Response jaxrsResponse = resource.healthCheck();
        
        resp.setStatus(jaxrsResponse.getStatus());
        
        if (jaxrsResponse.getEntity() != null) {
            writeJson(resp, jaxrsResponse.getEntity().toString());
        } else {
            writeJson(resp, "{\"status\": \"ok\"}");
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

