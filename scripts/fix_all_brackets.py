#!/usr/bin/env python3
"""
Script to fix all template tags to use double brackets {{}} instead of single brackets {}
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

def needs_bracket_fix(card_data):
    """Check if a card needs bracket fix"""
    dataset_query = card_data.get('dataset_query', {})
    if dataset_query.get('type') != 'native':
        return False
    
    native_query = dataset_query.get('native', {})
    query_text = native_query.get('query', '')
    
    # Check if SQL has single brackets that need to be replaced with double brackets
    has_single_brackets = re.search(r'\{[A-Z_]+\}', query_text)
    
    return has_single_brackets is not None

def fix_card_brackets(session_token, card_id, card_data):
    """Fix the brackets in a card's SQL query"""
    try:
        dataset_query = card_data.get('dataset_query', {})
        native_query = dataset_query.get('native', {})
        query_text = native_query.get('query', '')
        
        # Replace all single bracket template tags with double brackets
        updated_query = query_text
        
        # Replace {CREATED_AT} with {{CREATED_AT}}
        updated_query = re.sub(r'\{CREATED_AT\}', '{{CREATED_AT}}', updated_query)
        
        # Replace {PAY_SYSTEM} with {{PAY_SYSTEM}}
        updated_query = re.sub(r'\{PAY_SYSTEM\}', '{{PAY_SYSTEM}}', updated_query)
        
        # Replace {WIDGET_PARTNER_NAME} with {{WIDGET_PARTNER_NAME}}
        updated_query = re.sub(r'\{WIDGET_PARTNER_NAME\}', '{{WIDGET_PARTNER_NAME}}', updated_query)
        
        # Replace {CURRENCY} with {{CURRENCY}}
        updated_query = re.sub(r'\{CURRENCY\}', '{{CURRENCY}}', updated_query)
        
        # Replace {CRYPTO} with {{CRYPTO}}
        updated_query = re.sub(r'\{CRYPTO\}', '{{CRYPTO}}', updated_query)
        
        # Replace {TYPE} with {{TYPE}}
        updated_query = re.sub(r'\{TYPE\}', '{{TYPE}}', updated_query)
        
        # Replace {CARD_BIN} with {{CARD_BIN}}
        updated_query = re.sub(r'\{CARD_BIN\}', '{{CARD_BIN}}', updated_query)
        
        # Replace {Card_Geo} with {{Card_Geo}}
        updated_query = re.sub(r'\{Card_Geo\}', '{{Card_Geo}}', updated_query)
        
        # Replace {CARD_ISOCOUNTRY} with {{CARD_ISOCOUNTRY}}
        updated_query = re.sub(r'\{CARD_ISOCOUNTRY\}', '{{CARD_ISOCOUNTRY}}', updated_query)
        
        if updated_query == query_text:
            return False, "No changes needed"
        
        # Update the card data
        native_query['query'] = updated_query
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
            return True, "Fixed single brackets to double brackets"
        else:
            return False, f"API error: {update_response.status_code} - {update_response.text}"
            
    except Exception as e:
        return False, f"Error: {str(e)}"

def main():
    """Main function"""
    dashboard_id = 485
    
    print(f"🔧 Fixing all template tag brackets on Dashboard {dashboard_id}...")
    print("=" * 60)
    
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
    
    # Check each card for bracket issues
    print(f"\n🔍 Checking each card for bracket issues...")
    
    cards_needing_fix = []
    cards_checked = []
    
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
            continue
        
        # Check if card needs bracket fix
        needs_fix = needs_bracket_fix(card_data)
        
        if needs_fix:
            print(f"    ⚠️  Needs bracket fix: has single brackets that need double brackets")
            cards_needing_fix.append({
                'card_id': card_id,
                'card_name': card_name,
                'card_data': card_data
            })
        else:
            print(f"    ✅ No bracket fix needed")
        
        cards_checked.append({
            'card_id': card_id,
            'card_name': card_name,
            'needs_fix': needs_fix
        })
    
    # Fix cards that need it
    if cards_needing_fix:
        print(f"\n🔧 Fixing {len(cards_needing_fix)} cards with bracket issues...")
        
        updated_cards = []
        failed_cards = []
        
        for i, card_info in enumerate(cards_needing_fix):
            card_id = card_info['card_id']
            card_name = card_info['card_name']
            card_data = card_info['card_data']
            
            print(f"\n[{i+1}/{len(cards_needing_fix)}] Fixing: {card_name} (ID: {card_id})")
            
            success, message = fix_card_brackets(session_token, card_id, card_data)
            
            if success:
                print(f"    ✅ Success: {message}")
                updated_cards.append({
                    'card_id': card_id,
                    'card_name': card_name,
                    'changes': message
                })
            else:
                print(f"    ❌ Failed: {message}")
                failed_cards.append({
                    'card_id': card_id,
                    'card_name': card_name,
                    'error': message
                })
    else:
        print(f"\n✅ All cards already have correct brackets!")
    
    # Summary
    print(f"\n📈 Bracket Fix Summary:")
    print(f"Total cards checked: {len(cards_checked)}")
    print(f"Cards needing bracket fix: {len(cards_needing_fix)}")
    
    if cards_needing_fix:
        print(f"Successfully fixed: {len(updated_cards)} cards")
        print(f"Failed to fix: {len(failed_cards)} cards")
        
        if updated_cards:
            print(f"\n✅ Successfully fixed cards:")
            for card in updated_cards:
                print(f"  • {card['card_name']} (ID: {card['card_id']}) - {card['changes']}")
        
        if failed_cards:
            print(f"\n❌ Failed to fix cards:")
            for card in failed_cards:
                print(f"  • {card['card_name']} (ID: {card['card_id']}) - {card['error']}")
    
    # Save results
    with open('dashboard_485_all_brackets_fix.json', 'w') as f:
        json.dump({
            "dashboard_id": dashboard_id,
            "dashboard_name": dashboard.get('name'),
            "cards_checked": cards_checked,
            "cards_needing_fix": [{"card_id": c["card_id"], "card_name": c["card_name"]} for c in cards_needing_fix],
            "updated_cards": updated_cards if 'updated_cards' in locals() else [],
            "failed_cards": failed_cards if 'failed_cards' in locals() else [],
            "total_cards": len(dashcards)
        }, f, indent=2)
    
    print(f"\n💾 Results saved to dashboard_485_all_brackets_fix.json")

if __name__ == "__main__":
    main() 