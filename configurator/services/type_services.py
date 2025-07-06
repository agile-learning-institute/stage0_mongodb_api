from configurator.utils.file_io import FileIO
from configurator.utils.config import Config
from configurator.utils.configurator_exception import ConfiguratorEvent, ConfiguratorException
import os
import yaml
from collections import OrderedDict


class Type:
    def __init__(self, file_name: str, document: dict = {}):
        self.config = Config.get_instance()
        self.file_name = file_name
        self.name = file_name.split(".")[0]
        self.type_property = {}

        if document:
            self.property = TypeProperty(self.name, document)
        else:
            self.property = TypeProperty(self.name, FileIO.get_document(self.config.TYPE_FOLDER, file_name))


    def save(self) -> list[ConfiguratorEvent]:
        event = ConfiguratorEvent(event_id="TYP-03", event_type="SAVE_TYPE")
        try:
            # Get original content before saving
            original_doc = FileIO.get_document(self.config.TYPE_FOLDER, self.file_name)
            
            # Save the cleaned content
            FileIO.put_document(self.config.TYPE_FOLDER, self.file_name, self.property.to_dict())
            
            # Re-read the saved content
            saved_doc = FileIO.get_document(self.config.TYPE_FOLDER, self.file_name)
            
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
            event.append_events([ConfiguratorEvent(event_id="TYP-04", event_type="SAVE_TYPE", event_data={"error": str(e)})])
            event.record_failure("unexpected error saving document")
        return [event]
    
    def get_json_schema(self):
        return self.property.get_json_schema()
    
    def get_bson_schema(self):
        return self.property.get_bson_schema()
                
    def delete(self):
        event = ConfiguratorEvent(event_id="TYP-05", event_type="DELETE_TYPE")
        try:
            FileIO.delete_document(self.config.TYPE_FOLDER, self.file_name)
            event.record_success()
        except ConfiguratorException as e:
            event.append_events([e.event])
            event.record_failure("error deleting type")
        except Exception as e:
            event.record_failure("unexpected error deleting type", {"error": str(e)})
        return event

    def flip_lock(self):
        event = ConfiguratorEvent(event_id="TYP-06", event_type="LOCK_UNLOCK_TYPE")
        try:
            FileIO.lock_unlock(self.config.TYPE_FOLDER, self.file_name)
            event.record_success()
        except ConfiguratorException as e:
            event.append_events([e.event])
            event.record_failure("error locking/unlocking type")
        except Exception as e:
            event.record_failure("unexpected error locking/unlocking type", {"error": str(e)})
        return event

class TypeProperty:
    def __init__(self, name: str, property: dict):
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
    
    def get_json_schema(self):
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
                "items": self.items.get_json_schema()
            }
        if self.type == "object":
            properties = {}
            required_properties = []
            
            for name, property in self.properties.items():
                properties[name] = property.get_json_schema()
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
            custom_type = Type(f"{self.type}.yaml")
            custom_schema = custom_type.property.get_json_schema()
            custom_schema["description"] = self.description
            return custom_schema
    
        raise ConfiguratorException(f"Type {self.type} is not a valid type")
    
    def get_bson_schema(self):
        if self.is_universal:
            schema = self.schema.copy()
            schema["bsonType"] = schema["type"]
            del schema["type"]
            return {
                "description": self.description,
                **schema
            }
        if self.is_primitive:
            return {
                "description": self.description,
                **self.bson_type
            }
        if self.type == "array":
            return {
                "description": self.description,
                "bsonType": "array",
                "items": self.items.get_bson_schema()
            }
        if self.type == "object":
            properties = {}
            required_properties = []
            
            for name, property in self.properties.items():
                properties[name] = property.get_bson_schema()
                if property.required:
                    required_properties.append(name)
            
            result = {
                "description": self.description,
                "bsonType": "object",
                "properties": properties,
                "additionalProperties": self.additional_properties
            }
            
            if required_properties:
                result["required"] = required_properties
                
            return result
        if self.type:
            custom_type = Type(f"{self.type}.yaml")
            custom_schema = custom_type.property.get_bson_schema()
            custom_schema["description"] = self.description
            return custom_schema
        
        raise ConfiguratorException(f"Type {self.type} is not a valid type")