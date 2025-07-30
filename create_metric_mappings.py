#!/usr/bin/env python3
"""
Script to create metric mappings and generate new StarRocks metrics with SR suffix
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

def fetch_starrocks_metrics(session_token):
    """Fetch metrics from StarRocks collection (ID: 767)"""
    try:
        response = requests.get(
            f"{METABASE_CONFIG['base_url']}/api/collection/767/items",
            headers={"X-Metabase-Session": session_token}
        )
        
        if response.status_code == 200:
            data = response.json()
            return [item for item in data.get('data', []) if item.get('model') == 'metric']
        else:
            print(f"❌ Failed to fetch StarRocks metrics: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error fetching StarRocks metrics: {str(e)}")
        return []

def fetch_all_metrics(session_token):
    """Fetch all metrics from search endpoint"""
    try:
        response = requests.get(
            f"{METABASE_CONFIG['base_url']}/api/search?models=metric",
            headers={"X-Metabase-Session": session_token}
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get('data', [])
        else:
            print(f"❌ Failed to fetch all metrics: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error fetching all metrics: {str(e)}")
        return []

def get_metric_details(session_token, metric_id):
    """Get detailed information about a specific metric"""
    try:
        response = requests.get(
            f"{METABASE_CONFIG['base_url']}/api/metric/{metric_id}",
            headers={"X-Metabase-Session": session_token}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Failed to fetch metric {metric_id}: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error fetching metric {metric_id}: {str(e)}")
        return None

def create_metric_mapping(starrocks_metrics, all_metrics):
    """Create mapping between StarRocks metrics and all metrics"""
    mapping = {
        "starrocks_metrics": [],
        "all_metrics": [],
        "suggested_mappings": [],
        "unmapped_starrocks": []
    }
    
    # Process StarRocks metrics
    for metric in starrocks_metrics:
        mapping["starrocks_metrics"].append({
            "id": metric.get('id'),
            "name": metric.get('name'),
            "description": metric.get('description'),
            "collection": metric.get('collection_id'),
            "display": metric.get('display')
        })
    
    # Process all metrics
    for metric in all_metrics:
        mapping["all_metrics"].append({
            "id": metric.get('id'),
            "name": metric.get('name'),
            "description": metric.get('description'),
            "collection": metric.get('collection', {}).get('id'),
            "collection_name": metric.get('collection', {}).get('name'),
            "display": metric.get('display')
        })
    
    # Find mappings
    for sr_metric in mapping["starrocks_metrics"]:
        best_match = None
        best_score = 0
        
        for all_metric in mapping["all_metrics"]:
            # Skip if it's already a StarRocks metric
            if all_metric.get('collection') == 767:
                continue
                
            # Simple name matching
            sr_name = sr_metric['name'].lower()
            all_name = all_metric['name'].lower()
            
            # Check for exact match
            if sr_name == all_name:
                score = 100
            # Check for partial match
            elif sr_name in all_name or all_name in sr_name:
                score = 80
            # Check for common words
            elif any(word in all_name for word in sr_name.split()) or any(word in sr_name for word in all_name.split()):
                score = 60
            else:
                score = 0
            
            if score > best_score:
                best_score = score
                best_match = all_metric
        
        if best_match and best_score > 50:
            mapping["suggested_mappings"].append({
                "starrocks_metric": sr_metric,
                "browse_metric": best_match,
                "confidence_score": best_score
            })
        else:
            mapping["unmapped_starrocks"].append(sr_metric)
    
    return mapping

def create_new_starrocks_metric(session_token, original_metric, new_name):
    """Create a new StarRocks metric based on an existing one"""
    try:
        # Get the original metric details
        metric_details = get_metric_details(session_token, original_metric['id'])
        if not metric_details:
            return None
        
        # Create new metric definition
        new_metric = {
            "name": new_name,
            "description": f"StarRocks version of {original_metric['name']}",
            "table_id": metric_details.get('table_id'),
            "definition": metric_details.get('definition'),
            "collection_id": 767  # StarRocks collection
        }
        
        # Create the new metric
        response = requests.post(
            f"{METABASE_CONFIG['base_url']}/api/metric",
            headers={
                "X-Metabase-Session": session_token,
                "Content-Type": "application/json"
            },
            json=new_metric
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Failed to create metric {new_name}: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error creating metric {new_name}: {str(e)}")
        return None

def main():
    """Main function"""
    print("🔍 Creating metric mappings and generating StarRocks metrics...")
    print("=" * 70)
    
    # Authenticate
    session_token = authenticate()
    if not session_token:
        return
    
    print("✅ Authentication successful")
    
    # Fetch StarRocks metrics
    print("\n📊 Fetching StarRocks metrics from collection 767...")
    starrocks_metrics = fetch_starrocks_metrics(session_token)
    print(f"✅ Found {len(starrocks_metrics)} StarRocks metrics")
    
    # Fetch all metrics
    print("\n📊 Fetching all metrics from search...")
    all_metrics = fetch_all_metrics(session_token)
    print(f"✅ Found {len(all_metrics)} total metrics")
    
    # Create mapping
    print("\n🔄 Creating metric mappings...")
    mapping = create_metric_mapping(starrocks_metrics, all_metrics)
    
    # Print results
    print(f"\n📈 Mapping Results:")
    print(f"StarRocks metrics: {len(mapping['starrocks_metrics'])}")
    print(f"All metrics: {len(mapping['all_metrics'])}")
    print(f"Suggested mappings: {len(mapping['suggested_mappings'])}")
    print(f"Unmapped StarRocks: {len(mapping['unmapped_starrocks'])}")
    
    # Show sample mappings
    if mapping["suggested_mappings"]:
        print(f"\n🎯 Sample Suggested Mappings:")
        for i, mapping_item in enumerate(mapping["suggested_mappings"][:5]):
            sr_metric = mapping_item["starrocks_metric"]
            browse_metric = mapping_item["browse_metric"]
            score = mapping_item["confidence_score"]
            
            print(f"  {i+1}. {sr_metric['name']} (SR) → {browse_metric['name']} (Browse)")
            print(f"     Confidence: {score}%")
            print(f"     Browse Collection: {browse_metric.get('collection_name', 'Unknown')}")
    
    # Show unmapped StarRocks metrics
    if mapping["unmapped_starrocks"]:
        print(f"\n❓ Unmapped StarRocks Metrics:")
        for i, metric in enumerate(mapping["unmapped_starrocks"][:5]):
            print(f"  {i+1}. {metric['name']} (ID: {metric['id']})")
    
    # Save mapping
    with open('metric_mapping_analysis.json', 'w') as f:
        json.dump(mapping, f, indent=2)
    
    print(f"\n💾 Metric mapping analysis saved to metric_mapping_analysis.json")
    
    # Ask user if they want to create new StarRocks metrics
    print(f"\n🚀 Ready to create new StarRocks metrics with 'SR' suffix!")
    print(f"This will create new metrics in collection 767 based on the mappings.")
    
    # For now, just show what would be created
    print(f"\n📝 Would create these new StarRocks metrics:")
    for mapping_item in mapping["suggested_mappings"][:10]:  # Show first 10
        browse_metric = mapping_item["browse_metric"]
        new_name = f"{browse_metric['name']} SR"
        print(f"  • {new_name} (based on {browse_metric['name']})")

if __name__ == "__main__":
    main() 