from typing import Dict, List, Optional, Any, TypedDict
from stage0_mongodb_api.managers.schema_types import SchemaType, SchemaFormat, SchemaContext
from stage0_mongodb_api.managers.version_number import VersionNumber

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
        """Render a schema definition."""
        # Handle primitive types
        if "schema" in schema:
            return SchemaRenderer._render_primitive(schema["schema"], format)
        if "json_type" in schema:
            return SchemaRenderer._render_primitive({
                "type": schema["json_type"],
                "bsonType": schema["bson_type"]
            }, format)
            
        # Handle complex types
        type_name = schema["type"]
        if type_name == SchemaType.OBJECT.value:
            return SchemaRenderer._render_object(schema, format, enumerator_version, context)
        if type_name == SchemaType.ARRAY.value:
            return SchemaRenderer._render_array(schema, format, enumerator_version, context)
        if type_name in [SchemaType.ENUM.value, SchemaType.ENUM_ARRAY.value]:
            return SchemaRenderer._render_enum(schema, format, enumerator_version, context)
            
        return schema
        
    @staticmethod
    def _render_primitive(schema: Dict, format: SchemaFormat) -> Dict:
        """Render a primitive type definition.
        
        There are three cases for primitives:
        1. schema property: Used for both formats, converting type to bsonType for BSON
        2. json_schema property: Used as-is for JSON format
        3. bson_schema property: Used as-is for BSON format
        """
        # Case 1: schema property - convert type to bsonType for BSON
        if "schema" in schema:
            rendered = schema["schema"].copy()
            if format == SchemaFormat.BSON and "type" in rendered:
                rendered["bsonType"] = rendered["type"]
                del rendered["type"]
            return rendered
            
        # Case 2 & 3: Use format-specific schema as-is
        if format == SchemaFormat.JSON and "json_schema" in schema:
            return schema["json_schema"].copy()
        if format == SchemaFormat.BSON and "bson_schema" in schema:
            return schema["bson_schema"].copy()
            
        return schema
        
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
        type_prop = "bsonType" if format == SchemaFormat.BSON else "type"
        properties = {}
        required = []
        
        # Add type property
        properties[one_of_def["type_property"]] = {
            type_prop: "string",
            "enum": list(one_of_def["schemas"].keys())
        }
        required.append(one_of_def["type_property"])
        
        # Add schema properties
        for schema_name, schema_def in one_of_def["schemas"].items():
            if isinstance(schema_def, dict) and "$ref" in schema_def:
                ref_name = schema_def["$ref"]
                if ref_name in context["types"]:
                    properties[schema_name] = SchemaRenderer._render(
                        context["types"][ref_name], format, enumerator_version, context
                    )
                else:
                    properties[schema_name] = {
                        "$ref": f"#/definitions/{ref_name}"
                    }
            else:
                properties[schema_name] = SchemaRenderer._render(
                    schema_def, format, enumerator_version, context
                )
                
        return properties, required
        
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