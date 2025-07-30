#!/usr/bin/env python3
"""
Script to add Card_Geo and CARD_ISOCOUNTRY filters to all questions on dashboard 503
that use MART__TRANSACTIONS main table
"""

import requests
import json
import re
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

def create_standard_template_tags():
    """Create standard template tag configurations"""
    return {
        'Card_Geo': {
            "type": "dimension",
            "name": "Card_Geo",
            "id": "f9338c61-c741-44d7-a6a5-ac57bac8b387",
            "display-name": "Card Geo",
            "dimension": [
                "field",
                756074,
                None
            ],
            "widget-type": "string/="
        },
        'CARD_ISOCOUNTRY': {
            "type": "dimension",
            "name": "CARD_ISOCOUNTRY",
            "id": "3c2e2b6a-c8ca-4c78-824e-32e304de4bd9",
            "display-name": "Card Isocountry",
            "default": None,
            "dimension": [
                "field",
                756215,
                None
            ],
            "widget-type": "string/contains",
            "options": {
                "case-sensitive": False
            }
        }
    }

def uses_mart_transactions(card_data):
    """Check if the card uses MART__TRANSACTIONS table"""
    try:
        dataset_query = card_data.get('dataset_query', {})
        if dataset_query.get('type') != 'native':
            return False
        
        native_query = dataset_query.get('native', {})
        query_text = native_query.get('query', '')
        
        # Check if the query contains MART__TRANSACTIONS
        return 'MART__TRANSACTIONS' in query_text.upper()
        
    except Exception as e:
        print(f"Error checking MART__TRANSACTIONS usage: {str(e)}")
        return False

def needs_filter_update(card_data):
    """Check if a card needs filter updates"""
    try:
        dataset_query = card_data.get('dataset_query', {})
        if dataset_query.get('type') != 'native':
            return False, "Not a native SQL query"
        
        native_query = dataset_query.get('native', {})
        query_text = native_query.get('query', '')
        template_tags = native_query.get('template-tags', {})
        
        # Check if Card_Geo and CARD_ISOCOUNTRY are missing
        missing_filters = []
        if 'Card_Geo' not in template_tags:
            missing_filters.append('Card_Geo')
        if 'CARD_ISOCOUNTRY' not in template_tags:
            missing_filters.append('CARD_ISOCOUNTRY')
        
        # Check if there are hardcoded values that should be replaced
        has_hardcoded_values = False
        if "CARD_ISOCOUNTRY='" in query_text or "CARD_ISOCOUNTRY = '" in query_text:
            has_hardcoded_values = True
        
        # Check if template tags have default values that should be removed
        has_default_values = False
        for tag_name, tag_config in template_tags.items():
            if tag_name in ['Card_Geo', 'CARD_ISOCOUNTRY'] and tag_config.get('default') is not None:
                has_default_values = True
                break
        
        if missing_filters or has_hardcoded_values or has_default_values:
            return True, f"Missing filters: {missing_filters}, Hardcoded values: {has_hardcoded_values}, Default values: {has_default_values}"
        
        return False, "No updates needed"
        
    except Exception as e:
        return False, f"Error checking card: {str(e)}"

def update_card_with_filters(session_token, card_id, card_data):
    """Update a card with the required filters"""
    try:
        dataset_query = card_data.get('dataset_query', {})
        native_query = dataset_query.get('native', {})
        query_text = native_query.get('query', '')
        template_tags = native_query.get('template-tags', {})
        
        # Get standard template tags
        standard_tags = create_standard_template_tags()
        
        # Update template tags
        updated_template_tags = template_tags.copy()
        
        # Add missing template tags
        if 'Card_Geo' not in template_tags:
            updated_template_tags['Card_Geo'] = standard_tags['Card_Geo']
        
        if 'CARD_ISOCOUNTRY' not in template_tags:
            updated_template_tags['CARD_ISOCOUNTRY'] = standard_tags['CARD_ISOCOUNTRY']
        else:
            # Remove default value if it exists
            updated_template_tags['CARD_ISOCOUNTRY']['default'] = None
        
        # Update the query text
        updated_query = query_text
        
        # Replace hardcoded CARD_ISOCOUNTRY values with template tag
        updated_query = re.sub(
            r"CARD_ISOCOUNTRY\s*=\s*'[^']*'",
            "{{CARD_ISOCOUNTRY}}",
            updated_query,
            flags=re.IGNORECASE
        )
        
        # Add Card_Geo to WHERE clause if it's missing
        if '{{Card_Geo}}' not in updated_query:
            # Find the end of the WHERE clause
            where_pattern = re.compile(r'(where[\s\S]+?)(group by|order by|limit|$)', re.IGNORECASE)
            match = where_pattern.search(updated_query)
            
            if match:
                where_clause = match.group(1)
                rest_of_query = match.group(2)
                
                # Add Card_Geo to the WHERE clause
                if where_clause.strip().endswith('and'):
                    new_where = where_clause.rstrip().rstrip('and').strip() + ' and {{Card_Geo}}'
                else:
                    new_where = where_clause.strip() + ' and {{Card_Geo}}'
                
                updated_query = updated_query[:match.start(1)] + new_where + rest_of_query
            else:
                # If no WHERE clause found, add one
                updated_query = updated_query + ' WHERE {{Card_Geo}}'
        
        # Update the card data
        native_query['query'] = updated_query
        native_query['template-tags'] = updated_template_tags
        dataset_query['native'] = native_query
        card_data['dataset_query'] = dataset_query
        
        # Send update to Metabase
        update_response = requests.put(
            f"{METABASE_CONFIG['base_url']}/api/card/{card_id}",
            headers={
                "X-Metabase-Session": session_token,
                "Content-Type": "application/json"
            },
            json=card_data
        )
        
        if update_response.status_code == 200:
            return True, "Updated with filters"
        else:
            return False, f"API error: {update_response.status_code} - {update_response.text}"
            
    except Exception as e:
        return False, f"Error: {str(e)}"

