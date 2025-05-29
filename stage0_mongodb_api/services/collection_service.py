from typing import Dict, List, Optional
import logging
import os
import yaml
from stage0_py_utils import Config
from stage0_mongodb_api.managers.version_manager import VersionManager
from stage0_mongodb_api.managers.schema_manager import SchemaManager, SchemaFormat
from stage0_mongodb_api.managers.config_manager import ConfigManager
from stage0_mongodb_api.managers.version_number import VersionNumber

logger = logging.getLogger(__name__)

class CollectionService:
    """
    Service for managing MongoDB collection configurations.
    """
    
    def __init__(self):
        """Initialize the collection service.
        
        Args:
            input_folder: Optional path to the input folder containing collection configurations.
                         If not provided, uses Config.get_instance().INPUT_FOLDER
        """
        self.config = Config.get_instance()
        self.input_folder = self.config.INPUT_FOLDER
        self.version_manager = VersionManager()
        self.collections = []
        self.schema_manager = SchemaManager()
        self.config_manager = ConfigManager()
        self._load_collections(self.input_folder)

    def _load_collections(self, input_folder):
        """Load collection configurations from the input folder"""
        try:
            collections_folder = os.path.join(input_folder, "collections")
            logger.info(f"Loading collections from {collections_folder}")

            # Load all YAML files from collections folder
            for file in os.listdir(collections_folder):
                file_path = os.path.join(collections_folder, file)
                with open(file_path, "r") as f:
                    data = yaml.safe_load(f)
                    self.collections.append(data)

            # Get current versions from MongoDB
            for collection in self.collections:
                collection_name = collection.get("name")
                current_version = self.version_manager.get_current_version(collection_name)
                collection["current_version"] = current_version

            logger.info(f"Loaded {len(self.collections)} collections")
        except Exception as e:
            logger.error(f"Error loading collections: {str(e)}")
            raise

    def list_collections(self):
        """List all configured collections"""
        return self.collections

    def process_collections(self):
        """Process all configured collections"""
        results = []
        for collection in self.collections:
            try:
                result = self.process_collection(collection.get("name"))
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing collection {collection.get('name')}: {str(e)}")
                results.append({
                    "status": "error",
                    "collection": collection.get("name"),
                    "error": str(e)
                })
        return results

    def process_collection(self, collection_name: str) -> Dict:
        """Process a collection configuration.
        
        Args:
            collection_name: Name of the collection to process
            
        Returns:
            Dict containing processing results:
            {
                "status": "success",
                "collection": str,
                "operations": List[Dict]  # List of operation results
            }
        """
        # Find collection configuration
        collection = next((c for c in self.collections if c.get("name") == collection_name), None)
        if not collection:
            return {
                "status": "error",
                "collection": collection_name,
                "error": "Collection configuration not found"
            }
            
        # Process versions through version manager
        operations = self.version_manager.process_versions(collection_name, collection.get("versions", []))
            
        return {
            "status": "success",
            "collection": collection_name,
            "operations": operations
        }

    def create_collection(self, collection_name: str) -> Dict:
        """Create a new collection with schema validation.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Dict containing operation result
        """
        # Get full schema name from config
        schema_name = self.config_manager.get_full_schema_name(collection_name)
        if not schema_name:
            return {
                "status": "error",
                "operation": "create_collection",
                "collection": collection_name,
                "message": f"No configuration found for collection: {collection_name}"
            }
            
        # Validate schema with collection context
        errors = self.schema_manager.validate_schema(collection_name)
        if errors:
            return {
                "status": "error",
                "operation": "create_collection",
                "collection": collection_name,
                "message": "Schema validation failed",
                "errors": errors
            }
            
        # Apply schema
        return self.schema_manager.apply_schema(schema_name)
        
    def delete_collection(self, collection_name: str) -> Dict:
        """Delete a collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Dict containing operation result
        """
        # Remove schema first
        result = self.schema_manager.remove_schema(collection_name)
        if result["status"] == "error":
            return result
            
        # Delete collection
        try:
            self.schema_manager.mongo.delete_collection(collection_name)
            return {
                "status": "success",
                "operation": "delete_collection",
                "collection": collection_name
            }
        except Exception as e:
            return {
                "status": "error",
                "operation": "delete_collection",
                "collection": collection_name,
                "message": str(e)
            }
            
    def get_collection_info(self, collection_name: str) -> Dict:
        """Get information about a collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Dict containing collection information
        """
        # Get collection config
        config = self.config_manager.get_collection_config(collection_name)
        if not config:
            return {
                "status": "error",
                "operation": "get_collection_info",
                "collection": collection_name,
                "message": f"No configuration found for collection: {collection_name}"
            }
            
        # Get schema version
        version = self.config_manager.get_schema_version(collection_name)
        if not version:
            return {
                "status": "error",
                "operation": "get_collection_info",
                "collection": collection_name,
                "message": "Invalid version in collection configuration"
            }
            
        # Get schema
        schema_name = self.config_manager.get_full_schema_name(collection_name)
        if not schema_name:
            return {
                "status": "error",
                "operation": "get_collection_info",
                "collection": collection_name,
                "message": "Could not resolve schema name"
            }
            
        try:
            schema = self.schema_manager.render_schema(schema_name, collection_name, SchemaFormat.BSON_SCHEMA)
            return {
                "status": "success",
                "operation": "get_collection_info",
                "collection": collection_name,
                "config": config,
                "version": str(version),
                "schema": schema
            }
        except Exception as e:
            return {
                "status": "error",
                "operation": "get_collection_info",
                "collection": collection_name,
                "message": str(e)
            }
