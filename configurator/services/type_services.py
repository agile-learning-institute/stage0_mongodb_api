from configurator.utils.file_io import FileIO
from configurator.utils.config import Config
from configurator.utils.configurator_exception import ConfiguratorEvent, ConfiguratorException
import os
import yaml


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
            event.record_failure(message="error saving document")
        except Exception as e:
            event.append_events(ConfiguratorEvent(event_id="TYP-04", event_type="SAVE_TYPE", data=e))
            event.record_failure(message="unexpected error saving document")
        return [event]
    
    def get_json_schema(self):
        return self.property.get_json_schema()
    
    def get_bson_schema(self):
        return self.property.get_bson_schema()
                
class TypeProperty:
    def __init__(self, name: str, property: dict):
        self.name = name
        self.description = property.get("description", "Missing Required Description")
        self.schema = property.get("schema", None)
        self.json_type = self.schema.get("json_type", None) if self.schema else None
        self.bson_type = self.schema.get("bson_type", None) if self.schema else None
        self.type = property.get("type", None)
        self.required = property.get("required", False)
        self.additional_properties = property.get("additionalProperties", False)
        if self.type == "array":
            self.items = TypeProperty("items", property.get("items", {}))
        if self.type == "object":
            self.properties = {}
            for name, prop in property.get("properties", {}).items():
                self.properties[name] = TypeProperty(name, prop)
        # Initialize primitive flags
        self.is_primitive = False
        self.is_universal = False
        
        if self.schema:
            self.is_primitive = True
            self.is_universal = True
        if self.json_type and self.bson_type:
            self.is_primitive = True
            self.is_universal = False

    def to_dict(self):
        dict = {
            "description": self.description,
            "type": self.type,
        }
        if self.type == "array":
            dict["items"] = self.items.to_dict()
            dict["required"] = self.required
        if self.type == "object":
            dict["additionalProperties"] = self.additional_properties
            dict["required"] = self.required
            dict["properties"] = {}
            for name, property in self.properties.items():
                dict["properties"][name] = property.to_dict()
        if self.is_primitive:
            if self.is_universal:
                dict["schema"] = self.schema
            else:
                dict["json_type"] = self.json_type
                dict["bson_type"] = self.bson_type
        return dict
    
    def get_json_schema(self):
        schema = {}
        schema["description"] = self.description
        if self.type == "array":
            schema["type"] = "array"
            schema["items"] = self.items.get_json_schema()
        elif self.type == "object":
            schema["type"] = "object"
            schema["properties"] = {}
            for name, property in self.properties.items():
                schema["properties"][name] = property.get_json_schema()
        elif self.type:
            type = Type(f"{self.type}.yaml")
            schema.update(type.get_json_schema())
        elif self.is_primitive:
            if self.is_universal:
                schema.update(self.schema)
            else:
                schema.update(self.json_type)
        return schema
    
    def get_bson_schema(self):
        schema = {}
        schema["description"] = self.description
        if self.type == "array":
            schema["bsonType"] = "array"
            schema["items"] = self.items.get_bson_schema()
        elif self.type == "object":
            schema["bsonType"] = "object"
            schema["properties"] = {}
            for name, property in self.properties.items():
                schema["properties"][name] = property.get_bson_schema()
        elif self.type:
            type = Type(f"{self.type}.yaml")
            schema.update(type.get_bson_schema())
        elif self.is_primitive:
            if self.is_universal:
                schema.update(self.schema)
                schema["bsonType"] = schema["type"]
                del schema["type"]
            else:
                schema.update(self.bson_type)
        return schema