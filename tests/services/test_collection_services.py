import unittest
from unittest.mock import patch, MagicMock
import os
import yaml
from stage0_mongodb_api.services.collection_service import CollectionService
from stage0_py_utils import MongoIO, Config

class TestCollectionServices(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Set up test input folder
        self.config = Config.get_instance()
        self.config.INPUT_FOLDER = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'test_cases/large_sample'
        )
        
        # Create service instance with mocked VersionManager
        with patch('stage0_mongodb_api.services.collection_service.VersionManager') as mock_version_manager:
            self.mock_version_manager = mock_version_manager.return_value
            self.mock_version_manager.get_current_version.return_value = "1.0.0.1"
            self.service = CollectionService()

    def tearDown(self):
        """Clean up test fixtures after each test method."""
        pass
    
    def test_list_collections(self):
        """Test listing all collections."""
        # Act
        result = self.service.list_collections()

        # Assert
        self.assertEqual(len(result), 4)  # We have 4 collection files
        collection_names = {c["name"] for c in result}
        self.assertEqual(collection_names, {"user", "organization", "media", "search"})
        
        # Verify user collection structure
        user_collection = next(c for c in result if c["name"] == "user")
        self.assertEqual(user_collection["title"], "User Collection")
        self.assertEqual(user_collection["description"], "Collection for managing users")
        self.assertEqual(len(user_collection["versions"]), 3)
        self.assertEqual(user_collection["current_version"], "1.0.0.1")

    def test_process_collections_success(self):
        """Test processing all collections successfully."""
        # Arrange
        mock_operations = [
            {"status": "success", "operation": "schema_update"}
        ]
        self.mock_version_manager.process_versions.return_value = mock_operations

        # Act
        result = self.service.process_collections()

        # Assert
        self.assertEqual(len(result), 4)  # We have 4 collections
        for r in result:
            self.assertEqual(r["status"], "success")
            self.assertIn(r["collection"], ["user", "organization", "media", "search"])
            self.assertEqual(r["operations"], mock_operations)

    def test_process_collections_with_error(self):
        """Test processing collections when one fails."""
        # Arrange
        def mock_process_versions(collection_name, versions):
            if collection_name == "user":
                raise Exception("Test error")
            return [{"status": "success", "operation": "schema_update"}]
            
        self.mock_version_manager.process_versions.side_effect = mock_process_versions

        # Act
        result = self.service.process_collections()

        # Assert
        self.assertEqual(len(result), 4)
        user_result = next(r for r in result if r["collection"] == "user")
        self.assertEqual(user_result["status"], "error")
        self.assertIn("Test error", user_result["error"])
        
        # Other collections should succeed
        for r in result:
            if r["collection"] != "user":
                self.assertEqual(r["status"], "success")

    def test_process_collection_success(self):
        """Test processing a specific collection successfully."""
        # Arrange
        collection_name = "user"
        mock_operations = [
            {"status": "success", "operation": "schema_update"}
        ]
        self.mock_version_manager.process_versions.return_value = mock_operations

        # Act
        result = self.service.process_collection(collection_name)

        # Assert
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["collection"], collection_name)
        self.assertEqual(result["operations"], mock_operations)
        
        # Verify correct versions were passed to version manager
        user_collection = next(c for c in self.service.collections if c["name"] == "user")
        self.mock_version_manager.process_versions.assert_called_once_with(
            collection_name, user_collection["versions"]
        )

    def test_process_collection_not_found(self):
        """Test processing a non-existent collection."""
        # Arrange
        collection_name = "nonexistent"

        # Act
        result = self.service.process_collection(collection_name)

        # Assert
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["collection"], collection_name)
        self.assertEqual(result["error"], "Collection configuration not found")

if __name__ == '__main__':
    unittest.main()
