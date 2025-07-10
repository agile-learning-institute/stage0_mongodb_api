"""
Type Definitions
===============

A valid Type in this system must be one of the following three forms:

1. Universal Primitive:
   - Has only a top-level 'schema' property (e.g., {'schema': {'type': 'string', 'format': 'email'}})
   - Must NOT have 'json_type' or 'bson_type' at any level.

2. Typed Primitive:
   - Has top-level 'json_type' and/or 'bson_type' properties (e.g., {'json_type': {...}, 'bson_type': {...}})
   - Must NOT have a 'schema' property.

3. Complex Type (object or array):
   - Has 'type': 'object' or 'type': 'array' at the top level.
   - For 'object', must have a 'properties' dict; for 'array', must have an 'items' property.
   - May have additional fields like 'description', 'required', 'additionalProperties', etc.

Any other combination (e.g., 'schema' containing 'json_type'/'bson_type', or both 'schema' and 'json_type'/'bson_type' at the top level) is invalid and will raise an error.
"""
from configurator.utils.file_io import FileIO, File
from configurator.utils.config import Config
from configurator.utils.configurator_exception import ConfiguratorEvent, ConfiguratorException
import os
import yaml
from collections import OrderedDict


class Type:
    def __init__(self, file_name: str, document: dict = {}):
        self.config = Config.get_instance()
        self.file_name = file_name
        self.type_property = {}
        self._locked = False  # Default to unlocked

        if document:
            self.property = TypeProperty(file_name.replace('.yaml', ''), document)
            # Extract _locked from document if present
            self._locked = document.get("_locked", False)
        else:
            document_data = FileIO.get_document(self.config.TYPE_FOLDER, file_name)
            self.property = TypeProperty(file_name.replace('.yaml', ''), document_data)
            # Extract _locked from loaded document if present
            self._locked = document_data.get("_locked", False)


    def save(self):
        """Save the type and return the Type object."""
        try:
            # Save the cleaned content
            FileIO.put_document(self.config.TYPE_FOLDER, self.file_name, self.to_dict())
            return self
        except Exception as e:
            event = ConfiguratorEvent("TYP-03", "PUT_TYPE")
            event.record_failure(f"Failed to save type {self.file_name}: {str(e)}")
            raise ConfiguratorException(f"Failed to save type {self.file_name}: {str(e)}", event)
    
    @staticmethod
    def lock_all():
        """Lock all type files and return event with sub-events."""
        config = Config.get_instance()
        files = FileIO.get_documents(config.TYPE_FOLDER)
        
        event = ConfiguratorEvent("TYP-04", "LOCK_ALL_TYPES")
        event.data = {
            "total_files": len(files),
            "operation": "lock_all"
        }
        
        for file in files:
            try:
                type_obj = Type(file.name)
                # Set locked state and save using normal save() method
                type_obj._locked = True
                type_obj.save()
                
                sub_event = ConfiguratorEvent(f"TYP-{file.name}", "LOCK_TYPE")
                sub_event.data = {
                    "file_name": file.name,
                    "type_name": type_obj.file_name.replace('.yaml', ''),
                    "locked": True
                }
                sub_event.record_success()
                event.append_events([sub_event])
                
            except Exception as e:
                sub_event = ConfiguratorEvent(f"TYP-{file.name}", "LOCK_TYPE")
                sub_event.data = {
                    "file_name": file.name,
                    "error": str(e)
                }
                sub_event.record_failure(f"Failed to lock type {file.name}")
                event.append_events([sub_event])
        
        # Record overall success/failure based on sub-events
        if any(sub.status == "FAILURE" for sub in event.sub_events):
            event.record_failure("Some types failed to lock")
        else:
            event.record_success()
        
        return event
    
    def get_json_schema(self, type_stack: list = None):
        if type_stack is None:
            type_stack = []
        return self.property.get_json_schema(type_stack)
    
    def get_bson_schema(self, type_stack: list = None):
        if type_stack is None:
            type_stack = []
        return self.property.get_bson_schema(type_stack)
    
    def to_dict(self):
        return {
            "file_name": self.file_name,
            "_locked": self._locked,  # Always include _locked
            **self.property.to_dict()
        }
                
    def delete(self):
        if self._locked:
            event = ConfiguratorEvent(event_id="TYP-05", event_type="DELETE_TYPE", event_data={"error": "Type is locked"})
            raise ConfiguratorException("Cannot delete locked type", event)
        event = ConfiguratorEvent(event_id="TYP-05", event_type="DELETE_TYPE")
        try:
            delete_event = FileIO.delete_document(self.config.TYPE_FOLDER, self.file_name)
            if delete_event.status == "SUCCESS":
                event.record_success()
            else:
                event.append_events([delete_event])
                event.record_failure("error deleting type")
        except ConfiguratorException as e:
            event.append_events([e.event])
            event.record_failure("error deleting type")
        except Exception as e:
            event.record_failure("unexpected error deleting type", {"error": str(e)})
        return event



