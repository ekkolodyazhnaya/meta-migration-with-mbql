#!/usr/bin/env python3
"""
Test script for SQL converter functionality
"""

from sql_converter import SQLConverter
import json

def test_sql_converter():
    """Test the SQL converter with various Exasol queries"""
    
    converter = SQLConverter()
    
    test_cases = [
        {
            "name": "Simple table reference",
            "original": """
            SELECT * FROM MART.TRANSACTIONS 
            WHERE created_date >= {{start_date}}
            """,
            "expected_tables": ["MART.TRANSACTIONS"],
            "expected_variables": ["start_date"]
        },
        {
            "name": "Exasol functions",
            "original": """
            SELECT 
                ADD_DAYS(created_date, 7) as future_date,
                DAYS_BETWEEN(created_date, CURRENT_DATE) as days_ago,
                MEDIAN(amount) as median_amount,
                INSTR(description, 'test') as test_pos
            FROM MART.TRANSACTIONS
            WHERE amount > {{min_amount}}
            """,
            "expected_functions": ["ADD_DAYS", "DAYS_BETWEEN", "MEDIAN", "INSTR"],
            "expected_variables": ["min_amount"]
        },
        {
            "name": "LIMIT OFFSET syntax",
            "original": """
            SELECT * FROM MART.TRANSACTIONS
            ORDER BY created_date DESC
            LIMIT 100 OFFSET 0
            """,
            "expected_syntax": "LIMIT OFFSET"
        },
        {
            "name": "TOP syntax",
            "original": """
            SELECT TOP 10 * FROM MART.TRANSACTIONS
            ORDER BY amount DESC
            """,
            "expected_syntax": "TOP"
        },
        {
            "name": "Complex query with CTE",
            "original": """
            WITH daily_stats AS (
                SELECT 
                    DATE(created_date) as date,
                    COUNT(*) as count,
                    SUM(amount) as total_amount,
                    MEDIAN(amount) as median_amount
                FROM MART.TRANSACTIONS
                WHERE created_date >= {{start_date}}
                AND created_date <= {{end_date}}
                GROUP BY DATE(created_date)
            )
            SELECT * FROM daily_stats
            ORDER BY date DESC
            LIMIT 50 OFFSET 10
            """,
            "expected_variables": ["start_date", "end_date"],
            "expected_functions": ["MEDIAN"]
        }
    ]
    
    print("🧪 Testing SQL Converter")
    print("=" * 50)
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test_case['name']}")
        print("-" * 30)
        
        # Convert SQL
        converted = converter.convert_sql(test_case['original'])
        
        # Validate conversion
        validation = converter.validate_conversion(test_case['original'], converted)
        
        # Check results
        passed = True
        
        # Check variables
        if 'expected_variables' in test_case:
            actual_vars = converter.extract_variables(converted)
            expected_vars = test_case['expected_variables']
            if set(actual_vars) != set(expected_vars):
                print(f"❌ Variables mismatch: expected {expected_vars}, got {actual_vars}")
                passed = False
            else:
                print(f"✅ Variables preserved: {actual_vars}")
        
        # Check validation
        if not validation['success']:
            print(f"❌ Validation failed: {validation['errors']}")
            passed = False
        else:
            print(f"✅ Validation passed")
        
        # Show conversion
        print(f"\n📄 Original SQL:")
        print(test_case['original'].strip())
        
        print(f"\n🔄 Converted SQL:")
        print(converted.strip())
        
        if passed:
            print(f"\n✅ Test {i} PASSED")
        else:
            print(f"\n❌ Test {i} FAILED")
            all_passed = False
        
        print("-" * 50)
    
    # Summary
    print(f"\n📊 Test Summary")
    print("=" * 50)
    if all_passed:
        print("🎉 All tests PASSED!")
    else:
        print("❌ Some tests FAILED")
    
    return all_passed

def test_database_mappings():
    """Test database mapping functionality"""
    
    converter = SQLConverter()
    
    print("\n🗺️  Testing Database Mappings")
    print("=" * 50)
    
    mapping_tests = [
        "SELECT * FROM MART.TRANSACTIONS",
        "SELECT * FROM EXASOL.MART.TRANSACTIONS",
        "SELECT t.* FROM MART.TRANSACTIONS t",
        "SELECT * FROM MART.TRANSACTIONS WHERE id > 0"
    ]
    
    for test_sql in mapping_tests:
        print(f"\n📝 Testing: {test_sql}")
        converted = converter.convert_sql(test_sql)
        print(f"🔄 Result: {converted}")
        
        # Check if MART.TRANSACTIONS was converted to sr_mart.transactions
        if "sr_mart.transactions" in converted.lower():
            print("✅ Table mapping successful")
        else:
            print("❌ Table mapping failed")

if __name__ == "__main__":
    # Run tests
    sql_tests_passed = test_sql_converter()
    test_database_mappings()
    
    print(f"\n🎯 Overall Result: {'PASSED' if sql_tests_passed else 'FAILED'}") 