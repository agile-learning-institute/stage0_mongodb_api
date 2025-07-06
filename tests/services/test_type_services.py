import unittest
from unittest.mock import patch, MagicMock
from configurator.services.type_services import Type, TypeProperty


class TestTypeProperty(unittest.TestCase):
    """Test cases for TypeProperty class"""

    def test_init_with_basic_property(self):
        """Test TypeProperty initialization with basic property"""
        property_data = {
            "description": "Test description",
            "type": "string",
            "required": True
        }
        type_prop = TypeProperty("test_prop", property_data)
        
        self.assertEqual(type_prop.name, "test_prop")
        self.assertEqual(type_prop.description, "Test description")
        self.assertEqual(type_prop.type, "string")
        self.assertTrue(type_prop.required)
        self.assertFalse(type_prop.additional_properties)

    def test_init_with_schema(self):
        """Test TypeProperty initialization with schema"""
        property_data = {
            "description": "Test description",
            "schema": {
                "json_type": {"type": "string"},
                "bson_type": {"bsonType": "string"}
            }
        }
        type_prop = TypeProperty("test_prop", property_data)
        
        self.assertEqual(type_prop.schema, property_data["schema"])
        self.assertEqual(type_prop.json_type, {"type": "string"})
        self.assertEqual(type_prop.bson_type, {"bsonType": "string"})
        self.assertTrue(type_prop.is_primitive)
        self.assertFalse(type_prop.is_universal)

    def test_init_with_universal_schema(self):
        """Test TypeProperty initialization with universal schema"""
        property_data = {
            "description": "Test description",
            "schema": {"type": "string", "format": "email"}
        }
        type_prop = TypeProperty("test_prop", property_data)
        
        self.assertTrue(type_prop.is_primitive)
        self.assertTrue(type_prop.is_universal)

    def test_init_with_array_type(self):
        """Test TypeProperty initialization with array type"""
        property_data = {
            "description": "Array of strings",
            "type": "array",
            "items": {
                "description": "String item",
                "type": "string"
            }
        }
        type_prop = TypeProperty("test_array", property_data)
        
        self.assertEqual(type_prop.type, "array")
        self.assertIsInstance(type_prop.items, TypeProperty)
        self.assertEqual(type_prop.items.description, "String item")

    def test_init_with_object_type(self):
        """Test TypeProperty initialization with object type"""
        property_data = {
            "description": "Object with properties",
            "type": "object",
            "additionalProperties": True,
            "properties": {
                "name": {
                    "description": "Name property",
                    "type": "string"
                },
                "age": {
                    "description": "Age property",
                    "type": "number"
                }
            }
        }
        type_prop = TypeProperty("test_object", property_data)
        
        self.assertEqual(type_prop.type, "object")
        self.assertTrue(type_prop.additional_properties)
        self.assertIn("name", type_prop.properties)
        self.assertIn("age", type_prop.properties)
        self.assertEqual(type_prop.properties["name"].description, "Name property")

    def test_init_with_missing_values(self):
        """Test TypeProperty initialization with missing values"""
        property_data = {}
        type_prop = TypeProperty("test_prop", property_data)
        
        self.assertEqual(type_prop.description, "Missing Required Description")
        self.assertIsNone(type_prop.schema)
        self.assertIsNone(type_prop.json_type)
        self.assertIsNone(type_prop.bson_type)
        self.assertIsNone(type_prop.type)
        self.assertFalse(type_prop.required)
        self.assertFalse(type_prop.additional_properties)

    def test_to_dict_basic(self):
        """Test to_dict method for basic property"""
        property_data = {
            "description": "Test description",
            "type": "string",
            "required": True
        }
        type_prop = TypeProperty("test_prop", property_data)
        result = type_prop.to_dict()
        
        expected = {
            "description": "Test description",
            "type": "string"
        }
        self.assertEqual(result, expected)

    def test_to_dict_with_array(self):
        """Test to_dict method for array property"""
        property_data = {
            "description": "Array of strings",
            "type": "array",
            "required": True,
            "items": {
                "description": "String item",
                "type": "string"
            }
        }
        type_prop = TypeProperty("test_array", property_data)
        result = type_prop.to_dict()
        
        self.assertEqual(result["description"], "Array of strings")
        self.assertEqual(result["type"], "array")
        self.assertTrue(result["required"])
        self.assertIn("items", result)

    def test_to_dict_with_object(self):
        """Test to_dict method for object property"""
        property_data = {
            "description": "Object with properties",
            "type": "object",
            "additionalProperties": True,
            "required": False,
            "properties": {
                "name": {
                    "description": "Name property",
                    "type": "string"
                }
            }
        }
        type_prop = TypeProperty("test_object", property_data)
        result = type_prop.to_dict()
        
        self.assertEqual(result["description"], "Object with properties")
        self.assertEqual(result["type"], "object")
        self.assertTrue(result["additionalProperties"])
        self.assertFalse(result["required"])
        self.assertIn("properties", result)
        self.assertIn("name", result["properties"])

    def test_to_dict_with_primitive_universal(self):
        """Test to_dict method for primitive universal property"""
        property_data = {
            "description": "Test description",
            "schema": {"type": "string", "format": "email"}
        }
        type_prop = TypeProperty("test_prop", property_data)
        result = type_prop.to_dict()
        
        self.assertEqual(result["description"], "Test description")
        self.assertEqual(result["schema"], {"type": "string", "format": "email"})

    def test_to_dict_with_primitive_non_universal(self):
        """Test to_dict method for primitive non-universal property"""
        property_data = {
            "description": "Test description",
            "schema": {
                "json_type": {"type": "string"},
                "bson_type": {"bsonType": "string"}
            }
        }
        type_prop = TypeProperty("test_prop", property_data)
        result = type_prop.to_dict()
        
        self.assertEqual(result["description"], "Test description")
        self.assertEqual(result["json_type"], {"type": "string"})
        self.assertEqual(result["bson_type"], {"bsonType": "string"})

    @patch('configurator.services.type_services.Type')
    def test_get_json_schema_with_array(self, mock_type_class):
        """Test get_json_schema method for array type"""
        property_data = {
            "description": "Array of strings",
            "type": "array",
            "items": {
                "description": "String item",
                "type": "string"
            }
        }
        type_prop = TypeProperty("test_array", property_data)
        result = type_prop.get_json_schema()
        
        expected = {
            "description": "Array of strings",
            "type": "array",
            "items": {
                "description": "String item"
            }
        }
        self.assertEqual(result, expected)

    @patch('configurator.services.type_services.Type')
    def test_get_json_schema_with_object(self, mock_type_class):
        """Test get_json_schema method for object type"""
        property_data = {
            "description": "Object with properties",
            "type": "object",
            "properties": {
                "name": {
                    "description": "Name property",
                    "type": "string"
                }
            }
        }
        type_prop = TypeProperty("test_object", property_data)
        result = type_prop.get_json_schema()
        
        expected = {
            "description": "Object with properties",
            "type": "object",
            "properties": {
                "name": {
                    "description": "Name property"
                }
            }
        }
        self.assertEqual(result, expected)

    @patch('configurator.services.type_services.Type')
    def test_get_json_schema_with_type_reference(self, mock_type_class):
        """Test get_json_schema method with type reference"""
        mock_type = MagicMock()
        mock_type.get_json_schema.return_value = {"type": "string", "format": "email"}
        mock_type_class.return_value = mock_type
        
        property_data = {
            "description": "Email type",
            "type": "email"
        }
        type_prop = TypeProperty("test_email", property_data)
        result = type_prop.get_json_schema()
        
        mock_type_class.assert_called_once_with("email.yaml")
        self.assertEqual(result["description"], "Email type")

    def test_get_json_schema_with_primitive_universal(self):
        """Test get_json_schema method for primitive universal"""
        property_data = {
            "description": "Test description",
            "schema": {"type": "string", "format": "email"}
        }
        type_prop = TypeProperty("test_prop", property_data)
        result = type_prop.get_json_schema()
        
        expected = {
            "description": "Test description",
            "type": "string",
            "format": "email"
        }
        self.assertEqual(result, expected)

    def test_get_json_schema_with_primitive_non_universal(self):
        """Test get_json_schema method for primitive non-universal"""
        property_data = {
            "description": "Test description",
            "schema": {
                "json_type": {"type": "string", "maxLength": 100},
                "bson_type": {"bsonType": "string"}
            }
        }
        type_prop = TypeProperty("test_prop", property_data)
        result = type_prop.get_json_schema()
        
        expected = {
            "description": "Test description",
            "type": "string",
            "maxLength": 100
        }
        self.assertEqual(result, expected)

    @patch('configurator.services.type_services.Type')
    def test_get_bson_schema_with_array(self, mock_type_class):
        """Test get_bson_schema method for array type"""
        property_data = {
            "description": "Array of strings",
            "type": "array",
            "items": {
                "description": "String item",
                "type": "string"
            }
        }
        type_prop = TypeProperty("test_array", property_data)
        result = type_prop.get_bson_schema()
        
        expected = {
            "description": "Array of strings",
            "bsonType": "array",
            "items": {
                "description": "String item"
            }
        }
        self.assertEqual(result, expected)

    @patch('configurator.services.type_services.Type')
    def test_get_bson_schema_with_object(self, mock_type_class):
        """Test get_bson_schema method for object type"""
        property_data = {
            "description": "Object with properties",
            "type": "object",
            "properties": {
                "name": {
                    "description": "Name property",
                    "type": "string"
                }
            }
        }
        type_prop = TypeProperty("test_object", property_data)
        result = type_prop.get_bson_schema()
        
        expected = {
            "description": "Object with properties",
            "bsonType": "object",
            "properties": {
                "name": {
                    "description": "Name property"
                }
            }
        }
        self.assertEqual(result, expected)

    @patch('configurator.services.type_services.Type')
    def test_get_bson_schema_with_type_reference(self, mock_type_class):
        """Test get_bson_schema method with type reference"""
        mock_type = MagicMock()
        mock_type.get_bson_schema.return_value = {"bsonType": "string"}
        mock_type_class.return_value = mock_type
        
        property_data = {
            "description": "Email type",
            "type": "email"
        }
        type_prop = TypeProperty("test_email", property_data)
        result = type_prop.get_bson_schema()
        
        mock_type_class.assert_called_once_with("email.yaml")
        self.assertEqual(result["description"], "Email type")

    def test_get_bson_schema_with_primitive_universal(self):
        """Test get_bson_schema method for primitive universal"""
        property_data = {
            "description": "Test description",
            "schema": {"type": "string", "format": "email"}
        }
        type_prop = TypeProperty("test_prop", property_data)
        result = type_prop.get_bson_schema()
        
        expected = {
            "description": "Test description",
            "bsonType": "string",
            "format": "email"
        }
        self.assertEqual(result, expected)

    def test_get_bson_schema_with_primitive_non_universal(self):
        """Test get_bson_schema method for primitive non-universal"""
        property_data = {
            "description": "Test description",
            "schema": {
                "json_type": {"type": "string"},
                "bson_type": {"bsonType": "string", "maxLength": 100}
            }
        }
        type_prop = TypeProperty("test_prop", property_data)
        result = type_prop.get_bson_schema()
        
        expected = {
            "description": "Test description",
            "bsonType": "string",
            "maxLength": 100
        }
        self.assertEqual(result, expected)


