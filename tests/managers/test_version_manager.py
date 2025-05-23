import unittest
from unittest.mock import patch, MagicMock
from stage0_mongodb_api.managers.version_manager import VersionManager, VersionNumber
from stage0_py_utils import Config

class TestVersionNumber(unittest.TestCase):
    def test_parse_version(self):
        """Test parsing of version strings"""
        # Test full version with schema version
        version = VersionNumber("1.2.3.4")
        self.assertEqual(version.parts, [1, 2, 3, 4])
        
        # Test partial version (should pad with zeros)
        version = VersionNumber("1.2.3")
        self.assertEqual(version.parts, [1, 2, 3, 0])
        
        version = VersionNumber("1.2")
        self.assertEqual(version.parts, [1, 2, 0, 0])
        
        # Test single number
        version = VersionNumber("1")
        self.assertEqual(version.parts, [1, 0, 0, 0])

    def test_invalid_version_constructor(self):
        """Test that invalid version strings raise ValueError in constructor"""
        invalid_versions = [
            "",           # Empty string
            "1.2.3.4.5", # Too many components
            "a.b.c.d",   # Non-numeric
            "1.2.3.",    # Trailing dot
            "1.2.3.4.",  # Trailing dot with schema
            "1..2.3",    # Double dot
            ".1.2.3",    # Leading dot
            "1.2.3.4a",  # Non-numeric in schema
            "1.2.3a.4",  # Non-numeric in patch
            "1000.0.0.0", # Exceeds MAX_VERSION
            "0.1000.0.0", # Exceeds MAX_VERSION
            "0.0.1000.0", # Exceeds MAX_VERSION
            "0.0.0.1000", # Exceeds MAX_VERSION
        ]
        
        for invalid_version in invalid_versions:
            with self.assertRaises(ValueError):
                VersionNumber(invalid_version)

    def test_version_comparison(self):
        """Test version comparison operators"""
        v1 = VersionNumber("1.2.3.4")
        v2 = VersionNumber("1.2.3.5")
        v3 = VersionNumber("1.2.3.4")
        v4 = VersionNumber("1.2.4.0")  # Different patch version
        v5 = VersionNumber("1.2.3.0")  # Missing schema version
        
        self.assertTrue(v1 < v2)  # Different schema version
        self.assertTrue(v1 < v4)  # Different patch version
        self.assertTrue(v5 < v1)  # Missing schema version
        self.assertFalse(v2 < v1)
        self.assertTrue(v1 == v3)
        self.assertFalse(v1 == v2)
        
        # Test string comparison
        self.assertTrue(v1 < "1.2.3.5")
        self.assertTrue(v1 == "1.2.3.4")

class TestVersionManager(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.mock_mongo = MagicMock()
        
        # Patch MongoIO instance
        self.mongo_patcher = patch('stage0_mongodb_api.managers.version_manager.MongoIO.get_instance')
        self.mock_mongo_instance = self.mongo_patcher.start()
        self.mock_mongo_instance.return_value = self.mock_mongo
        
        # Create VersionManager after mock is set up
        self.version_manager = VersionManager()

    def tearDown(self):
        """Clean up test fixtures"""
        self.mongo_patcher.stop()

    def test_get_current_version_empty_collection_name(self):
        """Test getting current version with empty collection name"""
        with self.assertRaises(ValueError) as context:
            self.version_manager.get_current_version("")
        self.assertEqual(str(context.exception), "Collection name cannot be empty")

    def test_get_current_version_existing(self):
        """Test getting current version when it exists"""
        # Arrange
        self.mock_mongo.get_documents.return_value = [{
            "collection_name": "test_collection",
            "current_version": "1.2.3.4"  
        }]
        
        # Act
        version = self.version_manager.get_current_version("test_collection")
        
        # Assert
        self.assertEqual(version, "1.2.3.4")
        self.mock_mongo.get_documents.assert_called_once_with(
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
        self.assertEqual(version, "0.0.0.0")
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
        # Arrange
        self.mock_mongo.upsert_document.return_value = True
        
        # Act
        result = self.version_manager.update_version("test_collection", "1.2.3.4")
        
        # Assert
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["operation"], "version_update")
        self.assertEqual(result["collection"], "test_collection")
        self.assertEqual(result["version"], "1.2.3.4")
        self.mock_mongo.upsert_document.assert_called_once_with(
            Config.get_instance().VERSION_COLLECTION_NAME,
            match={"collection_name": "test_collection"},
            data={"collection_name": "test_collection", "current_version": "1.2.3.4"}
        )

    def test_update_version_invalid(self):
        """Test updating version with invalid version string"""
        # Arrange
        invalid_versions = [
            "1.2.3.4.5",  # Too many components
            "a.b.c.d",    # Non-numeric
            "1.2.3.",     # Trailing dot
            "",           # Empty string
            "1.2.3.4.",   # Trailing dot with schema
            "1..2.3",     # Double dot
            ".1.2.3",     # Leading dot
            "1000.0.0.0", # Exceeds MAX_VERSION
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
