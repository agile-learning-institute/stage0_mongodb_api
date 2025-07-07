from configurator.services.type_services import Type
from configurator.utils.configurator_exception import ConfiguratorEvent, ConfiguratorException
from configurator.services.enumerator_service import Enumerators
from configurator.utils.file_io import FileIO
from configurator.utils.config import Config
import os


class Dictionary:
    def __init__(self, file_name: str = "", document: dict = {}):
        self.config = Config.get_instance()
        self.file_name = file_name
        if document:
            self.property = Property("root", document)
        else:
            self.property = Property("root", FileIO.get_document(self.config.DICTIONARY_FOLDER, file_name))

    def to_dict(self):
        return self.property.to_dict()
    
    def get_json_schema(self, enumerators: Enumerators, ref_stack: list = None):
        if ref_stack is None:
            ref_stack = []
        return self.property.get_json_schema(enumerators, ref_stack)
    
    def get_bson_schema(self, enumerators: Enumerators, ref_stack: list = None):
        if ref_stack is None:
            ref_stack = []
        return self.property.get_bson_schema(enumerators, ref_stack)
            
    def save(self) -> list[ConfiguratorEvent]:
        event = ConfiguratorEvent(event_id="DIC-03", event_type="SAVE_DICTIONARY")
        try:
            # Get original content before saving
            original_doc = FileIO.get_document(self.config.DICTIONARY_FOLDER, self.file_name)
            
            # Save the cleaned content
            FileIO.put_document(self.config.DICTIONARY_FOLDER, self.file_name, self.property.to_dict())
            
            # Re-read the saved content
            saved_doc = FileIO.get_document(self.config.DICTIONARY_FOLDER, self.file_name)
            
            # Compare and set event data
            original_keys = set(original_doc.keys())
            saved_keys = set(saved_doc.keys())
            
            added = saved_keys - original_keys
            removed = original_keys - saved_keys
            
            event.data = {
                "added": {k: saved_doc[k] for k in added},
                "removed": {k: original_doc[k] for k in removed}
            }
            
            event.record_success()
        except ConfiguratorException as e:
            event.append_events([e.event])
            event.record_failure("error saving document")
        except Exception as e:
            event.append_events([ConfiguratorEvent(event_id="DIC-04", event_type="SAVE_DICTIONARY", event_data={"error": str(e)})])
            event.record_failure("unexpected error saving document")
        return [event]

    def delete(self):
        event = ConfiguratorEvent(event_id="DIC-05", event_type="DELETE_DICTIONARY")
        try:
            FileIO.delete_document(self.config.DICTIONARY_FOLDER, self.file_name)
            event.record_success()
        except ConfiguratorException as e:
            event.append_events([e.event])
            event.record_failure("error deleting dictionary")
        except Exception as e:
            event.record_failure("unexpected error deleting dictionary", {"error": str(e)})
        return event

    def lock_unlock(self):
        event = ConfiguratorEvent(event_id="DIC-06", event_type="LOCK_UNLOCK_DICTIONARY")
        try:
            FileIO.lock_unlock(self.config.DICTIONARY_FOLDER, self.file_name)
            event.record_success()
        except ConfiguratorException as e:
            event.append_events([e.event])
            event.record_failure("error locking/unlocking dictionary")
        except Exception as e:
            event.record_failure("unexpected error locking/unlocking dictionary", {"error": str(e)})
        return event

