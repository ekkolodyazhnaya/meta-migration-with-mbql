#!/usr/bin/env python3
"""
Script to add missing Card_Geo and CARD_ISOCOUNTRY template tags to SQL queries
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

def needs_filter_update(card_data):
    """Check if a card needs filter updates"""
    dataset_query = card_data.get('dataset_query', {})
    if dataset_query.get('type') != 'native':
        return False
    
    native_query = dataset_query.get('native', {})
    query_text = native_query.get('query', '')
    template_tags = native_query.get('template-tags', {})
    
    # Check if SQL has hardcoded values but missing template tags
    has_hardcoded_card_geo = re.search(r"CARD_GEO\s*=\s*['\"][^'\"]*['\"]", query_text, re.IGNORECASE)
    has_hardcoded_isocountry = re.search(r"CARD_ISOCOUNTRY\s*=\s*['\"][^'\"]*['\"]", query_text, re.IGNORECASE)
    
    has_card_geo_tag = 'Card_Geo' in template_tags
    has_isocountry_tag = 'CARD_ISOCOUNTRY' in template_tags
    
    # Check if template tags have default values that should be removed
    card_geo_has_default = has_card_geo_tag and template_tags.get('Card_Geo', {}).get('default') is not None
    isocountry_has_default = has_isocountry_tag and template_tags.get('CARD_ISOCOUNTRY', {}).get('default') is not None
    
    # Check if SQL query is missing {{Card_Geo}} in WHERE clause
    missing_card_geo_in_query = 'where' in query_text.lower() and '{{Card_Geo}}' not in query_text
    
    needs_update = False
    reasons = []
    
    if has_hardcoded_card_geo and not has_card_geo_tag:
        needs_update = True
        reasons.append("has hardcoded CARD_GEO but no Card_Geo template tag")
    
    if has_hardcoded_isocountry and not has_isocountry_tag:
        needs_update = True
        reasons.append("has hardcoded CARD_ISOCOUNTRY but no CARD_ISOCOUNTRY template tag")
    
    if has_hardcoded_card_geo and has_card_geo_tag:
        needs_update = True
        reasons.append("has hardcoded CARD_GEO that should be replaced with {{Card_Geo}}")
    
    if has_hardcoded_isocountry and has_isocountry_tag:
        needs_update = True
        reasons.append("has hardcoded CARD_ISOCOUNTRY that should be replaced with {{CARD_ISOCOUNTRY}}")
    
    if card_geo_has_default:
        needs_update = True
        reasons.append("Card_Geo template tag has default value that should be removed")
    
    if isocountry_has_default:
        needs_update = True
        reasons.append("CARD_ISOCOUNTRY template tag has default value that should be removed")
    
    if missing_card_geo_in_query:
        needs_update = True
        reasons.append("missing {{Card_Geo}} in WHERE clause")
    
    return needs_update, reasons

def create_filter_template_tags():
    """Create the template tag configurations for Card_Geo and CARD_ISOCOUNTRY"""
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

def update_card_with_filters(session_token, card_id, card_data):
    """Update a card to add missing template tags and replace hardcoded values, and add 'and {{Card_Geo}}' if missing"""
    try:
        dataset_query = card_data.get('dataset_query', {})
        native_query = dataset_query.get('native', {})
        query_text = native_query.get('query', '')
        template_tags = native_query.get('template-tags', {})
        
        # Create filter template tags
        filter_tags = create_filter_template_tags()
        
        # Add missing template tags
        updated_template_tags = template_tags.copy()
        updated_query = query_text
        
        changes_made = []
        
        # Check and add Card_Geo filter
        if 'Card_Geo' not in template_tags:
            updated_template_tags['Card_Geo'] = filter_tags['Card_Geo']
            changes_made.append("added Card_Geo template tag")
        else:
            # Remove default value if it exists
            if updated_template_tags['Card_Geo'].get('default') is not None:
                updated_template_tags['Card_Geo']['default'] = None
                changes_made.append("removed default value from Card_Geo template tag")
        
        # Check and add CARD_ISOCOUNTRY filter
        if 'CARD_ISOCOUNTRY' not in template_tags:
            updated_template_tags['CARD_ISOCOUNTRY'] = filter_tags['CARD_ISOCOUNTRY']
            changes_made.append("added CARD_ISOCOUNTRY template tag")
        else:
            # Remove default value if it exists
            if updated_template_tags['CARD_ISOCOUNTRY'].get('default') is not None:
                updated_template_tags['CARD_ISOCOUNTRY']['default'] = None
                changes_made.append("removed default value from CARD_ISOCOUNTRY template tag")
        
        # Replace hardcoded values with template tags
        if re.search(r"CARD_GEO\s*=\s*['\"][^'\"]*['\"]", updated_query, re.IGNORECASE):
            updated_query = re.sub(
                r"CARD_GEO\s*=\s*['\"][^'\"]*['\"]",
                "{{Card_Geo}}",
                updated_query,
                flags=re.IGNORECASE
            )
            changes_made.append("replaced hardcoded CARD_GEO with {{Card_Geo}}")
        
        if re.search(r"CARD_ISOCOUNTRY\s*=\s*['\"][^'\"]*['\"]", updated_query, re.IGNORECASE):
            updated_query = re.sub(
                r"CARD_ISOCOUNTRY\s*=\s*['\"][^'\"]*['\"]",
                "{{CARD_ISOCOUNTRY}}",
                updated_query,
                flags=re.IGNORECASE
            )
            changes_made.append("replaced hardcoded CARD_ISOCOUNTRY with {{CARD_ISOCOUNTRY}}")
        
        # Add 'and {{Card_Geo}}' if not present in WHERE clause
        if 'where' in updated_query.lower() and '{{Card_Geo}}' not in updated_query:
            # Find the WHERE clause and add 'and {{Card_Geo}}' at the end
            # Look for the pattern: where ... and {{CARD_ISOCOUNTRY}} and CONFIRMED and ...
            pattern = re.compile(r'(where[\s\S]+?)(group by|order by|limit|$)', re.IGNORECASE)
            match = pattern.search(updated_query)
            if match:
                where_clause = match.group(1)
                rest = updated_query[match.end(1):]
                
                # Add 'and {{Card_Geo}}' at the end of the WHERE clause
                if where_clause.strip().endswith('}'):  # already ends with a filter
                    new_where = where_clause + f" and {{Card_Geo}}"
                else:
                    new_where = where_clause + f" and {{Card_Geo}}"
                updated_query = new_where + rest
                changes_made.append("added 'and {{Card_Geo}}' to WHERE clause")
        
        if not changes_made:
            return False, "No changes needed"
        
        # Update the card data
        native_query['template-tags'] = updated_template_tags
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
            return True, ", ".join(changes_made)
        else:
            return False, f"API error: {update_response.status_code} - {update_response.text}"
            
    except Exception as e:
        return False, f"Error: {str(e)}"

def main():
    """Main function"""
    dashboard_id = 485
    
    print(f"🔍 Checking for missing Card_Geo and CARD_ISOCOUNTRY filters on Dashboard {dashboard_id}...")
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
    
    # Check each card for missing filters
    print(f"\n🔍 Checking each card for missing filters...")
    
    cards_needing_update = []
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
        
        # Check if card needs filter updates
        needs_update, reasons = needs_filter_update(card_data)
        
        if needs_update:
            print(f"    ⚠️  Needs update: {', '.join(reasons)}")
            cards_needing_update.append({
                'card_id': card_id,
                'card_name': card_name,
                'reasons': reasons,
                'card_data': card_data
            })
        else:
            print(f"    ✅ No updates needed")
        
        cards_checked.append({
            'card_id': card_id,
            'card_name': card_name,
            'needs_update': needs_update,
            'reasons': reasons
        })
    
    # Update cards that need it
    if cards_needing_update:
        print(f"\n🔄 Updating {len(cards_needing_update)} cards with missing filters...")
        
        updated_cards = []
        failed_cards = []
        
        for i, card_info in enumerate(cards_needing_update):
            card_id = card_info['card_id']
            card_name = card_info['card_name']
            card_data = card_info['card_data']
            
            print(f"\n[{i+1}/{len(cards_needing_update)}] Updating: {card_name} (ID: {card_id})")
            
            success, message = update_card_with_filters(session_token, card_id, card_data)
            
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
        print(f"\n✅ All cards already have the required filters!")
    
    # Summary
    print(f"\n📈 Filter Check Summary:")
    print(f"Total cards checked: {len(cards_checked)}")
    print(f"Cards needing updates: {len(cards_needing_update)}")
    
    if cards_needing_update:
        print(f"Successfully updated: {len(updated_cards)} cards")
        print(f"Failed to update: {len(failed_cards)} cards")
        
        if updated_cards:
            print(f"\n✅ Successfully updated cards:")
            for card in updated_cards:
                print(f"  • {card['card_name']} (ID: {card['card_id']}) - {card['changes']}")
        
        if failed_cards:
            print(f"\n❌ Failed to update cards:")
            for card in failed_cards:
                print(f"  • {card['card_name']} (ID: {card['card_id']}) - {card['error']}")
    
    # Save results
    with open('dashboard_485_filter_check.json', 'w') as f:
        json.dump({
            "dashboard_id": dashboard_id,
            "dashboard_name": dashboard.get('name'),
            "cards_checked": cards_checked,
            "cards_needing_update": [{"card_id": c["card_id"], "card_name": c["card_name"], "reasons": c["reasons"]} for c in cards_needing_update],
            "updated_cards": updated_cards if 'updated_cards' in locals() else [],
            "failed_cards": failed_cards if 'failed_cards' in locals() else [],
            "total_cards": len(dashcards)
        }, f, indent=2)
    
    print(f"\n💾 Results saved to dashboard_485_filter_check.json")

if __name__ == "__main__":
    main() 