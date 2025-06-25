"""
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
    "base_url": "https://metabase.mrcr.io",
    "username": "",
    "password": ""
}

# Database mappings from Exasol to StarRocks
# Add your table mappings here
DATABASE_MAPPINGS = [
    DatabaseMapping(
        exasol_db="exasol",
        exasol_schema="mart",
        exasol_table="transactions",
        starrocks_db="sr_mart",
        starrocks_table="transactions"
    ),
    # Add more mappings as needed:
    # DatabaseMapping(
    #     exasol_db="exasol",
    #     exasol_schema="analytics",
    #     exasol_table="users",
    #     starrocks_db="sr_analytics",
    #     starrocks_table="users"
    # ),
]

# SQL function mappings from Exasol to StarRocks
FUNCTION_MAPPINGS = {
    # Date functions
    "ADD_DAYS": "DATE_ADD",
    "ADD_MONTHS": "DATE_ADD",
    "ADD_YEARS": "DATE_ADD",
    "DAYS_BETWEEN": "DATEDIFF",
    "MONTHS_BETWEEN": "MONTHS_BETWEEN",
    
    # String functions
    "INSTR": "LOCATE",
    "SUBSTR": "SUBSTRING",
    
    # Aggregation functions
    "MEDIAN": "PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY",
    
    # Other functions
    "CURRENT_TIMESTAMP": "NOW()",
    "CURRENT_DATE": "CURDATE()",
}

# Migration settings
MIGRATION_SETTINGS = {
    "preserve_variables": True,
    "backup_original_sql": True,
    "output_format": "json",  # json, csv, sql
    "include_metadata": True,
}

# Exasol-specific patterns to handle
EXASOL_PATTERNS = {
    "limit_offset": r'\bLIMIT\s+(\d+)\s+OFFSET\s+(\d+)\b',
    "top_syntax": r'\bTOP\s+(\d+)\b',
    "schema_table": r'\b(\w+)\.(\w+)\b',
    "db_schema_table": r'\b(\w+)\.(\w+)\.(\w+)\b',
}

# StarRocks-specific replacements
STARROCKS_REPLACEMENTS = {
    "limit_offset": r'LIMIT \2, \1',
    "top_syntax": r'LIMIT \1',
} 
