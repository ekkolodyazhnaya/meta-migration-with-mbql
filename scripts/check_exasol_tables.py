#!/usr/bin/env python3
"""
Script to check what tables are available in Exasol database
"""

import json
from metabase_migrator import MetabaseMigrator, MetabaseConfig
from config import METABASE_CONFIG

def main():
    """Main function"""
    
    EXASOL_DB_ID = 2
    
    # Create configuration
    config = MetabaseConfig(
        base_url=METABASE_CONFIG["base_url"],
        username=METABASE_CONFIG["username"],
        password=METABASE_CONFIG["password"]
    )
    
    # Create migrator for authentication
    migrator = MetabaseMigrator(config)
    
    # Authenticate
    if not migrator.authenticate():
        print("❌ Authentication failed")
        return
    
    print("✅ Authentication successful")
    
    # Fetch metadata for Exasol database
    response = migrator.session.get(
        f"{migrator.config.base_url}/api/database/{EXASOL_DB_ID}/metadata",
        headers={"X-Metabase-Session": migrator.session_token}
    )
    
    if response.status_code == 200:
        metadata = response.json()
        tables = metadata.get('tables', [])
        
        print(f"📊 Found {len(tables)} tables in Exasol database")
        
        # Search for tables containing GROUP_SUM or TURNOVER
        group_sum_tables = []
        for table in tables:
            table_name = table.get('name', '').upper()
            if 'GROUP_SUM' in table_name or 'TURNOVER' in table_name:
                group_sum_tables.append(table)
        
        print(f"\n🔍 Found {len(group_sum_tables)} tables with GROUP_SUM or TURNOVER:")
        for table in group_sum_tables:
            print(f"  - {table.get('schema')}.{table.get('name')} (ID: {table.get('id')})")
            
            # Show fields for these tables
            fields = table.get('fields', [])
            print(f"    Fields ({len(fields)}):")
            for field in fields[:10]:  # Show first 10 fields
                print(f"      - {field.get('name')} (ID: {field.get('id')})")
            if len(fields) > 10:
                print(f"      ... and {len(fields) - 10} more fields")
            print()
    else:
        print(f"❌ Failed to fetch metadata: {response.status_code}")

if __name__ == "__main__":
    main() 