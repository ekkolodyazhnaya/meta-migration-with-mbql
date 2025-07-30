#!/usr/bin/env python3
"""
Script to check and fix dashboard filter configuration and ensure all cards have consistent template tags
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
        },
        'CREATED_AT': {
            "type": "dimension",
            "name": "CREATED_AT",
            "id": "764144ae-9181-4109-af3d-1fc83ae0e936",
            "display-name": "Created At",
            "default": None,
            "dimension": [
                "field",
                756080,
                None
            ],
            "widget-type": "date/all-options",
            "options": None
        },
        'PAY_SYSTEM': {
            "type": "dimension",
            "name": "PAY_SYSTEM",
            "id": "d08fbf9b-68ea-4906-bd1b-186b5aa73330",
            "display-name": "Pay System",
            "dimension": [
                "field",
                756097,
                None
            ],
            "widget-type": "string/="
        },
        'WIDGET_PARTNER_NAME': {
            "type": "dimension",
            "name": "WIDGET_PARTNER_NAME",
            "id": "6327ab6f-1235-4157-b45e-4b1f9425b5d4",
            "display-name": "Widget Partner Name",
            "dimension": [
                "field",
                756138,
                None
            ],
            "widget-type": "string/="
        },
        'CURRENCY': {
            "type": "dimension",
            "name": "CURRENCY",
            "id": "1a31bc3f-cdc2-4904-b21d-9a150d0b7937",
            "display-name": "Currency",
            "dimension": [
                "field",
                756119,
                None
            ],
            "widget-type": "string/="
        },
        'CRYPTO': {
            "type": "dimension",
            "name": "CRYPTO",
            "id": "381c2993-7db6-4a68-9787-9cd1ec02b7b9",
            "display-name": "Crypto",
            "dimension": [
                "field",
                756104,
                None
            ],
            "widget-type": "string/="
        },
        'TYPE': {
            "type": "dimension",
            "name": "TYPE",
            "id": "a716ead1-bce3-46fc-b726-9f883f099e5f",
            "display-name": "Type",
            "dimension": [
                "field",
                756091,
                None
            ],
            "widget-type": "string/="
        },
        'CARD_BIN': {
            "type": "dimension",
            "name": "CARD_BIN",
            "id": "7aca042c-08a3-400a-8df1-8394c48ca875",
            "display-name": "Card Bin",
            "default": None,
            "dimension": [
                "field",
                756200,
                None
            ],
            "widget-type": "string/="
        }
    }

def check_and_fix_card_template_tags(session_token, card_id, card_data):
    """Check and fix template tags for a card"""
    try:
        dataset_query = card_data.get('dataset_query', {})
        if dataset_query.get('type') != 'native':
            return False, "Not a native SQL query"
        
        native_query = dataset_query.get('native', {})
        current_template_tags = native_query.get('template-tags', {})
        
        # Get standard template tags
        standard_tags = create_standard_template_tags()
        
        # Check if Card_Geo and CARD_ISOCOUNTRY are present and correct
        needs_update = False
        updated_template_tags = current_template_tags.copy()
        
        # Ensure Card_Geo is present and correct
        if 'Card_Geo' not in current_template_tags:
            updated_template_tags['Card_Geo'] = standard_tags['Card_Geo']
            needs_update = True
        elif current_template_tags['Card_Geo'] != standard_tags['Card_Geo']:
            updated_template_tags['Card_Geo'] = standard_tags['Card_Geo']
            needs_update = True
        
        # Ensure CARD_ISOCOUNTRY is present and correct
        if 'CARD_ISOCOUNTRY' not in current_template_tags:
            updated_template_tags['CARD_ISOCOUNTRY'] = standard_tags['CARD_ISOCOUNTRY']
            needs_update = True
        elif current_template_tags['CARD_ISOCOUNTRY'] != standard_tags['CARD_ISOCOUNTRY']:
            updated_template_tags['CARD_ISOCOUNTRY'] = standard_tags['CARD_ISOCOUNTRY']
            needs_update = True
        
        if not needs_update:
            return False, "No template tag updates needed"
        
        # Update the card data
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
            return True, "Updated template tags"
        else:
            return False, f"API error: {update_response.status_code} - {update_response.text}"
            
    except Exception as e:
        return False, f"Error: {str(e)}"

def main():
    """Main function"""
    dashboard_id = 485
    
    print(f"🔧 Checking and fixing dashboard filter configuration for Dashboard {dashboard_id}...")
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
    
    # Check each card for template tag consistency
    print(f"\n🔍 Checking each card for template tag consistency...")
    
    cards_checked = []
    cards_updated = []
    cards_failed = []
    
    for i, dashcard in enumerate(dashcards):
        card = dashcard.get('card', {})
        card_id = card.get('id')
        card_name = card.get('name', 'Unknown')
        
        if not card_id:
            print(f"[{i+1}/{len(dashcards)}] Skipping card without ID: {card_name}")
            continue
        
        print(f"\n[{i+1}/{len(dashcards)}] Checking card: {card_name} (ID: {card_id})")
        
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
        
        # Check and fix template tags
        success, message = check_and_fix_card_template_tags(session_token, card_id, card_data)
        
        if success:
            print(f"    ✅ Success: {message}")
            cards_updated.append({
                'card_id': card_id,
                'card_name': card_name,
                'changes': message
            })
        elif message == "No template tag updates needed":
            print(f"    ✅ {message}")
            cards_checked.append({
                'card_id': card_id,
                'card_name': card_name,
                'status': 'No updates needed'
            })
        else:
            print(f"    ❌ Failed: {message}")
            cards_failed.append({
                'card_id': card_id,
                'card_name': card_name,
                'error': message
            })
    
    # Summary
    print(f"\n📈 Template Tag Check Summary:")
    print(f"Total cards processed: {len(cards_checked) + len(cards_updated) + len(cards_failed)}")
    print(f"Cards checked (no updates needed): {len(cards_checked)}")
    print(f"Cards updated: {len(cards_updated)}")
    print(f"Cards failed: {len(cards_failed)}")
    
    if cards_updated:
        print(f"\n✅ Successfully updated cards:")
        for card in cards_updated:
            print(f"  • {card['card_name']} (ID: {card['card_id']}) - {card['changes']}")
    
    if cards_failed:
        print(f"\n❌ Failed to update cards:")
        for card in cards_failed:
            print(f"  • {card['card_name']} (ID: {card['card_id']}) - {card['error']}")
    
    # Troubleshooting tips
    print(f"\n🔧 Troubleshooting Tips for 'undefined is not an object (evaluating e.name)' error:")
    print(f"1. Clear your browser cache and refresh the dashboard")
    print(f"2. Try opening the dashboard in an incognito/private window")
    print(f"3. Check if the dashboard filters are properly configured")
    print(f"4. Ensure all cards have consistent template tag configurations")
    print(f"5. Try refreshing the dashboard after a few minutes")
    
    # Save results
    with open('dashboard_485_filter_check.json', 'w') as f:
        json.dump({
            "dashboard_id": dashboard_id,
            "dashboard_name": dashboard.get('name'),
            "cards_checked": cards_checked,
            "cards_updated": cards_updated,
            "cards_failed": cards_failed,
            "total_cards": len(dashcards)
        }, f, indent=2)
    
    print(f"\n💾 Results saved to dashboard_485_filter_check.json")

if __name__ == "__main__":
    main() 