import json
import unittest
from configurator.utils.config import Config

class TestConfigDefaults(unittest.TestCase):

    def setUp(self):
        """Re-initialize the config for each test."""
        self.config = Config.get_instance()
        self.config.initialize()

    def test_default_string_properties(self):
        for key, default in self.config.config_strings.items():
            self.assertEqual(getattr(self.config, key), default)

    def test_default_int_properties(self):
        for key, default in self.config.config_ints.items():
            self.assertEqual(getattr(self.config, key), int(default))

    def test_default_boolean_properties(self):
        for key, default in self.config.config_booleans.items():
            self.assertEqual(getattr(self.config, key), (default.lower() == "true"))

    def test_default_string_secret_properties(self):
        for key, default in self.config.config_string_secrets.items():
            self.assertEqual(getattr(self.config, key), default)

    def test_to_dict(self):
        """Test the to_dict method of the Config class."""
        # Convert the config object to a dictionary
        result_dict = self.config.to_dict({})
        self.assertIsInstance(result_dict["config_items"], list)
        
    def test_default_string_ci(self):
        for key, default in {**self.config.config_strings, **self.config.config_ints}.items():
            self._test_config_default_value(key, default)

    def test_default_secret_ci(self):
        for key, default in {**self.config.config_string_secrets, **self.config.config_json_secrets}.items():
            self._test_config_default_value(key, "secret")

    def _test_config_default_value(self, config_name, expected_value):
        """Helper function to check default values."""
        items = self.config.config_items
        item = next((i for i in items if i['name'] == config_name), None)
        self.assertIsNotNone(item)
        self.assertEqual(item['name'], config_name)
        self.assertEqual(item['from'], "default")
        self.assertEqual(item['value'], expected_value)

if __name__ == '__main__':
    unittest.main()