# Metabase Dashboard Migration: Exasol to StarRocks

A comprehensive tool for migrating Metabase dashboards from Exasol to StarRocks database, with support for both native SQL and MBQL questions.

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.7+
- Access to Metabase instance
- Exasol and StarRocks database credentials

### 2. Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Configure your Metabase connection
# Edit config.py with your credentials
```

### 3. Migrate a Dashboard
```bash
# Edit the dashboard ID in migrate_dashboard.py (line ~15)
# Then run:
python3 migrate_dashboard.py
```

## 📁 Directory Structure

```
meta-migration/
├── README.md                           # This file
├── config.py                           # Metabase connection configuration
├── migrate_dashboard.py               # Main migration script
├── metabase_migrator.py               # Core migration library
├── column_mapping_config.json         # Column mappings and formatting rules
├── requirements.txt                   # Python dependencies
├── scripts/                           # Utility scripts
│   ├── add_filters_to_dashboard_503_v2.py
│   ├── create_metric_mappings.py
│   ├── fetch_metadata.py
│   └── ... (other utility scripts)
├── tools/                             # Core tools
│   ├── sql_converter.py
│   ├── test_converter.py
│   └── run_migration.py
├── examples/                          # Example outputs and configurations
│   ├── dashboard_503_migration_summary.md
│   ├── dashboard_503_filter_update_v2.json
│   └── ... (other examples)
├── results/                           # Migration results and logs
│   ├── migration_test_*.log
│   └── migration_summary.md
├── migrations/                        # Migration mapping files
│   ├── migration_mapping.json        # Field ID mappings
│   └── validation_results_*.txt      # Validation results
└── inspections/                       # Dashboard inspection data
    └── dashboard_*.json              # Cached dashboard metadata
```

## 🎯 Key Features

### ✅ **Complete Migration Support**
- **Native SQL questions**: Full SQL syntax conversion
- **MBQL questions**: Field ID and table mapping
- **Visualization settings**: Preserved formatting and display names
- **Template tags**: Updated with new field mappings

### 🔧 **SQL Compatibility**
- Exasol → StarRocks function mappings
- Schema reference updates (`mart.table` → `MART__TABLE`)
- Date/time function conversions
- Aggregation function mappings

### 🎨 **Formatting Preservation**
- Percentage formatting for acceptance rates
- Currency formatting for amounts
- Conditional formatting rules
- Column display names

### 🔍 **Filter Management**
- Add new filters to visualizations
- Template tag management
- Hardcoded value replacement

## 📋 Configuration

### `config.py`
```python
METABASE_CONFIG = {
    "base_url": "https://your-metabase-instance.com",
    "username": "your-username", 
    "password": "your-password"
}
```

### `column_mapping_config.json`
```json
{
  "column_mappings": {
    "exasol_to_starrocks": {
      "AR_PERIOD1": "ar_period1",
      "DELTA_AR": "delta_ar"
    }
  },
  "formatting_preservation": {
    "percentage_columns": ["AR_PERIOD1", "AR_PERIOD2"],
    "currency_columns": ["TURNOVER_EUR_PERIOD1"]
  }
}
```

## 🔄 Migration Process

1. **Dashboard Inspection**: Fetches metadata and caches it
2. **Question Processing**: Converts SQL/MBQL for StarRocks compatibility
3. **Field Mapping**: Updates field IDs from Exasol to StarRocks
4. **Validation**: Tests migrated questions
5. **Filter Addition**: Adds new filters if requested

## 🛠️ Usage Examples

### Basic Migration
```bash
# Edit dashboard ID in migrate_dashboard.py
dashboard_id = 503  # Change this to your target dashboard

# Run migration
python3 migrate_dashboard.py
```

### Add Filters to Dashboard
```bash
# Use the filter addition script
python3 scripts/add_filters_to_dashboard_503_v2.py
```

### Create Metric Mappings
```bash
# Generate metric mappings
python3 scripts/create_metric_mappings.py
```

## 📊 Recent Migration Example

### Dashboard 503 "USA Data Project"
- **Success Rate**: 95.8% (23/24 questions)
- **New Filters Added**: Card_Geo, CARD_ISOCOUNTRY
- **Migration Time**: 75.66 seconds
- **Database**: Exasol (DB 2) → StarRocks (DB 16)

See `examples/dashboard_503_migration_summary.md` for detailed results.

## 🔧 Troubleshooting

### Common Issues
1. **Authentication failed**: Check credentials in `config.py`
2. **Field mapping errors**: Run `python3 scripts/fetch_metadata.py`
3. **SQL compatibility issues**: Check `tools/sql_converter.py`

### Debug Mode
Enable detailed logging by modifying scripts to print more information.

## 📝 Best Practices

1. **Always validate migrations** - Check validation results
2. **Test with small dashboards first** - Start with few questions
3. **Backup before migration** - Export configurations if needed
4. **Update mappings regularly** - Re-run metadata fetch when schemas change

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This migration tool is provided as-is for internal use. Ensure you have proper permissions to modify Metabase dashboards and database connections.

---

**Ready to migrate your dashboard?** Start by editing the dashboard ID in `migrate_dashboard.py` and running the migration! 