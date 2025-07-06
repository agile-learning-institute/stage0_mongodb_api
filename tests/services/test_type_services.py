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
    """
    Canonical tests for Type/TypeProperty using types from tests/test_cases/small_sample/types.
    Folder names match config: types/, dictionaries/, configurations/, test_data/
    """
    def setUp(self):
        self.input_folder = 'tests/test_cases/small_sample'
        set_config_input_folder(self.input_folder)

    def tearDown(self):
        clear_config()

    def test_type_object(self):
        """Object type with id (identity) and name (word) properties."""
        document = {
            "description": "Object type",
            "type": "object",
            "properties": {
                "id": {"description": "ID property", "type": "identity"},
                "name": {"description": "Name property", "type": "word"}
            },
            "required": True,
            "additionalProperties": False
        }
        t = Type("obj.yaml", document)
        d = t.to_dict()
        self.assertEqual(d["type"], "object")
        self.assertIn("id", d["properties"])
        self.assertIn("name", d["properties"])
        
        # Test JSON schema rendering
        js = t.get_json_schema()
        self.assertEqual(js["type"], "object")
        self.assertIn("id", js["properties"])
        self.assertIn("name", js["properties"])

        # Verify identity type resolves to string with pattern (from json_type)
        self.assertEqual(js["properties"]["id"]["type"], "string")
        self.assertEqual(js["properties"]["id"]["pattern"], "^[0-9a-fA-F]{24}$")
        # Verify word type resolves to string with pattern
        self.assertEqual(js["properties"]["name"]["type"], "string")
        self.assertEqual(js["properties"]["name"]["pattern"], "^[^\\s]{4,40}$")
        
        # Test BSON schema rendering
        bs = t.get_bson_schema()
        self.assertEqual(bs["bsonType"], "object")
        self.assertIn("id", bs["properties"])
        self.assertIn("name", bs["properties"])
        # Verify identity type resolves to objectId
        self.assertEqual(bs["properties"]["id"]["bsonType"], "objectId")
        # Verify word type resolves to string with pattern
        self.assertEqual(bs["properties"]["name"]["bsonType"], "string")
        self.assertEqual(bs["properties"]["name"]["pattern"], "^[^\\s]{4,40}$")

    def test_type_array(self):
        """Array type of word (uses word.yaml from small_sample/types)."""
        document = {
            "description": "Array type",
            "type": "array",
            "items": {"description": "Item property", "type": "word"},
            "required": False
        }
        t = Type("arr.yaml", document)
        d = t.to_dict()
        self.assertEqual(d["type"], "array")
        
        # Test JSON schema rendering
        js = t.get_json_schema()
        self.assertEqual(js["type"], "array")
        self.assertIn("items", js)
        # Verify word type resolves to string with pattern
        self.assertEqual(js["items"]["type"], "string")
        self.assertEqual(js["items"]["pattern"], "^[^\\s]{4,40}$")
        
        # Test BSON schema rendering
        bs = t.get_bson_schema()
        self.assertEqual(bs["bsonType"], "array")
        self.assertIn("items", bs)
        # Verify word type resolves to string with pattern
        self.assertEqual(bs["items"]["bsonType"], "string")
        self.assertEqual(bs["items"]["pattern"], "^[^\\s]{4,40}$")

    def test_type_primitive_schema(self):
        """Primitive with schema (direct schema dict)."""
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
        """Primitive with json_type and bson_type (direct schema dict)."""
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


