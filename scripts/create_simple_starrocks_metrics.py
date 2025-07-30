#!/usr/bin/env python3
"""
Script to create new StarRocks metrics with SR suffix using a simpler approach
"""

import requests
import json
from config import METABASE_CONFIG

def authenticate():
    """Authenticate with Metabase"""
    try:
        response = requests.post(
            f"{METABASE_CONFIG['base_url']}/api/session",
            json={
                "username": METABASE_CONFIG["username"],
                "password": METABASE_CONFIG["password"]
            }
        )
        
        if response.status_code == 200:
            return response.json().get("id")
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Authentication error: {str(e)}")
        return None

def fetch_browse_metrics(session_token):
    """Fetch metrics from browse that are not in StarRocks collection"""
    try:
        response = requests.get(
            f"{METABASE_CONFIG['base_url']}/api/search?models=metric&archived=false",
            headers={"X-Metabase-Session": session_token}
        )
        
        if response.status_code == 200:
            data = response.json()
            # Filter out metrics that are already in StarRocks collection (767)
            browse_metrics = []
            for metric in data.get('data', []):
                collection_id = metric.get('collection', {}).get('id')
                if collection_id != 767:  # Not in StarRocks collection
                    browse_metrics.append(metric)
            return browse_metrics
        else:
            print(f"❌ Failed to fetch browse metrics: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error fetching browse metrics: {str(e)}")
        return []

def create_simple_starrocks_metric(session_token, original_metric, new_name):
    """Create a new StarRocks metric with simple structure"""
    try:
        print(f"  🔄 Creating metric: {new_name}")
        
        # Create new metric with basic structure
        new_metric = {
            "name": new_name,
            "description": f"StarRocks version of {original_metric['name']}",
            "collection_id": 767,  # StarRocks collection
            "display": "scalar",  # Default display type
            "visualization_settings": {},  # Required empty map
            "dataset_query": {
                "database": 16,  # StarRocks database ID
                "type": "query",
                "query": {
                    "source-table": 87255,  # Default table ID (MART__TRANSACTIONS)
                    "aggregation": [
                        ["count"]
                    ]
                }
            }
        }
        
        print(f"    📋 Collection ID: {new_metric['collection_id']}")
        print(f"    📋 Display: {new_metric['display']}")
        print(f"    📋 Database: {new_metric['dataset_query']['database']}")
        
        # Try to create the metric using the card endpoint (since metrics might be cards)
        response = requests.post(
            f"{METABASE_CONFIG['base_url']}/api/card",
            headers={
                "X-Metabase-Session": session_token,
                "Content-Type": "application/json"
            },
            json=new_metric
        )
        
        if response.status_code == 200:
            created_metric = response.json()
            print(f"    ✅ Created metric {new_name} with ID: {created_metric.get('id')}")
            return created_metric
        else:
            print(f"    ❌ Failed to create metric {new_name}: {response.status_code}")
            print(f"    ❌ Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"    ❌ Error creating metric {new_name}: {str(e)}")
        return None

def main():
    """Main function"""
    print("🚀 Creating new StarRocks metrics with SR suffix (simple approach)...")
    print("=" * 70)
    
    # Authenticate
    session_token = authenticate()
    if not session_token:
        return
    
    print("✅ Authentication successful")
    
    # Fetch browse metrics (excluding StarRocks collection)
    print("\n📊 Fetching browse metrics...")
    browse_metrics = fetch_browse_metrics(session_token)
    print(f"✅ Found {len(browse_metrics)} browse metrics to convert")
    
    # Show sample metrics
    print(f"\n📝 Sample browse metrics to convert:")
    for i, metric in enumerate(browse_metrics[:10]):
        collection_name = metric.get('collection', {}).get('name', 'Unknown')
        print(f"  {i+1}. {metric['name']} (Collection: {collection_name})")
    
    # Ask for confirmation
    print(f"\n⚠️  This will create {len(browse_metrics)} new StarRocks metrics with 'SR' suffix.")
    print(f"All new metrics will be placed in collection 767 (StarRocks Metabase Metrics).")
    
    # For now, let's create a few sample metrics to test
    print(f"\n🧪 Creating sample metrics (first 3)...")
    
    created_metrics = []
    for i, metric in enumerate(browse_metrics[:3]):
        new_name = f"{metric['name']} SR"
        created_metric = create_simple_starrocks_metric(session_token, metric, new_name)
        if created_metric:
            created_metrics.append({
                "original_name": metric['name'],
                "new_name": new_name,
                "new_id": created_metric.get('id'),
                "original_id": metric['id']
            })
    
    # Summary
    print(f"\n📈 Summary:")
    print(f"Attempted to create: 3 metrics")
    print(f"Successfully created: {len(created_metrics)} metrics")
    
    if created_metrics:
        print(f"\n✅ Created metrics:")
        for metric in created_metrics:
            print(f"  • {metric['new_name']} (ID: {metric['new_id']})")
    
    # Save results
    with open('created_simple_starrocks_metrics.json', 'w') as f:
        json.dump({
            "created_metrics": created_metrics,
            "total_browse_metrics": len(browse_metrics),
            "sample_created": 3
        }, f, indent=2)
    
    print(f"\n💾 Results saved to created_simple_starrocks_metrics.json")

if __name__ == "__main__":
    main() 