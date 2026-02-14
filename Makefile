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
#             db-app-deploy
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

# ── Zerobus config ───────────────────────────────────────────
ZEROBUS_ENDPOINT ?= 7405607216190670.zerobus.eastus2.azuredatabricks.net
DATABRICKS_PROFILE ?= daveok

# ── Databricks / pipeline / app ──────────────────────────────
CATALOG       ?= agl_demo
SCHEMA        ?= ot
WAREHOUSE_ID  ?= e65d34bf5b095b0f
REPO_PATH     ?= /Users/david.okeeffe@databricks.com/lakeflow-ignition-zerobus-connector
PIPELINE_NAME ?= [production] agl-etl
BUNDLE_TARGET ?= production
REPO_BRANCH   ?= main

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
	@echo "  workspace from profile [$(SP_PROFILE_NAME)]; endpoint=$(ZEROBUS_ENDPOINT); table=$(CATALOG).$(SCHEMA).zerobus_events"
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
	@echo "  workspace from profile [$(SP_PROFILE_NAME)]; endpoint=$(ZEROBUS_ENDPOINT); table=$(CATALOG).$(SCHEMA).zerobus_events"
	cd examples/agl_fleet && \
		CATALOG=$(CATALOG) SCHEMA=$(SCHEMA) \
		uv run --extra setup agl-sim --setup-only \
			--profile $(SP_PROFILE_NAME) \
			--zerobus-endpoint $(ZEROBUS_ENDPOINT) \
			--gateway http://localhost:$(PORT_81)
	@echo "✔ Configuration pushed. Run: make health-81"

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
	DATABRICKS_CONFIG_PROFILE=$(DATABRICKS_PROFILE) \
	CATALOG=$(CATALOG) SCHEMA=$(SCHEMA) WAREHOUSE_ID=$(WAREHOUSE_ID) \
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

.PHONY: db-create-sp
db-create-sp: ## Create SP, generate OAuth secret, write ~/.databrickscfg profile
	@echo "▸ Creating service principal '$(SP_NAME)'..."
	CATALOG=$(CATALOG) \
	SCHEMA=$(SCHEMA) \
	WAREHOUSE_ID=$(WAREHOUSE_ID) \
		uv run --with databricks-sdk python onboarding/databricks/create_service_principal.py \
			--sp-name "$(SP_NAME)" \
			--profile-name "$(SP_PROFILE_NAME)" \
			--workspace-profile "$(DATABRICKS_PROFILE)"

.PHONY: db-create-sp-no-grants
db-create-sp-no-grants: ## Create SP without running UC grants
	@echo "▸ Creating service principal '$(SP_NAME)' (skip grants)..."
	uv run --with databricks-sdk python onboarding/databricks/create_service_principal.py \
		--sp-name "$(SP_NAME)" \
		--profile-name "$(SP_PROFILE_NAME)" \
		--workspace-profile "$(DATABRICKS_PROFILE)" \
		--skip-grants

.PHONY: db-check-sp
db-check-sp: ## Check [agl-demo] profile and verify SP OAuth secret works
	@echo "▸ Checking SP profile [$(SP_PROFILE_NAME)] and secret..."
	SP_PROFILE_NAME="$(SP_PROFILE_NAME)" uv run --with databricks-sdk python onboarding/databricks/check_sp_and_secret.py
	@echo "✔ SP and secret OK. Use this profile for: make configure-83"

# ──────────────────────────────────────────────────────────────
# Catalog / schema / tables / grants
# ──────────────────────────────────────────────────────────────

.PHONY: db-setup-sql
db-setup-sql: ## Run setup SQL (catalog, schema, tables, SP grants)
	@echo "▸ Running setup SQL (catalog=$(CATALOG), schema=$(SCHEMA), SP=$(SP_APPLICATION_ID))..."
	DATABRICKS_CONFIG_PROFILE=$(DATABRICKS_PROFILE) \
	CATALOG=$(CATALOG) \
	SCHEMA=$(SCHEMA) \
	WAREHOUSE_ID=$(WAREHOUSE_ID) \
	SP_APPLICATION_ID=$(SP_APPLICATION_ID) \
		uv run --with databricks-sdk python onboarding/databricks/run_setup_sql.py
	@echo "✔ Setup SQL complete"

