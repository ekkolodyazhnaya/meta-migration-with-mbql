"""
SQL Converter for Exasol to StarRocks migration
Handles complex SQL syntax conversions while preserving Metabase variables
"""

import re
import logging
from typing import List, Dict, Tuple
from config import DATABASE_MAPPINGS, FUNCTION_MAPPINGS, EXASOL_PATTERNS, STARROCKS_REPLACEMENTS

logger = logging.getLogger(__name__)

class SQLConverter:
    def __init__(self):
        self.database_mappings = DATABASE_MAPPINGS
        self.function_mappings = FUNCTION_MAPPINGS
        
    def convert_sql(self, sql: str) -> str:
        """
        Convert Exasol SQL to StarRocks SQL while preserving Metabase variables
        """
        if not sql:
            return sql
            
        logger.info("Starting SQL conversion from Exasol to StarRocks")
        
        # Step 1: Protect Metabase variables
        protected_sql, variable_map = self._protect_variables(sql)
        
        # Step 2: Convert table references
        converted_sql = self._convert_table_references(protected_sql)
        
        # Step 3: Convert functions
        converted_sql = self._convert_functions(converted_sql)
        
        # Step 4: Convert syntax patterns
        converted_sql = self._convert_syntax_patterns(converted_sql)
        
        # Step 5: Restore Metabase variables
        final_sql = self._restore_variables(converted_sql, variable_map)
        
        logger.info("SQL conversion completed")
        return final_sql
    
    def _protect_variables(self, sql: str) -> Tuple[str, Dict[str, str]]:
        """
        Protect Metabase variables from being modified during conversion
        """
        variable_map = {}
        protected_sql = sql
        
        # Find all Metabase variables {{variable_name}}
        variables = re.findall(r'\{\{([^}]+)\}\}', sql)
        
        for i, variable in enumerate(variables):
            placeholder = f"__METABASE_VAR_{i}__"
            variable_map[placeholder] = f"{{{{{variable}}}}}"
            protected_sql = protected_sql.replace(f"{{{{{variable}}}}}", placeholder)
        
        return protected_sql, variable_map
    
    def _restore_variables(self, sql: str, variable_map: Dict[str, str]) -> str:
        """
        Restore Metabase variables after conversion
        """
        restored_sql = sql
        for placeholder, variable in variable_map.items():
            restored_sql = restored_sql.replace(placeholder, variable)
        
        return restored_sql
    
    def _convert_table_references(self, sql: str) -> str:
        """
        Convert table references from Exasol format to StarRocks format
        """
        converted_sql = sql
        
        for mapping in self.database_mappings:
            # Pattern for Exasol: SCHEMA.TABLE or DB.SCHEMA.TABLE
            exasol_patterns = [
                rf'\b{mapping.exasol_schema}\.{mapping.exasol_table}\b',
                rf'\b{mapping.exasol_db}\.{mapping.exasol_schema}\.{mapping.exasol_table}\b'
            ]
            
            for pattern in exasol_patterns:
                converted_sql = re.sub(
                    pattern,
                    f"{mapping.starrocks_db}.{mapping.starrocks_table}",
                    converted_sql,
                    flags=re.IGNORECASE
                )
        
        return converted_sql
    
    def _convert_functions(self, sql: str) -> str:
        """
        Convert Exasol-specific functions to StarRocks equivalents
        """
        converted_sql = sql
        
        # Convert function names
        for exasol_func, starrocks_func in self.function_mappings.items():
            # Handle special cases
            if exasol_func == "MEDIAN":
                # MEDIAN is more complex - needs special handling
                converted_sql = self._convert_median_function(converted_sql)
            else:
                # Simple function name replacement
                pattern = rf'\b{re.escape(exasol_func)}\s*\('
                converted_sql = re.sub(pattern, f"{starrocks_func}(", converted_sql, flags=re.IGNORECASE)
        
        return converted_sql
    
    def _convert_median_function(self, sql: str) -> str:
        """
        Convert Exasol MEDIAN function to StarRocks equivalent
        """
        # Pattern to match MEDIAN(column) or MEDIAN(expression)
        median_pattern = r'\bMEDIAN\s*\(\s*([^)]+)\s*\)'
        
        def replace_median(match):
            column_expr = match.group(1).strip()
            return f"PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY {column_expr})"
        
        return re.sub(median_pattern, replace_median, sql, flags=re.IGNORECASE)
    
    def _convert_syntax_patterns(self, sql: str) -> str:
        """
        Convert Exasol-specific syntax patterns to StarRocks
        """
        converted_sql = sql
        
        # Convert LIMIT OFFSET syntax
        converted_sql = re.sub(
            EXASOL_PATTERNS["limit_offset"],
            STARROCKS_REPLACEMENTS["limit_offset"],
            converted_sql,
            flags=re.IGNORECASE
        )
        
        # Convert TOP syntax to LIMIT
        converted_sql = re.sub(
            EXASOL_PATTERNS["top_syntax"],
            STARROCKS_REPLACEMENTS["top_syntax"],
            converted_sql,
            flags=re.IGNORECASE
        )
        
        # Handle Exasol's specific date literals
        converted_sql = self._convert_date_literals(converted_sql)
        
        # Handle Exasol's specific string literals
        converted_sql = self._convert_string_literals(converted_sql)
        
        return converted_sql
    
    def _convert_date_literals(self, sql: str) -> str:
        """
        Convert Exasol date literals to StarRocks format
        """
        # Convert Exasol date format to StarRocks
        # Exasol: DATE '2023-01-01' -> StarRocks: '2023-01-01'
        date_pattern = r"DATE\s+'([^']+)'"
        return re.sub(date_pattern, r"'\1'", sql, flags=re.IGNORECASE)
    
    def _convert_string_literals(self, sql: str) -> str:
        """
        Convert Exasol string literals to StarRocks format
        """
        # Handle any Exasol-specific string literal differences
        # For now, most string literals should work the same
        return sql
    
    def extract_variables(self, sql: str) -> List[str]:
        """
        Extract Metabase variables from SQL
        """
        variables = re.findall(r'\{\{([^}]+)\}\}', sql)
        return list(set(variables))  # Remove duplicates
    
    def validate_conversion(self, original_sql: str, converted_sql: str) -> Dict[str, any]:
        """
        Validate the SQL conversion and provide feedback
        """
        validation_result = {
            "success": True,
            "warnings": [],
            "errors": [],
            "variables_preserved": True,
            "tables_converted": 0,
            "functions_converted": 0
        }
        
        # Check if variables are preserved
        original_vars = self.extract_variables(original_sql)
        converted_vars = self.extract_variables(converted_sql)
        
        if set(original_vars) != set(converted_vars):
            validation_result["variables_preserved"] = False
            validation_result["warnings"].append("Some Metabase variables may have been modified")
        
        # Count table conversions
        for mapping in self.database_mappings:
            original_count = len(re.findall(
                rf'\b{mapping.exasol_schema}\.{mapping.exasol_table}\b',
                original_sql,
                flags=re.IGNORECASE
            ))
            if original_count > 0:
                validation_result["tables_converted"] += original_count
        
        # Count function conversions
        for exasol_func in self.function_mappings.keys():
            if exasol_func != "MEDIAN":  # Skip MEDIAN as it's handled specially
                count = len(re.findall(
                    rf'\b{re.escape(exasol_func)}\s*\(',
                    original_sql,
                    flags=re.IGNORECASE
                ))
                validation_result["functions_converted"] += count
        
        # Check for potential issues
        if "MEDIAN" in original_sql.upper():
            validation_result["warnings"].append("MEDIAN function conversion may need manual review")
        
        return validation_result

