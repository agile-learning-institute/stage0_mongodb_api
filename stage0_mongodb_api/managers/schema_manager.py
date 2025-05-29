from typing import Dict, List, Optional, Union, TypedDict, Set
from enum import Enum
from stage0_py_utils import MongoIO, Config
import yaml
import os
import re
import json
from stage0_mongodb_api.managers.version_number import VersionNumber
from stage0_mongodb_api.managers.config_manager import ConfigManager

class SchemaType(Enum):
    """Valid schema types."""
    ARRAY = "array"
    OBJECT = "object"
    ENUM = "enum"
    ENUM_ARRAY = "enum_array"
    ONE_OF = "one_of"

class SchemaFormat(Enum):
    """Schema output format."""
    JSON_SCHEMA = "json_schema"
    BSON_SCHEMA = "bson_schema"

class PrimitiveType(TypedDict):
    """Type definition for primitive types (string, number, boolean, etc).
    
    These types map directly to JSON/BSON types and don't need complex validation.
    """
    description: str
    schema: Dict     # Rules for both JSON and BSON when the only difference is type vs. bsonType
    json_type: Dict  # JSON Schema specific validation rules
    bson_type: Dict  # BSON Schema specific validation rules

class Schema(TypedDict):
    """Type definition for schema and schema properties.
    
    A schema can be either a root schema or a property definition.
    Root schemas require title, description, and type.
    Property definitions require description and type.
    """
    title: Optional[str]                        # Required for root schemas
    description: str
    type: str
    required: Optional[bool]                    # Default is False
    properties: Optional[Dict[str, 'Schema']]   # Required for object type only
    additionalProperties: Optional[bool]        # For object type, default is False
    items: Optional['Schema']                   # Required for array type only
    enums: Optional[str]                        # Required for enum and enum_array types only
    type_property: Optional[str]                # Required for one_of type only
    schemas: Optional[Dict[str, 'Schema']]      # Required for one_of type only

class SchemaError(Exception):
    """Base exception for schema-related errors."""
    pass

class SchemaValidationError(SchemaError):
    """Exception raised when schema validation fails."""
    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__("\n".join(errors))

