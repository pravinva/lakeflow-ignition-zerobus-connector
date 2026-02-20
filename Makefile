# ──────────────────────────────────────────────────────────────
# Zerobus Ignition — end-to-end from scratch
# ──────────────────────────────────────────────────────────────
#
# Bootstrap (automated steps):
#   make bootstrap-83
#     Step 1  db-create-sp     Create SP, generate OAuth secret, assign to workspace
#     Step 2  db-setup-sql     Create catalog/schema/tables, deploy app + pipeline
#             db-wheel
#             db-pipeline
#             db-app-deploy-direct
#     Step 3  build-83         Build Ignition + Zerobus module (.modl)
#     Step 4  up-83            Start Ignition gateway (opens setup wizard)
#
# Then finish manually:
#   make setup-wizard-83          Step 4b  Complete Ignition setup in browser
#   make configure-83             Step 5   Push SP credentials to gateway
#   make simulate-83              Step 6   Start synthetic data generation
#   make links-83                 Step 7   Print all URLs for easy navigation
#   make db-train-health-model    Step 8   (optional) Create/run train_health_model job, register model in UC
#
# Full reset (Ignition + Databricks clean, then bootstrap):
#   make db-clean clean-83 bootstrap-83
#   then: make setup-wizard-83 configure-83 simulate-83 links-83
# ──────────────────────────────────────────────────────────────

SHELL := /bin/bash

# ── Versions ─────────────────────────────────────────────────
IGNITION_83_TAG       ?= 8.3
IGNITION_83_BUILD_VER ?= 8.3.3
IGNITION_83_MIN_VER   ?= 8.3.0
IGNITION_83_HOME      ?= /usr/local/bin/ignition

IGNITION_81_TAG       ?= 8.1
IGNITION_81_BUILD_VER ?= 8.1.50
IGNITION_81_MIN_VER   ?= 8.1.0
IGNITION_81_HOME      ?= /usr/local/ignition

# ── Ports ────────────────────────────────────────────────────
PORT_83 ?= 7088
PORT_81 ?= 8097

# ── Zerobus / workspace (set once in .env, used everywhere) ─────
# Source .env before make, or export: DATABRICKS_WAREHOUSE_ID, WORKSPACE_ID, DATABRICKS_REGION
WORKSPACE_ID       ?= 7405616025546271
DATABRICKS_REGION  ?= australiaeast
# ZEROBUS_ENDPOINT: set explicitly or derived from WORKSPACE_ID + DATABRICKS_REGION
ifndef ZEROBUS_ENDPOINT
ZEROBUS_ENDPOINT   = $(WORKSPACE_ID).zerobus.$(DATABRICKS_REGION).azuredatabricks.net
endif
export DATABRICKS_WAREHOUSE_ID WORKSPACE_ID DATABRICKS_REGION ZEROBUS_ENDPOINT

DATABRICKS_CONFIG_PROFILE ?= daveok
# Workspace host from profile (so workspace steps get credentials when DATABRICKS_HOST is unset after db-create-sp)
WS_HOST ?= $(shell awk '/^\[$(DATABRICKS_CONFIG_PROFILE)\]/{found=1} found && /^host/{gsub(/^[^=]+=[ \t]*/,""); print; exit}' ~/.databrickscfg 2>/dev/null)

# ── Databricks / pipeline / app ──────────────────────────────
CATALOG       ?= agl_demo
SCHEMA        ?= ot
DATABRICKS_WAREHOUSE_ID  ?= e4082fdb7ea19a15
# Apply default when DATABRICKS_WAREHOUSE_ID is set but empty (e.g. from .env)
ifeq ($(strip $(DATABRICKS_WAREHOUSE_ID)),)
DATABRICKS_WAREHOUSE_ID  := e4082fdb7ea19a15
endif
REPO_PATH     ?= /Users/david.okeeffe@databricks.com/lakeflow-ignition-zerobus-connector
PIPELINE_NAME ?= [production] agl-etl
REPO_BRANCH   ?= main
LAKEBASE_INSTANCE_NAME ?= agl-demo-lakebase
LAKEBASE_INSTANCE_CAPACITY ?= CU_1
LAKEBASE_CONNECTOR_ARTIFACT ?= .lakebase-connector.env

# ── Databricks bundle direct engine ───────────────────────────
BUNDLE_ENGINE ?= direct
MIN_DATABRICKS_CLI_MINOR ?= 279

# ── Service principal ────────────────────────────────────────
SP_NAME         ?= ignition-zerobus-agl
SP_PROFILE_NAME ?= agl-demo
# Auto-read SP application ID from the SP profile in ~/.databrickscfg.
# Falls back to the hardcoded default if the profile doesn't exist yet.
SP_APPLICATION_ID ?= $(shell awk '/^\[$(SP_PROFILE_NAME)\]/{found=1} found && /^client_id/{gsub(/^[^=]+=[ \t]*/,""); print; exit}' ~/.databrickscfg 2>/dev/null)

# ── Simulator ─────────────────────────────────────────────────
# Volume: events/tick = (sites*units)*23 + sites*16 (BESS+Grid). events/s = events_per_tick * 1000/interval.
# Default (3 sites, 2 units, 1s): ~186 events/tick, ~186 events/s, ~11k/min.
# For data to flow through pipeline/app in ~30–60s, use heavier load e.g.:
#   SIM_SITES=5 SIM_UNITS=4 SIM_INTERVAL=500  → ~540 events/tick, ~1080 events/s (~65k/min).
SIM_SITES    ?= 3
SIM_UNITS    ?= 2
SIM_INTERVAL ?= 1000
SIM_TICKS    ?= 0

# ── Paths ────────────────────────────────────────────────────
COMPOSE_DIR   := docker/ignition-gateway
RELEASES_DIR  := releases
DOCKER_OUT_83 := docker-out/8.3
DOCKER_OUT_81 := docker-out/8.1
SDP_DIR       := pipelines/sdp
WHEEL_FILE    := agl_analytics-0.1.0-py3-none-any.whl

# ──────────────────────────────────────────────────────────────
# Build targets
# ──────────────────────────────────────────────────────────────

