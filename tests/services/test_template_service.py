import unittest
from unittest.mock import patch, MagicMock
from configurator.services.template_service import TemplateService
from configurator.utils.configurator_exception import ConfiguratorException, ConfiguratorEvent
import yaml
import os


def set_config_input_folder(folder):
    os.environ['INPUT_FOLDER'] = folder
    from configurator.utils.config import Config
    Config._instance = None
    return Config.get_instance()


def clear_config():
    if 'INPUT_FOLDER' in os.environ:
        del os.environ['INPUT_FOLDER']
    from configurator.utils.config import Config
    Config._instance = None


class TestTemplateService(unittest.TestCase):
    """Test cases for TemplateService"""

    def setUp(self):
        self.config = set_config_input_folder("tests/test_cases/small_sample")
        self.template_service = TemplateService()

    def tearDown(self):
        clear_config()

    def test_validate_collection_name_valid(self):
        """Test validation of valid collection names"""
        valid_names = ["test", "test123", "test_collection", "test-collection", "TestCollection"]
        for name in valid_names:
            # Should not raise exception
            self.template_service._validate_collection_name(name)

    def test_validate_collection_name_invalid(self):
        """Test validation of invalid collection names"""
        invalid_names = ["", " ", "test@collection", "test.collection", "test collection"]
        for name in invalid_names:
            with self.assertRaises(ConfiguratorException):
                self.template_service._validate_collection_name(name)

    def test_replace_placeholders(self):
        """Test placeholder replacement in templates"""
        content = "Hello {{collection_name}}, welcome to {{collection_name}} system"
        result = self.template_service._replace_placeholders(content, "test")
        expected = "Hello test, welcome to test system"
        self.assertEqual(result, expected)

    @patch('configurator.services.template_service.FileIO.get_document')
    def test_load_template_success(self, mock_get_document):
        """Test successful template loading"""
        mock_get_document.return_value = "template content"
        result = self.template_service._load_template("test.yaml")
        self.assertEqual(result, "template content")
        mock_get_document.assert_called_once_with("templates", "test.yaml")

    @patch('configurator.services.template_service.FileIO.get_document')
    def test_load_template_not_found(self, mock_get_document):
        """Test template loading when file not found"""
        mock_get_document.side_effect = Exception("File not found")
        with self.assertRaises(ConfiguratorException) as cm:
            self.template_service._load_template("missing.yaml")
        self.assertEqual(cm.exception.event.id, "TPL-01")
        self.assertEqual(cm.exception.event.type, "TEMPLATE_NOT_FOUND")

    def test_process_configuration_template(self):
        """Test configuration template processing"""
        with patch.object(self.template_service, '_load_template') as mock_load:
            mock_load.return_value = """
description: Collection for managing {{collection_name}}
name: {{collection_name}}
versions:
  - version: "0.0.1"
    test_data: {{collection_name}}.0.0.1.json
"""
            result = self.template_service.process_configuration_template("test_collection")
            
            expected = {
                "description": "Collection for managing test_collection",
                "name": "test_collection",
                "versions": [
                    {
                        "version": "0.0.1",
                        "test_data": "test_collection.0.0.1.json"
                    }
                ]
            }
            self.assertEqual(result, expected)

    def test_process_dictionary_template(self):
        """Test dictionary template processing"""
        with patch.object(self.template_service, '_load_template') as mock_load:
            mock_load.return_value = """
description: A {{collection_name}} collection for testing the schema system
type: object
properties:
  _id:
    description: The unique identifier for a {{collection_name}}
    type: identifier
    required: true
  name:
    description: The name of the {{collection_name}}
    type: word
    required: true
"""
            result = self.template_service.process_dictionary_template("test_collection")
            
            expected = {
                "description": "A test_collection collection for testing the schema system",
                "type": "object",
                "properties": {
                    "_id": {
                        "description": "The unique identifier for a test_collection",
                        "type": "identifier",
                        "required": True
                    },
                    "name": {
                        "description": "The name of the test_collection",
                        "type": "word",
                        "required": True
                    }
                }
            }
            self.assertEqual(result, expected)

    @patch('configurator.services.template_service.FileIO.get_document')
    @patch('configurator.services.template_service.FileIO.put_document')
    def test_create_collection_success(self, mock_put_document, mock_get_document):
        """Test successful collection creation"""
        # Mock template loading
        config_template = """
description: Collection for managing {{collection_name}}
name: {{collection_name}}
versions:
  - version: "0.0.1"
    test_data: {{collection_name}}.0.0.1.json
"""
        dict_template = """
description: A {{collection_name}} collection for testing the schema system
type: object
properties:
  _id:
    description: The unique identifier for a {{collection_name}}
    type: identifier
    required: true
"""
        
        def mock_get_side_effect(folder, filename):
            if filename == "configuration.yaml":
                return config_template
            elif filename == "dictionary.yaml":
                return dict_template
            elif filename in ["test_collection.yaml", "test_collection.0.0.1.yaml"]:
                # Simulate file not found
                event = ConfiguratorEvent("FIL-02", "FILE_NOT_FOUND", {"file_path": f"{folder}/{filename}"})
                raise ConfiguratorException(f"File not found: {folder}/{filename}", event)
            else:
                raise Exception("File not found")
        
        mock_get_document.side_effect = mock_get_side_effect
        
        result = self.template_service.create_collection("test_collection")
        
        expected = {
            "collection_name": "test_collection",
            "configuration_file": "test_collection.yaml",
            "dictionary_file": "test_collection.0.0.1.yaml"
        }
        self.assertEqual(result, expected)
        
        # Verify files were saved
        self.assertEqual(mock_put_document.call_count, 2)

    @patch('configurator.services.template_service.FileIO.get_document')
    def test_create_collection_configuration_exists(self, mock_get_document):
        """Test collection creation when configuration already exists"""
        # Mock that configuration file exists
        def mock_get_side_effect(folder, filename):
            if filename == "test_collection.yaml":
                return "existing content"  # File exists
            elif filename in ["configuration.yaml", "dictionary.yaml"]:
                return "template content"  # Templates exist
            else:
                # Simulate file not found
                event = ConfiguratorEvent("FIL-02", "FILE_NOT_FOUND", {"file_path": f"{folder}/{filename}"})
                raise ConfiguratorException(f"File not found: {folder}/{filename}", event)
        
        mock_get_document.side_effect = mock_get_side_effect
        
        with self.assertRaises(ConfiguratorException) as cm:
            self.template_service.create_collection("test_collection")
        self.assertEqual(cm.exception.event.id, "TPL-03")
        self.assertEqual(cm.exception.event.type, "CONFIGURATION_EXISTS")

    @patch('configurator.services.template_service.FileIO.get_document')
    def test_create_collection_dictionary_exists(self, mock_get_document):
        """Test collection creation when dictionary already exists"""
        # Mock that dictionary file exists
        def mock_get_side_effect(folder, filename):
            if filename == "test_collection.0.0.1.yaml":
                return "existing content"  # File exists
            elif filename in ["configuration.yaml", "dictionary.yaml"]:
                return "template content"  # Templates exist
            else:
                # Simulate file not found
                event = ConfiguratorEvent("FIL-02", "FILE_NOT_FOUND", {"file_path": f"{folder}/{filename}"})
                raise ConfiguratorException(f"File not found: {folder}/{filename}", event)
        
        mock_get_document.side_effect = mock_get_side_effect
        
        with self.assertRaises(ConfiguratorException) as cm:
            self.template_service.create_collection("test_collection")
        self.assertEqual(cm.exception.event.id, "TPL-03")
        self.assertEqual(cm.exception.event.type, "DICTIONARY_EXISTS")


if __name__ == '__main__':
    unittest.main() 