from typing import Dict, List, Optional
from stage0_mongodb_api.managers.schema_manager import SchemaManager, SchemaFormat
from stage0_mongodb_api.managers.config_manager import ConfigManager
from stage0_mongodb_api.managers.version_number import VersionNumber
import logging

logger = logging.getLogger(__name__)

class RenderService:
    """Service for rendering schemas in different formats.
    
    This service handles:
    1. Schema rendering in JSON and BSON formats
    2. Schema validation with collection context
    3. Version resolution for schemas and enumerators
    """
    
    def __init__(self):
        """Initialize the render service."""
        self.schema_manager = SchemaManager()
        self.config_manager = ConfigManager()
        
    def render_schema(self, collection_name: str, format: SchemaFormat = SchemaFormat.BSON_SCHEMA) -> Dict:
        """Render a schema in the specified format.
        
        Args:
            collection_name: Name of the collection
            format: Target schema format (JSON_SCHEMA or BSON_SCHEMA)
            
        Returns:
            Dict containing the rendered schema
        """
        # Get full schema name from config
        schema_name = self.config_manager.get_full_schema_name(collection_name)
        if not schema_name:
            return {
                "status": "error",
                "operation": "render_schema",
                "collection": collection_name,
                "message": f"No configuration found for collection: {collection_name}"
            }
            
        # Validate schema with collection context
        errors = self.schema_manager.validate_schema(collection_name)
        if errors:
            return {
                "status": "error",
                "operation": "render_schema",
                "collection": collection_name,
                "message": "Schema validation failed",
                "errors": errors
            }
            
        try:
            schema = self.schema_manager.render_schema(schema_name, collection_name, format)
            return {
                "status": "success",
                "operation": "render_schema",
                "collection": collection_name,
                "format": format.value,
                "schema": schema
            }
        except Exception as e:
            return {
                "status": "error",
                "operation": "render_schema",
                "collection": collection_name,
                "message": str(e)
            }
            
    def get_schema_info(self, collection_name: str) -> Dict:
        """Get information about a schema.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Dict containing schema information
        """
        # Get collection config
        config = self.config_manager.get_collection_config(collection_name)
        if not config:
            return {
                "status": "error",
                "operation": "get_schema_info",
                "collection": collection_name,
                "message": f"No configuration found for collection: {collection_name}"
            }
            
        # Get schema version
        version = self.config_manager.get_schema_version(collection_name)
        if not version:
            return {
                "status": "error",
                "operation": "get_schema_info",
                "collection": collection_name,
                "message": "Invalid version in collection configuration"
            }
            
        # Get schema name
        schema_name = self.config_manager.get_full_schema_name(collection_name)
        if not schema_name:
            return {
                "status": "error",
                "operation": "get_schema_info",
                "collection": collection_name,
                "message": "Could not resolve schema name"
            }
            
        try:
            # Get both JSON and BSON schemas
            json_schema = self.schema_manager.render_schema(schema_name, collection_name, SchemaFormat.JSON_SCHEMA)
            bson_schema = self.schema_manager.render_schema(schema_name, collection_name, SchemaFormat.BSON_SCHEMA)
            
            return {
                "status": "success",
                "operation": "get_schema_info",
                "collection": collection_name,
                "config": config,
                "version": str(version),
                "schema_name": schema_name,
                "json_schema": json_schema,
                "bson_schema": bson_schema
            }
        except Exception as e:
            return {
                "status": "error",
                "operation": "get_schema_info",
                "collection": collection_name,
                "message": str(e)
            }

    def render_json_schema(self, collection_name: str) -> Dict:
        """Render a JSON schema for a collection"""
        return {}

    def render_bson_schema(self, collection_name: str) -> Dict:
        """Render a BSON schema for a collection"""
        return {}

    def render_openapi(self, collection_name: str) -> Dict:
        """Render an OpenAPI specification for a collection"""
        return {}
    