.PHONY: build-83
build-83: ## Build the 8.3 .modl (Docker, no local Ignition needed)
	@echo "▸ Building Ignition 8.3 module..."
	DOCKER_BUILDKIT=1 docker build --no-cache \
		-f docker/Dockerfile.build-modl \
		--target out \
		--build-arg IGNITION_TAG=$(IGNITION_83_TAG) \
		--build-arg IGNITION_HOME=$(IGNITION_83_HOME) \
		--build-arg BUILD_FOR_IGNITION_VERSION=$(IGNITION_83_BUILD_VER) \
		--build-arg MIN_IGNITION_VERSION=$(IGNITION_83_MIN_VER) \
		--output type=local,dest=$(DOCKER_OUT_83) .
	@mkdir -p $(RELEASES_DIR)
	cp $(DOCKER_OUT_83)/*.modl $(RELEASES_DIR)/
	@echo "✔ Module(s) copied to $(RELEASES_DIR)/"
	@ls -lh $(RELEASES_DIR)/*.modl

.PHONY: build-81
build-81: ## Build the 8.1 .modl (Docker, no local Ignition needed)
	@echo "▸ Building Ignition 8.1 module..."
	DOCKER_BUILDKIT=1 docker build --no-cache \
		-f docker/Dockerfile.build-modl \
		--target out \
		--build-arg IGNITION_TAG=$(IGNITION_81_TAG) \
		--build-arg IGNITION_HOME=$(IGNITION_81_HOME) \
		--build-arg BUILD_FOR_IGNITION_VERSION=$(IGNITION_81_BUILD_VER) \
		--build-arg MIN_IGNITION_VERSION=$(IGNITION_81_MIN_VER) \
		--output type=local,dest=$(DOCKER_OUT_81) .
	@mkdir -p $(RELEASES_DIR)
	cp $(DOCKER_OUT_81)/*.modl $(RELEASES_DIR)/
	@echo "✔ Module(s) copied to $(RELEASES_DIR)/"
	@ls -lh $(RELEASES_DIR)/*.modl

# ──────────────────────────────────────────────────────────────
# Gateway lifecycle (8.3)
# ──────────────────────────────────────────────────────────────

.PHONY: up-83
up-83: ## Start Ignition 8.3 gateway (fresh volume, module baked in)
	@echo "▸ Resetting volume and starting Ignition 8.3 on port $(PORT_83)..."
	cd $(COMPOSE_DIR) && docker compose -f docker-compose.83.yml down -v 2>/dev/null || true
	cd $(COMPOSE_DIR) && docker compose -f docker-compose.83.yml up -d
	@echo ""
	@echo "✔ Gateway starting on http://localhost:$(PORT_83)"
	@echo "  Complete the setup wizard: make setup-wizard-83"

.PHONY: start-83
start-83: ## Start 8.3 gateway (keep existing volume)
	cd $(COMPOSE_DIR) && docker compose -f docker-compose.83.yml up -d
	@echo "✔ Gateway running on http://localhost:$(PORT_83)"

.PHONY: stop-83
stop-83: ## Stop 8.3 gateway (keep volume)
	cd $(COMPOSE_DIR) && docker compose -f docker-compose.83.yml down

.PHONY: clean-83
clean-83: ## Stop 8.3 gateway and destroy volume
	cd $(COMPOSE_DIR) && docker compose -f docker-compose.83.yml down -v

.PHONY: logs-83
logs-83: ## Tail 8.3 gateway logs
	docker logs --tail 100 -f ignition83_7088

.PHONY: setup-wizard-83
setup-wizard-83: ## Open browser to complete 8.3 setup wizard
	@echo "▸ Opening setup wizard..."
	@echo "  1. Accept EULA"
	@echo "  2. Create admin user (admin / password)"
	@echo "  3. Select Standard Trial"
	@echo "  4. Finish"
	@open "http://localhost:$(PORT_83)" 2>/dev/null || xdg-open "http://localhost:$(PORT_83)" 2>/dev/null || echo "Open http://localhost:$(PORT_83) in your browser"

# ──────────────────────────────────────────────────────────────
# Gateway lifecycle (8.1)
# ──────────────────────────────────────────────────────────────

.PHONY: up-81
up-81: ## Start Ignition 8.1 gateway (fresh volume, module baked in)
	@echo "▸ Resetting volume and starting Ignition 8.1 on port $(PORT_81)..."
	cd $(COMPOSE_DIR) && docker compose -f docker-compose.yml down -v 2>/dev/null || true
	cd $(COMPOSE_DIR) && docker compose -f docker-compose.yml up -d
	@echo ""
	@echo "✔ Gateway starting on http://localhost:$(PORT_81)"

.PHONY: start-81
start-81: ## Start 8.1 gateway (keep existing volume)
	cd $(COMPOSE_DIR) && docker compose -f docker-compose.yml up -d
	@echo "✔ Gateway running on http://localhost:$(PORT_81)"

.PHONY: stop-81
stop-81: ## Stop 8.1 gateway (keep volume)
	cd $(COMPOSE_DIR) && docker compose -f docker-compose.yml down

.PHONY: clean-81
clean-81: ## Stop 8.1 gateway and destroy volume
	cd $(COMPOSE_DIR) && docker compose -f docker-compose.yml down -v

.PHONY: logs-81
logs-81: ## Tail 8.1 gateway logs
	docker logs --tail 100 -f ignition81

# ──────────────────────────────────────────────────────────────
# Restore from .gwbk backup
# ──────────────────────────────────────────────────────────────

.PHONY: restore-83
restore-83: ## Restore 8.3 gateway from restore83/restore.gwbk
	@test -f $(COMPOSE_DIR)/restore83/restore.gwbk || \
		(echo "✘ Place your .gwbk at $(COMPOSE_DIR)/restore83/restore.gwbk first" && exit 1)
	cd $(COMPOSE_DIR) && docker compose -f docker-compose.83.restore.yml down -v 2>/dev/null || true
	cd $(COMPOSE_DIR) && docker compose -f docker-compose.83.restore.yml up -d
	@echo "✔ Restoring 8.3 gateway from backup on http://localhost:$(PORT_83)"

.PHONY: restore-81
restore-81: ## Restore 8.1 gateway from restore/restore.gwbk
	@test -f $(COMPOSE_DIR)/restore/restore.gwbk || \
		(echo "✘ Place your .gwbk at $(COMPOSE_DIR)/restore/restore.gwbk first" && exit 1)
	cd $(COMPOSE_DIR) && docker compose -f docker-compose.restore.yml down -v 2>/dev/null || true
	cd $(COMPOSE_DIR) && docker compose -f docker-compose.restore.yml up -d
	@echo "✔ Restoring 8.1 gateway from backup on http://localhost:$(PORT_81)"

# ──────────────────────────────────────────────────────────────
# Configure Zerobus connection
# ──────────────────────────────────────────────────────────────

.PHONY: configure-83
configure-83: ## Push Databricks/Zerobus config to 8.3 gateway
	@echo "▸ Configuring Zerobus on 8.3 gateway (port $(PORT_83))..."
	@echo "  workspace from profile [$(SP_PROFILE_NAME)]; endpoint=$(ZEROBUS_ENDPOINT); table=$(CATALOG).$(SCHEMA).raw_tags"
	cd examples/agl_fleet && \
		CATALOG=$(CATALOG) SCHEMA=$(SCHEMA) \
		uv run --extra setup agl-sim --setup-only \
			--profile $(SP_PROFILE_NAME) \
			--zerobus-endpoint $(ZEROBUS_ENDPOINT) \
			--gateway http://localhost:$(PORT_83)
	@echo "✔ Configuration pushed. Run: make health-83"

.PHONY: configure-81
configure-81: ## Push Databricks/Zerobus config to 8.1 gateway
	@echo "▸ Configuring Zerobus on 8.1 gateway (port $(PORT_81))..."
	@echo "  workspace from profile [$(SP_PROFILE_NAME)]; endpoint=$(ZEROBUS_ENDPOINT); table=$(CATALOG).$(SCHEMA).raw_tags"
	cd examples/agl_fleet && \
		CATALOG=$(CATALOG) SCHEMA=$(SCHEMA) \
		uv run --extra setup agl-sim --setup-only \
			--profile $(SP_PROFILE_NAME) \
			--zerobus-endpoint $(ZEROBUS_ENDPOINT) \
			--gateway http://localhost:$(PORT_81)
	@echo "✔ Configuration pushed. Run: make health-81"

.PHONY: configure-postgres-83
configure-postgres-83: ## Enable PostgreSQL sink on 8.3 gateway (requires LAKEBASE_* env vars)
	@if [ -z "$(LAKEBASE_HOST)" ] || [ -z "$(LAKEBASE_USER)" ] || [ -z "$(LAKEBASE_PASSWORD)" ]; then \
		echo "✘ Missing Lakebase env vars. Set LAKEBASE_HOST, LAKEBASE_USER, LAKEBASE_PASSWORD in .env"; \
		exit 1; \
	fi
	@echo "▸ Enabling PostgreSQL sink on 8.3 gateway (merging with existing config)..."
	@python3 -c " \
import json, urllib.request; \
current = json.loads(urllib.request.urlopen('http://localhost:$(PORT_83)/system/zerobus/config').read()); \
current.update({ \
    'sinkMode': 'lakebase', \
    'enableZerobusSink': False, \
    'enablePostgresSink': True, \
    'postgresHost': '$(LAKEBASE_HOST)', \
    'postgresPort': $(or $(LAKEBASE_PORT),5432), \
    'postgresDatabase': '$(or $(LAKEBASE_DATABASE),databricks_postgres)', \
    'postgresUser': '$(LAKEBASE_USER)', \
    'postgresPassword': '$(LAKEBASE_PASSWORD)', \
    'postgresTable': '$(or $(LAKEBASE_TABLE),raw_tags)' \
}); \
req = urllib.request.Request('http://localhost:$(PORT_83)/system/zerobus/config', \
    data=json.dumps(current).encode(), headers={'Content-Type': 'application/json'}); \
resp = json.loads(urllib.request.urlopen(req).read()); \
print('✔ PostgreSQL sink enabled' if resp.get('success') else '✘ ' + resp.get('message', 'Unknown error')) \
"

.PHONY: configure-postgres-81
configure-postgres-81: ## Enable PostgreSQL sink on 8.1 gateway (requires LAKEBASE_* env vars)
	@if [ -z "$(LAKEBASE_HOST)" ] || [ -z "$(LAKEBASE_USER)" ] || [ -z "$(LAKEBASE_PASSWORD)" ]; then \
		echo "✘ Missing Lakebase env vars. Set LAKEBASE_HOST, LAKEBASE_USER, LAKEBASE_PASSWORD in .env"; \
		exit 1; \
	fi
	@echo "▸ Enabling PostgreSQL sink on 8.1 gateway (merging with existing config)..."
	@python3 -c " \
import json, urllib.request; \
current = json.loads(urllib.request.urlopen('http://localhost:$(PORT_81)/system/zerobus/config').read()); \
current.update({ \
    'sinkMode': 'lakebase', \
    'enableZerobusSink': False, \
    'enablePostgresSink': True, \
    'postgresHost': '$(LAKEBASE_HOST)', \
    'postgresPort': $(or $(LAKEBASE_PORT),5432), \
    'postgresDatabase': '$(or $(LAKEBASE_DATABASE),databricks_postgres)', \
    'postgresUser': '$(LAKEBASE_USER)', \
    'postgresPassword': '$(LAKEBASE_PASSWORD)', \
    'postgresTable': '$(or $(LAKEBASE_TABLE),raw_tags)' \
}); \
req = urllib.request.Request('http://localhost:$(PORT_81)/system/zerobus/config', \
    data=json.dumps(current).encode(), headers={'Content-Type': 'application/json'}); \
resp = json.loads(urllib.request.urlopen(req).read()); \
print('✔ PostgreSQL sink enabled' if resp.get('success') else '✘ ' + resp.get('message', 'Unknown error')) \
"

.PHONY: configure-zerobus-83
configure-zerobus-83: configure-83 ## Force Zerobus-only mode on 8.3 gateway
	@echo "▸ Forcing Zerobus-only sink mode on 8.3 gateway..."
	@python3 -c " \
import json, urllib.request; \
current = json.loads(urllib.request.urlopen('http://localhost:$(PORT_83)/system/zerobus/config').read()); \
current.update({ \
    'sinkMode': 'zerobus', \
    'enableZerobusSink': True, \
    'enablePostgresSink': False \
}); \
req = urllib.request.Request('http://localhost:$(PORT_83)/system/zerobus/config', \
    data=json.dumps(current).encode(), headers={'Content-Type': 'application/json'}); \
resp = json.loads(urllib.request.urlopen(req).read()); \
print('✔ Zerobus-only mode enabled' if resp.get('success') else '✘ ' + resp.get('message', 'Unknown error')) \
"

.PHONY: configure-lakebase-83
configure-lakebase-83: configure-postgres-83 ## Force Lakebase-only mode on 8.3 gateway
	@echo "✔ Lakebase-only mode configured on 8.3 gateway"

.PHONY: configure-lakebase-83-direct
configure-lakebase-83-direct: db-lakebase-provision-direct ## Provision Lakebase + configure 8.3 gateway in Lakebase mode
	@echo "▸ Applying direct-provisioned Lakebase connector credentials to 8.3 gateway..."
	@if [ ! -f "$(LAKEBASE_CONNECTOR_ARTIFACT)" ]; then \
		echo "✘ Connector artifact not found: $(LAKEBASE_CONNECTOR_ARTIFACT)"; \
		echo "  Run: make db-lakebase-provision-direct"; \
		exit 1; \
	fi
	@set -a && source "$(LAKEBASE_CONNECTOR_ARTIFACT)" && set +a && \
		$(MAKE) configure-postgres-83 \
			LAKEBASE_HOST="$$LAKEBASE_HOST" \
			LAKEBASE_PORT="$$LAKEBASE_PORT" \
			LAKEBASE_DATABASE="$$LAKEBASE_DATABASE" \
			LAKEBASE_USER="$$LAKEBASE_USER" \
			LAKEBASE_PASSWORD="$$LAKEBASE_PASSWORD" \
			LAKEBASE_TABLE="$$LAKEBASE_TABLE"

.PHONY: configure-zerobus-81
configure-zerobus-81: configure-81 ## Force Zerobus-only mode on 8.1 gateway
	@echo "▸ Forcing Zerobus-only sink mode on 8.1 gateway..."
	@python3 -c " \
import json, urllib.request; \
current = json.loads(urllib.request.urlopen('http://localhost:$(PORT_81)/system/zerobus/config').read()); \
current.update({ \
    'sinkMode': 'zerobus', \
    'enableZerobusSink': True, \
    'enablePostgresSink': False \
}); \
req = urllib.request.Request('http://localhost:$(PORT_81)/system/zerobus/config', \
    data=json.dumps(current).encode(), headers={'Content-Type': 'application/json'}); \
resp = json.loads(urllib.request.urlopen(req).read()); \
print('✔ Zerobus-only mode enabled' if resp.get('success') else '✘ ' + resp.get('message', 'Unknown error')) \
"

.PHONY: configure-lakebase-81
configure-lakebase-81: configure-postgres-81 ## Force Lakebase-only mode on 8.1 gateway
	@echo "✔ Lakebase-only mode configured on 8.1 gateway"

.PHONY: configure-lakebase-81-direct
configure-lakebase-81-direct: db-lakebase-provision-direct ## Provision Lakebase + configure 8.1 gateway in Lakebase mode
	@echo "▸ Applying direct-provisioned Lakebase connector credentials to 8.1 gateway..."
	@if [ ! -f "$(LAKEBASE_CONNECTOR_ARTIFACT)" ]; then \
		echo "✘ Connector artifact not found: $(LAKEBASE_CONNECTOR_ARTIFACT)"; \
		echo "  Run: make db-lakebase-provision-direct"; \
		exit 1; \
	fi
	@set -a && source "$(LAKEBASE_CONNECTOR_ARTIFACT)" && set +a && \
		$(MAKE) configure-postgres-81 \
			LAKEBASE_HOST="$$LAKEBASE_HOST" \
			LAKEBASE_PORT="$$LAKEBASE_PORT" \
			LAKEBASE_DATABASE="$$LAKEBASE_DATABASE" \
			LAKEBASE_USER="$$LAKEBASE_USER" \
			LAKEBASE_PASSWORD="$$LAKEBASE_PASSWORD" \
			LAKEBASE_TABLE="$$LAKEBASE_TABLE"

# ──────────────────────────────────────────────────────────────
# Health & diagnostics
# ──────────────────────────────────────────────────────────────

.PHONY: health-83
health-83: ## Health check on 8.3 gateway
	@curl -sf http://localhost:$(PORT_83)/system/zerobus/health && echo "" || \
		echo "✘ Gateway not responding on port $(PORT_83)"

.PHONY: health-81
health-81: ## Health check on 8.1 gateway
	@curl -sf http://localhost:$(PORT_81)/system/zerobus/health && echo "" || \
		echo "✘ Gateway not responding on port $(PORT_81)"

.PHONY: diag-83
diag-83: ## Full diagnostics on 8.3 gateway (plain text)
	@code=$$(curl -s -o /tmp/diag_83_resp -w "%{http_code}" http://localhost:$(PORT_83)/system/zerobus/diagnostics 2>/dev/null); \
	if [ -z "$$code" ] || [ "$$code" = "000" ]; then echo "✘ Gateway not responding on port $(PORT_83) (connection refused or unreachable)"; exit 1; fi; \
	if [ "$$code" != "200" ]; then echo "✘ Gateway returned HTTP $$code:"; cat /tmp/diag_83_resp 2>/dev/null; exit 1; fi; \
	cat /tmp/diag_83_resp

.PHONY: diag-81
diag-81: ## Full diagnostics on 8.1 gateway (plain text)
	@code=$$(curl -s -o /tmp/diag_81_resp -w "%{http_code}" http://localhost:$(PORT_81)/system/zerobus/diagnostics 2>/dev/null); \
	if [ -z "$$code" ] || [ "$$code" = "000" ]; then echo "✘ Gateway not responding on port $(PORT_81) (connection refused or unreachable)"; exit 1; fi; \
	if [ "$$code" != "200" ]; then echo "✘ Gateway returned HTTP $$code:"; cat /tmp/diag_81_resp 2>/dev/null; exit 1; fi; \
	cat /tmp/diag_81_resp

# ──────────────────────────────────────────────────────────────
# Zerobus SDK connectivity test (create table then run SDK)
# ──────────────────────────────────────────────────────────────

.PHONY: zerobus-test-table
zerobus-test-table: ## Create agl_demo.ot.zerobus_test and grant SP UC write (run db-setup-sql first)
	@echo "▸ Creating $(CATALOG).$(SCHEMA).zerobus_test and granting SP $(SP_APPLICATION_ID) MODIFY, SELECT..."
	DATABRICKS_CONFIG_PROFILE=$(DATABRICKS_CONFIG_PROFILE) \
	CATALOG=$(CATALOG) SCHEMA=$(SCHEMA) DATABRICKS_WAREHOUSE_ID=$(DATABRICKS_WAREHOUSE_ID) \
	SP_APPLICATION_ID="$(SP_APPLICATION_ID)" \
		uv run --with databricks-sdk python onboarding/databricks/create_zerobus_test_table.py
	@echo "✔ Table and UC grants ready"

.PHONY: zerobus-test
zerobus-test: zerobus-test-table ## Create zerobus_test table then run Zerobus SDK test (load .env for credentials)
	@echo "▸ Running Zerobus SDK test (table=$(CATALOG).$(SCHEMA).zerobus_test)..."
	@if [ ! -f .env ]; then echo "✘ .env not found. Set DATABRICKS_CLIENT_ID and DATABRICKS_CLIENT_SECRET in .env"; exit 1; fi; \
	export $$(grep -v '^#' .env | xargs) 2>/dev/null; \
	export ZEROBUS_TARGET_TABLE="$(CATALOG).$(SCHEMA).zerobus_test"; \
	cd zerobus-test && uv run python test_zerobus.py

.PHONY: test-connection-83
test-connection-83: ## Validate Zerobus auth from inside Ignition (POST test-connection)
	@echo "▸ Testing Zerobus connection on 8.3 gateway..."
	@resp=$$(curl -s -X POST -H "Content-Type: application/json" http://localhost:$(PORT_83)/system/zerobus/test-connection 2>/dev/null); \
	if [ -z "$$resp" ]; then echo "✘ Gateway not responding on port $(PORT_83)"; exit 1; fi; \
	success=$$(echo "$$resp" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('success', False))" 2>/dev/null); \
	msg=$$(echo "$$resp" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('message',''))" 2>/dev/null); \
	if [ "$$success" = "True" ]; then echo "✔ $$msg"; exit 0; else echo "✘ $$msg"; echo "  Run make diag-83 for full diagnostics."; exit 1; fi

.PHONY: test-connection-81
test-connection-81: ## Validate Zerobus auth from inside Ignition (POST test-connection)
	@echo "▸ Testing Zerobus connection on 8.1 gateway..."
	@resp=$$(curl -s -X POST -H "Content-Type: application/json" http://localhost:$(PORT_81)/system/zerobus/test-connection 2>/dev/null); \
	if [ -z "$$resp" ]; then echo "✘ Gateway not responding on port $(PORT_81)"; exit 1; fi; \
	success=$$(echo "$$resp" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('success', False))" 2>/dev/null); \
	msg=$$(echo "$$resp" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('message',''))" 2>/dev/null); \
	if [ "$$success" = "True" ]; then echo "✔ $$msg"; exit 0; else echo "✘ $$msg"; echo "  Run make diag-81 for full diagnostics."; exit 1; fi

# ══════════════════════════════════════════════════════════════
# DATABRICKS — SP, catalog setup, wheel, pipeline, app
# ══════════════════════════════════════════════════════════════

# ──────────────────────────────────────────────────────────────
# Service principal (account-level create + workspace assign)
# ──────────────────────────────────────────────────────────────

# Clears the Databricks CLI token cache so the next account-level call re-authenticates.
# Use when you see "Endpoint not found" for account SCIM after re-running databricks auth login.
.PHONY: db-clear-account-cache
db-clear-account-cache: ## Clear CLI token cache so account auth is re-prompted
	@rm -f ~/.databricks/token-cache.json && \
	echo "✔ Cleared ~/.databricks/token-cache.json" && \
	echo "" && \
	echo "Re-authenticate at the account level, then run db-create-sp:" && \
	echo "  databricks auth login --host https://accounts.azuredatabricks.net --account-id ccb842e7-2376-4152-b0b0-29fa952379b8" && \
	echo "  make db-create-sp"

.PHONY: db-create-sp
db-create-sp: ## Create SP, generate OAuth secret, write ~/.databrickscfg profile
	@echo "▸ Creating service principal '$(SP_NAME)'..."
	@# Unset DATABRICKS_HOST so AccountClient uses the account profile host (accounts.azuredatabricks.net), not workspace URL
	CATALOG=$(CATALOG) \
	SCHEMA=$(SCHEMA) \
	DATABRICKS_WAREHOUSE_ID=$(DATABRICKS_WAREHOUSE_ID) \
	DATABRICKS_HOST= \
		uv run --with databricks-sdk python onboarding/databricks/create_service_principal.py \
			--sp-name "$(SP_NAME)" \
			--profile-name "$(SP_PROFILE_NAME)" \
			--workspace-profile "$(DATABRICKS_CONFIG_PROFILE)"

.PHONY: db-create-sp-no-grants
db-create-sp-no-grants: ## Create SP without running UC grants
	@echo "▸ Creating service principal '$(SP_NAME)' (skip grants)..."
	uv run --with databricks-sdk python onboarding/databricks/create_service_principal.py \
		--sp-name "$(SP_NAME)" \
		--profile-name "$(SP_PROFILE_NAME)" \
		--workspace-profile "$(DATABRICKS_CONFIG_PROFILE)" \
		--skip-grants

.PHONY: db-check-sp
db-check-sp: ## Check [agl-demo] profile and verify SP OAuth secret works
	@echo "▸ Checking SP profile [$(SP_PROFILE_NAME)] and secret..."
	SP_PROFILE_NAME="$(SP_PROFILE_NAME)" uv run --with databricks-sdk python onboarding/databricks/check_sp_and_secret.py
	@echo "✔ SP and secret OK. Use this profile for: make configure-83"

# Print the command to log in to the workspace (profile [daveok]). Use when db-setup-sql fails with "cannot configure default credentials".
.PHONY: db-login-workspace
db-login-workspace: ## Print command to log in to workspace (run it, then retry db-setup-sql)
	@WS_HOST="$(WS_HOST)"; \
	if [ -z "$$WS_HOST" ]; then \
		echo "✘ Could not read host from profile [$(DATABRICKS_CONFIG_PROFILE)] in ~/.databrickscfg"; \
		echo "  Ensure [$(DATABRICKS_CONFIG_PROFILE)] has a 'host' line (workspace URL)."; \
		exit 1; \
	fi; \
	echo "▸ Log in to the workspace so db-setup-sql can use profile [$(DATABRICKS_CONFIG_PROFILE)]:"; \
	echo ""; \
	echo "  databricks auth login --host $$WS_HOST"; \
	echo ""; \
	echo "Then run: make db-setup-sql"

# ──────────────────────────────────────────────────────────────
# Catalog / schema / tables / grants
# ──────────────────────────────────────────────────────────────

.PHONY: db-setup-sql
db-setup-sql: ## Run setup SQL (catalog, schema, tables, SP grants)
	@echo "▸ Running setup SQL (catalog=$(CATALOG), schema=$(SCHEMA), SP=$(SP_APPLICATION_ID))..."
	DATABRICKS_CONFIG_PROFILE=$(DATABRICKS_CONFIG_PROFILE) \
	DATABRICKS_HOST=$(or $(DATABRICKS_HOST),$(WS_HOST)) \
	CATALOG=$(CATALOG) \
	SCHEMA=$(SCHEMA) \
	DATABRICKS_WAREHOUSE_ID=$(DATABRICKS_WAREHOUSE_ID) \
	SP_APPLICATION_ID=$(SP_APPLICATION_ID) \
	SKIP_CATALOG_CREATE=$(SKIP_CATALOG_CREATE) \
		uv run --with databricks-sdk python onboarding/databricks/run_setup_sql.py
	@echo "✔ Setup SQL complete"

# ──────────────────────────────────────────────────────────────
# Lakebase (PostgreSQL) setup
# ──────────────────────────────────────────────────────────────

# Lakebase env vars: LAKEBASE_HOST, LAKEBASE_PORT, LAKEBASE_DATABASE, LAKEBASE_USER, LAKEBASE_PASSWORD
# Set in .env and source before running Lakebase targets.

.PHONY: db-lakebase-setup
db-lakebase-setup: ## Create raw_tags table in Lakebase (requires LAKEBASE_* env vars)
	@if [ -z "$(LAKEBASE_HOST)" ] || [ -z "$(LAKEBASE_DATABASE)" ] || [ -z "$(LAKEBASE_USER)" ] || [ -z "$(LAKEBASE_PASSWORD)" ]; then \
		echo "✘ Missing Lakebase env vars. Set LAKEBASE_HOST, LAKEBASE_DATABASE, LAKEBASE_USER, LAKEBASE_PASSWORD in .env"; \
		exit 1; \
	fi
	@echo "▸ Creating raw_tags table in Lakebase ($(LAKEBASE_HOST)/$(LAKEBASE_DATABASE))..."
	PGPASSWORD="$(LAKEBASE_PASSWORD)" PGSSLMODE=require psql \
		-h "$(LAKEBASE_HOST)" \
		-p "$(or $(LAKEBASE_PORT),5432)" \
		-U "$(LAKEBASE_USER)" \
		-d "$(LAKEBASE_DATABASE)" \
		-f onboarding/lakebase/create_raw_tags.sql
	@echo "✔ Lakebase table created"

.PHONY: db-lakebase-test
db-lakebase-test: ## Test Lakebase connection (SELECT 1)
	@if [ -z "$(LAKEBASE_HOST)" ] || [ -z "$(LAKEBASE_USER)" ] || [ -z "$(LAKEBASE_PASSWORD)" ]; then \
		echo "✘ Missing Lakebase env vars"; exit 1; \
	fi
	@echo "▸ Testing Lakebase connection..."
	@PGPASSWORD="$(LAKEBASE_PASSWORD)" PGSSLMODE=require psql \
		-h "$(LAKEBASE_HOST)" \
		-p "$(or $(LAKEBASE_PORT),5432)" \
		-U "$(LAKEBASE_USER)" \
		-d "$(or $(LAKEBASE_DATABASE),databricks_postgres)" \
		-c "SELECT 1 AS connected" && echo "✔ Lakebase connection OK" || echo "✘ Connection failed"

.PHONY: db-lakebase-provision-direct
db-lakebase-provision-direct: ## Provision Lakebase via SDK/CLI + create connector role + grants + connector artifact
	@if [ -z "$(LAKEBASE_USER)" ] || [ -z "$(LAKEBASE_PASSWORD)" ]; then \
		echo "✘ Missing Lakebase admin credentials. Set LAKEBASE_USER and LAKEBASE_PASSWORD in .env"; \
		exit 1; \
	fi
	@echo "▸ Provisioning Lakebase direct deployment artifacts..."
	DATABRICKS_CONFIG_PROFILE=$(DATABRICKS_CONFIG_PROFILE) \
	DATABRICKS_HOST=$(or $(DATABRICKS_HOST),$(WS_HOST)) \
	CATALOG=$(CATALOG) \
	SCHEMA=$(SCHEMA) \
	DATABRICKS_WAREHOUSE_ID=$(DATABRICKS_WAREHOUSE_ID) \
	SP_PROFILE_NAME=$(SP_PROFILE_NAME) \
	SP_APPLICATION_ID=$(SP_APPLICATION_ID) \
	LAKEBASE_INSTANCE_NAME=$(LAKEBASE_INSTANCE_NAME) \
	LAKEBASE_INSTANCE_CAPACITY=$(LAKEBASE_INSTANCE_CAPACITY) \
	LAKEBASE_DATABASE=$(or $(LAKEBASE_DATABASE),databricks_postgres) \
	LAKEBASE_PORT=$(or $(LAKEBASE_PORT),5432) \
	LAKEBASE_USER=$(LAKEBASE_USER) \
	LAKEBASE_PASSWORD=$(LAKEBASE_PASSWORD) \
	LAKEBASE_TABLE=$(or $(LAKEBASE_TABLE),raw_tags) \
	CONNECTOR_ROLE_NAME=$(or $(CONNECTOR_ROLE_NAME),zerobus_connector) \
	LAKEBASE_CONNECTOR_ARTIFACT=$(LAKEBASE_CONNECTOR_ARTIFACT) \
		uv run --with databricks-sdk --with psycopg[binary] python onboarding/databricks/provision_lakebase_direct.py
	@echo "✔ Direct Lakebase provisioning complete"

.PHONY: db-clean
db-clean: ## Drop catalog CASCADE, delete pipeline and app (clean Databricks for full reset)
	@echo "▸ Cleaning Databricks (catalog=$(CATALOG), pipeline=$(PIPELINE_NAME), app=zerobus-ignition-agl)..."
	DATABRICKS_CONFIG_PROFILE=$(DATABRICKS_CONFIG_PROFILE) \
	DATABRICKS_HOST=$(or $(DATABRICKS_HOST),$(WS_HOST)) \
	CATALOG=$(CATALOG) \
	PIPELINE_NAME="$(PIPELINE_NAME)" \
	DATABRICKS_WAREHOUSE_ID=$(DATABRICKS_WAREHOUSE_ID) \
		uv run --with databricks-sdk python onboarding/databricks/clean_databricks.py
	@echo "✔ Databricks clean complete"

# ──────────────────────────────────────────────────────────────
# Wheel build + upload to UC volume
# ──────────────────────────────────────────────────────────────

.PHONY: db-wheel-build
db-wheel-build: ## Build agl_analytics wheel
	@echo "▸ Building wheel..."
	uv build $(SDP_DIR)
	@echo "✔ Wheel built: $(SDP_DIR)/dist/$(WHEEL_FILE)"

.PHONY: db-wheel-upload
db-wheel-upload: ## Upload agl_analytics wheel to UC volume
	@test -f $(SDP_DIR)/dist/$(WHEEL_FILE) || \
		(echo "✘ Wheel not found. Run: make db-wheel-build" && exit 1)
	@echo "▸ Uploading wheel to /Volumes/$(CATALOG)/$(SCHEMA)/wheels/$(WHEEL_FILE)..."
	DATABRICKS_CONFIG_PROFILE=$(DATABRICKS_CONFIG_PROFILE) \
	DATABRICKS_HOST=$(or $(DATABRICKS_HOST),$(WS_HOST)) \
		databricks fs cp $(SDP_DIR)/dist/$(WHEEL_FILE) \
			"dbfs:/Volumes/$(CATALOG)/$(SCHEMA)/wheels/$(WHEEL_FILE)" --overwrite
	@echo "✔ Wheel uploaded"

.PHONY: db-wheel
db-wheel: db-wheel-build db-wheel-upload ## Build + upload wheel to UC volume

# ──────────────────────────────────────────────────────────────
# SDP pipeline (Git-backed, created/updated via SDK)
# ──────────────────────────────────────────────────────────────

.PHONY: db-pipeline
db-pipeline: ## Create or update SDP pipeline (Git folder in workspace)
	@echo "▸ Deploying pipeline '$(PIPELINE_NAME)' -> $(REPO_PATH)/pipelines/sdp..."
	DATABRICKS_CONFIG_PROFILE=$(DATABRICKS_CONFIG_PROFILE) \
	DATABRICKS_HOST=$(or $(DATABRICKS_HOST),$(WS_HOST)) \
	CATALOG=$(CATALOG) \
	SCHEMA=$(SCHEMA) \
	PIPELINE_NAME="$(PIPELINE_NAME)" \
		uv run --with databricks-sdk python onboarding/databricks/deploy_pipeline_sdk.py \
			--repo-path "$(REPO_PATH)"
	@echo "✔ Pipeline deployed"

.PHONY: db-pipeline-upload
db-pipeline-upload: ## Create/update pipeline + build/upload wheel
	@echo "▸ Deploying pipeline with --upload-wheel..."
	DATABRICKS_CONFIG_PROFILE=$(DATABRICKS_CONFIG_PROFILE) \
	DATABRICKS_HOST=$(or $(DATABRICKS_HOST),$(WS_HOST)) \
	CATALOG=$(CATALOG) \
	SCHEMA=$(SCHEMA) \
	PIPELINE_NAME="$(PIPELINE_NAME)" \
		uv run --with databricks-sdk python onboarding/databricks/deploy_pipeline_sdk.py \
			--repo-path "$(REPO_PATH)" --upload-wheel
	@echo "✔ Pipeline deployed with wheel"

.PHONY: db-verify-ml
db-verify-ml: ## Run health_scores verification query; exit 0 if ML path active (ml_health non-null)
	DATABRICKS_CONFIG_PROFILE=$(DATABRICKS_CONFIG_PROFILE) \
	DATABRICKS_HOST=$(or $(DATABRICKS_HOST),$(WS_HOST)) \
	CATALOG=$(CATALOG) \
	SCHEMA=$(SCHEMA) \
	DATABRICKS_WAREHOUSE_ID=$(DATABRICKS_WAREHOUSE_ID) \
		uv run --with databricks-sdk python onboarding/databricks/verify_ml_health.py

.PHONY: db-train-health-model
db-train-health-model: ## Create/update train_health_model job, run it, wait until model registered in UC
	DATABRICKS_CONFIG_PROFILE=$(DATABRICKS_CONFIG_PROFILE) \
	DATABRICKS_HOST=$(or $(DATABRICKS_HOST),$(WS_HOST)) \
	CATALOG=$(CATALOG) \
	SCHEMA=$(SCHEMA) \
	REPO_PATH="$(REPO_PATH)" \
		uv run --with databricks-sdk python onboarding/databricks/create_train_health_model_job.py \
			--repo-path "$(REPO_PATH)"

# ──────────────────────────────────────────────────────────────
# Databricks App (Git-backed via SDK)
# ──────────────────────────────────────────────────────────────

.PHONY: db-app-deploy
db-app-deploy: ## Deploy Databricks App from GitHub (SDK) + UC grants for app SP
	@echo "▸ Deploying app from GitHub via SDK..."
	DATABRICKS_CONFIG_PROFILE=$(DATABRICKS_CONFIG_PROFILE) \
	DATABRICKS_HOST=$(or $(DATABRICKS_HOST),$(WS_HOST)) \
		uv run --with databricks-sdk python onboarding/databricks/deploy_zerobus_app_from_github.py
	@echo "✔ App deployed (and UC grants applied for app SP)"

.PHONY: db-app-deploy-direct
db-app-deploy-direct: db-bundle-preflight-direct db-lakebase-provision-direct ## Deploy app via DAB direct deployment with Lakebase app resource
	@echo "▸ Deploying app with DAB direct deployment (Lakebase resource enabled)..."
	DATABRICKS_CONFIG_PROFILE=$(DATABRICKS_CONFIG_PROFILE) \
	DATABRICKS_HOST=$(or $(DATABRICKS_HOST),$(WS_HOST)) \
	DATABRICKS_BUNDLE_ENGINE=$(BUNDLE_ENGINE) \
		databricks bundle deploy -t production \
			--var="catalog=$(CATALOG)" \
			--var="schema=$(SCHEMA)" \
			--var="lakebase_instance_name=$(LAKEBASE_INSTANCE_NAME)" \
			--var="lakebase_instance_capacity=$(LAKEBASE_INSTANCE_CAPACITY)" \
			--var="lakebase_database_name=$(or $(LAKEBASE_DATABASE),databricks_postgres)" \
			--var="connector_role_name=$(or $(CONNECTOR_ROLE_NAME),zerobus_connector)"
	DATABRICKS_CONFIG_PROFILE=$(DATABRICKS_CONFIG_PROFILE) \
	DATABRICKS_HOST=$(or $(DATABRICKS_HOST),$(WS_HOST)) \
	DATABRICKS_BUNDLE_ENGINE=$(BUNDLE_ENGINE) \
		databricks bundle run zerobus_ignition_agl -t production \
			--var="catalog=$(CATALOG)" \
			--var="schema=$(SCHEMA)" \
			--var="lakebase_instance_name=$(LAKEBASE_INSTANCE_NAME)" \
			--var="lakebase_instance_capacity=$(LAKEBASE_INSTANCE_CAPACITY)" \
			--var="lakebase_database_name=$(or $(LAKEBASE_DATABASE),databricks_postgres)" \
			--var="connector_role_name=$(or $(CONNECTOR_ROLE_NAME),zerobus_connector)"
	@echo "▸ Re-applying Lakebase grants after app deploy to capture app SP role..."
	$(MAKE) db-lakebase-provision-direct
	@echo "✔ App direct deployment and run complete"

.PHONY: db-bundle-preflight-direct
db-bundle-preflight-direct: ## Validate Databricks CLI supports DAB direct engine (>= 0.279.0)
	@if ! command -v databricks >/dev/null 2>&1; then \
		echo "✘ Databricks CLI not found in PATH"; \
		exit 1; \
	fi
	@ver="$$(databricks version 2>/dev/null | sed -E 's/.*([0-9]+\.[0-9]+\.[0-9]+).*/\1/' | awk 'NR==1{print $$1}')"; \
	if [ -z "$$ver" ]; then \
		echo "✘ Could not parse Databricks CLI version"; \
		echo "  Install/upgrade CLI to >= 0.$(MIN_DATABRICKS_CLI_MINOR).0"; \
		exit 1; \
	fi; \
	major="$$(echo $$ver | cut -d. -f1)"; \
	minor="$$(echo $$ver | cut -d. -f2)"; \
	if [ "$$major" -eq 0 ] && [ "$$minor" -lt "$(MIN_DATABRICKS_CLI_MINOR)" ]; then \
		echo "✘ Databricks CLI $$ver is too old for direct deployment engine"; \
		echo "  Upgrade to >= 0.$(MIN_DATABRICKS_CLI_MINOR).0"; \
		exit 1; \
	fi; \
	echo "✔ Databricks CLI $$ver supports direct deployment engine"

