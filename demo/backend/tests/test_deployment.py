"""Tests for deployment configuration - app.yaml, package.json, README."""

from pathlib import Path

import yaml
import pytest

DEMO_DIR = Path(__file__).resolve().parent.parent.parent
APP_DIR = DEMO_DIR / "app"
REPO_ROOT = DEMO_DIR.parent


class TestAppYaml:
    @pytest.fixture(autouse=True)
    def _load(self):
        self.content = (APP_DIR / "app.yaml").read_text()
        self.yaml = yaml.safe_load(self.content)

    def test_exists_and_valid(self):
        assert self.yaml is not None
        assert isinstance(self.yaml, dict)

    def test_has_command(self):
        assert "command" in self.yaml
        assert isinstance(self.yaml["command"], list)

    def test_has_warehouse_value_from(self):
        assert "env" in self.yaml
        wh = [e for e in self.yaml["env"] if e.get("valueFrom") == "sql-warehouse"]
        assert len(wh) == 1
        assert wh[0]["name"] == "DATABRICKS_WAREHOUSE_ID"

    def test_no_hardcoded_secrets(self):
        lower = self.content.lower()
        assert "dapi" not in lower
        assert "token" not in lower
        assert "password" not in lower
        assert "secret" not in lower
        for entry in self.yaml["env"]:
            if "value" in entry:
                assert len(str(entry["value"])) < 50


class TestAppPackageJson:
    def test_exists_alongside_app_yaml(self):
        assert (APP_DIR / "app.yaml").exists()
        # For Python apps, we need requirements.txt or package.json for frontend build
        assert (APP_DIR / "requirements.txt").exists() or (APP_DIR / "package.json").exists()

    def test_requirements_has_fastapi(self):
        req = (APP_DIR / "requirements.txt").read_text()
        assert "fastapi" in req
        assert "uvicorn" in req


class TestReadme:
    def test_has_deployment_section(self):
        readme = (REPO_ROOT / "README.md").read_text()
        assert "Deploying to Databricks Apps" in readme
