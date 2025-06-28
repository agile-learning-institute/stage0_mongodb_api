from typing import Dict, List, Set, Optional, Any
import os
import re
import yaml
import json
import logging
from stage0_py_utils import Config, MongoIO
from stage0_mongodb_api.managers.schema_renderer import SchemaRenderer
from stage0_mongodb_api.managers.schema_validator import SchemaValidator
from stage0_mongodb_api.managers.schema_types import SchemaContext, SchemaFormat
from stage0_mongodb_api.managers.version_number import VersionNumber

logger = logging.getLogger(__name__)

class SchemaError(Exception):
    """Base exception for schema-related errors."""
    pass

class SchemaManager:
    """Manager class for handling schema operations."""
    
    def __init__(self, collection_configs: Optional[Dict[str, Dict]] = None):
        """Initialize the schema manager.
        
        Args:
            collection_configs: Optional collection configurations. If not provided,
                               will be loaded from the input folder.
        """
        self.config = Config.get_instance()
        self.mongo = MongoIO.get_instance()
        self.collection_configs = collection_configs or {}
        self.types: Dict = {}
        self.enumerators: List[Dict] = []
        self.dictionaries: Dict = {}

        # Load all schema definitions
        self.load_errors: List[Dict] = []
        self.load_errors.extend(self._load_types())
        self.load_errors.extend(self._load_enumerators())
        self.load_errors.extend(self._load_dictionaries())
        
        # If collection_configs wasn't provided, load them
        if not self.collection_configs:
            self._load_collection_configs()
            
        # Resolve $ref values in dictionaries (after all dictionaries are loaded)
        ref_errors = self._resolve_refs()
        self.load_errors.extend(ref_errors)
        
    def _load_types(self) -> List[Dict]:
        """Load type definitions.
        
        Returns:
            List of load errors
        """
        errors = []
        types_dir = os.path.join(self.config.INPUT_FOLDER, "types")
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
            
    def _resolve_refs(self) -> List[Dict]:
        """Resolve all $ref values in loaded dictionaries.
        
        This method recursively traverses all dictionary definitions and replaces
        $ref objects with the actual referenced dictionary content.
        
        Returns:
            List of errors encountered during resolution
        """
        ref_errors = []
        
        # Create a temporary copy of dictionaries for resolution
        resolved = {}
        
        for dict_name, dict_def in self.dictionaries.items():
            resolved_def, errors = self._resolve_refs_in_object(dict_def, dict_name, set())
            resolved[dict_name] = resolved_def
            ref_errors.extend(errors)
            
        self.dictionaries = resolved
        
        return ref_errors
        
    def _resolve_refs_in_object(self, obj: Any, dict_name: str, visited: Set[str]) -> tuple[Any, List[Dict]]:
        """Recursively resolve $ref values in an object.
        
        Args:
            obj: The object to resolve $ref values in
            dict_name: The name of the dictionary being resolved
            visited: Set of already visited paths (for cycle detection)
            
        Returns:
            Tuple of (resolved_object, list_of_errors)
        """
        errors = []
        if isinstance(obj, dict):
            # Check if this is a $ref object
            if "$ref" in obj:
                ref_name = obj["$ref"]
                if ref_name in visited:
                    errors.append({
                        "error": "circular_reference",
                        "error_id": "SCH-013",
                        "dict_name": dict_name,
                        "ref_name": ref_name,
                        "message": f"Circular reference detected: {ref_name}"
                    })
                    return obj, errors
                elif ref_name not in self.dictionaries:
                    errors.append({
                        "error": "ref_not_found",
                        "error_id": "SCH-014",
                        "dict_name": dict_name,
                        "ref_name": ref_name,
                        "message": f"Referenced dictionary not found: {ref_name}"
                    })
                    return obj, errors
                else:
                    # Resolve the reference - replace the entire object with the referenced content
                    visited.add(ref_name)
                    resolved, ref_errors = self._resolve_refs_in_object(self.dictionaries[ref_name], dict_name, visited)
                    visited.remove(ref_name)
                    errors.extend(ref_errors)
                    return resolved, errors
                    
            # Otherwise, recursively resolve all values in the dictionary
            resolved = {}
            for key, value in obj.items():
                resolved_value, value_errors = self._resolve_refs_in_object(value, dict_name, visited)
                resolved[key] = resolved_value
                errors.extend(value_errors)
            return resolved, errors
            
        elif isinstance(obj, list):
            # Recursively resolve all items in the list
            resolved_items = []
            for item in obj:
                resolved_item, item_errors = self._resolve_refs_in_object(item, dict_name, visited)
                resolved_items.append(resolved_item)
                errors.extend(item_errors)
            return resolved_items, errors
        else:
            # Primitive value, return as-is
            return obj, errors

    def _load_collection_configs(self) -> None:
        """Load collection configurations from the input folder.
        
        This method is only called if collection_configs is not provided in the constructor.
        """
        collections_folder = os.path.join(self.config.INPUT_FOLDER, "collections")
        logger.info(f"Loading collections from {collections_folder}")
        
        if not os.path.exists(collections_folder):
            self.load_errors.append({
                "error": "directory_not_found",
                "error_id": "CFG-001",
                "path": collections_folder,
                "message": "Collections directory not found"
            })
            return
            
        # Load all YAML files from collections folder
        for file in os.listdir(collections_folder):
            if not file.endswith(".yaml"):
                continue
                
            file_path = os.path.join(collections_folder, file)
            try:
                with open(file_path, "r") as f:
                    data = yaml.safe_load(f)
                    key = os.path.splitext(file)[0]
                    self.collection_configs[key] = data
            except yaml.YAMLError as e:
                self.load_errors.append({
                    "error": "parse_error",
                    "error_id": "CFG-002",
                    "file": file,
                    "message": str(e)
                })
            except Exception as e:
                self.load_errors.append({
                    "error": "load_error",
                    "error_id": "CFG-003",
                    "file": file,
                    "message": str(e)
                })
                
        logger.info(f"Loaded {len(self.collection_configs)} collection configurations")
            
    def validate_schema(self) -> List[Dict]:
        """Validate all loaded schema definitions.
        
        Returns:
            List of validation errors
        """
        errors = []
        
        # Create validation context
        context: SchemaContext = {
            "types": self.types,
            "enumerators": self.enumerators,
            "dictionaries": self.dictionaries,
            "collection_configs": self.collection_configs,
            "schema_name": None,
            "format": None
        }
        
        errors.extend(SchemaValidator.validate_schema(context))
        return errors
        
    def render_one(self, schema_name: str, format: SchemaFormat) -> Dict:
        """Render a single schema version.
        
        Args:
            schema_name: Name in the form collection.1.2.3.4
            format: Target schema format
            
        Returns:
            Dict containing the rendered schema
        """        
        # Create schema context
        context: SchemaContext = {
            "types": self.types,
            "dictionaries": self.dictionaries,
            "enumerators": self.enumerators,
            "collection_configs": self.collection_configs
        }
        
        return SchemaRenderer.render_schema(schema_name, format, context)

    def render_all(self) -> Dict:
        """Render all schemas in both BSON and JSON formats.
        
        Returns:
            Dict containing rendered schemas for all collections and versions
        """
        rendered = {}
        
        for collection_name, collection_config in self.collection_configs.items():
            for version_config in collection_config["versions"]:
                # Get version string and ensure it has collection name
                version_name = f"{collection_name}.{version_config["version"]}"
                rendered[version_name] = {}
                
                # Render in both formats
                for format in [SchemaFormat.BSON, SchemaFormat.JSON]:
                    rendered[version_name][format.value] = self.render_one(version_name, format)
                    
        return rendered

    def apply_schema(self, version_name: str) -> Dict:
        """Apply a schema to a collection.
        
        Args:
            version_name: Name of the collection version (e.g. user.1.0.0.1)
            
        Returns:
            Dict containing operation result in consistent format
        """
        # Extract collection name using VersionNumber class (version_name is already validated)
        try:
            version = VersionNumber(version_name)
            collection_name = version.collection_name
        except ValueError as e:
            # Handle case where VersionNumber fails (shouldn't happen if properly validated)
            return {
                "operation": "apply_schema",
                "collection": version_name,  # Use version_name as fallback
                "message": f"Invalid version format: {str(e)}",
                "details_type": "error",
                "details": {
                    "error": str(e)
                },
                "status": "error"
            }
        
        try:
            # Render and apply schema
            bson_schema = self.render_one(version_name, SchemaFormat.BSON)
            self.mongo.apply_schema(collection_name, bson_schema)
        except ValueError as e:
            return {
                "operation": "apply_schema",
                "collection": collection_name,
                "message": f"Invalid version format: {str(e)}",
                "details_type": "error",
                "details": {
                    "error": str(e)
                },
                "status": "error"
            }
        except Exception as e:
            return {
                "operation": "apply_schema",
                "collection": collection_name,
                "message": str(e),
                "details_type": "error",
                "details": {
                    "error": str(e)
                },
                "status": "error"
            }
        
        return {
            "operation": "apply_schema",
            "collection": collection_name,
            "message": f"Schema applied successfully for {version_name}",
            "details_type": "schema",
            "details": {
                "schema": bson_schema,
                "version": version_name.split(".")[-1] if "." in version_name else ""
            },
            "status": "success"
        }

    def remove_schema(self, collection_name: str) -> Dict:
        """Remove schema validation from a collection.
        
        Args:
            collection_name: Name of the collection (e.g. user)
            
        Returns:
            Dict containing operation result in consistent format
        """
        try:
            # Remove schema validation
            self.mongo.remove_schema(collection_name)
        except ValueError as e:
            return {
                "operation": "remove_schema",
                "collection": collection_name,
                "message": f"Invalid version format: {str(e)}",
                "details_type": "error",
                "details": {
                    "error": str(e)
                },
                "status": "error"
            }
        except Exception as e:
            return {
                "operation": "remove_schema",
                "collection": collection_name,
                "message": str(e),
                "details_type": "error",
                "details": {
                    "error": str(e)
                },
                "status": "error"
            }

        return {
            "operation": "remove_schema",
            "collection": collection_name,
            "message": f"Schema validation removed from {collection_name}",
            "status": "success"
        } 