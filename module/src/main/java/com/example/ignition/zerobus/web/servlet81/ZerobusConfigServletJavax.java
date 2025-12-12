package com.example.ignition.zerobus.web.servlet81;

import com.example.ignition.zerobus.ConfigModel;
import com.example.ignition.zerobus.ZerobusClientManager;
import com.example.ignition.zerobus.ZerobusGatewayHook;
import com.example.ignition.zerobus.web.TagEventPayload;
import com.example.ignition.zerobus.web.ZerobusConfigResource;
import com.example.ignition.zerobus.web.ZerobusConfigResourceHolder;
import com.google.gson.Gson;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.BufferedReader;
import java.io.IOException;
import java.util.HashMap;
import java.util.Map;

/**
 * Ignition 8.1/8.2 servlet implementation (javax.servlet.*).
 * Mounted at /system/zerobus via WebResourceManager.
 */
public class ZerobusConfigServletJavax extends HttpServlet {
    private static final Logger logger = LoggerFactory.getLogger(ZerobusConfigServletJavax.class);
    private static final Gson gson = new Gson();

    private ZerobusConfigResource resource() {
        ZerobusConfigResource res = ZerobusConfigResourceHolder.get();
        if (res == null) {
            throw new IllegalStateException("ZerobusConfigResource not initialized");
        }
        return res;
    }

    @Override
    protected void doGet(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
        String pathInfo = req.getPathInfo();

        // Normalize path - remove /zerobus prefix if present
        if (pathInfo != null && pathInfo.startsWith("/zerobus")) {
            pathInfo = pathInfo.substring("/zerobus".length());
        }

        resp.setContentType("application/json");
        resp.setCharacterEncoding("UTF-8");

        try {
            if (pathInfo == null || pathInfo.equals("/") || pathInfo.equals("/config")) {
                handleGetConfig(resp);
            } else if (pathInfo.equals("/health")) {
                handleHealthCheck(resp);
            } else if (pathInfo.equals("/diagnostics")) {
                handleGetDiagnostics(resp);
            } else {
                resp.setStatus(HttpServletResponse.SC_NOT_FOUND);
                Map<String, String> error = new HashMap<>();
                error.put("error", "Unknown endpoint: " + pathInfo);
                resp.getWriter().write(gson.toJson(error));
            }
        } catch (Exception e) {
            logger.error("Error handling GET request", e);
            resp.setStatus(HttpServletResponse.SC_INTERNAL_SERVER_ERROR);
            Map<String, String> error = new HashMap<>();
            error.put("error", e.getMessage());
            resp.getWriter().write(gson.toJson(error));
        }
    }

    @Override
    protected void doPost(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
        String pathInfo = req.getPathInfo();

        // Normalize path
        if (pathInfo != null && pathInfo.startsWith("/zerobus")) {
            pathInfo = pathInfo.substring("/zerobus".length());
        }

        resp.setContentType("application/json");
        resp.setCharacterEncoding("UTF-8");

        try {
            if (pathInfo == null || pathInfo.equals("/") || pathInfo.equals("/config")) {
                handleSaveConfig(req, resp);
            } else if (pathInfo.equals("/test-connection")) {
                handleTestConnection(resp);
            } else if (pathInfo.equals("/ingest")) {
                handleIngestEvent(req, resp);
            } else if (pathInfo.equals("/ingest/batch")) {
                handleIngestBatch(req, resp);
            } else {
                resp.setStatus(HttpServletResponse.SC_NOT_FOUND);
                Map<String, String> error = new HashMap<>();
                error.put("error", "Unknown endpoint: " + pathInfo);
                resp.getWriter().write(gson.toJson(error));
            }
        } catch (Exception e) {
            logger.error("Error handling POST request", e);
            resp.setStatus(HttpServletResponse.SC_INTERNAL_SERVER_ERROR);
            Map<String, String> error = new HashMap<>();
            error.put("error", e.getMessage());
            resp.getWriter().write(gson.toJson(error));
        }
    }

    private void handleGetConfig(HttpServletResponse resp) throws IOException {
        ZerobusGatewayHook hook = resource().getGatewayHook();
        ConfigModel config = hook.getConfigModel();

        resp.setStatus(HttpServletResponse.SC_OK);
        resp.getWriter().write(gson.toJson(config));
    }