.PHONY: db-bundle-migrate-direct
db-bundle-migrate-direct: db-bundle-preflight-direct ## One-time migrate bundle state from terraform to direct engine
	@echo "▸ Migrating bundle deployment state to direct engine (production target)..."
	DATABRICKS_CONFIG_PROFILE=$(DATABRICKS_CONFIG_PROFILE) \
	DATABRICKS_HOST=$(or $(DATABRICKS_HOST),$(WS_HOST)) \
	DATABRICKS_BUNDLE_ENGINE=$(BUNDLE_ENGINE) \
		databricks bundle deployment migrate -t production
	@echo "▸ Verifying migrated state with bundle plan..."
	DATABRICKS_CONFIG_PROFILE=$(DATABRICKS_CONFIG_PROFILE) \
	DATABRICKS_HOST=$(or $(DATABRICKS_HOST),$(WS_HOST)) \
	DATABRICKS_BUNDLE_ENGINE=$(BUNDLE_ENGINE) \
		databricks bundle plan -t production
	@echo "✔ Bundle state migration verified"

.PHONY: db-app-grant
db-app-grant: ## Run UC grants for the app's service principal only (no deploy)
	@echo "▸ Running UC grants for app SP..."
	DATABRICKS_CONFIG_PROFILE=$(DATABRICKS_CONFIG_PROFILE) DATABRICKS_HOST=$(or $(DATABRICKS_HOST),$(WS_HOST)) CATALOG=$(CATALOG) SCHEMA=$(SCHEMA) DATABRICKS_WAREHOUSE_ID=$(DATABRICKS_WAREHOUSE_ID) \
		uv run --with databricks-sdk python onboarding/databricks/deploy_zerobus_app_from_github.py --grant-only
	@echo "✔ App SP grants done"

