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
        
        For schema primitives, only convert type to bsonType.
        For json_type/bson_type primitives, use the provided types directly.
        """
        rendered = schema.copy()
        
        # For schema primitives, only convert type to bsonType
        if format == SchemaFormat.BSON and "type" in rendered and "bsonType" not in rendered:
            rendered["bsonType"] = rendered["type"]
            del rendered["type"]
            
        return rendered
        
    @staticmethod
    def _render_object(schema: Dict, format: SchemaFormat, enumerator_version: int, context: SchemaContext) -> Dict:
        """Render an object type definition."""
        rendered = {
            "type": "object",
            "properties": {},
            "required": schema.get("required", [])
        }
        
        # Render properties
        for prop_name, prop_def in schema["properties"].items():
            rendered["properties"][prop_name] = SchemaRenderer._render(
                prop_def, format, enumerator_version, context
            )
                
        # Render one_of if present
        if "one_of" in schema:
            one_of_def = schema["one_of"]
            rendered["properties"][one_of_def["type_property"]] = {
                "type": "string",
                "bsonType": "string",
                "enum": list(one_of_def["schemas"].keys())
            }
            rendered["required"].append(one_of_def["type_property"])
            
            # Add schema properties
            for schema_name, schema_def in one_of_def["schemas"].items():
                if isinstance(schema_def, dict) and "$ref" in schema_def:
                    ref_name = schema_def["$ref"]
                    if ref_name in context["types"]:
                        rendered["properties"][schema_name] = SchemaRenderer._render(
                            context["types"][ref_name], format, enumerator_version, context
                        )
                    else:
                        rendered["properties"][schema_name] = {
                            "$ref": f"#/definitions/{ref_name}"
                        }
                else:
                    rendered["properties"][schema_name] = SchemaRenderer._render(
                        schema_def, format, enumerator_version, context
                    )
                    
        return rendered
        
    @staticmethod
    def _render_array(schema: Dict, format: SchemaFormat, enumerator_version: int, context: SchemaContext) -> Dict:
        """Render an array type definition."""
        return {
            "type": "array",
            "bsonType": "array",
            "items": SchemaRenderer._render(schema["items"], format, enumerator_version, context)
        }
        
    @staticmethod
    def _render_enum(schema: Dict, format: SchemaFormat, enumerator_version: int, context: SchemaContext) -> Dict:
        """Render an enum type definition."""
        is_enum = schema["type"] == SchemaType.ENUM.value
        enum_name = schema["enums"]
        
        # Get enum values from the correct version
        version_entry = next(
            (entry for entry in context["enumerators"] 
             if entry["version"] == enumerator_version),
            None
        )
        
        if not version_entry or enum_name not in version_entry["enumerators"]:
            return schema
            
        enum_def = version_entry["enumerators"][enum_name]
        if is_enum:
            return {
                "type": "string",
                "bsonType": "string",
                "enum": list(enum_def.keys())
            }
            
        return {
            "type": "array",
            "bsonType": "array",
            "items": {
                "type": "string",
                "bsonType": "string",
                "enum": list(enum_def.keys())
            }
        } 