import unittest
from unittest.mock import patch, Mock
from configurator.services.enumerator_service import Enumerators, Enumerations
from configurator.utils.configurator_exception import ConfiguratorException, ConfiguratorEvent


class TestEnumerators(unittest.TestCase):
    """Test cases for Enumerators class."""

    @patch('configurator.services.enumerator_service.FileIO.get_documents')
    def test_init_with_none_data_loads_file(self, mock_get_documents):
        """Test Enumerators initialization loads from files."""
        # Arrange
        mock_files = [Mock(file_name="test1.yaml"), Mock(file_name="test2.yaml")]
        mock_get_documents.return_value = mock_files
        
        with patch('configurator.services.enumerator_service.Enumerations') as mock_enumerations:
            mock_enum1 = Mock()
            mock_enum2 = Mock()
            mock_enumerations.side_effect = [mock_enum1, mock_enum2]
            
            # Act
            enum = Enumerators()
            
            # Assert
            mock_get_documents.assert_called_once()
            self.assertEqual(len(enum.enumerations), 2)
            self.assertEqual(enum.enumerations[0], mock_enum1)
            self.assertEqual(enum.enumerations[1], mock_enum2)

    @patch('configurator.services.enumerator_service.FileIO.get_documents')
    def test_getVersion_finds_version(self, mock_get_documents):
        """Test getVersion finds the correct version."""
        # Arrange
        mock_files = [Mock(file_name="test1.yaml")]
        mock_get_documents.return_value = mock_files
        
        with patch('configurator.services.enumerator_service.Enumerations') as mock_enumerations:
            mock_enum = Mock(version=1)
            mock_enumerations.return_value = mock_enum
            
            # Act
            enum = Enumerators()
            result = enum.getVersion(1)
            
            # Assert
            self.assertEqual(result, mock_enum)

    @patch('configurator.services.enumerator_service.FileIO.get_documents')
    def test_getVersion_not_found(self, mock_get_documents):
        """Test getVersion when version is not found."""
        # Arrange
        mock_files = [Mock(file_name="test1.yaml")]
        mock_get_documents.return_value = mock_files
        
        with patch('configurator.services.enumerator_service.Enumerations') as mock_enumerations:
            mock_enum = Mock(version=1)
            mock_enumerations.return_value = mock_enum
            
            # Act & Assert
            enum = Enumerators()
            with self.assertRaises(ConfiguratorException):
                enum.getVersion(999)

    def test_version_alias(self):
        """Test that version() is an alias for getVersion()."""
        # Arrange
        with patch('configurator.services.enumerator_service.FileIO.get_documents') as mock_get_documents:
            mock_files = [Mock(file_name="test1.yaml")]
            mock_get_documents.return_value = mock_files
            
            with patch('configurator.services.enumerator_service.Enumerations') as mock_enumerations:
                mock_enum = Mock(version=1)
                mock_enumerations.return_value = mock_enum
                
                enum = Enumerators()
                
                with patch.object(enum, 'getVersion') as mock_get_version:
                    mock_get_version.return_value = Mock()
                    
                    # Act
                    enum.version(1)
                    
                    # Assert
                    mock_get_version.assert_called_once_with(1)

    def test_lock_all(self):
        """Test that lock_all() locks all enumerations and returns a ConfiguratorEvent."""
        # Arrange
        with patch('configurator.services.enumerator_service.FileIO.get_documents') as mock_get_documents:
            mock_files = [Mock(file_name="test1.yaml"), Mock(file_name="test2.yaml")]
            mock_get_documents.return_value = mock_files
            
            with patch('configurator.services.enumerator_service.Enumerations') as mock_enumerations:
                mock_enum1 = Mock(file_name="test1.yaml")
                mock_enum2 = Mock(file_name="test2.yaml")
                mock_enumerations.side_effect = [mock_enum1, mock_enum2]
                
                # Act
                enum = Enumerators()
                result = enum.lock_all()
                
                # Assert
                from configurator.utils.configurator_exception import ConfiguratorEvent
                self.assertIsInstance(result, ConfiguratorEvent)
                # There should be a sub-event for each file
                sub_event_ids = [e.id for e in result.sub_events]
                self.assertIn("ENU-test1.yaml", sub_event_ids)
                self.assertIn("ENU-test2.yaml", sub_event_ids)
                # Each enumeration should be locked and saved
                self.assertTrue(mock_enum1._locked)
                self.assertTrue(mock_enum2._locked)
                mock_enum1.save.assert_called_once()
                mock_enum2.save.assert_called_once()


