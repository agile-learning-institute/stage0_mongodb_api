import unittest
import os
from configurator.utils.config import Config

class TestConfigFiles(unittest.TestCase):
    """Test Config file loading using api_config feature.
    NOTE: Config is never mocked in these tests. The real Config singleton is used.
    """

    def setUp(self):
        # Reset the Config singleton to ensure clean state
        Config._instance = None
        
        # Set INPUT_FOLDER to point to the test config files
        os.environ["INPUT_FOLDER"] = "./tests/test_cases/config_files/"
        
        # Initialize the Config object
        self.config = Config.get_instance()
        self.config.initialize()
        
        # Clean up environment variable
        del os.environ["INPUT_FOLDER"]

    def test_file_string_properties(self):
        """Test that string properties are loaded from api_config files."""
        self.assertEqual(self.config.MONGO_DB_NAME, "TEST_VALUE")

    def test_file_int_properties(self):
        """Test that integer properties are loaded from api_config files."""
        self.assertEqual(self.config.API_PORT, 9999)

    def test_file_boolean_properties(self):
        """Test that boolean properties are loaded from api_config files."""
        self.assertEqual(self.config.AUTO_PROCESS, True)

    def test_file_secret_properties(self):
        """Test that secret properties are loaded from api_config files."""
        self.assertEqual(self.config.MONGO_CONNECTION_STRING, "TEST_VALUE")

    def test_config_items_source(self):
        """Test that config items show correct source."""
        # Test that our test values show as coming from "file"
        test_configs = {
            "MONGO_DB_NAME": "TEST_VALUE",
            "API_PORT": "9999",
            "AUTO_PROCESS": "true",
            "MONGO_CONNECTION_STRING": "secret"  # Secret fields show "secret" not actual value
        }
        
        for config_name, expected_value in test_configs.items():
            item = next((i for i in self.config.config_items if i['name'] == config_name), None)
            self.assertIsNotNone(item, f"Config item {config_name} not found")
            self.assertEqual(item['from'], "file")
            self.assertEqual(item['value'], expected_value)

    def test_default_values_preserved(self):
        """Test that default values are preserved for non-test configs."""
        # Test that some default values are still used
        self.assertEqual(self.config.SPA_PORT, 9999)  # From file
        self.assertEqual(self.config.LOAD_TEST_DATA, True)  # From file

if __name__ == '__main__':
    unittest.main()