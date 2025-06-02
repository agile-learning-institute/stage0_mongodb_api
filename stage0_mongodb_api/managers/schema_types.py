from enum import Enum
from typing import Dict, Optional, TypedDict

class SchemaType(Enum):
    """Schema type definitions."""
    OBJECT = "object"
    ARRAY = "array"
    ENUM = "enum"
    ENUM_ARRAY = "enum_array"
    ONE_OF = "one_of"

class SchemaFormat(Enum):
    """Schema format definitions."""
    BSON = "bson"
    JSON = "json"

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
    title: Optional[str]                        # Best Practices for root schemas
    description: str
    type: str
    required: Optional[bool]                    # Default is False
    properties: Optional[Dict[str, 'Schema']]   # Required for object type only
    additionalProperties: Optional[bool]        # For object type, default is False
    items: Optional['Schema']                   # Required for array type only
    enums: Optional[str]                        # Required for enum and enum_array types only
    type_property: Optional[str]                # Required for one_of type only
    schemas: Optional[Dict[str, 'Schema']]      # Required for one_of type only 