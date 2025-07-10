import unittest
from unittest.mock import patch, MagicMock, Mock
from configurator.services.enumerator_service import Enumerators, Enumerations
from configurator.utils.configurator_exception import ConfiguratorException, ConfiguratorEvent

class TestEnumerators(unittest.TestCase):
    @patch('configurator.services.enumerator_service.FileIO.get_document')
    def test_init_with_none_data_loads_file(self, mock_get_document):
        """Test Enumerators initialization with None data loads from file."""
        mock_get_document.return_value = [{"version": 0, "enumerators": {}}]
        enum = Enumerators(None)
        self.assertEqual(enum.dict, [{"version": 0, "enumerators": {}}])
        mock_get_document.assert_called_once_with("test_data", "enumerators.json")

    def test_init_with_data(self):
        """Test Enumerators initialization with provided data."""
        data = [{"version": 0, "enumerators": {}}]
        enum = Enumerators(data)
        self.assertEqual(enum.dict, data)

    @patch('configurator.services.enumerator_service.FileIO.put_document')
    @patch('configurator.services.enumerator_service.FileIO.get_document')
    def test_save_success_with_changes(self, mock_get_document, mock_put_document):
        """Test successful save with file comparison showing changes."""
        # Arrange
        original_data = [{"version": 0, "enumerators": {"old": {"value": 1}}}]
        cleaned_data = [{"version": 0, "enumerators": {"new": {"value": 2}}}]
        
        # Mock get_document to return different original and saved content
        mock_get_document.side_effect = [original_data, cleaned_data]
        
        # Mock put_document to return a File object
        mock_file = Mock()
        mock_file.name = "enumerators.json"
        mock_file.path = "/path/to/enumerators.json"
        mock_put_document.return_value = mock_file
        
        enum = Enumerators(cleaned_data)
        
        # Act
        result = enum.save()
        
        # Assert
        self.assertEqual(result, mock_file)
        
        # Verify FileIO calls
        mock_put_document.assert_called_once_with("test_data", "enumerators.json", cleaned_data)

    @patch('configurator.services.enumerator_service.FileIO.put_document')
    @patch('configurator.services.enumerator_service.FileIO.get_document')
    def test_save_success_no_changes(self, mock_get_document, mock_put_document):
        """Test successful save with no changes detected."""
        # Arrange
        same_data = [{"version": 0, "enumerators": {"same": {"value": 1}}}]
        
        # Mock get_document to return same content for original and saved
        mock_get_document.side_effect = [same_data, same_data]
        
        # Mock put_document to return a File object
        mock_file = Mock()
        mock_file.name = "enumerators.json"
        mock_file.path = "/path/to/enumerators.json"
        mock_put_document.return_value = mock_file
        
        enum = Enumerators(same_data)
        
        # Act
        result = enum.save()
        
        # Assert
        self.assertEqual(result, mock_file)
        
        # Verify FileIO calls
        mock_put_document.assert_called_once_with("test_data", "enumerators.json", same_data)

    @patch('configurator.services.enumerator_service.FileIO.put_document')
    @patch('configurator.services.enumerator_service.FileIO.get_document')
    def test_save_configurator_exception(self, mock_get_document, mock_put_document):
        """Test save when ConfiguratorException is raised during file operations."""
        # Arrange
        data = [{"version": 0, "enumerators": {}}]
        enum = Enumerators(data)
        
        # Mock put_document to raise ConfiguratorException
        event = ConfiguratorEvent("TEST-01", "TEST_ERROR")
        mock_put_document.side_effect = ConfiguratorException("Test error", event)
        
        # Act & Assert
        with self.assertRaises(ConfiguratorException) as cm:
            enum.save()
        
        self.assertIn("Failed to save enumerators", str(cm.exception))

    @patch('configurator.services.enumerator_service.FileIO.put_document')
    @patch('configurator.services.enumerator_service.FileIO.get_document')
    def test_save_general_exception(self, mock_get_document, mock_put_document):
        """Test save when general Exception is raised during file operations."""
        # Arrange
        data = [{"version": 0, "enumerators": {}}]
        enum = Enumerators(data)
        
        # Mock put_document to raise general Exception
        mock_put_document.side_effect = Exception("Unexpected error")
        
        # Act & Assert
        with self.assertRaises(ConfiguratorException) as cm:
            enum.save()
        
        self.assertIn("Failed to save enumerators", str(cm.exception))

    def test_version_returns_correct_version(self):
        """Test that version method returns the correct version."""
        data = [
            {"version": 0, "enumerators": {"a": 1}},
            {"version": 1, "enumerators": {"b": 2}}
        ]
        enum = Enumerators(data)
        # Test that version method returns the correct version
        result = enum.version(1)
        self.assertEqual(result.version, 1)
        self.assertEqual(result.enumerators, {"b": 2})

    def test_to_dict_returns_data(self):
        """Test that to_dict method returns the enumerators data."""
        data = [{"version": 0, "enumerators": {"test": {"value": 1}}}]
        enum = Enumerators(data)
        result = enum.to_dict()
        self.assertEqual(result, data)

class TestEnumerations(unittest.TestCase):
    def test_init_with_valid_data(self):
        """Test Enumerations initialization with valid data."""
        data = {
            "name": "test",
            "status": "active",
            "version": 1,
            "enumerators": {"foo": {"bar": 1}}
        }
        enum = Enumerations(data)
        self.assertEqual(enum.name, "test")
        self.assertEqual(enum.status, "active")
        self.assertEqual(enum.version, 1)
        self.assertEqual(enum.enumerators, {"foo": {"bar": 1}})

    def test_init_with_none_data_raises(self):
        """Test Enumerations initialization with None data raises ConfiguratorException."""
        with self.assertRaises(ConfiguratorException):
            Enumerations(None)

    def test_init_with_invalid_data_raises(self):
        """Test Enumerations initialization with invalid data raises ConfiguratorException."""
        with self.assertRaises(ConfiguratorException):
            Enumerations("invalid_data")

    def test_get_enum_values_success(self):
        """Test successful retrieval of enum values."""
        data = {
            "name": "test",
            "status": "active",
            "version": 1,
            "enumerators": {"foo": {"bar": 1, "baz": 2}}
        }
        enum = Enumerations(data)
        values = enum.get_enum_values("foo")
        self.assertIn("bar", values)
        self.assertIn("baz", values)

    def test_get_enum_values_invalid_name_raises(self):
        """Test that get_enum_values raises ConfiguratorException for invalid enum name."""
        data = {
            "name": "test",
            "status": "active",
            "version": 1,
            "enumerators": {"foo": {"bar": 1}}
        }
        enum = Enumerations(data)
        with self.assertRaises(ConfiguratorException):
            enum.get_enum_values("not_a_key")

    def test_get_enum_values_with_none_enumerators_raises(self):
        """Test that get_enum_values raises ConfiguratorException when enumerators is None."""
        data = {
            "name": "test",
            "status": "active",
            "version": 1,
            "enumerators": None
        }
        enum = Enumerations(data)
        with self.assertRaises(ConfiguratorException):
            enum.get_enum_values("foo")

if __name__ == '__main__':
    unittest.main() 