class TestType(unittest.TestCase):
    """Test cases for Type class"""

    @patch('configurator.services.type_services.FileIO')
    @patch('configurator.services.type_services.Config')
    def test_init_with_file_name(self, mock_config_class, mock_file_io):
        """Test Type initialization with file name"""
        mock_config = MagicMock()
        mock_config.TYPES_FOLDER = "/test/types"
        mock_config_class.return_value = mock_config
        
        mock_file_io.get_document.return_value = {
            "description": "Test type",
            "type": "string"
        }
        
        type_obj = Type("test.yaml")
        
        self.assertEqual(type_obj.file_name, "test.yaml")
        self.assertEqual(type_obj.name, "test")
        mock_file_io.get_document.assert_called_once_with("/test/types", "test.yaml")

    @patch('configurator.services.type_services.Config')
    def test_init_with_document(self, mock_config_class):
        """Test Type initialization with document"""
        # Mock Config to avoid singleton issues
        mock_config_class.side_effect = Exception("This class is a singleton!")
        
        document = {
            "description": "Test type",
            "type": "string"
        }
        
        type_obj = Type("test.yaml", document)
        
        self.assertEqual(type_obj.file_name, "test.yaml")
        self.assertEqual(type_obj.name, "test")
        self.assertEqual(type_obj.property.description, "Test type")

    @patch('configurator.services.type_services.Config')
    def test_to_dict(self, mock_config_class):
        """Test to_dict method"""
        # Mock Config to avoid singleton issues
        mock_config_class.side_effect = Exception("This class is a singleton!")
        
        document = {
            "description": "Test type",
            "type": "string"
        }
        
        type_obj = Type("test.yaml", document)
        result = type_obj.to_dict()
        
        expected = {
            "description": "Test type",
            "type": "string"
        }
        self.assertEqual(result, expected)

    def test_get_json_schema(self):
        """Test get_json_schema method"""
        document = {
            "description": "Test type",
            "type": "string",
            "schema": {"type": "string"}
        }
        
        type_obj = Type("test.yaml", document)
        result = type_obj.get_json_schema()
        
        expected = {
            "description": "Test type",
            "type": "string"
        }
        self.assertEqual(result, expected)

    def test_get_bson_schema(self):
        """Test get_bson_schema method"""
        document = {
            "description": "Test type",
            "type": "string",
            "schema": {"type": "string"}
        }
        
        type_obj = Type("test.yaml", document)
        result = type_obj.get_bson_schema()
        
        expected = {
            "description": "Test type",
            "bsonType": "string"
        }
        self.assertEqual(result, expected)


