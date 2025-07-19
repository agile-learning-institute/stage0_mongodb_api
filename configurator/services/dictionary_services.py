import os
from configurator.utils.configurator_exception import ConfiguratorException, ConfiguratorEvent
from configurator.utils.file_io import FileIO
from configurator.services.type_services import Type
from configurator.services.enumerator_service import Enumerators
from configurator.utils.config import Config

class Dictionary:
    def __init__(self, file_name: str = "", document: dict = None):
        self.config = Config.get_instance()
        self.file_name = file_name
        self._locked = False
        self.root = None

        try:
            if document is not None:
                self._locked = document.get("_locked", False)
                self.root = Property("root", document["root"])
            else:
                document_data = FileIO.get_document(self.config.DICTIONARY_FOLDER, file_name)
                self._locked = document_data.get("_locked", False)
                self.root = Property("root", document_data["root"])
        except ConfiguratorException as e:
            # Re-raise with additional context about the dictionary file
            event = ConfiguratorEvent(event_id=f"DIC-CONSTRUCTOR-{file_name}", event_type="DICTIONARY_CONSTRUCTOR")
            event.record_failure(f"Failed to construct dictionary from {file_name}")
            event.append_events([e.event])
            raise ConfiguratorException(f"Failed to construct dictionary from {file_name}: {str(e)}", event)
        except Exception as e:
            # Handle unexpected errors during construction
            event = ConfiguratorEvent(event_id=f"DIC-CONSTRUCTOR-{file_name}", event_type="DICTIONARY_CONSTRUCTOR")
            event.record_failure(f"Unexpected error constructing dictionary from {file_name}: {str(e)}")
            raise ConfiguratorException(f"Unexpected error constructing dictionary from {file_name}: {str(e)}", event)

    def to_dict(self):
        result = {}
        result["file_name"] = self.file_name
        result["_locked"] = self._locked
        result["root"] = self.root.to_dict()
        return result

    def save(self):
        """Save the dictionary and return the File object."""
        try:
            event = ConfiguratorEvent("DIC-03", "PUT_DICTIONARY")
            file_obj = FileIO.put_document(self.config.DICTIONARY_FOLDER, self.file_name, self.to_dict())
            return file_obj
        except ConfiguratorException as e:
            event.append_events([e.event])
            event.record_failure(f"Failed to save dictionary {self.file_name}: {str(e)}")
            raise ConfiguratorException(f"Failed to save dictionary {self.file_name}: {str(e)}", event)
        except Exception as e:
            event.record_failure(f"Failed to save dictionary {self.file_name}: {str(e)}")
            raise ConfiguratorException(f"Failed to save dictionary {self.file_name}: {str(e)}", event)

    def get_json_schema(self, enumerations, ref_stack: list = None):
        if ref_stack is None:
            ref_stack = []
        return self.root.get_json_schema(enumerations, ref_stack)

    def get_bson_schema(self, enumerations, ref_stack: list = None):
        if ref_stack is None:
            ref_stack = []
        return self.root.get_bson_schema(enumerations, ref_stack)

    @staticmethod
    def lock_all():
        """Lock all dictionary files."""
        config = Config.get_instance()
        event = ConfiguratorEvent("DIC-05", "LOCK_ALL_DICTIONARIES")
        
        try:
            files = FileIO.get_documents(config.DICTIONARY_FOLDER)
            for file in files:
                sub_event = ConfiguratorEvent(f"DIC-{file.file_name}", "LOCK_DICTIONARY")
                event.append_events([sub_event])
                dictionary = Dictionary(file.file_name)
                dictionary._locked = True
                dictionary.save()                
                sub_event.record_success()
            event.record_success()
            return event
        except ConfiguratorException as ce:
            event.append_events([ce.event])
            event.record_failure(f"ConfiguratorException locking dictionary {file.file_name}")
            raise ConfiguratorException(f"ConfiguratorException locking dictionary {file.file_name}", event)
        except Exception as e:
            event.record_failure(f"Unexpected error locking dictionary {file.file_name}")
            raise ConfiguratorException(f"Unexpected error locking dictionary {file.file_name}", event)

    def delete(self):
        if self._locked:
            event = ConfiguratorEvent(event_id="DIC-05", event_type="DELETE_DICTIONARY", event_data={"error": "Dictionary is locked"})
            raise ConfiguratorException("Cannot delete locked dictionary", event)
        event = ConfiguratorEvent(event_id="DIC-05", event_type="DELETE_DICTIONARY")
        try:
            event.append_events(FileIO.delete_document(self.config.DICTIONARY_FOLDER, self.file_name))
            event.record_success()
            return event
        except ConfiguratorException as e:
            event.append_events([e.event])
            event.record_failure("error deleting dictionary")
            return event
        except Exception as e:
            event.record_failure("unexpected error deleting dictionary", {"error": str(e)})
            return event


