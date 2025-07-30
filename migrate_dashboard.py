#!/usr/bin/env python3
"""
Script to migrate all questions in a dashboard from Exasol to StarRocks
"""

import json
import requests
import re
import time
from datetime import datetime
from metabase_migrator import MetabaseMigrator, MetabaseConfig
from config import METABASE_CONFIG
import config
print(f"[DEBUG] config.py loaded from: {config.__file__}")

# Configuration for specific dashboards
DASHBOARD_CONFIG = {
    405: {
        "granularity_to_static_list": True,
        "granularity_static_values": [
            ["hour"],
            ["day"], 
            ["week"],
            ["month"],
            ["quarter"],
            ["year"]
        ],
        "granularity_default": "week"
    },
    406: {
        "granularity_to_static_list": True,
        "granularity_static_values": [
            ["hour"],
            ["day"], 
            ["week"],
            ["month"],
            ["quarter"],
            ["year"]
        ],
        "granularity_default": "week"
    },
    407: {
        "granularity_to_static_list": True,
        "granularity_static_values": [
            ["hour"],
            ["day"], 
            ["week"],
            ["month"],
            ["quarter"],
            ["year"]
        ],
        "granularity_default": "week"
    },
    408: {
        "granularity_to_static_list": True,
        "granularity_static_values": [
            ["hour"],
            ["day"], 
            ["week"],
            ["month"],
            ["quarter"],
            ["year"]
        ],
        "granularity_default": "week"
    },
    409: {
        "granularity_to_static_list": True,
        "granularity_static_values": [
            ["hour"],
            ["day"], 
            ["week"],
            ["month"],
            ["quarter"],
            ["year"]
        ],
        "granularity_default": "week"
    },
    410: {
        "granularity_to_static_list": True,
        "granularity_static_values": [
            ["hour"],
            ["day"], 
            ["week"],
            ["month"],
            ["quarter"],
            ["year"]
        ],
        "granularity_default": "week"
    },
    411: {
        "granularity_to_static_list": True,
        "granularity_static_values": [
            ["hour"],
            ["day"], 
            ["week"],
            ["month"],
            ["quarter"],
            ["year"]
        ],
        "granularity_default": "week"
    },
    158: {
        "granularity_to_static_list": True,
        "granularity_static_values": [
            ["hour"],
            ["day"], 
            ["week"],
            ["month"],
            ["quarter"],
            ["year"]
        ],
        "granularity_default": "week"
    },
    412: {
        "granularity_to_static_list": True,
        "granularity_static_values": [
            ["hour"],
            ["day"], 
            ["week"],
            ["month"],
            ["quarter"],
            ["year"]
        ],
        "granularity_default": "week"
    },
    413: {
        "granularity_to_static_list": True,
        "granularity_static_values": [
            ["hour"],
            ["day"], 
            ["week"],
            ["month"],
            ["quarter"],
            ["year"]
        ],
        "granularity_default": "week"
    },
    414: {
        "granularity_to_static_list": True,
        "granularity_static_values": [
            ["hour"],
            ["day"], 
            ["week"],
            ["month"],
            ["quarter"],
            ["year"]
        ],
        "granularity_default": "week"
    },
    415: {
        "granularity_to_static_list": True,
        "granularity_static_values": [
            ["hour"],
            ["day"], 
            ["week"],
            ["month"],
            ["quarter"],
            ["year"]
        ],
        "granularity_default": "week"
    },
    503: {
        "granularity_to_static_list": True,
        "granularity_static_values": [
            ["hour"],
            ["day"], 
            ["week"],
            ["month"],
            ["quarter"],
            ["year"]
        ],
        "granularity_default": "week"
    },
    416: {
        "granularity_to_static_list": True,
        "granularity_static_values": [
            ["hour"],
            ["day"], 
            ["week"],
            ["month"],
            ["quarter"],
            ["year"]
        ],
        "granularity_default": "week"
    },
    417: {
        "granularity_to_static_list": True,
        "granularity_static_values": [
            ["hour"],
            ["day"], 
            ["week"],
            ["month"],
            ["quarter"],
            ["year"]
        ],
        "granularity_default": "week"
    },
    418: {
        "granularity_to_static_list": True,
        "granularity_static_values": [
            ["hour"],
            ["day"], 
            ["week"],
            ["month"],
            ["quarter"],
            ["year"]
        ],
        "granularity_default": "week"
    },
    419: {
        "granularity_to_static_list": True,
        "granularity_static_values": [
            ["hour"],
            ["day"], 
            ["week"],
            ["month"],
            ["quarter"],
            ["year"]
        ],
        "granularity_default": "week"
    },
    420: {
        "granularity_to_static_list": True,
        "granularity_static_values": [
            ["hour"],
            ["day"], 
            ["week"],
            ["month"],
            ["quarter"],
            ["year"]
        ],
        "granularity_default": "week"
    },
    421: {
        "granularity_to_static_list": True,
        "granularity_static_values": [
            ["hour"],
            ["day"], 
            ["week"],
            ["month"],
            ["quarter"],
            ["year"]
        ],
        "granularity_default": "week"
    }
}

