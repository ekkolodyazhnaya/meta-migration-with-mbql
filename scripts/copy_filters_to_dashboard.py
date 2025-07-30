#!/usr/bin/env python3
"""
Script to copy Card_Geo and CARD_ISOCOUNTRY filters from Total Turnover question to all other questions on dashboard 485
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

def get_card_details(session_token, card_id):
    """Get detailed information about a card"""
    try:
        response = requests.get(
            f"{METABASE_CONFIG['base_url']}/api/card/{card_id}",
            headers={"X-Metabase-Session": session_token}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Failed to fetch card {card_id}: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error fetching card {card_id}: {str(e)}")
        return None

def find_total_turnover_card(dashcards):
    """Find the Total Turnover card in the dashboard"""
    for dashcard in dashcards:
        card = dashcard.get('card', {})
        card_name = card.get('name', '').lower()
        if 'total turnover' in card_name:
            return card
    return None

def extract_filters_from_card(card_data):
    """Extract Card_Geo and CARD_ISOCOUNTRY filters from a card's template tags"""
    filters = []
    
    # Check if the card has template tags (for native SQL queries)
    dataset_query = card_data.get('dataset_query', {})
    if dataset_query.get('type') == 'native':
        template_tags = dataset_query.get('native', {}).get('template-tags', {})
        for tag_name, tag_config in template_tags.items():
            if tag_name in ['Card_Geo', 'CARD_ISOCOUNTRY']:
                # Create a copy of the config and remove default value for CARD_ISOCOUNTRY
                config_copy = tag_config.copy()
                if tag_name == 'CARD_ISOCOUNTRY':
                    config_copy['default'] = None
                    print(f"    🗑️  Removed default value for {tag_name}")
                
                filters.append({
                    'name': tag_name,
                    'config': config_copy
                })
    
    return filters

def add_filters_to_card(session_token, card_id, filters_to_add):
    """Add filters to a card's template tags"""
    try:
        # Get the current card details
        card_data = get_card_details(session_token, card_id)
        if not card_data:
            return False
        
        # Check if this is a native SQL query
        dataset_query = card_data.get('dataset_query', {})
        if dataset_query.get('type') != 'native':
            print(f"    ⏭️  Card is not a native SQL query, skipping")
            return False
        
        # Get current template tags
        native_query = dataset_query.get('native', {})
        current_template_tags = native_query.get('template-tags', {})
        
        # Add new filters if they don't already exist
        updated_template_tags = current_template_tags.copy()
        existing_tag_names = list(current_template_tags.keys())
        
        for filter_config in filters_to_add:
            filter_name = filter_config['name']
            if filter_name not in existing_tag_names:
                updated_template_tags[filter_name] = filter_config['config']
                print(f"    ➕ Added filter: {filter_name}")
            else:
                print(f"    ⏭️  Filter already exists: {filter_name}")
        
        # Update the card
        native_query['template-tags'] = updated_template_tags
        dataset_query['native'] = native_query
        card_data['dataset_query'] = dataset_query
        
        update_response = requests.put(
            f"{METABASE_CONFIG['base_url']}/api/card/{card_id}",
            headers={
                "X-Metabase-Session": session_token,
                "Content-Type": "application/json"
            },
            json=card_data
        )
        
        if update_response.status_code == 200:
            print(f"    ✅ Successfully updated card {card_id}")
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
    dashboard_id = 485
    
    print(f"🔄 Copying Card_Geo and CARD_ISOCOUNTRY filters to all questions on Dashboard {dashboard_id}...")
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
    
    # Get dashboard cards
    dashcards = dashboard.get('dashcards', [])
    print(f"📋 Dashboard has {len(dashcards)} cards")
    
    # Find the Total Turnover card
    print(f"\n🔍 Looking for Total Turnover card...")
    total_turnover_card = find_total_turnover_card(dashcards)
    
    if not total_turnover_card:
        print("❌ Could not find Total Turnover card")
        return
    
    print(f"✅ Found Total Turnover card: {total_turnover_card.get('name')} (ID: {total_turnover_card.get('id')})")
    
    # Extract filters from Total Turnover card
    print(f"\n📋 Extracting filters from Total Turnover card...")
    filters_to_copy = extract_filters_from_card(total_turnover_card)
    
    if not filters_to_copy:
        print("❌ No Card_Geo or CARD_ISOCOUNTRY filters found in Total Turnover card")
        return
    
    print(f"✅ Found {len(filters_to_copy)} filters to copy:")
    for filter_param in filters_to_copy:
        print(f"  • {filter_param.get('name')} ({filter_param.get('type')})")
    
    # Copy filters to all other cards
    print(f"\n🔄 Copying filters to all other cards...")
    
    updated_cards = []
    failed_cards = []
    skipped_cards = []
    
    for i, dashcard in enumerate(dashcards):
        card = dashcard.get('card', {})
        card_id = card.get('id')
        card_name = card.get('name', 'Unknown')
        
        # Skip the Total Turnover card itself
        if card_id == total_turnover_card.get('id'):
            print(f"[{i+1}/{len(dashcards)}] Skipping Total Turnover card (source)")
            skipped_cards.append({
                "card_id": card_id,
                "card_name": card_name,
                "reason": "Source card"
            })
            continue
        
        print(f"\n[{i+1}/{len(dashcards)}] Processing card: {card_name} (ID: {card_id})")
        
        # Add filters to the card
        if add_filters_to_card(session_token, card_id, filters_to_copy):
            updated_cards.append({
                "card_id": card_id,
                "card_name": card_name
            })
        else:
            failed_cards.append({
                "card_id": card_id,
                "card_name": card_name
            })
    
    # Summary
    print(f"\n📈 Filter Copy Summary:")
    print(f"Total cards processed: {len(dashcards)}")
    print(f"Successfully updated: {len(updated_cards)} cards")
    print(f"Failed to update: {len(failed_cards)} cards")
    print(f"Skipped: {len(skipped_cards)} cards")
    
    if updated_cards:
        print(f"\n✅ Successfully updated cards:")
        for card in updated_cards:
            print(f"  • {card['card_name']} (ID: {card['card_id']})")
    
    if failed_cards:
        print(f"\n❌ Failed to update cards:")
        for card in failed_cards:
            print(f"  • {card['card_name']} (ID: {card['card_id']})")
    
    # Save results
    with open('dashboard_485_filter_copy.json', 'w') as f:
        json.dump({
            "dashboard_id": dashboard_id,
            "dashboard_name": dashboard.get('name'),
            "source_card": {
                "id": total_turnover_card.get('id'),
                "name": total_turnover_card.get('name')
            },
            "filters_copied": [f.get('name') for f in filters_to_copy],
            "updated_cards": updated_cards,
            "failed_cards": failed_cards,
            "skipped_cards": skipped_cards,
            "total_cards": len(dashcards)
        }, f, indent=2)
    
    print(f"\n💾 Results saved to dashboard_485_filter_copy.json")

if __name__ == "__main__":
    main() 