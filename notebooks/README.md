# Databricks Notebooks

**Purpose**: Databricks-side setup, monitoring, and data quality validation

---

## 📓 Available Notebooks

### 1. Setup Databricks Table
**File**: `01_Setup_Databricks_Table.py`  
**Purpose**: Complete Databricks setup for Ignition integration

**What it does:**
- Creates Unity Catalog and schema
- Creates Delta table with proper schema
- Enables Zerobus on the table
- Grants permissions to Service Principal
- Verifies setup

**When to run:** Once during initial setup, or when creating new tables

**Required input:**
- Service Principal UUID
- Catalog/schema/table names

---

### 2. Monitor Data Flow
**File**: `02_Monitor_Data_Flow.py`  
**Purpose**: Real-time monitoring of tag events

**What it does:**
- Shows recent events
- Displays data flow rate
- Tag statistics
- Quality distribution
- Latency analysis
- Time series visualization

**When to run:** Continuously for monitoring, or when troubleshooting

**Use cases:**
- Verify data is flowing
- Check throughput
- Monitor data quality
- Identify gaps or issues

---

### 3. Data Quality Check
**File**: `03_Data_Quality_Check.py`  
**Purpose**: Automated data quality validation

**What it does:**
- Validates schema compliance
- Checks for nulls in required fields
- Validates data types
- Checks for duplicates
- Validates timestamp consistency
- Calculates overall quality score

**When to run:** Daily or weekly for quality monitoring

**Output:** Data quality score (0-100%)

---

## 🚀 Quick Start

### Import to Databricks

**Option 1: Via Repos (Recommended)**
```
1. Databricks → Repos → Add Repo
2. Clone: https://github.com/pravinva/lakeflow-ignition-zerobus-connector
3. Navigate to notebooks/
4. Run notebooks in order
```

**Option 2: Manual Upload**
```
1. Databricks → Workspace
2. Create folder: /Users/your-email/ignition-zerobus/
3. Upload .py files
4. Run notebooks in order
```

---

## 📋 Usage Workflow

### Initial Setup
```
1. Run: 01_Setup_Databricks_Table.py
   → Creates table and grants permissions
   
2. Configure Ignition module with output details
   
3. Enable Event Stream in Ignition
   
4. Run: 02_Monitor_Data_Flow.py
   → Verify data is arriving
```

### Ongoing Operations
```
Daily:
- Run: 03_Data_Quality_Check.py
  → Monitor data quality trends

As Needed:
- Run: 02_Monitor_Data_Flow.py
  → Check specific tags or troubleshoot issues
```

---

## 🔧 What's NOT in Notebooks

### Module Development
**Location**: `module/src/main/java/`  
**Tool**: IDE (IntelliJ, VS Code)  
**Why not notebook**: Needs proper Java IDE, Gradle, debugging tools

### Ignition-Side Automation
**Location**: `scripts/`  
**Tool**: Command line / shell  
**Why not notebook**: Runs on Ignition Gateway, not Databricks

### Configuration Files
**Location**: `configs/`, `examples/`  
**Tool**: Text editor / Git  
**Why not notebook**: Better version control as files

---

## 🎯 Best Practices

### Scheduling
Set up Databricks Jobs to run notebooks automatically:

```python
# Example Job Schedule
- Setup: Run once (manual)
- Monitoring: Every 15 minutes (dashboard)
- Quality Check: Daily at midnight
```

### Alerting
Add alerts in notebooks:

```python
# Example: Alert on low quality score
if overall_score < 85:
    dbutils.notebook.exit(json.dumps({
        "status": "FAILED",
        "message": f"Quality score {overall_score}% below threshold"
    }))
```

### Parameterization
Make notebooks flexible with widgets:

```python
# Add at top of notebook
dbutils.widgets.text("catalog", "ignition_demo", "Catalog Name")
dbutils.widgets.text("schema", "scada_data", "Schema Name")
dbutils.widgets.text("table", "tag_events", "Table Name")

# Use in queries
CATALOG_NAME = dbutils.widgets.get("catalog")
```

---

## 📊 Dashboard Integration

### Create Databricks Dashboard
```
1. Run: 02_Monitor_Data_Flow.py
2. Click "New Dashboard"
3. Add visualizations:
   - Line chart: Tag values over time
   - Bar chart: Events per tag
   - Table: Recent events
   - Counter: Total events, quality %
4. Set refresh: Every 5 minutes
```

---

## 🔗 Related Documentation

- **Module Development**: See `module/README.md`
- **Automation Scripts**: See `scripts/README.md`
- **User Guide**: See `USER_GUIDE.md`
- **Quick Start**: See `QUICK_START.md`

---

## 💡 Tips

1. **Use Git integration** for notebook version control
2. **Create job clusters** for scheduled runs (cheaper than all-purpose)
3. **Add comments** in SQL cells for future reference
4. **Save results** to tables for historical tracking
5. **Use Databricks Alerts** for automated notifications

---

**Last Updated**: December 2025  
**Compatibility**: Databricks Runtime 13.0+