# ──────────────────────────────────────────────────────────────
# Repo sync (git pull in workspace)
# ──────────────────────────────────────────────────────────────

.PHONY: db-repo-sync
db-repo-sync: ## Pull latest from $(REPO_BRANCH) into workspace repo
	@echo "▸ Syncing workspace repo $(REPO_PATH) to branch $(REPO_BRANCH)..."
	@DATABRICKS_CONFIG_PROFILE=$(DATABRICKS_CONFIG_PROFILE) DATABRICKS_HOST=$(or $(DATABRICKS_HOST),$(WS_HOST)) \
		uv run --with databricks-sdk python onboarding/databricks/repo_sync.py "$(REPO_PATH)" "$(REPO_BRANCH)"

# ──────────────────────────────────────────────────────────────
# Simulator (synthetic OT data generation)
# ──────────────────────────────────────────────────────────────

.PHONY: simulate-83
simulate-83: ## [Step 6] Start synthetic data generation against 8.3 gateway
	@echo "▸ Starting AGL Fleet Simulator ($(SIM_SITES) sites, $(SIM_UNITS) units/site)..."
	cd examples/agl_fleet && \
		uv run agl-sim \
			--gateway http://localhost:$(PORT_83) \
			--sites $(SIM_SITES) \
			--units $(SIM_UNITS) \
			--interval $(SIM_INTERVAL) \
			--ticks $(SIM_TICKS)

