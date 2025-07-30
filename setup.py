#!/usr/bin/env python3
"""
Setup script for Metabase Migration Tool
"""

import os
import sys

def create_config_template():
    """Create a config template if it doesn't exist"""
    config_content = '''"""
Configuration file for Metabase migration from Exasol to StarRocks
"""

from dataclasses import dataclass
from typing import List, Dict

@dataclass
class DatabaseMapping:
    """Mapping from Exasol to StarRocks database/schema/table"""
    exasol_db: str
    exasol_schema: str
    exasol_table: str
    starrocks_db: str
    starrocks_table: str

# Metabase connection configuration
METABASE_CONFIG = {
    "base_url": "https://your-metabase-instance.com",
    "username": "your-username",
    "password": "your-password"
}

# Database mappings from Exasol to StarRocks
DATABASE_MAPPINGS = [
    DatabaseMapping(
        exasol_db="exasol",
        exasol_schema="mart",
        exasol_table="transactions",
        starrocks_db="sr_mart",
        starrocks_table="transactions"
    ),
]

# SQL function mappings from Exasol to StarRocks
FUNCTION_MAPPINGS = {
    "ADD_DAYS": "DATE_ADD",
    "ADD_MONTHS": "DATE_ADD",
    "ADD_YEARS": "DATE_ADD",
    "DAYS_BETWEEN": "DATEDIFF",
    "MONTHS_BETWEEN": "MONTHS_BETWEEN",
    "INSTR": "LOCATE",
    "SUBSTR": "SUBSTRING",
    "MEDIAN": "PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY",
    "CURRENT_TIMESTAMP": "NOW()",
    "CURRENT_DATE": "CURDATE()",
}

# Migration settings
MIGRATION_SETTINGS = {
    "preserve_variables": True,
    "backup_original_sql": True,
    "output_format": "json",
    "include_metadata": True,
}
'''
    
    if not os.path.exists('config.py'):
        with open('config.py', 'w') as f:
            f.write(config_content)
        print("✅ Created config.py template")
        print("📝 Please edit config.py with your Metabase credentials")
    else:
        print("ℹ️  config.py already exists")

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import requests
        print("✅ requests library is installed")
    except ImportError:
        print("❌ requests library is missing")
        print("📦 Installing dependencies...")
        os.system("pip install requests")
        print("✅ Dependencies installed")

def create_example_script():
    """Create an example migration script"""
    example_content = '''#!/usr/bin/env python3
"""
Example: How to migrate a dashboard
"""

# Step 1: Edit the dashboard ID in migrate_dashboard.py
# Change line ~15 from:
# dashboard_id = 503
# to your target dashboard ID

# Step 2: Run the migration
# python3 migrate_dashboard.py

# Step 3: Check results in migrations/validation_results_dashboard_XXX.txt

print("🚀 Ready to migrate your dashboard!")
print("📝 Edit migrate_dashboard.py to set your dashboard ID")
print("🔧 Run: python3 migrate_dashboard.py")
'''
    
    with open('example_migration.py', 'w') as f:
        f.write(example_content)
    print("✅ Created example_migration.py")

def main():
    """Main setup function"""
    print("🔧 Setting up Metabase Migration Tool...")
    print("=" * 50)
    
    # Check dependencies
    check_dependencies()
    
    # Create config template
    create_config_template()
    
    # Create example script
    create_example_script()
    
    print("\n🎉 Setup complete!")
    print("\n📋 Next steps:")
    print("1. Edit config.py with your Metabase credentials")
    print("2. Edit migrate_dashboard.py to set your dashboard ID")
    print("3. Run: python3 migrate_dashboard.py")
    print("\n📚 See README.md for detailed instructions")

if __name__ == "__main__":
    main() 