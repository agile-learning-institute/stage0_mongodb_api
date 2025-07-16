from configurator.utils.config import Config
from configurator.services.configuration_services import Configuration
from configurator.services.dictionary_services import Dictionary
from configurator.services.enumerator_service import Enumerators
from configurator.utils.configurator_exception import ConfiguratorException, ConfiguratorEvent
import unittest
import os
from unittest.mock import patch, Mock

class TestBadReferences(unittest.TestCase):
    """Integration tests using the failing_refs folder to test bad reference handling"""

    def setUp(self):
        os.environ['INPUT_FOLDER'] = "./tests/test_cases/failing_refs"
        Config._instance = None
        self.config = Config.get_instance()

    def tearDown(self):
        # Clean up environment variable
        if 'INPUT_FOLDER' in os.environ:
            del os.environ['INPUT_FOLDER']
        Config._instance = None

    def test_circular_reference_dictionary(self):
        """Test that circular references in dictionaries are properly detected and reported"""
        dict_file = "circular_ref.1.0.0.yaml"
        mock_enumerations = Mock()
        mock_enumerations.get_enum_values.return_value = []
        with self.assertRaises(ConfiguratorException) as context:
            dictionary = Dictionary(dict_file)
            dictionary.get_json_schema(mock_enumerations)
        exception = context.exception
        self.assertIsInstance(exception.event, ConfiguratorEvent)
        self.assertIn("circular", str(exception).lower())

    def test_missing_reference_dictionary(self):
        """Test that missing references in dictionaries are properly detected and reported"""
        dict_file = "missing_ref.1.0.0.yaml"
        mock_enumerations = Mock()
        mock_enumerations.get_enum_values.return_value = []
        with self.assertRaises(ConfiguratorException) as context:
            dictionary = Dictionary(dict_file)
            dictionary.get_json_schema(mock_enumerations)
        exception = context.exception
        self.assertIsInstance(exception.event, ConfiguratorEvent)
        # Accept either 'file not found' or 'missing' in the error message
        self.assertTrue(
            "file not found" in str(exception).lower() or
            "missing" in str(exception).lower() or
            "not found" in str(exception).lower()
        )

    def test_missing_type_reference(self):
        """Test that missing type references are properly detected and reported"""
        dict_file = "missing_type.1.0.0.yaml"
        mock_enumerations = Mock()
        mock_enumerations.get_enum_values.return_value = []
        with self.assertRaises(ConfiguratorException) as context:
            dictionary = Dictionary(dict_file)
            dictionary.get_json_schema(mock_enumerations)
        exception = context.exception
        self.assertIsInstance(exception.event, ConfiguratorEvent)
        self.assertIn("missing", str(exception).lower() or "not found", str(exception).lower())

    def test_missing_test_data_reference(self):
        """Test that a configuration referencing missing test data fails during processing"""
        config_file = "test_data.yaml"
        with self.assertRaises(ConfiguratorException) as context:
            configuration = Configuration(config_file)
            configuration.get_json_schema("1.0.0.0")
        exception = context.exception
        self.assertIsInstance(exception.event, ConfiguratorEvent)
        # The error should indicate that the test data file is missing
        self.assertTrue(
            "file not found" in str(exception).lower() or
            "missing" in str(exception).lower() or
            "not found" in str(exception).lower()
        )

    def test_missing_migration_reference(self):
        """Test that a configuration referencing missing migration data fails during processing"""
        config_file = "test_migrations.yaml"
        with self.assertRaises(ConfiguratorException) as context:
            configuration = Configuration(config_file)
            configuration.get_json_schema("1.0.0.0")
        exception = context.exception
        self.assertIsInstance(exception.event, ConfiguratorEvent)
        # The error should indicate that the migration file is missing
        self.assertTrue(
            "file not found" in str(exception).lower() or
            "missing" in str(exception).lower() or
            "not found" in str(exception).lower()
        )

if __name__ == '__main__':
    unittest.main() 