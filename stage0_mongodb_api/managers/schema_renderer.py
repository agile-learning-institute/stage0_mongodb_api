from typing import Dict, List, Optional, Any, TypedDict
from stage0_mongodb_api.managers.schema_types import SchemaType, SchemaFormat, SchemaContext
from stage0_mongodb_api.managers.version_number import VersionNumber

class SchemaRenderer:
    """Static utility class for rendering schemas in different formats."""
    
    @staticmethod
    def render_schema(version_name: str, format: SchemaFormat, context: SchemaContext) -> Dict:
        """Render a schema in the specified format.
        
        Args:
            version_name: The version name (collection name + 4-part version number)
            context: Schema context containing all necessary data and rendering parameters
            
        Returns:
            Dict containing the rendered schema
        """
        # Parse the version name
        version = VersionNumber(version_name)
        
        # Get the schema from dictionaries using the schema version
        schema = context["dictionaries"][version.get_schema_version()]
        
        if format == SchemaFormat.BSON:
            return SchemaRenderer._render_bson_schema(schema, version.get_enumerator_version(), context)
        elif format == SchemaFormat.JSON:
            return SchemaRenderer._render_json_schema(schema, version.get_enumerator_version(), context)
        else:
            raise ValueError(f"Unsupported schema format: {format}")

    @staticmethod
    def _render_bson_schema(schema: Dict, enumerator_version: int, context: SchemaContext) -> Dict:
        """Render a schema in BSON format.
        
        BSON schemas use bsonType instead of type and have specific validation rules.
        See: https://www.mongodb.com/docs/manual/core/schema-validation/
        """
        resolved = SchemaRenderer._resolve_schema(schema, enumerator_version, context)
        
        # Convert JSON Schema to BSON Schema format
        if "type" in resolved:
            # Map JSON types to BSON types
            type_mapping = {
                "string": "string",
                "number": "double",
                "integer": "int",
                "boolean": "bool",
                "array": "array",
                "object": "object",
                "null": "null"
            }
            resolved["bsonType"] = type_mapping.get(resolved["type"], resolved["type"])
            del resolved["type"]
            
        # Handle required fields at the root level
        if "required" in resolved:
            resolved["required"] = resolved["required"]
            
        # Handle properties for objects
        if "properties" in resolved:
            for prop_name, prop_schema in resolved["properties"].items():
                if isinstance(prop_schema, dict):
                    # Recursively convert nested properties
                    resolved["properties"][prop_name] = SchemaRenderer._render_bson_schema(
                        prop_schema, enumerator_version, context
                    )
                    
        # Handle array items
        if "items" in resolved:
            if isinstance(resolved["items"], dict):
                resolved["items"] = SchemaRenderer._render_bson_schema(
                    resolved["items"], enumerator_version, context
                )
                
        return resolved

    @staticmethod
    def _render_json_schema(schema: Dict, enumerator_version: int, context: SchemaContext) -> Dict:
        """Render a schema in JSON format."""
        return SchemaRenderer._resolve_schema(schema, enumerator_version, context)

    @staticmethod
    def _resolve_schema(schema: Dict, enumerator_version: int, context: SchemaContext) -> Dict:
        """Resolve a schema definition to its primitive type."""
        # Check if this is a primitive type
        if "schema" in schema:
            return schema["schema"]
        elif "json_type" in schema and "bson_type" in schema:
            return {
                "type": schema["json_type"],
                "bsonType": schema["bson_type"]
            }
            
        # Handle schema types
        type_name = schema.get("type")
        if not type_name:
            return schema
            
        if type_name == SchemaType.OBJECT.value:
            return SchemaRenderer._resolve_object_type(schema, enumerator_version, context)
        elif type_name == SchemaType.ARRAY.value:
            return SchemaRenderer._resolve_array_type(schema, enumerator_version, context)
        elif type_name in [SchemaType.ENUM.value, SchemaType.ENUM_ARRAY.value]:
            return SchemaRenderer._resolve_enum_type(schema, enumerator_version, context)
            
        return schema

    @staticmethod
    def _resolve_object_type(schema: Dict, enumerator_version: int, context: SchemaContext) -> Dict:
        """Resolve an object type definition."""
        resolved = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        # Resolve properties if present
        if "properties" in schema:
            for prop_name, prop_def in schema["properties"].items():
                resolved["properties"][prop_name] = SchemaRenderer._resolve_schema(
                    prop_def, enumerator_version, context
                )
                
        # Resolve one_of if present
        if "one_of" in schema:
            one_of_def = schema["one_of"]
            if "type_property" in one_of_def and "schemas" in one_of_def:
                # Add type property to properties
                resolved["properties"][one_of_def["type_property"]] = {
                    "type": "string",
                    "bsonType": "string",
                    "enum": list(one_of_def["schemas"].keys())
                }
                resolved["required"].append(one_of_def["type_property"])
                
                # Add schema properties
                for schema_name, schema_def in one_of_def["schemas"].items():
                    # If schema is a $ref, resolve the reference
                    if isinstance(schema_def, dict) and "$ref" in schema_def:
                        ref_name = schema_def["$ref"]
                        if ref_name in context["types"]:
                            resolved["properties"][schema_name] = SchemaRenderer._resolve_schema(
                                context["types"][ref_name], enumerator_version, context
                            )
                        else:
                            # If not in types, assume it's a dictionary reference
                            resolved["properties"][schema_name] = {
                                "$ref": f"#/definitions/{ref_name}"
                            }
                    else:
                        resolved["properties"][schema_name] = SchemaRenderer._resolve_schema(
                            schema_def, enumerator_version, context
                        )
                    
        # Add required fields
        if "required" in schema:
            resolved["required"].extend(schema["required"])
            
        return resolved

    @staticmethod
    def _resolve_array_type(schema: Dict, enumerator_version: int, context: SchemaContext) -> Dict:
        """Resolve an array type definition."""
        resolved = {
            "type": "array",
            "bsonType": "array"
        }
        
        if "items" in schema:
            resolved["items"] = SchemaRenderer._resolve_schema(
                schema["items"], enumerator_version, context
            )
            
        return resolved

    @staticmethod
    def _resolve_enum_type(schema: Dict, enumerator_version: int, context: SchemaContext) -> Dict:
        """Resolve an enum type definition."""
        resolved = {
            "type": "string" if schema["type"] == SchemaType.ENUM.value else "array",
            "bsonType": "string" if schema["type"] == SchemaType.ENUM.value else "array"
        }
        
        if "enums" in schema:
            enum_name = schema["enums"]
            
            # Find the specified version
            version_entry = next(
                (entry for entry in context["enumerators"] 
                 if entry["version"] == enumerator_version),
                None
            )
            
            if version_entry and enum_name in version_entry["enumerators"]:
                enum_def = version_entry["enumerators"][enum_name]
                if schema["type"] == SchemaType.ENUM.value:
                    resolved["enum"] = list(enum_def.keys())
                else:
                    resolved["items"] = {
                        "type": "string",
                        "bsonType": "string",
                        "enum": list(enum_def.keys())
                    }
                        
        return resolved 