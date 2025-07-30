#!/usr/bin/env python3
"""
Script to migrate a single specific dashboard
"""

import sys
import json
from metabase_migrator import MetabaseMigrator, MetabaseConfig
from config import METABASE_CONFIG

def migrate_single_dashboard(dashboard_id: int, dashboard_name: str = None):
    """Migrate a single dashboard by ID"""
    
    print(f"🚀 Migrating Single Dashboard")
    print("=" * 50)
    print(f"Dashboard ID: {dashboard_id}")
    if dashboard_name:
        print(f"Dashboard Name: {dashboard_name}")
    print()
    
    # Create configuration
    try:
        config = MetabaseConfig(
            base_url=METABASE_CONFIG["base_url"],
            username=METABASE_CONFIG["username"],
            password=METABASE_CONFIG["password"]
        )
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return None
    
    # Create migrator
    try:
        migrator = MetabaseMigrator(config)
        print("✅ Migration tool initialized")
    except Exception as e:
        print(f"❌ Failed to initialize migration tool: {e}")
        return None
    
    # Test authentication
    print("\n🔐 Testing authentication...")
    if not migrator.authenticate():
        print("❌ Authentication failed")
        return None
    
    print("✅ Authentication successful")
    
    # Get specific dashboard
    print(f"\n📊 Fetching dashboard {dashboard_id}...")
    dashboard_details = migrator.get_dashboard_details(dashboard_id)
    
    if not dashboard_details:
        print(f"❌ Dashboard {dashboard_id} not found or no access")
        return None
    
    dashboard_name = dashboard_details.get('name', 'Unknown')
    print(f"✅ Found dashboard: {dashboard_name}")
    
    # Create a mock dashboard object for the migrator
    dashboard = {
        'id': dashboard_id,
        'name': dashboard_name
    }
    
    # Run migration for single dashboard
    print(f"\n🔄 Starting migration for dashboard: {dashboard_name}")
    try:
        result = migrator.migrate_dashboard(dashboard)
        
        # Save results
        filename = f"dashboard_{dashboard_id}_migration.json"
        migrator.save_migration_results([result], filename)
        
        # Display results
        print("\n📊 Migration Results")
        print("=" * 50)
        print(f"📈 Dashboard: {result.get('dashboard_name', 'Unknown')}")
        print(f"❓ Total Questions: {result.get('total_questions', 0)}")
        
        questions = result.get('questions', [])
        successful = 0
        failed = 0
        
        for i, question in enumerate(questions, 1):
            if "error" in question:
                failed += 1
                print(f"   ❌ Question {i}: {question.get('question_name', 'Unknown')} - {question['error']}")
            else:
                successful += 1
                question_type = question.get('type', 'unknown')
                print(f"   ✅ Question {i}: {question.get('question_name', 'Unknown')} ({question_type})")
                
                if question_type == 'native':
                    variables = question.get('variables', [])
                    if variables:
                        print(f"      Variables: {', '.join(variables)}")
                    
                    validation = question.get('validation', {})
                    if validation.get('warnings'):
                        print(f"      ⚠️  Warnings: {', '.join(validation['warnings'])}")
        
        print(f"\n📊 Summary:")
        print(f"   ✅ Successful: {successful}")
        print(f"   ❌ Failed: {failed}")
        
        print(f"\n📄 Detailed results saved to {filename}")
        
        if failed == 0:
            print("🎉 Migration completed successfully!")
        else:
            print("⚠️  Migration completed with some errors. Please review the results.")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        return None

def main():
    """Main function"""
    dashboard_id = 385
    dashboard_name = "OOR Transaction Amount Statistics chart - Duplicate"
    
    result = migrate_single_dashboard(dashboard_id, dashboard_name)
    
    if result:
        print(f"\n🎯 Migration completed for dashboard {dashboard_id}")
    else:
        print(f"\n❌ Migration failed for dashboard {dashboard_id}")
        sys.exit(1)

if __name__ == "__main__":
    main() 