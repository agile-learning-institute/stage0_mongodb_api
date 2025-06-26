import unittest
from unittest.mock import patch, MagicMock
import os
from stage0_mongodb_api.services.collection_service import CollectionService, CollectionNotFoundError, CollectionProcessingError
from stage0_py_utils import Config

class TestCollectionServices(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Set up test input folder
        self.config = Config.get_instance()
        self.test_cases_dir = os.path.join(os.path.dirname(__file__), "..", "test_cases")

    @patch('stage0_mongodb_api.services.collection_service.ConfigManager')
    def test_list_collections_success(self, mock_config_manager):
        """Test listing all collections successfully."""
        mock_config_manager.return_value.collection_configs = {
            "simple": {
                "name": "simple",
                "versions": [
                    {"version": "1.0.0.1"},
                    {"version": "1.0.0.2"},
                    {"version": "1.0.0.3"}
                ]
            }
        }
        mock_config_manager.return_value.load_errors = None
        mock_config_manager.return_value.validate_configs.return_value = []
        with patch('stage0_mongodb_api.services.collection_service.VersionManager') as mock_version_manager:
            mock_version_manager.get_current_version.return_value = "simple.1.0.0.1"
            result = CollectionService.list_collections()
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result, list)
        self.assertEqual(result[0]["collection_name"], "simple")
        self.assertEqual(result[0]["version"], "simple.1.0.0.1")
        self.assertEqual(result[0]["targeted_version"], "simple.1.0.0.3")

    @patch('stage0_mongodb_api.services.collection_service.ConfigManager')
    def test_list_collections_load_error(self, mock_config_manager):
        """Test listing collections with load errors."""
        mock_config_manager.return_value.load_errors = [{"error": "load_error"}]
        with self.assertRaises(CollectionProcessingError) as context:
            CollectionService.list_collections()
        self.assertEqual(context.exception.collection_name, "collections")
        self.assertEqual(context.exception.errors, [{"error": "load_error"}])

    @patch('stage0_mongodb_api.services.collection_service.ConfigManager')
    def test_list_collections_validation_error(self, mock_config_manager):
        """Test listing collections with validation errors."""
        mock_config_manager.return_value.load_errors = None
        mock_config_manager.return_value.validate_configs.return_value = [{"error": "validation_error"}]
        with self.assertRaises(CollectionProcessingError) as context:
            CollectionService.list_collections()
        self.assertEqual(context.exception.collection_name, "collections")
        self.assertEqual(context.exception.errors, [{"error": "validation_error"}])

    @patch('stage0_mongodb_api.services.collection_service.ConfigManager')
    def test_get_collection_success(self, mock_config_manager):
        """Test getting a collection successfully."""
        mock_config_manager.return_value.load_errors = None
        mock_config_manager.return_value.validate_configs.return_value = []
        mock_config_manager.return_value.get_collection_config.return_value = {"name": "simple"}
        result = CollectionService.get_collection("simple")
        self.assertEqual(result, {"name": "simple"})

    @patch('stage0_mongodb_api.services.collection_service.ConfigManager')
    def test_get_collection_not_found(self, mock_config_manager):
        """Test getting a collection that does not exist."""
        mock_config_manager.return_value.load_errors = None
        mock_config_manager.return_value.validate_configs.return_value = []
        mock_config_manager.return_value.get_collection_config.return_value = None
        with self.assertRaises(CollectionNotFoundError):
            CollectionService.get_collection("nonexistent")

    @patch('stage0_mongodb_api.services.collection_service.ConfigManager')
    def test_get_collection_load_error(self, mock_config_manager):
        """Test getting a collection with load errors."""
        mock_config_manager.return_value.load_errors = [{"error": "load_error"}]
        with self.assertRaises(CollectionProcessingError) as context:
            CollectionService.get_collection("simple")
        self.assertEqual(context.exception.collection_name, "simple")
        self.assertEqual(context.exception.errors, [{"error": "load_error"}])

    @patch('stage0_mongodb_api.services.collection_service.ConfigManager')
    def test_get_collection_validation_error(self, mock_config_manager):
        """Test getting a collection with validation errors."""
        mock_config_manager.return_value.load_errors = None
        mock_config_manager.return_value.validate_configs.return_value = [{"error": "validation_error"}]
        with self.assertRaises(CollectionProcessingError) as context:
            CollectionService.get_collection("simple")
        self.assertEqual(context.exception.collection_name, "simple")
        self.assertEqual(context.exception.errors, [{"error": "validation_error"}])

    @patch('stage0_mongodb_api.services.collection_service.ConfigManager')
    def test_process_collections_success(self, mock_config_manager):
        """Test processing all collections successfully."""
        mock_config_manager.return_value.collection_configs = {
            "user": {"name": "user"},
            "organization": {"name": "organization"},
            "media": {"name": "media"},
            "search": {"name": "search"}
        }
        mock_config_manager.return_value.load_errors = None
        mock_config_manager.return_value.validate_configs.return_value = []
        with patch.object(CollectionService, 'process_collection', return_value={"status": "success", "collection": "user", "operations": []}) as mock_proc:
            result = CollectionService.process_collections()
        self.assertEqual(len(result), 4)
        mock_proc.assert_called()

    @patch('stage0_mongodb_api.services.collection_service.ConfigManager')
    def test_process_collections_with_error(self, mock_config_manager):
        """Test processing collections when an error occurs."""
        mock_config_manager.return_value.collection_configs = {
            "simple": {
                "name": "simple",
                "versions": ["1.0.0"]
            }
        }
        mock_config_manager.return_value.load_errors = None
        mock_config_manager.return_value.validate_configs.return_value = []
        with patch.object(CollectionService, 'process_collection', side_effect=Exception("Test error")):
            result = CollectionService.process_collections()
        self.assertEqual(len(result), 1)
        # Test structure rather than specific values
        self.assertIn("status", result[0])
        self.assertIn("collection", result[0])
        self.assertIn("message", result[0])
        self.assertEqual(result[0]["status"], "error")
        self.assertEqual(result[0]["collection"], "simple")

    @patch('stage0_mongodb_api.services.collection_service.ConfigManager')
    def test_process_collections_skips_not_found(self, mock_config_manager):
        """Test process_collections skips collections that raise CollectionNotFoundError."""
        mock_config_manager.return_value.collection_configs = {
            "user": {"name": "user"},
            "ghost": {"name": "ghost"}
        }
        mock_config_manager.return_value.load_errors = None
        mock_config_manager.return_value.validate_configs.return_value = []
        def side_effect(name, token=None):
            if name == "ghost":
                raise CollectionNotFoundError(name)
            return {"status": "success", "collection": name, "operations": []}
        with patch.object(CollectionService, 'process_collection', side_effect=side_effect):
            result = CollectionService.process_collections()
        self.assertEqual(len(result), 1)
        # Test structure rather than specific values
        self.assertIn("collection", result[0])
        self.assertEqual(result[0]["collection"], "user")

    @patch('stage0_mongodb_api.services.collection_service.ConfigManager')
    def test_process_collection_success(self, mock_config_manager):
        """Test processing a specific collection successfully."""
        mock_config_manager.return_value.load_errors = None
        mock_config_manager.return_value.validate_configs.return_value = []
        # Use the new consistent format
        mock_operations = [
            {
                "operation": "evaluate_version",
                "collection": "simple",
                "message": "Evaluating version 1.0.0.1",
                "status": "success"
            }
        ]
        mock_config_manager.return_value.process_collection_versions.return_value = mock_operations
        collection_name = "simple"
        result = CollectionService.process_collection(collection_name)
        # Test structure rather than specific values
        self.assertIn("status", result)
        self.assertIn("collection", result)
        self.assertIn("operations", result)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["collection"], collection_name)
        self.assertEqual(result["operations"], mock_operations)

    @patch('stage0_mongodb_api.services.collection_service.ConfigManager')
    def test_process_collection_not_found(self, mock_config_manager):
        """Test processing a non-existent collection."""
        mock_config_manager.return_value.load_errors = None
        mock_config_manager.return_value.validate_configs.return_value = []
        mock_config_manager.return_value.process_collection_versions.side_effect = ValueError("Collection 'nonexistent' not found in configurations")
        collection_name = "nonexistent"
        with self.assertRaises(CollectionNotFoundError):
            CollectionService.process_collection(collection_name)
        mock_config_manager.return_value.process_collection_versions.assert_called_once_with(collection_name)

    @patch('stage0_mongodb_api.services.collection_service.ConfigManager')
    def test_process_collection_processing_error(self, mock_config_manager):
        """Test process_collection raises CollectionProcessingError for generic errors."""
        mock_config_manager.return_value.load_errors = None
        mock_config_manager.return_value.validate_configs.return_value = []
        mock_config_manager.return_value.process_collection_versions.side_effect = Exception("Some error")
        with self.assertRaises(CollectionProcessingError) as context:
            CollectionService.process_collection("simple")
        self.assertEqual(context.exception.collection_name, "simple")
        self.assertEqual(context.exception.errors[0]["message"], "Some error")

    @patch('stage0_mongodb_api.services.collection_service.ConfigManager')
    def test_process_collection_returns_error_status_when_operations_fail(self, mock_config_manager):
        """Test that process_collection returns error status when operations contain errors."""
        # Arrange
        mock_config_manager.return_value.load_errors = None
        mock_config_manager.return_value.validate_configs.return_value = []
        
        # Mock operations that include an error using the new format
        mock_operations = [
            {
                "operation": "remove_schema",
                "collection": "test_collection",
                "message": "Schema removed successfully",
                "status": "success"
            },
            {
                "operation": "apply_schema",
                "collection": "test_collection",
                "message": "Schema validation failed",
                "details_type": "error",
                "details": {"error": "Schema validation failed"},
                "status": "error"
            },
            {
                "operation": "update_version",
                "collection": "test_collection",
                "message": "Version updated successfully",
                "status": "success"
            }
        ]
        mock_config_manager.return_value.process_collection_versions.return_value = mock_operations
        
        collection_name = "test_collection"

        # Act
        result = CollectionService.process_collection(collection_name)

        # Assert
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["collection"], collection_name)
        self.assertEqual(result["operations"], mock_operations)

    @patch('stage0_mongodb_api.services.collection_service.ConfigManager')
    def test_process_collection_returns_success_status_when_all_operations_succeed(self, mock_config_manager):
        """Test that process_collection returns success status when all operations succeed."""
        # Arrange
        mock_config_manager.return_value.load_errors = None
        mock_config_manager.return_value.validate_configs.return_value = []
        
        # Mock operations that all succeed using the new format
        mock_operations = [
            {
                "operation": "remove_schema",
                "collection": "test_collection",
                "message": "Schema removed successfully",
                "status": "success"
            },
            {
                "operation": "apply_schema",
                "collection": "test_collection",
                "message": "Schema applied successfully",
                "details_type": "schema",
                "details": {"schema": {}, "version": "1.0.0.1"},
                "status": "success"
            },
            {
                "operation": "update_version",
                "collection": "test_collection",
                "message": "Version updated successfully",
                "status": "success"
            }
        ]
        mock_config_manager.return_value.process_collection_versions.return_value = mock_operations
        
        collection_name = "test_collection"

        # Act
        result = CollectionService.process_collection(collection_name)

        # Assert
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["collection"], collection_name)
        self.assertEqual(result["operations"], mock_operations)

if __name__ == '__main__':
    unittest.main()
