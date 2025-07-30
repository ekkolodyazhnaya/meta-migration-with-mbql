#!/usr/bin/env python3
"""
Improved script to replace Exasol metrics in dashboard 500 with StarRocks metrics
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

def get_all_metrics(session_token):
    """Get all metrics and create a mapping"""
    try:
        response = requests.get(
            f"{METABASE_CONFIG['base_url']}/api/search?models=metric&archived=false",
            headers={"X-Metabase-Session": session_token}
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get('data', [])
        else:
            print(f"❌ Failed to fetch metrics: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error fetching metrics: {str(e)}")
        return []

def create_metric_mapping(all_metrics):
    """Create mapping between Exasol and StarRocks metrics"""
    mapping = {}
    
    # Group metrics by collection
    exasol_metrics = []
    starrocks_metrics = []
    
    for metric in all_metrics:
        collection_name = metric.get('collection', {}).get('name', '')
        if 'Migrated Metrics' in collection_name:
            exasol_metrics.append(metric)
        elif 'Starrocks Metabase Metrics' in collection_name:
            starrocks_metrics.append(metric)
    
    print(f"📊 Found {len(exasol_metrics)} Exasol metrics and {len(starrocks_metrics)} StarRocks metrics")
    
    # Create mapping based on name similarity
    for exasol_metric in exasol_metrics:
        exasol_name = exasol_metric.get('name', '').lower()
        best_match = None
        best_score = 0
        
        for sr_metric in starrocks_metrics:
            sr_name = sr_metric.get('name', '').lower()
            
            # Remove common suffixes for comparison
            exasol_clean = exasol_name.replace(' (oor)', '').replace(' (ooor)', '').replace(' sr', '')
            sr_clean = sr_name.replace(' (oor)', '').replace(' (ooor)', '').replace(' sr', '')
            
            # Exact match
            if exasol_clean == sr_clean:
                score = 100
            # Contains match
            elif exasol_clean in sr_clean or sr_clean in exasol_clean:
                score = 80
            # Word match
            elif any(word in sr_clean for word in exasol_clean.split()) or any(word in exasol_clean for word in sr_clean.split()):
                score = 60
            else:
                score = 0
            
            if score > best_score:
                best_score = score
                best_match = sr_metric
        
        if best_match and best_score > 50:
            mapping[exasol_metric['id']] = {
                'exasol_metric': exasol_metric,
                'starrocks_metric': best_match,
                'confidence': best_score
            }
    
    return mapping

def update_card_metric(session_token, card_id, new_metric_id):
    """Update a card to use a new metric"""
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
        
        # Update the dataset_query to use the new metric
        dataset_query = card_data.get('dataset_query', {})
        if dataset_query.get('type') == 'query':
            query = dataset_query.get('query', {})
            aggregations = query.get('aggregation', [])
            
            # Replace metric references
            updated_aggregations = []
            for agg in aggregations:
                if isinstance(agg, list) and len(agg) > 1 and agg[0] == 'metric':
                    # Replace with new metric
                    updated_aggregations.append(['metric', new_metric_id])
                else:
                    updated_aggregations.append(agg)
            
            # Update the query
            query['aggregation'] = updated_aggregations
            dataset_query['query'] = query
            card_data['dataset_query'] = dataset_query
        
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
            print(f"    ❌ Response: {update_response.text}")
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
    
    # Get all metrics and create mapping
    print(f"\n📊 Fetching all metrics and creating mapping...")
    all_metrics = get_all_metrics(session_token)
    metric_mapping = create_metric_mapping(all_metrics)
    
    print(f"✅ Created {len(metric_mapping)} metric mappings")
    
    # Show sample mappings
    print(f"\n📋 Sample metric mappings:")
    for i, (exasol_id, mapping) in enumerate(list(metric_mapping.items())[:5]):
        exasol_name = mapping['exasol_metric']['name']
        sr_name = mapping['starrocks_metric']['name']
        confidence = mapping['confidence']
        print(f"  {i+1}. {exasol_name} (ID: {exasol_id}) → {sr_name} (Confidence: {confidence}%)")
    
    # Analyze dashboard cards
    dashcards = dashboard.get('dashcards', [])
    print(f"\n📋 Dashboard has {len(dashcards)} cards")
    
    # Track replacements
    replaced_cards = []
    failed_cards = []
    skipped_cards = []
    
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
            found_metrics = []
            for agg in aggregations:
                if isinstance(agg, list) and len(agg) > 1 and agg[0] == 'metric':
                    metric_id = agg[1]
                    found_metrics.append(metric_id)
                    print(f"    📊 Found metric reference: {metric_id}")
                    
                    # Check if we have a mapping for this metric
                    if metric_id in metric_mapping:
                        mapping = metric_mapping[metric_id]
                        new_metric_id = mapping['starrocks_metric']['id']
                        new_metric_name = mapping['starrocks_metric']['name']
                        confidence = mapping['confidence']
                        
                        print(f"    🔄 Mapping to StarRocks metric: {new_metric_name} (ID: {new_metric_id}, Confidence: {confidence}%)")
                        
                        # Update the card
                        if update_card_metric(session_token, card_id, new_metric_id):
                            replaced_cards.append({
                                "card_id": card_id,
                                "card_name": card_name,
                                "old_metric_id": metric_id,
                                "old_metric_name": mapping['exasol_metric']['name'],
                                "new_metric_id": new_metric_id,
                                "new_metric_name": new_metric_name,
                                "confidence": confidence
                            })
                        else:
                            failed_cards.append({
                                "card_id": card_id,
                                "card_name": card_name,
                                "old_metric_id": metric_id,
                                "reason": "Failed to update card"
                            })
                    else:
                        print(f"    ⚠️  No StarRocks mapping found for metric {metric_id}")
                        failed_cards.append({
                            "card_id": card_id,
                            "card_name": card_name,
                            "old_metric_id": metric_id,
                            "reason": "No StarRocks metric mapping found"
                        })
            
            if not found_metrics:
                print(f"    ⏭️  No metrics found in this card")
                skipped_cards.append({
                    "card_id": card_id,
                    "card_name": card_name,
                    "reason": "No metrics found"
                })
        else:
            print(f"    ⏭️  Skipping card - not a query type: {query_type}")
            skipped_cards.append({
                "card_id": card_id,
                "card_name": card_name,
                "reason": f"Not a query type: {query_type}"
            })
    
    # Summary
    print(f"\n📈 Replacement Summary:")
    print(f"Total cards processed: {len(dashcards)}")
    print(f"Successfully replaced: {len(replaced_cards)} cards")
    print(f"Failed to replace: {len(failed_cards)} cards")
    print(f"Skipped: {len(skipped_cards)} cards")
    
    if replaced_cards:
        print(f"\n✅ Successfully replaced cards:")
        for card in replaced_cards:
            print(f"  • {card['card_name']}: {card['old_metric_name']} → {card['new_metric_name']} (Confidence: {card['confidence']}%)")
    
    if failed_cards:
        print(f"\n❌ Failed to replace cards:")
        for card in failed_cards[:5]:  # Show first 5
            print(f"  • {card['card_name']}: {card['reason']}")
        if len(failed_cards) > 5:
            print(f"  ... and {len(failed_cards) - 5} more")
    
    # Save results
    with open('dashboard_500_metric_replacement_v2.json', 'w') as f:
        json.dump({
            "dashboard_id": dashboard_id,
            "dashboard_name": dashboard.get('name'),
            "replaced_cards": replaced_cards,
            "failed_cards": failed_cards,
            "skipped_cards": skipped_cards,
            "total_cards": len(dashcards),
            "metric_mappings": {str(k): {
                "exasol_name": v['exasol_metric']['name'],
                "starrocks_name": v['starrocks_metric']['name'],
                "confidence": v['confidence']
            } for k, v in metric_mapping.items()}
        }, f, indent=2)
    
    print(f"\n💾 Results saved to dashboard_500_metric_replacement_v2.json")

if __name__ == "__main__":
    main() 