class TestTypePropertyCanonical(unittest.TestCase):
    def test_object_type(self):
        property_data = {
            "description": "Object type",
            "type": "object",
            "properties": {
                "foo": {
                    "description": "Foo property",
                    "type": "string"
                },
                "bar": {
                    "description": "Bar property",
                    "type": "number"
                }
            },
            "required": True,
            "additionalProperties": False
        }
        prop = TypeProperty("obj", property_data)
        # to_dict
        d = prop.to_dict()
        self.assertEqual(d["description"], "Object type")
        self.assertEqual(d["type"], "object")
        self.assertIn("foo", d["properties"])
        self.assertIn("bar", d["properties"])
        # get_json_schema
        js = prop.get_json_schema()
        self.assertEqual(js["type"], "object")
        self.assertIn("foo", js["properties"])
        # get_bson_schema
        bs = prop.get_bson_schema()
        self.assertEqual(bs["bsonType"], "object")
        self.assertIn("foo", bs["properties"])

    def test_array_type(self):
        property_data = {
            "description": "Array type",
            "type": "array",
            "items": {
                "description": "Item property",
                "type": "string"
            },
            "required": False
        }
        prop = TypeProperty("arr", property_data)
        # to_dict
        d = prop.to_dict()
        self.assertEqual(d["description"], "Array type")
        self.assertEqual(d["type"], "array")
        self.assertIn("items", d)
        # get_json_schema
        js = prop.get_json_schema()
        self.assertEqual(js["type"], "array")
        self.assertIn("items", js)
        # get_bson_schema
        bs = prop.get_bson_schema()
        self.assertEqual(bs["bsonType"], "array")
        self.assertIn("items", bs)

    def test_primitive_with_schema(self):
        property_data = {
            "description": "Primitive with schema",
            "schema": {"type": "string", "format": "email"}
        }
        prop = TypeProperty("prim_schema", property_data)
        # to_dict
        d = prop.to_dict()
        self.assertEqual(d["description"], "Primitive with schema")
        self.assertIn("schema", d)
        # get_json_schema
        js = prop.get_json_schema()
        self.assertEqual(js["type"], "string")
        self.assertEqual(js["format"], "email")
        # get_bson_schema
        bs = prop.get_bson_schema()
        self.assertEqual(bs["bsonType"], "string")
        self.assertEqual(bs["format"], "email")

    def test_primitive_with_json_bson_type(self):
        property_data = {
            "description": "Primitive with json_type and bson_type",
            "schema": {
                "json_type": {"type": "string", "maxLength": 10},
                "bson_type": {"bsonType": "string", "maxLength": 10}
            }
        }
        prop = TypeProperty("prim_jb", property_data)
        # to_dict
        d = prop.to_dict()
        self.assertEqual(d["description"], "Primitive with json_type and bson_type")
        self.assertIn("json_type", d)
        self.assertIn("bson_type", d)
        # get_json_schema
        js = prop.get_json_schema()
        self.assertEqual(js["type"], "string")
        self.assertEqual(js["maxLength"], 10)
        # get_bson_schema
        bs = prop.get_bson_schema()
        self.assertEqual(bs["bsonType"], "string")
        self.assertEqual(bs["maxLength"], 10)


