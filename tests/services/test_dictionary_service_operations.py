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
        self.assertEqual(prop.type, "void")
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
        self.assertEqual(prop.type, "void")
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
            "file_name": "test.yaml",
            "_locked": False,
            "root": {
                "description": "Test dictionary",
                "version": "1.0.0",
                "properties": {
                    "name": {
                        "description": "Name property",
                        "type": "string"
                    }
                }
            }
        }
        
        dictionary = Dictionary("test.yaml")
        
        self.assertEqual(dictionary.file_name, "test.yaml")
        self.assertIsInstance(dictionary.root, Property)
        self.assertEqual(dictionary.root.description, "Test dictionary")

    def test_init_with_document(self):
        """Test Dictionary initialization with document"""
        doc = {
            "file_name": "test.yaml",
            "_locked": False,
            "root": {
                "description": "Test dictionary",
                "version": "1.0.0",
                "properties": {
                    "name": {
                        "description": "Name property",
                        "type": "string"
                    }
                }
            }
        }
        dictionary = Dictionary("test.yaml", doc)
        self.assertEqual(dictionary.file_name, "test.yaml")
        self.assertIsInstance(dictionary.root, Property)
        self.assertEqual(dictionary.root.description, "Test dictionary")

    def test_to_dict(self):
        """Test Dictionary to_dict method"""
        dictionary = Dictionary("test.yaml", {
            "file_name": "test.yaml",
            "_locked": False,
            "root": {
                "description": "Test dictionary",
                "version": "1.0.0",
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name field"
                    }
                }
            }
        })
        
        result = dictionary.to_dict()
        self.assertEqual(result["file_name"], "test.yaml")
        self.assertEqual(result["_locked"], False)
        self.assertIn("root", result)
        
        # Check that root contains the expected structure
        root = result["root"]
        self.assertEqual(root["description"], "Test dictionary")
        self.assertIn("properties", root)

    def test_to_dict_roundtrip_basic(self):
        """Test that Dictionary.to_dict() returns the same data used to create it - basic case"""
        test_data = {
            "file_name": "test.yaml",
            "_locked": False,
            "root": {
                "description": "Test dictionary",
                "version": "1.0.0",
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name field",
                        "required": True
                    },
                    "age": {
                        "type": "number",
                        "description": "Age field",
                        "required": False
                    }
                }
            }
        }
        
        dictionary = Dictionary("test.yaml", test_data)
        result = dictionary.to_dict()
        
        # Check that the structure is correct
        self.assertEqual(result["file_name"], "test.yaml")
        self.assertEqual(result["_locked"], False)
        self.assertIn("root", result)
        
        # The root should contain the property structure (without document-level fields)
        expected_root = {
            "description": "Test dictionary",
            "type": "object",
            "required": False,
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name field",
                    "required": True
                },
                "age": {
                    "type": "number",
                    "description": "Age field",
                    "required": False
                }
            },
            "additionalProperties": False
        }
        self.assertEqual(result["root"], expected_root)

    def test_to_dict_roundtrip_with_one_of(self):
        """Test that Dictionary.to_dict() returns the same data used to create it - with one_of"""
        test_data = {
            "file_name": "test.yaml",
            "_locked": False,
            "root": {
                "description": "Test dictionary with oneOf",
                "version": "1.0.0",
                "type": "object",
                "properties": {
                    "content_data": {
                        "description": "Content data with oneOf",
                        "type": "object",
                        "required": True,
                        "properties": {},
                        "additionalProperties": False,
                        "one_of": [
                            {
                                "description": "Article content",
                                "type": "object",
                                "properties": {
                                    "body": {
                                        "description": "Article body",
                                        "type": "string",
                                        "required": True
                                    }
                                },
                                "required": ["body"],
                                "additionalProperties": False
                            },
                            {
                                "description": "Video content",
                                "type": "object",
                                "properties": {
                                    "url": {
                                        "description": "Video URL",
                                        "type": "string",
                                        "required": True
                                    }
                                },
                                "required": ["url"],
                                "additionalProperties": False
                            }
                        ]
                    }
                }
            }
        }
        
        dictionary = Dictionary("test.yaml", test_data)
        result = dictionary.to_dict()
        
        # Check that the structure is correct
        self.assertEqual(result["file_name"], "test.yaml")
        self.assertEqual(result["_locked"], False)
        self.assertIn("root", result)
        
        # The root should contain the property structure (without document-level fields)
        expected_root = {
            "description": "Test dictionary with oneOf",
            "type": "object",
            "required": False,
            "properties": {
                "content_data": {
                    "description": "Content data with oneOf",
                    "type": "object",
                    "required": True,
                    "properties": {},
                    "additionalProperties": False,
                    "one_of": [
                        {
                            "description": "Article content",
                            "type": "object",
                            "properties": {
                                "body": {
                                    "description": "Article body",
                                    "type": "string",
                                    "required": True
                                }
                            },
                            "required": ["body"],
                            "additionalProperties": False
                        },
                        {
                            "description": "Video content",
                            "type": "object",
                            "properties": {
                                "url": {
                                    "description": "Video URL",
                                    "type": "string",
                                    "required": True
                                }
                            },
                            "required": ["url"],
                            "additionalProperties": False
                        }
                    ]
                }
            },
            "additionalProperties": False
        }
        self.assertEqual(result["root"], expected_root)

    def test_to_dict_roundtrip_with_refs(self):
        """Test that Dictionary.to_dict() returns the same data used to create it - with refs"""
        test_data = {
            "file_name": "test.yaml",
            "_locked": False,
            "root": {
                "description": "Test dictionary with refs",
                "version": "1.0.0",
                "type": "object",
                "properties": {
                    "user": {
                        "ref": "user.1.0.0.yaml"
                    },
                    "settings": {
                        "ref": "settings.1.0.0.yaml"
                    }
                }
            }
        }
        
        dictionary = Dictionary("test.yaml", test_data)
        result = dictionary.to_dict()
        
        # Check that the structure is correct
        self.assertEqual(result["file_name"], "test.yaml")
        self.assertEqual(result["_locked"], False)
        self.assertIn("root", result)
        
        # The root should contain the property structure (without document-level fields)
        expected_root = {
            "description": "Test dictionary with refs",
            "type": "object",
            "required": False,
            "properties": {
                "user": {
                    "ref": "user.1.0.0.yaml"
                },
                "settings": {
                    "ref": "settings.1.0.0.yaml"
                }
            },
            "additionalProperties": False
        }
        self.assertEqual(result["root"], expected_root)

    def test_to_dict_roundtrip_with_enums(self):
        """Test that Dictionary.to_dict() returns the same data used to create it - with enums"""
        test_data = {
            "file_name": "test.yaml",
            "_locked": False,
            "root": {
                "description": "Test dictionary with enums",
                "version": "1.0.0",
                "type": "object",
                "properties": {
                    "status": {
                        "type": "enum",
                        "description": "Status enum",
                        "enums": "default_status",
                        "required": True
                    },
                    "tags": {
                        "type": "enum_array",
                        "description": "Array of tags",
                        "enums": "content_tags",
                        "required": False
                    }
                }
            }
        }
        
        dictionary = Dictionary("test.yaml", test_data)
        result = dictionary.to_dict()
        
        # Check that the structure is correct
        self.assertEqual(result["file_name"], "test.yaml")
        self.assertEqual(result["_locked"], False)
        self.assertIn("root", result)
        
        # The root should contain the property structure (without document-level fields)
        expected_root = {
            "description": "Test dictionary with enums",
            "type": "object",
            "required": False,
            "properties": {
                "status": {
                    "type": "enum",
                    "description": "Status enum",
                    "enums": "default_status",
                    "required": True
                },
                "tags": {
                    "type": "enum_array",
                    "description": "Array of tags",
                    "enums": "content_tags",
                    "required": False
                }
            },
            "additionalProperties": False
        }
        self.assertEqual(result["root"], expected_root)

    def test_to_dict_roundtrip_with_arrays(self):
        """Test that Dictionary.to_dict() returns the same data used to create it - with arrays"""
        test_data = {
            "file_name": "test.yaml",
            "_locked": False,
            "root": {
                "description": "Test dictionary with arrays",
                "version": "1.0.0",
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "description": "Array of items",
                        "required": True,
                        "items": {
                            "description": "Individual item",
                            "type": "string"
                        }
                    },
                    "metadata": {
                        "type": "array",
                        "description": "Array of metadata",
                        "required": False,
                        "items": {
                            "description": "Metadata item",
                            "type": "object",
                            "properties": {
                                "key": {
                                    "type": "string",
                                    "description": "Metadata key"
                                },
                                "value": {
                                    "type": "string",
                                    "description": "Metadata value"
                                }
                            }
                        }
                    }
                }
            }
        }
        
        dictionary = Dictionary("test.yaml", test_data)
        result = dictionary.to_dict()
        
        # Check that the structure is correct
        self.assertEqual(result["file_name"], "test.yaml")
        self.assertEqual(result["_locked"], False)
        self.assertIn("root", result)
        
        # The root should contain the property structure (without document-level fields)
        expected_root = {
            "description": "Test dictionary with arrays",
            "type": "object",
            "required": False,
            "properties": {
                "items": {
                    "type": "array",
                    "description": "Array of items",
                    "required": True,
                    "items": {
                        "description": "Individual item",
                        "type": "string",
                        "required": False
                    }
                },
                "metadata": {
                    "type": "array",
                    "description": "Array of metadata",
                    "required": False,
                    "items": {
                        "description": "Metadata item",
                        "type": "object",
                        "required": False,
                        "additionalProperties": False,
                        "properties": {
                            "key": {
                                "type": "string",
                                "description": "Metadata key",
                                "required": False
                            },
                            "value": {
                                "type": "string",
                                "description": "Metadata value",
                                "required": False
                            }
                        }
                    }
                }
            },
            "additionalProperties": False
        }
        self.assertEqual(result["root"], expected_root)

    def test_to_dict_roundtrip_with_missing_values(self):
        """Test that Dictionary.to_dict() returns the same data used to create it - with missing values"""
        test_data = {
            "file_name": "test.yaml",
            "_locked": False,
            "root": {
                "description": "Test dictionary with missing values",
                "version": "1.0.0",
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string"
                        # Missing description, required, etc.
                    },
                    "age": {
                        "type": "number"
                        # Missing description, required, etc.
                    }
                }
            }
        }
        
        dictionary = Dictionary("test.yaml", test_data)
        result = dictionary.to_dict()
        
        # Check that the structure is correct
        self.assertEqual(result["file_name"], "test.yaml")
        self.assertEqual(result["_locked"], False)
        self.assertIn("root", result)
        
        # The root should have default values filled in, so we need to check
        # that the original structure is preserved but with defaults added
        root = result["root"]
        self.assertEqual(root["description"], "Test dictionary with missing values")
        self.assertEqual(root["type"], "object")
        self.assertIn("properties", root)
        self.assertIn("name", root["properties"])
        self.assertIn("age", root["properties"])
        
        # Check that defaults are applied
        self.assertEqual(root["properties"]["name"]["description"], "Missing Required Description")
        self.assertFalse(root["properties"]["name"]["required"])
        self.assertEqual(root["properties"]["age"]["description"], "Missing Required Description")
        self.assertFalse(root["properties"]["age"]["required"])

    def test_to_dict_roundtrip_complex_nested(self):
        """Test that Dictionary.to_dict() returns the same data used to create it - complex nested structure"""
        test_data = {
            "file_name": "test.yaml",
            "_locked": False,
            "root": {
                "description": "Complex nested dictionary",
                "version": "1.0.0",
                "type": "object",
                "properties": {
                    "user": {
                        "type": "object",
                        "description": "User object",
                        "properties": {
                            "profile": {
                                "type": "object",
                                "description": "User profile",
                                "properties": {
                                    "name": {
                                        "type": "string",
                                        "description": "User name"
                                    },
                                    "preferences": {
                                        "type": "array",
                                        "description": "User preferences",
                                        "items": {
                                            "type": "string"
                                        }
                                    }
                                },
                                "additionalProperties": False
                            },
                            "settings": {
                                "ref": "settings.1.0.0.yaml"
                            }
                        },
                        "additionalProperties": False
                    },
                    "content": {
                        "type": "object",
                        "description": "Content object",
                        "properties": {
                            "title": {"type": "string", "required": True, "description": "Missing Required Description"},
                            "body": {"type": "string", "required": True, "description": "Missing Required Description"}
                        },
                        "additionalProperties": False
                    },
                    "media": {
                        "type": "object",
                        "description": "Media object",
                        "properties": {
                            "url": {"type": "string", "required": True, "description": "Missing Required Description"},
                            "duration": {"type": "number", "required": False, "description": "Missing Required Description"}
                        },
                        "additionalProperties": False
                    }
                },
                "additionalProperties": False
            }
        }
        
        dictionary = Dictionary("test.yaml", test_data)
        result = dictionary.to_dict()
        expected_root = {
            "description": "Complex nested dictionary",
            "type": "object",
            "required": False,
            "properties": {
                "user": {
                    "type": "object",
                    "description": "User object",
                    "required": False,
                    "properties": {
                        "profile": {
                            "type": "object",
                            "description": "User profile",
                            "required": False,
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": "User name",
                                    "required": False
                                },
                                "preferences": {
                                    "type": "array",
                                    "description": "User preferences",
                                    "required": False,
                                    "items": {
                                        "description": "Missing Required Description",
                                        "type": "string",
                                        "required": False
                                    }
                                }
                            },
                            "additionalProperties": False
                        },
                        "settings": {
                            "ref": "settings.1.0.0.yaml"
                        }
                    },
                    "additionalProperties": False
                },
                "content": {
                    "type": "object",
                    "description": "Content object",
                    "required": False,
                    "properties": {
                        "title": {"type": "string", "required": True, "description": "Missing Required Description"},
                        "body": {"type": "string", "required": True, "description": "Missing Required Description"}
                    },
                    "additionalProperties": False
                },
                "media": {
                    "type": "object",
                    "description": "Media object",
                    "required": False,
                    "properties": {
                        "url": {"type": "string", "required": True, "description": "Missing Required Description"},
                        "duration": {"type": "number", "required": False, "description": "Missing Required Description"}
                    },
                    "additionalProperties": False
                }
            },
            "additionalProperties": False
        }
        self.assertEqual(result["root"], expected_root)


if __name__ == '__main__':
    unittest.main() 