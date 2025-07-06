import unittest
from unittest.mock import patch, MagicMock
from configurator.services.type_services import Type, TypeProperty
import os
import yaml
import json


def load_yaml(path):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)

def set_config_input_folder(folder):
    os.environ['INPUT_FOLDER'] = folder
    from configurator.utils.config import Config
    Config._instance = None
    return Config.get_instance()

def clear_config():
    if 'INPUT_FOLDER' in os.environ:
        del os.environ['INPUT_FOLDER']
    from configurator.utils.config import Config
    Config._instance = None


class TestTypeProperty(unittest.TestCase):
    """Test cases for TypeProperty class - non-rendering operations"""

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
        result = type_prop.to_dict()
        self.assertEqual(result["description"], "Test description")
        self.assertEqual(result["json_type"], {"type": "string"})
        self.assertEqual(result["bson_type"], {"bsonType": "string"})
        self.assertNotIn("schema", result)

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
            "type": "string",
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


class TestType(unittest.TestCase):
    """Test cases for Type class - non-rendering operations"""

    @patch('configurator.services.type_services.FileIO')
    @patch('configurator.services.type_services.Config')
    def test_init_with_file_name(self, mock_config_class, mock_file_io):
        """Test Type initialization with file name"""
        mock_config = MagicMock()
        mock_config_class.get_instance.return_value = mock_config
        mock_config.TYPE_FOLDER = "/test/types"
        
        mock_file_io.get_document.return_value = {
            "title": "Test Type",
            "description": "Test type description",
            "type": "object",
            "properties": {
                "name": {"type": "string"}
            }
        }
        
        type_instance = Type("test_type.yaml")
        
        self.assertEqual(type_instance.name, "test_type")
        self.assertEqual(type_instance.property.description, "Test type description")
        mock_file_io.get_document.assert_called_once_with("/test/types", "test_type.yaml")

    @patch('configurator.services.type_services.Config')
    def test_init_with_document(self, mock_config_class):
        """Test Type initialization with document"""
        mock_config = MagicMock()
        mock_config_class.get_instance.return_value = mock_config
        
        document = {
            "title": "Test Type",
            "description": "Test type description",
            "type": "object",
            "properties": {
                "name": {"type": "string"}
            }
        }
        
        type_instance = Type("test_type", document)
        
        self.assertEqual(type_instance.name, "test_type")
        self.assertEqual(type_instance.property.description, "Test type description")
        self.assertIn("name", type_instance.property.properties)

    @patch('configurator.services.type_services.Config')
    def test_to_dict(self, mock_config_class):
        """Test to_dict method"""
        mock_config = MagicMock()
        mock_config_class.get_instance.return_value = mock_config
        
        document = {
            "title": "Test Type",
            "description": "Test type description",
            "type": "object",
            "properties": {
                "name": {"type": "string"}
            }
        }
        
        type_instance = Type("test_type", document)
        result = type_instance.property.to_dict()
        
        self.assertEqual(result["description"], "Test type description")
        self.assertEqual(result["type"], "object")
        self.assertIn("properties", result)
        self.assertIn("name", result["properties"])


class TestTypePropertyCanonical(unittest.TestCase):
    """Test canonical scenarios for TypeProperty - non-rendering operations"""

    def test_object_type(self):
        """Test object type property initialization and to_dict"""
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
        
        # Test initialization
        self.assertEqual(type_prop.type, "object")
        self.assertTrue(type_prop.additional_properties)
        self.assertIn("name", type_prop.properties)
        self.assertIn("age", type_prop.properties)
        
        # Test to_dict
        result = type_prop.to_dict()
        self.assertEqual(result["description"], "Object with properties")
        self.assertEqual(result["type"], "object")
        self.assertTrue(result["additionalProperties"])
        self.assertIn("properties", result)

    def test_array_type(self):
        """Test array type property initialization and to_dict"""
        property_data = {
            "description": "Array of strings",
            "type": "array",
            "items": {
                "description": "String item",
                "type": "string"
            }
        }
        type_prop = TypeProperty("test_array", property_data)
        
        # Test initialization
        self.assertEqual(type_prop.type, "array")
        self.assertIsInstance(type_prop.items, TypeProperty)
        self.assertEqual(type_prop.items.description, "String item")
        
        # Test to_dict
        result = type_prop.to_dict()
        self.assertEqual(result["description"], "Array of strings")
        self.assertEqual(result["type"], "array")
        self.assertIn("items", result)

    def test_primitive_with_schema(self):
        """Test primitive property with schema initialization and to_dict"""
        property_data = {
            "description": "Test description",
            "schema": {
                "json_type": {"type": "string"},
                "bson_type": {"bsonType": "string"}
            }
        }
        type_prop = TypeProperty("test_prop", property_data)
        
        # Test initialization
        self.assertEqual(type_prop.schema, property_data["schema"])
        self.assertEqual(type_prop.json_type, {"type": "string"})
        self.assertEqual(type_prop.bson_type, {"bsonType": "string"})
        self.assertTrue(type_prop.is_primitive)
        self.assertFalse(type_prop.is_universal)
        
        # Test to_dict
        result = type_prop.to_dict()
        self.assertEqual(result["description"], "Test description")
        self.assertEqual(result["json_type"], {"type": "string"})
        self.assertEqual(result["bson_type"], {"bsonType": "string"})
        self.assertNotIn("schema", result)

    def test_primitive_with_json_bson_type(self):
        """Test primitive property with json_type/bson_type initialization and to_dict"""
        property_data = {
            "description": "Test description",
            "json_type": {"type": "string"},
            "bson_type": {"bsonType": "string"}
        }
        type_prop = TypeProperty("test_prop", property_data)
        # Test initialization
        self.assertEqual(type_prop.json_type, {"type": "string"})
        self.assertEqual(type_prop.bson_type, {"bsonType": "string"})
        self.assertTrue(type_prop.is_primitive)
        self.assertFalse(type_prop.is_universal)
        # Test to_dict
        result = type_prop.to_dict()
        self.assertEqual(result["description"], "Test description")
        self.assertEqual(result["json_type"], {"type": "string"})
        self.assertEqual(result["bson_type"], {"bsonType": "string"})
        self.assertNotIn("schema", result)


