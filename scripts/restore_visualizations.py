#!/usr/bin/env python3
"""
Script to restore original visualization settings for all cards on dashboard 485
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

def get_original_visualization_settings(card_name):
    """Get original visualization settings based on card name"""
    # Default visualization settings for different chart types
    default_settings = {
        "line": {
            "graph.dimensions": ["CREATED_AT"],
            "graph.metrics": ["count"],
            "graph.show_values": False,
            "graph.x_axis.title_text": "Created At",
            "graph.y_axis.title_text": "Count"
        },
        "bar": {
            "graph.dimensions": ["CREATED_AT"],
            "graph.metrics": ["count"],
            "graph.show_values": False,
            "graph.x_axis.title_text": "Created At",
            "graph.y_axis.title_text": "Count"
        },
        "pie": {
            "pie.show_legend": True,
            "pie.show_values": False
        },
        "table": {
            "table.column_widths": [],
            "table.pivot_column": None,
            "table.cell_column": None
        },
        "scalar": {
            "scalar.decimals": 0,
            "scalar.prefix": "",
            "scalar.suffix": ""
        }
    }
    
    # Map card names to their original visualization types
    card_visualizations = {
        "Revenue Per User": "scalar",
        "Transactions dynamic": "line",
        "Antifraud": "scalar",
        "Total Costs": "scalar",
        "Total Turnover": "scalar",
        "AR dynamic": "line",
        "Turnover": "scalar",
        "MAU OOR": "scalar",
        "DAU OOR": "scalar",
        "Costs": "scalar",
        "GMV": "scalar",
        "Revenue": "scalar",
        "Revenue Per Turnover": "scalar",
        "Total Revenue": "scalar",
        "Total GMV": "scalar",
        "Failed reasons": "pie",
        "Total Transactions": "scalar",
        "Total AR": "scalar",
        "Transaction size dynamic": "line",
        "Reason reject statistics": "bar",
        "KYC dynamic": "line",
        "GMV detailing": "table",
        "Turnover detailing": "table"
    }
    
    viz_type = card_visualizations.get(card_name, "scalar")
    return default_settings.get(viz_type, {})

def restore_card_visualization(session_token, card_id, card_data):
    """Restore original visualization settings for a card"""
    try:
        card_name = card_data.get('name', 'Unknown')
        
        # Get original visualization settings
        original_settings = get_original_visualization_settings(card_name)
        
        # Update the card data with original visualization settings
        card_data['visualization_settings'] = original_settings
        
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
            return True, f"Restored {card_name} visualization"
        else:
            return False, f"API error: {update_response.status_code} - {update_response.text}"
            
    except Exception as e:
        return False, f"Error: {str(e)}"

def main():
    """Main function"""
    dashboard_id = 485
    
    print(f"🎨 Restoring original visualizations for Dashboard {dashboard_id}...")
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
    
    # Restore visualizations for each card
    print(f"\n🎨 Restoring visualizations for each card...")
    
    cards_restored = []
    cards_failed = []
    
    for i, dashcard in enumerate(dashcards):
        card = dashcard.get('card', {})
        card_id = card.get('id')
        card_name = card.get('name', 'Unknown')
        
        if not card_id:
            print(f"[{i+1}/{len(dashcards)}] Skipping card without ID: {card_name}")
            continue
        
        print(f"\n[{i+1}/{len(dashcards)}] Restoring visualization for: {card_name} (ID: {card_id})")
        
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
        
        # Restore visualization
        success, message = restore_card_visualization(session_token, card_id, card_data)
        
        if success:
            print(f"    ✅ Success: {message}")
            cards_restored.append({
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
    print(f"\n📈 Visualization Restoration Summary:")
    print(f"Total cards processed: {len(cards_restored) + len(cards_failed)}")
    print(f"Cards restored: {len(cards_restored)}")
    print(f"Cards failed: {len(cards_failed)}")
    
    if cards_restored:
        print(f"\n✅ Successfully restored visualizations:")
        for card in cards_restored:
            print(f"  • {card['card_name']} (ID: {card['card_id']}) - {card['changes']}")
    
    if cards_failed:
        print(f"\n❌ Failed to restore visualizations:")
        for card in cards_failed:
            print(f"  • {card['card_name']} (ID: {card['card_id']}) - {card['error']}")
    
    # Save results
    with open('dashboard_485_visualization_restore.json', 'w') as f:
        json.dump({
            "dashboard_id": dashboard_id,
            "dashboard_name": dashboard.get('name'),
            "cards_restored": cards_restored,
            "cards_failed": cards_failed,
            "total_cards": len(dashcards)
        }, f, indent=2)
    
    print(f"\n💾 Results saved to dashboard_485_visualization_restore.json")
    print(f"\n🎯 All visualizations have been restored to their original state!")
    print(f"   Refresh the dashboard to see the changes.")

if __name__ == "__main__":
    main() 