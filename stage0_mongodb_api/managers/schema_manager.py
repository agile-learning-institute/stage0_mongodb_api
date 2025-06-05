from typing import Dict, List, Optional, Union, TypedDict, Set
from enum import Enum
from stage0_py_utils import MongoIO, Config
import yaml
import os
import re
import json
from stage0_mongodb_api.managers.version_number import VersionNumber
from stage0_mongodb_api.managers.config_manager import ConfigManager
from stage0_mongodb_api.managers.schema_renderer import SchemaRenderer
from stage0_mongodb_api.managers.schema_validator import SchemaValidator, SchemaValidationError
from stage0_mongodb_api.managers.schema_types import SchemaType, SchemaFormat, Schema, PrimitiveType, SchemaContext

class SchemaError(Exception):
    """Base exception for schema-related errors."""
    pass

class SchemaManager:
    """Manager class for handling schema operations."""
    
    def __init__(self):
        """Initialize the schema manager.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config = Config.get_instance()
        self.config_manager = ConfigManager()
        self.types: Dict = {}
        self.enumerators: List[Dict] = []
        self.dictionaries: Dict = {}

        # Load all schema definitions
        self.load_errors: List[Dict] = self.config_manager.load_errors
        self.load_errors.extend(self._load_types())
        self.load_errors.extend(self._load_enumerators())
        self.load_errors.extend(self._load_dictionaries())
        
    def _load_types(self) -> List[Dict]:
        """Load type definitions.
        
        Returns:
            List of load errors
        """
        errors = []
        types_dir = os.path.join(self.config.INPUT_FOLDER, "dictionary", "types")
        if not os.path.exists(types_dir):
            errors.append({
                "error": "directory_not_found",
                "error_id": "SCH-001",
                "path": types_dir,
                "message": "Types directory not found"
            })
            return errors
            
        try:
            for filename in os.listdir(types_dir):
                if filename.endswith(".yaml"):
                    file_path = os.path.join(types_dir, filename)
                    try:
                        with open(file_path, "r") as f:
                            type_def = yaml.safe_load(f)
                            self.types[filename[:-5]] = type_def
                    except yaml.YAMLError:
                        errors.append({
                            "error": "parse_error",
                            "error_id": "SCH-002",
                            "file": filename,
                            "message": "Failed to parse type definition"
                        })
                    except Exception as e:
                        errors.append({
                            "error": "load_error",
                            "error_id": "SCH-003",
                            "file": filename,
                            "message": str(e)
                        })
        except Exception as e:
            errors.append({
                "error": "load_error",
                "error_id": "SCH-003",
                "path": types_dir,
                "message": str(e)
            })
        return errors
            
    def _load_enumerators(self) -> List[Dict]:
        """Load all enumerator definitions from the enumerators.json file.
        
        Returns:
            List of load errors
        """
        errors = []
        enumerator_file = os.path.join(self.config.INPUT_FOLDER, "data", "enumerators.json")
        
        try:
            with open(enumerator_file, 'r') as f:
                enumerators = json.load(f)
                self.enumerators = enumerators
            
        except FileNotFoundError:
            errors.append({
                'error_id': 'SCH-004',
                'message': f'Enumerator file not found: {enumerator_file}'
            })
        except json.JSONDecodeError as e:
            errors.append({
                'error_id': 'SCH-007',
                'message': f'Failed to parse enumerator file {enumerator_file}: {str(e)}'
            })
        return errors
            
    def _load_dictionaries(self) -> List[Dict]:
        """Load dictionary definitions.
        
        Returns:
            List of load errors
        """
        errors = []
        dictionaries_dir = os.path.join(self.config.INPUT_FOLDER, "dictionary")
        if not os.path.exists(dictionaries_dir):
            errors.append({
                "error": "directory_not_found",
                "error_id": "SCH-009",
                "path": dictionaries_dir,
                "message": "Dictionaries directory not found"
            })
            return errors
            
        try:
            for filename in os.listdir(dictionaries_dir):
                if filename.endswith((".yaml", ".yml")):
                    file_path = os.path.join(dictionaries_dir, filename)
                    try:
                        with open(file_path, "r") as f:
                            dict_def = yaml.safe_load(f)
                            self.dictionaries[os.path.splitext(filename)[0]] = dict_def
                    except yaml.YAMLError:
                        errors.append({
                            "error": "parse_error",
                            "error_id": "SCH-011",
                            "file": filename,
                            "message": "Failed to parse dictionary definition"
                        })
                    except Exception as e:
                        errors.append({
                            "error": "load_error",
                            "error_id": "SCH-012",
                            "file": filename,
                            "message": str(e)
                        })
        except Exception as e:
            errors.append({
                "error": "load_error",
                "error_id": "SCH-012",
                "path": dictionaries_dir,
                "message": str(e)
            })
        return errors
            
    def validate_schema(self) -> List[Dict]:
        """Validate all loaded schema definitions.
        
        Returns:
            List of validation errors
        """
        errors = self.config_manager.validate_configs()
        
        # Create validation context
        context: SchemaContext = {
            "types": self.types,
            "enumerators": self.enumerators,
            "dictionaries": self.dictionaries,
            "collection_configs": self.config_manager.collection_configs,
            "schema_name": None,
            "format": None
        }
        
        errors.extend(SchemaValidator.validate_schema(context))
        return errors
        
    def render_one(self, collection_name: str, version: str, format: SchemaFormat) -> Dict:
        """Render a single schema version.
        
        Args:
            collection_name: Name of the collection
            version: Version string (e.g. "1.0.0.1")
            format: Target schema format
            
        Returns:
            Dict containing the rendered schema
        """
        # Get the collection config
        collection_config = self.config.get_collection_config(collection_name)
        if not collection_config:
            raise ValueError(f"Collection not found: {collection_name}")
            
        # Get the schema name
        schema_name = f"{collection_name}.{version}"
        
        # Create schema context
        context: SchemaContext = {
            "types": self.types,
            "dictionaries": self.dictionaries,
            "enumerators": self.enumerators,
            "collection_configs": self.config.collection_configs,
            "schema_name": None,
            "format": format
        }
        
        return SchemaRenderer.render_schema(schema_name, context)

    def render_all(self) -> Dict[str, Dict[str, Dict]]:
        """Render all schema versions in both BSON and JSON formats.
        
        Returns:
            Dict mapping collection names to version maps, which map versions to format maps
        """
        rendered = {}
        
        for collection_name, collection_config in self.config.collection_configs.items():
            rendered[collection_name] = {}
            
            for version in collection_config["versions"]:
                version_name = f"{collection_name}.{version}"
                rendered[collection_name][version] = {}
                
                # Render in both formats
                for format in [SchemaFormat.BSON, SchemaFormat.JSON]:
                    context: SchemaContext = {
                        "types": self.types,
                        "dictionaries": self.dictionaries,
                        "enumerators": self.enumerators,
                        "collection_configs": self.config.collection_configs,
                        "schema_name": None,
                        "format": format
                    }
                    rendered[collection_name][version][format.value] = SchemaRenderer.render_schema(
                        version_name, context
                    )
                    
        return rendered

    def apply_schema(self, version_name: str) -> Dict:
        """Apply a schema to a collection.
        
        Args:
            version_name: Name of the collection version (e.g. user.1.0.0.1)
            
        Returns:
            Dict containing operation result
        """
        if not version_name:
            return {
                "status": "error",
                "operation": "apply_schema",
                "collection": version_name,
                "message": "Collection name cannot be empty"
            }

        [collection_name, version_number] = version_name.split(".")
        try:
            bson_schema = self.render_one(collection_name, version_number, SchemaFormat.BSON)
            self.mongo.apply_schema(collection_name, bson_schema)
        except Exception as e:
            return {
                "status": "error",
                "operation": "apply_schema",
                "collection": collection_name,
                "message": str(e)
            }
        
        return {
            "status": "success",
            "operation": "apply_schema",
            "collection": collection_name,
            "schema": bson_schema
        }

    def remove_schema(self, collection_name: str) -> Dict:
        """Remove schema validation from a collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Dict containing operation result
        """
        if not collection_name:
            return {
                "status": "error",
                "operation": "remove_schema",
                "collection": collection_name,
                "message": "Collection name cannot be empty"
            }
            
        try:
            self.mongo.remove_schema(collection_name)
        except Exception as e:
            return {
                "status": "error",
                "operation": "remove_schema",
                "collection": collection_name,
                "message": str(e)
            }

        return {
            "status": "success",
            "operation": "remove_schema",
            "collection": collection_name
        } 