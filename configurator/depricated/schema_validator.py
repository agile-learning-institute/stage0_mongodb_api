from typing import Dict, List, Optional, Set
import re
import json
from stage0_py_utils import Config
from stage0_mongodb_api.managers.schema_types import SchemaType, Schema, ValidationContext
from stage0_mongodb_api.managers.version_number import VersionNumber
import logging
logger = logging.getLogger(__name__)

class SchemaError(Exception):
    """Base exception for schema-related errors."""
    pass

class SchemaValidationError(SchemaError):
    """Exception raised when schema validation fails."""
    def __init__(self, errors: List[Dict]):
        self.errors = errors
        super().__init__("\n".join(str(error) for error in errors))

class SchemaValidator:
    """Static utility class for validating schemas."""
    
    SCHEMA_NAME_PATTERN = r'^[a-zA-Z][a-zA-Z0-9_]*$'
    VALID_TYPES = {t.value for t in SchemaType}
    
    @staticmethod
    def validate_schema(context: ValidationContext) -> List[Dict]:
        """Validate schema definitions against collection configurations.
        
        Args:
            context: Validation context containing all necessary data
            
        Returns:
            List of validation errors
        """
        errors = []
        errors.extend(SchemaValidator._validate_enumerators(context["enumerators"]))
        errors.extend(SchemaValidator._validate_types(context["types"], context))

        for collection_name, collection in context["collection_configs"].items():
            # Must have a version list
            if "versions" not in collection or not isinstance(collection["versions"], list):
                errors.append({
                    "error": "invalid_versions",
                    "error_id": "VLD-001",
                    "message": "versions must be a list"
                })
                continue
            
            # Validate each version of the collection
            for version_config in collection["versions"]:
                if not isinstance(version_config, dict):
                    errors.append({
                        "error": "invalid_version_config",
                        "error_id": "VLD-002",
                        "version_config": version_config,
                        "message": "Version config must be a dictionary"
                    })
                    continue
                
                if "version" not in version_config or not isinstance(version_config["version"], str):
                    errors.append({
                        "error": "missing_required_field",
                        "error_id": "VLD-003",
                        "field": "version",
                        "message": "Version config must have a version number"
                    })
                    continue
                
                try:
                    # Create version number instance and ensure it has the collection name
                    version = VersionNumber(version_config["version"])
                    if not version.collection_name:
                        version_str = f"{collection_name}.{version.version}"
                        version = VersionNumber(version_str)
                except ValueError as e:
                    errors.append({
                        "error": "invalid_version_format",
                        "error_id": "VLD-005",
                        "version": version_config["version"],
                        "message": str(e)
                    })
                    continue
                
                # Use get_schema_version() which now handles collection names
                schema_name = version.get_schema_version()
                enumerator_version = version.get_enumerator_version()
                
                # Validate schema exists
                if schema_name not in context["dictionaries"]:
                    errors.append({
                        "error": "schema_not_found",
                        "error_id": "VLD-004",
                        "schema_name": schema_name,
                        "message": f"Schema not found for collection {collection_name} version {version} in dictionaries"
                    })
                    continue
                    
                # Validate schema structure and references
                schema = context["dictionaries"][schema_name]
                errors.extend(SchemaValidator._validate_complex_type(schema_name, schema, context, enumerator_version))
        
        return errors

    @staticmethod
    def _validate_enumerators(enumerators: List[Dict]) -> List[Dict]:
        """Validate enumerator definitions against the schema.
        
        Validates:
        1. Each version has required fields (version, enumerators)
        2. Version number is valid
        3. Enumerator values are properly structured
        4. Each enumerator value has a string description
        
        Args:
            enumerators: List of enumerator version definitions
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Validate each enumerator version
        for version in enumerators:
            # Validate version field
            if "version" not in version:
                errors.append({
                    "error": "missing_required_field",
                    "error_id": "VLD-101",
                    "field": "version",
                    "message": "Enumerator version must have a version number"
                })
            elif type(version["version"]) != int:
                errors.append({
                    "error": "invalid_version_format",
                    "error_id": "VLD-102",
                    "version": version["version"],
                    "message": "Version must be an integer"
                })
                
            # Validate enumerators field
            if "enumerators" not in version:
                errors.append({
                    "error": "missing_required_field",
                    "error_id": "VLD-103",
                    "field": "enumerators",
                    "message": "Enumerator version must have an enumerators definition"
                })
            elif not isinstance(version["enumerators"], dict):
                errors.append({
                    "error": "invalid_enumerators_format",
                    "error_id": "VLD-104",
                    "enumerator": version.get("name", "unknown"),
                    "message": "Enumerators must be a dictionary of values to descriptions"
                })
            else:
                # Validate each enumerator values
                for name, enumerations in version["enumerators"].items():
                    if not isinstance(name, str):
                        errors.append({
                            "error": "invalid_enumerator_name",
                            "error_id": "VLD-105",
                            "value": str(name),
                            "message": "Enumerator name must be a string"
                        })
                    if not isinstance(enumerations, dict):
                        errors.append({
                            "error": "invalid_enumerations",
                            "error_id": "VLD-106",
                            "description": enumerations,
                            "message": "Enumerators bust be an object"
                        })
                    else:
                        for value, description in enumerations.items():
                            if not isinstance(value, str):
                                errors.append({
                                    "error": "invalid_enumerator_value",
                                    "error_id": "VLD-107",
                                    "value": str(value),
                                    "message": "Enumerator value must be a string"
                                })
                            if not isinstance(description, str):
                                errors.append({
                                    "error": "invalid_enumerator_description",
                                    "error_id": "VLD-108",
                                    "description": str(description),
                                    "message": "Enumerator description must be a string"    
                                })
                                
        return errors

    @staticmethod
    def _validate_types(types: Dict, context: ValidationContext) -> List[Dict]:
        """Validate custom type definitions.
        
        Args:
            types: Dictionary of custom type definitions
            context: Validation context containing all necessary data
            
        Returns:
            List of validation errors
        """
        errors = []
        validated = set()  # Track which types we've validated
        
        # Validate each type
        for type_name, type_def in types.items():
            if type_name in validated:
                continue
            if any(key in type_def for key in {"schema", "json_type", "bson_type"}):
                errors.extend(SchemaValidator._validate_primitive_type(type_name, type_def))
            else:
                errors.extend(SchemaValidator._validate_complex_type(type_name, type_def, context))
            validated.add(type_name)
            
        return errors

    @staticmethod
    def _validate_primitive_type(type_name: str, type_def: Dict) -> List[Dict]:
        """Validate a primitive custom type definition."""
        type_errors = []
        
        # Validate schema or json_type/bson_type
        has_schema = "schema" in type_def
        has_json_type = "json_type" in type_def
        has_bson_type = "bson_type" in type_def
        
        # must have either schema or both json_type and bson_type
        if not (has_schema or (has_json_type and has_bson_type)):
            type_errors.append({
                "error": "invalid_primitive_type",
                "error_id": "VLD-201",
                "type": type_name,
                "message": "Primitive type must have either schema or both json_type and bson_type"
            })
            
        if has_schema and not isinstance(type_def["schema"], dict):
            type_errors.append({
                "error": "invalid_primitive_type",
                "error_id": "VLD-202",
                "type": type_name,
                "message": "Primitive type `schema` must be a valid object"
            })

        if has_json_type and not isinstance(type_def["json_type"], dict):
            type_errors.append({
                "error": "invalid_primitive_type",
                "error_id": "VLD-203",
                "type": type_name,
                "message": "Primitive type `json_type` must be a valid object"
            })
        
        if has_bson_type and not isinstance(type_def["bson_type"], dict):
            type_errors.append({
                "error": "invalid_primitive_type",
                "error_id": "VLD-204",
                "type": type_name,
                "message": "Primitive type `bson_type` must be a valid object"
            })

        logging.info(f"Validated primitive type: {type_name}")
        return type_errors
            
    @staticmethod
    def _validate_complex_type(prop_name: str, prop_def: Dict, context: ValidationContext, enumerator_version: Optional[int] = 0, visited: Optional[Set[str]] = None) -> List[Dict]:
        """Validate a complex type definition.
        
        Args:
            prop_name: Name of the property being validated
            prop_def: Property definition to validate
            context: Validation context containing all necessary data
            enumerator_version: Current enumerator version for enum validation
            visited: Set of already visited paths (for cycle detection)
            
        Returns:
            List of validation errors
        """
        if visited is None:
            visited = set()
            
        # Check for circular references
        if prop_name in visited:
            return [{
                "error": "circular_reference",
                "error_id": "VLD-020",
                "type": prop_name,
                "message": f"Circular reference detected in type: {prop_name}"
            }]
            
        visited.add(prop_name)
        try:
            return SchemaValidator._validate_complex_type_properties(prop_name, prop_def, context, enumerator_version, visited)
        finally:
            visited.remove(prop_name)
            logging.info(f"Validated complex type: {prop_name}")

            
    @staticmethod
    def _validate_complex_type_properties(prop_name: str, prop_def: Dict, context: ValidationContext, enumerator_version: Optional[int], visited: Set[str]) -> List[Dict]:
        """Internal validation logic for complex types."""
        type_errors = []
        
        # Validate basic structure
        if not isinstance(prop_def, dict):
            type_errors.extend([{
                "error": "invalid_type",
                "error_id": "VLD-301",
                "type": prop_name,
                "message": "Type must be a valid object"
            }])
            return type_errors
            
        # Validate required fields
        type_errors.extend(SchemaValidator._validate_required_fields(prop_name, prop_def))
        if type_errors:
            return type_errors
                        
        if prop_def["type"] not in SchemaValidator.VALID_TYPES:
            return SchemaValidator._validate_custom_type(prop_name, prop_def["type"], context)
            
        # Validate type-specific properties
        if prop_def["type"] == SchemaType.OBJECT.value:
            type_errors.extend(SchemaValidator._validate_object_type(prop_name, prop_def, context, enumerator_version, visited))
        elif prop_def["type"] == SchemaType.ARRAY.value:
            type_errors.extend(SchemaValidator._validate_array_type(prop_name, prop_def, context, enumerator_version, visited))
        elif prop_def["type"] in [SchemaType.ENUM.value, SchemaType.ENUM_ARRAY.value]:
            type_errors.extend(SchemaValidator._validate_enum_type(prop_name, prop_def, context, enumerator_version))
            
        return type_errors
        
    @staticmethod
    def _validate_required_fields(prop_name: str, prop_def: Dict) -> List[Dict]:
        """Validate required fields in a type definition."""
        errors = []
        for field in ["type", "description"]:
            if field not in prop_def:
                errors.append({
                    "error": "missing_required_field",
                    "error_id": "VLD-401",
                    "type": prop_name,
                    "field": field,
                    "message": f"Missing required field: {field}"
                })
        return errors
        
    @staticmethod
    def _validate_custom_type(prop_name: str, type_name: str, context: ValidationContext) -> List[Dict]:
        """Validate a custom type reference."""
        if type_name not in context["types"]:
            return [{
                "error": "invalid_type",
                "error_id": "VLD-601",
                "type": prop_name,
                "value": type_name,
                "message": f"Unknown type: {type_name}"
            }]
        return []
        
    @staticmethod
    def _validate_object_type(prop_name: str, prop_def: Dict, context: ValidationContext, enumerator_version: Optional[int], visited: Set[str]) -> List[Dict]:
        """Validate an object type definition."""
        errors = []
        
        if "properties" not in prop_def:
            errors.append({
                "error": "missing_required_field",
                "error_id": "VLD-701",
                "type": prop_name,
                "field": "properties",
                "message": f"Missing required field: properties"
            })
            return errors
        
        # Validate properties if present
        if "properties" in prop_def:
            for nested_name, nested_def in prop_def["properties"].items():
                errors.extend(SchemaValidator._validate_complex_type(
                    f"{prop_name}.{nested_name}", 
                    nested_def, 
                    context,
                    enumerator_version,
                    visited
                ))
                
        # Validate one_of if present
        if "one_of" in prop_def:
            errors.extend(SchemaValidator._validate_one_of_type(prop_name, prop_def["one_of"], context, enumerator_version, visited))
                
        return errors
        
    @staticmethod
    def _validate_array_type(prop_name: str, prop_def: Dict, context: ValidationContext, enumerator_version: Optional[int], visited: Set[str]) -> List[Dict]:
        """Validate an array type definition."""
        if "items" not in prop_def:
            return [{
                "error": "invalid_array_items",
                "error_id": "VLD-801",
                "type": prop_name,
                "message": f"Array type {prop_name} must have items definition"
            }]
            
        return SchemaValidator._validate_complex_type(
            f"{prop_name}.items", 
            prop_def["items"], 
            context,
            enumerator_version,
            visited
        )
        
    @staticmethod
    def _validate_enum_type(prop_name: str, prop_def: Dict, context: ValidationContext, enumerator_version: Optional[int] = 0) -> List[Dict]:
        """Validate an enum type definition."""
        if "enums" not in prop_def:
            return [{
                "error": "invalid_enum_reference",
                "error_id": "VLD-901",
                "type": prop_name,
                "message": f"Enum type {prop_name} must have valid enums definition"
            }]
            
        if prop_def["enums"] not in context["enumerators"][enumerator_version]["enumerators"]:
            return [{
                "error": "invalid_enum_reference",
                "error_id": "VLD-902",
                "type": prop_name,
                "enum": prop_def["enums"],
                "message": f"Enum type {prop_def['enums']} not found in version {enumerator_version}"
            }]
            
        return []
        
    @staticmethod
    def _validate_one_of_type(prop_name: str, one_of_def: Dict, context: ValidationContext, enumerator_version: Optional[int], visited: Set[str]) -> List[Dict]:
        """Validate a one_of type definition."""
        logging.info(f"Validating one_of type: {prop_name}")
        errors = []
        
        if not isinstance(one_of_def, dict):
            errors.append({
                "error": "invalid_one_of_format",
                "error_id": "VLD-1001",
                "type": prop_name,
                "message": f"OneOf definition must be a valid object"
            })
            return errors
            
        if "type_property" not in one_of_def:
            errors.append({
                "error": "invalid_one_of_type_property",
                "error_id": "VLD-1002",
                "type": prop_name,
                "message": f"OneOf definition must have a type_property"
            })
            return errors
            
        if "schemas" not in one_of_def:
            errors.append({
                "error": "invalid_one_of_schemas",
                "error_id": "VLD-1003",
                "type": prop_name,
                "message": f"OneOf definition must have schemas"
            })
            return errors
            
        # Validate each schema in the one_of definition
        for schema_name, schema_def in one_of_def["schemas"].items():
            # Validate as a complex type (all $ref objects will have been resolved during loading)
            errors.extend(SchemaValidator._validate_complex_type(
                f"{prop_name}.{schema_name}", 
                schema_def, 
                context,
                enumerator_version,
                visited
            ))
            
        return errors
 