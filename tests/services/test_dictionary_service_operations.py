import unittest
from unittest.mock import patch, MagicMock
from configurator.services.dictionary_services import Dictionary, Property
import os
import yaml
import json
from configurator.services.enumerator_service import Enumerators


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


class TestProperty(unittest.TestCase):
    """Test cases for Property class - non-rendering operations"""

    def test_init_with_basic_property(self):
        """Test Property initialization with basic property"""
        property_data = {
            "description": "Test description",
            "type": "string",
            "required": True
        }
        prop = Property("test_prop", property_data)
        
        self.assertEqual(prop.name, "test_prop")
        self.assertEqual(prop.description, "Test description")
        self.assertEqual(prop.type, "string")
        self.assertTrue(prop.required)
        self.assertFalse(prop.additional_properties)
        self.assertIsNone(prop.ref)
        self.assertIsNone(prop.enums)

    def test_init_with_ref(self):
        """Test Property initialization with ref"""
        property_data = {
            "ref": "sample.1.0.0.yaml",
            "description": "Reference to another dictionary"
        }
        prop = Property("test_ref", property_data)
        
        self.assertEqual(prop.ref, "sample.1.0.0.yaml")
        self.assertEqual(prop.description, "Reference to another dictionary")
        self.assertIsNone(prop.type)
        self.assertFalse(prop.required)

    def test_init_with_enum(self):
        """Test Property initialization with enum type"""
        property_data = {
            "description": "Status enum",
            "type": "enum",
            "enums": "default_status",
            "required": True
        }
        prop = Property("test_enum", property_data)
        
        self.assertEqual(prop.type, "enum")
        self.assertEqual(prop.enums, "default_status")
        self.assertTrue(prop.required)

    def test_init_with_enum_array(self):
        """Test Property initialization with enum_array type"""
        property_data = {
            "description": "Array of status enums",
            "type": "enum_array",
            "enums": "default_status"
        }
        prop = Property("test_enum_array", property_data)
        
        self.assertEqual(prop.type, "enum_array")
        self.assertEqual(prop.enums, "default_status")

    def test_init_with_array_type(self):
        """Test Property initialization with array type"""
        property_data = {
            "description": "Array of strings",
            "type": "array",
            "items": {
                "description": "String item",
                "type": "string"
            }
        }
        prop = Property("test_array", property_data)
        
        self.assertEqual(prop.type, "array")
        self.assertIsInstance(prop.items, Property)
        self.assertEqual(prop.items.description, "String item")

    def test_init_with_object_type(self):
        """Test Property initialization with object type"""
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
        prop = Property("test_object", property_data)
        
        self.assertEqual(prop.type, "object")
        self.assertTrue(prop.additional_properties)
        self.assertIn("name", prop.properties)
        self.assertIn("age", prop.properties)
        self.assertEqual(prop.properties["name"].description, "Name property")

    def test_init_with_missing_values(self):
        """Test Property initialization with missing values"""
        property_data = {}
        prop = Property("test_prop", property_data)
        
        self.assertEqual(prop.description, "Missing Required Description")
        self.assertIsNone(prop.ref)
        self.assertIsNone(prop.type)
        self.assertIsNone(prop.enums)
        self.assertFalse(prop.required)
        self.assertFalse(prop.additional_properties)
        self.assertEqual(prop.properties, {})
        self.assertIsNone(prop.items)

    def test_to_dict_with_ref(self):
        """Test to_dict method for ref property"""
        property_data = {
            "ref": "sample.1.0.0.yaml"
        }
        prop = Property("test_ref", property_data)
        result = prop.to_dict()
        
        expected = {"ref": "sample.1.0.0.yaml"}
        self.assertEqual(result, expected)

    def test_to_dict_basic(self):
        """Test to_dict method for basic property"""
        property_data = {
            "description": "Test description",
            "type": "string",
            "required": True
        }
        prop = Property("test_prop", property_data)
        result = prop.to_dict()
        
        expected = {
            "description": "Test description",
            "type": "string",
            "required": True
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
        prop = Property("test_array", property_data)
        result = prop.to_dict()
        
        self.assertEqual(result["description"], "Array of strings")
        self.assertEqual(result["type"], "array")
        self.assertTrue(result["required"])
        self.assertIn("items", result)

    def test_to_dict_with_object(self):
        """Test to_dict method for object property"""
        property_data = {
            "description": "Object with properties",
            "type": "object",
            "properties": {
                "name": {"description": "Name property", "type": "string"}
            },
            "additionalProperties": True
        }
        prop = Property("test_object", property_data)
        result = prop.to_dict()
        self.assertEqual(result["type"], "object")
        self.assertIn("properties", result)
        self.assertIn("name", result["properties"])
        self.assertEqual(result["properties"]["name"]["type"], "string")
        self.assertIn("required", result)
        self.assertFalse(result["required"])  # required should be present and False

    def test_to_dict_with_enum(self):
        """Test to_dict method for enum property"""
        property_data = {
            "description": "Status enum",
            "type": "enum",
            "enums": "default_status",
            "required": True
        }
        prop = Property("test_enum", property_data)
        result = prop.to_dict()
        
        self.assertEqual(result["description"], "Status enum")
        self.assertEqual(result["type"], "enum")
        self.assertEqual(result["enums"], "default_status")
        self.assertTrue(result["required"])

    def test_to_dict_with_enum_array(self):
        """Test to_dict method for enum_array property"""
        property_data = {
            "description": "Array of status enums",
            "type": "enum_array",
            "enums": "default_status"
        }
        prop = Property("test_enum_array", property_data)
        result = prop.to_dict()
        
        self.assertEqual(result["description"], "Array of status enums")
        self.assertEqual(result["type"], "enum_array")
        self.assertEqual(result["enums"], "default_status")

    def test_get_required(self):
        """Test _get_required method"""
        property_data = {
            "description": "Object with required properties",
            "type": "object",
            "properties": {
                "id": {
                    "description": "Required ID",
                    "type": "string",
                    "required": True
                },
                "name": {
                    "description": "Optional name",
                    "type": "string",
                    "required": False
                },
                "status": {
                    "description": "Required status",
                    "type": "enum",
                    "enums": "default_status",
                    "required": True
                }
            }
        }
        prop = Property("test_object", property_data)
        required = prop._get_required()
        
        self.assertIn("id", required)
        self.assertIn("status", required)
        self.assertNotIn("name", required)
        self.assertEqual(len(required), 2)


class TestDictionary(unittest.TestCase):
    """Test cases for Dictionary class - non-rendering operations"""

    @patch('configurator.services.dictionary_services.FileIO')
    def test_init_with_file_name(self, mock_file_io):
        """Test Dictionary initialization with file name"""
        mock_file_io.get_document.return_value = {
            "description": "Test dictionary",
            "type": "object",
            "properties": {
                "name": {
                    "description": "Name property",
                    "type": "string"
                }
            }
        }
        
        dictionary = Dictionary("test.yaml")
        
        self.assertEqual(dictionary.name, "test")
        self.assertIsInstance(dictionary.property, Property)
        self.assertEqual(dictionary.property.description, "Test dictionary")

    def test_init_with_document(self):
        """Test Dictionary initialization with document"""
        doc = {
            "description": "Test dictionary",
            "type": "object",
            "properties": {
                "name": {
                    "description": "Name property",
                    "type": "string"
                }
            }
        }
        dictionary = Dictionary("test.yaml", doc)
        
        self.assertEqual(dictionary.name, "test")
        self.assertIsInstance(dictionary.property, Property)
        self.assertEqual(dictionary.property.description, "Test dictionary")

    def test_to_dict(self):
        """Test Dictionary to_dict method"""
        doc = {
            "description": "Test dictionary",
            "type": "object",
            "properties": {
                "name": {
                    "description": "Name property",
                    "type": "string"
                }
            }
        }
        dictionary = Dictionary("test.yaml", doc)
        result = dictionary.to_dict()
        
        self.assertEqual(result["description"], "Test dictionary")
        self.assertEqual(result["type"], "object")
        self.assertIn("properties", result)


class TestPropertyCanonical(unittest.TestCase):
    """Test cases for Property class using canonical test data"""

    def setUp(self):
        self.config = set_config_input_folder("tests/test_cases/small_sample")

    def tearDown(self):
        clear_config()

    def test_object_type(self):
        """Test Property with object type from test data"""
        property_data = {
            "description": "A simple collection for testing",
            "type": "object",
            "properties": {
                "_id": {
                    "description": "The unique identifier for the media",
                    "type": "identifier",
                    "required": True
                },
                "name": {
                    "description": "The name of the document",
                    "type": "word"
                },
                "status": {
                    "description": "The current status of the document",
                    "type": "enum",
                    "enums": "default_status",
                    "required": True
                }
            }
        }
        
        prop = Property("root", property_data)
        
        self.assertEqual(prop.description, "A simple collection for testing")
        self.assertEqual(prop.type, "object")
        self.assertIn("_id", prop.properties)
        self.assertIn("name", prop.properties)
        self.assertIn("status", prop.properties)
        
        # Check nested properties
        id_prop = prop.properties["_id"]
        self.assertEqual(id_prop.description, "The unique identifier for the media")
        self.assertEqual(id_prop.type, "identifier")
        self.assertTrue(id_prop.required)
        
        status_prop = prop.properties["status"]
        self.assertEqual(status_prop.type, "enum")
        self.assertEqual(status_prop.enums, "default_status")
        self.assertTrue(status_prop.required)

    def test_array_type(self):
        """Test Property with array type"""
        property_data = {
            "description": "Array of items",
            "type": "array",
            "items": {
                "description": "Item in array",
                "type": "string"
            }
        }
        
        prop = Property("root", property_data)
        
        self.assertEqual(prop.type, "array")
        self.assertIsInstance(prop.items, Property)
        self.assertEqual(prop.items.description, "Item in array")
        self.assertEqual(prop.items.type, "string")

    def test_enum_type(self):
        """Test Property with enum type"""
        property_data = {
            "description": "Status enum",
            "type": "enum",
            "enums": "default_status",
            "required": True
        }
        
        prop = Property("root", property_data)
        
        self.assertEqual(prop.type, "enum")
        self.assertEqual(prop.enums, "default_status")
        self.assertTrue(prop.required)

    def test_enum_array_type(self):
        """Test Property with enum_array type"""
        property_data = {
            "description": "Array of status enums",
            "type": "enum_array",
            "enums": "default_status"
        }
        
        prop = Property("root", property_data)
        
        self.assertEqual(prop.type, "enum_array")
        self.assertEqual(prop.enums, "default_status")

    def test_ref_type(self):
        """Test Property with ref type"""
        property_data = {
            "ref": "sample.1.0.0.yaml",
            "description": "Reference to sample dictionary"
        }
        
        prop = Property("root", property_data)
        
        self.assertEqual(prop.ref, "sample.1.0.0.yaml")
        self.assertEqual(prop.description, "Reference to sample dictionary")


class TestDictionaryCanonical(unittest.TestCase):
    """Test cases for Dictionary class using canonical test data"""

    def setUp(self):
        self.config = set_config_input_folder("tests/test_cases/small_sample")

    def tearDown(self):
        clear_config()

    def test_dictionary_object(self):
        """Test Dictionary with object type from test data"""
        doc = load_yaml("tests/test_cases/small_sample/dictionaries/sample.1.0.0.yaml")
        
        dictionary = Dictionary("sample.1.0.0.yaml", doc)
        
        self.assertEqual(dictionary.name, "sample.1.0.0")
        self.assertEqual(dictionary.property.description, "A simple collection for testing")
        self.assertEqual(dictionary.property.type, "object")
        
        # Test to_dict
        result = dictionary.to_dict()
        self.assertEqual(result["description"], "A simple collection for testing")
        self.assertEqual(result["type"], "object")
        self.assertIn("properties", result)
        self.assertIn("_id", result["properties"])
        self.assertIn("name", result["properties"])
        self.assertIn("status", result["properties"])

    def test_dictionary_ref(self):
        """Test Dictionary with ref type"""
        doc = {
            "ref": "sample.1.0.0.yaml",
            "description": "Reference to sample dictionary"
        }
        
        dictionary = Dictionary("ref.yaml", doc)
        
        self.assertEqual(dictionary.property.ref, "sample.1.0.0.yaml")
        self.assertEqual(dictionary.property.description, "Reference to sample dictionary")
        
        # Test to_dict
        result = dictionary.to_dict()
        self.assertEqual(result, {"name": "ref", "_locked": False, "ref": "sample.1.0.0.yaml"})

if __name__ == '__main__':
    unittest.main() 