.PHONY: simulate-81
simulate-81: ## Start synthetic data generation against 8.1 gateway
	cd examples/agl_fleet && \
		uv run agl-sim \
			--gateway http://localhost:$(PORT_81) \
			--sites $(SIM_SITES) \
			--units $(SIM_UNITS) \
			--interval $(SIM_INTERVAL) \
			--ticks $(SIM_TICKS)

.PHONY: simulate-dry-run
simulate-dry-run: ## Dry-run simulator (generate events, don't send)
	cd examples/agl_fleet && \
		uv run agl-sim --dry-run \
			--sites $(SIM_SITES) \
			--units $(SIM_UNITS) \
			--ticks 10

# ──────────────────────────────────────────────────────────────
# Links / status (all URLs for easy navigation)
# ──────────────────────────────────────────────────────────────

.PHONY: links-83
links-83: ## [Step 7] Print all URLs for workspace, app, gateway, pipeline
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo " Zerobus Ignition — Quick Links"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@echo " Ignition Gateway"
	@echo "   http://localhost:$(PORT_83)"
	@echo "   Health:  http://localhost:$(PORT_83)/system/zerobus/health"
	@echo "   Diag:    http://localhost:$(PORT_83)/system/zerobus/diagnostics"
	@echo ""
	@echo " Databricks Workspace"
	@WS_HOST=$$(awk '/^\[$(DATABRICKS_CONFIG_PROFILE)\]/{found=1} found && /^host/{gsub(/^[^=]+=[ \t]*/,""); print; exit}' ~/.databrickscfg 2>/dev/null); \
	if [ -n "$$WS_HOST" ]; then \
		echo "   $$WS_HOST"; \
		echo "   Catalog: $$WS_HOST/explore/data/$(CATALOG)/$(SCHEMA)"; \
		echo "   Apps:    $$WS_HOST/apps"; \
		echo "   Pipelines: $$WS_HOST/pipelines"; \
	else \
		echo "   (could not read host from [$(DATABRICKS_CONFIG_PROFILE)] profile)"; \
	fi
	@echo ""
	@echo " Key Make commands"
	@echo "   make simulate-83      Start synthetic data"
	@echo "   make health-83        Gateway health check"
	@echo "   make diag-83          Full diagnostics"
	@echo "   make logs-83          Gateway container logs"
	@echo "   make stop-83          Stop gateway"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ──────────────────────────────────────────────────────────────
