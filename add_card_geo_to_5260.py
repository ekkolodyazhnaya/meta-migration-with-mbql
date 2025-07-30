#!/usr/bin/env python3
"""
Script to add 'and {{Card_Geo}}' to card 5260's WHERE clause
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

def create_filter_template_tags():
    """Create the template tag configuration for Card_Geo"""
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
        }
    }

def update_card_5260_with_card_geo(session_token, card_id, card_data):
    """Update card 5260 to add Card_Geo template tag and 'and {{Card_Geo}}' to WHERE clause"""
    try:
        dataset_query = card_data.get('dataset_query', {})
        native_query = dataset_query.get('native', {})
        query_text = native_query.get('query', '')
        template_tags = native_query.get('template-tags', {})
        
        # Create filter template tags
        filter_tags = create_filter_template_tags()
        
        # Add Card_Geo template tag if not present
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
    card_id = 5260
    
    print(f"🔄 Adding Card_Geo filter to card {card_id}...")
    print("=" * 50)
    
    # Authenticate
    session_token = authenticate()
    if not session_token:
        return
    
    print("✅ Authentication successful")
    
    # Get card details
    print(f"\n📊 Fetching card {card_id} details...")
    card_data = get_card_details(session_token, card_id)
    if not card_data:
        return
    
    print(f"✅ Found card: {card_data.get('name', 'Unknown')}")
    
    # Show current query
    current_query = card_data.get('dataset_query', {}).get('native', {}).get('query', '')
    print(f"\n📋 Current SQL Query:")
    print(current_query)
    
    # Update the card
    print(f"\n🔄 Updating card {card_id}...")
    success, message = update_card_5260_with_card_geo(session_token, card_id, card_data)
    
    if success:
        print(f"✅ Success: {message}")
        
        # Show updated query
        updated_card = get_card_details(session_token, card_id)
        if updated_card:
            updated_query = updated_card.get('dataset_query', {}).get('native', {}).get('query', '')
            print(f"\n📋 Updated SQL Query:")
            print(updated_query)
    else:
        print(f"❌ Failed: {message}")

if __name__ == "__main__":
    main() 