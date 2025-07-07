import unittest
from unittest.mock import patch, MagicMock
from configurator.services.configuration_services import Configuration
from configurator.utils.configurator_exception import ConfiguratorException


@patch('configurator.services.configuration_services.FileIO')
@patch('configurator.services.configuration_services.Dictionary')
@patch('configurator.services.configuration_services.Enumerators')
class TestConfigurationProcessing(unittest.TestCase):
    """Unit tests for Configuration service processing"""

    def test_basic_configuration_construction(self, mock_enumerators, mock_dictionary, mock_file_io):
        """Test basic Configuration construction with mocked dependencies"""
        # Setup mocks
        mock_file_io.get_document.return_value = {
            "name": "test_config",
            "description": "Test configuration",
            "versions": [
                {
                    "version": "1.0.0.1",
                    "drop_indexes": [],
                    "add_indexes": [],
                    "migrations": []
                }
            ]
        }
        
        mock_dict_instance = MagicMock()
        mock_dictionary.return_value = mock_dict_instance
        
        mock_enum_instance = MagicMock()
        mock_enumerators.return_value = mock_enum_instance
        
        # Test construction
        config = Configuration("test.yaml")
        
        # Verify mocks were called correctly
        mock_file_io.get_document.assert_called_once()
        # Dictionary is not instantiated during Configuration construction
        # mock_dictionary.assert_called_once_with("test.yaml", mock_file_io.get_document.return_value)
        # mock_enumerators.assert_called_once()
        
        # Verify basic attributes
        self.assertEqual(config.file_name, "test.yaml")
        self.assertEqual(config.name, "test_config")
        self.assertEqual(config.description, "Test configuration")
        self.assertEqual(len(config.versions), 1)

    def test_configuration_process_success(self, mock_enumerators, mock_dictionary, mock_file_io):
        """Test successful Configuration processing"""
        # Setup mocks
        mock_file_io.get_document.return_value = {
            "name": "test_config",
            "description": "Test configuration",
            "versions": [
                {
                    "version": "1.0.0.1",
                    "drop_indexes": [],
                    "add_indexes": [],
                    "migrations": []
                }
            ]
        }
        
        mock_dict_instance = MagicMock()
        mock_dict_instance.to_dict.return_value = {"processed": "dictionary"}
        mock_dictionary.return_value = mock_dict_instance
        
        mock_enum_instance = MagicMock()
        mock_enum_instance.to_dict.return_value = {"processed": "enumerators"}
        mock_enumerators.return_value = mock_enum_instance
        
        # Create and process configuration
        config = Configuration("test.yaml")
        result = config.process()
        
        # Verify result is a ConfiguratorEvent
        from configurator.utils.configurator_exception import ConfiguratorEvent
        self.assertIsInstance(result, ConfiguratorEvent)

    def test_configuration_construction_with_file_error(self, mock_enumerators, mock_dictionary, mock_file_io):
        """Test Configuration construction when FileIO raises an exception"""
        # Mock FileIO to raise an exception during construction
        mock_file_io.get_document.side_effect = ConfiguratorException("File not found", "FILE_NOT_FOUND")
        
        # Test that construction raises the expected exception
        with self.assertRaises(ConfiguratorException) as context:
            Configuration("test.yaml")
        
        self.assertEqual(str(context.exception), "File not found")

    def test_configuration_to_dict(self, mock_enumerators, mock_dictionary, mock_file_io):
        """Test Configuration to_dict method"""
        # Setup mocks
        mock_file_io.get_document.return_value = {
            "name": "test_config",
            "description": "Test configuration",
            "versions": [
                {
                    "version": "1.0.0.1",
                    "drop_indexes": [],
                    "add_indexes": [],
                    "migrations": []
                }
            ]
        }
        
        mock_dict_instance = MagicMock()
        mock_dict_instance.to_dict.return_value = {"dictionary": "data"}
        mock_dictionary.return_value = mock_dict_instance
        
        mock_enum_instance = MagicMock()
        mock_enum_instance.to_dict.return_value = {"enumerators": "data"}
        mock_enumerators.return_value = mock_enum_instance
        
        # Create configuration and test to_dict
        config = Configuration("test.yaml")
        result = config.to_dict()
        
        # Verify result structure
        self.assertIsInstance(result, dict)
        self.assertIn("name", result)
        self.assertIn("description", result)
        self.assertIn("versions", result)
        self.assertEqual(result["name"], "test_config")
        self.assertEqual(result["description"], "Test configuration")

    def test_configuration_with_document_parameter(self, mock_enumerators, mock_dictionary, mock_file_io):
        """Test Configuration construction with document parameter (bypasses FileIO)"""
        test_doc = {
            "name": "test_config_with_doc",
            "description": "Test configuration with doc",
            "versions": [
                {
                    "version": "1.0.0.1",
                    "drop_indexes": [],
                    "add_indexes": [],
                    "migrations": []
                }
            ]
        }
        
        mock_dict_instance = MagicMock()
        mock_dictionary.return_value = mock_dict_instance
        
        mock_enum_instance = MagicMock()
        mock_enumerators.return_value = mock_enum_instance
        
        # Create configuration with document
        config = Configuration("test.yaml", test_doc)
        
        # Verify FileIO was not called (since we passed document)
        mock_file_io.get_document.assert_not_called()
        
        # Verify basic attributes
        self.assertEqual(config.name, "test_config_with_doc")
        self.assertEqual(config.description, "Test configuration with doc")

    def test_configuration_file_not_found(self, mock_enumerators, mock_dictionary, mock_file_io):
        """Test Configuration construction when file is not found"""
        # Setup FileIO to raise an exception
        mock_file_io.get_document.side_effect = ConfiguratorException("File not found", "FILE_NOT_FOUND")
        
        # Test that construction raises the expected exception
        with self.assertRaises(ConfiguratorException) as context:
            Configuration("nonexistent.yaml")
        
        self.assertEqual(str(context.exception), "File not found")

    def test_configuration_process_returns_event(self, mock_enumerators, mock_dictionary, mock_file_io):
        """Test that Configuration.process() returns a properly structured event"""
        # Setup mocks
        mock_file_io.get_document.return_value = {
            "name": "test_config",
            "description": "Test configuration",
            "versions": [
                {
                    "version": "1.0.0.1",
                    "drop_indexes": [],
                    "add_indexes": [],
                    "migrations": []
                }
            ]
        }
        
        mock_dict_instance = MagicMock()
        mock_dict_instance.to_dict.return_value = {"name": "test_dict"}
        mock_dictionary.return_value = mock_dict_instance
        
        mock_enum_instance = MagicMock()
        mock_enum_instance.to_dict.return_value = {"status": "active"}
        mock_enumerators.return_value = mock_enum_instance
        
        # Create and process configuration
        config = Configuration("test.yaml")
        event = config.process()
        
        # Verify event is returned (real ConfiguratorEvent)
        from configurator.utils.configurator_exception import ConfiguratorEvent
        self.assertIsInstance(event, ConfiguratorEvent)


if __name__ == '__main__':
    unittest.main() 