class TestTypeCanonical(unittest.TestCase):
    def test_type_object(self):
        document = {
            "description": "Object type",
            "type": "object",
            "properties": {
                "foo": {"description": "Foo property", "type": "string"}
            },
            "required": True,
            "additionalProperties": False
        }
        t = Type("obj.yaml", document)
        d = t.to_dict()
        self.assertEqual(d["type"], "object")
        self.assertIn("foo", d["properties"])
        js = t.get_json_schema()
        self.assertEqual(js["type"], "object")
        bs = t.get_bson_schema()
        self.assertEqual(bs["bsonType"], "object")

    def test_type_array(self):
        document = {
            "description": "Array type",
            "type": "array",
            "items": {"description": "Item property", "type": "string"},
            "required": False
        }
        t = Type("arr.yaml", document)
        d = t.to_dict()
        self.assertEqual(d["type"], "array")
        js = t.get_json_schema()
        self.assertEqual(js["type"], "array")
        bs = t.get_bson_schema()
        self.assertEqual(bs["bsonType"], "array")

    def test_type_primitive_schema(self):
        document = {
            "description": "Primitive with schema",
            "schema": {"type": "string", "format": "email"}
        }
        t = Type("prim_schema.yaml", document)
        d = t.to_dict()
        self.assertIn("schema", d)
        js = t.get_json_schema()
        self.assertEqual(js["type"], "string")
        self.assertEqual(js["format"], "email")
        bs = t.get_bson_schema()
        self.assertEqual(bs["bsonType"], "string")
        self.assertEqual(bs["format"], "email")

    def test_type_primitive_json_bson(self):
        document = {
            "description": "Primitive with json_type and bson_type",
            "schema": {
                "json_type": {"type": "string", "maxLength": 10},
                "bson_type": {"bsonType": "string", "maxLength": 10}
            }
        }
        t = Type("prim_jb.yaml", document)
        d = t.to_dict()
        self.assertIn("json_type", d)
        self.assertIn("bson_type", d)
        js = t.get_json_schema()
        self.assertEqual(js["type"], "string")
        self.assertEqual(js["maxLength"], 10)
        bs = t.get_bson_schema()
        self.assertEqual(bs["bsonType"], "string")
        self.assertEqual(bs["maxLength"], 10)


if __name__ == '__main__':
    unittest.main() 