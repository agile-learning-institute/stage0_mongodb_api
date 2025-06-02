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
from stage0_mongodb_api.managers.schema_types import SchemaType, SchemaFormat, Schema, PrimitiveType

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
        self.load_errors: List[Dict] = []
        
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
                if filename.endswith(".json"):
                    file_path = os.path.join(types_dir, filename)
                    try:
                        with open(file_path, "r") as f:
                            type_def = json.load(f)
                            self.types[filename[:-5]] = type_def
                    except json.JSONDecodeError:
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
                
            # Validate that enumerators is a dictionary
            if not isinstance(enumerators, List):
                self.load_errors.append({
                    'error_id': 'SCH-005',
                    'message': f'Invalid enumerator format in {enumerator_file}: must be a List'
                })
                return
                
            # Store enumerators
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
                if filename.endswith(".json"):
                    file_path = os.path.join(dictionaries_dir, filename)
                    try:
                        with open(file_path, "r") as f:
                            dict_def = json.load(f)
                            if "version" not in dict_def:
                                self.load_errors.append({
                                    "error": "invalid_version",
                                    "error_id": "SCH-010",
                                    "file": filename,
                                    "message": "Dictionary must have a version"
                                })
                                continue
                                
                            self.dictionaries[filename[:-5]] = dict_def
                    except json.JSONDecodeError:
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
            
    def validate_schema(self, schema_name: str, enum_version: Optional[int] = None) -> List[Dict]:
        """Validate a schema definition.
        
        Args:
            schema_name: Name of the schema to validate
            enum_version: Optional version number for enumerators
            
        Returns:
            List of validation errors
        """
        if schema_name not in self.types:
            return [{
                "error": "schema_not_found",
                "error_id": "SCH-013",
                "schema_name": schema_name,
                "message": "Schema not found"
            }]
            
        schema = self.types[schema_name]
        errors = SchemaValidator.validate_schema(schema, schema_name, enum_version, self.enumerators)
        
        # Validate enumerators if present
        if self.enumerators:
            errors.extend(SchemaValidator.validate_enumerators(self.enumerators))
            
        return errors
        
    def render_schema(self, schema_name: str, format: SchemaFormat = SchemaFormat.BSON) -> Dict:
        """Render a schema in the specified format.
        
        Args:
            schema_name: Name of the schema to render
            format: Target schema format
            
        Returns:
            Dict containing the rendered schema
        """
        if schema_name not in self.types:
            raise ValueError(f"Schema not found: {schema_name}")
            
        schema = self.types[schema_name]
        return SchemaRenderer.render_schema(schema, format, self.types, self.enumerators)

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