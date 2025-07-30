#!/usr/bin/env python3
"""
Script to check what tables are available in StarRocks database
"""

import json
from metabase_migrator import MetabaseMigrator, MetabaseConfig
from config import METABASE_CONFIG

def main():
    """Main function"""
    
    STARROCKS_DB_ID = 7
    
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
    
    # Fetch metadata for StarRocks database
    print(f"📊 Fetching metadata for StarRocks database {STARROCKS_DB_ID}...")
    
    try:
        response = migrator.session.get(
            f"{config.base_url}/api/database/{STARROCKS_DB_ID}/metadata",
            headers={"X-Metabase-Session": migrator.session_token}
        )
        
        if response.status_code == 200:
            metadata = response.json()
            print(f"✅ Successfully fetched metadata for StarRocks database")
            
            # List all tables
            print(f"\n📋 Available tables in StarRocks database:")
            for table in metadata.get('tables', []):
                schema = table.get('schema', 'unknown')
                name = table.get('name', 'unknown')
                table_id = table.get('id', 'unknown')
                print(f"  {schema}.{name} (ID: {table_id})")
                
                # Show first few columns for transactions-related tables
                if 'transaction' in name.lower():
                    print(f"    Columns:")
                    for field in table.get('fields', [])[:5]:
                        field_name = field.get('name', 'unknown')
                        field_id = field.get('id', 'unknown')
                        print(f"      {field_name} (ID: {field_id})")
                    if len(table.get('fields', [])) > 5:
                        print(f"      ... and {len(table.get('fields', [])) - 5} more columns")
                    print()
            
        else:
            print(f"❌ Failed to fetch metadata: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error fetching metadata: {str(e)}")

if __name__ == "__main__":
    main() 