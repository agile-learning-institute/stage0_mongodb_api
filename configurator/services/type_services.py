from configurator.utils.file_io import FileIO


class Type:
    def __init__(self, file_name: str, document: dict = {}):
        self.file_name = file_name
        self.name = file_name.split(".")[0]
        self.type_property = {}

        if document:
            self.property = TypeProperty(document)
        else:
            self.property = TypeProperty(FileIO.get_document(self.config.TYPES_FOLDER, file_name))

    def to_dict(self):
        return self.property.to_dict()
    
    def get_json_schema(self):
        return self.property.get_json_schema()
    
    def get_bson_schema(self):
        return self.property.get_bson_schema()
                
class TypeProperty:
    def __init__(self, name: str, property: dict):
        self.name = name
        self.description = property["description", "Missing Required Description"]
        self.schema = property["schema", None]
        self.json_type = self.schema["json_type", None]
        self.bson_type = self.schema["bson_type", None]
        self.type = property["type", None]
        self.required = property["required", False]
        self.additional_properties = property["additionalProperties", False]
        if self.type == "array":
            self.items = TypeProperty("items", property["items", {}])
        if self.type == "object":
            self.properties = {}
            for name, property in property["properties", {}].items():
                self.properties[name] = TypeProperty(name, property)
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
                schema.update[self.schema]
            else:
                schema.update[self.json_type]
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
                schema.update[self.schema]
                schema["bsonType"] = schema["type"]
                del schema["type"]
            else:
                schema.update[self.bson_type]
        return schema