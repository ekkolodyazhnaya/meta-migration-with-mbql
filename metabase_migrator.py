#!/usr/bin/env python3
"""
Metabase Dashboard Migration Tool
Migrates dashboards from Exasol to StarRocks while preserving filters and variables.
"""

import requests
import json
import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import urljoin

from config import METABASE_CONFIG, DATABASE_MAPPINGS, MIGRATION_SETTINGS
from sql_converter import SQLConverter

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class MetabaseConfig:
    """Configuration for Metabase connection"""
    base_url: str
    username: str
    password: str

class MetabaseMigrator:
    def __init__(self, config: MetabaseConfig):
        self.config = config
        self.session = requests.Session()
        self.session_token = None
        self.sql_converter = SQLConverter()
        
    def authenticate(self) -> bool:
        """Authenticate with Metabase and get session token"""
        try:
            login_data = {
                "username": self.config.username,
                "password": self.config.password
            }
            
            response = self.session.post(
                urljoin(self.config.base_url, "/api/session"),
                json=login_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                self.session_token = response.json().get("id")
                logger.info("Successfully authenticated with Metabase")
                return True
            else:
                logger.error(f"Authentication failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return False
    
    def get_dashboards(self) -> List[Dict]:
        """Get all dashboards from Metabase"""
        try:
            response = self.session.get(
                urljoin(self.config.base_url, "/api/dashboard"),
                headers={"X-Metabase-Session": self.session_token}
            )
            
            if response.status_code == 200:
                dashboards = response.json()
                logger.info(f"Found {len(dashboards)} dashboards")
                return dashboards
            else:
                logger.error(f"Failed to get dashboards: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting dashboards: {str(e)}")
            return []
    
    def get_dashboard_details(self, dashboard_id: int) -> Optional[Dict]:
        """Get detailed information about a specific dashboard"""
        try:
            response = self.session.get(
                urljoin(self.config.base_url, f"/api/dashboard/{dashboard_id}"),
                headers={"X-Metabase-Session": self.session_token}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get dashboard {dashboard_id}: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting dashboard details: {str(e)}")
            return None
    
    def get_question_details(self, question_id: int) -> Optional[Dict]:
        """Get detailed information about a specific question"""
        try:
            response = self.session.get(
                urljoin(self.config.base_url, f"/api/card/{question_id}"),
                headers={"X-Metabase-Session": self.session_token}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get question {question_id}: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting question details: {str(e)}")
            return None
    
    def migrate_native_question(self, question: Dict) -> Dict:
        """Migrate a native SQL question from Exasol to StarRocks"""
        try:
            question_id = question.get('id')
            question_details = self.get_question_details(question_id)
            
            if not question_details:
                return {"error": f"Could not get details for question {question_id}"}
            
            original_sql = question_details.get('dataset_query', {}).get('native', {}).get('query', '')
            
            if not original_sql:
                return {"error": f"No SQL found in question {question_id}"}
            
            # Extract variables before conversion
            variables = self.sql_converter.extract_variables(original_sql)
            
            # Convert SQL using the dedicated converter
            converted_sql = self.sql_converter.convert_sql(original_sql)
            
            # Validate conversion
            validation = self.sql_converter.validate_conversion(original_sql, converted_sql)
            
            return {
                "question_id": question_id,
                "question_name": question.get('name', 'Unknown'),
                "original_sql": original_sql if MIGRATION_SETTINGS["backup_original_sql"] else None,
                "converted_sql": converted_sql,
                "variables": variables,
                "type": "native",
                "validation": validation
            }
            
        except Exception as e:
            logger.error(f"Error migrating native question {question.get('id')}: {str(e)}")
            return {"error": str(e)}
    
    def migrate_mbql_question(self, question: Dict) -> Dict:
        import logging
        try:
            question_id = question.get('id')
            question_details = self.get_question_details(question_id)
            if not question_details:
                return {"error": f"Could not get details for question {question_id}"}

            mbql_query = question_details.get('dataset_query', {}).get('query', {})
            # Load migration mapping
            with open('migrations/migration_mapping.json', 'r') as f:
                migration_mapping = json.load(f)
            column_mapping = migration_mapping.get('column_mapping', {})

            # Recursively map field IDs in MBQL
            def map_field_ids(obj):
                if isinstance(obj, list):
                    return [map_field_ids(x) for x in obj]
                elif isinstance(obj, dict):
                    # Map field IDs
                    if 'field' in obj and isinstance(obj['field'], int):
                        str_id = str(obj['field'])
                        if str_id in column_mapping:
                            obj['field'] = column_mapping[str_id]
                    # Map join-alias field IDs
                    if 'join-alias' in obj and isinstance(obj['join-alias'], int):
                        str_id = str(obj['join-alias'])
                        if str_id in column_mapping:
                            obj['join-alias'] = column_mapping[str_id]
                    return {k: map_field_ids(v) for k, v in obj.items()}
                else:
                    return obj

            migrated_mbql = map_field_ids(mbql_query)

            # Update main and join table IDs directly
            migrated_mbql['source-table'] = 87255  # MART__TRANSACTIONS
            if 'joins' in migrated_mbql:
                for join in migrated_mbql['joins']:
                    join['source-table'] = 91055  # EIGHTB_WORLD__ACQUIRING_WP_MONEYMAPLETECHLTD

            # Update database
            question_details['dataset_query']['database'] = 16  # StarRocks DB ID
            question_details['dataset_query']['query'] = migrated_mbql

            resp = self.session.put(
                f"{self.config.base_url}/api/card/{question_id}",
                headers={"X-Metabase-Session": self.session_token, "Content-Type": "application/json"},
                json={
                    "dataset_query": question_details['dataset_query'],
                    "visualization_settings": question_details.get('visualization_settings', {})
                }
            )
            print(f"[DEBUG] Metabase API response: {resp.status_code} {resp.text}")
            if resp.status_code == 200:
                return {"success": f"Question {question_id} migrated to StarRocks with full field and table mapping."}
            else:
                return {"error": f"Failed to update question {question_id}: {resp.text}"}
        except Exception as e:
            print(f"[DEBUG] Exception: {str(e)}")
            return {"error": str(e)}
    
    def migrate_dashboard(self, dashboard: Dict) -> Dict:
        """Migrate an entire dashboard"""
        dashboard_id = dashboard.get('id')
        dashboard_name = dashboard.get('name', 'Unknown')
        
        logger.info(f"Migrating dashboard: {dashboard_name} (ID: {dashboard_id})")
        
        # Get detailed dashboard information
        dashboard_details = self.get_dashboard_details(dashboard_id)
        if not dashboard_details:
            return {"error": f"Could not get details for dashboard {dashboard_id}"}
        
        # Extract questions from dashboard - use 'dashcards' instead of 'ordered_cards'
        questions = []
        dashcards = dashboard_details.get('dashcards', [])
        
        for dashcard in dashcards:
            card_details = dashcard.get('card', {})
            if card_details:
                questions.append(card_details)
        
        # Migrate each question
        migrated_questions = []
        for question in questions:
            question_type = question.get('dataset_query', {}).get('type', 'unknown')
            
            if question_type == 'native':
                migrated_question = self.migrate_native_question(question)
            elif question_type == 'query':
                migrated_question = self.migrate_mbql_question(question)
            else:
                migrated_question = {
                    "question_id": question.get('id'),
                    "question_name": question.get('name', 'Unknown'),
                    "type": question_type,
                    "note": f"Unsupported question type: {question_type}"
                }
            
            migrated_questions.append(migrated_question)
        
        return {
            "dashboard_id": dashboard_id,
            "dashboard_name": dashboard_name,
            "questions": migrated_questions,
            "total_questions": len(migrated_questions),
            "migration_timestamp": self._get_timestamp()
        }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for migration tracking"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def migrate_all_dashboards(self) -> List[Dict]:
        """Migrate all dashboards"""
        if not self.authenticate():
            return [{"error": "Authentication failed"}]
        
        dashboards = self.get_dashboards()
        if not dashboards:
            return [{"error": "No dashboards found"}]
        
        migrated_dashboards = []
        for dashboard in dashboards:
            migrated_dashboard = self.migrate_dashboard(dashboard)
            migrated_dashboards.append(migrated_dashboard)
        
        return migrated_dashboards
    
    def save_migration_results(self, results: List[Dict], filename: str = "migration_results.json"):
        """Save migration results to a JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            logger.info(f"Migration results saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving migration results: {str(e)}")
    
    def generate_summary_report(self, results: List[Dict]) -> Dict:
        """Generate a summary report of the migration"""
        summary = {
            "total_dashboards": 0,
            "total_questions": 0,
            "native_questions": 0,
            "mbql_questions": 0,
            "successful_conversions": 0,
            "failed_conversions": 0,
            "errors": [],
            "warnings": []
        }
        
        for result in results:
            if "error" in result:
                summary["errors"].append(result["error"])
                continue
            
            summary["total_dashboards"] += 1
            questions = result.get("questions", [])
            summary["total_questions"] += len(questions)
            
            for question in questions:
                if "error" in question:
                    summary["failed_conversions"] += 1
                    summary["errors"].append(f"Question {question.get('question_name', 'Unknown')}: {question['error']}")
                else:
                    summary["successful_conversions"] += 1
                    question_type = question.get("type", "unknown")
                    
                    if question_type == "native":
                        summary["native_questions"] += 1
                    elif question_type == "mbql":
                        summary["mbql_questions"] += 1
                    
                    # Check for validation warnings
                    validation = question.get("validation", {})
                    if validation.get("warnings"):
                        summary["warnings"].extend(validation["warnings"])
        
        return summary

def main():
    """Main function to run the migration"""
    config = MetabaseConfig(
        base_url=METABASE_CONFIG["base_url"],
        username=METABASE_CONFIG["username"],
        password=METABASE_CONFIG["password"]
    )
    
    migrator = MetabaseMigrator(config)
    
    print("🚀 Starting Metabase migration from Exasol to StarRocks...")
    print("=" * 60)
    
    # Run migration
    results = migrator.migrate_all_dashboards()
    
    # Generate summary
    summary = migrator.generate_summary_report(results)
    
    # Save results
    migrator.save_migration_results(results)
    
    # Print summary
    print("\n📊 Migration Summary:")
    print("=" * 60)
    print(f"📈 Total Dashboards: {summary['total_dashboards']}")
    print(f"❓ Total Questions: {summary['total_questions']}")
    print(f"📝 Native Questions: {summary['native_questions']}")
    print(f"🔧 MBQL Questions: {summary['mbql_questions']}")
    print(f"✅ Successful Conversions: {summary['successful_conversions']}")
    print(f"❌ Failed Conversions: {summary['failed_conversions']}")
    
    if summary["warnings"]:
        print(f"\n⚠️  Warnings ({len(summary['warnings'])}):")
        for warning in summary["warnings"][:5]:  # Show first 5 warnings
            print(f"   • {warning}")
        if len(summary["warnings"]) > 5:
            print(f"   ... and {len(summary['warnings']) - 5} more")
    
    if summary["errors"]:
        print(f"\n❌ Errors ({len(summary['errors'])}):")
        for error in summary["errors"][:5]:  # Show first 5 errors
            print(f"   • {error}")
        if len(summary["errors"]) > 5:
            print(f"   ... and {len(summary['errors']) - 5} more")
    
    print(f"\n📄 Detailed results saved to migration_results.json")
    print("🎉 Migration completed!")

if __name__ == "__main__":
    main() 