class Property:
    """
    Property class is used to represent a property in a dictionary.

    Properties have 5 type specific forms. 
    A ref property is a reference to another property file and is a solo format with only this property
    All other properties have a name, and description, type, and required properties boolean.
    type: object properties have properties, additional_properties boolean, and optionally one_of
    type: list properties have items
    type: enum and enum_array properties have enums
    type: Anything else is considered a custom type 
    """
    def __init__(self, name: str, property: dict):
        self.config = Config.get_instance()
        self.name = name
        self.ref = property.get("ref", None)
        self.description = property.get("description", "Missing Required Description")
        self.type = property.get("type", "void")
        self.required = property.get("required", False)
        self.enums = property.get("enums", None)
        self.additional_properties = property.get("additionalProperties", False)
        self.properties = {}
        self.items = None
        self.one_of = None

        # Initialize properties if this is an object type
        if self.type == "object":
            for prop_name, prop_data in property.get("properties", {}).items():
                self.properties[prop_name] = Property(prop_name, prop_data)

            # Initialize oneOf if present
            one_of_data = property.get("one_of", None)
            if one_of_data:
                self.one_of = OneOf(one_of_data)

        # Initialize items if this is an array type
        if self.type == "array":
            items_data = property.get("items", {})
            if items_data:
                self.items = Property("items", items_data)

        if self.type == "enum" or self.type == "enum_array":
            self.enums = property.get("enums", None)

    def to_dict(self):
        if self.ref:
            return {"ref": self.ref}
        result = {}
        result["description"] = self.description
        result["type"] = self.type
        result["required"] = self.required

        if self.type == "object":
            result["additionalProperties"] = self.additional_properties
            result["properties"] = {}
            for prop_name, prop in self.properties.items():
                result["properties"][prop_name] = prop.to_dict()

            if self.one_of:
                result["one_of"] = self.one_of.to_dict()

        elif self.type == "array":
            result["items"] = self.items.to_dict()

        elif self.type in ["enum", "enum_array"]:
            result["enums"] = self.enums

        return result

    def get_json_schema(self, enumerations, ref_stack: list = None):
        if ref_stack is None:
            ref_stack = []

        if self.ref:
            return self._handle_ref_schema(enumerations, ref_stack, "json")

        if self.type == "object":
            schema = {}
            schema["description"] = self.description
            schema["type"] = "object"
            schema["properties"] = {}
            for prop_name, prop in self.properties.items():
                schema["properties"][prop_name] = prop.get_json_schema(enumerations, ref_stack)
            required_props = self._get_required()
            if required_props:
                schema["required"] = required_props
            schema["additionalProperties"] = self.additional_properties

            # Handle oneOf structure (JSON Schema standard)
            if self.one_of:
                schema["oneOf"] = self.one_of.get_json_schema(enumerations, ref_stack)

            return schema

        elif self.type == "array":
            schema = {}
            schema["description"] = self.description
            schema["type"] = "array"
            if self.items:
                schema["items"] = self.items.get_json_schema(enumerations, ref_stack)
            return schema

        elif self.type == "enum":
            schema = {}
            schema["description"] = self.description
            schema["type"] = "string"
            if self.enums:
                schema["enum"] = enumerations.get_enum_values(self.enums)
            return schema

        elif self.type == "enum_array":
            schema = {}
            schema["description"] = self.description
            schema["type"] = "array"
            if self.enums:
                schema["items"] = {"type": "string", "enum": enumerations.get_enum_values(self.enums)}
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

    def get_bson_schema(self, enumerations, ref_stack: list = None):
        if ref_stack is None:
            ref_stack = []

        if self.ref:
            return self._handle_ref_schema(enumerations, ref_stack, "bson")

        if self.type == "object":
            schema = {}
            schema["bsonType"] = "object"
            schema["properties"] = {}
            for prop_name, prop in self.properties.items():
                schema["properties"][prop_name] = prop.get_bson_schema(enumerations, ref_stack)
            required_props = self._get_required()
            if required_props:
                schema["required"] = required_props
            schema["additionalProperties"] = self.additional_properties

            # Handle oneOf structure (JSON Schema standard)
            if self.one_of:
                schema["oneOf"] = self.one_of.get_bson_schema(enumerations, ref_stack)

            return schema

        elif self.type == "array":
            schema = {}
            schema["bsonType"] = "array"
            if self.items:
                schema["items"] = self.items.get_bson_schema(enumerations, ref_stack)
            return schema

        elif self.type == "enum":
            schema = {}
            schema["bsonType"] = "string"
            if self.enums:
                schema["enum"] = enumerations.get_enum_values(self.enums)
            return schema

        elif self.type == "enum_array":
            schema = {}
            schema["bsonType"] = "array"
            if self.enums:
                schema["items"] = {"bsonType": "string", "enum": enumerations.get_enum_values(self.enums)}
            return schema

        elif self.type:
            # Reference a custom type
            custom_type = Type(f"{self.type}.yaml")
            custom_schema = custom_type.get_bson_schema()
            return custom_schema
        else:
            raise ConfiguratorException(f"Invalid dictionary property type: {self.type}",
                                      ConfiguratorEvent(event_id="DIC-99", event_type="INVALID_PROPERTY_TYPE"))

        return schema

    def _handle_ref_schema(self, enumerations, ref_stack: list, schema_type: str):
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
                return dictionary.get_json_schema(enumerations, ref_stack)
            else:
                return dictionary.get_bson_schema(enumerations, ref_stack)
        finally:
            ref_stack.pop()

    def _get_required(self):
        required = []
        for prop_name, prop in self.properties.items():
            if prop.required:
                required.append(prop_name)
        return required


