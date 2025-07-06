from configurator.services.type_services import Type
from configurator.utils.configurator_exception import ConfiguratorEvent, ConfiguratorException
from configurator.services.enumerator_service import Enumerators
from configurator.utils.file_io import FileIO
import os


class Dictionary:
    def __init__(self, file_name: str = "", document: dict = {}):
        self.file_name = file_name
        if document:
            self.property = Property(document)
        else:
            self.property = Property(FileIO.get_document(self.config.DICTIONARIES_FOLDER, file_name))

    def to_dict(self):
        return self.property.to_dict()
    
    def get_json_schema(self, enumerators: Enumerators):
        return self.property.get_json_schema(enumerators)
    
    def get_bson_schema(self, enumerators: Enumerators):
        return self.property.get_bson_schema(enumerators)
            
    def save(self) -> list[ConfiguratorEvent]:
        event = ConfiguratorEvent(event_id="DIC-03", event_type="SAVE_DICTIONARY")
        try:
            # Get original content before saving
            original_doc = FileIO.get_document(self.config.DICTIONARIES_FOLDER, self.file_name)
            
            # Save the cleaned content
            FileIO.save_document(self.config.DICTIONARIES_FOLDER, self.file_name, self.property.to_dict())
            
            # Re-read the saved content
            saved_doc = FileIO.get_document(self.config.DICTIONARIES_FOLDER, self.file_name)
            
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
            event.append_events(ConfiguratorEvent(event_id="DIC-04", event_type="SAVE_DICTIONARY", data=e))
            event.record_failure(message="unexpected error saving document")
        return [event]

class Property:
    def __init__(self, name: str, property: dict):
        self.name = name
        self.ref = property["$ref", None]
        self.description = property["description", "Missing Required Description"]
        self.type = property["type", "Missing Required Type"]
        self.enums = property["enums", ""]
        self.required = property["required", False]
        self.additional_properties = property["additionalProperties", False]
        self.properties = {}
        for name, property in property["properties", {}].items():
            self.properties[name] = Property(name, property)
        self.items = Property(property["items"])
                    
    def to_dict(self):
        if self.ref:
            return {"$ref": self.ref}
        
        dict = {
            "description": self.description,
            "type": self.type,
        }
        
        if self.type == "object":
            dict["properties"] = {}
            for property in self.properties:
                dict["properties"][property] = self.properties[property].to_dict()
        
        if self.type == "array":
            dict["items"] = self.items.to_dict()
        
        if self.type == "enum" or self.type == "enum_array":
            dict["enums"] = self.enums

        if self.required: 
            dict["required"] = self.required
            
        if self.additional_properties: 
            dict["additionalProperties"] = self.additional_properties
            
        return dict    
    
    def get_json_schema(self, enumerators: Enumerators):
        schema = {}
        if self.ref:
            dictionary = Dictionary(self.ref)
            return dictionary.get_json_schema(enumerators)

        schema["description"] = self.description            
        if self.type == "object":
            schema["type"] = "object"
            for property in self.properties:
                schema["properties"][property] = self.properties[property].get_json_schema(enumerators)
            schema["required"] = self._get_required()
            schema["additionalProperties"] = self.additional_properties
        elif self.type == "array":
            schema["type"] = "array"
            schema["items"] = self.items.get_json_schema(enumerators)
        elif self.type == "enum":
            schema["type"] = "string"
            schema["enums"] = enumerators.get_enum_values(self.enums)
        elif self.type == "enum_array":
            schema["type"] = "array"
            schema["items"] = {"type": "string", "enums": enumerators.get_enum_values(self.enums)}
        else:
            type = Type(f"{self.type}.yaml")
            schema = type.get_json_schema()
            
        return schema
    
    def get_bson_schema(self, enumerators: Enumerators):
        schema = {}
        if self.ref:
            dictionary = Dictionary(self.ref)
            return dictionary.get_bson_schema(enumerators)

        schema["description"] = self.description
        if self.type == "object":
            schema["bsonType"] = "object"
            for property in self.properties:
                schema["properties"][property] = self.properties[property].get_json_schema(enumerators)
            schema["required"] = self._get_required()
            schema["additionalProperties"] = self.additional_properties
        elif self.type == "array":
            schema["bsonType"] = "array"
            schema["items"] = self.items.get_json_schema(enumerators)
        elif self.type == "enum":
            schema["bsonType"] = "string"
            schema["enums"] = enumerators.get_enum_values(self.enums)
        elif self.type == "enum_array":
            schema["bsonType"] = "array"
            schema["items"] = {"type": "string", "enums": enumerators.get_enum_values(self.enums)}
        else:
            type = Type(f"{self.type}.yaml")
            schema = type.get_bson_schema()
            
        return schema
    
    
    def _get_required(self):
        required = []
        for property in self.properties:
            if self.properties[property].required:
                required.append(property)
        return required