    private void handleSaveConfig(HttpServletRequest req, HttpServletResponse resp) throws IOException {
        String jsonBody = readBody(req);
        ConfigModel newConfig = gson.fromJson(jsonBody, ConfigModel.class);
        resource().getGatewayHook().saveConfiguration(newConfig);

        resp.setStatus(HttpServletResponse.SC_OK);
        Map<String, Object> result = new HashMap<>();
        result.put("success", true);
        result.put("message", "Configuration saved successfully");
        resp.getWriter().write(gson.toJson(result));
    }

    private void handleTestConnection(HttpServletResponse resp) throws IOException {
        ZerobusGatewayHook hook = resource().getGatewayHook();
        ZerobusClientManager clientManager = hook.getZerobusClientManager();

        Map<String, Object> result = new HashMap<>();
        if (clientManager != null && clientManager.isInitialized()) {
            result.put("success", true);
            result.put("message", "Connection test successful");
            result.put("connected", clientManager.isConnected());
        } else {
            result.put("success", false);
            result.put("message", "Zerobus client not initialized");
            result.put("connected", false);
        }

        resp.setStatus(HttpServletResponse.SC_OK);
        resp.getWriter().write(gson.toJson(result));
    }

    private void handleHealthCheck(HttpServletResponse resp) throws IOException {
        ZerobusGatewayHook hook = resource().getGatewayHook();
        ConfigModel config = hook.getConfigModel();
        ZerobusClientManager clientManager = hook.getZerobusClientManager();

        Map<String, Object> health = new HashMap<>();
        health.put("status", "UP");
        health.put("moduleEnabled", config.isEnabled());
        health.put("zerobusInitialized", clientManager != null && clientManager.isInitialized());
        health.put("zerobusConnected", clientManager != null && clientManager.isConnected());

        resp.setStatus(HttpServletResponse.SC_OK);
        resp.getWriter().write(gson.toJson(health));
    }

    private void handleGetDiagnostics(HttpServletResponse resp) throws IOException {
        String diagnostics = resource().getGatewayHook().getDiagnostics();
        resp.setStatus(HttpServletResponse.SC_OK);
        resp.setContentType("text/plain");
        resp.getWriter().write(diagnostics);
    }

    private void handleIngestEvent(HttpServletRequest req, HttpServletResponse resp) throws IOException {
        String jsonBody = readBody(req);
        try {
            TagEventPayload payload = gson.fromJson(jsonBody, TagEventPayload.class);
            boolean accepted = resource().getGatewayHook().ingestTagEvent(payload);

            if (accepted) {
                resp.setStatus(HttpServletResponse.SC_OK);
                Map<String, Object> result = new HashMap<>();
                result.put("success", true);
                result.put("message", "Event accepted");
                resp.getWriter().write(gson.toJson(result));
            } else {
                resp.setStatus(HttpServletResponse.SC_SERVICE_UNAVAILABLE);
                Map<String, Object> result = new HashMap<>();
                result.put("success", false);
                result.put("message", "Event queue full - backpressure applied");
                resp.getWriter().write(gson.toJson(result));
            }
        } catch (Exception e) {
            logger.error("Error processing tag event", e);
            resp.setStatus(HttpServletResponse.SC_BAD_REQUEST);
            Map<String, String> error = new HashMap<>();
            error.put("error", "Invalid event payload: " + e.getMessage());
            resp.getWriter().write(gson.toJson(error));
        }
    }

    private void handleIngestBatch(HttpServletRequest req, HttpServletResponse resp) throws IOException {
        String jsonBody = readBody(req);
        try {
            TagEventPayload[] payloads = gson.fromJson(jsonBody, TagEventPayload[].class);
            int accepted = resource().getGatewayHook().ingestTagEventBatch(payloads);

            resp.setStatus(HttpServletResponse.SC_OK);
            Map<String, Object> result = new HashMap<>();
            result.put("success", true);
            result.put("accepted", accepted);
            result.put("total", payloads.length);
            result.put("dropped", payloads.length - accepted);
            resp.getWriter().write(gson.toJson(result));
        } catch (Exception e) {
            logger.error("Error processing tag event batch", e);
            resp.setStatus(HttpServletResponse.SC_BAD_REQUEST);
            Map<String, String> error = new HashMap<>();
            error.put("error", "Invalid batch payload: " + e.getMessage());
            resp.getWriter().write(gson.toJson(error));
        }
    }

    private static String readBody(HttpServletRequest req) throws IOException {
        StringBuilder sb = new StringBuilder();
        try (BufferedReader reader = req.getReader()) {
            String line;
            while ((line = reader.readLine()) != null) {
                sb.append(line);
            }
        }
        return sb.toString();
    }
}


