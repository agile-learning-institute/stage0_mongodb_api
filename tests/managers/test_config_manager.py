import unittest
import os
import shutil
import tempfile
from stage0_mongodb_api.managers.config_manager import ConfigManager
from stage0_py_utils import Config
from unittest.mock import patch

class TestConfigManager(unittest.TestCase):
    def setUp(self):
        self.test_cases_dir = os.path.join(os.path.dirname(__file__), '..', 'test_cases')
        self.config = Config.get_instance()
    
    def tearDown(self):
        pass
    
    def test_load_minimum_valid(self):
        """Test loading empty Collections directory structure."""

        # Initialize SchemaManager 
        test_case_dir = os.path.join(self.test_cases_dir, "minimum_valid")
        self.config.INPUT_FOLDER = test_case_dir        
        manager = ConfigManager()
        
        # Verify no load errors
        self.assertEqual(manager.load_errors, [], "Unexpected load errors in simple_valid test case")
        self.assertEqual(len(manager.collection_configs), 0, f"Unexpected number of collection configs {len(manager.collection_configs)}")

    def test_load_small_sample(self):
        """Test loading Small configuration."""

        # Initialize SchemaManager 
        test_case_dir = os.path.join(self.test_cases_dir, "small_sample")
        self.config.INPUT_FOLDER = test_case_dir        
        manager = ConfigManager()
        
        # Verify no load errors
        self.assertEqual(manager.load_errors, [], "Unexpected load errors in simple_valid test case")
        self.assertEqual(len(manager.collection_configs), 1, f"Unexpected number of collection configs {len(manager.collection_configs)}")
        self.assertIn("simple", manager.collection_configs)

    def test_load_large_sample(self):
        """Test loading large config"""

        # Initialize SchemaManager 
        test_case_dir = os.path.join(self.test_cases_dir, "large_sample")
        self.config.INPUT_FOLDER = test_case_dir        
        manager = ConfigManager()
        
        # Verify no load errors
        self.assertEqual(manager.load_errors, [], "Unexpected load errors in simple_valid test case")
        self.assertEqual(len(manager.collection_configs), 4, f"Unexpected number of collection configs {len(manager.collection_configs)}")
        self.assertIn("media", manager.collection_configs)
        self.assertIn("organization", manager.collection_configs)
        self.assertIn("search", manager.collection_configs)
        self.assertIn("user", manager.collection_configs)

    def test_non_parsable(self):
        """Test loading with non-parsable files"""

        # Initialize SchemaManager 
        test_case_dir = os.path.join(self.test_cases_dir, "non_parsable")
        self.config.INPUT_FOLDER = test_case_dir        
        manager = ConfigManager()
        
        # Verify no load errors
        self.assertEqual(len(manager.load_errors), 1, f"Unexpected load errors {manager.load_errors}")

    def test_validation_errors(self):
        """Test loading with validation errors"""

        # Initialize SchemaManager 
        test_case_dir = os.path.join(self.test_cases_dir, "validation_errors")
        self.config.INPUT_FOLDER = test_case_dir        
        manager = ConfigManager()
        errors = manager.validate_configs()
        
        # Verify no load errors
        self.assertEqual(len(manager.load_errors), 0, f"Unexpected load errors {manager.load_errors}")
        self.assertEqual(len(errors), 6, f"Unexpected number of validation errors {errors}")

    @patch('stage0_mongodb_api.managers.config_manager.MongoIO')
    def test_load_test_data_bulk_write_error(self, mock_mongo):
        """Test that _load_test_data properly handles bulk write errors."""
        # Arrange
        from stage0_py_utils.mongo_utils.mongo_io import TestDataLoadError
        mock_details = {'writeErrors': [{'index': 0, 'code': 121, 'errmsg': 'Document failed validation'}]}
        mock_mongo.return_value.load_test_data.side_effect = TestDataLoadError("Schema validation failed during test data load", details=mock_details)
        
        config_manager = ConfigManager()
        collection_name = "test_collection"
        test_data_file = "test.json"
        
        # Act
        result = config_manager._load_test_data(collection_name, test_data_file)
        
        # Assert
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["operation"], "load_test_data")
        self.assertEqual(result["collection"], collection_name)
        self.assertIn("test.json", result["test_data"])
        self.assertEqual(result["error"], "Schema validation failed during test data load")
        self.assertEqual(result["details"], mock_details)

    @patch('stage0_mongodb_api.managers.config_manager.MongoIO')
    def test_load_test_data_generic_error(self, mock_mongo):
        """Test that _load_test_data properly handles generic errors."""
        # Arrange
        mock_mongo.return_value.load_test_data.side_effect = Exception("File not found")
        
        config_manager = ConfigManager()
        collection_name = "test_collection"
        test_data_file = "test.json"
        
        # Act
        result = config_manager._load_test_data(collection_name, test_data_file)
        
        # Assert
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["operation"], "load_test_data")
        self.assertEqual(result["collection"], collection_name)
        self.assertIn("test.json", result["test_data"])
        self.assertEqual(result["error"], "File not found")

    @patch('stage0_mongodb_api.managers.config_manager.MongoIO')
    def test_load_test_data_success(self, mock_mongo):
        """Test that _load_test_data properly handles successful loads."""
        # Arrange
        mock_results = {
            "status": "success",
            "operation": "load_test_data",
            "collection": "test_collection",
            "documents_loaded": 5,
            "inserted_ids": ["id1", "id2", "id3", "id4", "id5"],
            "acknowledged": True
        }
        mock_mongo.return_value.load_test_data.return_value = mock_results
        
        config_manager = ConfigManager()
        collection_name = "test_collection"
        test_data_file = "test.json"
        
        # Act
        result = config_manager._load_test_data(collection_name, test_data_file)
        
        # Assert
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["operation"], "load_test_data")
        self.assertEqual(result["collection"], collection_name)
        self.assertIn("test.json", result["test_data"])
        self.assertEqual(result["results"], mock_results)

if __name__ == '__main__':
    unittest.main() 