class TestTypeCanonical(unittest.TestCase):
    """Test canonical scenarios for Type - non-rendering operations"""

    def setUp(self):
        self.config = set_config_input_folder("tests/test_cases/small_sample")

    def tearDown(self):
        clear_config()

    def test_type_object(self):
        """Test object type initialization and to_dict"""
        type_data = {
            "title": "Test Object Type",
            "description": "Test object type description",
            "type": "object",
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
        type_instance = Type("test_object", type_data)
        
        # Test initialization
        self.assertEqual(type_instance.name, "test_object")
        self.assertEqual(type_instance.property.description, "Test object type description")
        self.assertEqual(type_instance.property.type, "object")
        self.assertIn("name", type_instance.property.properties)
        self.assertIn("age", type_instance.property.properties)
        
        # Test to_dict
        result = type_instance.property.to_dict()
        self.assertEqual(result["description"], "Test object type description")
        self.assertEqual(result["type"], "object")
        self.assertIn("properties", result)
        self.assertIn("name", result["properties"])
        self.assertIn("age", result["properties"])

    def test_type_array(self):
        """Test array type initialization and to_dict"""
        type_data = {
            "title": "Test Array Type",
            "description": "Test array type description",
            "type": "array",
            "items": {
                "description": "Array of strings",
                "type": "string"
            }
        }
        type_instance = Type("test_array", type_data)
        
        # Test initialization
        self.assertEqual(type_instance.name, "test_array")
        self.assertEqual(type_instance.property.description, "Test array type description")
        self.assertEqual(type_instance.property.type, "array")
        self.assertIsInstance(type_instance.property.items, TypeProperty)
        
        # Test to_dict
        result = type_instance.property.to_dict()
        self.assertEqual(result["description"], "Test array type description")
        self.assertEqual(result["type"], "array")
        self.assertIn("items", result)

    def test_type_primitive_schema(self):
        """Test primitive type with schema initialization and to_dict"""
        type_data = {
            "title": "Test Primitive Type",
            "description": "Test primitive type description",
            "schema": {
                "json_type": {"type": "string"},
                "bson_type": {"bsonType": "string"}
            }
        }
        type_instance = Type("test_primitive", type_data)
        
        # Test initialization
        self.assertEqual(type_instance.name, "test_primitive")
        self.assertEqual(type_instance.property.description, "Test primitive type description")
        self.assertIsNotNone(type_instance.property.schema)
        
        # Test to_dict
        result = type_instance.property.to_dict()
        self.assertEqual(result["description"], "Test primitive type description")
        self.assertEqual(result["json_type"], {"type": "string"})
        self.assertEqual(result["bson_type"], {"bsonType": "string"})
        self.assertNotIn("schema", result)

    def test_type_primitive_json_bson(self):
        """Test primitive type with json_type/bson_type initialization and to_dict"""
        type_data = {
            "title": "Test Primitive Type",
            "description": "Test primitive type description",
            "json_type": {"type": "string"},
            "bson_type": {"bsonType": "string"}
        }
        type_instance = Type("test_primitive", type_data)
        # Test initialization
        self.assertEqual(type_instance.name, "test_primitive")
        self.assertEqual(type_instance.property.description, "Test primitive type description")
        self.assertEqual(type_instance.property.json_type, {"type": "string"})
        self.assertEqual(type_instance.property.bson_type, {"bsonType": "string"})
        self.assertTrue(type_instance.property.is_primitive)
        # Test to_dict
        result = type_instance.property.to_dict()
        self.assertEqual(result["description"], "Test primitive type description")
        self.assertEqual(result["json_type"], {"type": "string"})
        self.assertEqual(result["bson_type"], {"bsonType": "string"})
        self.assertNotIn("schema", result)


if __name__ == '__main__':
    unittest.main() 