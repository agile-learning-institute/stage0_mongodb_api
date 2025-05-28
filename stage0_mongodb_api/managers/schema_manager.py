from typing import Dict, List, Optional, Union, TypedDict, Set
from enum import Enum
from stage0_py_utils import MongoIO, Config
import yaml
import os
import re
import json
from stage0_mongodb_api.managers.version_number import VersionNumber

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
        self.types: Dict[str, Dict] = {}
        self.enumerators: List[Dict] = []  
        self.dictionaries: Dict[str, Schema] = {}
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

    def validate_schema(self) -> List[Dict]:
        """Validate all loaded schemas and configurations against the stage0 Simple Schema standard.
        
        Returns:
            List of validation errors. Empty list indicates all configurations are valid.
        """
        errors = []
        
        # Validate all custom types
        for type_name, type_def in self.types.items():
            errors.extend(self._validate_custom_type(type_def, type_name))
            
        # Validate all schemas
        for schema_name, schema in self.dictionaries.items():
            errors.extend(self._validate_schema_structure(schema))
            
            if "properties" in schema:
                for prop_name, prop_def in schema["properties"].items():
                    errors.extend(self._validate_property(prop_name, prop_def))
                    
                    # Validate enumerator references
                    if prop_def.get("type") in ["enum", "enum_array"]:
                        enum_name = prop_def.get("enums")
                        if enum_name not in self.enumerators:
                            errors.append(f"Schema '{schema_name}' references unknown enumerator '{enum_name}' in property '{prop_name}'")
                            
                    # Validate custom type references
                    elif prop_def.get("type") in self.types:
                        type_name = prop_def["type"]
                        if type_name not in self.types:
                            errors.append(f"Schema '{schema_name}' references unknown type '{type_name}' in property '{prop_name}'")
                
        return errors

    def _validate_schema_structure(self, schema: Schema, is_root: bool = True) -> List[str]:
        """Validate the basic structure of a schema.
        
        Args:
            schema: The schema to validate
            is_root: Whether this is a root schema (requires title)
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Validate schema is a dictionary
        if not isinstance(schema, dict):
            errors.append("Schema must be a dictionary")
            return errors
            
        # Validate required fields
        if is_root and "title" not in schema:
            errors.append("Missing required field 'title' at root level")
            
        if "description" not in schema:
            errors.append("Missing required field 'description'")
            
        if "type" not in schema:
            errors.append("Missing required field 'type'")
            return errors
            
        # Validate type is valid
        if schema["type"] not in self.VALID_TYPES:
            errors.append(f"Invalid schema type '{schema['type']}'")
            return errors
            
        # Validate type-specific properties
        type_name = schema["type"]
        valid_fields = {"title", "description", "type", "required"}
        
        if type_name == SchemaType.OBJECT.value:
            valid_fields.update({"properties", "additionalProperties"})
            if "properties" not in schema:
                errors.append("Object type must have properties definition")
        elif type_name == SchemaType.ARRAY.value:
            valid_fields.add("items")
            if "items" not in schema:
                errors.append("Array type must have items definition")
        elif type_name in [SchemaType.ENUM.value, SchemaType.ENUM_ARRAY.value]:
            valid_fields.add("enums")
            if "enums" not in schema:
                errors.append(f"{type_name} type must have enums reference")
        elif type_name == SchemaType.ONE_OF.value:
            valid_fields.update({"type_property", "schemas"})
            if "type_property" not in schema:
                errors.append("one_of type must have type_property definition")
            if "schemas" not in schema:
                errors.append("one_of type must have schemas definition")
                
        # Validate no unexpected fields
        for field in schema:
            if field not in valid_fields:
                errors.append(f"Unexpected field '{field}' for type '{type_name}'")
                
        return errors

    def _validate_property(self, prop_name: str, prop_def: Schema, path: str = "") -> List[str]:
        """Validate a property definition recursively.
        
        Args:
            prop_name: Name of the property
            prop_def: Property definition to validate
            path: Current property path for error messages
            
        Returns:
            List of validation errors
            
        """
        errors = []
        current_path = f"{path}.{prop_name}" if path else prop_name
        
        # Validate property structure
        errors.extend(self._validate_schema_structure(prop_def, is_root=False))
        if errors:
            return errors
            
        type_name = prop_def["type"]
        
        # Validate type-specific requirements
        if type_name == SchemaType.OBJECT.value:
            for sub_prop_name, sub_prop_def in prop_def["properties"].items():
                errors.extend(self._validate_property(sub_prop_name, sub_prop_def, current_path))
                
            # Validate additionalProperties if present
            if "additionalProperties" in prop_def and not isinstance(prop_def["additionalProperties"], bool):
                errors.append(f"Property {current_path} has invalid additionalProperties value: must be boolean")
                
        elif type_name == SchemaType.ARRAY.value:
            errors.extend(self._validate_property("items", prop_def["items"], current_path))
                
        elif type_name in [SchemaType.ENUM.value, SchemaType.ENUM_ARRAY.value]:
            if prop_def["enums"] not in self.enumerators:
                errors.append(f"Unknown enumerator '{prop_def['enums']}' referenced by property {current_path}")
                
        elif type_name == SchemaType.ONE_OF.value:
            if "type_property" not in prop_def:
                errors.append(f"Property {current_path} of type 'one_of' missing required type_property definition")
            if "schemas" not in prop_def:
                errors.append(f"Property {current_path} of type 'one_of' missing required schemas definition")
            elif not isinstance(prop_def["schemas"], dict):
                errors.append(f"Property {current_path} has invalid schemas value: must be a dictionary")
            else:
                for schema_name, schema_def in prop_def["schemas"].items():
                    errors.extend(self._validate_property(schema_name, schema_def, current_path))
                    
        elif type_name in self.types:
            # Validate custom type recursively
            type_def = self.types[type_name]
            errors.extend(self._validate_custom_type(type_def, current_path))
                
        return errors

    def _validate_custom_type(self, type_def: Dict, path: str) -> List[str]:
        """Validate a custom type definition.
        
        Custom types can be either primitive types (string, number, etc) or complex types
        (objects, arrays). Primitive types must have json_type and bson_type definitions.
        Complex types are validated as regular schemas.
        
        Args:
            type_def: Type definition to validate
            path: Path to the type for error messages
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Validate type is a dictionary
        if not isinstance(type_def, dict):
            errors.append(f"Custom type {path} must be a dictionary")
            return errors
            
        # Check if this is a primitive type
        if "json_type" in type_def and "bson_type" in type_def:
            # Validate primitive type
            required_fields = ["description", "json_type", "bson_type"]
            for field in required_fields:
                if field not in type_def:
                    errors.append(f"Primitive type {path} missing required field '{field}'")
                    
            # Validate JSON and BSON types are valid
            if "json_type" in type_def:
                try:
                    json.dumps(type_def["json_type"])
                except (TypeError, ValueError):
                    errors.append(f"Primitive type {path} has invalid json_type: must be valid JSON")
                    
            if "bson_type" in type_def:
                try:
                    json.dumps(type_def["bson_type"])
                except (TypeError, ValueError):
                    errors.append(f"Primitive type {path} has invalid bson_type: must be valid JSON")
        else:
            # Validate as a complex type (object or array)
            errors.extend(self._validate_schema_structure(type_def, is_root=True))
            
        return errors

    def _get_enumerator_version(self, collection_name: str) -> int:
        """Get the enumerator version from a collection configuration.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Enumerator version number
            
        Raises:
            KeyError: If collection configuration not found
        """
        # Get collection config from Config singleton
        collection_config = self.config.get_collection_config(collection_name)
        if not collection_config:
            raise KeyError(f"No configuration found for collection: {collection_name}")
            
        # Get version from config
        version = collection_config.get("version")
        if not version:
            raise KeyError(f"No version found in collection config: {collection_name}")
            
        # Parse version using VersionNumber
        try:
            _, version_number = VersionNumber.from_collection_config(collection_name, version)
            return version_number.get_enumerator_version()
        except ValueError as e:
            raise KeyError(f"Invalid version format in collection config: {version}")

    def _get_enumerator_for_version(self, enum_name: str, version: int) -> Dict:
        """Get the enumerator definition for a specific version.
        
        Args:
            enum_name: Name of the enumerator
            version: Version number to get
            
        Returns:
            Enumerator definition for the specified version
            
        Raises:
            KeyError: If enumerator or version not found
        """
        # Find the version entry
        version_entry = None
        for entry in self.enumerators:
            if entry["version"] == version and entry["status"] == "Active":
                version_entry = entry
                break
                
        if not version_entry:
            raise KeyError(f"No active enumerator version {version} found")
            
        # Get the enumerator from the version
        if enum_name not in version_entry["enumerators"]:
            raise KeyError(f"Enumerator '{enum_name}' not found in version {version}")
            
        return version_entry["enumerators"][enum_name]

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