class OneOf:
    def __init__(self, one_of_data):
        self.schemas = []
        
        # Handle array format (JSON Schema standard)
        if isinstance(one_of_data, list):
            for i, schema_data in enumerate(one_of_data):
                # Check if this is a ref object
                if isinstance(schema_data, dict) and "ref" in schema_data:
                    # Create a Property with just the ref
                    self.schemas.append(Property(f"oneOf_item_{i}", {"ref": schema_data["ref"]}))
                else:
                    # Regular schema object
                    self.schemas.append(Property(f"oneOf_item_{i}", schema_data))
        else:
            # If not a list, this is an error - oneOf should always be an array
            raise ConfiguratorException(
                f"oneOf data must be an array, got {type(one_of_data)}", 
                ConfiguratorEvent(event_id="DIC-10", event_type="INVALID_ONEOF_FORMAT")
            )

    def to_dict(self):
        # Return array of schemas (JSON Schema standard)
        return [schema.to_dict() for schema in self.schemas]

    def get_json_schema(self, enumerations, ref_stack: list = None):
        return [schema.get_json_schema(enumerations, ref_stack) for schema in self.schemas]

    def get_bson_schema(self, enumerations, ref_stack: list = None):
        return [schema.get_bson_schema(enumerations, ref_stack) for schema in self.schemas]