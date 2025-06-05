import unittest
from unittest.mock import patch, MagicMock
from stage0_mongodb_api.managers.version_manager import VersionManager
from stage0_py_utils import Config

class TestVersionManager(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.mock_mongo = MagicMock()
        
        # Patch MongoIO instance
        self.mongo_patcher = patch('stage0_mongodb_api.managers.version_manager.MongoIO.get_instance')
        self.mock_mongo_instance = self.mongo_patcher.start()
        self.mock_mongo_instance.return_value = self.mock_mongo
        
        # Patch SchemaManager to prevent file system access
        self.schema_manager_patcher = patch('stage0_mongodb_api.managers.version_manager.SchemaManager')
        self.mock_schema_manager = self.schema_manager_patcher.start()
        self.mock_schema_manager.return_value = MagicMock()
        
        # Create VersionManager after mocks are set up
        self.version_manager = VersionManager()

    def tearDown(self):
        """Clean up test fixtures"""
        self.mongo_patcher.stop()
        self.schema_manager_patcher.stop()

    def test_get_current_version_empty_collection_name(self):
        """Test getting current version with empty collection name"""
        with self.assertRaises(ValueError) as context:
            self.version_manager.get_current_version("")
        self.assertEqual(str(context.exception), "Collection name cannot be empty")

    def test_get_current_version_existing(self):
        """Test getting current version when it exists"""
        # Test with version without collection name
        self.mock_mongo.get_documents.return_value = [{
            "collection_name": "test_collection",
            "current_version": "1.2.3.4"  
        }]
        
        version = self.version_manager.get_current_version("test_collection")
        self.assertEqual(version, "test_collection.1.2.3.4")
        
        # Test with version that already includes collection name
        self.mock_mongo.get_documents.return_value = [{
            "collection_name": "test_collection",
            "current_version": "test_collection.1.2.3.4"  
        }]
        
        version = self.version_manager.get_current_version("test_collection")
        self.assertEqual(version, "test_collection.1.2.3.4")
        
        self.mock_mongo.get_documents.assert_called_with(
            Config.get_instance().VERSION_COLLECTION_NAME,
            match={"collection_name": "test_collection"}
        )

    def test_get_current_version_no_version_exists(self):
        """Test getting current version when no version exists"""
        # Arrange
        self.mock_mongo.get_documents.return_value = []
        
        # Act
        version = self.version_manager.get_current_version("test_collection")
        
        # Assert
        self.assertEqual(version, "test_collection.0.0.0.0")
        self.mock_mongo.get_documents.assert_called_once_with(
            Config.get_instance().VERSION_COLLECTION_NAME,
            match={"collection_name": "test_collection"}
        )

    def test_get_current_version_multiple_versions_exist(self):
        """Test getting current version when multiple versions exist"""
        # Arrange
        self.mock_mongo.get_documents.return_value = [
            {"collection_name": "test_collection", "current_version": "1.2.3.4"},
            {"collection_name": "test_collection", "current_version": "1.2.3.5"}
        ]
        
        # Act & Assert
        with self.assertRaises(RuntimeError) as context:
            self.version_manager.get_current_version("test_collection")
        self.assertEqual(str(context.exception), "Multiple versions found for collection: test_collection")

    def test_get_current_version_invalid_document(self):
        """Test getting current version when document is invalid"""
        # Arrange
        self.mock_mongo.get_documents.return_value = [{
            "collection_name": "test_collection"
            # Missing current_version field
        }]
        
        # Act & Assert
        with self.assertRaises(RuntimeError) as context:
            self.version_manager.get_current_version("test_collection")
        self.assertEqual(str(context.exception), "Invalid version document for collection: test_collection")

    def test_update_version_empty_collection_name(self):
        """Test updating version with empty collection name"""
        with self.assertRaises(ValueError) as context:
            self.version_manager.update_version("", "1.2.3.4")
        self.assertEqual(str(context.exception), "Collection name cannot be empty")

    def test_update_version_valid(self):
        """Test updating version with valid version string"""
        # Test with version without collection name
        self.mock_mongo.upsert_document.return_value = True
        
        result = self.version_manager.update_version("test_collection", "1.2.3.4")
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["operation"], "version_update")
        self.assertEqual(result["collection"], "test_collection")
        self.assertEqual(result["version"], "test_collection.1.2.3.4")
        
        # Test with version that already includes collection name
        result = self.version_manager.update_version("test_collection", "test_collection.1.2.3.4")
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["operation"], "version_update")
        self.assertEqual(result["collection"], "test_collection")
        self.assertEqual(result["version"], "test_collection.1.2.3.4")
        
        self.mock_mongo.upsert_document.assert_called_with(
            Config.get_instance().VERSION_COLLECTION_NAME,
            match={"collection_name": "test_collection"},
            data={"collection_name": "test_collection", "current_version": "test_collection.1.2.3.4"}
        )

    def test_update_version_invalid(self):
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
                self.version_manager.update_version("test_collection", invalid_version)

    def test_update_version_failed_upsert(self):
        """Test updating version when upsert fails"""
        # Arrange
        self.mock_mongo.upsert_document.return_value = None
        
        # Act & Assert
        with self.assertRaises(RuntimeError) as context:
            self.version_manager.update_version("test_collection", "1.2.3.4")
        self.assertEqual(str(context.exception), "Failed to update version for collection: test_collection")

if __name__ == '__main__':
    unittest.main()
