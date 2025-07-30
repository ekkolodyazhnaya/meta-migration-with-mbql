#!/usr/bin/env python3
"""
Script to replace Exasol-based metrics in dashboard 500 with StarRocks metrics
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

def get_dashboard_details(session_token, dashboard_id):
    """Get detailed information about a dashboard"""
    try:
        response = requests.get(
            f"{METABASE_CONFIG['base_url']}/api/dashboard/{dashboard_id}",
            headers={"X-Metabase-Session": session_token}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Failed to fetch dashboard {dashboard_id}: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error fetching dashboard {dashboard_id}: {str(e)}")
        return None

def get_starrocks_metrics(session_token):
    """Get all StarRocks metrics (cards) from collection 767"""
    try:
        response = requests.get(
            f"{METABASE_CONFIG['base_url']}/api/collection/767/items",
            headers={"X-Metabase-Session": session_token}
        )
        
        if response.status_code == 200:
            data = response.json()
            return [item for item in data.get('data', []) if item.get('model') == 'card']
        else:
            print(f"❌ Failed to fetch StarRocks metrics: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error fetching StarRocks metrics: {str(e)}")
        return []

def find_metric_mapping(original_metric_name, starrocks_metrics):
    """Find the corresponding StarRocks metric for an original metric name"""
    # Remove "SR" suffix if present and try to match
    base_name = original_metric_name.replace(" SR", "")
    
    for sr_metric in starrocks_metrics:
        sr_name = sr_metric.get('name', '')
        # Check if the StarRocks metric name contains the original name
        if base_name.lower() in sr_name.lower() or sr_name.lower() in base_name.lower():
            return sr_metric
    
    return None

def update_dashboard_card(session_token, card_id, new_metric_id):
    """Update a dashboard card to use a new metric"""
    try:
        # Get the current card details
        response = requests.get(
            f"{METABASE_CONFIG['base_url']}/api/card/{card_id}",
            headers={"X-Metabase-Session": session_token}
        )
        
        if response.status_code != 200:
            print(f"    ❌ Failed to fetch card {card_id}: {response.status_code}")
            return False
        
        card_data = response.json()
        
        # Update the card to use the new metric
        # This is a simplified approach - you might need to adjust based on the actual card structure
        card_data['dataset_query'] = {
            "database": 16,  # StarRocks database
            "type": "query",
            "query": {
                "source-table": 87255,  # Default table
                "aggregation": [
                    ["metric", new_metric_id]
                ]
            }
        }
        
        # Update the card
        update_response = requests.put(
            f"{METABASE_CONFIG['base_url']}/api/card/{card_id}",
            headers={
                "X-Metabase-Session": session_token,
                "Content-Type": "application/json"
            },
            json=card_data
        )
        
        if update_response.status_code == 200:
            print(f"    ✅ Updated card {card_id} to use metric {new_metric_id}")
            return True
        else:
            print(f"    ❌ Failed to update card {card_id}: {update_response.status_code}")
            return False
            
    except Exception as e:
        print(f"    ❌ Error updating card {card_id}: {str(e)}")
        return False

def main():
    """Main function"""
    dashboard_id = 500
    
    print(f"🔄 Replacing Exasol metrics in Dashboard {dashboard_id} with StarRocks metrics...")
    print("=" * 70)
    
    # Authenticate
    session_token = authenticate()
    if not session_token:
        return
    
    print("✅ Authentication successful")
    
    # Get dashboard details
    print(f"\n📊 Fetching dashboard {dashboard_id} details...")
    dashboard = get_dashboard_details(session_token, dashboard_id)
    if not dashboard:
        return
    
    print(f"✅ Found dashboard: {dashboard.get('name', 'Unknown')}")
    
    # Get StarRocks metrics
    print(f"\n📊 Fetching StarRocks metrics...")
    starrocks_metrics = get_starrocks_metrics(session_token)
    print(f"✅ Found {len(starrocks_metrics)} StarRocks metrics")
    
    # Analyze dashboard cards
    dashcards = dashboard.get('dashcards', [])
    print(f"\n📋 Dashboard has {len(dashcards)} cards")
    
    # Track replacements
    replaced_cards = []
    failed_cards = []
    
    for i, dashcard in enumerate(dashcards):
        card = dashcard.get('card', {})
        card_id = card.get('id')
        card_name = card.get('name', 'Unknown')
        
        print(f"\n[{i+1}/{len(dashcards)}] Processing card: {card_name} (ID: {card_id})")
        
        # Check if this card uses metrics
        dataset_query = card.get('dataset_query', {})
        query_type = dataset_query.get('type')
        
        if query_type == 'query':
            query = dataset_query.get('query', {})
            aggregations = query.get('aggregation', [])
            
            # Look for metric references in aggregations
            for agg in aggregations:
                if isinstance(agg, list) and len(agg) > 1 and agg[0] == 'metric':
                    metric_id = agg[1]
                    print(f"    📊 Found metric reference: {metric_id}")
                    
                    # Try to find a corresponding StarRocks metric
                    sr_metric = find_metric_mapping(card_name, starrocks_metrics)
                    if sr_metric:
                        new_metric_id = sr_metric.get('id')
                        print(f"    🔄 Mapping to StarRocks metric: {sr_metric.get('name')} (ID: {new_metric_id})")
                        
                        # Update the card
                        if update_dashboard_card(session_token, card_id, new_metric_id):
                            replaced_cards.append({
                                "card_id": card_id,
                                "card_name": card_name,
                                "old_metric_id": metric_id,
                                "new_metric_id": new_metric_id,
                                "new_metric_name": sr_metric.get('name')
                            })
                        else:
                            failed_cards.append({
                                "card_id": card_id,
                                "card_name": card_name,
                                "old_metric_id": metric_id,
                                "reason": "Failed to update card"
                            })
                    else:
                        print(f"    ⚠️  No StarRocks metric found for: {card_name}")
                        failed_cards.append({
                            "card_id": card_id,
                            "card_name": card_name,
                            "old_metric_id": metric_id,
                            "reason": "No StarRocks metric mapping found"
                        })
        else:
            print(f"    ⏭️  Skipping card - not a query type: {query_type}")
    
    # Summary
    print(f"\n📈 Replacement Summary:")
    print(f"Total cards processed: {len(dashcards)}")
    print(f"Successfully replaced: {len(replaced_cards)} cards")
    print(f"Failed to replace: {len(failed_cards)} cards")
    
    if replaced_cards:
        print(f"\n✅ Successfully replaced cards:")
        for card in replaced_cards:
            print(f"  • {card['card_name']} → {card['new_metric_name']}")
    
    if failed_cards:
        print(f"\n❌ Failed to replace cards:")
        for card in failed_cards:
            print(f"  • {card['card_name']}: {card['reason']}")
    
    # Save results
    with open('dashboard_500_metric_replacement.json', 'w') as f:
        json.dump({
            "dashboard_id": dashboard_id,
            "dashboard_name": dashboard.get('name'),
            "replaced_cards": replaced_cards,
            "failed_cards": failed_cards,
            "total_cards": len(dashcards)
        }, f, indent=2)
    
    print(f"\n💾 Results saved to dashboard_500_metric_replacement.json")

if __name__ == "__main__":
    main() 