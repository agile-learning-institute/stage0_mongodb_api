import unittest
from unittest.mock import patch, MagicMock
from stage0_py_utils import Config
import os
import yaml
import json
from stage0_mongodb_api.managers.schema_manager import SchemaManager, SchemaFormat, SchemaError, SchemaValidationError

class TestSchemaManager(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.config = Config.get_instance()
        self.test_cases_dir = os.path.join(os.path.dirname(__file__), '..', 'test_cases')
        
        # Mock MongoIO for apply/remove schema tests
        self.mongo_patcher = patch('stage0_mongodb_api.managers.schema_manager.MongoIO')
        self.mock_mongo = self.mongo_patcher.start()
        self.mock_mongo.get_instance.return_value = MagicMock()
        
    def tearDown(self):
        """Clean up test fixtures"""
        self.mongo_patcher.stop()
        
    def _load_yaml(self, filename):
        """Load a YAML file from the test cases directory."""
        with open(filename, 'r') as f:
            return yaml.safe_load(f)
            
    def _load_json(self, filename):
        """Load a JSON file from the test cases directory."""
        with open(filename, 'r') as f:
            return json.load(f)
            
    def test_load_schema_simple(self):
        """Test schema application with valid schema."""

        # Initialize SchemaManager 
        test_case_dir = os.path.join(self.test_cases_dir, "simple_valid")
        self.config.INPUT_FOLDER = test_case_dir        
        manager = SchemaManager()
        
        # Verify no load errors
        self.assertEqual(manager.load_errors, [], "Unexpected load errors in simple_valid test case")

    def test_schema_validation_and_rendering(self):
        """Test schema validation and rendering for all test cases."""
        # Get all test case folders
        test_cases = [d for d in os.listdir(self.test_cases_dir) 
                     if os.path.isdir(os.path.join(self.test_cases_dir, d))]
        
        for test_case in test_cases:
            test_case_dir = os.path.join(self.test_cases_dir, test_case)
            expected_dir = os.path.join(test_case_dir, 'expected')
            
            # Set input folder for this test case
            self.config.INPUT_FOLDER = test_case_dir
            
            # Initialize SchemaManager and check for load errors
            manager = SchemaManager()
            self.assertEqual(manager.load_errors, [], "Unexpected load errors in simple_valid test case")
            
            # Test validation
            validation_file = os.path.join(expected_dir, 'validation.json')
            errors = manager.validate_schema()
            expected_validation = self._load_json(validation_file)
            self.assertEqual(errors, expected_validation, f"Validation failed for test case: {test_case}")
            
            # Test schema rendering
            dict_dir = os.path.join(expected_dir, 'dictionary')
            if os.path.exists(dict_dir):
                for dict_file in os.listdir(dict_dir):
                    # Extract schema name and format from filename
                    # Example: user.1.0.0.bson -> user.1.0.0, BSON
                    parts = dict_file.split('.')
                    schema_name = '.'.join(parts[:-2])  # Remove .bson or .json
                    format_type = SchemaFormat.BSON_SCHEMA if 'bson' in dict_file else SchemaFormat.JSON_SCHEMA
                    
                    # Render schema
                    schema = manager.render_schema(schema_name, format_type)
                    
                    # Compare with expected output
                    expected_schema = self._load_json(os.path.join(dict_dir, dict_file))
                    self.assertEqual(schema, expected_schema,
                                   f"Schema rendering failed for {dict_file} in test case: {test_case}")
        
    def test_apply_schema_valid(self):
        """Test schema application with valid schema."""

        # Initialize SchemaManager 
        test_case_dir = os.path.join(self.test_cases_dir, "simple_valid")
        self.config.INPUT_FOLDER = test_case_dir        
        manager = SchemaManager()
        
        # Verify no load errors
        self.assertEqual(manager.load_errors, [], "Unexpected load errors in simple_valid test case")
        
        # Load the expected BSON schema
        bson_schema = self._load_json(os.path.join(self.test_cases_dir, 'no_errors', 'expected', 'dictionary', 'user.1.0.0.bson.json'))
        
        result = manager.apply_schema("test_collection", bson_schema)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["operation"], "apply_schema")
        self.assertEqual(result["collection"], "test_collection")
        self.assertEqual(result["schema"], bson_schema)
        
        # Verify MongoIO was called correctly
        self.mock_mongo.get_instance.return_value.update_document.assert_called_once_with(
            "test_collection",
            set_data={"validator": {"$jsonSchema": bson_schema}}
        )
        
    def test_remove_schema_valid(self):
        """Test schema removal with valid collection name."""
        test_case_dir = os.path.join(self.test_cases_dir, "simple_valid")
        self.config.INPUT_FOLDER = test_case_dir
        
        # Initialize SchemaManager and check for load errors
        manager = SchemaManager()
        self.assertEqual(manager.load_errors, [], "Unexpected load errors in simple_valid test case")
        
        result = manager.remove_schema("test_collection")
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["operation"], "remove_schema")
        self.assertEqual(result["collection"], "test_collection")
        
        # Verify MongoIO was called correctly
        self.mock_mongo.get_instance.return_value.update_document.assert_called_once_with(
            "test_collection",
            set_data={"validator": {}}
        )

if __name__ == '__main__':
    unittest.main()
