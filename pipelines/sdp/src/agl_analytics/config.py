"""Pipeline catalog/schema configuration.

Hardcoded to match pipeline settings: catalog=agl_demo, schema=ot.
"""

# Pipeline target catalog and schema (from pipeline settings)
CATALOG = "agl_demo"
SCHEMA = "ot"


def get_catalog():
    """Current Unity Catalog catalog (pipeline target)."""
    return CATALOG


def get_schema():
    """Current schema (pipeline target, e.g. ot)."""
    return SCHEMA


def table(name: str) -> str:
    """Fully qualified table name in pipeline catalog.schema."""
    return f"{CATALOG}.{SCHEMA}.{name}"


def site_table(site_schema: str, name: str) -> str:
    """Fully qualified table in a schema (same catalog, e.g. ot)."""
    return f"{CATALOG}.{site_schema}.{name}"
