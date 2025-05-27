from typing import Dict, List, Optional, Union, TypedDict, Set
from enum import Enum
from stage0_py_utils import MongoIO
import yaml
import os
import re
import json

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
    json_type: Dict  # JSON Schema validation rules
    bson_type: Dict  # BSON Schema validation rules

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
        __init__(input_path: str) -> None
        
    Public Methods:
        validate_schema() -> List[str]
        render_schema(schema_name: str, format: SchemaFormat = SchemaFormat.BSON_SCHEMA) -> Dict
        apply_schema(collection_name: str, schema_name: str) -> Dict
        remove_schema(collection_name: str) -> Dict

    See /docs/schema.md, /docs/processing.md for more details.
    """
    
    SCHEMA_NAME_PATTERN = r'^[a-zA-Z][a-zA-Z0-9_]*$'
    VERSION_PATTERN = r'^\d+\.\d+\.\d+$'
    VALID_TYPES = {t.value for t in SchemaType}
    
    def __init__(self, input_path: str):
        """Initialize the schema manager with input path.
        
        Args:
            input_path: Path to the input directory containing dictionary, types, and data folders
            
        Raises:
            ValueError: If input_path is empty or invalid
            FileNotFoundError: If required input files are missing
            SchemaError: If input files contain invalid content
        """
        if not input_path:
            raise ValueError("Input path cannot be empty")
            
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input path does not exist: {input_path}")
            
        self.input_path = input_path
        self.mongo = MongoIO.get_instance()
        self.types: Dict[str, Dict] = {}
        self.enumerators: Dict[str, Dict] = {}
        self.dictionaries: Dict[str, Schema] = {}
        
        self._load_types()
        self._load_enumerators()
        self._load_dictionaries()

    def _load_types(self) -> None:
        """Load type definitions from the types directory.
        
        Raises:
            FileNotFoundError: If types directory is missing
            SchemaError: If type definition fails to parse
        """
        types_dir = os.path.join(self.input_path, "dictionary", "types")
        if not os.path.exists(types_dir):
            raise FileNotFoundError(f"Types directory not found: {types_dir}")
            
        for file in os.listdir(types_dir):
            if file.endswith(".yaml"):
                with open(os.path.join(types_dir, file), 'r') as f:
                    try:
                        type_def = yaml.safe_load(f)
                        key = os.path.splitext(file)[0]
                        self.types[key] = type_def
                    except yaml.YAMLError as e:
                        raise SchemaError(f"Failed to parse type definition in {file}: {str(e)}")

    def _load_enumerators(self) -> None:
        """Load enumerators from the data directory.
        
        Raises:
            FileNotFoundError: If data directory or enumerators file is missing
            SchemaError: If enumerators file fails to parse
        """
        data_dir = os.path.join(self.input_path, "data")
        if not os.path.exists(data_dir):
            raise FileNotFoundError(f"Data directory not found: {data_dir}")
            
        enumerators_file = os.path.join(data_dir, "enumerators.json")
        if not os.path.exists(enumerators_file):
            raise FileNotFoundError(f"Enumerators file not found: {enumerators_file}")
            
        with open(enumerators_file, 'r') as f:
            try:
                self.enumerators = json.load(f)
            except json.JSONDecodeError as e:
                raise SchemaError(f"Failed to parse enumerators file: {str(e)}")

    def _load_dictionaries(self) -> None:
        """Load dictionary definitions from the dictionary directory.
        
        Raises:
            FileNotFoundError: If dictionary directory is missing
            SchemaError: If dictionary definition fails to parse
        """
        dict_dir = os.path.join(self.input_path, "dictionary")
        if not os.path.exists(dict_dir):
            raise FileNotFoundError(f"Dictionary directory not found: {dict_dir}")
            
        for file in os.listdir(dict_dir):
            if file.endswith(".yaml"):
                # Extract version from filename
                name_parts = os.path.splitext(file)[0].split(".")
                if len(name_parts) < 2 or not re.match(self.VERSION_PATTERN, name_parts[-1]):
                    raise SchemaError(f"Invalid schema version format in {file}")
                    
                with open(os.path.join(dict_dir, file), 'r') as f:
                    try:
                        dict_def = yaml.safe_load(f)
                        key = os.path.splitext(file)[0]
                        self.dictionaries[key] = dict_def
                    except yaml.YAMLError as e:
                        raise SchemaError(f"Failed to parse dictionary definition in {file}: {str(e)}")

    def validate_schema(self) -> List[str]:
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

    def render_schema(self, schema_name: str, format: SchemaFormat = SchemaFormat.BSON_SCHEMA) -> Dict:
        """Render a schema in the specified format.
        
        Args:
            schema_name: Name of the schema to render
            format: Target schema format (JSON_SCHEMA or BSON_SCHEMA)
            
        Returns:
            Dict containing the rendered schema
            
        Raises:
            ValueError: If schema_name is empty or invalid
            SchemaValidationError: If schema validation fails
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
            return self._render_bson_schema(schema)
        else:
            return self._render_json_schema(schema)

    def _render_bson_schema(self, schema_def: Dict) -> Dict:
        """Render a BSON schema."""
        schema = {
            "bsonType": "object",
            "required": schema_def.get("required", []),
            "properties": {}
        }
        
        for prop_name, prop_def in schema_def["properties"].items():
            schema["properties"][prop_name] = self._resolve_property(prop_def)
            
        return schema

    def _render_json_schema(self, schema_def: Dict) -> Dict:
        """Render a JSON schema."""
        schema = {
            "type": "object",
            "required": schema_def.get("required", []),
            "properties": {}
        }
        
        for prop_name, prop_def in schema_def["properties"].items():
            schema["properties"][prop_name] = self._resolve_property(prop_def, is_json=True)
            
        return schema

    def _resolve_property(self, prop_def: Schema, is_json: bool = False) -> Dict:
        """Resolve a property definition to its primitive type.
        
        Args:
            prop_def: Property definition to resolve
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
            resolved.update(self._resolve_enum(prop_def["enums"], is_json))
        elif type_name == SchemaType.OBJECT.value and "properties" in prop_def:
            resolved.update(self._resolve_schema({"type": "object", "properties": prop_def["properties"]}, is_json))
        elif type_name == SchemaType.ARRAY.value and "items" in prop_def:
            resolved_items = self._resolve_property(prop_def["items"], is_json)
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

    def _resolve_enum(self, enum_name: str, is_json: bool) -> Dict:
        """Resolve an enumerator definition."""
        enum_def = self.enumerators[enum_name]
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

    def _resolve_schema(self, schema_def: Schema, is_json: bool = False) -> Dict:
        """Resolve a schema definition to its primitive type.
        
        Args:
            schema_def: Schema definition to resolve
            is_json: Whether to resolve to JSON Schema format
            
        Returns:
            Resolved schema definition
            
        Example:
            >>> manager._resolve_schema({"type": "object", "properties": {"status": {"type": "enum", "enums": "status"}}})
            {"type": "object", "properties": {"status": {"type": "string", "enum": ["Active", "Inactive"]}}}
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
            resolved["properties"][prop_name] = self._resolve_property(prop_def, is_json)
            
        return resolved

    def apply_schema(self, collection_name: str, schema_name: str) -> Dict:
        """Apply a schema to a collection.
        
        Args:
            collection_name: Name of the collection
            schema_name: Name of the schema to apply
            
        Returns:
            Dict containing operation result:
            {
                "status": "success",
                "operation": "apply_schema",
                "collection": str,
                "schema": str
            }
            
        Raises:
            ValueError: If collection_name or schema_name is empty or invalid
            SchemaValidationError: If schema validation fails
        """
        if not collection_name:
            raise ValueError("Collection name cannot be empty")
            
        if not schema_name:
            raise ValueError("Schema name cannot be empty")
            
        schema = self.render_schema(schema_name, SchemaFormat.BSON_SCHEMA)
        self.mongo.update_document(
                    collection_name,
            set_data={"validator": {"$jsonSchema": schema}}
        )
        return {
            "status": "success",
            "operation": "apply_schema",
            "collection": collection_name,
            "schema": schema_name
        }

    def remove_schema(self, collection_name: str) -> Dict:
        """Remove schema validation from a collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Dict containing operation result:
            {
                "status": "success",
                "operation": "remove_schema",
                "collection": str
            }
            
        Raises:
            ValueError: If collection_name is empty
        """
        if not collection_name:
            raise ValueError("Collection name cannot be empty")
            
        self.mongo.update_document(
            collection_name,
            set_data={"validator": {}}
        )
            return {
            "status": "success",
            "operation": "remove_schema",
            "collection": collection_name
            } 