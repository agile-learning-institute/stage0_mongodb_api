import unittest
from unittest.mock import patch, MagicMock
from stage0_mongodb_api.managers.version_manager import VersionManager
from stage0_py_utils import Config

class TestVersionManager(unittest.TestCase):
    """Test cases for VersionManager static methods."""

    @patch('stage0_mongodb_api.managers.version_manager.MongoIO.get_instance')
    def test_get_current_version_empty_collection_name(self, mock_mongo_instance):
        """Test getting current version with empty collection name"""
        with self.assertRaises(ValueError) as context:
            VersionManager.get_current_version("")
        self.assertEqual(str(context.exception), "Collection name cannot be empty")

    @patch('stage0_mongodb_api.managers.version_manager.MongoIO.get_instance')
    def test_get_current_version_existing(self, mock_mongo_instance):
        """Test getting current version when it exists"""
        mock_mongo = MagicMock()
        mock_mongo_instance.return_value = mock_mongo
        
        # Test with version without collection name
        mock_mongo.get_documents.return_value = [{
            "collection_name": "test_collection",
            "current_version": "1.2.3.4"  
        }]
        
        version = VersionManager.get_current_version("test_collection")
        self.assertEqual(version, "test_collection.1.2.3.4")
        
        # Test with version that already includes collection name
        mock_mongo.get_documents.return_value = [{
            "collection_name": "test_collection",
            "current_version": "test_collection.1.2.3.4"  
        }]
        
        version = VersionManager.get_current_version("test_collection")
        self.assertEqual(version, "test_collection.1.2.3.4")
        
        mock_mongo.get_documents.assert_called_with(
            Config.get_instance().VERSION_COLLECTION_NAME,
            match={"collection_name": "test_collection"}
        )

    @patch('stage0_mongodb_api.managers.version_manager.MongoIO.get_instance')
    def test_get_current_version_no_version_exists(self, mock_mongo_instance):
        """Test getting current version when no version exists"""
        mock_mongo = MagicMock()
        mock_mongo_instance.return_value = mock_mongo
        
        # Arrange
        mock_mongo.get_documents.return_value = []
        
        # Act
        version = VersionManager.get_current_version("test_collection")
        
        # Assert
        self.assertEqual(version, "test_collection.0.0.0.0")
        mock_mongo.get_documents.assert_called_once_with(
            Config.get_instance().VERSION_COLLECTION_NAME,
            match={"collection_name": "test_collection"}
        )

    @patch('stage0_mongodb_api.managers.version_manager.MongoIO.get_instance')
    def test_get_current_version_multiple_versions_exist(self, mock_mongo_instance):
        """Test getting current version when multiple versions exist"""
        mock_mongo = MagicMock()
        mock_mongo_instance.return_value = mock_mongo
        
        # Arrange
        mock_mongo.get_documents.return_value = [
            {"collection_name": "test_collection", "current_version": "1.2.3.4"},
            {"collection_name": "test_collection", "current_version": "1.2.3.5"}
        ]
        
        # Act & Assert
        with self.assertRaises(RuntimeError) as context:
            VersionManager.get_current_version("test_collection")
        self.assertEqual(str(context.exception), "Multiple versions found for collection: test_collection")

    @patch('stage0_mongodb_api.managers.version_manager.MongoIO.get_instance')
    def test_get_current_version_invalid_document(self, mock_mongo_instance):
        """Test getting current version when document is invalid"""
        mock_mongo = MagicMock()
        mock_mongo_instance.return_value = mock_mongo
        
        # Arrange
        mock_mongo.get_documents.return_value = [{
            "collection_name": "test_collection"
            # Missing current_version field
        }]
        
        # Act & Assert
        with self.assertRaises(RuntimeError) as context:
            VersionManager.get_current_version("test_collection")
        self.assertEqual(str(context.exception), "Invalid version document for collection: test_collection")

    @patch('stage0_mongodb_api.managers.version_manager.MongoIO.get_instance')
    def test_update_version_empty_collection_name(self, mock_mongo_instance):
        """Test updating version with empty collection name"""
        with self.assertRaises(ValueError) as context:
            VersionManager.update_version("", "1.2.3.4")
        self.assertEqual(str(context.exception), "Collection name cannot be empty")

    @patch('stage0_mongodb_api.managers.version_manager.MongoIO.get_instance')
    def test_update_version_valid(self, mock_mongo_instance):
        """Test updating version with valid version string"""
        mock_mongo = MagicMock()
        mock_mongo_instance.return_value = mock_mongo
        
        # Test with version without collection name
        mock_mongo.upsert_document.return_value = True
        
        result = VersionManager.update_version("test_collection", "1.2.3.4")
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["operation"], "version_update")
        self.assertEqual(result["collection"], "test_collection")
        self.assertEqual(result["details_type"], "version")
        self.assertEqual(result["details"]["version"], "test_collection.1.2.3.4")
        
        # Test with version that already includes collection name
        result = VersionManager.update_version("test_collection", "test_collection.1.2.3.4")
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["operation"], "version_update")
        self.assertEqual(result["collection"], "test_collection")
        self.assertEqual(result["details_type"], "version")
        self.assertEqual(result["details"]["version"], "test_collection.1.2.3.4")
        
        mock_mongo.upsert_document.assert_called_with(
            Config.get_instance().VERSION_COLLECTION_NAME,
            match={"collection_name": "test_collection"},
            data={"collection_name": "test_collection", "current_version": "test_collection.1.2.3.4"}
        )

    @patch('stage0_mongodb_api.managers.version_manager.MongoIO.get_instance')
    def test_update_version_invalid(self, mock_mongo_instance):
        """Test updating version with invalid version string"""
        # Arrange
        invalid_versions = [
            "1.2.3.4.5.6",  # Too many components
            "a.b.c.d",    # Non-numeric
            "1.2.3.",     # Trailing dot
            "",           # Empty string
            "1.2.3.4.",   # Trailing dot with schema
            "1..2.3",     # Double dot
            ".1.2.3",     # Leading dot
            "1000.0.0.0", # Exceeds MAX_VERSION
            "user.1.2.3", # Collection with too few components
            "user.1.2.3.4.5", # Collection with too many components
            "user..1.2.3.4", # Collection with double dot
            "user.1.2.3.4.", # Collection with trailing dot
            ".user.1.2.3.4", # Collection with leading dot
        ]
        
        # Act & Assert
        for invalid_version in invalid_versions:
            with self.assertRaises(ValueError):
                VersionManager.update_version("test_collection", invalid_version)

    @patch('stage0_mongodb_api.managers.version_manager.MongoIO.get_instance')
    def test_update_version_failed_upsert(self, mock_mongo_instance):
        """Test updating version when upsert fails"""
        mock_mongo = MagicMock()
        mock_mongo_instance.return_value = mock_mongo
        
        # Arrange
        mock_mongo.upsert_document.return_value = None
        
        # Act & Assert
        with self.assertRaises(RuntimeError) as context:
            VersionManager.update_version("test_collection", "1.2.3.4")
        self.assertEqual(str(context.exception), "Failed to update version for collection: test_collection")

if __name__ == '__main__':
    unittest.main()