# Convenience combos
# ──────────────────────────────────────────────────────────────

.PHONY: all-83
all-83: build-83 up-83 ## Build + start 8.3 (still need setup wizard + configure)

.PHONY: all-81
all-81: build-81 up-81 ## Build + start 8.1 (still need configure)

.PHONY: db-all
db-all: db-create-sp db-setup-sql db-wheel db-repo-sync db-pipeline db-app-deploy ## Full Databricks setup (SP + SQL + wheel + repo sync + pipeline + app)

.PHONY: db-all-direct
db-all-direct: db-create-sp db-setup-sql db-wheel db-repo-sync db-pipeline db-app-deploy-direct ## Full Databricks setup with DAB direct app deployment

.PHONY: bootstrap-83
bootstrap-83: db-all-direct build-83 up-83 ## Everything from scratch using DAB direct app deploy (steps 1-4, then manual 4b-7)
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo " Bootstrap complete! (Steps 1-4 done)"
	@echo ""
	@echo " ✔ Step 1: SP '$(SP_NAME)' created (profile: $(SP_PROFILE_NAME))"
	@echo " ✔ Step 2: $(CATALOG).$(SCHEMA) + tables + app + pipeline deployed"
	@echo " ✔ Step 3: Ignition module built"
	@echo " ✔ Step 4: Gateway started on http://localhost:$(PORT_83)"
	@echo ""
	@echo " Continue with (run in this order):"
	@echo "   4b  make setup-wizard-83       Complete Ignition setup in browser"
	@echo "   5   make configure-83          Push SP credentials to gateway"
	@echo "   6   make simulate-83           Start synthetic data generation"
	@echo "   7   make links-83              Show all URLs"
	@echo "   8   make db-train-health-model (optional) Train health model, register in UC"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

