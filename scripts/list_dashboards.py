#!/usr/bin/env python3
"""
Script to list all available dashboards
"""

from metabase_migrator import MetabaseMigrator, MetabaseConfig
from config import METABASE_CONFIG

def list_dashboards():
    """List all available dashboards"""
    
    print("📋 Listing All Dashboards")
    print("=" * 50)
    
    # Create configuration
    config = MetabaseConfig(
        base_url=METABASE_CONFIG["base_url"],
        username=METABASE_CONFIG["username"],
        password=METABASE_CONFIG["password"]
    )
    
    # Create migrator
    migrator = MetabaseMigrator(config)
    
    # Authenticate
    if not migrator.authenticate():
        print("❌ Authentication failed")
        return
    
    # Get all dashboards
    dashboards = migrator.get_dashboards()
    
    if not dashboards:
        print("❌ No dashboards found")
        return
    
    print(f"📊 Found {len(dashboards)} dashboards")
    print()
    
    # Sort by question count (we'll need to check each dashboard)
    dashboard_info = []
    
    for dashboard in dashboards:
        dashboard_id = dashboard.get('id')
        dashboard_name = dashboard.get('name', 'Unknown')
        
        # Get dashboard details to count questions
        dashboard_details = migrator.get_dashboard_details(dashboard_id)
        if dashboard_details:
            dashcards = dashboard_details.get('dashcards', [])
            question_count = len(dashcards)
        else:
            question_count = 0
        
        dashboard_info.append({
            'id': dashboard_id,
            'name': dashboard_name,
            'question_count': question_count
        })
    
    # Sort by question count (descending)
    dashboard_info.sort(key=lambda x: x['question_count'], reverse=True)
    
    # Display dashboards
    for i, info in enumerate(dashboard_info, 1):
        question_count = info['question_count']
        status = "🟢" if question_count > 0 else "🔴"
        print(f"{status} {i:2d}. ID: {info['id']:3d} | Questions: {question_count:2d} | {info['name']}")
    
    # Show summary
    dashboards_with_questions = sum(1 for d in dashboard_info if d['question_count'] > 0)
    total_questions = sum(d['question_count'] for d in dashboard_info)
    
    print(f"\n📊 Summary:")
    print(f"   📈 Total Dashboards: {len(dashboard_info)}")
    print(f"   ✅ Dashboards with Questions: {dashboards_with_questions}")
    print(f"   ❌ Empty Dashboards: {len(dashboard_info) - dashboards_with_questions}")
    print(f"   📝 Total Questions: {total_questions}")
    
    # Suggest dashboards to migrate
    if dashboards_with_questions > 0:
        print(f"\n💡 Suggested dashboards to migrate:")
        for info in dashboard_info[:5]:  # Top 5 with most questions
            if info['question_count'] > 0:
                print(f"   • ID {info['id']}: {info['name']} ({info['question_count']} questions)")

if __name__ == "__main__":
    list_dashboards() 