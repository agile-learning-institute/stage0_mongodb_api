from typing import Dict, List
from stage0_py_utils import MongoIO

class SchemaManager:
    """Static class for managing MongoDB schemas."""
    
    @staticmethod
    def validate_schema(schema: Dict) -> bool:
        """Validate a schema configuration."""
        required_fields = ["bsonType", "properties"]
        if not all(field in schema for field in required_fields):
            return False
            
        # Validate properties
        for prop_name, prop_config in schema["properties"].items():
            if "bsonType" not in prop_config:
                return False
                
        return True

    @staticmethod
    def apply_schema(collection_name: str, schema: Dict) -> Dict:
        """Apply a schema to a collection."""
        mongo = MongoIO.get_instance()
        
        try:
            if not SchemaManager.validate_schema(schema):
                raise ValueError("Invalid schema configuration")
                
            # Apply schema validation
            mongo.update_document(
                collection_name,
                set_data={"validator": {"$jsonSchema": schema}}
            )
            
            return {
                "status": "success",
                "collection": collection_name
            }
        except Exception as e:
            return {
                "status": "error",
                "collection": collection_name,
                "error": str(e)
            }

    @staticmethod
    def run_migration(collection_name: str, migration: Dict) -> Dict:
        """Run a migration on a collection."""
        mongo = MongoIO.get_instance()
        
        try:
            # Validate migration configuration
            if "operation" not in migration:
                raise ValueError("Migration must include 'operation'")
                
            operation = migration["operation"]
            if operation == "update":
                if "query" not in migration or "update" not in migration:
                    raise ValueError("Update migration must include 'query' and 'update'")
                mongo.update_document(
                    collection_name,
                    match=migration["query"],
                    set_data=migration["update"]
                )
            elif operation == "delete":
                if "query" not in migration:
                    raise ValueError("Delete migration must include 'query'")
                mongo.delete_document(
                    collection_name,
                    migration["query"]
                )
            else:
                raise ValueError(f"Unsupported migration operation: {operation}")
                
            return {
                "status": "success",
                "migration": operation
            }
        except Exception as e:
            return {
                "status": "error",
                "migration": migration.get("operation", "unknown"),
                "error": str(e)
            } 