#!/usr/bin/env python3
"""
Script to restore the complete SQL query for card 5260
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
    """Create the template tag configurations"""
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

def fix_card_5260_query(session_token, card_id, card_data):
    """Fix the SQL query for card 5260"""
    try:
        # The correct complete SQL query
        correct_query = """Select  
-- date_trunc('day',tr.CREATED_AT)
--  tr.ID 
-- ,rr.RATE                                            AS DAY_CLOSE
-- , sum(tr.REVENUE_EUR/rr.RATE) as Revenue_USD
-- , sum(tr.GMV_EUR/rr.RATE) as GMV_USD
 round(sum(TOTAL_TRANSACTION_COSTS_EUR*cast(rr.RATE as DECIMAL(18,6))), 0) as "Costs"
--  sum(TOTAL_TRANSACTION_COSTS_EUR/rr.RATE) as TRANSACTION_COST
-- , CARD_ISOCOUNTRY
-- , CURRENCY
-- , PAY_SYSTEM
-- , CARD_BRAND
-- , WIDGET_PARTNER_NAME
from MART__TRANSACTIONS
LEFT JOIN RATES__CURRENCY_RATES_PER_DAY___MART as rr
                                         on rr.FROM_CURRENCY = 'EUR' and
                                            rr.TO_CURRENCY = 'USD' and
                                            rr.dt = date_trunc('day',MART__TRANSACTIONS.CREATED_AT) and
                                            rr.RATES_SOURCE = 'YAHOO_FINANCE'
where {{CARD_ISOCOUNTRY}} and CONFIRMED
and {{CREATED_AT}}
and {{PAY_SYSTEM}} and {{WIDGET_PARTNER_NAME}} and {{CURRENCY}} and {{CRYPTO}} and {{TYPE}} and {{CARD_BIN}}
and {{Card_Geo}}"""
        
        # Create all template tags
        template_tags = create_filter_template_tags()
        
        # Update the card data
        dataset_query = card_data.get('dataset_query', {})
        native_query = dataset_query.get('native', {})
        native_query['query'] = correct_query
        native_query['template-tags'] = template_tags
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
            return True, "Successfully restored complete SQL query with all filters"
        else:
            return False, f"API error: {update_response.status_code} - {update_response.text}"
            
    except Exception as e:
        return False, f"Error: {str(e)}"

def main():
    """Main function"""
    card_id = 5260
    
    print(f"🔄 Fixing SQL query for card {card_id}...")
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
    
    # Show current broken query
    current_query = card_data.get('dataset_query', {}).get('native', {}).get('query', '')
    print(f"\n📋 Current broken SQL Query:")
    print(current_query)
    
    # Fix the card
    print(f"\n🔄 Fixing card {card_id}...")
    success, message = fix_card_5260_query(session_token, card_id, card_data)
    
    if success:
        print(f"✅ Success: {message}")
        
        # Show fixed query
        updated_card = get_card_details(session_token, card_id)
        if updated_card:
            updated_query = updated_card.get('dataset_query', {}).get('native', {}).get('query', '')
            print(f"\n📋 Fixed SQL Query:")
            print(updated_query)
    else:
        print(f"❌ Failed: {message}")

if __name__ == "__main__":
    main() 