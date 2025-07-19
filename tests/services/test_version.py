import unittest
from unittest.mock import Mock, patch
from configurator.services.configuration_services import Version
from configurator.utils.configurator_exception import ConfiguratorException


class TestVersion(unittest.TestCase):
    """Test cases for Version class."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_config = Mock()
        self.mock_config.DICTIONARY_FOLDER = "dictionaries"
        self.mock_config.INPUT_FOLDER = "input"
        self.mock_config.MIGRATIONS_FOLDER = "migrations"
        self.mock_config.TEST_DATA_FOLDER = "test_data"
        self.mock_config.VERSION_COLLECTION_NAME = "CollectionVersions"

    def test_init_with_locked_true(self):
        """Test Version initialization with _locked set to True."""
        version_data = {
            "version": "1.0.0.1",
            "drop_indexes": ["old_index"],
            "add_indexes": [{"key": "new_field", "unique": True}],
            "migrations": ["migration1.json"],
            "test_data": "test_data.json",
            "_locked": True
        }
        
        version = Version("test_collection", version_data, self.mock_config)
        
        self.assertEqual(version.collection_name, "test_collection")
        self.assertEqual(version.version_str, "1.0.0.1")
        self.assertEqual(version.drop_indexes, ["old_index"])
        self.assertEqual(version.add_indexes, [{"key": "new_field", "unique": True}])
        self.assertEqual(version.migrations, ["migration1.json"])
        self.assertEqual(version.test_data, "test_data.json")
        self.assertTrue(version._locked)

    def test_init_with_locked_false(self):
        """Test Version initialization with _locked set to False."""
        version_data = {
            "version": "1.0.0.1",
            "_locked": False
        }
        
        version = Version("test_collection", version_data, self.mock_config)
        
        self.assertEqual(version.collection_name, "test_collection")
        self.assertEqual(version.version_str, "1.0.0.1")
        self.assertFalse(version._locked)

    def test_init_without_locked_defaults_to_false(self):
        """Test Version initialization without _locked field defaults to False."""
        version_data = {
            "version": "1.0.0.1"
        }
        
        version = Version("test_collection", version_data, self.mock_config)
        
        self.assertEqual(version.collection_name, "test_collection")
        self.assertEqual(version.version_str, "1.0.0.1")
        self.assertFalse(version._locked)

    def test_to_dict_with_locked_true(self):
        """Test to_dict method with _locked set to True."""
        version_data = {
            "version": "1.0.0.1",
            "drop_indexes": ["old_index"],
            "add_indexes": [{"key": "new_field", "unique": True}],
            "migrations": ["migration1.json"],
            "test_data": "test_data.json",
            "_locked": True
        }
        
        version = Version("test_collection", version_data, self.mock_config)
        result = version.to_dict()
        
        expected = {
            "version": "1.0.0.1",
            "drop_indexes": ["old_index"],
            "add_indexes": [{"key": "new_field", "unique": True}],
            "migrations": ["migration1.json"],
            "test_data": "test_data.json",
            "_locked": True
        }
        self.assertEqual(result, expected)

    def test_to_dict_with_locked_false(self):
        """Test to_dict method with _locked set to False."""
        version_data = {
            "version": "1.0.0.1",
            "drop_indexes": ["old_index"],
            "add_indexes": [{"key": "new_field", "unique": True}],
            "migrations": ["migration1.json"],
            "test_data": "test_data.json",
            "_locked": False
        }
        
        version = Version("test_collection", version_data, self.mock_config)
        result = version.to_dict()
        
        expected = {
            "version": "1.0.0.1",
            "drop_indexes": ["old_index"],
            "add_indexes": [{"key": "new_field", "unique": True}],
            "migrations": ["migration1.json"],
            "test_data": "test_data.json",
            "_locked": False
        }
        self.assertEqual(result, expected)

    def test_to_dict_without_locked_includes_false(self):
        """Test to_dict method without _locked in input includes False."""
        version_data = {
            "version": "1.0.0.1",
            "drop_indexes": ["old_index"],
            "add_indexes": [{"key": "new_field", "unique": True}],
            "migrations": ["migration1.json"],
            "test_data": "test_data.json"
        }
        
        version = Version("test_collection", version_data, self.mock_config)
        result = version.to_dict()
        
        expected = {
            "version": "1.0.0.1",
            "drop_indexes": ["old_index"],
            "add_indexes": [{"key": "new_field", "unique": True}],
            "migrations": ["migration1.json"],
            "test_data": "test_data.json",
            "_locked": False
        }
        self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main() 