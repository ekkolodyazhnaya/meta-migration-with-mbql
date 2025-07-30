#!/usr/bin/env python3
"""
Script to check Metabase questions and verify their responses after migration
"""

import json
import requests
import time
from metabase_migrator import MetabaseMigrator, MetabaseConfig
from config import METABASE_CONFIG

def load_migration_results():
    """Load the migration results from file"""
    try:
        with open('dashboard_385_migration.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Migration results file not found.")
        return None

def check_question_response(question_id, question_name, migrator):
    """Check if a question returns a valid response"""
    print(f"  🔍 Checking Question {question_id}: {question_name}")
    
    # First, get the question details
    response = migrator.session.get(
        f"{migrator.config.base_url}/api/card/{question_id}",
        headers={"X-Metabase-Session": migrator.session_token}
    )
    
    if response.status_code != 200:
        print(f"    ❌ Failed to fetch question: {response.status_code}")
        return False
    
    question = response.json()
    dataset_query = question.get('dataset_query', {})
    database_id = dataset_query.get('database')
    query_type = dataset_query.get('type')
    
    print(f"    📊 Database ID: {database_id}")
    print(f"    📝 Query Type: {query_type}")
    
    # For native queries, show the SQL
    if query_type == 'native':
        native_query = dataset_query.get('native', {})
        sql = native_query.get('query', '')
        print(f"    🔍 SQL Preview: {sql[:100]}...")
    
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
            data = result.get('data', {})
            rows = data.get('rows', [])
            cols = data.get('cols', [])
            
            print(f"    ✅ Query executed successfully!")
            print(f"    📊 Rows returned: {len(rows)}")
            print(f"    📋 Columns: {len(cols)}")
            
            # Show column names
            column_names = [col.get('name', 'Unknown') for col in cols]
            print(f"    📝 Column names: {column_names}")
            
            # Show first few rows if any
            if rows:
                print(f"    📈 First row: {rows[0]}")
                if len(rows) > 1:
                    print(f"    📈 Second row: {rows[1]}")
            else:
                print(f"    ⚠️  No data returned")
            
            return True
            
        else:
            print(f"    ❌ Query execution failed: {query_response.status_code}")
            print(f"    📄 Error: {query_response.text}")
            return False
            
    except Exception as e:
        print(f"    ❌ Exception during query execution: {str(e)}")
        return False

def check_dashboard_questions(dashboard_id, migrator):
    """Check all questions in a dashboard"""
    print(f"🚀 Checking questions for Dashboard {dashboard_id}")
    print("=" * 60)
    
    # Load migration results
    migration_results = load_migration_results()
    if not migration_results:
        return
    
    # Find the dashboard
    dashboard_migration = None
    for dashboard in migration_results:
        if dashboard.get('dashboard_id') == dashboard_id:
            dashboard_migration = dashboard
            break
    
    if not dashboard_migration:
        print(f"❌ Dashboard {dashboard_id} not found in migration results")
        return
    
    questions = dashboard_migration.get('questions', [])
    print(f"📊 Found {len(questions)} questions to check")
    
    # Check each question
    success_count = 0
    total_count = 0
    
    for question in questions:
        question_id = question.get('question_id')
        question_name = question.get('question_name')
        question_type = question.get('type')
        
        total_count += 1
        print(f"\n📝 Question {total_count}/{len(questions)}")
        print("-" * 50)
        
        if check_question_response(question_id, question_name, migrator):
            success_count += 1
        
        # Add a small delay to avoid overwhelming the server
        time.sleep(1)
    
    print(f"\n🎉 Check Summary:")
    print(f"✅ Successfully checked: {success_count}/{total_count} questions")
    print(f"📊 Dashboard {dashboard_id} check completed!")

def check_specific_question(question_id, migrator):
    """Check a specific question by ID"""
    print(f"🔍 Checking specific question {question_id}")
    print("=" * 60)
    
    # Get question name first
    response = migrator.session.get(
        f"{migrator.config.base_url}/api/card/{question_id}",
        headers={"X-Metabase-Session": migrator.session_token}
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to fetch question: {response.status_code}")
        return
    
    question = response.json()
    question_name = question.get('name', 'Unknown')
    
    check_question_response(question_id, question_name, migrator)

def main():
    """Main function"""
    # Create configuration and authenticate
    config = MetabaseConfig(
        base_url=METABASE_CONFIG["base_url"],
        username=METABASE_CONFIG["username"],
        password=METABASE_CONFIG["password"]
    )
    
    migrator = MetabaseMigrator(config)
    
    if not migrator.authenticate():
        print("❌ Authentication failed")
        return
    
    print("✅ Authentication successful")
    
    # Check dashboard 385 questions
    check_dashboard_questions(385, migrator)
    
    # You can also check specific questions if needed
    # check_specific_question(3727, migrator)

if __name__ == "__main__":
    main() 