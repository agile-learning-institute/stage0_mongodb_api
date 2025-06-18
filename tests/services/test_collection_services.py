import unittest
from unittest.mock import patch, MagicMock
import os
from stage0_mongodb_api.services.collection_service import CollectionService
from stage0_py_utils import Config

class TestCollectionServices(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Set up test input folder
        self.config = Config.get_instance()
        self.test_cases_dir = os.path.join(os.path.dirname(__file__), "..", "test_cases")

    @patch('stage0_mongodb_api.services.collection_service.ConfigManager')
    def test_list_collections_small_sample(self, mock_config_manager):
        """Test listing all collections using simple data."""
        # Arrange
        mock_config_manager.return_value.collection_configs = {"simple": {}}
        
        # Act
        result = CollectionService.list_collections()

        # Assert
        self.assertEqual(len(result), 1)  # Small sample has 1 collection
        self.assertIsInstance(result, dict)
        self.assertIn("simple", result)

    @patch('stage0_mongodb_api.services.collection_service.ConfigManager')
    def test_process_collections(self, mock_config_manager):
        """Test processing all collections."""
        # Arrange
        mock_config_manager.return_value.collection_configs = {
            "user": {"name": "user"},
            "organization": {"name": "organization"},
            "media": {"name": "media"},
            "search": {"name": "search"}
        }
        mock_config_manager.return_value.process_collection_versions.return_value = [
            {"status": "success", "operation": "schema_update"},
            {"status": "success", "operation": "schema_update"},
            {"status": "success", "operation": "schema_update"},
            {"status": "success", "operation": "schema_update"},
        ]
        
        # Act
        result = CollectionService.process_collections()

        # Assert
        self.assertEqual(len(result), 4)
        self.assertEqual(result[0]["status"], "success")
        self.assertEqual(result[1]["status"], "success")
        self.assertEqual(result[2]["status"], "success")
        self.assertEqual(result[3]["status"], "success")

    @patch('stage0_mongodb_api.services.collection_service.ConfigManager')
    def test_process_collection_success(self, mock_config_manager):
        """Test processing a specific collection successfully."""
        # Arrange
        mock_config_manager.return_value.get_collection_config.return_value = {
            "name": "simple",
            "versions": ["1.0.0"]
        }
        mock_config_manager.return_value.process_collection_versions.return_value = [
            {"status": "success", "operation": "schema_update"}
        ]
        collection_name = "simple"

        # Act
        result = CollectionService.process_collection(collection_name)

        # Assert
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["collection"], collection_name)
        self.assertEqual(result["operations"], [{"status": "success", "operation": "schema_update"}])

    @patch('stage0_mongodb_api.services.collection_service.ConfigManager')
    def test_process_collection_not_found(self, mock_config_manager):
        """Test processing a non-existent collection."""
        # Arrange
        mock_config_manager.return_value.get_collection_config.return_value = None
        collection_name = "nonexistent"

        # Act
        result = CollectionService.process_collection(collection_name)

        # Assert
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["collection"], collection_name)
        self.assertEqual(result["error"], "Collection configuration not found")
        mock_config_manager.return_value.process_collection_versions.assert_not_called()
        mock_config_manager.return_value.get_collection_config.assert_called_once_with(collection_name)

    @patch('stage0_mongodb_api.services.collection_service.ConfigManager')
    def test_process_collections_with_error(self, mock_config_manager):
        """Test processing collections when an error occurs."""
        # Arrange
        mock_config_manager.return_value.collection_configs = {
            "simple": {
                "name": "simple",
                "versions": ["1.0.0"]
            }
        }
        mock_config_manager.return_value.process_collection_versions.side_effect = Exception("Test error")
        
        # Act
        result = CollectionService.process_collections()

        # Assert
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["status"], "error")
        self.assertEqual(result[0]["collection"], "simple")
        self.assertEqual(result[0]["error"], "Test error")

if __name__ == '__main__':
    unittest.main()
