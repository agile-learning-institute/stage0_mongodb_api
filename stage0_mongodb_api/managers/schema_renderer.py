from typing import Dict, List, Optional, Any
from stage0_mongodb_api.managers.schema_types import SchemaType, SchemaFormat

class SchemaRenderer:
    """Static utility class for rendering schemas in different formats."""
    
    @staticmethod
    def render_schema(schema: Dict, format: SchemaFormat, types: Optional[Dict] = None, enumerators: Optional[List[Dict]] = None) -> Dict:
        """Render a schema in the specified format."""
        if format == SchemaFormat.BSON:
            return SchemaRenderer._render_bson_schema(schema, types, enumerators)
        elif format == SchemaFormat.JSON:
            return SchemaRenderer._render_json_schema(schema, types, enumerators)
        else:
            raise ValueError(f"Unsupported schema format: {format}")

    @staticmethod
    def _render_bson_schema(schema: Dict, types: Optional[Dict] = None, enumerators: Optional[List[Dict]] = None) -> Dict:
        """Render a schema in BSON format."""
        return SchemaRenderer._resolve_schema(schema, types, enumerators)

    @staticmethod
    def _render_json_schema(schema: Dict, types: Optional[Dict] = None, enumerators: Optional[List[Dict]] = None) -> Dict:
        """Render a schema in JSON format."""
        return SchemaRenderer._resolve_schema(schema, types, enumerators)

    @staticmethod
    def _resolve_schema(schema: Dict, types: Optional[Dict] = None, enumerators: Optional[List[Dict]] = None) -> Dict:
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
            return SchemaRenderer._resolve_object_type(schema, types, enumerators)
        elif type_name == SchemaType.ARRAY.value:
            return SchemaRenderer._resolve_array_type(schema, types, enumerators)
        elif type_name in [SchemaType.ENUM.value, SchemaType.ENUM_ARRAY.value]:
            return SchemaRenderer._resolve_enum_type(schema, types, enumerators)
        elif type_name == SchemaType.ONE_OF.value:
            return SchemaRenderer._resolve_one_of_type(schema, types, enumerators)
            
        return schema

    @staticmethod
    def _resolve_object_type(schema: Dict, types: Optional[Dict] = None, enumerators: Optional[List[Dict]] = None) -> Dict:
        """Resolve an object type definition."""
        resolved = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        if "properties" in schema:
            for prop_name, prop_def in schema["properties"].items():
                resolved["properties"][prop_name] = SchemaRenderer._resolve_schema(prop_def, types, enumerators)
                
        if "required" in schema:
            resolved["required"] = schema["required"]
            
        return resolved

    @staticmethod
    def _resolve_array_type(schema: Dict, types: Optional[Dict] = None, enumerators: Optional[List[Dict]] = None) -> Dict:
        """Resolve an array type definition."""
        resolved = {
            "type": "array"
        }
        
        if "items" in schema:
            resolved["items"] = SchemaRenderer._resolve_schema(schema["items"], types, enumerators)
            
        return resolved

    @staticmethod
    def _resolve_enum_type(schema: Dict, types: Optional[Dict] = None, enumerators: Optional[List[Dict]] = None) -> Dict:
        """Resolve an enum type definition."""
        resolved = {
            "type": "string" if schema["type"] == SchemaType.ENUM.value else "array"
        }
        
        if "enums" in schema:
            enum_name = schema["enums"]
            if enumerators:
                # Find the active version
                version_entry = next(
                    (entry for entry in enumerators 
                     if entry["status"] == "Active"),
                    None
                )
                
                if version_entry and enum_name in version_entry["enumerators"]:
                    enum_def = version_entry["enumerators"][enum_name]
                    if schema["type"] == SchemaType.ENUM.value:
                        resolved["enum"] = list(enum_def.keys())
                    else:
                        resolved["items"] = {
                            "type": "string",
                            "enum": list(enum_def.keys())
                        }
                        
        return resolved

    @staticmethod
    def _resolve_one_of_type(schema: Dict, types: Optional[Dict] = None, enumerators: Optional[List[Dict]] = None) -> Dict:
        """Resolve a one_of type definition."""
        resolved = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        if "type_property" in schema:
            resolved["properties"][schema["type_property"]] = {
                "type": "string",
                "enum": []
            }
            resolved["required"].append(schema["type_property"])
            
        if "schemas" in schema:
            for schema_name, schema_def in schema["schemas"].items():
                resolved["properties"][schema_name] = SchemaRenderer._resolve_schema(schema_def, types, enumerators)
                if "type_property" in schema:
                    resolved["properties"][schema["type_property"]]["enum"].append(schema_name)
                    
        return resolved 