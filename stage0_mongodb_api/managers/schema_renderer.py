from typing import Dict, List, Optional, Any, TypedDict
from stage0_mongodb_api.managers.schema_types import SchemaType, SchemaFormat, SchemaContext
from stage0_mongodb_api.managers.version_number import VersionNumber
import logging
logger = logging.getLogger(__name__)

class SchemaRenderer:
    """Utility class for rendering schemas in different formats."""
    
    @staticmethod
    def render_schema(version_name: str, format: SchemaFormat, context: SchemaContext) -> Dict:
        """Render a schema in the specified format."""
        version = VersionNumber(version_name)
        schema = context["dictionaries"][version.get_schema_version()]
        return SchemaRenderer._render(schema, format, version.get_enumerator_version(), context)
    
    @staticmethod
    def _render(schema: Dict, format: SchemaFormat, enumerator_version: int, context: SchemaContext) -> Dict:
        """ Recursively render a schema definition."""
        # Handle $ref first - replace with referenced dictionary
        if "$ref" in schema:
            return SchemaRenderer._render(
                context["dictionaries"][schema["$ref"]], 
                format, 
                enumerator_version, 
                context
            )
            
        # Handle primitive types
        if "schema" in schema or "json_type" in schema:
            return SchemaRenderer._render_primitive(schema, format)
            
        # Handle complex types
        type_name = schema["type"]
        if type_name == SchemaType.OBJECT.value:
            return SchemaRenderer._render_object(schema, format, enumerator_version, context)
        if type_name == SchemaType.ARRAY.value:
            return SchemaRenderer._render_array(schema, format, enumerator_version, context)
        if type_name in [SchemaType.ENUM.value, SchemaType.ENUM_ARRAY.value]:
            return SchemaRenderer._render_enum(schema, format, enumerator_version, context)
            
        # Handle custom types
        if type_name in context["types"]:
            return SchemaRenderer._render(context["types"][type_name], format, enumerator_version, context)
            
        # Remove description and return remaining schema
        rendered = schema.copy()
        rendered.pop("description", None)
        return rendered
        
    @staticmethod
    def _render_primitive(schema: Dict, format: SchemaFormat) -> Dict:
        """Render a primitive type definition."""
        
        # Schema property - convert type to bsonType for BSON
        if "schema" in schema:
            rendered = schema["schema"].copy()
            rendered.pop("description", None)
            if format == SchemaFormat.BSON and "type" in rendered:
                rendered["bsonType"] = rendered["type"]
                del rendered["type"]
            return rendered
            
        # or Use format-specific schema as-is
        if format == SchemaFormat.JSON and "json_type" in schema:
            rendered = schema["json_type"].copy()
            rendered.pop("description", None)
            return rendered
        
        if format == SchemaFormat.BSON and "bson_type" in schema:
            rendered = schema["bson_type"].copy()
            rendered.pop("description", None)
            return rendered
        
    @staticmethod
    def _render_object(schema: Dict, format: SchemaFormat, enumerator_version: int, context: SchemaContext) -> Dict:
        """Render an object type definition."""
        type_prop = "bsonType" if format == SchemaFormat.BSON else "type"
        rendered = {
            type_prop: "object",
            "properties": {},
            "additionalProperties": False
        }
        required = []
        
        # Render properties
        for prop_name, prop_def in schema["properties"].items():
            rendered["properties"][prop_name] = SchemaRenderer._render(
                prop_def, format, enumerator_version, context
            )
            # If property is required, add to required list
            if prop_def.get("required", False):
                required.append(prop_name)
                
        # Render one_of if present
        if "one_of" in schema:
            one_of_props, one_of_required = SchemaRenderer._render_one_of(
                schema["one_of"], format, enumerator_version, context
            )
            rendered["properties"].update(one_of_props)
            required.extend(one_of_required)
        
        # Add required properties if any
        if required:
            rendered["required"] = required
                    
        return rendered
        
    @staticmethod
    def _render_one_of(one_of_def: Dict, format: SchemaFormat, enumerator_version: int, context: SchemaContext) -> tuple[Dict, List[str]]:
        """Render a one_of type definition.
        
        Returns:
            Tuple of (properties dictionary, list of required property names)
        """
        properties = {}
        
        # Add schema properties
        for schema_name, schema_def in one_of_def["schemas"].items():
            properties[schema_name] = SchemaRenderer._render(
                schema_def, format, enumerator_version, context
            )
                
        return properties, []
        
    @staticmethod
    def _render_array(schema: Dict, format: SchemaFormat, enumerator_version: int, context: SchemaContext) -> Dict:
        """Render an array type definition."""
        type_prop = "bsonType" if format == SchemaFormat.BSON else "type"
        return {
            type_prop: "array",
            "items": SchemaRenderer._render(schema["items"], format, enumerator_version, context)
        }
        
    @staticmethod
    def _render_enum(schema: Dict, format: SchemaFormat, enumerator_version: int, context: SchemaContext) -> Dict:
        """Render an enum type definition."""
        type_prop = "bsonType" if format == SchemaFormat.BSON else "type"
        is_enum = schema["type"] == SchemaType.ENUM.value
        enum_name = schema["enums"]
        
        # Get enum values from the correct version
        if enumerator_version >= len(context["enumerators"]) or enum_name not in context["enumerators"][enumerator_version]["enumerators"]:
            return schema
            
        enum_def = context["enumerators"][enumerator_version]["enumerators"][enum_name]
        if is_enum:
            return {
                type_prop: "string",
                "enum": list(enum_def.keys())
            }
            
        return {
            type_prop: "array",
            "items": {
                type_prop: "string",
                "enum": list(enum_def.keys())
            }
        } 