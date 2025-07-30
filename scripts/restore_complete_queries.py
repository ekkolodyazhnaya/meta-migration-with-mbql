#!/usr/bin/env python3
"""
Script to restore complete SQL queries for all cards that lost their SELECT and FROM clauses
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

def get_complete_query_for_card(card_name):
    """Get the complete SQL query template based on card name"""
    base_query = """Select  
{select_clause}
from MART__TRANSACTIONS
LEFT JOIN RATES__CURRENCY_RATES_PER_DAY___MART as rr
                                         on rr.FROM_CURRENCY = 'EUR' and
                                            rr.TO_CURRENCY = 'USD' and
                                            rr.dt = date_trunc('day',MART__TRANSACTIONS.CREATED_AT) and
                                            rr.RATES_SOURCE = 'YAHOO_FINANCE'
where CONFIRMED
and TYPE_MAIN = 'buy' and
      SOURCE_MAIN = 'widget'
and {{CREATED_AT}}
and {{PAY_SYSTEM}} and {{WIDGET_PARTNER_NAME}} and {{CURRENCY}} and {{CRYPTO}} and {{TYPE}} and {{CARD_BIN}}
and {{Card_Geo}} and {{CARD_ISOCOUNTRY}}
{group_by_clause}"""
    
    # Define select clauses for different card types
    select_clauses = {
        'Revenue Per User': 'round(sum(MART__TRANSACTIONS.REVENUE_EUR*cast(rr.RATE as DECIMAL(18,6))), 0) as "Revenue Per User"',
        'Transactions dynamic': 'date_trunc(\'day\',MART__TRANSACTIONS.CREATED_AT) as "Date", count(*) as "Transactions"',
        'Antifraud': 'round(sum(MART__TRANSACTIONS.ANTIFRAUD_COST_EUR*cast(rr.RATE as DECIMAL(18,6))), 0) as "Antifraud"',
        'AR dynamic': 'date_trunc(\'day\',MART__TRANSACTIONS.CREATED_AT) as "Date", round(sum(MART__TRANSACTIONS.REVENUE_EUR*cast(rr.RATE as DECIMAL(18,6))), 0) as "AR"',
        'Turnover': 'round(sum(MART__TRANSACTIONS.TURNOVER_EUR*cast(rr.RATE as DECIMAL(18,6))), 0) as "Turnover"',
        'MAU OOR': 'count(distinct case when date_trunc(\'month\', MART__TRANSACTIONS.CREATED_AT) = date_trunc(\'month\', current_date) then MART__TRANSACTIONS.USER_ID end) as "MAU OOR"',
        'DAU OOR': 'count(distinct case when date_trunc(\'day\', MART__TRANSACTIONS.CREATED_AT) = date_trunc(\'day\', current_date) then MART__TRANSACTIONS.USER_ID end) as "DAU OOR"',
        'Costs': 'round(sum(MART__TRANSACTIONS.TOTAL_TRANSACTION_COSTS_EUR*cast(rr.RATE as DECIMAL(18,6))), 0) as "Costs"',
        'GMV': 'round(sum(MART__TRANSACTIONS.GMV_EUR*cast(rr.RATE as DECIMAL(18,6))), 0) as "GMV"',
        'Revenue': 'round(sum(MART__TRANSACTIONS.REVENUE_EUR*cast(rr.RATE as DECIMAL(18,6))), 0) as "Revenue"',
        'Revenue Per Turnover': 'round(sum(MART__TRANSACTIONS.REVENUE_EUR*cast(rr.RATE as DECIMAL(18,6))) / sum(MART__TRANSACTIONS.TURNOVER_EUR*cast(rr.RATE as DECIMAL(18,6))) * 100, 2) as "Revenue Per Turnover"',
        'Total Revenue': 'round(sum(MART__TRANSACTIONS.REVENUE_EUR*cast(rr.RATE as DECIMAL(18,6))), 0) as "Total Revenue"',
        'Total GMV': 'round(sum(MART__TRANSACTIONS.GMV_EUR*cast(rr.RATE as DECIMAL(18,6))), 0) as "Total GMV"',
        'Failed reasons': 'MART__TRANSACTIONS.FAILED_REASON as "Failed Reason", count(*) as "Count"',
        'Total Transactions': 'count(*) as "Total Transactions"',
        'Total AR': 'round(sum(MART__TRANSACTIONS.REVENUE_EUR*cast(rr.RATE as DECIMAL(18,6))), 0) as "Total AR"',
        'Transaction size dynamic': 'date_trunc(\'day\',MART__TRANSACTIONS.CREATED_AT) as "Date", round(avg(MART__TRANSACTIONS.TURNOVER_EUR*cast(rr.RATE as DECIMAL(18,6))), 2) as "Transaction Size"',
        'Reason reject statistics': 'MART__TRANSACTIONS.REJECT_REASON as "Reject Reason", count(*) as "Count"',
        'KYC dynamic': 'date_trunc(\'day\',MART__TRANSACTIONS.CREATED_AT) as "Date", count(*) as "KYC"',
        'GMV detailing': 'MART__TRANSACTIONS.CURRENCY as "Currency", round(sum(MART__TRANSACTIONS.GMV_EUR*cast(rr.RATE as DECIMAL(18,6))), 0) as "GMV"',
        'Turnover detailing': 'MART__TRANSACTIONS.CURRENCY as "Currency", round(sum(MART__TRANSACTIONS.TURNOVER_EUR*cast(rr.RATE as DECIMAL(18,6))), 0) as "Turnover"'
    }
    
    # Define group by clauses for cards that need them
    group_by_clauses = {
        'Transactions dynamic': 'group by date_trunc(\'day\',MART__TRANSACTIONS.CREATED_AT)',
        'AR dynamic': 'group by date_trunc(\'day\',MART__TRANSACTIONS.CREATED_AT)',
        'Failed reasons': 'group by MART__TRANSACTIONS.FAILED_REASON',
        'Transaction size dynamic': 'group by date_trunc(\'day\',MART__TRANSACTIONS.CREATED_AT)',
        'Reason reject statistics': 'group by MART__TRANSACTIONS.REJECT_REASON',
        'KYC dynamic': 'group by date_trunc(\'day\',MART__TRANSACTIONS.CREATED_AT)',
        'GMV detailing': 'group by MART__TRANSACTIONS.CURRENCY',
        'Turnover detailing': 'group by MART__TRANSACTIONS.CURRENCY'
    }
    
    select_clause = select_clauses.get(card_name, 'count(*) as "Count"')
    group_by_clause = group_by_clauses.get(card_name, '')
    
    return base_query.format(select_clause=select_clause, group_by_clause=group_by_clause)

def restore_complete_query(session_token, card_id, card_data):
    """Restore the complete SQL query for a card"""
    try:
        card_name = card_data.get('name', 'Unknown')
        
        # Get the complete query template
        complete_query = get_complete_query_for_card(card_name)
        
        # Create all template tags
        template_tags = create_filter_template_tags()
        
        # Update the card data
        dataset_query = card_data.get('dataset_query', {})
        native_query = dataset_query.get('native', {})
        native_query['query'] = complete_query
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
            return True, f"Restored complete SQL query for {card_name}"
        else:
            return False, f"API error: {update_response.status_code} - {update_response.text}"
            
    except Exception as e:
        return False, f"Error: {str(e)}"

def main():
    """Main function"""
    # List of card IDs that need to be fixed (the ones that lost their SELECT/FROM clauses)
    cards_to_fix = [
        5267,  # Revenue Per User
        5256,  # Transactions dynamic
        5259,  # Antifraud
        5274,  # AR dynamic
        5253,  # Turnover
        5257,  # MAU OOR
        5252,  # DAU OOR
        5258,  # Costs
        5273,  # GMV
        5270,  # Revenue
        5268,  # Revenue Per Turnover
        5271,  # Total Revenue
        5263,  # Total GMV
        5264,  # Failed reasons
        5266,  # Total Transactions
        5272,  # Total AR
        5269,  # Transaction size dynamic
        5262,  # Reason reject statistics
        5265,  # KYC dynamic
        5255,  # GMV detailing
        5261   # Turnover detailing
    ]
    
    print(f"🔄 Restoring complete SQL queries for {len(cards_to_fix)} cards...")
    print("=" * 60)
    
    # Authenticate
    session_token = authenticate()
    if not session_token:
        return
    
    print("✅ Authentication successful")
    
    # Fix each card
    updated_cards = []
    failed_cards = []
    
    for i, card_id in enumerate(cards_to_fix):
        print(f"\n[{i+1}/{len(cards_to_fix)}] Processing card ID: {card_id}")
        
        # Get card details
        card_data = get_card_details(session_token, card_id)
        if not card_data:
            print(f"    ❌ Failed to fetch card details")
            failed_cards.append({
                'card_id': card_id,
                'card_name': 'Unknown',
                'error': 'Failed to fetch card details'
            })
            continue
        
        card_name = card_data.get('name', 'Unknown')
        print(f"    📋 Card: {card_name}")
        
        # Show current broken query
        current_query = card_data.get('dataset_query', {}).get('native', {}).get('query', '')
        print(f"    📋 Current broken query (first 100 chars): {current_query[:100]}...")
        
        # Restore the complete query
        success, message = restore_complete_query(session_token, card_id, card_data)
        
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
    
    # Summary
    print(f"\n📈 Query Restoration Summary:")
    print(f"Total cards processed: {len(cards_to_fix)}")
    print(f"Successfully restored: {len(updated_cards)} cards")
    print(f"Failed to restore: {len(failed_cards)} cards")
    
    if updated_cards:
        print(f"\n✅ Successfully restored cards:")
        for card in updated_cards:
            print(f"  • {card['card_name']} (ID: {card['card_id']}) - {card['changes']}")
    
    if failed_cards:
        print(f"\n❌ Failed to restore cards:")
        for card in failed_cards:
            print(f"  • {card['card_name']} (ID: {card['card_id']}) - {card['error']}")
    
    # Save results
    with open('dashboard_485_query_restoration.json', 'w') as f:
        json.dump({
            "cards_processed": len(cards_to_fix),
            "updated_cards": updated_cards,
            "failed_cards": failed_cards
        }, f, indent=2)
    
    print(f"\n💾 Results saved to dashboard_485_query_restoration.json")

if __name__ == "__main__":
    main() 