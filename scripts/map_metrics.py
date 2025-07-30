#!/usr/bin/env python3
"""
Script to map metrics from StarRocks collection to main metrics browse page
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

def fetch_collection_items(session_token, collection_id):
    """Fetch items from a specific collection"""
    try:
        response = requests.get(
            f"{METABASE_CONFIG['base_url']}/api/collection/{collection_id}",
            headers={"X-Metabase-Session": session_token}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Failed to fetch collection {collection_id}: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error fetching collection {collection_id}: {str(e)}")
        return None

def fetch_metrics_from_browse(session_token):
    """Fetch metrics from the browse metrics page"""
    try:
        # Try different endpoints to get metrics
        endpoints = [
            "/api/metric",
            "/api/metrics", 
            "/api/collection/metrics",
            "/api/database/16/metrics",  # StarRocks database
            "/api/database/2/metrics"    # Exasol database
        ]
        
        for endpoint in endpoints:
            response = requests.get(
                f"{METABASE_CONFIG['base_url']}{endpoint}",
                headers={"X-Metabase-Session": session_token}
            )
            
            if response.status_code == 200:
                print(f"✅ Found metrics at endpoint: {endpoint}")
                return response.json()
        
        print("❌ No metrics found at any endpoint")
        return []
        
    except Exception as e:
        print(f"❌ Error fetching metrics: {str(e)}")
        return []

def analyze_metrics_structure(metrics_data):
    """Analyze the structure of metrics data"""
    if not metrics_data:
        return {}
    
    analysis = {
        "total_count": len(metrics_data),
        "sample_structure": metrics_data[0] if metrics_data else {},
        "field_names": list(metrics_data[0].keys()) if metrics_data else []
    }
    
    return analysis

def create_metric_mapping(starrocks_metrics, browse_metrics):
    """Create mapping between StarRocks metrics and browse metrics"""
    mapping = {
        "starrocks_metrics": [],
        "browse_metrics": [],
        "suggested_mappings": []
    }
    
    # Process StarRocks metrics
    if starrocks_metrics and 'items' in starrocks_metrics:
        for item in starrocks_metrics['items']:
            if item.get('model') == 'metric':
                mapping["starrocks_metrics"].append({
                    "id": item.get('id'),
                    "name": item.get('name'),
                    "description": item.get('description'),
                    "table": item.get('table', {}).get('name') if item.get('table') else None
                })
    
    # Process browse metrics
    for metric in browse_metrics:
        mapping["browse_metrics"].append({
            "id": metric.get('id'),
            "name": metric.get('name'),
            "description": metric.get('description'),
            "table": metric.get('table', {}).get('name') if metric.get('table') else None,
            "database": metric.get('table', {}).get('db', {}).get('name') if metric.get('table') else None
        })
    
    # Suggest mappings based on name similarity
    for sr_metric in mapping["starrocks_metrics"]:
        best_match = None
        best_score = 0
        
        for browse_metric in mapping["browse_metrics"]:
            # Simple name matching
            sr_name = sr_metric['name'].lower()
            browse_name = browse_metric['name'].lower()
            
            # Check for exact match
            if sr_name == browse_name:
                score = 100
            # Check for partial match
            elif sr_name in browse_name or browse_name in sr_name:
                score = 80
            # Check for common words
            elif any(word in browse_name for word in sr_name.split()) or any(word in sr_name for word in browse_name.split()):
                score = 60
            else:
                score = 0
            
            if score > best_score:
                best_score = score
                best_match = browse_metric
        
        if best_match and best_score > 50:
            mapping["suggested_mappings"].append({
                "starrocks_metric": sr_metric,
                "browse_metric": best_match,
                "confidence_score": best_score
            })
    
    return mapping

def main():
    """Main function"""
    print("🔍 Mapping StarRocks metrics to browse metrics...")
    print("=" * 60)
    
    # Authenticate
    session_token = authenticate()
    if not session_token:
        return
    
    print("✅ Authentication successful")
    
    # Fetch StarRocks collection (ID: 767)
    print("\n📊 Fetching StarRocks collection (ID: 767)...")
    starrocks_collection = fetch_collection_items(session_token, 767)
    
    if not starrocks_collection:
        print("❌ Failed to fetch StarRocks collection")
        return
    
    print(f"✅ Found StarRocks collection: {starrocks_collection.get('name', 'Unknown')}")
    print(f"📋 Items in collection: {len(starrocks_collection.get('items', []))}")
    
    # Fetch browse metrics
    print("\n📊 Fetching browse metrics...")
    browse_metrics = fetch_metrics_from_browse(session_token)
    
    if not browse_metrics:
        print("❌ Failed to fetch browse metrics")
        return
    
    print(f"✅ Found {len(browse_metrics)} browse metrics")
    
    # Analyze structures
    print("\n🔍 Analyzing metric structures...")
    starrocks_analysis = analyze_metrics_structure(starrocks_collection.get('items', []))
    browse_analysis = analyze_metrics_structure(browse_metrics)
    
    print(f"StarRocks metrics structure: {starrocks_analysis}")
    print(f"Browse metrics structure: {browse_analysis}")
    
    # Create mapping
    print("\n🔄 Creating metric mappings...")
    mapping = create_metric_mapping(starrocks_collection, browse_metrics)
    
    # Print results
    print(f"\n📈 Mapping Results:")
    print(f"StarRocks metrics: {len(mapping['starrocks_metrics'])}")
    print(f"Browse metrics: {len(mapping['browse_metrics'])}")
    print(f"Suggested mappings: {len(mapping['suggested_mappings'])}")
    
    # Show sample mappings
    if mapping["suggested_mappings"]:
        print(f"\n🎯 Sample Suggested Mappings:")
        for i, mapping_item in enumerate(mapping["suggested_mappings"][:5]):
            sr_metric = mapping_item["starrocks_metric"]
            browse_metric = mapping_item["browse_metric"]
            score = mapping_item["confidence_score"]
            
            print(f"  {i+1}. {sr_metric['name']} (SR) → {browse_metric['name']} (Browse)")
            print(f"     Confidence: {score}%")
            print(f"     SR Table: {sr_metric.get('table', 'Unknown')}")
            print(f"     Browse Table: {browse_metric.get('table', 'Unknown')}")
            print(f"     Browse DB: {browse_metric.get('database', 'Unknown')}")
    
    # Save mapping
    with open('metric_mapping.json', 'w') as f:
        json.dump(mapping, f, indent=2)
    
    print(f"\n💾 Metric mapping saved to metric_mapping.json")

if __name__ == "__main__":
    main() 