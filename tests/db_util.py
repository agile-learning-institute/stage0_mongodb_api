#!/usr/bin/env python3
"""
Database utility for testing purposes.

This module provides utilities for:
- Dropping the entire database (for testing cleanup)
- Comparing database contents with JSON files
- Harvesting database contents to JSON files

WARNING: This module is for testing only and should never be deployed to production.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from bson import ObjectId, json_util

# Add the project root to the path so we can import stage0_py_utils
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from stage0_py_utils import Config, MongoIO


class DatabaseUtil:
    """Database utility class for testing operations."""
    
    def __init__(self):
        """Initialize the database utility."""
        self.config = Config.get_instance()
        self.mongo = MongoIO.get_instance()
        self.db_name = self.config.MONGO_DB_NAME
        
    def drop_database(self, passphrase: Optional[str] = None) -> Dict[str, Any]:
        """Drop the entire database.
        
        WARNING: This will permanently delete all data in the database.
        
        Args:
            passphrase: Optional passphrase to skip confirmation prompt
            
        Returns:
            Dict containing operation result
        """
        try:
            # Check passphrase if provided
            if passphrase:
                expected_passphrase = "DROP_DROWSSAP_YEK"
                if passphrase != expected_passphrase:
                    return {
                        "operation": "drop_database",
                        "database": self.db_name,
                        "error": "Invalid passphrase",
                        "timestamp": datetime.now().isoformat(),
                        "status": "error"
                    }
            else:
                # Require manual confirmation if no passphrase
                print("⚠️  WARNING: This will permanently delete all data in the database!")
                confirm = input("Type 'YES' to confirm: ")
                if confirm != "YES":
                    return {
                        "operation": "drop_database",
                        "database": self.db_name,
                        "timestamp": datetime.now().isoformat(),
                        "status": "cancelled"
                    }
            
            # Get the database object
            db = self.mongo.client[self.db_name]
            
            # Drop the database
            self.mongo.client.drop_database(self.db_name)
            
            print(f"✅ Database '{self.db_name}' dropped successfully")
            
            return {
                "operation": "drop_database",
                "database": self.db_name,
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            }
            
        except Exception as e:
            error_msg = f"Failed to drop database '{self.db_name}': {str(e)}"
            print(f"❌ {error_msg}")
            
            return {
                "operation": "drop_database",
                "database": self.db_name,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "status": "error"
            }
    
    def compare_database_with_files(self) -> Dict[str, Any]:
        """Compare database contents with JSON files.
        
        Returns:
            Dict containing comparison results
        """
        try:
            base_path = os.path.join(self.config.INPUT_FOLDER, self.db_name)
            base_path = Path(base_path)
            if not base_path.exists():
                raise ValueError(f"Base path does not exist: {base_path}")
            
            results = {
                "operation": "compare_database",
                "database": self.db_name,
                "comparisons": [],
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            }
            
            # Get all collections in the database
            db = self.mongo.client[self.db_name]
            collections = db.list_collection_names()
            
            # Find JSON files that match collection names
            json_files = list(base_path.glob("*.json"))
            
            for json_file in json_files:
                # Extract collection name from filename (e.g., "user.1.0.0.1.json" -> "user")
                collection_name = json_file.stem.split('.')[0]
                
                if collection_name in collections:
                    comparison = self._compare_collection_with_file(collection_name, json_file)
                    results["comparisons"].append(comparison)
                else:
                    results["comparisons"].append({
                        "collection": collection_name,
                        "file": str(json_file),
                        "status": "collection_not_found",
                        "message": f"Collection '{collection_name}' not found in database"
                    })
            
            # Check for collections without corresponding files
            for collection in collections:
                if not any(collection in str(f) for f in json_files):
                    results["comparisons"].append({
                        "collection": collection,
                        "file": None,
                        "status": "file_not_found",
                        "message": f"No JSON file found for collection '{collection}'"
                    })
            
            return results
            
        except Exception as e:
            return {
                "operation": "compare_database",
                "database": self.db_name,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "status": "error"
            }
    
    def _compare_collection_with_file(self, collection_name: str, json_file: Path) -> Dict[str, Any]:
        """Compare a single collection with its corresponding JSON file.
        
        Args:
            collection_name: Name of the collection
            json_file: Path to the JSON file
            
        Returns:
            Dict containing comparison result
        """
        try:
            # Load expected data from JSON file
            with open(json_file, 'r') as f:
                expected_data = json.load(f)
            
            # Get actual data from database
            collection = self.mongo.client[self.db_name][collection_name]
            actual_data = list(collection.find({}))
            
            # Convert ObjectIds to strings for comparison
            actual_data = json.loads(json_util.dumps(actual_data))
            
            # Compare document counts
            expected_count = len(expected_data)
            actual_count = len(actual_data)
            
            if expected_count != actual_count:
                return {
                    "collection": collection_name,
                    "file": str(json_file),
                    "status": "count_mismatch",
                    "expected_count": expected_count,
                    "actual_count": actual_count,
                    "message": f"Document count mismatch: expected {expected_count}, got {actual_count}"
                }
            
            # Compare documents (simplified - could be enhanced for deep comparison)
            matches = 0
            mismatches = []
            
            for i, (expected, actual) in enumerate(zip(expected_data, actual_data)):
                if self._documents_match(expected, actual):
                    matches += 1
                else:
                    mismatches.append({
                        "index": i,
                        "expected": expected,
                        "actual": actual
                    })
            
            if matches == expected_count:
                return {
                    "collection": collection_name,
                    "file": str(json_file),
                    "status": "match",
                    "document_count": expected_count,
                    "message": f"All {expected_count} documents match"
                }
            else:
                return {
                    "collection": collection_name,
                    "file": str(json_file),
                    "status": "content_mismatch",
                    "document_count": expected_count,
                    "matches": matches,
                    "mismatches": len(mismatches),
                    "mismatch_details": mismatches[:5],  # Limit to first 5 mismatches
                    "message": f"{matches}/{expected_count} documents match"
                }
                
        except Exception as e:
            return {
                "collection": collection_name,
                "file": str(json_file),
                "status": "error",
                "error": str(e),
                "message": f"Error comparing collection: {str(e)}"
            }
    
    def _documents_match(self, expected: Dict, actual: Dict) -> bool:
        """Compare two documents for equality.
        
        Args:
            expected: Expected document
            actual: Actual document
            
        Returns:
            True if documents match, False otherwise
        """
        # Remove _id field for comparison (it's auto-generated)
        expected_copy = {k: v for k, v in expected.items() if k != '_id'}
        actual_copy = {k: v for k, v in actual.items() if k != '_id'}
        
        return expected_copy == actual_copy
    
    def harvest_database(self, output_path: Optional[str] = None) -> Dict[str, Any]:
        """Harvest all database contents to JSON files.
        
        Args:
            output_path: Directory to save harvested JSON files (defaults to input folder)
            
        Returns:
            Dict containing harvest results
        """
        try:
            if output_path is None:
                output_path = os.path.join(self.config.INPUT_FOLDER, self.db_name)
            
            output_path = Path(output_path)
            
            # Check if files already exist and prompt for replacement
            existing_files = []
            for collection_name in self.mongo.client[self.db_name].list_collection_names():
                potential_file = output_path / f"{collection_name}.json"
                if potential_file.exists():
                    existing_files.append(str(potential_file))
            
            if existing_files:
                print(f"⚠️  Found existing files in {output_path}:")
                for file in existing_files:
                    print(f"   - {file}")
                confirm = input("Replace existing files? (y/N): ")
                if confirm.lower() not in ['y', 'yes']:
                    return {
                        "operation": "harvest_database",
                        "database": self.db_name,
                        "output_path": str(output_path),
                        "message": "Operation cancelled by user",
                        "timestamp": datetime.now().isoformat(),
                        "status": "cancelled"
                    }
            
            output_path.mkdir(parents=True, exist_ok=True)
            
            results = {
                "operation": "harvest_database",
                "database": self.db_name,
                "output_path": str(output_path),
                "collections": [],
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            }
            
            # Get all collections
            db = self.mongo.client[self.db_name]
            collections = db.list_collection_names()
            
            for collection_name in collections:
                collection_result = self._harvest_collection(collection_name, output_path)
                results["collections"].append(collection_result)
            
            print(f"✅ Database harvested to {output_path}")
            return results
            
        except Exception as e:
            return {
                "operation": "harvest_database",
                "database": self.db_name,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "status": "error"
            }
    
    def _harvest_collection(self, collection_name: str, output_path: Path) -> Dict[str, Any]:
        """Harvest a single collection to a JSON file.
        
        Args:
            collection_name: Name of the collection
            output_path: Directory to save the file
            
        Returns:
            Dict containing harvest result
        """
        try:
            # Get all documents from collection
            collection = self.mongo.client[self.db_name][collection_name]
            documents = list(collection.find({}))
            
            # Convert to JSON-serializable format
            json_data = json.loads(json_util.dumps(documents, default=str))
            
            # Save to file
            output_file = output_path / f"{collection_name}.json"
            with open(output_file, 'w') as f:
                json.dump(json_data, f, indent=2, default=str)
            
            return {
                "collection": collection_name,
                "file": str(output_file),
                "document_count": len(documents),
                "status": "success"
            }
            
        except Exception as e:
            return {
                "collection": collection_name,
                "error": str(e),
                "status": "error"
            }


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Database utility for testing")
    parser.add_argument("command", choices=["drop", "compare", "harvest"], 
                       help="Command to execute")
    parser.add_argument("--output-path", 
                       help="Output path for harvested data (defaults to input folder / database name)")
    parser.add_argument("--passphrase", 
                       help="Passphrase for silent database drop: DROP_DROWSSAP_YEK")
    
    args = parser.parse_args()
    
    util = DatabaseUtil()
    
    if args.command == "drop":
        if args.passphrase:
            result = util.drop_database(args.passphrase)
        else:
            print("⚠️  WARNING: This will permanently delete all data in the database!")
            confirm = input("Type 'YES' to confirm: ")
            if confirm == "YES":
                result = util.drop_database()
            else:
                print("Operation cancelled")
                return
    
    elif args.command == "compare":
        result = util.compare_database_with_files()
        
    elif args.command == "harvest":
        result = util.harvest_database(args.output_path)
    
    # Print results
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main() 