.PHONY: db-clean
db-clean: ## Drop catalog CASCADE, delete pipeline and app (clean Databricks for full reset)
	@echo "▸ Cleaning Databricks (catalog=$(CATALOG), pipeline=$(PIPELINE_NAME), app=zerobus-ignition-agl)..."
	DATABRICKS_CONFIG_PROFILE=$(DATABRICKS_PROFILE) \
	CATALOG=$(CATALOG) \
	PIPELINE_NAME="$(PIPELINE_NAME)" \
	WAREHOUSE_ID=$(WAREHOUSE_ID) \
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
	DATABRICKS_CONFIG_PROFILE=$(DATABRICKS_PROFILE) \
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
	DATABRICKS_CONFIG_PROFILE=$(DATABRICKS_PROFILE) \
	CATALOG=$(CATALOG) \
	SCHEMA=$(SCHEMA) \
	PIPELINE_NAME="$(PIPELINE_NAME)" \
		uv run --with databricks-sdk python onboarding/databricks/deploy_pipeline_sdk.py \
			--repo-path "$(REPO_PATH)"
	@echo "✔ Pipeline deployed"

.PHONY: db-pipeline-upload
db-pipeline-upload: ## Create/update pipeline + build/upload wheel
	@echo "▸ Deploying pipeline with --upload-wheel..."
	DATABRICKS_CONFIG_PROFILE=$(DATABRICKS_PROFILE) \
	CATALOG=$(CATALOG) \
	SCHEMA=$(SCHEMA) \
	PIPELINE_NAME="$(PIPELINE_NAME)" \
		uv run --with databricks-sdk python onboarding/databricks/deploy_pipeline_sdk.py \
			--repo-path "$(REPO_PATH)" --upload-wheel
	@echo "✔ Pipeline deployed with wheel"

.PHONY: db-verify-ml
db-verify-ml: ## Run health_scores verification query; exit 0 if ML path active (ml_health non-null)
	DATABRICKS_CONFIG_PROFILE=$(DATABRICKS_PROFILE) \
	CATALOG=$(CATALOG) \
	SCHEMA=$(SCHEMA) \
	WAREHOUSE_ID=$(WAREHOUSE_ID) \
		uv run --with databricks-sdk python onboarding/databricks/verify_ml_health.py

.PHONY: db-train-health-model
db-train-health-model: ## Create/update train_health_model job, run it, wait until model registered in UC
	DATABRICKS_CONFIG_PROFILE=$(DATABRICKS_PROFILE) \
	CATALOG=$(CATALOG) \
	SCHEMA=$(SCHEMA) \
	REPO_PATH="$(REPO_PATH)" \
		uv run --with databricks-sdk python onboarding/databricks/create_train_health_model_job.py \
			--repo-path "$(REPO_PATH)"

# ──────────────────────────────────────────────────────────────
# Databricks App (Git-backed via SDK or Asset Bundle)
# ──────────────────────────────────────────────────────────────

.PHONY: db-app-deploy
db-app-deploy: ## Deploy Databricks App from GitHub (SDK) + UC grants for app SP
	@echo "▸ Deploying app from GitHub via SDK..."
	DATABRICKS_CONFIG_PROFILE=$(DATABRICKS_PROFILE) \
		uv run --with databricks-sdk python onboarding/databricks/deploy_zerobus_app_from_github.py
	@echo "✔ App deployed (and UC grants applied for app SP)"

.PHONY: db-app-grant
db-app-grant: ## Run UC grants for the app's service principal only (no deploy)
	@echo "▸ Running UC grants for app SP..."
	DATABRICKS_CONFIG_PROFILE=$(DATABRICKS_PROFILE) CATALOG=$(CATALOG) SCHEMA=$(SCHEMA) WAREHOUSE_ID=$(WAREHOUSE_ID) \
		uv run --with databricks-sdk python onboarding/databricks/deploy_zerobus_app_from_github.py --grant-only
	@echo "✔ App SP grants done"

.PHONY: db-bundle-deploy
db-bundle-deploy: ## Deploy Databricks App via Asset Bundle
	@echo "▸ Deploying bundle (target=$(BUNDLE_TARGET))..."
	databricks bundle deploy -t $(BUNDLE_TARGET)
	@echo "✔ Bundle deployed"