.PHONY: next-steps-83
next-steps-83: ## Print post-bootstrap steps (4b–8) in sequence
	@echo ""
	@echo " Continue with (run in this order):"
	@echo "   4b  make setup-wizard-83       Complete Ignition setup in browser"
	@echo "   5   make configure-83          Push SP credentials to gateway"
	@echo "   6   make simulate-83           Start synthetic data generation"
	@echo "   7   make links-83              Show all URLs"
	@echo "   8   make db-train-health-model (optional) Train health model, register in UC"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""

.PHONY: redeploy
redeploy: ## Print steps to redeploy to a new workspace (see CLAUDE.md)
	@echo "Redeploy to a new workspace:"
	@echo "  1. In ~/.databrickscfg set [$(DATABRICKS_CONFIG_PROFILE)] host = new workspace URL"
	@echo "  2. Create SQL warehouse in new workspace; set DATABRICKS_WAREHOUSE_ID=<id>"
	@echo "  3. Clone this repo in workspace (Repos); set REPO_PATH=/Repos/.../lakeflow-ignition-zerobus-connector"
	@echo "  4. make db-create-sp"
	@echo "  5. DATABRICKS_WAREHOUSE_ID=<id> make db-setup-sql"
	@echo "  6. make db-wheel"
	@echo "  7. REPO_PATH=/Repos/... make db-pipeline"
	@echo "  8. make db-app-deploy-direct"
	@echo "  9. make build-83 up-83 && make setup-wizard-83 && make configure-83"
	@echo "  Set WORKSPACE_ID and DATABRICKS_REGION (or ZEROBUS_ENDPOINT) in env or .env; Make derives endpoint if unset."

