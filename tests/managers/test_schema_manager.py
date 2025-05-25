import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import yaml
import json
from stage0_mongodb_api.managers.schema_manager import SchemaManager, SchemaFormat, SchemaError, SchemaValidationError

class TestSchemaManager(unittest.TestCase):
    def setUp(self):
        self.dictionary_path = "/test/dictionary"
        self.types_dir = os.path.join(self.dictionary_path, "types")
        self.dict_dir = os.path.join(self.dictionary_path, "dictionary")
        self.data_dir = os.path.join(self.dictionary_path, "data")
        
        # Mock file system
        self.patcher = patch('os.path.exists')
        self.mock_exists = self.patcher.start()
        self.mock_exists.return_value = True
        
        # Mock file operations
        self.mock_open_patcher = patch('builtins.open', mock_open())
        self.mock_open = self.mock_open_patcher.start()
        
        # Mock directory listing
        self.listdir_patcher = patch('os.listdir')
        self.mock_listdir = self.listdir_patcher.start()
        
    def tearDown(self):
        self.patcher.stop()
        self.mock_open_patcher.stop()
        self.listdir_patcher.stop()
        
    def test_init_valid_dictionary(self):
        """Test initialization with valid dictionary path."""
        # Mock directory contents
        self.mock_listdir.side_effect = [
            ["word.yaml", "sentence.yaml"],  # types directory
            ["user.1.0.0.yaml", "user.1.0.1.yaml"],  # dictionary directory
            ["enumerators.json"]  # data directory
        ]
        
        # Mock type definitions
        type_def = {
            "title": "Word",
            "description": "A string of text",
            "json_type": {"type": "string"},
            "bson_type": {"type": "string"}
        }
        self.mock_open.return_value.__enter__.return_value.read.side_effect = [
            yaml.dump(type_def),  # word.yaml
            yaml.dump(type_def),  # sentence.yaml
            yaml.dump({"title": "User", "description": "User schema"}),  # user.1.0.0.yaml
            yaml.dump({"title": "User", "description": "Updated user schema"}),  # user.1.0.1.yaml
            json.dumps({"status": {"active": "Active status"}})  # enumerators.json
        ]
        
        manager = SchemaManager(self.dictionary_path)
        
        # Verify types loaded correctly
        self.assertEqual(manager.types["word"], type_def)
        self.assertEqual(manager.types["sentence"], type_def)
        
        # Verify dictionaries loaded correctly
        self.assertEqual(len(manager.dictionaries), 2)  # 2 yaml files
        self.assertIn("user.1.0.0", manager.dictionaries)
        self.assertIn("user.1.0.1", manager.dictionaries)
        
        # Verify enumerators loaded correctly
        self.assertEqual(manager.enumerators, {"status": {"active": "Active status"}})
        
    def test_init_missing_directories(self):
        """Test initialization with missing directories."""
        self.mock_exists.side_effect = [True, False, True, True]  # types dir missing
        with self.assertRaises(FileNotFoundError) as context:
            SchemaManager(self.dictionary_path)
        self.assertEqual(str(context.exception), f"Types directory not found: {self.types_dir}")
        
        self.mock_exists.side_effect = [True, True, False, True]  # dictionary dir missing
        with self.assertRaises(FileNotFoundError) as context:
            SchemaManager(self.dictionary_path)
        self.assertEqual(str(context.exception), f"Dictionary directory not found: {self.dict_dir}")
        
        self.mock_exists.side_effect = [True, True, True, False]  # data dir missing
        with self.assertRaises(FileNotFoundError) as context:
            SchemaManager(self.dictionary_path)
        self.assertEqual(str(context.exception), f"Data directory not found: {self.data_dir}")
        
    def test_init_missing_enumerators(self):
        """Test initialization with missing enumerators file."""
        self.mock_exists.side_effect = [True, True, True, False]  # enumerators.json missing
        with self.assertRaises(FileNotFoundError) as context:
            SchemaManager(self.dictionary_path)
        self.assertEqual(str(context.exception), f"Enumerators file not found: {os.path.join(self.data_dir, 'enumerators.json')}")
        
    def test_init_invalid_type_definition(self):
        """Test initialization with invalid type definition."""
        self.mock_listdir.side_effect = [
            ["invalid.yaml"],  # types directory
            [],  # dictionary directory
            ["enumerators.json"]  # data directory
        ]
        self.mock_open.return_value.__enter__.return_value.read.side_effect = [
            "invalid: yaml",  # invalid.yaml
            json.dumps({"status": {"active": "Active status"}})  # enumerators.json
        ]
        with self.assertRaises(SchemaError) as context:
            SchemaManager(self.dictionary_path)
        self.assertIn("Invalid type definition", str(context.exception))
        
    def test_init_invalid_dictionary_definition(self):
        """Test initialization with invalid dictionary definition."""
        self.mock_listdir.side_effect = [
            [],  # types directory
            ["invalid.yaml"],  # dictionary directory
            ["enumerators.json"]  # data directory
        ]
        self.mock_open.return_value.__enter__.return_value.read.side_effect = [
            "invalid: yaml",  # invalid.yaml
            json.dumps({"status": {"active": "Active status"}})  # enumerators.json
        ]
        with self.assertRaises(SchemaError) as context:
            SchemaManager(self.dictionary_path)
        self.assertIn("Invalid dictionary definition", str(context.exception))
        
    def test_init_invalid_enumerators_json(self):
        """Test initialization with invalid enumerators JSON."""
        self.mock_listdir.side_effect = [
            [],  # types directory
            [],  # dictionary directory
            ["enumerators.json"]  # data directory
        ]
        self.mock_open.return_value.__enter__.return_value.read.return_value = "invalid json"
        with self.assertRaises(SchemaError) as context:
            SchemaManager(self.dictionary_path)
        self.assertIn("Invalid JSON in enumerators file", str(context.exception))
        
    def test_init_non_dict_enumerators(self):
        """Test initialization with non-dictionary enumerators."""
        self.mock_listdir.side_effect = [
            [],  # types directory
            [],  # dictionary directory
            ["enumerators.json"]  # data directory
        ]
        self.mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(["not", "a", "dict"])
        with self.assertRaises(SchemaError) as context:
            SchemaManager(self.dictionary_path)
        self.assertIn("Invalid enumerators file: must be a dictionary", str(context.exception))
        
    def test_validate_schema_empty_name(self):
        """Test schema validation with empty name."""
        manager = SchemaManager(self.dictionary_path)
        with self.assertRaises(ValueError) as context:
            manager.validate_schema("")
        self.assertEqual(str(context.exception), "Schema name cannot be empty")
        
    def test_validate_schema_invalid_name(self):
        """Test schema validation with invalid name format."""
        manager = SchemaManager(self.dictionary_path)
        with self.assertRaises(ValueError) as context:
            manager.validate_schema("invalid-name")
        self.assertEqual(str(context.exception), "Invalid schema name format: invalid-name")
        
    def test_validate_schema_nonexistent_file(self):
        """Test schema validation with nonexistent schema file."""
        manager = SchemaManager(self.dictionary_path)
        self.mock_exists.return_value = False
        with self.assertRaises(FileNotFoundError) as context:
            manager.validate_schema("test")
        self.assertEqual(str(context.exception), "Schema file not found: test")
        
    def test_validate_schema_invalid_structure(self):
        """Test schema validation with invalid structure."""
        manager = SchemaManager(self.dictionary_path)
        schema = {"description": "Test schema"}
        self.mock_open.return_value.__enter__.return_value.read.return_value = yaml.dump(schema)
        
        errors = manager.validate_schema("test")
        self.assertIn("Missing required field 'title' at root level", errors)
        self.assertIn("Missing required field 'type' at root level", errors)
        
    def test_validate_schema_invalid_property(self):
        """Test schema validation with invalid property."""
        manager = SchemaManager(self.dictionary_path)
        schema = {
            "title": "Test",
            "description": "Test schema",
            "type": "object",
            "properties": {
                "name": {
                    "type": "invalid_type"
                }
            }
        }
        self.mock_open.return_value.__enter__.return_value.read.return_value = yaml.dump(schema)
        
        errors = manager.validate_schema("test")
        self.assertIn("Property 'name' missing description", errors)
        self.assertIn("Property 'name' has invalid type 'invalid_type'", errors)
        
    def test_validate_schema_object_properties(self):
        """Test schema validation for object properties."""
        manager = SchemaManager(self.dictionary_path)
        schema = {
            "title": "Test",
            "description": "Test schema",
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "description": "User object",
                    "additionalProperties": "invalid"  # Should be boolean
                }
            }
        }
        self.mock_open.return_value.__enter__.return_value.read.return_value = yaml.dump(schema)
        
        errors = manager.validate_schema("test")
        self.assertIn("Property 'user' has invalid additionalProperties value: must be boolean", errors)
        
    def test_validate_schema_required_property(self):
        """Test schema validation for required property."""
        manager = SchemaManager(self.dictionary_path)
        schema = {
            "title": "Test",
            "description": "Test schema",
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name field",
                    "required": "invalid"  # Should be boolean
                }
            }
        }
        self.mock_open.return_value.__enter__.return_value.read.return_value = yaml.dump(schema)
        
        errors = manager.validate_schema("test")
        self.assertIn("Property 'name' has invalid required value: must be boolean", errors)
        
    def test_validate_schema_custom_type(self):
        """Test schema validation for custom type."""
        # Mock type definition
        type_def = {
            "title": "Word",
            "description": "A string of text",
            "json_type": {"type": "string"},
            "bson_type": {"type": "string"}
        }
        self.mock_open.return_value.__enter__.return_value.read.return_value = yaml.dump(type_def)
        
        manager = SchemaManager(self.dictionary_path)
        schema = {
            "title": "Test",
            "description": "Test schema",
            "type": "object",
            "properties": {
                "name": {
                    "type": "Word",
                    "description": "Name field"
                }
            }
        }
        self.mock_open.return_value.__enter__.return_value.read.return_value = yaml.dump(schema)
        
        errors = manager.validate_schema("test")
        self.assertEqual(len(errors), 0)  # Should be valid
        
    def test_validate_schema_invalid_custom_type(self):
        """Test schema validation for invalid custom type."""
        # Mock type definition with missing required fields
        type_def = {
            "title": "Word",
            "description": "A string of text"
            # Missing json_type and bson_type
        }
        self.mock_open.return_value.__enter__.return_value.read.return_value = yaml.dump(type_def)
        
        manager = SchemaManager(self.dictionary_path)
        schema = {
            "title": "Test",
            "description": "Test schema",
            "type": "object",
            "properties": {
                "name": {
                    "type": "Word",
                    "description": "Name field"
                }
            }
        }
        self.mock_open.return_value.__enter__.return_value.read.return_value = yaml.dump(schema)
        
        errors = manager.validate_schema("test")
        self.assertIn("Custom type name missing required field 'json_type'", errors)
        self.assertIn("Custom type name missing required field 'bson_type'", errors)
        
    def test_render_schema_empty_name(self):
        """Test schema rendering with empty name."""
        manager = SchemaManager(self.dictionary_path)
        with self.assertRaises(ValueError) as context:
            manager.render_schema("")
        self.assertEqual(str(context.exception), "Schema name cannot be empty")
        
    def test_apply_schema_empty_collection_name(self):
        """Test schema application with empty collection name."""
        manager = SchemaManager(self.dictionary_path)
        with self.assertRaises(ValueError) as context:
            manager.apply_schema("", "test")
        self.assertEqual(str(context.exception), "Collection name cannot be empty")
        
    def test_apply_schema_empty_schema_name(self):
        """Test schema application with empty schema name."""
        manager = SchemaManager(self.dictionary_path)
        with self.assertRaises(ValueError) as context:
            manager.apply_schema("test", "")
        self.assertEqual(str(context.exception), "Schema name cannot be empty")
        
    def test_remove_schema_empty_collection_name(self):
        """Test schema removal with empty collection name."""
        manager = SchemaManager(self.dictionary_path)
        with self.assertRaises(ValueError) as context:
            manager.remove_schema("")
        self.assertEqual(str(context.exception), "Collection name cannot be empty")

if __name__ == '__main__':
    unittest.main()
