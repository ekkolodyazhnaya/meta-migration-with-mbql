#!/usr/bin/env python3
"""
Script to fetch metadata from Exasol and StarRocks databases and create mapping dictionaries
"""

import json
import requests
from metabase_migrator import MetabaseMigrator, MetabaseConfig
from config import METABASE_CONFIG

def load_migration_exceptions():
    """Load migration exceptions from config file"""
    try:
        with open('migration_exceptions.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("⚠️  migration_exceptions.json not found, using empty exceptions")
        return {"table_id_exceptions": {}, "table_name_exceptions": {}}
    except Exception as e:
        print(f"❌ Error loading migration_exceptions.json: {str(e)}")
        return {"table_id_exceptions": {}, "table_name_exceptions": {}}

def fetch_database_metadata(database_id: int, migrator: MetabaseMigrator):
    """Fetch metadata for a specific database"""
    print(f"📊 Fetching metadata for database {database_id}...")
    
    try:
        response = migrator.session.get(
            f"{migrator.config.base_url}/api/database/{database_id}/metadata",
            headers={"X-Metabase-Session": migrator.session_token}
        )
        
        if response.status_code == 200:
            metadata = response.json()
            print(f"✅ Successfully fetched metadata for database {database_id}")
            return metadata
        else:
            print(f"❌ Failed to fetch metadata for database {database_id}: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error fetching metadata for database {database_id}: {str(e)}")
        return None

def find_table_with_prefix(metadata, exasol_table_name, exasol_schema=None):
    """Find a table in StarRocks with a prefix matching the Exasol schema (if any)"""
    candidates = []
    for table in metadata.get('tables', []):
        name = table.get('name', '')
        if '__' in name:
            prefix, base_name = name.split('__', 1)
            if base_name.upper() == exasol_table_name.upper():
                if exasol_schema is None or prefix.upper() == exasol_schema.upper():
                    candidates.append(table)
        elif name.upper() == exasol_table_name.upper():
            candidates.append(table)
    return candidates[0] if candidates else None

def create_column_mapping_for_all_tables(exasol_metadata, starrocks_metadata, table_mapping, exceptions):
    """Create column mapping for all tables that have a successful table mapping"""
    print("\n🔍 Creating column mapping for all mapped tables...")
    column_mapping = {}
    
    for exasol_table_full, starrocks_table_name in table_mapping.items():
        print(f"\n📋 Processing table mapping: {exasol_table_full} -> {starrocks_table_name}")
        
        # Parse Exasol table name
        if '.' in exasol_table_full:
            exasol_schema, exasol_name = exasol_table_full.split('.', 1)
        else:
            exasol_schema = None
            exasol_name = exasol_table_full
        
        # Find Exasol table
        exasol_table = None
        for table in exasol_metadata.get('tables', []):
            if (table.get('name', '').lower() == exasol_name.lower() and 
                table.get('schema', '').lower() == exasol_schema.lower()):
                exasol_table = table
                break
        
        # Find StarRocks table
        starrocks_table = None
        for table in starrocks_metadata.get('tables', []):
            if table.get('name', '') == starrocks_table_name:
                starrocks_table = table
                break
        
        if not exasol_table:
            print(f"  ❌ Could not find Exasol table: {exasol_table_full}")
            continue
        if not starrocks_table:
            print(f"  ❌ Could not find StarRocks table: {starrocks_table_name}")
            continue
        
        print(f"  ✅ Found both tables, mapping columns...")
        
        # Map columns by name
        exasol_columns = {col.get('name', '').lower(): col for col in exasol_table.get('fields', [])}
        starrocks_columns = {col.get('name', '').lower(): col for col in starrocks_table.get('fields', [])}
        
        mapped_count = 0
        for col_name, exasol_col in exasol_columns.items():
            if col_name in starrocks_columns:
                starrocks_col = starrocks_columns[col_name]
                column_mapping[str(exasol_col.get('id'))] = starrocks_col.get('id')
                mapped_count += 1
        
        print(f"  🔄 Mapped {mapped_count} columns for {exasol_table_full}")
    
    # Add hardcoded exceptions from config
    for exasol_id, starrocks_id in exceptions.get('table_id_exceptions', {}).items():
        column_mapping[str(exasol_id)] = starrocks_id
        print(f"  🔄 Added exception mapping: Exasol ID {exasol_id} -> StarRocks ID {starrocks_id}")
    
    return column_mapping

def create_table_mapping(exasol_metadata, starrocks_metadata, exceptions):
    """Create mapping between Exasol and StarRocks table names"""
    print("\n🔍 Creating table mapping...")
    table_mapping = {}
    
    # For each Exasol table, find the corresponding StarRocks table
    for exasol_table in exasol_metadata.get('tables', []):
        exasol_schema = exasol_table.get('schema', '').upper()
        exasol_name = exasol_table.get('name', '').upper()
        exasol_full = f"{exasol_schema.lower()}.{exasol_name.lower()}"
        
        # Check if there's a hardcoded exception for this table
        if exasol_full in exceptions.get('table_name_exceptions', {}):
            starrocks_table_name = exceptions['table_name_exceptions'][exasol_full]
            table_mapping[exasol_full] = starrocks_table_name
            print(f"  🔄 Exception: {exasol_full} -> {starrocks_table_name}")
            continue
        
        # Find matching StarRocks table (by prefix logic)
        starrocks_table = find_table_with_prefix(starrocks_metadata, exasol_name, exasol_schema)
        if starrocks_table:
            table_mapping[exasol_full] = starrocks_table.get('name')
            print(f"  {exasol_full} -> {starrocks_table.get('name')}")
        else:
            print(f"  ⚠️  No match for {exasol_full}")
    
    return table_mapping

def main():
    """Main function"""
    
    # Database IDs
    EXASOL_DB_ID = 2
    STARROCKS_DB_ID = 16
    
    # Load migration exceptions
    exceptions = load_migration_exceptions()
    print(f"📋 Loaded {len(exceptions.get('table_id_exceptions', {}))} table ID exceptions")
    print(f"📋 Loaded {len(exceptions.get('table_name_exceptions', {}))} table name exceptions")
    
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
    
    # Fetch metadata for databases
    exasol_metadata = fetch_database_metadata(EXASOL_DB_ID, migrator)
    starrocks_metadata = fetch_database_metadata(STARROCKS_DB_ID, migrator)
    
    if not exasol_metadata or not starrocks_metadata:
        print("❌ Failed to fetch metadata for one or more databases")
        return
    
    # Create table mapping first
    table_mapping = create_table_mapping(exasol_metadata, starrocks_metadata, exceptions)
    
    # Create column mapping for all mapped tables
    column_mapping = create_column_mapping_for_all_tables(exasol_metadata, starrocks_metadata, table_mapping, exceptions)
    
    # Create the complete mapping dictionary
    migration_mapping = {
        "database_mapping": {
            "exasol": EXASOL_DB_ID,
            "starrocks": STARROCKS_DB_ID
        },
        "column_mapping": column_mapping,
        "table_mapping": table_mapping
    }
    
    # Save mapping to file
    with open('migrations/migration_mapping.json', 'w') as f:
        json.dump(migration_mapping, f, indent=2)
    
    print(f"\n💾 Migration mapping saved to migrations/migration_mapping.json")
    print(f"📊 Database mapping: Exasol ({EXASOL_DB_ID}) -> StarRocks ({STARROCKS_DB_ID})")
    print(f"🔗 Table mappings: {len(table_mapping)} tables mapped")
    print(f"🔗 Column mappings: {len(column_mapping)} columns mapped")
    
    # Print some examples
    print("\n📝 Example table mappings:")
    for i, (exasol_table, starrocks_table) in enumerate(list(table_mapping.items())[:5]):
        print(f"  {exasol_table} -> {starrocks_table}")
        if i >= 4:
            break
    
    print("\n📝 Example column mappings:")
    for i, (exasol_id, starrocks_id) in enumerate(list(column_mapping.items())[:5]):
        print(f"  Exasol ID {exasol_id} -> StarRocks ID {starrocks_id}")
        if i >= 4:
            break

if __name__ == "__main__":
    main() 