# ──────────────────────────────────────────────────────────────
# Help
# ──────────────────────────────────────────────────────────────

.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help
	@echo "Zerobus Ignition — Gateway + Databricks"
	@echo ""
	@echo "══ From scratch (7 steps) ══════════════════"
	@echo ""
	@printf "  \033[36mmake bootstrap-83\033[0m         Steps 1-4 (automated)\n"
	@echo "    Step 1: Create SP, generate OAuth secret, assign to workspace"
	@echo "    Step 2: Create catalog/schema/tables, deploy app + pipeline"
	@echo "    Step 3: Build Ignition + Zerobus module"
	@echo "    Step 4: Start Ignition gateway"
	@echo ""
	@printf "  \033[36mmake setup-wizard-83\033[0m      Step 4b: Accept EULA + create admin (browser)\n"
	@printf "  \033[36mmake configure-83\033[0m         Step 5:  Push SP credentials to gateway\n"
	@printf "  \033[36mmake simulate-83\033[0m          Step 6:  Start synthetic data generation\n"
	@printf "  \033[36mmake links-83\033[0m             Step 7:  Print all URLs\n"
	@printf "  \033[36mmake db-train-health-model\033[0m Step 8:  (optional) Train health model, register in UC\n"
	@echo ""
	@echo "══ Full reset (clean Databricks + Ignition, then bootstrap) ══"
	@echo "  make db-clean clean-83 bootstrap-83"
	@echo "  then: make setup-wizard-83 configure-83 simulate-83 links-83"
	@echo ""
	@echo "══ Individual targets ══════════════════════"
	@echo ""
	@echo "── Gateway ─────────────────────────────────"
	@grep -E '^(build|up|start|stop|clean|logs|setup-wizard|restore|configure|configure-postgres|configure-zerobus|configure-lakebase|health|diag|test-connection|all)-[0-9]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-24s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "── Databricks ──────────────────────────────"
	@grep -E '^db-[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-24s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "── Simulator ───────────────────────────────"
	@grep -E '^simulate-[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-24s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "── Links ───────────────────────────────────"
	@grep -E '^links-[0-9]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-24s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "── Overrides (or set once in .env and source before make) ──"
	@echo "  DATABRICKS_WAREHOUSE_ID=<id> WORKSPACE_ID=<id> DATABRICKS_REGION=<region>  (used everywhere)"
	@echo "  CATALOG=x SCHEMA=y make db-setup-sql"
	@echo "  SKIP_CATALOG_CREATE=1 make db-setup-sql   (if catalog exists / no CREATE CATALOG permission)"
	@echo "  Heavier sim (data in ~30–60s): SIM_SITES=5 SIM_UNITS=4 SIM_INTERVAL=500 make simulate-83"
	@echo "  SIM_SITES=5 SIM_UNITS=4 make simulate-83"
	@echo "  REPO_PATH=/Repos/me@co.com/repo make db-pipeline"
	@echo "  SP_NAME=my-sp SP_PROFILE_NAME=my-sp make db-create-sp"
