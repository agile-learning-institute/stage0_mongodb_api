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
                    
    def test_load_minimum_valid(self):
        """Test loading empty schema directory structure."""

        # Initialize SchemaManager 
        test_case_dir = os.path.join(self.test_cases_dir, "minimum_valid")
        self.config.INPUT_FOLDER = test_case_dir        
        manager = SchemaManager()
        
        # Verify no load errors
        self.assertEqual(manager.load_errors, [], "Unexpected load errors in simple_valid test case")
        self.assertEqual(len(manager.dictionaries), 0, f"Unexpected number of dictionaries {len(manager.dictionaries)}")
        self.assertEqual(len(manager.types), 0, f"Unexpected number of types {len(manager.types)}")
        self.assertEqual(len(manager.enumerators), 0, f"Unexpected number of enumerators {len(manager.enumerators)}")
        
    def test_load_small_sample(self):
        """Test loading large sample schema."""

        # Initialize SchemaManager 
        test_case_dir = os.path.join(self.test_cases_dir, "small_sample")
        self.config.INPUT_FOLDER = test_case_dir        
        manager = SchemaManager()
        
        # Verify no load errors
        self.assertEqual(manager.load_errors, [], f"Unexpected load errors {manager.load_errors}")
        self.assertEqual(len(manager.dictionaries), 1, f"Unexpected number of dictionaries {len(manager.dictionaries)}")
        self.assertEqual(len(manager.types), 2, f"Unexpected number of types {len(manager.types)}")
        self.assertEqual(len(manager.enumerators), 2, f"Unexpected number of enumerators {len(manager.enumerators)}")

    def test_load_large_sample(self):
        """Test loading large sample schema."""

        # Initialize SchemaManager 
        test_case_dir = os.path.join(self.test_cases_dir, "large_sample")
        self.config.INPUT_FOLDER = test_case_dir        
        manager = SchemaManager()
        
        # Verify no load errors
        self.assertEqual(manager.load_errors, [], f"Unexpected load errors {manager.load_errors}")
        self.assertEqual(len(manager.dictionaries), 5, f"Unexpected number of dictionaries {len(manager.dictionaries)}")
        self.assertEqual(len(manager.types), 10, f"Unexpected number of types {len(manager.types)}")
        self.assertEqual(len(manager.enumerators), 4, f"Unexpected number of enumerators {len(manager.enumerators)}")

    def test_missing_folders(self):
        """Test loading with missing folders."""

        # Initialize SchemaManager 
        test_case_dir = os.path.join(self.test_cases_dir, "missing_folders")
        self.config.INPUT_FOLDER = test_case_dir        
        manager = SchemaManager()
        
        # Verify no load errors
        self.assertEqual(len(manager.load_errors), 3, f"Unexpected load errors {manager.load_errors}")

    def test_non_parsable(self):
        """Test loading with non-parsable files"""

        # Initialize SchemaManager 
        test_case_dir = os.path.join(self.test_cases_dir, "non_parsable")
        self.config.INPUT_FOLDER = test_case_dir        
        manager = SchemaManager()
        
        # Verify no load errors
        self.assertEqual(len(manager.load_errors), 3, f"Unexpected load errors {manager.load_errors}")

    def test_validate_small_sample(self):
        """Test schema validation for small sample."""

        # Initialize SchemaManager 
        test_case_dir = os.path.join(self.test_cases_dir, "small_sample")
        self.config.INPUT_FOLDER = test_case_dir        
        manager = SchemaManager()
        errors = manager.validate_schema()
        
        # Assert Validation
        self.assertEqual(manager.load_errors, [], f"Unexpected load errors {manager.load_errors}")
        self.assertEqual(errors, [], f"Unexpected validation errors {errors}, with enumerators {manager.enumerators}")       
        
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