class Property:
    def __init__(self, name: str, property: dict):
        self.config = Config.get_instance()
        self.name = name
        self.ref = property.get("$ref", None)
        self.description = property.get("description", "Missing Required Description")
        self.type = property.get("type", None)
        self.enums = property.get("enums", None)
        self.required = property.get("required", False)
        self.additional_properties = property.get("additionalProperties", False)
        self.properties = {}
        self.items = None
        
        # Initialize properties if this is an object type
        if self.type == "object":
            for prop_name, prop_data in property.get("properties", {}).items():
                self.properties[prop_name] = Property(prop_name, prop_data)
        
        # Initialize items if this is an array type
        if self.type == "array":
            items_data = property.get("items", {})
            if items_data:
                self.items = Property("items", items_data)
                    
    def to_dict(self):
        if self.ref:
            return {"$ref": self.ref}
        result = {}
        
        if self.type == "object":
            result["description"] = self.description
            result["type"] = self.type
            result["required"] = self.required
            result["properties"] = {}
            for prop_name, prop in self.properties.items():
                result["properties"][prop_name] = prop.to_dict()
            result["additionalProperties"] = self.additional_properties
        
        elif self.type == "array":
            result["description"] = self.description
            result["type"] = self.type
            result["required"] = self.required
            result["items"] = self.items.to_dict()
        
        elif self.type in ["enum", "enum_array"]:
            result["description"] = self.description
            result["type"] = self.type
            result["required"] = self.required
            result["enums"] = self.enums
            
        elif self.type:
            # Custom type (like identifier, word, etc.)
            result["description"] = self.description
            result["type"] = self.type
            result["required"] = self.required
            
        return result    
    
    def get_json_schema(self, enumerators: Enumerators, ref_stack: list = None):
        if ref_stack is None:
            ref_stack = []
        
        if self.ref:
            return self._handle_ref_schema(enumerators, ref_stack, "json")

        if self.type == "object":
            schema = {}
            schema["description"] = self.description
            schema["type"] = "object"
            schema["properties"] = {}
            for prop_name, prop in self.properties.items():
                schema["properties"][prop_name] = prop.get_json_schema(enumerators, ref_stack)
            required_props = self._get_required()
            if required_props:
                schema["required"] = required_props
            schema["additionalProperties"] = self.additional_properties
            return schema
            
        elif self.type == "array":
            schema = {}
            schema["description"] = self.description
            schema["type"] = "array"
            if self.items:
                schema["items"] = self.items.get_json_schema(enumerators, ref_stack)
            return schema
            
        elif self.type == "enum":
            schema = {}
            schema["description"] = self.description
            schema["type"] = "string"
            if self.enums:
                schema["enum"] = enumerators.get_enum_values(self.enums)
            return schema
            
        elif self.type == "enum_array":
            schema = {}
            schema["description"] = self.description
            schema["type"] = "array"
            if self.enums:
                schema["items"] = {"type": "string", "enum": enumerators.get_enum_values(self.enums)}
            return schema
            
        elif self.type:
            # Reference a custom type
            custom_type = Type(f"{self.type}.yaml")
            custom_schema = custom_type.get_json_schema()
            custom_schema["description"] = self.description
            return custom_schema
        else:
            raise ConfiguratorException(f"Invalid dictionary property type: {self.type}", 
                                      ConfiguratorEvent(event_id="DIC-99", event_type="INVALID_PROPERTY_TYPE"))
            
    def get_bson_schema(self, enumerators: Enumerators, ref_stack: list = None):
        if ref_stack is None:
            ref_stack = []
        
        if self.ref:
            return self._handle_ref_schema(enumerators, ref_stack, "bson")

        if self.type == "object":
            schema = {}
            schema["description"] = self.description
            schema["bsonType"] = "object"
            schema["properties"] = {}
            for prop_name, prop in self.properties.items():
                schema["properties"][prop_name] = prop.get_bson_schema(enumerators, ref_stack)
            required_props = self._get_required()
            if required_props:
                schema["required"] = required_props
            schema["additionalProperties"] = self.additional_properties
            return schema
            
        elif self.type == "array":
            schema = {}
            schema["description"] = self.description
            schema["bsonType"] = "array"
            if self.items:
                schema["items"] = self.items.get_bson_schema(enumerators, ref_stack)
            return schema
            
        elif self.type == "enum":
            schema = {}
            schema["description"] = self.description
            schema["bsonType"] = "string"
            if self.enums:
                schema["enum"] = enumerators.get_enum_values(self.enums)
            return schema
            
        elif self.type == "enum_array":
            schema = {}
            schema["description"] = self.description
            schema["bsonType"] = "array"
            if self.enums:
                schema["items"] = {"bsonType": "string", "enum": enumerators.get_enum_values(self.enums)}
            return schema
            
        elif self.type:
            # Reference a custom type
            custom_type = Type(f"{self.type}.yaml")
            custom_schema = custom_type.get_bson_schema()
            custom_schema["description"] = self.description
            return custom_schema
        else:
            raise ConfiguratorException(f"Invalid dictionary property type: {self.type}", 
                                      ConfiguratorEvent(event_id="DIC-99", event_type="INVALID_PROPERTY_TYPE"))
            
        return schema
    
    def _handle_ref_schema(self, enumerators: Enumerators, ref_stack: list, schema_type: str):
        """Handle reference schema processing with circular reference and depth checking."""
        # Check for circular reference
        if self.ref in ref_stack:
            ref_chain = " -> ".join(ref_stack + [self.ref])
            event = ConfiguratorEvent(
                event_id="DIC-07", 
                event_type="CIRCULAR_REFERENCE",
                event_data={"ref_chain": ref_chain, "ref_stack": ref_stack}
            )
            raise ConfiguratorException(f"Circular reference detected: {ref_chain}", event)
        
        # Check stack depth limit
        if len(ref_stack) >= self.config.RENDER_STACK_MAX_DEPTH:
            event = ConfiguratorEvent(
                event_id="DIC-08", 
                event_type="STACK_DEPTH_EXCEEDED",
                event_data={"max_depth": self.config.RENDER_STACK_MAX_DEPTH, "current_depth": len(ref_stack)}
            )
            raise ConfiguratorException(f"Reference stack depth exceeded maximum of {self.config.RENDER_STACK_MAX_DEPTH}", event)
        
        # Add current ref to stack and process
        ref_stack.append(self.ref)
        try:
            dictionary = Dictionary(self.ref)
            if schema_type == "json":
                return dictionary.get_json_schema(enumerators, ref_stack)
            else:
                return dictionary.get_bson_schema(enumerators, ref_stack)
        finally:
            ref_stack.pop()
    
    def _get_required(self):
        required = []
        for prop_name, prop in self.properties.items():
            if prop.required:
                required.append(prop_name)
        return required