class TestTypeRenderingVerified(unittest.TestCase):
    """
    Compare rendered output to verified files for small_sample.
    Flexible for other test_case input folders.
    """
    def setUp(self):
        self.input_folder = 'tests/test_cases/small_sample'
        set_config_input_folder(self.input_folder)

    def tearDown(self):
        clear_config()

    def test_object_type_json_schema(self):
        """Compare rendered JSON schema to verified output for small_sample/simple.1.0.0.1.yaml"""
        # Arrange: use dictionary and types from small_sample
        document = {
            "title": "Simple",
            "description": "A simple collection for testing",
            "type": "object",
            "properties": {
                "_id": {"description": "The unique identifier for the media", "type": "identity", "required": True},
                "name": {"description": "The name of the document", "type": "word"},
                "status": {"description": "The current status of the document", "type": "string", "enum": ["active", "archived"], "required": True}
            },
            "additionalProperties": False,
            "required": ["_id", "status"]
        }
        t = Type("simple.1.0.0.1.yaml", document)
        rendered = t.get_json_schema()
        expected = load_yaml(os.path.join(self.input_folder, "verified_output/json_schema/simple.1.0.0.1.yaml"))
        self.assertEqual(rendered, expected)

    def test_object_type_bson_schema(self):
        """Compare rendered BSON schema to verified output for small_sample/simple.1.0.0.1.json"""
        document = {
            "title": "Simple",
            "description": "A simple collection for testing",
            "type": "object",
            "properties": {
                "_id": {"description": "The unique identifier for the media", "type": "identity", "required": True},
                "name": {"description": "The name of the document", "type": "word"},
                "status": {"description": "The current status of the document", "type": "string", "enum": ["active", "archived"], "required": True}
            },
            "additionalProperties": False,
            "required": ["_id", "status"]
        }
        t = Type("simple.1.0.0.1.yaml", document)
        rendered = t.get_bson_schema()
        expected = load_json(os.path.join(self.input_folder, "verified_output/bson_schema/simple.1.0.0.1.json"))
        self.assertEqual(rendered, expected)


class TestTypeUnitTestVerified(unittest.TestCase):
    """
    Unit tests for type rendering using type_unit_test folder.
    Drives comparisons by getting all files from verified output,
    rendering based on filename, and comparing.
    """
    def setUp(self):
        self.input_folder = 'tests/test_cases/type_unit_test'
        set_config_input_folder(self.input_folder)

    def tearDown(self):
        clear_config()

    def test_all_types_json_schema(self):
        """Test JSON schema rendering for all types in verified output"""
        verified_dir = os.path.join(self.input_folder, "verified_output/json_schema")
        for filename in os.listdir(verified_dir):
            if filename.endswith('.yaml'):
                type_name = filename[:-5]  # Remove .yaml extension
                self._compare_json_schema(type_name, filename)

    def test_all_types_bson_schema(self):
        """Test BSON schema rendering for all types in verified output"""
        verified_dir = os.path.join(self.input_folder, "verified_output/bson_schema")
        for filename in os.listdir(verified_dir):
            if filename.endswith('.json'):
                type_name = filename[:-5]  # Remove .json extension
                self._compare_bson_schema(type_name, filename)

    def _compare_json_schema(self, type_name, expected_filename):
        """Compare rendered JSON schema to expected output"""
        # Render the type
        t = Type(f"{type_name}.yaml")
        rendered = t.get_json_schema()
        
        # Load expected output
        expected_path = os.path.join(self.input_folder, "verified_output/json_schema", expected_filename)
        expected = load_yaml(expected_path)
        
        # Compare with missing/extra logic
        self._assert_dict_equality(rendered, expected, f"JSON schema for {type_name}")

    def _compare_bson_schema(self, type_name, expected_filename):
        """Compare rendered BSON schema to expected output"""
        # Render the type
        t = Type(f"{type_name}.yaml")
        rendered = t.get_bson_schema()
        
        # Load expected output
        expected_path = os.path.join(self.input_folder, "verified_output/bson_schema", expected_filename)
        expected = load_json(expected_path)
        
        # Compare with missing/extra logic
        self._assert_dict_equality(rendered, expected, f"BSON schema for {type_name}")

    def _assert_dict_equality(self, actual, expected, context):
        """Assert dictionary equality with missing/extra reporting"""
        missing = self._dict_diff(expected, actual)
        extra = self._dict_diff(actual, expected)
        
        if missing or extra:
            message = f"\n{context} comparison failed:"
            if missing:
                message += f"\nMissing (expected - given): {missing}"
            if extra:
                message += f"\nExtra (given - expected): {extra}"
            self.fail(message)

    def _dict_diff(self, dict1, dict2):
        """Return keys in dict1 that are missing or different in dict2"""
        diff = {}
        for key, value1 in dict1.items():
            if key not in dict2:
                diff[key] = value1
            elif isinstance(value1, dict) and isinstance(dict2[key], dict):
                nested_diff = self._dict_diff(value1, dict2[key])
                if nested_diff:
                    diff[key] = nested_diff
            elif value1 != dict2[key]:
                diff[key] = value1
        return diff


if __name__ == '__main__':
    unittest.main() 