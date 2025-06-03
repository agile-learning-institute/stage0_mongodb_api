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
from stage0_mongodb_api.managers.schema_types import SchemaType, SchemaFormat, Schema, PrimitiveType, ValidationContext

class SchemaError(Exception):
    """Base exception for schema-related errors."""
    pass

class SchemaManager:
    """Manager class for handling schema operations."""
    
    def __init__(self, config_manager: ConfigManager):
        """Initialize the schema manager.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config = Config.get_instance()
        self.config_manager = config_manager
        self.types: Dict = {}
        self.enumerators: List[Dict] = []
        self.dictionaries: Dict = {}
        self.load_errors: List[Dict] = config_manager.load_errors
        
    def load_schemas(self) -> None:
        """Load all schema definitions."""
        self._load_types()
        self._load_enumerators()
        self._load_dictionaries()
        
    def _load_types(self) -> None:
        """Load type definitions."""
        types_dir = os.path.join(self.config.INPUT_FOLDER, "dictionary", "types")
        if not os.path.exists(types_dir):
            self.load_errors.append({
                "error": "directory_not_found",
                "error_id": "SCH-001",
                "path": types_dir,
                "message": "Types directory not found"
            })
            return
            
        try:
            for filename in os.listdir(types_dir):
                if filename.endswith(".yaml"):
                    file_path = os.path.join(types_dir, filename)
                    try:
                        with open(file_path, "r") as f:
                            type_def = yaml.safe_load(f)
                            self.types[filename[:-5]] = type_def
                    except yaml.YAMLError:
                        self.load_errors.append({
                            "error": "parse_error",
                            "error_id": "SCH-002",
                            "file": filename,
                            "message": "Failed to parse type definition"
                        })
                    except Exception as e:
                        self.load_errors.append({
                            "error": "load_error",
                            "error_id": "SCH-003",
                            "file": filename,
                            "message": str(e)
                        })
        except Exception as e:
            self.load_errors.append({
                "error": "load_error",
                "error_id": "SCH-003",
                "path": types_dir,
                "message": str(e)
            })
            
    def _load_enumerators(self) -> None:
        """Load all enumerator definitions from the enumerators.json file."""
        enumerator_file = os.path.join(self.config.INPUT_FOLDER, "data", "enumerators.json")
        
        try:
            with open(enumerator_file, 'r') as f:
                enumerators = json.load(f)
                self.enumerators = enumerators
            
        except FileNotFoundError:
            self.load_errors.append({
                'error_id': 'SCH-004',
                'message': f'Enumerator file not found: {enumerator_file}'
            })
        except json.JSONDecodeError as e:
            self.load_errors.append({
                'error_id': 'SCH-007',
                'message': f'Failed to parse enumerator file {enumerator_file}: {str(e)}'
            })
            
    def _load_dictionaries(self) -> None:
        """Load dictionary definitions."""
        dictionaries_dir = os.path.join(self.config.INPUT_FOLDER, "dictionary")
        if not os.path.exists(dictionaries_dir):
            self.load_errors.append({
                "error": "directory_not_found",
                "error_id": "SCH-009",
                "path": dictionaries_dir,
                "message": "Dictionaries directory not found"
            })
            return
            
        try:
            for filename in os.listdir(dictionaries_dir):
                if filename.endswith(".yaml"):
                    file_path = os.path.join(dictionaries_dir, filename)
                    try:
                        with open(file_path, "r") as f:
                            dict_def = yaml.safe_load(f)
                            self.dictionaries[filename[:-5]] = dict_def
                    except yaml.YAMLError:
                        self.load_errors.append({
                            "error": "parse_error",
                            "error_id": "SCH-011",
                            "file": filename,
                            "message": "Failed to parse dictionary definition"
                        })
                    except Exception as e:
                        self.load_errors.append({
                            "error": "load_error",
                            "error_id": "SCH-012",
                            "file": filename,
                            "message": str(e)
                        })
        except Exception as e:
            self.load_errors.append({
                "error": "load_error",
                "error_id": "SCH-012",
                "path": dictionaries_dir,
                "message": str(e)
            })
            
    def validate_schema(self) -> List[Dict]:
        """Validate all loaded schema definitions.
        
        Returns:
            List of validation errors
        """
        errors = self.config_manager.validate_configs()
        
        # Create validation context
        context: ValidationContext = {
            "types": self.types,
            "enumerators": self.enumerators,
            "dictionaries": self.dictionaries,
            "collection_configs": self.config_manager.collection_configs
        }
        
        errors.extend(SchemaValidator.validate_schema(context))
        return errors
        
    def render_schema(self, schema_name: str, format: SchemaFormat = SchemaFormat.BSON) -> Dict:
        """Render a schema in the specified format.
        
        Args:
            schema_name: Name of the schema to render
            format: Target schema format
            
        Returns:
            Dict containing the rendered schema
        """
        return SchemaRenderer.render_schema(self, schema_name, format)

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
            bson_schema = self.render_schema(version_name, SchemaFormat.BSON)
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