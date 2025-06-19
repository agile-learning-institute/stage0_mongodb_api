from typing import Dict, List, Optional
from stage0_mongodb_api.managers.schema_manager import SchemaManager, SchemaFormat
from stage0_mongodb_api.managers.version_number import VersionNumber
from stage0_mongodb_api.managers.config_manager import ConfigManager
import logging

logger = logging.getLogger(__name__)

class RenderNotFoundError(Exception):
    """Raised when a schema is not found for rendering."""
    def __init__(self, schema_name: str, errors: List[Dict] = None):
        self.schema_name = schema_name
        self.errors = errors or []
        super().__init__(f"Schema '{schema_name}' not found for rendering")

class RenderProcessingError(Exception):
    """Raised when schema rendering fails."""
    def __init__(self, schema_name: str, errors: List[Dict]):
        self.schema_name = schema_name
        self.errors = errors
        super().__init__(f"Failed to render schema '{schema_name}'")

class RenderService:
    """Service for rendering schemas in different formats."""
    
    @staticmethod
    def render_json_schema(schema_name: str, token: Dict = None) -> Dict:
        """Render a JSON schema for a schema name
        
        Args:
            schema_name: Complete schema name including version (e.g., "collection.1.0.0.1")
            token: Authentication token for RBAC enforcement
            
        Returns:
            Dict containing the rendered JSON schema
            
        Raises:
            RenderNotFoundError: If schema is not found
            RenderProcessingError: If there are load, validation, or rendering errors
        """
        config_manager = ConfigManager()
        schema_manager = SchemaManager(config_manager.collection_configs)
        
        # Check for load errors
        if config_manager.load_errors:
            raise RenderProcessingError(schema_name, config_manager.load_errors)
            
        # Check for validation errors
        validation_errors = config_manager.validate_configs()
        if validation_errors:
            raise RenderProcessingError(schema_name, validation_errors)
            
        try:
            return schema_manager.render_one(schema_name, SchemaFormat.JSON)
        except Exception as e:
            logger.error(f"Error rendering JSON schema for {schema_name}: {str(e)}")
            raise RenderProcessingError(schema_name, [{
                "error": "rendering_error",
                "error_id": "RND-002",
                "message": str(e)
            }])

    @staticmethod
    def render_bson_schema(schema_name: str, token: Dict = None) -> Dict:
        """Render a BSON schema for a schema name
        
        Args:
            schema_name: Complete schema name including version (e.g., "collection.1.0.0.1")
            token: Authentication token for RBAC enforcement
            
        Returns:
            Dict containing the rendered BSON schema
            
        Raises:
            RenderNotFoundError: If schema is not found
            RenderProcessingError: If there are load, validation, or rendering errors
        """
        config_manager = ConfigManager()
        schema_manager = SchemaManager(config_manager.collection_configs)
        
        # Check for load errors
        if config_manager.load_errors:
            raise RenderProcessingError(schema_name, config_manager.load_errors)
            
        # Check for validation errors
        validation_errors = config_manager.validate_configs()
        if validation_errors:
            raise RenderProcessingError(schema_name, validation_errors)
            
        try:
            return schema_manager.render_one(schema_name, SchemaFormat.BSON)
        except Exception as e:
            logger.error(f"Error rendering BSON schema for {schema_name}: {str(e)}")
            raise RenderProcessingError(schema_name, [{
                "error": "rendering_error",
                "error_id": "RND-003",
                "message": str(e)
            }])
    
    @staticmethod
    def render_openapi(schema_name: str, token: Dict = None) -> Dict:
        """Render an OpenAPI specification for a schema name
        
        Args:
            schema_name: Complete schema name including version (e.g., "collection.1.0.0.1")
            token: Authentication token for RBAC enforcement
            
        Returns:
            Dict containing a message that OpenAPI rendering is to be implemented
            
        Note:
            This will be implemented using Jinja templates and JSON schema rendering
        """
        return {
            "message": "OpenAPI rendering not yet implemented"
        }
    
