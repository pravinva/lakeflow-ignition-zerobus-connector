# Databricks notebook source
# MAGIC %md
# MAGIC # 00 - Prereqs & Permissions (Notebook, `%sql`)
# MAGIC
# MAGIC This notebook is the notebook-first equivalent of:
# MAGIC - `onboarding/tilt/databricks/sql/00_prereqs_and_permissions.sql`
# MAGIC
# MAGIC It uses widgets + `%sql` so you can run it without the Databricks SQL editor “add parameter” prompt.

# COMMAND ----------
# Create widgets (run this cell first to see widgets)
dbutils.widgets.text("catalog", "ignition_demo", "Catalog")
dbutils.widgets.text("schema", "tilt_ot", "Schema")
dbutils.widgets.text("sp", "pravin_zerobus", "Service Principal (name or app id)")

# COMMAND ----------
# MAGIC %md
# MAGIC ## Create catalog + schema

# COMMAND ----------
# MAGIC %sql
# MAGIC CREATE CATALOG IF NOT EXISTS ${catalog};
# MAGIC CREATE SCHEMA IF NOT EXISTS ${catalog}.${schema};

# COMMAND ----------
# MAGIC %md
# MAGIC ## Minimal grants (so the SP can use the catalog + schema)

# COMMAND ----------
# MAGIC %sql
# MAGIC GRANT USE CATALOG ON CATALOG ${catalog} TO `${sp}`;
# MAGIC GRANT USE SCHEMA  ON SCHEMA  ${catalog}.${schema} TO `${sp}`;

# COMMAND ----------
# MAGIC %md
# MAGIC ## Verify

# COMMAND ----------
# MAGIC %sql
# MAGIC SHOW SCHEMAS IN ${catalog};
# MAGIC SHOW GRANTS ON SCHEMA ${catalog}.${schema};


