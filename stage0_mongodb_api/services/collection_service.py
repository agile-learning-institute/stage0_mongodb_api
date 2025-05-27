from typing import Dict, List, Optional
import logging
import os
import yaml
from stage0_py_utils import MongoIO, Config
from managers.version_manager import VersionManager
from managers.index_manager import IndexManager
from managers.schema_manager import SchemaManager
from managers.migration_manager import MigrationManager

logger = logging.getLogger(__name__)

class CollectionService:
    """Service for managing MongoDB collections, including schema validation, indexes, and migrations."""
    
    def __init__(self, input_folder: str):
        """Initialize the collection service.
        
        Args:
            input_folder: Path to the input folder containing collection configurations
        """
        self.input_folder = input_folder
        self.mongo = MongoIO.get_instance()
        self.config = Config.get_instance()
        self.version_manager = VersionManager()
        self.schema_manager = SchemaManager(os.path.join(input_folder, "dictionary"))
        self.migration_manager = MigrationManager()
        self.index_manager = IndexManager()
        self.configs = {}
        self.collections = {}
        self._load_collections()
        
        # Load API templates
        self.api_templates = self._load_api_templates()

    def _load_collections(self):
        """Load collection configurations from the input folder"""
        try:
            input_folder = os.getenv("INPUT_FOLDER", "/input")
            logger.info(f"Loading collections from {input_folder}")

            # Load all YAML files from input folder
            for root, _, files in os.walk(input_folder):
                for file in files:
                    if file.endswith(".yaml"):
                        file_path = os.path.join(root, file)
                        with open(file_path, "r") as f:
                            data = yaml.safe_load(f)
                            collection_name = os.path.splitext(file)[0]
                            self.configs[collection_name] = data
                            self.collections[collection_name] = {
                                "name": collection_name,
                                "versions": data.get("versions", []),
                                "dropIndexes": data.get("dropIndexes", []),
                                "migrations": data.get("migrations", []),
                                "addIndexes": data.get("addIndexes", [])
                            }

            # Get current versions from MongoDB
            for collection_name in self.collections:
                current_version = self.version_manager.get_current_version(collection_name)
                if current_version:
                    self.collections[collection_name]["current_version"] = current_version

            logger.info(f"Loaded {len(self.collections)} collections")
        except Exception as e:
            logger.error(f"Error loading collections: {str(e)}")
            raise

    def list_collections(self):
        """List all configured collections"""
        return [{
            "name": name,
            "current_version": config.get("current_version", "unknown"),
            "versions": config.get("versions", [])
        } for name, config in self.collections.items()]

    def get_collection(self, collection_name):
        """Get collection configuration by name"""
        if collection_name not in self.collections:
            raise ValueError(f"Collection {collection_name} not found")
        return self.collections[collection_name]

    def process_collections(self):
        """Process all configured collections"""
        results = {}
        for collection_name in self.collections:
            try:
                results[collection_name] = self.process_collection(collection_name)
            except Exception as e:
                logger.error(f"Error processing collection {collection_name}: {str(e)}")
                results[collection_name] = {"error": str(e)}
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
        # Load collection configuration
        config = self._load_collection_config(collection_name)
        if not config:
            return {
                "status": "error",
                "collection": collection_name,
                "error": "Collection configuration not found"
            }
            
        operations = []
        
        # Process each version in sequence
        for version in config.get("versions", []):
            version_ops = self._process_version(collection_name, version)
            operations.extend(version_ops)
            
        return {
            "status": "success",
            "collection": collection_name,
            "operations": operations
        }

    def _load_collection_config(self, collection_name: str) -> Optional[Dict]:
        """Load a collection configuration file."""
        config_file = os.path.join(self.input_folder, "collections", f"{collection_name}.yaml")
        if not os.path.exists(config_file):
            return None
            
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)

    def _process_version(self, collection_name: str, version: Dict) -> List[Dict]:
        """Process a single version of a collection."""
        operations = []

        # Remove existing schema validation
        operations.append(self.schema_manager.remove_schema(collection_name))
        
        # Remove indexes
        for index in version.get("removeIndexes", []):
            operations.append(self.index_manager.drop_index(collection_name, index))
            
        # Run migrations
        for migration in version.get("migrations", []):
            operations.append(self.migration_manager.run_migration(collection_name, migration))
            
        # Add indexes
        for index in version.get("addIndexes", []):
            operations.append(self.index_manager.create_index(collection_name, index))
            
        # Apply schema validation
        schema_name = version.get("schema")
        if schema_name:
            operations.append(self.schema_manager.apply_schema(collection_name, schema_name))
        
        return operations

    def _load_api_templates(self) -> Dict:
        """Load API templates from the input folder."""
        templates_file = os.path.join(self.input_folder, "api", "templates.yaml")
        if not os.path.exists(templates_file):
            return {}
            
        with open(templates_file, 'r') as f:
            return yaml.safe_load(f)

    def generate_openapi(self, collection_name: str) -> Dict:
        """Generate OpenAPI documentation for a collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Dict containing the OpenAPI specification
        """
        # Load collection configuration
        config = self._load_collection_config(collection_name)
        if not config:
            return {
                "status": "error",
                "collection": collection_name,
                "error": "Collection configuration not found"
            }
            
        # Get the latest version's schema
        latest_version = config["versions"][-1]
        schema_name = latest_version.get("schema")
        if not schema_name:
            return {
                "status": "error",
                "collection": collection_name,
                "error": "No schema defined for latest version"
            }
            
        # Get JSON Schema
        json_schema = self.schema_manager.render_schema(schema_name, SchemaFormat.JSON_SCHEMA)

        # Get API template
        template = self.api_templates.get(collection_name, {})
        
        # Combine template with schema
        openapi = {
            "openapi": "3.0.0",
            "info": {
                "title": config.get("title", collection_name),
                "description": config.get("description", ""),
                "version": latest_version.get("version", "1.0.0")
            },
            "paths": {
                f"/{collection_name}": {
                    "get": {
                        "summary": f"List {collection_name}",
                        "responses": {
                            "200": {
                                "description": "Successful response",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "array",
                                            "items": json_schema
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "post": {
                        "summary": f"Create {collection_name}",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": json_schema
                                }
                            }
                        },
                        "responses": {
                            "201": {
                                "description": "Created",
                                "content": {
                                    "application/json": {
                                        "schema": json_schema
                                    }
                                }
                            }
                        }
                    }
                },
                f"/{collection_name}/{{id}}": {
                    "get": {
                        "summary": f"Get {collection_name} by ID",
                        "parameters": [
                            {
                                "name": "id",
                                "in": "path",
                                "required": True,
                                "schema": {
                                    "type": "string"
                                }
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "Successful response",
                                "content": {
                                    "application/json": {
                                        "schema": json_schema
                                    }
                                }
                            }
                        }
                    },
                    "put": {
                        "summary": f"Update {collection_name}",
                        "parameters": [
                            {
                                "name": "id",
                                "in": "path",
                                "required": True,
                                "schema": {
                                    "type": "string"
                                }
                            }
                        ],
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": json_schema
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Updated",
                                "content": {
                                    "application/json": {
                                        "schema": json_schema
                                    }
                                }
                            }
                        }
                    },
                    "delete": {
                        "summary": f"Delete {collection_name}",
                        "parameters": [
                            {
                                "name": "id",
                                "in": "path",
                                "required": True,
                                "schema": {
                                    "type": "string"
                                }
                            }
                        ],
                        "responses": {
                            "204": {
                                "description": "Deleted"
                            }
                        }
                    }
                }
            }
        }
        
        # Merge with template
        if template:
            openapi = self._merge_templates(openapi, template)

        return {
            "status": "success",
            "collection": collection_name,
            "openapi": openapi
        }

    def _merge_templates(self, base: Dict, template: Dict) -> Dict:
        """Merge a template with the base OpenAPI specification."""
        # Deep merge dictionaries
        result = base.copy()
        for key, value in template.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_templates(result[key], value)
            else:
                result[key] = value
        return result 