.PHONY: db-app-start
db-app-start: ## Start the Databricks App via bundle
	@echo "▸ Starting app via bundle (target=$(BUNDLE_TARGET))..."
	databricks bundle run zerobus_ignition_agl -t $(BUNDLE_TARGET)
	@echo "✔ App started"

.PHONY: db-bundle
db-bundle: db-bundle-deploy db-app-start ## Deploy + start app via Asset Bundle

# ──────────────────────────────────────────────────────────────
# Repo sync (git pull in workspace)
# ──────────────────────────────────────────────────────────────

.PHONY: db-repo-sync
db-repo-sync: ## Pull latest from $(REPO_BRANCH) into workspace repo
	@echo "▸ Syncing workspace repo $(REPO_PATH) to branch $(REPO_BRANCH)..."
	@DATABRICKS_CONFIG_PROFILE=$(DATABRICKS_PROFILE) \
		uv run --with databricks-sdk python -c "\
from databricks.sdk import WorkspaceClient; \
w = WorkspaceClient(); \
repos = [r for r in w.repos.list(path_prefix='$(REPO_PATH)') if r.path.rstrip('/') == '$(REPO_PATH)'.rstrip('/')]; \
assert repos, 'Repo not found at $(REPO_PATH)'; \
r = repos[0]; \
w.repos.update(repo_id=r.id, branch='$(REPO_BRANCH)'); \
print(f'✔ Repo {r.path} (id={r.id}) synced to $(REPO_BRANCH)')"

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
	@WS_HOST=$$(awk '/^\[$(DATABRICKS_PROFILE)\]/{found=1} found && /^host/{gsub(/^[^=]+=[ \t]*/,""); print; exit}' ~/.databrickscfg 2>/dev/null); \
	if [ -n "$$WS_HOST" ]; then \
		echo "   $$WS_HOST"; \
		echo "   Catalog: $$WS_HOST/explore/data/$(CATALOG)/$(SCHEMA)"; \
		echo "   Apps:    $$WS_HOST/apps"; \
		echo "   Pipelines: $$WS_HOST/pipelines"; \
	else \
		echo "   (could not read host from [$(DATABRICKS_PROFILE)] profile)"; \
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
db-all: db-create-sp db-setup-sql db-wheel db-pipeline db-app-deploy ## Full Databricks setup (SP + SQL + wheel + pipeline + app)

.PHONY: bootstrap-83
bootstrap-83: db-all build-83 up-83 ## Everything from scratch (steps 1-4, then manual 4b-7)
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo " Bootstrap complete! (Steps 1-4 done)"
	@echo ""
	@echo " ✔ Step 1: SP '$(SP_NAME)' created (profile: $(SP_PROFILE_NAME))"
	@echo " ✔ Step 2: $(CATALOG).$(SCHEMA) + tables + app + pipeline deployed"
	@echo " ✔ Step 3: Ignition module built"
	@echo " ✔ Step 4: Gateway started on http://localhost:$(PORT_83)"
	@echo ""
	@echo " Continue with:"
	@echo "   make setup-wizard-83    Step 4b: Complete Ignition setup in browser"
	@echo "   make configure-83       Step 5:  Push SP credentials to gateway"
	@echo "   make simulate-83        Step 6:  Start synthetic data generation"
	@echo "   make links-83           Step 7:  Show all URLs"
	@echo "   make db-train-health-model  Step 8:  (optional) Train health model, register in UC"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

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
	@grep -E '^(build|up|start|stop|clean|logs|setup-wizard|restore|configure|health|diag|test-connection|all)-[0-9]+:.*?## .*$$' $(MAKEFILE_LIST) | \
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
	@echo "── Overrides ───────────────────────────────"
	@echo "  CATALOG=x SCHEMA=y make db-setup-sql"
	@echo "  Heavier sim (data in ~30–60s): SIM_SITES=5 SIM_UNITS=4 SIM_INTERVAL=500 make simulate-83"
	@echo "  SIM_SITES=5 SIM_UNITS=4 make simulate-83"
	@echo "  REPO_PATH=/Repos/me@co.com/repo make db-pipeline"
	@echo "  SP_NAME=my-sp SP_PROFILE_NAME=my-sp make db-create-sp"
