from typing import Dict, List, Optional
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
    def validate_enumerators(enumerators: List[Dict]) -> List[Dict]:
        """Validate enumerator definitions against the schema."""
        errors = []
        
        # Validate each enumerator version
        for version in enumerators:
            # Validate required fields
            if "name" not in version:
                errors.append({
                    "error": "invalid_enumerator_name",
                    "error_id": "SCH-013",
                    "name": version.get("name", "unknown"),
                    "message": "Invalid enumerator name format"
                })
            elif not re.match(r'^[A-Z][a-zA-Z0-9_]*$', version["name"]):
                errors.append({
                    "error": "invalid_enumerator_name",
                    "error_id": "SCH-014",
                    "name": version["name"],
                    "message": "Invalid enumerator name format"
                })
                
            if "status" not in version:
                errors.append({
                    "error": "invalid_enumerator_status",
                    "error_id": "SCH-015",
                    "status": version.get("status", "unknown"),
                    "message": "Invalid enumerator status"
                })
            elif version["status"] not in ["Active", "Deprecated"]:
                errors.append({
                    "error": "invalid_enumerator_status",
                    "error_id": "SCH-016",
                    "status": version["status"],
                    "message": "Invalid enumerator status"
                })
                
            if "version" not in version:
                errors.append({
                    "error": "invalid_enumerator_version",
                    "error_id": "SCH-017",
                    "version": version.get("version", "unknown"),
                    "message": "Invalid enumerator version number"
                })
            elif not isinstance(version["version"], int) or version["version"] < 0:
                errors.append({
                    "error": "invalid_enumerator_version",
                    "error_id": "SCH-018",
                    "version": version["version"],
                    "message": "Invalid enumerator version number"
                })
                
            if "enumerators" not in version:
                errors.append({
                    "error": "invalid_enumerator_structure",
                    "error_id": "SCH-019",
                    "enumerator": version.get("name", "unknown"),
                    "message": "Enumerator must be a dictionary"
                })
            elif not isinstance(version["enumerators"], dict):
                errors.append({
                    "error": "invalid_enumerator_structure",
                    "error_id": "SCH-020",
                    "enumerator": version["name"],
                    "message": "Enumerator must be a dictionary"
                })
            else:
                # Validate each enumerator definition
                for enum_name, enum_def in version["enumerators"].items():
                    if not isinstance(enum_def, dict):
                        errors.append({
                            "error": "invalid_enumerator_structure",
                            "error_id": "SCH-021",
                            "enumerator": enum_name,
                            "message": "Enumerator must be a dictionary"
                        })
                    else:
                        # Validate each value has a description
                        for value, description in enum_def.items():
                            if not isinstance(description, str):
                                errors.append({
                                    "error": "invalid_enumerator_value",
                                    "error_id": "SCH-022",
                                    "enumerator": enum_name,
                                    "value": value,
                                    "message": "Enumerator value must have a string description"
                                })
                                
        return errors

    @staticmethod
    def validate_schema(context: ValidationContext) -> List[Dict]:
        """Validate schema definitions against collection configurations.
        
        Args:
            context: Validation context containing all necessary data
            
        Returns:
            List of validation errors
        """
        errors = []

        # Validate enumerators 
        errors.extend(SchemaValidator.validate_enumerators(context["enumerators"]))
            
        # Validate each collection configuration
        for collection in context["collection_configs"]:
            # Get the version number from the collection config
            version = VersionNumber.from_string(collection["version"])
            
            # Construct schema name with version (e.g., user.1.2.3)
            schema_name = f"{collection['name']}.{version.major}.{version.minor}.{version.patch}"
            
            # Get the enumerator version from the collection config
            enum_version = collection["enum_version"]
            
            # Validate the schema exists
            if schema_name not in context["types"]:
                errors.append({
                    "error": "schema_not_found",
                    "error_id": "SCH-013",
                    "schema_name": schema_name,
                    "message": f"Schema not found for collection {collection['name']} version {version}"
                })
                continue
                
            # Validate the schema structure
            schema = context["types"][schema_name]
            schema_errors = SchemaValidator._validate_schema_type(schema, schema_name, enum_version, context["enumerators"])
            errors.extend(schema_errors)            
        return errors

    @staticmethod
    def _validate_primitive_type(schema: Dict, path: str) -> List[Dict]:
        """Validate a primitive type definition."""
        errors = []
        
        # Check for valid schema/json_type/bson_type combination
        has_schema = "schema" in schema
        has_json_type = "json_type" in schema
        has_bson_type = "bson_type" in schema
        
        if has_schema:
            if has_json_type or has_bson_type:
                errors.append({
                    "error": "invalid_schema_combination",
                    "error_id": "SCH-024",
                    "path": path,
                    "message": "Primitive type cannot have both 'schema' and *_type fields"
                })
        else:
            if not (has_json_type and has_bson_type):
                errors.append({
                    "error": "invalid_primitive_type",
                    "error_id": "SCH-025",
                    "path": path,
                    "message": "Primitive type must have either 'schema' or both 'json_type' and 'bson_type' fields"
                })
        
        # Validate required fields
        if "description" not in schema:
            errors.append({
                "error": "missing_required_field",
                "error_id": "SCH-026",
                "path": path,
                "field": "description",
                "message": "Missing required field"
            })
            
        # Validate schema/json_type/bson_type are valid JSON
        for field in ["schema", "json_type", "bson_type"]:
            if field in schema:
                try:
                    json.dumps(schema[field])
                except (TypeError, ValueError):
                    errors.append({
                        "error": f"invalid_{field}",
                        "error_id": f"SCH-{27 if field == 'schema' else 28 if field == 'json_type' else 29}",
                        "path": path,
                        "message": f"Primitive type has invalid {field}: must be valid JSON"
                    })
                    
        return errors

    @staticmethod
    def _validate_schema_type(schema: Dict, path: str, enum_version: Optional[int] = None, enumerators: Optional[List[Dict]] = None) -> List[Dict]:
        """Validate a schema type definition."""
        errors = []
        
        # Validate required fields
        if "description" not in schema:
            errors.append({
                "error": "missing_required_field",
                "error_id": "SCH-030",
                "path": path,
                "field": "description",
                "message": "Missing required field"
            })
            
        if "type" not in schema:
            errors.append({
                "error": "missing_required_field",
                "error_id": "SCH-031",
                "path": path,
                "field": "type",
                "message": "Missing required field"
            })
            return errors
            
        # Validate type is valid
        type_name = schema["type"]
        if type_name not in SchemaValidator.VALID_TYPES:
            errors.append({
                "error": "invalid_schema_type",
                "error_id": "SCH-032",
                "path": path,
                "type": type_name,
                "message": "Invalid type"
            })
            return errors
            
        # Validate type-specific properties
        if type_name == SchemaType.OBJECT.value:
            errors.extend(SchemaValidator._validate_object_type(schema, path, enum_version, enumerators))
        elif type_name == SchemaType.ARRAY.value:
            errors.extend(SchemaValidator._validate_array_type(schema, path, enum_version, enumerators))
        elif type_name in [SchemaType.ENUM.value, SchemaType.ENUM_ARRAY.value]:
            errors.extend(SchemaValidator._validate_enum_type(schema, path, enum_version, enumerators))
        elif type_name == SchemaType.ONE_OF.value:
            errors.extend(SchemaValidator._validate_one_of_type(schema, path, enum_version, enumerators))
            
        return errors

    @staticmethod
    def _validate_object_type(schema: Dict, path: str, enum_version: Optional[int] = None, enumerators: Optional[List[Dict]] = None) -> List[Dict]:
        """Validate an object type definition."""
        errors = []
        if "properties" not in schema:
            errors.append({
                "error": "invalid_object_properties",
                "error_id": "SCH-033",
                "path": path,
                "message": "Object type must have properties definition"
            })
        else:
            for prop_name, prop_def in schema["properties"].items():
                errors.extend(SchemaValidator.validate_schema(prop_def, f"{path}.{prop_name}", enum_version, enumerators))
        return errors

    @staticmethod
    def _validate_array_type(schema: Dict, path: str, enum_version: Optional[int] = None, enumerators: Optional[List[Dict]] = None) -> List[Dict]:
        """Validate an array type definition."""
        errors = []
        if "items" not in schema:
            errors.append({
                "error": "invalid_array_items",
                "error_id": "SCH-034",
                "path": path,
                "message": "Array type must have items definition"
            })
        else:
            errors.extend(SchemaValidator.validate_schema(schema["items"], f"{path}.items", enum_version, enumerators))
        return errors

    @staticmethod
    def _validate_enum_type(schema: Dict, path: str, enum_version: Optional[int] = None, enumerators: Optional[List[Dict]] = None) -> List[Dict]:
        """Validate an enum type definition."""
        errors = []
        if "enums" not in schema:
            errors.append({
                "error": "invalid_enum_reference",
                "error_id": "SCH-035",
                "path": path,
                "type": schema["type"],
                "message": "Enum type must have enums reference"
            })
            return errors
            
        enum_name = schema["enums"]
        
        if not enumerators:
            errors.append({
                "error": "unknown_enumerator",
                "error_id": "SCH-036",
                "path": path,
                "enumerator": enum_name,
                "version": enum_version,
                "message": "No enumerators available for validation"
            })
            return errors
                
        # Find the version entry using next() with a generator expression
        version_entry = next(
            (entry for entry in enumerators 
             if entry["version"] == enum_version and entry["status"] == "Active"),
            None
        )
                
        if not version_entry:
            errors.append({
                "error": "unknown_enumerator",
                "error_id": "SCH-036",
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
                "error_id": "SCH-037",
                "path": path,
                "enumerator": enum_name,
                "version": enum_version,
                "message": "Unknown enumerator in version"
            })
            return errors
                    
        return errors

    @staticmethod
    def _validate_one_of_type(schema: Dict, path: str, enum_version: Optional[int] = None, enumerators: Optional[List[Dict]] = None) -> List[Dict]:
        """Validate a one_of type definition."""
        errors = []
        if "type_property" not in schema:
            errors.append({
                "error": "invalid_one_of_type",
                "error_id": "SCH-038",
                "path": path,
                "message": "one_of type must have type_property definition"
            })
        if "schemas" not in schema:
            errors.append({
                "error": "invalid_one_of_schemas",
                "error_id": "SCH-039",
                "path": path,
                "message": "one_of type must have schemas definition"
            })
        elif not isinstance(schema["schemas"], dict):
            errors.append({
                "error": "invalid_schemas_value",
                "error_id": "SCH-040",
                "path": path,
                "message": "Invalid schemas value: must be a dictionary"
            })
        else:
            for schema_name, schema_def in schema["schemas"].items():
                errors.extend(SchemaValidator.validate_schema(schema_def, f"{path}.schemas.{schema_name}", enum_version, enumerators))
        return errors 