def load_migration_mapping():
    """Load the migration mapping from file"""
    try:
        with open('migrations/migration_mapping.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Migration mapping file not found. Please run fetch_metadata.py first.")
        return None

def fetch_dashboard_inspection(dashboard_id, migrator):
    """Fetch dashboard inspection data from Metabase"""
    print(f"🔍 Fetching dashboard inspection data for Dashboard {dashboard_id}")
    
    # Fetch dashboard details
    response = migrator.session.get(
        f"{migrator.config.base_url}/api/dashboard/{dashboard_id}",
        headers={"X-Metabase-Session": migrator.session_token}
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to fetch dashboard: {response.status_code}")
        return None
    
    dashboard_data = response.json()
    
    # Save to inspections folder
    filename = f'inspections/dashboard_{dashboard_id}_inspection.json'
    with open(filename, 'w') as f:
        json.dump(dashboard_data, f, indent=2)
    
    print(f"✅ Dashboard inspection data saved to {filename}")
    
    # Print summary
    dashcards = dashboard_data.get('dashcards', [])
    print(f"📊 Found {len(dashcards)} dashcards in dashboard")
    
    for i, dashcard in enumerate(dashcards):
        card = dashcard.get('card', {})
        question_id = card.get('id')
        question_name = card.get('name', 'Unknown')
        print(f"  📝 Dashcard {i}: Question {question_id} - {question_name}")
    
    return dashboard_data

def load_dashboard_inspection(dashboard_id, migrator):
    """Load the dashboard inspection data, fetch if not exists"""
    filename = f'inspections/dashboard_{dashboard_id}_inspection.json'
    
    try:
        with open(filename, 'r') as f:
            print(f"✅ Loaded existing dashboard inspection from {filename}")
            return json.load(f)
    except FileNotFoundError:
        print(f"📁 Dashboard inspection file not found at {filename}")
        print("🔄 Fetching dashboard inspection data from Metabase...")
        return fetch_dashboard_inspection(dashboard_id, migrator)

def get_visualization_settings(dashboard_data, question_id):
    """Get visualization settings for a specific question from dashboard data"""
    print(f"    🔍 Looking for visualization settings for question ID: {question_id}")
    
    # Find the question in dashboard data
    for i, dashcard in enumerate(dashboard_data.get('dashcards', [])):
        card = dashcard.get('card', {})
        card_id = card.get('id')
        
        # Check if this card has the question ID
        if card_id == question_id:
            print(f"    ✅ Found question {question_id} in dashcard {i}")
            viz_settings = dashcard.get('visualization_settings', {})
            print(f"    📊 Found visualization settings with {len(viz_settings)} keys")
            return viz_settings
    
    print(f"    ⚠️  No visualization settings found for question {question_id}")
    return {}

def map_column_names_in_visualization_settings(viz_settings, column_mapping):
    """Map column names in visualization settings from Exasol to StarRocks format"""
    if not viz_settings:
        return viz_settings
    
    mapped_settings = viz_settings.copy()
    
    # Map column names in column_settings
    column_settings = viz_settings.get('column_settings', {})
    if column_settings:
        mapped_column_settings = {}
        for key, value in column_settings.items():
            # Parse the key format: '["name","COLUMN_NAME"]'
            if key.startswith('["name","') and key.endswith('"]'):
                # Extract the column name
                column_name = key[8:-2]  # Remove '["name","' and '"]'
                
                # Try to find the mapped column name
                mapped_column_name = None
                for exasol_col, starrocks_col in column_mapping.items():
                    if exasol_col.lower() == column_name.lower():
                        mapped_column_name = starrocks_col
                        break
                
                if mapped_column_name:
                    new_key = f'["name","{mapped_column_name}"]'
                    mapped_column_settings[new_key] = value
                    print(f"    🔄 Mapped column setting: '{column_name}' -> '{mapped_column_name}'")
                else:
                    # Keep original if no mapping found
                    mapped_column_settings[key] = value
                    print(f"    ⚠️  No mapping found for column: '{column_name}'")
            else:
                # Keep non-column keys as is
                mapped_column_settings[key] = value
        
        mapped_settings['column_settings'] = mapped_column_settings
    
    # Map column names in graph.dimensions
    dimensions = viz_settings.get('graph.dimensions', [])
    if dimensions:
        mapped_dimensions = []
        for dim in dimensions:
            mapped_dim = None
            for exasol_col, starrocks_col in column_mapping.items():
                if exasol_col.lower() == dim.lower():
                    mapped_dim = starrocks_col
                    break
            
            if mapped_dim:
                mapped_dimensions.append(mapped_dim)
                print(f"    🔄 Mapped dimension: '{dim}' -> '{mapped_dim}'")
            else:
                mapped_dimensions.append(dim)
                print(f"    ⚠️  No mapping found for dimension: '{dim}'")
        
        mapped_settings['graph.dimensions'] = mapped_dimensions
    
    # Map column names in graph.metrics
    metrics = viz_settings.get('graph.metrics', [])
    if metrics:
        mapped_metrics = []
        for metric in metrics:
            mapped_metric = None
            for exasol_col, starrocks_col in column_mapping.items():
                if exasol_col.lower() == metric.lower():
                    mapped_metric = starrocks_col
                    break
            
            if mapped_metric:
                mapped_metrics.append(mapped_metric)
                print(f"    🔄 Mapped metric: '{metric}' -> '{mapped_metric}'")
            else:
                mapped_metrics.append(metric)
                print(f"    ⚠️  No mapping found for metric: '{metric}'")
        
        mapped_settings['graph.metrics'] = mapped_metrics
    
    # Map scalar.field if present
    scalar_field = viz_settings.get('scalar.field')
    if scalar_field:
        mapped_scalar_field = None
        for exasol_col, starrocks_col in column_mapping.items():
            if exasol_col.lower() == scalar_field.lower():
                mapped_scalar_field = starrocks_col
                break
        
        if mapped_scalar_field:
            mapped_settings['scalar.field'] = mapped_scalar_field
            print(f"    🔄 Mapped scalar field: '{scalar_field}' -> '{mapped_scalar_field}'")
        else:
            print(f"    ⚠️  No mapping found for scalar field: '{scalar_field}'")
    
    # Map table.cell_column if present
    cell_column = viz_settings.get('table.cell_column')
    if cell_column:
        mapped_cell_column = None
        for exasol_col, starrocks_col in column_mapping.items():
            if exasol_col.lower() == cell_column.lower():
                mapped_cell_column = starrocks_col
                break
        
        if mapped_cell_column:
            mapped_settings['table.cell_column'] = mapped_cell_column
            print(f"    🔄 Mapped cell column: '{cell_column}' -> '{mapped_cell_column}'")
        else:
            print(f"    ⚠️  No mapping found for cell column: '{cell_column}'")
    
    # Map table.pivot_column if present
    pivot_column = viz_settings.get('table.pivot_column')
    if pivot_column:
        mapped_pivot_column = None
        for exasol_col, starrocks_col in column_mapping.items():
            if exasol_col.lower() == pivot_column.lower():
                mapped_pivot_column = starrocks_col
                break
        
        if mapped_pivot_column:
            mapped_settings['table.pivot_column'] = mapped_pivot_column
            print(f"    🔄 Mapped pivot column: '{pivot_column}' -> '{mapped_pivot_column}'")
        else:
            print(f"    ⚠️  No mapping found for pivot column: '{pivot_column}'")
    
    return mapped_settings

def get_visualization_columns(dashboard_data, question_id):
    """Get column names from visualization settings for a specific question"""
    columns = set()
    
    print(f"    🔍 Looking for question ID: {question_id}")
    print(f"    📋 Total dashcards in dashboard: {len(dashboard_data.get('dashcards', []))}")
    
    # Find the question in dashboard data
    for i, dashcard in enumerate(dashboard_data.get('dashcards', [])):
        card = dashcard.get('card', {})
        card_id = card.get('id')
        print(f"    🔍 Dashcard {i}: Card ID = {card_id}")
        
        # Check if this card has the question ID
        if card_id == question_id:
            print(f"    ✅ Found question {question_id} in dashcard {i}")
            viz_settings = dashcard.get('visualization_settings', {})
            print(f"    📊 Visualization settings: {viz_settings}")
            
            # Get dimensions
            dimensions = viz_settings.get('graph.dimensions', [])
            columns.update(dimensions)
            print(f"    📏 Dimensions found: {dimensions}")
            
            # Get metrics
            metrics = viz_settings.get('graph.metrics', [])
            columns.update(metrics)
            print(f"    📈 Metrics found: {metrics}")
            
            # Get other potential column references
            for key, value in viz_settings.items():
                if isinstance(value, str) and value not in ['null', 'true', 'false']:
                    columns.add(value)
            
            break
    
    print(f"    🎯 Final columns: {list(columns)}")
    return columns

def get_current_visualization_columns(question_id, migrator):
    """Get current visualization columns directly from Metabase"""
    columns = set()
    
    # Fetch the current question to get its visualization settings
    response = migrator.session.get(
        f"{migrator.config.base_url}/api/card/{question_id}",
        headers={"X-Metabase-Session": migrator.session_token}
    )
    
    if response.status_code == 200:
        question = response.json()
        viz_settings = question.get('visualization_settings', {})
        print(f"    📊 Current visualization settings: {viz_settings}")
        
        # Get dimensions
        dimensions = viz_settings.get('graph.dimensions', [])
        columns.update(dimensions)
        print(f"    📏 Current dimensions: {dimensions}")
        
        # Get metrics
        metrics = viz_settings.get('graph.metrics', [])
        columns.update(metrics)
        print(f"    📈 Current metrics: {metrics}")
        
        # Get other potential column references
        for key, value in viz_settings.items():
            if isinstance(value, str) and value not in ['null', 'true', 'false']:
                columns.add(value)
    
    print(f"    🎯 Current columns: {list(columns)}")
    return columns

def log_and_print(message, log_file=None):
    print(message)
    if log_file:
        log_file.write(message + '\n')

def log_timing(start_time, step_name):
    """Log timing for a step"""
    elapsed = time.time() - start_time
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"⏱️  [{timestamp}] {step_name}: {elapsed:.2f}s")
    return time.time()

def clean_sql_for_starrocks(sql, visualization_columns, table_mapping):
    """Clean SQL for StarRocks compatibility"""
    start_time = time.time()
    print(f"  🔧 Applying StarRocks compatibility fixes...")
    
    # First pass: Replace schema.table patterns (longer patterns first)
    for exasol_table, starrocks_table in table_mapping.items():
        if '.' in exasol_table:
            exasol_schema, exasol_name = exasol_table.split('.', 1)
            
            # Replace full schema.table format (e.g., mart.transactions)
            if exasol_table in sql:
                sql = sql.replace(exasol_table, starrocks_table)
                print(f"    🔄 Replaced '{exasol_table}' -> '{starrocks_table}'")
            
            # Replace uppercase schema.table format (e.g., MART.TRANSACTIONS)
            uppercase_pattern = f"{exasol_schema.upper()}.{exasol_name.upper()}"
            if uppercase_pattern in sql:
                sql = sql.replace(uppercase_pattern, starrocks_table)
                print(f"    🔄 Replaced '{uppercase_pattern}' -> '{starrocks_table}'")
            
            # Replace mixed case schema.table format (e.g., MART.transactions)
            mixed_pattern1 = f"{exasol_schema.upper()}.{exasol_name.lower()}"
            if mixed_pattern1 in sql:
                sql = sql.replace(mixed_pattern1, starrocks_table)
                print(f"    🔄 Replaced '{mixed_pattern1}' -> '{starrocks_table}'")
            
            mixed_pattern2 = f"{exasol_schema.lower()}.{exasol_name.upper()}"
            if mixed_pattern2 in sql:
                sql = sql.replace(mixed_pattern2, starrocks_table)
                print(f"    🔄 Replaced '{mixed_pattern2}' -> '{starrocks_table}'")
    
    # Second pass: Contextual replacement - find which StarRocks tables are actually used
    # and only replace standalone references to those specific table names
    used_starrocks_tables = set()
    
    # Find all StarRocks table names that are actually used in the SQL
    for starrocks_table in table_mapping.values():
        if starrocks_table in sql:
            used_starrocks_tables.add(starrocks_table)
            print(f"    📋 Found StarRocks table in use: '{starrocks_table}'")
    
    # For each used StarRocks table, find the corresponding Exasol table name
    # and replace standalone references to that table name
    for exasol_table, starrocks_table in table_mapping.items():
        if starrocks_table in used_starrocks_tables:
            if '.' in exasol_table:
                _, exasol_name = exasol_table.split('.', 1)
            else:
                exasol_name = exasol_table
            
            # Replace standalone references to this table name
            if re.search(rf'\b{re.escape(exasol_name.upper())}\b', sql):
                sql = re.sub(rf'\b{re.escape(exasol_name.upper())}\b', starrocks_table, sql)
                print(f"    🔄 Contextual replacement: '{exasol_name.upper()}' -> '{starrocks_table}'")
            
            if re.search(rf'\b{re.escape(exasol_name.lower())}\b', sql):
                sql = re.sub(rf'\b{re.escape(exasol_name.lower())}\b', starrocks_table, sql)
                print(f"    🔄 Contextual replacement: '{exasol_name.lower()}' -> '{starrocks_table}'")
    
    # Fix StarRocks window function syntax
    sql = re.sub(r'PARTITION BY 1', '', sql, flags=re.IGNORECASE)
    sql = re.sub(r'OVER \(\)', 'OVER ()', sql, flags=re.IGNORECASE)
    
    # Replace Exasol-specific functions with StarRocks equivalents
    # NULLIFZERO(value) -> NULLIF(value, 0)
    sql = re.sub(r'NULLIFZERO\s*\(\s*([^)]+)\s*\)', r'NULLIF(\1, 0)', sql, flags=re.IGNORECASE)
    
    # zeroifnull -> ifnull(, 0)
    sql = re.sub(r'zeroifnull\s*\(\s*([^)]+)\s*\)', r'ifnull(\1, 0)', sql, flags=re.IGNORECASE)
    
    # Fix nullif(bigint(20)) compatibility issue
    # Replace nullif(bigint(20)) with ifnull(bigint(20), 0)
    sql = re.sub(r'nullif\s*\(\s*bigint\s*\(\s*20\s*\)\s*\)', r'ifnull(bigint(20), 0)', sql, flags=re.IGNORECASE)
    
    # Fix NULLIF compatibility - cast value to float
    # NULLIF(value, 0) -> NULLIF(cast(value as float), 0)
    # But avoid double-casting if already cast
    sql = re.sub(
        r'NULLIF\s*\(\s*(?!cast\()([^,]+)\s*,\s*0\s*\)',
        r'NULLIF(cast(\1 as float), 0)',
        sql,
        flags=re.IGNORECASE
    )
    
    # convert -> cast
    sql = re.sub(r'convert\s*\(\s*([^)]+)\s*\)', r'cast(\1)', sql, flags=re.IGNORECASE)
    
    # to_char -> char
    original_sql = sql
    sql = re.sub(r'to_char\s*\(\s*([^)]+)\s*\)', r'char(\1)', sql, flags=re.IGNORECASE)
    if sql != original_sql:
        print(f"    🔄 Replaced to_char() with char()")
    
    # to_date -> date
    sql = re.sub(r'to_date\s*\(\s*([^)]+)\s*\)', r'date(\1)', sql, flags=re.IGNORECASE)
    
    # Fix json_value patterns
    # json_value(t.FEE_PARAMETERS, '$.profit_fx_markup') -> parse_json(t.FEE_PARAMETERS)->'profit_fx_markup'
    sql = re.sub(
        r'json_value\s*\(\s*([^,]+)\s*,\s*[\'"]([^\'"]+)[\'"]\s*\)',
        r'parse_json(\1)->\'\2\'',
        sql,
        flags=re.IGNORECASE
    )
    
    # json_value with complex path -> CAST(JSON_QUERY(...))
    sql = re.sub(
        r'json_value\s*\(\s*([^,]+)\s*,\s*[\'"]([^\'"]+)[\'"]\s*\)',
        r'CAST(JSON_QUERY(parse_json(\1), \'\2\') AS VARCHAR(128))',
        sql,
        flags=re.IGNORECASE
    )
    
    # Fix full outer join in CTEs - replace with left join + union
    # This is a complex transformation that needs careful handling
    # For now, we'll add a warning and suggest manual review
    if re.search(r'FULL\s+OUTER\s+JOIN', sql, flags=re.IGNORECASE):
        print(f"    ⚠️  WARNING: Found FULL OUTER JOIN - may need manual conversion")
    
    # Fix null handling in != comparisons
    # In Exasol, != preserves nulls, in StarRocks it filters them out
    # We need to explicitly handle nulls: column != value -> (column != value OR column IS NULL)
    # This is complex and may need manual review for specific cases
    
    # Fix distinct in window functions
    # count(distinct column) over (partition by ...) -> not supported in StarRocks
    # We'll add a warning for this
    if re.search(r'count\s*\(\s*distinct\s+[^)]+\)\s+over\s*\(', sql, flags=re.IGNORECASE):
        print(f"    ⚠️  WARNING: Found DISTINCT in window function - not supported in StarRocks")
    
    # Fix sum()/sum() division patterns
    # sum(revenue_EUR)/sum(Turnover_EUR) -> sum(revenue_EUR)/cast(sum(Turnover_EUR) as float)
    sql = re.sub(
        r'sum\s*\(\s*([^)]+)\s*\)\s*/\s*sum\s*\(\s*([^)]+)\s*\)',
        r'sum(\1)/cast(sum(\2) as float)',
        sql,
        flags=re.IGNORECASE
    )
    
    # Add table aliases to subqueries without names
    # select * from (select * from table) -> select * from (select * from table) as subquery
    sql = re.sub(
        r'from\s*\(\s*select\s+\*\s+from\s+([^)]+)\s*\)\s*(?=\s|$)',
        r'from (select * from \1) as subquery',
        sql,
        flags=re.IGNORECASE
    )
    
    # Convert granularity field reference to template tag parameter
    # date_trunc(gran.granularity, fatpay.PAYMENT_AT) -> date_trunc({{granularity}}, fatpay.PAYMENT_AT)
    # Handle any table alias: fg.granularity, gran.granularity, etc.
    sql = re.sub(
        r'date_trunc\s*\(\s*[a-zA-Z_]+\.granularity\s*,\s*([^)]+)\s*\)',
        r'date_trunc({{granularity}}, \1)',
        sql,
        flags=re.IGNORECASE
    )
    
    # Change "grouping" to "grouped" everywhere except in template variables
    # This handles cases like "as grouping" -> "as grouped"
    sql = re.sub(
        r'\bgrouping\b(?!\})',  # Negative lookahead to avoid matching {{grouping}}
        r'grouped',
        sql,
        flags=re.IGNORECASE
    )
    
    # Convert listagg to group_concat for StarRocks compatibility
    # listagg(column, ',') -> group_concat(column, ',')
    sql = re.sub(
        r'listagg\s*\(\s*([^)]+)\s*\)',
        r'group_concat(\1)',
        sql,
        flags=re.IGNORECASE
    )
    
    # Fix median function - StarRocks doesn't have PERCENTILE_CONT, use a different approach
    # Replace PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY column) with a window function approach
    sql = re.sub(
        r'PERCENTILE_CONT\(0\.5\)\s+WITHIN\s+GROUP\s*\(\s*ORDER\s+BY\s+([^)]+)\s*\)',
        r'PERCENTILE_CONT(\1, 0.5)',
        sql,
        flags=re.IGNORECASE
    )
    
    # Also handle direct median() function calls - use correct StarRocks syntax
    sql = re.sub(
        r'median\s*\(\s*([^)]+)\s*\)',
        r'PERCENTILE_CONT(\1, 0.5)',
        sql,
        flags=re.IGNORECASE
    )
    
    # Fix column aliases based on visualization settings
    for col in visualization_columns:
        if col:
            # Handle subquery aliases (as column_name)
            pattern = rf'as\s+{re.escape(col.lower())}\b'
            replacement = f'as {col}'
            sql = re.sub(pattern, replacement, sql, flags=re.IGNORECASE)
            
            # Handle main query references (tr.column_name)
            pattern = rf'tr\.{re.escape(col.lower())}\b'
            replacement = f'tr.{col}'
            sql = re.sub(pattern, replacement, sql, flags=re.IGNORECASE)
            
            # Handle other table references (table.column_name)
            pattern = rf'\b{re.escape(col.lower())}\b'
            replacement = col
            sql = re.sub(pattern, replacement, sql, flags=re.IGNORECASE)
    
    print(f"  ✅ StarRocks compatibility fixes applied")
    log_timing(start_time, "SQL cleaning")
    return sql

def convert_granularity_to_static_list(template_tags, dashboard_id):
    """Convert granularity from field reference to static list parameter"""
    if dashboard_id not in DASHBOARD_CONFIG:
        return template_tags
    
    config = DASHBOARD_CONFIG[dashboard_id]
    if not config.get("granularity_to_static_list", False):
        return template_tags
    
    updated_tags = {}
    for tag_name, tag_config in template_tags.items():
        if tag_name == "granularity":
            # Convert to static list with default value
            updated_tags[tag_name] = {
                "id": tag_config.get("id", "granularity"),
                "name": "granularity",
                "display-name": "Granularity",
                "type": "text",
                "required": True,
                "default": config.get("granularity_default", "week"),
                "values_source_type": "static-list",
                "values_source_config": {
                    "values": config["granularity_static_values"]
                }
            }
            print(f"  🔄 Converted granularity to static list parameter with default '{config.get('granularity_default', 'week')}'")
        else:
            updated_tags[tag_name] = tag_config
    
    return updated_tags

def update_template_tags(template_tags, column_mapping):
    """Update template tags with new column IDs"""
    updated_tags = {}
    unmapped_fields = []
    
    print(f"  🔍 Debug: Column mapping has {len(column_mapping)} entries")
    print(f"  🔍 Debug: Template tags: {list(template_tags.keys())}")
    
    for tag_name, tag_config in template_tags.items():
        updated_tag = tag_config.copy()
        
        # Update field-id if it exists and has a mapping
        if 'field-id' in tag_config:
            exasol_field_id = tag_config['field-id']
            exasol_field_id_str = str(exasol_field_id)
            print(f"  🔍 Debug: Looking for field-id {exasol_field_id_str} in mapping")
            if exasol_field_id_str in column_mapping:
                updated_tag['field-id'] = column_mapping[exasol_field_id_str]
                print(f"  🔄 Updated template tag '{tag_name}': field-id {exasol_field_id} -> {column_mapping[exasol_field_id_str]}")
            else:
                print(f"  ⚠️  No mapping found for field-id {exasol_field_id} in '{tag_name}'")
                unmapped_fields.append(f"{tag_name} (field-id: {exasol_field_id})")
        
        # Update dimension field IDs if they exist and have mappings
        if 'dimension' in tag_config and isinstance(tag_config['dimension'], list):
            dimension = tag_config['dimension'].copy()
            if len(dimension) >= 2 and dimension[0] == 'field' and isinstance(dimension[1], int):
                exasol_field_id = dimension[1]
                exasol_field_id_str = str(exasol_field_id)
                print(f"  🔍 Debug: Looking for dimension field-id {exasol_field_id_str} in mapping")
                if exasol_field_id_str in column_mapping:
                    dimension[1] = column_mapping[exasol_field_id_str]
                    updated_tag['dimension'] = dimension
                    print(f"  🔄 Updated template tag '{tag_name}': dimension field {exasol_field_id} -> {column_mapping[exasol_field_id_str]}")
                else:
                    print(f"  ⚠️  No mapping found for dimension field {exasol_field_id} in '{tag_name}'")
                    unmapped_fields.append(f"{tag_name} (dimension field: {exasol_field_id})")
        
        updated_tags[tag_name] = updated_tag
    
    if unmapped_fields:
        print(f"  ❌ Found unmapped fields: {unmapped_fields}")
        print(f"  ⚠️  This question cannot be migrated due to missing field mappings")
        return None
    
    return updated_tags

def update_question(question_id, converted_sql, visualization_columns, migrator, migration_mapping, dashboard_id, dashboard_data=None, column_config=None):
    """Update a specific question in Metabase"""
    print(f"  🔄 Updating Question {question_id}")
    
    # Fetch current question
    response = migrator.session.get(
        f"{migrator.config.base_url}/api/card/{question_id}",
        headers={"X-Metabase-Session": migrator.session_token}
    )
    
    if response.status_code != 200:
        print(f"  ❌ Failed to fetch question: {response.status_code}")
        return False
    
    question = response.json()
    print(f"  ✅ Found question: {question.get('name', 'Unknown')}")
    
    # Get current SQL and database
    dataset_query = question.get('dataset_query', {})
    native_query = dataset_query.get('native', {})
    current_sql = native_query.get('query', '')
    current_database_id = dataset_query.get('database')
    
    print(f"  📄 Current database ID: {current_database_id}")
    
    # Get template tags
    template_tags = native_query.get('template-tags', {})
    print(f"  🏷️  Template tags: {list(template_tags.keys())}")
    
    # Get current visualization settings to preserve formatting
    current_viz_settings = question.get('visualization_settings', {})
    print(f"  📊 Current visualization settings: {len(current_viz_settings)} keys")
    
    # Get original visualization settings from dashboard if available
    original_viz_settings = {}
    if dashboard_data:
        original_viz_settings = get_visualization_settings(dashboard_data, question_id)
        print(f"  📊 Original visualization settings: {len(original_viz_settings)} keys")
    
    # Clean SQL for StarRocks
    cleaned_sql = clean_sql_for_starrocks(converted_sql, visualization_columns, migration_mapping['table_mapping'])
    
    # Update template tags with new column IDs
    column_mapping = migration_mapping['column_mapping']
    
    # First convert granularity to static list if configured
    template_tags = convert_granularity_to_static_list(template_tags, dashboard_id)
    
    # Then update other template tags with new column IDs
    updated_template_tags = update_template_tags(template_tags, column_mapping)
    
    # Check if template tag update failed due to unmapped fields
    if updated_template_tags is None:
        print(f"  ❌ Cannot migrate question due to unmapped template tag fields")
        return False
    
    # Use target database
    target_database_id = migration_mapping['database_mapping']['starrocks']
    print(f"  🗄️  Database: {current_database_id} -> {target_database_id}")
    
    # Get column mapping from configuration
    if column_config is None:
        column_config = load_column_mapping_config()
    
    column_name_mapping = get_column_mapping_for_dashboard(dashboard_id, column_config)
    
    # Use original visualization settings if available, otherwise use current ones
    viz_settings_to_map = original_viz_settings if original_viz_settings else current_viz_settings
    mapped_viz_settings = map_column_names_in_visualization_settings(viz_settings_to_map, column_name_mapping)
    
    # Enhance visualization settings with formatting preservation
    formatting_config = column_config.get("formatting_preservation", {})
    enhanced_viz_settings = enhance_visualization_settings_with_formatting(mapped_viz_settings, column_name_mapping, formatting_config)
    
    # Apply display name mappings to preserve original column titles
    display_name_mappings = column_config.get("display_name_mappings", {})
    final_viz_settings = apply_display_name_mappings(enhanced_viz_settings, display_name_mappings)
    
    # Update the question
    update_data = {
        "dataset_query": {
            "type": "native",
            "native": {
                "query": cleaned_sql,
                "template-tags": updated_template_tags
            },
            "database": target_database_id
        },
        "visualization_settings": final_viz_settings
    }
    
    print(f"  📤 Sending update request to Metabase...")
    print(f"  📋 Update data preview: {str(update_data)[:200]}...")
    
    response = migrator.session.put(
        f"{migrator.config.base_url}/api/card/{question_id}",
        headers={
            "X-Metabase-Session": migrator.session_token,
            "Content-Type": "application/json"
        },
        json=update_data
    )
    
    print(f"  📥 Response status: {response.status_code}")
    print(f"  📥 Response headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        print(f"  ✅ Question {question_id} updated successfully!")
        print(f"  📄 Response content: {response.text[:500]}...")
        
        # Verify the update by fetching the question again
        verify_response = migrator.session.get(
            f"{migrator.config.base_url}/api/card/{question_id}",
            headers={"X-Metabase-Session": migrator.session_token}
        )
        
        if verify_response.status_code == 200:
            updated_question = verify_response.json()
            updated_dataset_query = updated_question.get('dataset_query', {})
            updated_database_id = updated_dataset_query.get('database')
            print(f"  ✅ Verification: Question now uses database {updated_database_id}")
            
            # Check if the SQL was actually updated
            updated_native_query = updated_dataset_query.get('native', {})
            updated_sql = updated_native_query.get('query', '')
            print(f"  ✅ Verification: SQL updated successfully")
            print(f"  📄 Updated SQL preview: {updated_sql[:100]}...")
            
            # Check if visualization settings were preserved
            updated_viz_settings = updated_question.get('visualization_settings', {})
            print(f"  ✅ Verification: Visualization settings preserved ({len(updated_viz_settings)} keys)")
        else:
            print(f"  ⚠️  Could not verify update: {verify_response.status_code}")
        
        return True
    else:
        print(f"  ❌ Update failed: {response.status_code}")
        print(f"  📄 Error response: {response.text}")
        return False

def update_mbql_question(question_id, mbql_json, migrator, migration_mapping, dashboard_id, dashboard_data=None, column_config=None):
    """Update a specific MBQL question in Metabase."""
    print(f"  🔄 Updating MBQL Question {question_id}")
    # Fetch current question
    response = migrator.session.get(
        f"{migrator.config.base_url}/api/card/{question_id}",
        headers={"X-Metabase-Session": migrator.session_token}
    )
    if response.status_code != 200:
        print(f"  ❌ Failed to fetch question: {response.status_code}")
        return False
    question = response.json()
    print(f"  ✅ Found question: {question.get('name', 'Unknown')}")
    # Print original MBQL JSON for inspection
    print(f"  [DEBUG] Original MBQL JSON for question {question_id}:")
    print(json.dumps(mbql_json, indent=2))
    # Get current visualization settings to preserve formatting
    current_viz_settings = question.get('visualization_settings', {})
    print(f"  📊 Current visualization settings: {len(current_viz_settings)} keys")
    # Get original visualization settings from dashboard if available
    original_viz_settings = {}
    if dashboard_data:
        original_viz_settings = get_visualization_settings(dashboard_data, question_id)
        print(f"  📊 Original visualization settings: {len(original_viz_settings)} keys")
    # Map tables and field IDs in MBQL JSON
    table_mapping = migration_mapping['table_mapping']
    column_mapping = migration_mapping['column_mapping']
    mapped_mbql = map_tables_in_mbql(json.loads(json.dumps(mbql_json)), table_mapping)
    mapped_mbql = map_field_ids_in_mbql(mapped_mbql, column_mapping)
    # Print mapped MBQL JSON for inspection
    print(f"  [DEBUG] Mapped MBQL JSON for question {question_id}:")
    print(json.dumps(mapped_mbql, indent=2))
    # Set the target database
    mapped_mbql['database'] = migration_mapping['database_mapping']['starrocks']
    # Get column mapping from configuration
    if column_config is None:
        column_config = load_column_mapping_config()
    column_name_mapping = get_column_mapping_for_dashboard(dashboard_id, column_config)
    # Use original visualization settings if available, otherwise use current ones
    viz_settings_to_map = original_viz_settings if original_viz_settings else current_viz_settings
    mapped_viz_settings = map_column_names_in_visualization_settings(viz_settings_to_map, column_name_mapping)
    # Enhance visualization settings with formatting preservation
    formatting_config = column_config.get("formatting_preservation", {})
    enhanced_viz_settings = enhance_visualization_settings_with_formatting(mapped_viz_settings, column_name_mapping, formatting_config)
    # Apply display name mappings to preserve original column titles
    display_name_mappings = column_config.get("display_name_mappings", {})
    final_viz_settings = apply_display_name_mappings(enhanced_viz_settings, display_name_mappings)
    # Update the question
    update_data = {
        "dataset_query": mapped_mbql,
        "visualization_settings": final_viz_settings
    }
    print(f"  📤 Sending MBQL update request to Metabase...")
    print(f"  📋 MBQL Update data preview: {str(update_data)[:200]}...")
    response = migrator.session.put(
        f"{migrator.config.base_url}/api/card/{question_id}",
        headers={
            "X-Metabase-Session": migrator.session_token,
            "Content-Type": "application/json"
        },
        json=update_data
    )
    print(f"  📥 Response status: {response.status_code}")
    print(f"  📥 Response headers: {dict(response.headers)}")
    if response.status_code == 200:
        print(f"  ✅ MBQL Question {question_id} updated successfully!")
        print(f"  📄 Response content: {response.text[:500]}...")
        return True
    else:
        print(f"  ❌ MBQL Update failed: {response.status_code}")
        print(f"  📄 Error response: {response.text}")
        return False

def validate_question_response(question_id, question_name, migrator, log_file=None):
    """Validate if a migrated question returns a valid response"""
    log_and_print(f"  🔍 Validating Question {question_id}: {question_name}", log_file)
    
    # First, get the question details
    response = migrator.session.get(
        f"{migrator.config.base_url}/api/card/{question_id}",
        headers={"X-Metabase-Session": migrator.session_token}
    )
    
    if response.status_code != 200:
        log_and_print(f"    ❌ Failed to fetch question: {response.status_code}", log_file)
        return False
    
    question = response.json()
    dataset_query = question.get('dataset_query', {})
    database_id = dataset_query.get('database')
    query_type = dataset_query.get('type')
    
    log_and_print(f"    📊 Database ID: {database_id}", log_file)
    log_and_print(f"    📝 Query Type: {query_type}", log_file)
    
    # For native queries, show the SQL
    if query_type == 'native':
        native_query = dataset_query.get('native', {})
        sql = native_query.get('query', '')
        log_and_print(f"    🔍 SQL Preview: {sql[:100]}...", log_file)
    
    # Try to execute the query
    try:
        # Use the query endpoint to get results
        query_response = migrator.session.post(
            f"{migrator.config.base_url}/api/dataset",
            headers={
                "X-Metabase-Session": migrator.session_token,
                "Content-Type": "application/json"
            },
            json=dataset_query
        )
        
        if query_response.status_code in [200, 202]:  # Both 200 and 202 indicate success
            result = query_response.json()
            
            # Check if there's an error in the response
            if 'error' in result:
                log_and_print(f"    ❌ SQL Error: {result['error']}", log_file)
                return False
            
            # Check if there's an error message in the data
            data = result.get('data', {})
            if 'error' in data:
                log_and_print(f"    ❌ SQL Error: {data['error']}", log_file)
                return False
            
            # Check if there's an error message in the response text
            response_text = query_response.text.lower()
            if 'syntax error' in response_text or 'error' in response_text:
                log_and_print(f"    ❌ SQL Error detected in response", log_file)
                log_and_print(f"    📄 Response: {query_response.text}", log_file)
                return False
            
            rows = data.get('rows', [])
            cols = data.get('cols', [])
            
            log_and_print(f"    ✅ Query executed successfully!", log_file)
            log_and_print(f"    📊 Rows returned: {len(rows)}", log_file)
            log_and_print(f"    📋 Columns: {len(cols)}", log_file)
            
            # Show column names
            column_names = [col.get('name', 'Unknown') for col in cols]
            log_and_print(f"    📝 Column names: {column_names}", log_file)
            
            # Show first few rows if any
            if rows:
                log_and_print(f"    📈 First row: {rows[0]}", log_file)
                if len(rows) > 1:
                    log_and_print(f"    📈 Second row: {rows[1]}", log_file)
            else:
                log_and_print(f"    ⚠️  No data returned", log_file)
            
            return True
            
        else:
            log_and_print(f"    ❌ Query execution failed: {query_response.status_code}", log_file)
            log_and_print(f"    📄 Error: {query_response.text}", log_file)
            return False
            
    except Exception as e:
        log_and_print(f"    ❌ Exception during query execution: {str(e)}", log_file)
        return False

def validate_migration(dashboard_migration, migrator):
    """Validate all migrated questions and write results to a file"""
    filename = f'migrations/validation_results_dashboard_{dashboard_migration["dashboard_id"]}.txt'
    with open(filename, 'w') as log_file:
        log_and_print(f"\n🔍 Validating migration results...", log_file)
        log_and_print("=" * 60, log_file)
        questions = dashboard_migration.get('questions', [])
        log_and_print(f"📊 Validating {len(questions)} questions", log_file)
        success_count = 0
        total_count = 0
        for question in questions:
            question_id = question.get('question_id')
            question_name = question.get('question_name')
            question_type = question.get('type')
            converted_sql = question.get('converted_sql')
            if question_type != 'native' or not converted_sql:
                log_and_print(f"⏭️  Skipping question {question_id} ({question_name}) - not a native SQL question", log_file)
                continue
            total_count += 1
            log_and_print(f"\n📝 Validating Question {total_count}/{len([q for q in questions if q.get('type') == 'native' and q.get('converted_sql')])}", log_file)
            log_and_print("-" * 50, log_file)
            if validate_question_response(question_id, question_name, migrator, log_file):
                success_count += 1
            time.sleep(1)
        log_and_print(f"\n🎉 Validation Summary:", log_file)
        log_and_print(f"✅ Successfully validated: {success_count}/{total_count} questions", log_file)
        if success_count == total_count:
            log_and_print(f"🎊 All questions are working correctly! Migration successful!", log_file)
            return True
        else:
            log_and_print(f"⚠️  Some questions have issues. Migration may need fixes.", log_file)
            return False

def load_column_mapping_config():
    """Load the column mapping configuration from file"""
    try:
        with open('column_mapping_config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Column mapping configuration file not found. Using default mappings.")
        return {
            "column_mappings": {
                "exasol_to_starrocks": {}
            },
            "dashboard_specific_mappings": {},
            "formatting_preservation": {
                "percentage_columns": [],
                "currency_columns": [],
                "mini_bar_columns": [],
                "conditional_formatting_rules": {}
            }
        }

def get_column_mapping_for_dashboard(dashboard_id, column_config):
    """Get the complete column mapping for a specific dashboard"""
    # Start with the base mappings
    base_mappings = column_config.get("column_mappings", {}).get("exasol_to_starrocks", {})
    
    # Add dashboard-specific mappings if they exist
    dashboard_mappings = column_config.get("dashboard_specific_mappings", {}).get(str(dashboard_id), {})
    additional_mappings = dashboard_mappings.get("additional_mappings", {})
    
    # Merge the mappings
    complete_mapping = base_mappings.copy()
    complete_mapping.update(additional_mappings)
    
    print(f"  📋 Loaded {len(complete_mapping)} column mappings for dashboard {dashboard_id}")
    if additional_mappings:
        print(f"  📋 Including {len(additional_mappings)} dashboard-specific mappings")
    
    return complete_mapping

def enhance_visualization_settings_with_formatting(viz_settings, column_mapping, formatting_config):
    """Enhance visualization settings with formatting preservation based on configuration"""
    if not viz_settings:
        return viz_settings
    
    enhanced_settings = viz_settings.copy()
    
    # Get formatting configuration
    percentage_columns = formatting_config.get("percentage_columns", [])
    currency_columns = formatting_config.get("currency_columns", [])
    mini_bar_columns = formatting_config.get("mini_bar_columns", [])
    conditional_formatting_rules = formatting_config.get("conditional_formatting_rules", {})
    
    # Ensure column_settings exists
    if 'column_settings' not in enhanced_settings:
        enhanced_settings['column_settings'] = {}
    
    # Apply formatting to columns based on configuration
    for exasol_col, starrocks_col in column_mapping.items():
        column_key = f'["name","{starrocks_col}"]'
        
        # Initialize column settings if not exists
        if column_key not in enhanced_settings['column_settings']:
            enhanced_settings['column_settings'][column_key] = {}
        
        # Apply percentage formatting
        if exasol_col in percentage_columns:
            enhanced_settings['column_settings'][column_key]['number_style'] = 'percent'
            print(f"    🎨 Applied percentage formatting to '{starrocks_col}'")
        
        # Apply currency formatting
        if exasol_col in currency_columns:
            enhanced_settings['column_settings'][column_key]['number_style'] = 'currency'
            enhanced_settings['column_settings'][column_key]['decimals'] = 0
            print(f"    💰 Applied currency formatting to '{starrocks_col}'")
        
        # Apply mini bar formatting
        if exasol_col in mini_bar_columns:
            enhanced_settings['column_settings'][column_key]['show_mini_bar'] = True
            print(f"    📊 Applied mini bar to '{starrocks_col}'")
        
        # Apply conditional formatting rules
        if exasol_col in conditional_formatting_rules:
            rules = conditional_formatting_rules[exasol_col]
            if 'table.column_formatting' not in enhanced_settings:
                enhanced_settings['table.column_formatting'] = []
            
            # Add rules for this column
            for rule in rules:
                rule_copy = rule.copy()
                rule_copy['columns'] = [starrocks_col]
                enhanced_settings['table.column_formatting'].append(rule_copy)
            
            print(f"    🎯 Applied conditional formatting to '{starrocks_col}'")
    
    return enhanced_settings

def apply_display_name_mappings(viz_settings, display_name_mappings):
    """Apply display name mappings to preserve original column titles"""
    if not viz_settings or not display_name_mappings:
        return viz_settings
    
    enhanced_settings = viz_settings.copy()
    
    # Ensure column_settings exists
    if 'column_settings' not in enhanced_settings:
        enhanced_settings['column_settings'] = {}
    
    # Apply display name mappings to column settings
    for starrocks_col, display_name in display_name_mappings.items():
        column_key = f'["name","{starrocks_col}"]'
        
        # Initialize column settings if not exists
        if column_key not in enhanced_settings['column_settings']:
            enhanced_settings['column_settings'][column_key] = {}
        
        # Set the column title to preserve the original display name
        enhanced_settings['column_settings'][column_key]['column_title'] = display_name
        print(f"    📝 Applied display name: '{starrocks_col}' -> '{display_name}'")
    
    return enhanced_settings

# Add Exasol to StarRocks table ID mapping (expand as needed)
table_id_mapping = {
    31801: 87212,
    71055: 87239,
    35483: 90833,
    35484: 90838,
    32333: 87253,
    37762: 90421,
    37460: 90425,
    24797: 87236,
    32652: 87241,
    164: 87251,
    41076: 90423,
    41074: 90419,
    98: 87210,
    84359: 90422,
    77213: 90655,
    77208: 90654,
    26542: 87228,
    42763: 87257,
    51: 87209,
    35485: 90424,
    36348: 87237,
    39315: 91055,
    1161: 87218,
    163: 87249,
    222: 87229,
    1570: 87225,
    33784: 87215,
    36071: 90835,
    38534: 87234,
    31632: 91065,
    31635: 87211,
    37403: 88338,
    32962: 88337,
    35325: 88772,
    1314: 90837,
    87010: 87232,
    853: 87258,
    31187: 87250,
    37671: 88339,
    78230: 87201,
    39928: 87222,
    25041: 87245,
    34803: 87252,
    34790: 87216,
    36046: 87247,
    42183: 89022,
    2841: 87204,
    37604: 87203,
    45: 87255,
    31112: 87227,
    38562: 90597,
    31634: 87202,
    701: 87238,
    74490: 87223,
    157: 87205,
    233: 87244,
    160: 91005,
    35480: 90832,
    32503: 90420,
    35481: 90418,
    62: 90834,
    108: 87235,
    210: 87206,
    213: 87214,
    26390: 87230,
    36: 89193,
    71209: 87240,
    36832: 87243,
    212: 87256,
    29: 87383,
    147: 89180,
    96: 91060,
    24295: 87213,
    24283: 87217,
    190: 87221,
    232: 87207,
    39805: 87242,
    99: 87248,
    204: 87219,
    37236: 87226,
    39403: 89181,
    24284: 87224,
    122: 87208,
    64538: 87254,
    9: 87220,
    37377: 88340
}

def map_tables_in_mbql(mbql_json, table_mapping):
    """Recursively map table names and table IDs in MBQL JSON using table_mapping and table_id_mapping."""
    if isinstance(mbql_json, dict):
        for k, v in list(mbql_json.items()):  # Use list() to avoid runtime dict size change
            if k == 'table' and isinstance(v, str):
                mapped = table_mapping.get(v, None)
                if mapped:
                    print(f"    🔄 MBQL table mapping: '{v}' -> '{mapped}'")
                    mbql_json[k] = mapped
                else:
                    if '.' in v:
                        _, table_only = v.split('.', 1)
                        mapped = table_mapping.get(table_only, None)
                        if mapped:
                            print(f"    🔄 MBQL table mapping (schema removed): '{v}' -> '{mapped}'")
                            mbql_json[k] = mapped
                        else:
                            print(f"    ⚠️  No mapping found for MBQL table: '{v}' (schema removed: '{table_only}')")
                    else:
                        print(f"    ⚠️  No mapping found for MBQL table: '{v}'")
            elif k == 'source-table' and isinstance(v, int):
                mapped_id = table_id_mapping.get(v, None)
                if mapped_id:
                    print(f"    🔄 MBQL table ID mapping: {v} -> {mapped_id}")
                    mbql_json[k] = mapped_id
                else:
                    print(f"    ⚠️  No mapping found for MBQL table ID: {v}")
            # Always recurse into all values
            map_tables_in_mbql(v, table_mapping)
    elif isinstance(mbql_json, list):
        for item in mbql_json:
            map_tables_in_mbql(item, table_mapping)
    return mbql_json

def map_field_ids_in_mbql(mbql_json, column_mapping, parent_key=None, top_level=False):
    """Recursively map field IDs in MBQL JSON using column_mapping.
    Only skip unmapped fields in top-level 'fields' and 'aggregation' arrays.
    """
    # Handle lists
    if isinstance(mbql_json, list):
        # MBQL field reference: ["field", <id>, ...]
        if len(mbql_json) > 1 and mbql_json[0] == "field" and isinstance(mbql_json[1], int):
            old_id = mbql_json[1]
            new_id = column_mapping.get(str(old_id), None)
            if new_id:
                print(f"    🔄 MBQL field ID mapping: {old_id} -> {new_id}")
                mbql_json[1] = new_id
            else:
                print(f"    ⚠️  No mapping found for MBQL field ID: {old_id}")
                # Only skip if in top-level 'fields' or 'aggregation' array
                if top_level and parent_key in ("fields", "aggregation"):
                    print(f"    ⚠️  Skipping field {old_id} in top-level '{parent_key}' array")
                    return None
            # Recurse into the rest of the field reference
            for item in mbql_json[2:]:
                map_field_ids_in_mbql(item, column_mapping)
            return mbql_json
        # Otherwise, process the list and filter out None results if top-level
        new_list = []
        for item in mbql_json:
            mapped_item = map_field_ids_in_mbql(item, column_mapping, parent_key, top_level)
            if mapped_item is not None:
                new_list.append(mapped_item)
        return new_list
    # Handle dicts
    elif isinstance(mbql_json, dict):
        # If this is the top-level query dict, set top_level=True for 'fields' and 'aggregation' keys
        for k, v in list(mbql_json.items()):
            if k in ("fields", "aggregation"):
                mapped_v = map_field_ids_in_mbql(v, column_mapping, k, top_level=True)
            else:
                mapped_v = map_field_ids_in_mbql(v, column_mapping, k, top_level=False)
            mbql_json[k] = mapped_v
        return mbql_json
    else:
        return mbql_json

def main():
    """Main function"""
    overall_start = time.time()
    # Debug print for METABASE_CONFIG (mask password)
    debug_config = METABASE_CONFIG.copy()
    if 'password' in debug_config:
        debug_config['password'] = '***MASKED***'
    print(f"[DEBUG] METABASE_CONFIG: {debug_config}")
    dashboard_id = 503  # Set to the dashboard the user wants to migrate
    
    print(f"🚀 Starting migration for Dashboard {dashboard_id}")
    print("=" * 60)
    
    # Load required data
    step_start = time.time()
    migration_mapping = load_migration_mapping()
    if not migration_mapping:
        return
    step_start = log_timing(step_start, "Load migration mapping")
    
    # Load column mapping configuration
    step_start = time.time()
    column_config = load_column_mapping_config()
    step_start = log_timing(step_start, "Load column mapping config")
    
    migrator = MetabaseMigrator(MetabaseConfig(
        base_url=METABASE_CONFIG["base_url"],
        username=METABASE_CONFIG["username"],
        password=METABASE_CONFIG["password"]
    ))
    
    step_start = time.time()
    if not migrator.authenticate():
        print("❌ Authentication failed")
        return
    step_start = log_timing(step_start, "Authentication")
    
    print("✅ Authentication successful")
    
    # Get dashboard details
    step_start = time.time()
    dashboard_data = load_dashboard_inspection(dashboard_id, migrator)
    if not dashboard_data:
        return
    step_start = log_timing(step_start, "Load dashboard inspection")
    
    # Process all questions in the dashboard
    success_count = 0
    total_count = 0
    processed_count = 0
    migrated_questions = []  # Track which questions were actually migrated
    
    step_start = time.time()
    for dashcard in dashboard_data.get('dashcards', []):
        card = dashcard.get('card', {})
        question_id = card.get('id')
        question_name = card.get('name', 'Unknown')
        
        if not question_id:
            continue
        
        print(f"\n📝 Processing Question {question_id}: {question_name}")
        print("-" * 50)
        
        processed_count += 1
        
        # Fetch the question details
        question_start = time.time()
        question_response = migrator.session.get(
            f"{migrator.config.base_url}/api/card/{question_id}",
            headers={"X-Metabase-Session": migrator.session_token}
        )
        log_timing(question_start, f"Fetch question {question_id}")
        
        if question_response.status_code != 200:
            print(f"  ❌ Failed to fetch question: {question_response.status_code}")
            continue
        
        question = question_response.json()
        dataset_query = question.get('dataset_query', {})
        query_type = dataset_query.get('type')
        
        if query_type == 'native':
            total_count += 1
            # Get current SQL
            native_query = dataset_query.get('native', {})
            current_sql = native_query.get('query', '')
            if not current_sql:
                print(f"  ⚠️  No SQL found in question {question_id}")
                continue
            print(f"  📄 Current SQL preview: {current_sql[:100]}...")
            # Get visualization columns for this question
            viz_start = time.time()
            visualization_columns = get_visualization_columns(dashboard_data, question_id)
            if not visualization_columns:
                print(f"  🔄 No visualization columns found in inspection, fetching from Metabase...")
                visualization_columns = get_current_visualization_columns(question_id, migrator)
            log_timing(viz_start, f"Get visualization columns for {question_id}")
            print(f"  📊 Visualization columns: {list(visualization_columns)}")
            # Update the question with the current SQL (it will be cleaned by clean_sql_for_starrocks)
            update_start = time.time()
            if update_question(question_id, current_sql, visualization_columns, migrator, migration_mapping, dashboard_id, dashboard_data, column_config):
                success_count += 1
                migrated_questions.append({
                    "question_id": question_id,
                    "question_name": question_name,
                    "type": "native",
                    "converted_sql": "migrated"
                })
            log_timing(update_start, f"Update question {question_id}")
        elif query_type == 'query':
            # MBQL question
            print(f"  📝 Detected MBQL question {question_id} ({question_name})")
            mbql_json = dataset_query
            update_start = time.time()
            if update_mbql_question(question_id, mbql_json, migrator, migration_mapping, dashboard_id, dashboard_data, column_config):
                success_count += 1
                migrated_questions.append({
                    "question_id": question_id,
                    "question_name": question_name,
                    "type": "mbql",
                    "converted_mbql": "migrated"
                })
            log_timing(update_start, f"Update MBQL question {question_id}")
        else:
            print(f"  ⏭️  Skipping question {question_id} ({question_name}) - unsupported question type: {query_type}")
            continue
    
    step_start = log_timing(step_start, f"Process {processed_count} questions")
    
    print(f"\n🎉 Migration Summary:")
    print(f"📊 Total dashcards processed: {processed_count}")
    print(f"📝 Native SQL questions found: {total_count}")
    print(f"✅ Successfully migrated: {success_count}/{total_count} questions")
    print(f"📊 Dashboard {dashboard_id} migration completed!")
    
    # Create a simple migration result for validation - only include migrated questions
    migration_result = {
        "dashboard_id": dashboard_id,
        "dashboard_name": dashboard_data.get('name', 'Unknown'),
        "questions": migrated_questions
    }
    
    # Validate the migration
    print(f"\n" + "=" * 60)
    print(f"🔍 VALIDATION PHASE")
    print("=" * 60)
    
    validation_start = time.time()
    if validate_migration(migration_result, migrator):
        print(f"\n🎊 FINAL RESULT: Migration successful!")
        print(f"✅ All questions migrated and validated")
        print(f"✅ Dashboard {dashboard_id} is now operational with StarRocks")
    else:
        print(f"\n⚠️  FINAL RESULT: Migration completed with issues")
        print(f"✅ {success_count} questions migrated successfully")
        print(f"❌ Some questions need manual fixes")
        print(f"🔧 Please review the validation results and fix any remaining issues")
    
    log_timing(validation_start, "Validation phase")
    log_timing(overall_start, "TOTAL MIGRATION TIME")

if __name__ == "__main__":
    main() 