class TypeProperty:
    def __init__(self, name: str, property: dict):
        self.config = Config.get_instance()
        self.name = name
        self.description = property.get("description", "Missing Required Description")
        self.schema = property.get("schema", None)
        self.json_type = property.get("json_type", None)
        self.bson_type = property.get("bson_type", None)
        self.type = property.get("type", None)
        self.required = property.get("required", False)
        self.additional_properties = property.get("additionalProperties", False)
        self.is_primitive = False
        self.is_universal = False

        # Enforce mutual exclusivity
        if self.schema is not None and (self.json_type is not None or self.bson_type is not None):
            event = ConfiguratorEvent("TYP-99", "INVALID_TYPE_DEFINITION")
            event.record_failure("Type definition cannot have both 'schema' and 'json_type'/'bson_type' at the top level.")
            raise ConfiguratorException("Type definition cannot have both 'schema' and 'json_type'/'bson_type' at the top level.", event)
        if self.schema is not None and ("json_type" in self.schema or "bson_type" in self.schema):
            event = ConfiguratorEvent("TYP-99", "INVALID_TYPE_DEFINITION")
            event.record_failure("'json_type' and 'bson_type' must not be nested under 'schema'. They must be top-level properties.")
            raise ConfiguratorException("'json_type' and 'bson_type' must not be nested under 'schema'. They must be top-level properties.", event)

        # Universal primitive: schema only
        if self.schema is not None:
            self.is_primitive = True
            self.is_universal = True
            return
        # Non-universal primitive: json_type/bson_type only
        if self.json_type is not None or self.bson_type is not None:
            self.is_primitive = True
            self.is_universal = False
            return
        # Array
        if self.type == "array":
            self.items = TypeProperty("items", property.get("items", {}))
            return
        # Object
        if self.type == "object":
            self.properties = {}
            for name, prop in property.get("properties", {}).items():
                self.properties[name] = TypeProperty(name, prop)
            return

    def to_dict(self):
        # Universal primitive
        if self.is_universal:
            return {
                "description": self.description,
                "schema": self.schema,
            }
        # Non-universal primitive
        if self.is_primitive:
            return {
                "description": self.description,
                "json_type": self.json_type or {},
                "bson_type": self.bson_type or {},
            }
        # Array
        if self.type == "array":
            return {
                "description": self.description,
                "required": self.required,
                "type": self.type,
                "items": self.items.to_dict(),
            }
        # Object
        if self.type == "object":
            return {
                "description": self.description,
                "required": self.required,
                "type": self.type,
                "properties": {name: property.to_dict() for name, property in self.properties.items()},
                "additionalProperties": self.additional_properties
            }
        # Basic type (string, number, etc.)
        return {
            "description": self.description,
            "type": self.type
        }
    
    def get_json_schema(self, type_stack: list = None):
        if type_stack is None:
            type_stack = []
        if self.is_universal:
            return {
                "description": self.description,
                **self.schema
            }
        if self.is_primitive:
            return {
                "description": self.description,
                **self.json_type
            }
        if self.type == "array":
            return {
                "description": self.description,
                "type": "array",
                "items": self.items.get_json_schema(type_stack)
            }
        if self.type == "object":
            properties = {}
            required_properties = []
            
            for name, property in self.properties.items():
                properties[name] = property.get_json_schema(type_stack)
                if property.required:
                    required_properties.append(name)
            
            result = {
                "description": self.description,
                "type": "object",
                "properties": properties,
                "additionalProperties": self.additional_properties
            }
            
            if required_properties:
                result["required"] = required_properties
                
            return result
        if self.type:
            return self._handle_type_reference(type_stack, "json")

        raise ConfiguratorException(f"Type {self.type} is not a valid type", ConfiguratorEvent(event_id="TYP-99", event_type="INVALID_TYPE"))
    
    def get_bson_schema(self, type_stack: list = None):
        if type_stack is None:
            type_stack = []
        if self.is_universal:
            schema = self.schema.copy()
            schema["bsonType"] = schema["type"]
            del schema["type"]
            return {
                **schema
            }
        if self.is_primitive:
            return {
                **self.bson_type
            }
        if self.type == "array":
            return {
                "bsonType": "array",
                "items": self.items.get_bson_schema(type_stack)
            }
        if self.type == "object":
            properties = {}
            required_properties = []
            
            for name, property in self.properties.items():
                properties[name] = property.get_bson_schema(type_stack)
                if property.required:
                    required_properties.append(name)
            
            result = {
                "bsonType": "object",
                "properties": properties,
                "additionalProperties": self.additional_properties
            }
            
            if required_properties:
                result["required"] = required_properties
                
            return result
        if self.type:
            return self._handle_type_reference(type_stack, "bson")

        raise ConfiguratorException(f"Type {self.type} is not a valid type", ConfiguratorEvent(event_id="TYP-99", event_type="INVALID_TYPE"))

    def _handle_type_reference(self, type_stack: list, schema_type: str):
        """Handle type reference processing with circular reference and depth checking."""
        type_name = f"{self.type}.yaml"
        # Check for circular reference
        if type_name in type_stack:
            type_chain = " -> ".join(type_stack + [type_name])
            event = ConfiguratorEvent(
                event_id="TYP-07", 
                event_type="CIRCULAR_TYPE_REFERENCE",
                event_data={"type_chain": type_chain, "type_stack": type_stack}
            )
            raise ConfiguratorException(f"Circular type reference detected: {type_chain}", event)
        # Check stack depth limit
        if len(type_stack) >= self.config.RENDER_STACK_MAX_DEPTH:
            event = ConfiguratorEvent(
                event_id="TYP-08", 
                event_type="TYPE_STACK_DEPTH_EXCEEDED",
                event_data={"max_depth": self.config.RENDER_STACK_MAX_DEPTH, "current_depth": len(type_stack)}
            )
            raise ConfiguratorException(f"Type stack depth exceeded maximum of {self.config.RENDER_STACK_MAX_DEPTH}", event)
        # Add current type to stack and process
        type_stack.append(type_name)
        try:
            custom_type = Type(type_name)
            if schema_type == "json":
                custom_schema = custom_type.property.get_json_schema(type_stack)
            else:
                custom_schema = custom_type.property.get_bson_schema(type_stack)
            return custom_schema
        finally:
            type_stack.pop()