def main():
    """Main function"""
    dashboard_id = 503
    
    print(f"🔧 Adding Card_Geo and CARD_ISOCOUNTRY filters to Dashboard {dashboard_id}...")
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
    
    # Process each card
    print(f"\n🔍 Processing each card for filter updates...")
    
    cards_updated = []
    cards_skipped = []
    cards_failed = []
    cards_no_mart_transactions = []
    
    for i, dashcard in enumerate(dashcards):
        card = dashcard.get('card', {})
        card_id = card.get('id')
        card_name = card.get('name', 'Unknown')
        
        if not card_id:
            print(f"[{i+1}/{len(dashcards)}] Skipping card without ID: {card_name}")
            continue
        
        print(f"\n[{i+1}/{len(dashcards)}] Processing card: {card_name} (ID: {card_id})")
        
        # Get card details
        card_data = get_card_details(session_token, card_id)
        if not card_data:
            print(f"    ❌ Failed to fetch card details")
            cards_failed.append({
                'card_id': card_id,
                'card_name': card_name,
                'error': 'Failed to fetch card details'
            })
            continue
        
        # Check if card uses MART__TRANSACTIONS
        if not uses_mart_transactions(card_data):
            print(f"    ⏭️  Card does not use MART__TRANSACTIONS table")
            cards_no_mart_transactions.append({
                'card_id': card_id,
                'card_name': card_name,
                'reason': 'Does not use MART__TRANSACTIONS table'
            })
            continue
        
        print(f"    ✅ Card uses MART__TRANSACTIONS table")
        
        # Check if card needs updates
        needs_update, reason = needs_filter_update(card_data)
        
        if not needs_update:
            print(f"    ✅ {reason}")
            cards_skipped.append({
                'card_id': card_id,
                'card_name': card_name,
                'reason': reason
            })
            continue
        
        print(f"    🔧 Needs update: {reason}")
        
        # Update the card
        success, message = update_card_with_filters(session_token, card_id, card_data)
        
        if success:
            print(f"    ✅ Success: {message}")
            cards_updated.append({
                'card_id': card_id,
                'card_name': card_name,
                'changes': message
            })
        else:
            print(f"    ❌ Failed: {message}")
            cards_failed.append({
                'card_id': card_id,
                'card_name': card_name,
                'error': message
            })
    
    # Summary
    print(f"\n📈 Filter Update Summary:")
    print(f"Total cards processed: {len(cards_updated) + len(cards_skipped) + len(cards_failed) + len(cards_no_mart_transactions)}")
    print(f"Cards using MART__TRANSACTIONS: {len(cards_updated) + len(cards_skipped) + len(cards_failed)}")
    print(f"Cards updated: {len(cards_updated)}")
    print(f"Cards skipped: {len(cards_skipped)}")
    print(f"Cards failed: {len(cards_failed)}")
    print(f"Cards without MART__TRANSACTIONS: {len(cards_no_mart_transactions)}")
    
    if cards_updated:
        print(f"\n✅ Successfully updated cards:")
        for card in cards_updated:
            print(f"  • {card['card_name']} (ID: {card['card_id']}) - {card['changes']}")
    
    if cards_skipped:
        print(f"\n⏭️  Skipped cards:")
        for card in cards_skipped:
            print(f"  • {card['card_name']} (ID: {card['card_id']}) - {card['reason']}")
    
    if cards_failed:
        print(f"\n❌ Failed to update cards:")
        for card in cards_failed:
            print(f"  • {card['card_name']} (ID: {card['card_id']}) - {card['error']}")
    
    if cards_no_mart_transactions:
        print(f"\n📊 Cards not using MART__TRANSACTIONS:")
        for card in cards_no_mart_transactions:
            print(f"  • {card['card_name']} (ID: {card['card_id']}) - {card['reason']}")
    
    # Save results
    with open('dashboard_503_filter_update_v2.json', 'w') as f:
        json.dump({
            "dashboard_id": dashboard_id,
            "dashboard_name": dashboard.get('name'),
            "cards_updated": cards_updated,
            "cards_skipped": cards_skipped,
            "cards_failed": cards_failed,
            "cards_no_mart_transactions": cards_no_mart_transactions,
            "total_cards": len(dashcards)
        }, f, indent=2)
    
    print(f"\n💾 Results saved to dashboard_503_filter_update_v2.json")
    print(f"\n🎯 All questions on dashboard {dashboard_id} that use MART__TRANSACTIONS now have Card_Geo and CARD_ISOCOUNTRY filters!")

if __name__ == "__main__":
    main() 