import unittest
from unittest.mock import patch, MagicMock
from stage0_py_utils import Config
import os
import yaml
import json
from stage0_mongodb_api.managers.schema_manager import SchemaManager, SchemaFormat, SchemaError, SchemaValidationError
from typing import List, Dict

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
        self.assertEqual(len(manager.dictionaries), 6, f"Unexpected number of dictionaries {len(manager.dictionaries)}")
        self.assertEqual(len(manager.types), 10, f"Unexpected number of types {len(manager.types)}")
        self.assertEqual(len(manager.enumerators), 4, f"Unexpected number of enumerators {len(manager.enumerators)}")

    def test_load_errors(self):
        """Test loading with all load errors."""

        # Arrange - Initialize SchemaManager 
        test_case_dir = os.path.join(self.test_cases_dir, "load_errors")
        self.config.INPUT_FOLDER = test_case_dir        

        # Act - Load SchemaManager
        manager = SchemaManager()
        errors = manager.load_errors
        
        # Assert - Verify expected load error IDs
        expected_error_ids = {
            "CFG-001", "CFG-002", "CFG-003", "CFG-004", "CFG-005", "CFG-006",
            "SCH-001", "SCH-002", "SCH-003", "SCH-004", "SCH-005", "SCH-006",
            "SCH-007", "SCH-008", "SCH-009", "SCH-010", "SCH-011", "SCH-012"
        }
        
        actual_error_ids = {error.get('error_id') for error in errors if 'error_id' in error}
        missing_errors = expected_error_ids - actual_error_ids
        unexpected_errors = actual_error_ids - expected_error_ids
        self.assertEqual(missing_errors, set(), f"Missing error IDs: {missing_errors} ")
        self.assertEqual(unexpected_errors, set(), f"Unexpected error IDs: {unexpected_errors}")

    def test_validate_minimum_valid(self):
        """Test schema validation for minimum valid."""

        # Initialize SchemaManager 
        test_case_dir = os.path.join(self.test_cases_dir, "minimum_valid")
        self.config.INPUT_FOLDER = test_case_dir        
        manager = SchemaManager()
        errors = manager.validate_schema()
        
        # Assert Validation
        self.assertEqual(manager.load_errors, [], f"Unexpected load errors {manager.load_errors}")
        self.assertEqual(errors, [], f"Unexpected validation errors {errors}, with enumerators {manager.enumerators}")       
        
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
        
    def test_validate_large_sample(self):
        """Test schema validation for large sample."""

        # Initialize SchemaManager 
        test_case_dir = os.path.join(self.test_cases_dir, "large_sample")
        self.config.INPUT_FOLDER = test_case_dir        
        manager = SchemaManager()
        errors = manager.validate_schema()
        
        # Assert Validation
        self.assertEqual(manager.load_errors, [], f"Unexpected load errors {manager.load_errors}")
        self.assertEqual(errors, [], f"Unexpected validation errors {errors}, with enumerators {manager.enumerators}")       

    def test_validation_errors(self):
        """Test schema validation with all validation errors."""

        # Arrange - Initialize SchemaManager 
        test_case_dir = os.path.join(self.test_cases_dir, "validation_errors")
        self.config.INPUT_FOLDER = test_case_dir        
        manager = SchemaManager()
        self.assertEqual(manager.load_errors, [], f"Unexpected load errors {manager.load_errors}")
        
        # Act - validate the schema
        errors = manager.validate_schema()
        
        # Assert - Verify expected validation error IDs
        expected_error_ids = {
            # Schema Manager validation errors
            "SCH-013", "SCH-014", "SCH-015", "SCH-016", "SCH-017", "SCH-023",
            "SCH-026", "SCH-033", "SCH-034", "SCH-035", "SCH-036", "SCH-038",
            "SCH-039", "SCH-040", "SCH-024", "SCH-025", "SCH-027", "SCH-028",
            "SCH-029",
            
            # Config Manager validation errors
            "CFG-004", "CFG-005", "CFG-006", "CFG-007", "CFG-008", "CFG-009",
            "CFG-010", "CFG-011", "CFG-012", "CFG-013"
        }
        
        actual_error_ids = {error.get('error_id') for error in errors if 'error_id' in error}
        missing_errors = expected_error_ids - actual_error_ids
        unexpected_errors = actual_error_ids - expected_error_ids
        self.assertEqual(missing_errors, set(), f"Missing error IDs: {missing_errors}")
        self.assertEqual(unexpected_errors, set(), f"Unexpected error IDs: {unexpected_errors}")

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
