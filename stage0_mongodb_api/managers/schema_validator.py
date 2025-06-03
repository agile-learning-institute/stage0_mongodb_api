from typing import Dict, List, Optional, Set
import re
import json
from stage0_py_utils import Config
from stage0_mongodb_api.managers.schema_types import SchemaType, Schema, ValidationContext
from stage0_mongodb_api.managers.version_number import VersionNumber

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
        errors.extend(SchemaValidator._validate_dictionaries(context["dictionaries"]))

        for collection_name, collection in context["collection_configs"].items():
            # Validate each version of the collection
            for version_config in collection["versions"]:
                version = VersionNumber(version_config["version"])
                schema_name = f"{collection_name}.{version.get_schema_version()}"
                
                # Validate schema exists
                if schema_name not in context["dictionaries"]:
                    errors.append({
                        "error": "schema_not_found",
                        "error_id": "VLD-011",
                        "schema_name": schema_name,
                        "message": f"Schema not found for collection {collection_name} version {version} in dictionaries"
                    })
                    continue
                    
                # Validate schema structure and references
                schema = context["dictionaries"][schema_name]
                errors.extend(SchemaValidator._validate_schema_references(
                    schema, 
                    schema_name, 
                    version.get_enumerator_version(),
                    context
                ))
        
        return errors

    @staticmethod
    def _validate_enumerators(enumerators: List[Dict]) -> List[Dict]:
        """Validate enumerator definitions against the schema."""
        errors = []
        
        # Validate each enumerator version
        for version in enumerators:
            # Validate required fields
            if "name" not in version:
                errors.append({
                    "error": "invalid_enumerator_name",
                    "error_id": "VLD-001",
                    "name": version.get("name", "unknown"),
                    "message": "Invalid enumerator name format"
                })
            elif not re.match(r'^[A-Z][a-zA-Z0-9_]*$', version["name"]):
                errors.append({
                    "error": "invalid_enumerator_name",
                    "error_id": "VLD-002",
                    "name": version["name"],
                    "message": "Invalid enumerator name format"
                })
                
            if "status" not in version:
                errors.append({
                    "error": "invalid_enumerator_status",
                    "error_id": "VLD-003",
                    "status": version.get("status", "unknown"),
                    "message": "Invalid enumerator status"
                })
            elif version["status"] not in ["Active", "Deprecated"]:
                errors.append({
                    "error": "invalid_enumerator_status",
                    "error_id": "VLD-004",
                    "status": version["status"],
                    "message": "Invalid enumerator status"
                })
                
            if "version" not in version:
                errors.append({
                    "error": "invalid_enumerator_version",
                    "error_id": "VLD-005",
                    "version": version.get("version", "unknown"),
                    "message": "Invalid enumerator version number"
                })
            elif not isinstance(version["version"], int) or version["version"] < 0:
                errors.append({
                    "error": "invalid_enumerator_version",
                    "error_id": "VLD-006",
                    "version": version["version"],
                    "message": "Invalid enumerator version number"
                })
                
            if "enumerators" not in version:
                errors.append({
                    "error": "invalid_enumerator_structure",
                    "error_id": "VLD-007",
                    "enumerator": version.get("name", "unknown"),
                    "message": "Enumerator must be a dictionary"
                })
            elif not isinstance(version["enumerators"], dict):
                errors.append({
                    "error": "invalid_enumerator_structure",
                    "error_id": "VLD-008",
                    "enumerator": version["name"],
                    "message": "Enumerator must be a dictionary"
                })
            else:
                # Validate each enumerator definition
                for enum_name, enum_def in version["enumerators"].items():
                    if not isinstance(enum_def, dict):
                        errors.append({
                            "error": "invalid_enumerator_structure",
                            "error_id": "VLD-009",
                            "enumerator": enum_name,
                            "message": "Enumerator must be a dictionary"
                        })
                    else:
                        # Validate each value has a description
                        for value, description in enum_def.items():
                            if not isinstance(description, str):
                                errors.append({
                                    "error": "invalid_enumerator_value",
                                    "error_id": "VLD-010",
                                    "enumerator": enum_name,
                                    "value": value,
                                    "message": "Enumerator value must have a string description"
                                })
                                
        return errors

    @staticmethod
    def _validate_dictionaries(dictionaries: Dict) -> List[Dict]:
        """Validate all dictionary definitions.
        
        Args:
            dictionaries: Dictionary of dictionary definitions
            
        Returns:
            List of validation errors
        """
        errors = []
        validated = set()  # Track which dictionaries we've validated
        validation_stack = set()  # Track dictionaries currently being validated (for cycle detection)
        
        def validate_dictionary(dict_name: str, dict_def: Dict, path: str) -> List[Dict]:
            if dict_name in validated:
                return []  # Already validated this dictionary
                
            if dict_name in validation_stack:
                return [{
                    "error": "circular_reference",
                    "error_id": "VLD-012",
                    "path": path,
                    "message": f"Circular reference detected in dictionary: {dict_name}"
                }]
                
            validation_stack.add(dict_name)
            dict_errors = []
            
            # Validate basic structure
            if not isinstance(dict_def, dict):
                dict_errors.append({
                    "error": "invalid_dictionary",
                    "error_id": "VLD-013",
                    "path": path,
                    "message": "Dictionary must be a valid object"
                })
                validation_stack.remove(dict_name)
                return dict_errors
                
            # Validate required fields
            for field in ["type", "description"]:
                if field not in dict_def:
                    dict_errors.append({
                        "error": "missing_required_field",
                        "error_id": "VLD-014",
                        "path": path,
                        "field": field,
                        "message": f"Missing required field: {field}"
                    })
                    
            # Validate type is valid
            if "type" in dict_def and dict_def["type"] not in SchemaValidator.VALID_TYPES:
                dict_errors.append({
                    "error": "invalid_type",
                    "error_id": "VLD-015",
                    "path": path,
                    "type": dict_def["type"],
                    "message": "Invalid type"
                })
                
            # Validate $ref if present
            if "$ref" in dict_def:
                ref_name = dict_def["$ref"]
                if ref_name not in dictionaries:
                    dict_errors.append({
                        "error": "invalid_reference",
                        "error_id": "VLD-016",
                        "path": path,
                        "reference": ref_name,
                        "message": f"Referenced dictionary not found: {ref_name}"
                    })
                else:
                    # Recursively validate referenced dictionary
                    dict_errors.extend(validate_dictionary(ref_name, dictionaries[ref_name], f"{path}.$ref"))
                    
            validation_stack.remove(dict_name)
            validated.add(dict_name)
            return dict_errors
        
        # Validate each dictionary
        for dict_name, dict_def in dictionaries.items():
            errors.extend(validate_dictionary(dict_name, dict_def, dict_name))
            
        return errors

    @staticmethod
    def _validate_schema_references(schema: Dict, path: str, enum_version: int, context: ValidationContext, visited: Optional[Set[str]] = None) -> List[Dict]:
        """Validate schema references and structure.
        
        Args:
            schema: Schema to validate
            path: Current validation path
            enum_version: Current enumerator version
            context: Validation context
            visited: Set of already visited paths (for cycle detection)
            
        Returns:
            List of validation errors
        """
        if visited is None:
            visited = set()
            
        if path in visited:
            return [{
                "error": "circular_reference",
                "error_id": "VLD-017",
                "path": path,
                "message": f"Circular reference detected in schema: {path}"
            }]
            
        visited.add(path)
        errors = []
        
        # Validate basic structure
        if not isinstance(schema, dict):
            errors.append({
                "error": "invalid_schema",
                "error_id": "VLD-018",
                "path": path,
                "message": "Schema must be a valid object"
            })
            visited.remove(path)
            return errors
            
        # Validate type-specific properties
        if "type" in schema:
            if schema["type"] == SchemaType.OBJECT.value:
                errors.extend(SchemaValidator._validate_object_references(schema, path, enum_version, context, visited))
            elif schema["type"] == SchemaType.ARRAY.value:
                errors.extend(SchemaValidator._validate_array_references(schema, path, enum_version, context, visited))
            elif schema["type"] in [SchemaType.ENUM.value, SchemaType.ENUM_ARRAY.value]:
                errors.extend(SchemaValidator._validate_enum_references(schema, path, enum_version, context))
                
        visited.remove(path)
        return errors

    @staticmethod
    def _validate_object_references(schema: Dict, path: str, enum_version: int, context: ValidationContext, visited: Set[str]) -> List[Dict]:
        """Validate object type references."""
        errors = []
        if "properties" not in schema:
            errors.append({
                "error": "invalid_object_properties",
                "error_id": "VLD-019",
                "path": path,
                "message": "Object type must have properties definition"
            })
        else:
            for prop_name, prop_def in schema["properties"].items():
                errors.extend(SchemaValidator._validate_schema_references(
                    prop_def, 
                    f"{path}.{prop_name}", 
                    enum_version, 
                    context,
                    visited
                ))
        return errors

    @staticmethod
    def _validate_array_references(schema: Dict, path: str, enum_version: int, context: ValidationContext, visited: Set[str]) -> List[Dict]:
        """Validate array type references."""
        errors = []
        if "items" not in schema:
            errors.append({
                "error": "invalid_array_items",
                "error_id": "VLD-020",
                "path": path,
                "message": "Array type must have items definition"
            })
        else:
            errors.extend(SchemaValidator._validate_schema_references(
                schema["items"], 
                f"{path}.items", 
                enum_version, 
                context,
                visited
            ))
        return errors

    @staticmethod
    def _validate_enum_references(schema: Dict, path: str, enum_version: int, context: ValidationContext) -> List[Dict]:
        """Validate enum type references."""
        errors = []
        if "enums" not in schema:
            errors.append({
                "error": "invalid_enum_reference",
                "error_id": "VLD-021",
                "path": path,
                "type": schema["type"],
                "message": "Enum type must have enums reference"
            })
            return errors
            
        enum_name = schema["enums"]
        
        if not context["enumerators"]:
            errors.append({
                "error": "unknown_enumerator",
                "error_id": "VLD-022",
                "path": path,
                "enumerator": enum_name,
                "version": enum_version,
                "message": "No enumerators available for validation"
            })
            return errors
                
        # Find the version entry using next() with a generator expression
        version_entry = next(
            (entry for entry in context["enumerators"] 
             if entry["version"] == enum_version and entry["status"] == "Active"),
            None
        )
                
        if not version_entry:
            errors.append({
                "error": "unknown_enumerator",
                "error_id": "VLD-023",
                "path": path,
                "enumerator": enum_name,
                "version": enum_version,
                "message": "No active enumerator version found"
            })
            return errors
            
        # Check if enumerator exists in this version
        if enum_name not in version_entry["enumerators"]:
            errors.append({
                "error": "unknown_enumerator",
                "error_id": "VLD-024",
                "path": path,
                "enumerator": enum_name,
                "version": enum_version,
                "message": "Unknown enumerator in version"
            })
            return errors
                    
        return errors 