class TestEnumerations(unittest.TestCase):
    """Test cases for Enumerations class."""

    def test_init_with_none_data_loads_file(self):
        """Test Enumerations initialization with None data loads from file."""
        # Arrange
        with patch('configurator.services.enumerator_service.FileIO.get_document') as mock_get_document:
            mock_get_document.return_value = {
                "name": "test",
                "status": "active",
                "version": 1,
                "enumerators": {"test_enum": {"value1": True, "value2": False}},
                "_locked": True
            }
            
            # Act
            enum = Enumerations(data=None, file_name="test.yaml")
            
            # Assert
            self.assertEqual(enum.name, "test")
            self.assertEqual(enum.status, "active")
            self.assertEqual(enum.version, 1)
            self.assertEqual(enum.enumerators, {"test_enum": {"value1": True, "value2": False}})
            self.assertTrue(enum._locked)

    def test_init_with_invalid_data_raises(self):
        """Test Enumerations initialization with invalid data raises AttributeError."""
        # Act & Assert
        with self.assertRaises(AttributeError):
            Enumerations(data="invalid")

    def test_init_with_valid_data(self):
        """Test Enumerations initialization with valid data."""
        # Arrange
        data = {
            "name": "test",
            "status": "active",
            "version": 1,
            "enumerators": {"test_enum": {"value1": True, "value2": False}},
            "_locked": True
        }
        
        # Act
        enum = Enumerations(data=data)
        
        # Assert
        self.assertEqual(enum.name, "test")
        self.assertEqual(enum.status, "active")
        self.assertEqual(enum.version, 1)
        self.assertEqual(enum.enumerators, {"test_enum": {"value1": True, "value2": False}})
        self.assertTrue(enum._locked)

    def test_get_enum_values(self):
        """Test get_enum_values method."""
        # Arrange
        data = {
            "name": "test",
            "status": "active",
            "version": 1,
            "enumerators": {"test_enum": {"value1": True, "value2": False}}
        }
        enum = Enumerations(data=data)
        
        # Act
        values = enum.get_enum_values("test_enum")
        
        # Assert
        self.assertEqual(values, ["value1", "value2"])

    def test_get_enum_values_none_enumerators(self):
        """Test get_enum_values when enumerators is None."""
        # Arrange
        data = {
            "name": "test",
            "status": "active",
            "version": 1,
            "enumerators": None
        }
        enum = Enumerations(data=data)
        
        # Act & Assert
        with self.assertRaises(TypeError):
            enum.get_enum_values("test_enum")

    def test_get_enum_values_enum_not_found(self):
        """Test get_enum_values when enum is not found."""
        # Arrange
        data = {
            "name": "test",
            "status": "active",
            "version": 1,
            "enumerators": {"test_enum": {"value1": True}}
        }
        enum = Enumerations(data=data)
        
        # Act & Assert
        with self.assertRaises(ConfiguratorException):
            enum.get_enum_values("nonexistent_enum")

    def test_to_dict(self):
        """Test to_dict method."""
        # Arrange
        data = {
            "name": "test",
            "status": "active",
            "version": 1,
            "enumerators": {"test_enum": {"value1": True}},
            "_locked": True
        }
        enum = Enumerations(data=data)
        
        # Act
        result = enum.to_dict()
        
        # Assert
        expected = {
            "name": "test",
            "status": "active",
            "version": 1,
            "enumerators": {"test_enum": {"value1": True}},
            "_locked": True
        }
        self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main() 