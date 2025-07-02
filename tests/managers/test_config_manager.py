import unittest
import os
import shutil
import tempfile
from stage0_mongodb_api.managers.config_manager import ConfigManager
from stage0_py_utils import Config
from unittest.mock import patch, MagicMock

class TestConfigManager(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mongoio_patcher = patch('stage0_py_utils.mongo_utils.mongo_io.MongoIO.get_instance')
        cls.mock_mongoio_get_instance = cls.mongoio_patcher.start()
        cls.mock_mongoio_get_instance.return_value = MagicMock()

    @classmethod
    def tearDownClass(cls):
        cls.mongoio_patcher.stop()

    def setUp(self):
        self.test_cases_dir = os.path.join(os.path.dirname(__file__), '..', 'test_cases')
        self.config = Config.get_instance()
    
    def tearDown(self):
        pass
    
    def test_load_minimum_valid(self):
        """Test loading empty Collections directory structure."""
        test_case_dir = os.path.join(self.test_cases_dir, "minimum_valid")
        self.config.INPUT_FOLDER = test_case_dir        
        manager = ConfigManager()
        self.assertEqual(manager.load_errors, [], "Unexpected load errors in simple_valid test case")
        self.assertEqual(len(manager.collection_configs), 0, f"Unexpected number of collection configs {len(manager.collection_configs)}")

    def test_load_small_sample(self):
        """Test loading Small configuration."""
        test_case_dir = os.path.join(self.test_cases_dir, "small_sample")
        self.config.INPUT_FOLDER = test_case_dir        
        manager = ConfigManager()
        self.assertEqual(manager.load_errors, [], "Unexpected load errors in simple_valid test case")
        self.assertEqual(len(manager.collection_configs), 1, f"Unexpected number of collection configs {len(manager.collection_configs)}")
        self.assertIn("simple", manager.collection_configs)

    def test_load_large_sample(self):
        """Test loading large config"""
        test_case_dir = os.path.join(self.test_cases_dir, "large_sample")
        self.config.INPUT_FOLDER = test_case_dir        
        manager = ConfigManager()
        self.assertEqual(manager.load_errors, [], "Unexpected load errors in simple_valid test case")
        self.assertEqual(len(manager.collection_configs), 4, f"Unexpected number of collection configs {len(manager.collection_configs)}")
        self.assertIn("media", manager.collection_configs)
        self.assertIn("organization", manager.collection_configs)
        self.assertIn("search", manager.collection_configs)
        self.assertIn("user", manager.collection_configs)

    def test_non_parsable(self):
        """Test loading with non-parsable files"""
        test_case_dir = os.path.join(self.test_cases_dir, "non_parsable")
        self.config.INPUT_FOLDER = test_case_dir        
        manager = ConfigManager()
        self.assertEqual(len(manager.load_errors), 1, f"Unexpected load errors {manager.load_errors}")

    def test_load_test_data_bulk_write_error(self):
        """Test that _load_test_data properly handles bulk write errors."""
        from stage0_py_utils.mongo_utils.mongo_io import TestDataLoadError
        mock_details = {'writeErrors': [{'index': 0, 'code': 121, 'errmsg': 'Document failed validation'}]}
        self.mock_mongoio_get_instance.return_value.load_test_data.side_effect = TestDataLoadError(
            "Schema validation failed during test data load", details=mock_details
        )
        config_manager = ConfigManager()
        collection_name = "test_collection"
        test_data_file = "test.json"
        result = config_manager._load_test_data(collection_name, test_data_file)
        
        # Test structure rather than specific values
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["operation"], "load_test_data")
        self.assertEqual(result["collection"], collection_name)
        self.assertEqual(result["details_type"], "error")
        self.assertIn("test.json", result["details"]["test_data_file"])
        self.assertIn("message", result)  # Should have message field
        self.assertIn("details", result["details"])  # Should have details field

    def test_load_test_data_generic_error(self):
        """Test that _load_test_data properly handles generic errors."""
        self.mock_mongoio_get_instance.return_value.load_test_data.side_effect = Exception("File not found")
        config_manager = ConfigManager()
        collection_name = "test_collection"
        test_data_file = "test.json"
        result = config_manager._load_test_data(collection_name, test_data_file)
        
        # Test structure rather than specific values
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["operation"], "load_test_data")
        self.assertEqual(result["collection"], collection_name)
        self.assertEqual(result["details_type"], "error")
        self.assertIn("test.json", result["details"]["test_data_file"])
        self.assertIn("message", result)  # Should have message field

    def test_load_test_data_success(self):
        """Test that _load_test_data properly handles successful loads."""
        # Reset any previous side effects or return values
        self.mock_mongoio_get_instance.return_value.load_test_data.reset_mock()
        self.mock_mongoio_get_instance.return_value.load_test_data.side_effect = None
        mock_results = {
            "status": "success",
            "operation": "load_test_data",
            "collection": "test_collection",
            "documents_loaded": 5,
            "inserted_ids": ["id1", "id2", "id3", "id4", "id5"],
            "acknowledged": True
        }
        self.mock_mongoio_get_instance.return_value.load_test_data.return_value = mock_results
        config_manager = ConfigManager()
        collection_name = "test_collection"
        test_data_file = "test.json"
        result = config_manager._load_test_data(collection_name, test_data_file)
        
        # Test structure rather than specific values
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["operation"], "load_test_data")
        self.assertEqual(result["collection"], collection_name)
        self.assertEqual(result["details_type"], "test_data")
        self.assertIn("test.json", result["details"]["test_data_file"])
        self.assertIn("results", result["details"])  # Should have results field

    def test_process_collection_versions_structure(self):
        """Test that process_collection_versions returns the expected structure."""
        test_case_dir = os.path.join(self.test_cases_dir, "small_sample")
        self.config.INPUT_FOLDER = test_case_dir
        
        # Mock VersionManager.get_current_version to return a version that will be processed
        with patch('stage0_mongodb_api.managers.config_manager.VersionManager.get_current_version') as mock_get_version:
            mock_get_version.return_value = "simple.0.0.0.0"
            
            # Mock all the manager operations to return success
            with patch('stage0_mongodb_api.managers.config_manager.SchemaManager') as mock_schema_manager, \
                 patch('stage0_mongodb_api.managers.config_manager.IndexManager') as mock_index_manager, \
                 patch('stage0_mongodb_api.managers.config_manager.MigrationManager') as mock_migration_manager, \
                 patch('stage0_mongodb_api.managers.config_manager.VersionManager') as mock_version_manager:
                
                # Set up mock return values
                mock_schema_manager.return_value.remove_schema.return_value = {
                    "operation": "remove_schema", "collection": "simple", "status": "success"
                }
                mock_schema_manager.return_value.apply_schema.return_value = {
                    "operation": "apply_schema", "collection": "simple", "schema": {}, "status": "success"
                }
                mock_version_manager.return_value.update_version.return_value = {
                    "operation": "version_update", "collection": "simple", "version": "simple.1.0.0.1", "status": "success"
                }
                
                config_manager = ConfigManager()
                result = config_manager.process_collection_versions("simple")
                
                # Test that we get a list of operations
                self.assertIsInstance(result, list)
                self.assertGreater(len(result), 0)
                
                # Test that each operation has the expected structure
                for operation in result:
                    self.assertIsInstance(operation, dict)
                    self.assertIn("operation", operation)
                    self.assertIn("status", operation)
                    self.assertIn("collection", operation)
                    # Status should be the last property
                    self.assertEqual(list(operation.keys())[-1], "status")

    def test_process_all_collections_structure(self):
        """Test that process_all_collections returns the expected structure."""
        test_case_dir = os.path.join(self.test_cases_dir, "small_sample")
        self.config.INPUT_FOLDER = test_case_dir
        
        # Mock VersionManager.get_current_version to return a version that will be processed
        with patch('stage0_mongodb_api.managers.config_manager.VersionManager.get_current_version') as mock_get_version:
            mock_get_version.return_value = "simple.0.0.0.0"
            
            # Mock all the manager operations to return success
            with patch('stage0_mongodb_api.managers.config_manager.SchemaManager') as mock_schema_manager, \
                 patch('stage0_mongodb_api.managers.config_manager.IndexManager') as mock_index_manager, \
                 patch('stage0_mongodb_api.managers.config_manager.MigrationManager') as mock_migration_manager, \
                 patch('stage0_mongodb_api.managers.config_manager.VersionManager') as mock_version_manager:
                
                # Set up mock return values
                mock_schema_manager.return_value.remove_schema.return_value = {
                    "operation": "remove_schema", "collection": "simple", "status": "success"
                }
                mock_schema_manager.return_value.apply_schema.return_value = {
                    "operation": "apply_schema", "collection": "simple", "schema": {}, "status": "success"
                }
                mock_version_manager.return_value.update_version.return_value = {
                    "operation": "version_update", "collection": "simple", "version": "simple.1.0.0.1", "status": "success"
                }
                
                config_manager = ConfigManager()
                result = config_manager.process_all_collections()
                
                # Test that we get a dict mapping collection names to operation lists
                self.assertIsInstance(result, dict)
                self.assertIn("simple", result)
                self.assertIsInstance(result["simple"], list)
                
                # Test that each collection has operations
                for collection_name, operations in result.items():
                    self.assertIsInstance(operations, list)
                    self.assertGreater(len(operations), 0)
                    
                    # Test that each operation has the expected structure
                    for operation in operations:
                        self.assertIsInstance(operation, dict)
                        self.assertIn("operation", operation)
                        self.assertIn("status", operation)
                        # Status should be the last property
                        self.assertEqual(list(operation.keys())[-1], "status")

    def test_process_enumerators_success(self):
        """Test that _process_enumerators successfully processes enumerators."""
        test_case_dir = os.path.join(self.test_cases_dir, "small_sample")
        self.config.INPUT_FOLDER = test_case_dir
        self.config.ENUMERATORS_COLLECTION_NAME = "Enumerators"
        
        # Mock schema_manager to return test enumerators
        mock_enumerators = [
            {"version": 0, "enumerators": {}},
            {"version": 1, "enumerators": {"default_status": ["active", "archived"]}}
        ]
        
        # Reset and mock MongoIO upsert_document to return the input document
        self.mock_mongoio_get_instance.return_value.upsert_document.reset_mock()
        def upsert_side_effect(collection, filter, document):
            return document
        self.mock_mongoio_get_instance.return_value.upsert_document.side_effect = upsert_side_effect
        
        with patch('stage0_mongodb_api.managers.config_manager.SchemaManager') as mock_schema_manager_class:
            # Create a mock schema manager instance
            mock_schema_manager = MagicMock()
            mock_schema_manager.enumerators = mock_enumerators
            mock_schema_manager_class.return_value = mock_schema_manager
            
            config_manager = ConfigManager()
            result = config_manager._process_enumerators()
            
            # Test that we get the expected success structure
            self.assertEqual(result["operation"], "process_enumerators")
            self.assertEqual(result["collection"], "Enumerators")
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["details_type"], "success")
            self.assertEqual(result["details"]["processed_count"], 2)
            self.assertEqual(result["details"]["total_count"], 2)
            
            # Verify upsert_document was called for each enumerator
            self.assertEqual(
                self.mock_mongoio_get_instance.return_value.upsert_document.call_count, 2
            )

    def test_process_enumerators_file_not_found(self):
        """Test that _process_enumerators handles empty enumerators list."""
        test_case_dir = os.path.join(self.test_cases_dir, "minimum_valid")
        self.config.INPUT_FOLDER = test_case_dir
        self.config.ENUMERATORS_COLLECTION_NAME = "Enumerators"
        
        # Reset and mock MongoIO upsert_document to return success for empty array
        self.mock_mongoio_get_instance.return_value.upsert_document.reset_mock()
        self.mock_mongoio_get_instance.return_value.upsert_document.return_value = {
            "version": 0,
            "enumerators": {}
        }
        
        with patch('stage0_mongodb_api.managers.config_manager.SchemaManager') as mock_schema_manager_class:
            # Create a mock schema manager instance with empty enumerators
            mock_schema_manager = MagicMock()
            mock_schema_manager.enumerators = []
            mock_schema_manager_class.return_value = mock_schema_manager
            
            config_manager = ConfigManager()
            result = config_manager._process_enumerators()
            
            # Test that we get the expected success structure for empty list
            self.assertEqual(result["operation"], "process_enumerators")
            self.assertEqual(result["collection"], "Enumerators")
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["details_type"], "success")
            self.assertEqual(result["details"]["processed_count"], 0)
            self.assertEqual(result["details"]["total_count"], 0)
            
            # Verify upsert_document was not called since list is empty
            self.assertEqual(
                self.mock_mongoio_get_instance.return_value.upsert_document.call_count, 0
            )

    def test_process_enumerators_invalid_format(self):
        """Test that _process_enumerators handles invalid enumerators format."""
        test_case_dir = os.path.join(self.test_cases_dir, "minimum_valid")
        self.config.INPUT_FOLDER = test_case_dir
        self.config.ENUMERATORS_COLLECTION_NAME = "Enumerators"
        
        # Mock schema_manager to return invalid enumerators (not a list)
        mock_enumerators = {"invalid": "format"}  # Not a list
        
        with patch('stage0_mongodb_api.managers.config_manager.SchemaManager') as mock_schema_manager_class:
            # Create a mock schema manager instance with invalid enumerators
            mock_schema_manager = MagicMock()
            mock_schema_manager.enumerators = mock_enumerators
            mock_schema_manager_class.return_value = mock_schema_manager
            
            config_manager = ConfigManager()
            result = config_manager._process_enumerators()
            
            # Test that we get the expected error structure
            self.assertEqual(result["status"], "error")
            self.assertEqual(result["operation"], "process_enumerators")
            self.assertEqual(result["collection"], "Enumerators")
            self.assertEqual(result["details_type"], "error")
            self.assertIn("error", result["details"])
            self.assertEqual(result["details"]["expected"], "list")
            self.assertEqual(result["details"]["actual"], "dict")

    def test_process_all_collections_includes_enumerators(self):
        """Test that process_all_collections includes enumerators processing."""
        test_case_dir = os.path.join(self.test_cases_dir, "small_sample")
        self.config.INPUT_FOLDER = test_case_dir
        self.config.ENUMERATORS_COLLECTION_NAME = "Enumerators"
        
        # Mock schema_manager to return test enumerators
        mock_enumerators = [
            {"version": 0, "enumerators": {}},
            {"version": 1, "enumerators": {"default_status": ["active", "archived"]}}
        ]
        
        # Reset and mock MongoIO upsert_document to return the input document
        self.mock_mongoio_get_instance.return_value.upsert_document.reset_mock()
        def upsert_side_effect(collection, filter, document):
            return document
        self.mock_mongoio_get_instance.return_value.upsert_document.side_effect = upsert_side_effect
        
        # Mock VersionManager.get_current_version to return a version that will be processed
        with patch('stage0_mongodb_api.managers.config_manager.VersionManager.get_current_version') as mock_get_version:
            mock_get_version.return_value = "simple.0.0.0.0"
            
            # Mock all the manager operations to return success
            with patch('stage0_mongodb_api.managers.config_manager.SchemaManager') as mock_schema_manager, \
                 patch('stage0_mongodb_api.managers.config_manager.IndexManager') as mock_index_manager, \
                 patch('stage0_mongodb_api.managers.config_manager.MigrationManager') as mock_migration_manager, \
                 patch('stage0_mongodb_api.managers.config_manager.VersionManager') as mock_version_manager:
                
                # Set up mock schema manager with enumerators
                mock_schema_manager.return_value.enumerators = mock_enumerators
                mock_schema_manager.return_value.remove_schema.return_value = {
                    "operation": "remove_schema", "collection": "simple", "status": "success"
                }
                mock_schema_manager.return_value.apply_schema.return_value = {
                    "operation": "apply_schema", "collection": "simple", "schema": {}, "status": "success"
                }
                mock_version_manager.return_value.update_version.return_value = {
                    "operation": "version_update", "collection": "simple", "version": "simple.1.0.0.1", "status": "success"
                }
                
                config_manager = ConfigManager()
                result = config_manager.process_all_collections()
                
                # Test that we get a dict with enumerators and collections
                self.assertIsInstance(result, dict)
                self.assertIn("enumerators", result)
                self.assertIn("simple", result)
                
                # Test that enumerators processing is included
                enumerators_result = result["enumerators"]
                self.assertIsInstance(enumerators_result, list)
                self.assertEqual(len(enumerators_result), 2)  # enumerators result + overall_status
                self.assertEqual(enumerators_result[0]["operation"], "process_enumerators")
                self.assertEqual(enumerators_result[0]["status"], "success")

if __name__ == '__main__':
    unittest.main() 