#!/usr/bin/env python3
"""
Script to fetch and analyze metrics from Metabase
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

def fetch_metrics(session_token):
    """Fetch all metrics from Metabase"""
    try:
        response = requests.get(
            f"{METABASE_CONFIG['base_url']}/api/metric",
            headers={"X-Metabase-Session": session_token}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Failed to fetch metrics: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error fetching metrics: {str(e)}")
        return []

def analyze_metrics(metrics):
    """Analyze metrics structure and group by database"""
    analysis = {
        "total_metrics": len(metrics),
        "by_database": {},
        "exasol_metrics": [],
        "starrocks_metrics": []
    }
    
    for metric in metrics:
        db_id = metric.get('table', {}).get('db_id')
        db_name = metric.get('table', {}).get('db', {}).get('name', 'Unknown')
        
        if db_id not in analysis["by_database"]:
            analysis["by_database"][db_id] = {
                "name": db_name,
                "count": 0,
                "metrics": []
            }
        
        analysis["by_database"][db_id]["count"] += 1
        analysis["by_database"][db_id]["metrics"].append(metric)
        
        # Group by database name for easier identification
        if "exasol" in db_name.lower():
            analysis["exasol_metrics"].append(metric)
        elif "starrocks" in db_name.lower() or "sr_" in db_name.lower():
            analysis["starrocks_metrics"].append(metric)
    
    return analysis

def main():
    """Main function"""
    print("🔍 Fetching and analyzing metrics from Metabase...")
    print("=" * 60)
    
    # Authenticate
    session_token = authenticate()
    if not session_token:
        return
    
    print("✅ Authentication successful")
    
    # Fetch metrics
    metrics = fetch_metrics(session_token)
    if not metrics:
        print("❌ No metrics found")
        return
    
    print(f"📊 Found {len(metrics)} metrics")
    
    # Analyze metrics
    analysis = analyze_metrics(metrics)
    
    # Print analysis
    print(f"\n📈 Metrics Analysis:")
    print(f"Total metrics: {analysis['total_metrics']}")
    print(f"Exasol metrics: {len(analysis['exasol_metrics'])}")
    print(f"StarRocks metrics: {len(analysis['starrocks_metrics'])}")
    
    print(f"\n📋 By Database:")
    for db_id, db_info in analysis["by_database"].items():
        print(f"  Database {db_id} ({db_info['name']}): {db_info['count']} metrics")
    
    # Show sample Exasol metrics
    if analysis["exasol_metrics"]:
        print(f"\n📝 Sample Exasol Metrics:")
        for i, metric in enumerate(analysis["exasol_metrics"][:5]):
            print(f"  {i+1}. {metric.get('name', 'Unknown')} (ID: {metric.get('id')})")
            print(f"     Table: {metric.get('table', {}).get('name', 'Unknown')}")
            print(f"     Definition: {metric.get('definition', {}).get('aggregation', 'Unknown')}")
    
    # Save detailed analysis
    with open('metrics_analysis.json', 'w') as f:
        json.dump(analysis, f, indent=2)
    
    print(f"\n💾 Detailed analysis saved to metrics_analysis.json")

if __name__ == "__main__":
    main() 