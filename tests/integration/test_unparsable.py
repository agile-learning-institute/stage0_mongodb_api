from configurator.utils.config import Config
from configurator.utils.file_io import FileIO
from configurator.utils.configurator_exception import ConfiguratorException, ConfiguratorEvent
import unittest
import os

class TestUnparsableFiles(unittest.TestCase):
    """Integration tests using the failing_not_parsable folder to test unparsable file handling"""

    def setUp(self):
        os.environ['INPUT_FOLDER'] = "./tests/test_cases/failing_not_parsable"
        Config._instance = None
        self.config = Config.get_instance()

    def tearDown(self):
        # Clean up environment variable
        if 'INPUT_FOLDER' in os.environ:
            del os.environ['INPUT_FOLDER']
        Config._instance = None

    def test_unparsable_configuration_file(self):
        """Test that unparsable configuration files are properly detected and reported"""
        # Arrange
        config_file = "invalid_configuration.yaml"
        
        # Act & Assert
        with self.assertRaises(ConfiguratorException) as context:
            FileIO.get_document("configurations", config_file)
        
        # Verify the exception contains appropriate error information
        exception = context.exception
        self.assertIsInstance(exception.event, ConfiguratorEvent)
        self.assertIn("Failed to get document", str(exception))

    def test_unparsable_dictionary_file(self):
        """Test that unparsable dictionary files are properly detected and reported"""
        # Arrange
        dict_file = "invalid_dictionary.yaml"
        
        # Act & Assert
        with self.assertRaises(ConfiguratorException) as context:
            FileIO.get_document("dictionaries", dict_file)
        
        # Verify the exception contains appropriate error information
        exception = context.exception
        self.assertIsInstance(exception.event, ConfiguratorEvent)
        self.assertIn("Failed to get document", str(exception))

    def test_unparsable_enumerators_file(self):
        """Test that unparsable enumerators files are properly detected and reported"""
        # Arrange
        enum_file = "invalid_enumerators.yaml"
        
        # Act & Assert
        with self.assertRaises(ConfiguratorException) as context:
            FileIO.get_document("enumerators", enum_file)
        
        # Verify the exception contains appropriate error information
        exception = context.exception
        self.assertIsInstance(exception.event, ConfiguratorEvent)
        self.assertIn("Failed to get document", str(exception))

    def test_unparsable_migrations_file(self):
        """Test that unparsable migrations files are properly detected and reported"""
        # Arrange
        migration_file = "invalid_migrations.json"
        
        # Act & Assert
        with self.assertRaises(ConfiguratorException) as context:
            FileIO.get_document("migrations", migration_file)
        
        # Verify the exception contains appropriate error information
        exception = context.exception
        self.assertIsInstance(exception.event, ConfiguratorEvent)
        self.assertIn("Failed to get document", str(exception))

    def test_unparsable_test_data_file(self):
        """Test that unparsable test data files are properly detected and reported"""
        # Arrange
        test_data_file = "invalid_test_data.json"
        
        # Act & Assert
        with self.assertRaises(ConfiguratorException) as context:
            FileIO.get_document("test_data", test_data_file)
        
        # Verify the exception contains appropriate error information
        exception = context.exception
        self.assertIsInstance(exception.event, ConfiguratorEvent)
        self.assertIn("Failed to get document", str(exception))

    def test_unsupported_file_type(self):
        """Test that unsupported file types are properly detected and reported"""
        # Arrange
        unsupported_file = "test.txt"
        
        # Act & Assert
        with self.assertRaises(ConfiguratorException) as context:
            FileIO.get_document("configurations", unsupported_file)
        
        # Verify the exception contains appropriate error information
        exception = context.exception
        self.assertIsInstance(exception.event, ConfiguratorEvent)
        self.assertIn("UNSUPPORTED_FILE_TYPE", str(exception.event.type))

if __name__ == '__main__':
    unittest.main() 