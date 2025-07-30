#!/usr/bin/env python3
"""
Simple script to run the Metabase migration
"""

import sys
import os
from metabase_migrator import MetabaseMigrator, MetabaseConfig
from config import METABASE_CONFIG

def main():
    """Run the migration with user-friendly output"""
    
    print("🚀 Metabase Migration Tool")
    print("=" * 40)
    print("Migrating from Exasol to StarRocks")
    print()
    
    # Check if we can import required modules
    try:
        import requests
        import json
        import re
    except ImportError as e:
        print(f"❌ Missing required module: {e}")
        print("Please install dependencies with: pip install -r requirements.txt")
        sys.exit(1)
    
    # Create configuration
    try:
        config = MetabaseConfig(
            base_url=METABASE_CONFIG["base_url"],
            username=METABASE_CONFIG["username"],
            password=METABASE_CONFIG["password"]
        )
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        print("Please check your config.py file")
        sys.exit(1)
    
    # Create migrator
    try:
        migrator = MetabaseMigrator(config)
        print("✅ Migration tool initialized")
    except Exception as e:
        print(f"❌ Failed to initialize migration tool: {e}")
        sys.exit(1)
    
    # Test authentication
    print("\n🔐 Testing authentication...")
    if not migrator.authenticate():
        print("❌ Authentication failed")
        print("Please check your credentials in config.py")
        sys.exit(1)
    
    print("✅ Authentication successful")
    
    # Get dashboards
    print("\n📊 Fetching dashboards...")
    dashboards = migrator.get_dashboards()
    
    if not dashboards:
        print("❌ No dashboards found")
        print("Please check your Metabase permissions")
        sys.exit(1)
    
    print(f"✅ Found {len(dashboards)} dashboards")
    
    # Confirm before proceeding
    print(f"\n⚠️  About to migrate {len(dashboards)} dashboards")
    response = input("Continue? (y/N): ").strip().lower()
    
    if response not in ['y', 'yes']:
        print("Migration cancelled")
        sys.exit(0)
    
    # Run migration
    print("\n🔄 Starting migration...")
    try:
        results = migrator.migrate_all_dashboards()
        
        # Generate summary
        summary = migrator.generate_summary_report(results)
        
        # Save results
        migrator.save_migration_results(results)
        
        # Display results
        print("\n📊 Migration Results")
        print("=" * 40)
        print(f"📈 Total Dashboards: {summary['total_dashboards']}")
        print(f"❓ Total Questions: {summary['total_questions']}")
        print(f"📝 Native Questions: {summary['native_questions']}")
        print(f"🔧 MBQL Questions: {summary['mbql_questions']}")
        print(f"✅ Successful Conversions: {summary['successful_conversions']}")
        print(f"❌ Failed Conversions: {summary['failed_conversions']}")
        
        if summary["warnings"]:
            print(f"\n⚠️  Warnings ({len(summary['warnings'])}):")
            for warning in summary["warnings"][:3]:
                print(f"   • {warning}")
            if len(summary["warnings"]) > 3:
                print(f"   ... and {len(summary['warnings']) - 3} more")
        
        if summary["errors"]:
            print(f"\n❌ Errors ({len(summary['errors'])}):")
            for error in summary["errors"][:3]:
                print(f"   • {error}")
            if len(summary["errors"]) > 3:
                print(f"   ... and {len(summary['errors']) - 3} more")
        
        print(f"\n📄 Detailed results saved to migration_results.json")
        
        if summary['failed_conversions'] == 0:
            print("🎉 Migration completed successfully!")
        else:
            print("⚠️  Migration completed with some errors. Please review the results.")
        
    except KeyboardInterrupt:
        print("\n⏹️  Migration interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 