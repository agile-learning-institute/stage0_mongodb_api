import unittest
from unittest.mock import Mock, patch
from configurator.utils.version_manager import VersionManager
from configurator.utils.configurator_exception import ConfiguratorException
from configurator.utils.mongo_io import MongoIO
from configurator.utils.config import Config
from configurator.utils.version_number import VersionNumber


class TestVersionManager(unittest.TestCase):
    """Test cases for VersionManager class
    NOTE: Config is never mocked in these tests. The real Config singleton is used, and config values are set/reset in setUp/tearDown.
    """

    def setUp(self):
        """Set up test fixtures"""
        self.mock_mongo_io = Mock(spec=MongoIO)
        self.collection_name = "test_collection"
        # Get the actual config value
        self.config = Config.get_instance()
        self.version_collection_name = self.config.VERSION_COLLECTION_NAME

    def test_get_current_version_no_versions_found(self):
        """Test get_current_version when no versions are found in database"""
        # Mock empty result from database
        self.mock_mongo_io.get_documents.return_value = []
        
        result = VersionManager.get_current_version(self.mock_mongo_io, self.collection_name)
        
        # Verify the expected default version is returned
        self.assertIsInstance(result, VersionNumber)
        self.assertEqual(str(result), f"{self.collection_name}.0.0.0.yaml")
        
        # Verify mongo_io.get_documents was called correctly
        self.mock_mongo_io.get_documents.assert_called_once_with(
            self.version_collection_name,
            match={"collection_name": self.collection_name}
        )

    def test_get_current_version_single_version_found(self):
        """Test get_current_version when a single version is found"""
        # Mock single version document from database
        version_doc = {"collection_name": self.collection_name, "current_version": "1.2.3.4"}
        self.mock_mongo_io.get_documents.return_value = [version_doc]
        
        result = VersionManager.get_current_version(self.mock_mongo_io, self.collection_name)
        
        # Verify the version is returned as a VersionNumber
        self.assertIsInstance(result, VersionNumber)
        self.assertEqual(str(result), f"{self.collection_name}.1.2.3.yaml")
        
        # Verify mongo_io.get_documents was called correctly
        self.mock_mongo_io.get_documents.assert_called_once_with(
            self.version_collection_name,
            match={"collection_name": self.collection_name}
        )

    def test_get_current_version_multiple_versions_found(self):
        """Test get_current_version when multiple versions are found (should raise exception)"""
        # Mock multiple version documents from database
        version_docs = [
            {"collection_name": self.collection_name, "current_version": "1.2.3.4"},
            {"collection_name": self.collection_name, "current_version": "1.2.3.5"}
        ]
        self.mock_mongo_io.get_documents.return_value = version_docs
        
        # Verify exception is raised
        with self.assertRaises(ConfiguratorException) as context:
            VersionManager.get_current_version(self.mock_mongo_io, self.collection_name)
        
        # Verify exception message
        self.assertIn(f"Multiple versions found for collection: {self.collection_name}", str(context.exception))
        
        # Verify the exception has the correct event data
        self.assertEqual(context.exception.event.type, "GET_CURRENT_VERSION")
        self.assertEqual(context.exception.event.data, version_docs)

    def test_get_current_version_none_result(self):
        """Test get_current_version when database returns None"""
        # Mock None result from database
        self.mock_mongo_io.get_documents.return_value = None
        
        result = VersionManager.get_current_version(self.mock_mongo_io, self.collection_name)
        
        # Verify the expected default version is returned
        self.assertIsInstance(result, VersionNumber)
        self.assertEqual(str(result), f"{self.collection_name}.0.0.0.yaml")

    def test_update_version_new_version(self):
        """Test update_version for a new version"""
        # Mock upsert to return a document
        mock_version_doc = {"collection_name": self.collection_name, "current_version": "1.2.3.4"}
        self.mock_mongo_io.upsert.return_value = mock_version_doc
        
        # Mock get_current_version to return the updated version
        self.mock_mongo_io.get_documents.return_value = [{"current_version": "1.2.3.4"}]
        
        result = VersionManager.update_version(self.mock_mongo_io, self.collection_name, "1.2.3.4")
        
        # Verify the result
        self.assertIsInstance(result, VersionNumber)
        self.assertEqual(str(result), f"{self.collection_name}.1.2.3.yaml")
        
        # Verify upsert was called correctly
        self.mock_mongo_io.upsert.assert_called_once_with(
            self.version_collection_name,
            match={"collection_name": self.collection_name},
            data={"collection_name": self.collection_name, "current_version": "1.2.3.4"}
        )

    def test_update_version_existing_version(self):
        """Test update_version for an existing version"""
        # Mock upsert to return a document
        mock_version_doc = {"collection_name": self.collection_name, "current_version": "2.0.0.1"}
        self.mock_mongo_io.upsert.return_value = mock_version_doc
        
        # Mock get_current_version to return the updated version
        self.mock_mongo_io.get_documents.return_value = [{"current_version": "2.0.0.1"}]
        
        result = VersionManager.update_version(self.mock_mongo_io, self.collection_name, "2.0.0.1")
        
        # Verify the result
        self.assertIsInstance(result, VersionNumber)
        self.assertEqual(str(result), f"{self.collection_name}.2.0.0.yaml")
        
        # Verify upsert was called correctly
        self.mock_mongo_io.upsert.assert_called_once_with(
            self.version_collection_name,
            match={"collection_name": self.collection_name},
            data={"collection_name": self.collection_name, "current_version": "2.0.0.1"}
        )

    def test_update_version_invalid_version_format(self):
        """Test update_version with invalid version format"""
        # Mock upsert to raise an exception due to invalid version
        self.mock_mongo_io.upsert.side_effect = Exception("Invalid version format")
        
        # Verify exception is raised when trying to create VersionNumber with invalid format
        with self.assertRaises(ConfiguratorException):
            VersionManager.update_version(self.mock_mongo_io, self.collection_name, "invalid.version")

    def test_get_current_version_with_different_collection_names(self):
        """Test get_current_version with different collection names"""
        collection_names = ["users", "products", "orders", "inventory"]
        
        for collection_name in collection_names:
            with self.subTest(collection_name=collection_name):
                # Mock empty result for each collection
                self.mock_mongo_io.get_documents.return_value = []
                
                result = VersionManager.get_current_version(self.mock_mongo_io, collection_name)
                
                # Verify the expected default version is returned
                self.assertIsInstance(result, VersionNumber)
                self.assertEqual(str(result), f"{collection_name}.0.0.0.yaml")
                
                # Verify the correct collection name was used in the query
                self.mock_mongo_io.get_documents.assert_called_with(
                    self.version_collection_name,
                    match={"collection_name": collection_name}
                )

    def test_version_lifecycle(self):
        """Test complete version lifecycle: get current, update, get updated"""
        # Step 1: Get current version (no versions exist)
        self.mock_mongo_io.get_documents.return_value = []
        current_version = VersionManager.get_current_version(self.mock_mongo_io, self.collection_name)
        self.assertIsInstance(current_version, VersionNumber)
        self.assertEqual(str(current_version), f"{self.collection_name}.0.0.0.yaml")
        
        # Step 2: Update to a new version
        self.mock_mongo_io.upsert.return_value = {"collection_name": self.collection_name, "current_version": "1.0.0.1"}
        self.mock_mongo_io.get_documents.return_value = [{"current_version": "1.0.0.1"}]
        
        updated_version = VersionManager.update_version(self.mock_mongo_io, self.collection_name, "1.0.0.1")
        self.assertIsInstance(updated_version, VersionNumber)
        self.assertEqual(str(updated_version), f"{self.collection_name}.1.0.0.yaml")
        
        # Step 3: Get current version again (should return the updated version)
        self.mock_mongo_io.get_documents.return_value = [{"current_version": "1.0.0.1"}]
        final_version = VersionManager.get_current_version(self.mock_mongo_io, self.collection_name)
        self.assertIsInstance(final_version, VersionNumber)
        self.assertEqual(str(final_version), f"{self.collection_name}.1.0.0.yaml")

    def test_mongo_io_method_calls(self):
        """Test that MongoIO methods are called with correct parameters"""
        # Test get_documents call
        self.mock_mongo_io.get_documents.return_value = []
        VersionManager.get_current_version(self.mock_mongo_io, self.collection_name)
        
        # Verify get_documents was called with correct parameters
        self.mock_mongo_io.get_documents.assert_called_once_with(
            self.version_collection_name,
            match={"collection_name": self.collection_name}
        )
        
        # Reset mock for next test
        self.mock_mongo_io.reset_mock()
        
        # Test upsert call
        self.mock_mongo_io.upsert.return_value = {"collection_name": self.collection_name, "current_version": "1.0.0.1"}
        self.mock_mongo_io.get_documents.return_value = [{"current_version": "1.0.0.1"}]
        
        VersionManager.update_version(self.mock_mongo_io, self.collection_name, "1.0.0.1")
        
        # Verify upsert was called with correct parameters
        self.mock_mongo_io.upsert.assert_called_once_with(
            self.version_collection_name,
            match={"collection_name": self.collection_name},
            data={"collection_name": self.collection_name, "current_version": "1.0.0.1"}
        )


if __name__ == '__main__':
    unittest.main() 