# Example usage and testing
def test_conversion():
    """
    Test the SQL converter with example queries
    """
    converter = SQLConverter()
    
    test_queries = [
        # Simple query with table reference
        """
        SELECT * FROM MART.TRANSACTIONS 
        WHERE created_date >= {{start_date}} 
        AND created_date <= {{end_date}}
        """,
        
        # Query with Exasol functions
        """
        SELECT 
            ADD_DAYS(created_date, 7) as future_date,
            DAYS_BETWEEN(created_date, CURRENT_DATE) as days_ago,
            MEDIAN(amount) as median_amount
        FROM MART.TRANSACTIONS
        WHERE amount > {{min_amount}}
        LIMIT 100 OFFSET 0
        """,
        
        # Complex query with multiple patterns
        """
        WITH daily_stats AS (
            SELECT 
                DATE(created_date) as date,
                COUNT(*) as count,
                SUM(amount) as total_amount
            FROM MART.TRANSACTIONS
            WHERE created_date >= {{start_date}}
            GROUP BY DATE(created_date)
        )
        SELECT * FROM daily_stats
        ORDER BY date DESC
        TOP 10
        """
    ]
    
    for i, query in enumerate(test_queries):
        print(f"\n--- Test Query {i+1} ---")
        print("Original:")
        print(query.strip())
        
        converted = converter.convert_sql(query)
        print("\nConverted:")
        print(converted.strip())
        
        validation = converter.validate_conversion(query, converted)
        print(f"\nValidation: {validation}")

if __name__ == "__main__":
    test_conversion() 