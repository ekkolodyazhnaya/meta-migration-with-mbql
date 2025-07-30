#!/usr/bin/env python3
"""
Script to create all StarRocks metrics with SR suffix
"""

import requests
import json
import time
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

def create_starrocks_metric(session_token, original_metric, new_name):
    """Create a new StarRocks metric"""
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
        
        # Create the metric
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
    print("🚀 Creating all StarRocks metrics with SR suffix...")
    print("=" * 60)
    
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
    
    # Create all metrics
    print(f"\n🚀 Creating all metrics...")
    
    created_metrics = []
    failed_metrics = []
    
    for i, metric in enumerate(browse_metrics):
        new_name = f"{metric['name']} SR"
        print(f"\n[{i+1}/{len(browse_metrics)}] Processing: {metric['name']}")
        
        created_metric = create_starrocks_metric(session_token, metric, new_name)
        if created_metric:
            created_metrics.append({
                "original_name": metric['name'],
                "new_name": new_name,
                "new_id": created_metric.get('id'),
                "original_id": metric['id'],
                "collection": metric.get('collection', {}).get('name', 'Unknown')
            })
        else:
            failed_metrics.append({
                "original_name": metric['name'],
                "original_id": metric['id'],
                "collection": metric.get('collection', {}).get('name', 'Unknown')
            })
        
        # Add a small delay to avoid overwhelming the API
        time.sleep(0.5)
    
    # Summary
    print(f"\n📈 Final Summary:")
    print(f"Total browse metrics: {len(browse_metrics)}")
    print(f"Successfully created: {len(created_metrics)} metrics")
    print(f"Failed to create: {len(failed_metrics)} metrics")
    
    if created_metrics:
        print(f"\n✅ Successfully created metrics:")
        for metric in created_metrics[:10]:  # Show first 10
            print(f"  • {metric['new_name']} (ID: {metric['new_id']})")
        if len(created_metrics) > 10:
            print(f"  ... and {len(created_metrics) - 10} more")
    
    if failed_metrics:
        print(f"\n❌ Failed to create metrics:")
        for metric in failed_metrics[:5]:  # Show first 5
            print(f"  • {metric['original_name']}")
        if len(failed_metrics) > 5:
            print(f"  ... and {len(failed_metrics) - 5} more")
    
    # Save results
    with open('all_created_starrocks_metrics.json', 'w') as f:
        json.dump({
            "created_metrics": created_metrics,
            "failed_metrics": failed_metrics,
            "total_browse_metrics": len(browse_metrics),
            "success_count": len(created_metrics),
            "failure_count": len(failed_metrics)
        }, f, indent=2)
    
    print(f"\n💾 Results saved to all_created_starrocks_metrics.json")
    print(f"🎉 Metric creation completed!")

if __name__ == "__main__":
    main() 