import unittest
from configurator.services.configuration_services import Configuration, Version
from configurator.utils.version_number import VersionNumber
import os
import yaml
import json
from configurator.utils.config import Config


def load_yaml(path):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def set_config_input_folder(folder):
    os.environ['INPUT_FOLDER'] = folder
    Config._instance = None
    return Config.get_instance()

def clear_config():
    if 'INPUT_FOLDER' in os.environ:
        del os.environ['INPUT_FOLDER']
    Config._instance = None


class TestConfigurationOperations(unittest.TestCase):
    """Test configuration service operations"""

    def setUp(self):
        self.config = set_config_input_folder("./tests/test_cases/small_sample")

    def tearDown(self):
        clear_config()

    def test_configuration_loading(self):
        """Test loading configuration from YAML file"""
        config = Configuration("sample.yaml")
        
        self.assertEqual(config.name, "sample")
        self.assertEqual(config.file_name, "sample.yaml")
        self.assertEqual(len(config.versions), 1)
        
        # Test version details
        version = config.versions[0]
        self.assertEqual(version.collection_name, "sample")
        self.assertEqual(version.version_str, "1.0.0.1")
        self.assertEqual(version.test_data, "sample.1.0.0.1.json")

    def test_configuration_to_dict(self):
        """Test configuration serialization to dictionary"""
        config = Configuration("sample.yaml")
        config_dict = config.to_dict()
        
        self.assertEqual(config_dict["name"], "sample")
        self.assertEqual(len(config_dict["versions"]), 1)
        
        version_dict = config_dict["versions"][0]
        self.assertEqual(version_dict["version"], "1.0.0.1")
        self.assertEqual(version_dict["test_data"], "sample.1.0.0.1.json")

    def test_version_creation(self):
        """Test Version object creation and properties"""
        version_data = {
            "version": "1.0.0.1",
            "drop_indexes": ["old_index"],
            "add_indexes": ["new_index"],
            "migrations": ["migration1"],
            "test_data": "test.json"
        }
        
        version = Version("test_collection", version_data, Config.get_instance())
        
        self.assertEqual(version.collection_name, "test_collection")
        self.assertEqual(version.version_str, "1.0.0.1")
        self.assertEqual(version.drop_indexes, ["old_index"])
        self.assertEqual(version.add_indexes, ["new_index"])
        self.assertEqual(version.migrations, ["migration1"])
        self.assertEqual(version.test_data, "test.json")

    def test_version_equality(self):
        """Test Version object equality comparison"""
        version_data1 = {"version": "1.0.0.1", "drop_indexes": [], "add_indexes": [], "migrations": [], "test_data": "test.json"}
        version_data2 = {"version": "1.0.0.1", "drop_indexes": [], "add_indexes": [], "migrations": [], "test_data": "test.json"}
        version_data3 = {"version": "1.0.0.2", "drop_indexes": [], "add_indexes": [], "migrations": [], "test_data": "test.json"}
        
        version1 = Version("test_collection", version_data1, Config.get_instance())
        version2 = Version("test_collection", version_data2, Config.get_instance())
        version3 = Version("test_collection", version_data3, Config.get_instance())
        
        self.assertEqual(version1, version2)
        self.assertNotEqual(version1, version3)

    def test_version_to_dict(self):
        """Test Version serialization to dictionary"""
        version_data = {
            "version": "1.0.0.1",
            "drop_indexes": ["index1"],
            "add_indexes": ["index2"],
            "migrations": ["migration1"],
            "test_data": "test.json"
        }
        
        version = Version("test_collection", version_data, Config.get_instance())
        version_dict = version.to_dict()
        
        self.assertEqual(version_dict["version"], "1.0.0.1")
        self.assertEqual(version_dict["drop_indexes"], ["index1"])
        self.assertEqual(version_dict["add_indexes"], ["index2"])
        self.assertEqual(version_dict["migrations"], ["migration1"])
        self.assertEqual(version_dict["test_data"], "test.json")

    def test_version_number_parsing(self):
        """Test that Version correctly parses version numbers"""
        version_data = {"version": "1.0.0.1", "drop_indexes": [], "add_indexes": [], "migrations": [], "test_data": "test.json"}
        version = Version("test_collection", version_data, Config.get_instance())
        
        # Test that collection_version is a VersionNumber object
        self.assertIsInstance(version.collection_version, VersionNumber)
        self.assertEqual(str(version.collection_version), "test_collection.1.0.0.yaml")
        self.assertEqual(version.collection_version.get_enumerator_version(), 1)

    def test_configuration_with_multiple_versions(self):
        """Test configuration with multiple versions"""
        # Create a test configuration with multiple versions
        config_data = {
            "name": "multi_version",
            "title": "Multi Version Test",
            "description": "Test configuration with multiple versions",
            "versions": [
                {
                    "version": "1.0.0.0",
                    "drop_indexes": [],
                    "add_indexes": ["v1_index"],
                    "migrations": [],
                    "test_data": "v1_data.json"
                },
                {
                    "version": "1.0.0.1",
                    "drop_indexes": ["v1_index"],
                    "add_indexes": ["v2_index"],
                    "migrations": ["v2_migration"],
                    "test_data": "v2_data.json"
                }
            ]
        }
        
        # Test creating configuration from dict
        config = Configuration("test.yaml", config_data)
        
        self.assertEqual(config.name, "multi_version")
        self.assertEqual(len(config.versions), 2)
        
        # Test version ordering
        self.assertEqual(config.versions[0].version_str, "1.0.0.0")
        self.assertEqual(config.versions[1].version_str, "1.0.0.1")

    def test_get_json_schema_for_version(self):
        """Test getting JSON schema for a specific version"""
        config = Configuration("sample.yaml")
        
        # Test getting schema for existing version
        schema = config.get_json_schema("1.0.0.1")
        self.assertIsInstance(schema, dict)
        self.assertIn("type", schema)
        self.assertEqual(schema["type"], "object")

    def test_get_bson_schema_for_version(self):
        """Test getting BSON schema for a specific version"""
        config = Configuration("sample.yaml")
        
        # Test getting schema for existing version
        schema = config.get_bson_schema("1.0.0.1")
        self.assertIsInstance(schema, dict)
        self.assertIn("bsonType", schema)
        self.assertEqual(schema["bsonType"], "object")

    def test_get_schema_for_nonexistent_version(self):
        """Test error handling when requesting schema for non-existent version"""
        config = Configuration("sample.yaml")
        
        # Test getting schema for non-existent version
        with self.assertRaises(Exception):
            config.get_json_schema("2.0.0.0")
        
        with self.assertRaises(Exception):
            config.get_bson_schema("2.0.0.0")

    def test_version_enumerator_access(self):
        """Test accessing enumerator version from Version object"""
        version_data = {"version": "1.0.0.1", "drop_indexes": [], "add_indexes": [], "migrations": [], "test_data": "test.json"}
        version = Version("test_collection", version_data, Config.get_instance())
        
        # Test that we can access the enumerator version
        self.assertEqual(version.collection_version.get_enumerator_version(), 1)


if __name__ == '__main__':
    unittest.main() 