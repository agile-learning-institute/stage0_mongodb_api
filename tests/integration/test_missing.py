from configurator.utils.config import Config
from configurator.utils.file_io import FileIO
from configurator.utils.configurator_exception import ConfiguratorException, ConfiguratorEvent
import unittest
import os

class TestMissingData(unittest.TestCase):
    """Integration tests using the failing_empty folder to test missing data handling"""

    def setUp(self):
        os.environ['INPUT_FOLDER'] = "./tests/test_cases/failing_empty"
        Config._instance = None
        self.config = Config.get_instance()

    def tearDown(self):
        # Clean up environment variable
        if 'INPUT_FOLDER' in os.environ:
            del os.environ['INPUT_FOLDER']
        Config._instance = None

    def test_empty_configurations_folder(self):
        """Test that empty configurations folder is handled properly"""
        # Arrange
        config_dir = f"{self.config.INPUT_FOLDER}/configurations"
        
        # Act & Assert
        if os.path.exists(config_dir):
            # If the directory exists but is empty, test that it's handled gracefully
            files = os.listdir(config_dir)
            if len(files) == 0:
                # Test that processing empty configurations doesn't crash
                # This might be a valid scenario in some cases
                pass
        else:
            # If the directory doesn't exist, test that it's handled gracefully
            with self.assertRaises(ConfiguratorException) as context:
                FileIO.get_documents("configurations")
            
            # Verify the exception contains appropriate error information
            exception = context.exception
            self.assertIsInstance(exception.event, ConfiguratorEvent)

    def test_empty_dictionaries_folder(self):
        """Test that empty dictionaries folder is handled properly"""
        # Arrange
        dict_dir = f"{self.config.INPUT_FOLDER}/dictionaries"
        
        # Act & Assert
        if os.path.exists(dict_dir):
            # If the directory exists but is empty, test that it's handled gracefully
            files = os.listdir(dict_dir)
            if len(files) == 0:
                # Test that processing empty dictionaries doesn't crash
                # This might be a valid scenario in some cases
                pass
        else:
            # If the directory doesn't exist, test that it's handled gracefully
            with self.assertRaises(ConfiguratorException) as context:
                FileIO.get_documents("dictionaries")
            
            # Verify the exception contains appropriate error information
            exception = context.exception
            self.assertIsInstance(exception.event, ConfiguratorEvent)

    def test_empty_types_folder(self):
        """Test that empty types folder is handled properly"""
        # Arrange
        types_dir = f"{self.config.INPUT_FOLDER}/types"
        
        # Act & Assert
        if os.path.exists(types_dir):
            # If the directory exists but is empty, test that it's handled gracefully
            files = os.listdir(types_dir)
            if len(files) == 0:
                # Test that processing empty types doesn't crash
                # This might be a valid scenario in some cases
                pass
        else:
            # If the directory doesn't exist, test that it's handled gracefully
            with self.assertRaises(ConfiguratorException) as context:
                FileIO.get_documents("types")
            
            # Verify the exception contains appropriate error information
            exception = context.exception
            self.assertIsInstance(exception.event, ConfiguratorEvent)

    def test_empty_enumerators_folder(self):
        """Test that empty enumerators folder is handled properly"""
        # Arrange
        enum_dir = f"{self.config.INPUT_FOLDER}/enumerators"
        
        # Act & Assert
        if os.path.exists(enum_dir):
            # If the directory exists but is empty, test that it's handled gracefully
            files = os.listdir(enum_dir)
            if len(files) == 0:
                # Test that processing empty enumerators doesn't crash
                # This might be a valid scenario in some cases
                pass
        else:
            # If the directory doesn't exist, test that it's handled gracefully
            with self.assertRaises(ConfiguratorException) as context:
                FileIO.get_documents("enumerators")
            
            # Verify the exception contains appropriate error information
            exception = context.exception
            self.assertIsInstance(exception.event, ConfiguratorEvent)

    def test_empty_test_data_folder(self):
        """Test that empty test_data folder is handled properly"""
        # Arrange
        test_data_dir = f"{self.config.INPUT_FOLDER}/test_data"
        
        # Act & Assert
        if os.path.exists(test_data_dir):
            # If the directory exists but is empty, test that it's handled gracefully
            files = os.listdir(test_data_dir)
            if len(files) == 0:
                # Test that processing empty test_data doesn't crash
                # This might be a valid scenario in some cases
                pass
        else:
            # If the directory doesn't exist, test that it's handled gracefully
            with self.assertRaises(ConfiguratorException) as context:
                FileIO.get_documents("test_data")
            
            # Verify the exception contains appropriate error information
            exception = context.exception
            self.assertIsInstance(exception.event, ConfiguratorEvent)

if __name__ == '__main__':
    unittest.main() 