class SchemaManager:
    """Implements the stage0 Simple Schema standard.
    
    Constructor:
        __init__() -> None : Initialize the schema manager, load all the schemas and types from the input folder
        
    Public Methods:
        validate_schema() -> List[str]
        render_schema(schema_name: str, format: SchemaFormat = SchemaFormat.BSON_SCHEMA) -> Dict
        apply_schema(collection_name: str, bson_schema: Dict) -> Dict
        remove_schema(collection_name: str) -> Dict

    See /docs/schema.md, /docs/processing.md for more details.
    """
    
    SCHEMA_NAME_PATTERN = r'^[a-zA-Z][a-zA-Z0-9_]*$'
    VERSION_PATTERN = r'^\d+\.\d+\.\d+$'  # Three-part version for schema files
    VALID_TYPES = {t.value for t in SchemaType}
    
    def __init__(self):
        """Initialize the schema manager with input path."""
        self.config = Config.get_instance()
        self.mongo = MongoIO.get_instance()
        self.config_manager = ConfigManager()
        self.types: Dict[str, Dict] = {}
        self.enumerators: List[Dict] = []  
        self.dictionaries: Dict[str, Schema] = {}
        self.config_manager = ConfigManager()
        self.load_errors: List[Dict] = []
        
        # Load and validate all components
        self.load_errors.extend(self._load_types())
        self.load_errors.extend(self._load_enumerators())
        self.load_errors.extend(self._load_dictionaries())

    def _load_types(self) -> List[Dict]:
        """Load type definitions from the types directory.
        
        Returns:
            List of load errors. Empty list indicates all types loaded successfully.
        """
        errors = []
        types_dir = os.path.join(self.config.INPUT_FOLDER, "dictionary", "types")
        if not os.path.exists(types_dir):
            errors.append({"error": "directory_not_found", "path": types_dir})
            return errors
            
        for file in os.listdir(types_dir):
            if file.endswith(".yaml"):
                try:
                    with open(os.path.join(types_dir, file), 'r') as f:
                        type_def = yaml.safe_load(f)
                        key = os.path.splitext(file)[0]
                        self.types[key] = type_def
                except yaml.YAMLError as e:
                    errors.append({
                        "error": "parse_error",
                        "file": file,
                        "message": str(e)
                    })
                except Exception as e:
                    errors.append({
                        "error": "load_error",
                        "file": file,
                        "message": str(e)
                    })
                    
        return errors

    def _load_enumerators(self) -> List[Dict]:
        """Load enumerators from the data directory.
        
        Returns:
            List of load errors. Empty list indicates all enumerators loaded successfully.
        """
        errors = []
        data_dir = os.path.join(self.config.INPUT_FOLDER, "data")
        if not os.path.exists(data_dir):
            errors.append({"error": "directory_not_found", "path": data_dir})
            return errors
            
        enumerators_file = os.path.join(data_dir, "enumerators.json")
        if not os.path.exists(enumerators_file):
            errors.append({"error": "file_not_found", "path": enumerators_file})
            return errors
            
        try:
            with open(enumerators_file, 'r') as f:
                self.enumerators = json.load(f)
                if not isinstance(self.enumerators, list):
                    errors.append({
                        "error": "invalid_format",
                        "file": "enumerators.json",
                        "message": "must be a list of versioned enumerators"
                    })
        except json.JSONDecodeError as e:
            errors.append({
                "error": "parse_error",
                "file": "enumerators.json",
                "message": str(e)
            })
        except Exception as e:
            errors.append({
                "error": "load_error",
                "file": "enumerators.json",
                "message": str(e)
            })
            
        return errors

    def _load_dictionaries(self) -> List[Dict]:
        """Load dictionary definitions from the dictionary directory.
        
        Returns:
            List of load errors. Empty list indicates all dictionaries loaded successfully.
        """
        errors = []
        dict_dir = os.path.join(self.config.INPUT_FOLDER, "dictionary")
        if not os.path.exists(dict_dir):
            errors.append({"error": "directory_not_found", "path": dict_dir})
            return errors
            
        for file in os.listdir(dict_dir):
            if file.endswith(".yaml"):
                try:
                    # Parse schema name and version
                    schema_name = os.path.splitext(file)[0]
                    collection_name, version = VersionNumber.from_schema_name(schema_name)
                    
                    with open(os.path.join(dict_dir, file), 'r') as f:
                        dict_def = yaml.safe_load(f)
                        self.dictionaries[schema_name] = dict_def
                except ValueError as e:
                    errors.append({
                        "error": "invalid_version",
                        "file": file,
                        "message": str(e)
                    })
                except yaml.YAMLError as e:
                    errors.append({
                        "error": "parse_error",
                        "file": file,
                        "message": str(e)
                    })
                except Exception as e:
                    errors.append({
                        "error": "load_error",
                        "file": file,
                        "message": str(e)
                    })
                    
        return errors

    def validate_schema(self) -> List[str]:
        """Validate all loaded schemas and configurations against the stage0 Simple Schema standard.
        
        Args:
            collection_name: Optional collection name for context-aware validation
            
        Returns:
            List of validation errors. Empty list indicates all configurations are valid.
        """
        errors = []
        
        # Validate collection configs
        errors.extend(self.config_manager.validate_configs())
        
        # Validate enumerators first
        errors.extend(self._validate_enumerators())
        
        # Validate all custom types
        for type_name, type_def in self.types.items():
            errors.extend(self._validate_type(type_def, type_name))
            
        # Validate all schemas in all collection contexts
        for config in self.config_manager.collection_configs:
            collection_name = config.get("name")
                
            # Validate each version in the collection config
            for version_str in config.get("versions", []):
                version = VersionNumber.from_collection_config(collection_name, version_str)
                schema_name = version.get_schema_name()
                enum_version = version.get_enumerator_version()
                    
                if schema_name not in self.dictionaries:
                    errors.append({
                        "error": "schema_not_found",
                        "schema_name": schema_name,
                        "collection_name": collection_name
                    })
                    continue

                errors.extend(self._validate_type(
                    schema=self.dictionaries[schema_name], 
                    path=schema_name,
                    enum_version=enum_version
                ))
            
        return errors

    def _validate_enumerators(self) -> List[str]:
        """Validate enumerator definitions against the schema.
        
        Returns:
            List of validation errors
        """
        errors = []
        
        # Validate each enumerator version
        for version in self.enumerators:
            # Validate required fields
            if "name" not in version:
                errors.append("Enumerator version missing required field 'name'")
            elif not re.match(r'^[A-Z][a-zA-Z0-9_]*$', version["name"]):
                errors.append(f"Invalid enumerator name format: {version['name']}")
                
            if "status" not in version:
                errors.append("Enumerator version missing required field 'status'")
            elif version["status"] not in ["Active", "Deprecated"]:
                errors.append(f"Invalid enumerator status: {version['status']}")
                
            if "version" not in version:
                errors.append("Enumerator version missing required field 'version'")
            elif not isinstance(version["version"], int) or version["version"] < 0:
                errors.append(f"Invalid enumerator version number: {version['version']}")
                
            if "enumerators" not in version:
                errors.append("Enumerator version missing required field 'enumerators'")
            elif not isinstance(version["enumerators"], dict):
                errors.append("Enumerator version 'enumerators' must be a dictionary")
            else:
                # Validate each enumerator definition
                for enum_name, enum_def in version["enumerators"].items():
                    if not isinstance(enum_def, dict):
                        errors.append(f"Enumerator '{enum_name}' must be a dictionary")
                    else:
                        # Validate each value has a description
                        for value, description in enum_def.items():
                            if not isinstance(description, str):
                                errors.append(f"Enumerator '{enum_name}' value '{value}' must have a string description")
                                
        return errors

    def _validate_type(self, schema: Dict, path: str, enum_version: Optional[int] = None) -> List[str]:
        """Validate a schema or type definition.
        
        Args:
            schema: Schema or type definition to validate
            path: Path to the schema/type for error messages
            enum_version: Optional enumerator version number for context-aware validation
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Validate schema is a dictionary
        if not isinstance(schema, dict):
            errors.append(f"{path} must be a dictionary")
            return errors

        # Check if this is a primitive type
        has_schema = "schema" in schema
        has_json_type = "json_type" in schema
        has_bson_type = "bson_type" in schema
        
        if has_schema or has_json_type or has_bson_type:
            errors.extend(self._validate_primitive_type(schema, path))
        else:
            errors.extend(self._validate_schema_type(schema, path, enum_version))
                
        return errors

    def _validate_primitive_type(self, schema: Dict, path: str) -> List[str]:
        """Validate a primitive type definition.
        
        Args:
            schema: Primitive type definition to validate
            path: Path to the type for error messages
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Check for valid schema/json_type/bson_type combination
        has_schema = "schema" in schema
        has_json_type = "json_type" in schema
        has_bson_type = "bson_type" in schema
        
        if has_schema:
            if has_json_type or has_bson_type:
                errors.append(f"Primitive type {path} cannot have both 'schema' and *_type fields")
        else:
            if not (has_json_type and has_bson_type):
                errors.append(f"Primitive type {path} must have either 'schema' or both 'json_type' and 'bson_type' fields")
        
        # Validate required fields
        if "description" not in schema:
            errors.append(f"Primitive type {path} missing required field 'description'")
            
        # Validate schema/json_type/bson_type are valid JSON
        for field in ["schema", "json_type", "bson_type"]:
            if field in schema:
                try:
                    json.dumps(schema[field])
                except (TypeError, ValueError):
                    errors.append(f"Primitive type {path} has invalid {field}: must be valid JSON")
                    
        return errors

    def _validate_schema_type(self, schema: Dict, path: str, enum_version: int) -> List[str]:
        """Validate a schema type definition.
        
        Args:
            schema: Schema definition to validate
            path: Path to the schema for error messages
            enum_version: Optional enumerator version number for context-aware validation
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Validate required fields
        if "description" not in schema:
            errors.append(f"Missing required field 'description' in {path}")
            
        if "type" not in schema:
            errors.append(f"Missing required field 'type' in {path}")
            return errors
            
        # Validate type is valid
        type_name = schema["type"]
        if type_name not in self.VALID_TYPES and type_name not in self.types:
            errors.append(f"Invalid type '{type_name}' in {path}")
            return errors
            
        # Validate type-specific properties
        if type_name == SchemaType.OBJECT.value:
            errors.extend(self._validate_object_type(schema, path, enum_version))
        elif type_name == SchemaType.ARRAY.value:
            errors.extend(self._validate_array_type(schema, path, enum_version))
        elif type_name in [SchemaType.ENUM.value, SchemaType.ENUM_ARRAY.value]:
            errors.extend(self._validate_enum_type(schema, path, enum_version))
        elif type_name == SchemaType.ONE_OF.value:
            errors.extend(self._validate_one_of_type(schema, path, enum_version))
        elif type_name in self.types:
            # Validate custom type recursively
            type_def = self.types[type_name]
            errors.extend(self._validate_type(type_def, path, enum_version))
            
        return errors

    def _validate_object_type(self, schema: Dict, path: str, enum_version: int) -> List[str]:
        """Validate an object type definition."""
        errors = []
        if "properties" not in schema:
            errors.append(f"Object type must have properties definition in {path}")
        else:
            for prop_name, prop_def in schema["properties"].items():
                errors.extend(self._validate_type(prop_def, f"{path}.{prop_name}", enum_version))
        return errors

    def _validate_array_type(self, schema: Dict, path: str, enum_version: Optional[int] = None) -> List[str]:
        """Validate an array type definition."""
        errors = []
        if "items" not in schema:
            errors.append(f"Array type must have items definition in {path}")
        else:
            errors.extend(self._validate_type(schema["items"], f"{path}.items", enum_version))
        return errors

    def _validate_enum_type(self, schema: Dict, path: str, enum_version: int) -> List[str]:
        """Validate an enum type definition.
        
        Args:
            schema: Schema definition to validate
            path: Path to the schema for error messages
            enum_version: Enumerator version number for context-aware validation
            
        Returns:
            List of validation errors
        """
        errors = []
        if "enums" not in schema:
            errors.append(f"{schema['type']} type must have enums reference in {path}")
            return errors
            
        enum_name = schema["enums"]
                
        # Find the version entry using next() with a generator expression
        version_entry = next(
            (entry for entry in self.enumerators 
             if entry["version"] == enum_version and entry["status"] == "Active"),
            None
        )
                
        if not version_entry:
            errors.append(f"No active enumerator version {enum_version} found")
            return errors
            
        # Check if enumerator exists in this version
        if enum_name not in version_entry["enumerators"]:
            errors.append(f"Unknown enumerator '{enum_name}' in version {enum_version} referenced in {path}")
            return errors
                    
        return errors

    def _validate_one_of_type(self, schema: Dict, path: str, enum_version: Optional[int] = None) -> List[str]:
        """Validate a one_of type definition."""
        errors = []
        if "type_property" not in schema:
            errors.append(f"one_of type must have type_property definition in {path}")
        if "schemas" not in schema:
            errors.append(f"one_of type must have schemas definition in {path}")
        elif not isinstance(schema["schemas"], dict):
            errors.append(f"Invalid schemas value in {path}: must be a dictionary")
        else:
            for schema_name, schema_def in schema["schemas"].items():
                errors.extend(self._validate_type(schema_def, f"{path}.schemas.{schema_name}", enum_version))
        return errors

    def _resolve_enum(self, enum_name: str, collection_name: str, is_json: bool) -> Dict:
        """Resolve an enumerator definition for a specific collection.
        
        Args:
            enum_name: Name of the enumerator
            collection_name: Name of the collection (used to get version)
            is_json: Whether to resolve to JSON Schema format
            
        Returns:
            Resolved enumerator definition
            
        Raises:
            KeyError: If enumerator or version not found
        """
        version = self._get_enumerator_version(collection_name)
        enum_def = self._get_enumerator_for_version(enum_name, version)
        
        if is_json:
            return {
                "type": "string",
                "enum": list(enum_def.keys())
            }
        else:
            return {
                "bsonType": "string",
                "enum": list(enum_def.keys())
            }

    def _resolve_property(self, prop_def: Schema, collection_name: str, is_json: bool = False) -> Dict:
        """Resolve a property definition to its primitive type.
        
        Args:
            prop_def: Property definition to resolve
            collection_name: Name of the collection (used for version-specific enumerators)
            is_json: Whether to resolve to JSON Schema format
            
        Returns:
            Resolved property definition
        """
        if "type" not in prop_def:
            return prop_def
            
        type_name = prop_def["type"]
        resolved = {}
        
        # Copy title and description if present
        if "title" in prop_def:
            resolved["title"] = prop_def["title"]
        if "description" in prop_def:
            resolved["description"] = prop_def["description"]
            
        if type_name in self.types:
            resolved.update(self._resolve_type(self.types[type_name], is_json))
        elif type_name in [SchemaType.ENUM.value, SchemaType.ENUM_ARRAY.value]:
            resolved.update(self._resolve_enum(prop_def["enums"], collection_name, is_json))
        elif type_name == SchemaType.OBJECT.value and "properties" in prop_def:
            resolved.update(self._resolve_schema({"type": "object", "properties": prop_def["properties"]}, collection_name, is_json))
        elif type_name == SchemaType.ARRAY.value and "items" in prop_def:
            resolved_items = self._resolve_property(prop_def["items"], collection_name, is_json)
            resolved.update({
                "type": "array" if is_json else "array",
                "items": resolved_items
            })
            
        return resolved

    def _resolve_type(self, type_def: Dict, is_json: bool) -> Dict:
        """Resolve a type definition to its primitive type."""
        if is_json:
            return type_def["json_type"]
        else:
            return type_def["bson_type"]

    def _resolve_schema(self, schema_def: Schema, collection_name: str, is_json: bool = False) -> Dict:
        """Resolve a schema definition to its primitive type.
        
        Args:
            schema_def: Schema definition to resolve
            collection_name: Name of the collection (used for version-specific enumerators)
            is_json: Whether to resolve to JSON Schema format
            
        Returns:
            Resolved schema definition
        """
        if not schema_def.get("properties"):
            return schema_def
            
        resolved = {
            "type": "object" if is_json else "object",
            "properties": {}
        }
        
        if "required" in schema_def:
            resolved["required"] = schema_def["required"]
            
        for prop_name, prop_def in schema_def["properties"].items():
            resolved["properties"][prop_name] = self._resolve_property(prop_def, collection_name, is_json)
            
        return resolved

    def render_schema(self, schema_name: str, collection_name: str, format: SchemaFormat = SchemaFormat.BSON_SCHEMA) -> Dict:
        """Render a schema in the specified format.
        
        Args:
            schema_name: Name of the schema to render
            collection_name: Name of the collection (used for version-specific enumerators)
            format: Target schema format (JSON_SCHEMA or BSON_SCHEMA)
            
        Returns:
            Dict containing the rendered schema
            
        Raises:
            ValueError: If schema_name is empty or invalid
            SchemaValidationError: If schema validation fails
            KeyError: If collection configuration not found
        """
        if not schema_name:
            raise ValueError("Schema name cannot be empty")
            
        if not re.match(self.SCHEMA_NAME_PATTERN, schema_name):
            raise ValueError(f"Invalid schema name format: {schema_name}")
            
        # Validate schema before rendering
        errors = self.validate_schema()
        if errors:
            raise SchemaValidationError(errors)
            
        schema = self._load_schema(schema_name)
        
        if format == SchemaFormat.BSON_SCHEMA:
            return self._render_bson_schema(schema, collection_name)
        else:
            return self._render_json_schema(schema, collection_name)

    def _render_bson_schema(self, schema_def: Dict, collection_name: str) -> Dict:
        """Render a BSON schema."""
        schema = {
            "bsonType": "object",
            "required": schema_def.get("required", []),
            "properties": {}
        }
        
        for prop_name, prop_def in schema_def["properties"].items():
            schema["properties"][prop_name] = self._resolve_property(prop_def, collection_name, is_json=False)
            
        return schema

    def _render_json_schema(self, schema_def: Dict, collection_name: str) -> Dict:
        """Render a JSON schema."""
        schema = {
            "type": "object",
            "required": schema_def.get("required", []),
            "properties": {}
        }
        
        for prop_name, prop_def in schema_def["properties"].items():
            schema["properties"][prop_name] = self._resolve_property(prop_def, collection_name, is_json=True)
            
        return schema

    def apply_schema(self, version_name: str) -> Dict:
        """Apply a schema to a collection.
        
        Args:
            collection_name: Name of the collection version (e.g. user.1.0.0.1)
            bson_schema: BSON schema to apply
            
        Returns:
            Dict containing operation result
            
        """
        if not version_name:
            return {
                "status": "error",
                "operation": "apply_schema",
                "collection": collection_name,
                "message": "Collection name cannot be empty"
            }

        [collection_name, version_number] = version_name.split(".")
        try:
            bson_schema = self.render_schema(version_name, SchemaFormat.BSON_SCHEMA)
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
            Dict containing operation result:

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