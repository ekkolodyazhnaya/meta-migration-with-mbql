#!/usr/bin/env python3
"""
Script to update a specific Metabase question with converted StarRocks SQL
"""

import json
import requests
import re
from metabase_migrator import MetabaseMigrator, MetabaseConfig
from config import METABASE_CONFIG

def load_migration_mapping():
    """Load the migration mapping from file"""
    try:
        with open('migration_mapping.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Migration mapping file not found. Please run fetch_metadata.py first.")
        return None

def update_template_tags(template_tags, column_mapping):
    """Update template tags with new column IDs"""
    updated_tags = {}
    
    print(f"🔍 Available mappings: {len(column_mapping)} fields")
    print(f"🔍 Sample mappings: {list(column_mapping.items())[:5]}")
    
    for tag_name, tag_config in template_tags.items():
        updated_tag = tag_config.copy()
        
        # Update field-id if it exists and has a mapping
        if 'field-id' in tag_config:
            exasol_field_id = tag_config['field-id']
            # Convert to string for lookup since mapping uses string keys
            exasol_field_id_str = str(exasol_field_id)
            if exasol_field_id_str in column_mapping:
                updated_tag['field-id'] = column_mapping[exasol_field_id_str]
                print(f"🔄 Updated template tag '{tag_name}': field-id {exasol_field_id} -> {column_mapping[exasol_field_id_str]}")
            else:
                print(f"⚠️  No mapping found for field-id {exasol_field_id} in '{tag_name}'")
        
        # Update dimension field IDs if they exist and have mappings
        if 'dimension' in tag_config and isinstance(tag_config['dimension'], list):
            dimension = tag_config['dimension'].copy()
            if len(dimension) >= 2 and dimension[0] == 'field' and isinstance(dimension[1], int):
                exasol_field_id = dimension[1]
                exasol_field_id_str = str(exasol_field_id)
                if exasol_field_id_str in column_mapping:
                    dimension[1] = column_mapping[exasol_field_id_str]
                    updated_tag['dimension'] = dimension
                    print(f"🔄 Updated template tag '{tag_name}': dimension field {exasol_field_id} -> {column_mapping[exasol_field_id_str]}")
                else:
                    print(f"⚠️  No mapping found for dimension field {exasol_field_id} in '{tag_name}'")
        
        updated_tags[tag_name] = updated_tag
    
    return updated_tags

def update_question_sql(question_id: int, new_sql: str):
    """Update a specific question's SQL in Metabase"""
    
    print(f"🔄 Updating Question {question_id}")
    print("=" * 50)
    
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
    
    # Load migration mapping
    migration_mapping = load_migration_mapping()
    if not migration_mapping:
        return
    
    # Fetch current question
    print(f"\n📊 Fetching current question {question_id}...")
    response = migrator.session.get(
        f"{migrator.config.base_url}/api/card/{question_id}",
        headers={"X-Metabase-Session": migrator.session_token}
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to fetch question: {response.status_code}")
        return
    
    question = response.json()
    print(f"✅ Found question: {question.get('name', 'Unknown')}")
    
    # Get current SQL and database
    dataset_query = question.get('dataset_query', {})
    native_query = dataset_query.get('native', {})
    current_sql = native_query.get('query', '')
    current_database_id = dataset_query.get('database')
    
    print(f"📄 Current SQL (first 100 chars): {current_sql[:100]}...")
    print(f"🗄️  Current database ID: {current_database_id}")
    
    # Get template tags
    template_tags = native_query.get('template-tags', {})
    print(f"🏷️  Current template tags: {list(template_tags.keys())}")
    
    # Update template tags with new column IDs
    column_mapping = migration_mapping['column_mapping']
    updated_template_tags = update_template_tags(template_tags, column_mapping)
    
    # Use target database (all fields are now in database 7)
    target_database_id = migration_mapping['database_mapping']['starrocks']  # Database 7
    print(f"🗄️  Database: {current_database_id} -> {target_database_id}")
    
    # Update the question
    print(f"\n🔄 Updating question in Metabase...")
    
    update_data = {
        "dataset_query": {
            "type": "native",
            "native": {
                "query": new_sql,
                "template-tags": updated_template_tags
            },
            "database": target_database_id
        }
    }
    
    response = migrator.session.put(
        f"{migrator.config.base_url}/api/card/{question_id}",
        headers={
            "X-Metabase-Session": migrator.session_token,
            "Content-Type": "application/json"
        },
        json=update_data
    )
    
    if response.status_code == 200:
        print("✅ Question updated successfully!")
        
        # Verify the update
        verify_response = migrator.session.get(
            f"{migrator.config.base_url}/api/card/{question_id}",
            headers={"X-Metabase-Session": migrator.session_token}
        )
        
        if verify_response.status_code == 200:
            updated_question = verify_response.json()
            updated_dataset_query = updated_question.get('dataset_query', {})
            updated_database_id = updated_dataset_query.get('database')
            print(f"✅ Verification: Question now uses database {updated_database_id}")
        else:
            print("⚠️  Could not verify update")
    else:
        print(f"❌ Update failed: {response.status_code} - {response.text}")

def main():
    """Main function"""
    question_id = 3727
    
    # Get the converted SQL from the migration results
    try:
        with open('dashboard_385_migration.json', 'r') as f:
            migration_data = json.load(f)
        
        # Find question 3727
        question_3727 = None
        for dashboard in migration_data:
            for question in dashboard.get('questions', []):
                if question.get('question_id') == question_id:
                    question_3727 = question
                    break
            if question_3727:
                break
        
        if not question_3727:
            print(f"❌ Question {question_id} not found in migration results")
            return
        
        converted_sql = question_3727.get('converted_sql')
        if not converted_sql:
            print(f"❌ No converted SQL found for question {question_id}")
            return
        
        # Remove schema prefixes from the SQL
        cleaned_sql = converted_sql.replace('sr_mart.transactions', 'TRANSACTIONS')
        cleaned_sql = cleaned_sql.replace('mart.CALCULATIONS_UNIQ', 'CALCULATIONS_UNIQ')
        cleaned_sql = cleaned_sql.replace('ANALYST.GROUP_SUM_TURNOVER_EUR', 'GROUP_SUM_TURNOVER_EUR')
        
        # Fix StarRocks window function syntax
        cleaned_sql = re.sub(r'PARTITION BY 1', '', cleaned_sql, flags=re.IGNORECASE)
        cleaned_sql = re.sub(r'OVER \(\)', 'OVER ()', cleaned_sql, flags=re.IGNORECASE)
        
        # Fix column aliases to uppercase to match visualization settings
        # Fix subquery aliases
        cleaned_sql = re.sub(r'as dt', 'as DT', cleaned_sql, flags=re.IGNORECASE)
        cleaned_sql = re.sub(r'as count_transactions', 'as COUNT_TRANSACTIONS', cleaned_sql, flags=re.IGNORECASE)
        cleaned_sql = re.sub(r'as Turnover_EUR', 'as TURNOVER_EUR', cleaned_sql, flags=re.IGNORECASE)
        cleaned_sql = re.sub(r'as avg_Turnover_EUR', 'as AVG_TURNOVER_EUR', cleaned_sql, flags=re.IGNORECASE)
        cleaned_sql = re.sub(r'as median_Turnover_EUR', 'as MEDIAN_TURNOVER_EUR', cleaned_sql, flags=re.IGNORECASE)
        cleaned_sql = re.sub(r'as min_Turnover_EUR', 'as MIN_TURNOVER_EUR', cleaned_sql, flags=re.IGNORECASE)
        cleaned_sql = re.sub(r'as max_Turnover_EUR', 'as MAX_TURNOVER_EUR', cleaned_sql, flags=re.IGNORECASE)
        cleaned_sql = re.sub(r'as AR', 'as AR', cleaned_sql, flags=re.IGNORECASE)
        cleaned_sql = re.sub(r'as total_turnover_eur', 'as TOTAL_TURNOVER_EUR', cleaned_sql, flags=re.IGNORECASE)
        
        # Fix main query column references to uppercase
        cleaned_sql = re.sub(r'tr\.dt', 'tr.DT', cleaned_sql, flags=re.IGNORECASE)
        cleaned_sql = re.sub(r'tr\.count_transactions', 'tr.COUNT_TRANSACTIONS', cleaned_sql, flags=re.IGNORECASE)
        cleaned_sql = re.sub(r'tr\.Turnover_EUR', 'tr.TURNOVER_EUR', cleaned_sql, flags=re.IGNORECASE)
        cleaned_sql = re.sub(r'tr\.avg_Turnover_EUR', 'tr.AVG_TURNOVER_EUR', cleaned_sql, flags=re.IGNORECASE)
        cleaned_sql = re.sub(r'tr\.median_Turnover_EUR', 'tr.MEDIAN_TURNOVER_EUR', cleaned_sql, flags=re.IGNORECASE)
        cleaned_sql = re.sub(r'tr\.min_Turnover_EUR', 'tr.MIN_TURNOVER_EUR', cleaned_sql, flags=re.IGNORECASE)
        cleaned_sql = re.sub(r'tr\.max_Turnover_EUR', 'tr.MAX_TURNOVER_EUR', cleaned_sql, flags=re.IGNORECASE)
        cleaned_sql = re.sub(r'tr\.AR', 'tr.AR', cleaned_sql, flags=re.IGNORECASE)
        cleaned_sql = re.sub(r'tr\.total_turnover_eur', 'tr.TOTAL_TURNOVER_EUR', cleaned_sql, flags=re.IGNORECASE)
        
        print(f"📝 Question: {question_3727.get('question_name')}")
        print(f"🔧 Type: {question_3727.get('type')}")
        print(f"🔄 SQL cleaned: sr_mart.transactions -> TRANSACTIONS, mart.CALCULATIONS_UNIQ -> CALCULATIONS_UNIQ, ANALYST.GROUP_SUM_TURNOVER_EUR -> GROUP_SUM_TURNOVER_EUR")
        print(f"🔄 Fixed StarRocks syntax: PARTITION BY 1 -> OVER ()")
        print(f"🔄 Fixed column aliases: lowercase -> UPPERCASE to match visualization settings")
        
        # Update the question
        update_question_sql(question_id, cleaned_sql)
        
    except FileNotFoundError:
        print("❌ Migration results file not found. Please run migration first.")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main() 