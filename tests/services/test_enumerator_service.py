import unittest
from unittest.mock import patch, MagicMock
from configurator.services.enumerator_service import Enumerators, Enumerations
from configurator.utils.configurator_exception import ConfiguratorException

class TestEnumerators(unittest.TestCase):
    @patch('configurator.services.enumerator_service.FileIO.get_document')
    def test_init_with_none_data_loads_file(self, mock_get_document):
        mock_get_document.return_value = [{"version": 0, "enumerators": {}}]
        enum = Enumerators(None)
        self.assertEqual(enum.dict, [{"version": 0, "enumerators": {}}])

    def test_init_with_data(self):
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
        
        enum = Enumerators(cleaned_data)
        
        # Act
        events = enum.save()
        
        # Assert
        self.assertEqual(len(events), 1)
        event = events[0]
        self.assertEqual(event.id, "ENU-03")
        self.assertEqual(event.type, "SAVE_ENUMERATORS")
        self.assertEqual(event.status, "SUCCESS")
        
        # Check that the event data shows the differences
        self.assertIn("data", event.__dict__)
        event_data = event.data
        self.assertIn("original", event_data)
        self.assertIn("saved", event_data)
        self.assertTrue(event_data["changed"])
        
        # Verify FileIO calls
        mock_get_document.assert_called()
        mock_put_document.assert_called_once_with("test_data", "enumerators.json", cleaned_data)

    @patch('configurator.services.enumerator_service.FileIO.put_document')
    @patch('configurator.services.enumerator_service.FileIO.get_document')
    def test_save_success_no_changes(self, mock_get_document, mock_put_document):
        """Test successful save with no changes detected."""
        # Arrange
        same_data = [{"version": 0, "enumerators": {"same": {"value": 1}}}]
        
        # Mock get_document to return same content for original and saved
        mock_get_document.side_effect = [same_data, same_data]
        
        enum = Enumerators(same_data)
        
        # Act
        events = enum.save()
        
        # Assert
        self.assertEqual(len(events), 1)
        event = events[0]
        self.assertEqual(event.id, "ENU-03")
        self.assertEqual(event.type, "SAVE_ENUMERATORS")
        self.assertEqual(event.status, "SUCCESS")
        
        # Check that the event data shows no differences
        self.assertIn("data", event.__dict__)
        event_data = event.data
        self.assertFalse(event_data["changed"])

    @patch('configurator.services.enumerator_service.FileIO.put_document')
    @patch('configurator.services.enumerator_service.FileIO.get_document')
    def test_save_configurator_exception(self, mock_get_document, mock_put_document):
        """Test save when ConfiguratorException is raised."""
        # Arrange
        data = [{"version": 0, "enumerators": {}}]
        enum = Enumerators(data)
        
        # Mock get_document to raise ConfiguratorException
        from configurator.utils.configurator_exception import ConfiguratorEvent
        event = ConfiguratorEvent("TEST-01", "TEST_ERROR")
        mock_get_document.side_effect = ConfiguratorException("Test error", event)
        
        # Act
        events = enum.save()
        
        # Assert
        self.assertEqual(len(events), 1)
        event = events[0]
        self.assertEqual(event.id, "ENU-03")
        self.assertEqual(event.type, "SAVE_ENUMERATORS")
        self.assertEqual(event.status, "FAILURE")
        self.assertEqual(event.data["error"], "error saving document")
        self.assertEqual(len(event.sub_events), 1)
        self.assertEqual(event.sub_events[0].id, "TEST-01")

    @patch('configurator.services.enumerator_service.FileIO.put_document')
    @patch('configurator.services.enumerator_service.FileIO.get_document')
    def test_save_general_exception(self, mock_get_document, mock_put_document):
        """Test save when general Exception is raised."""
        # Arrange
        data = [{"version": 0, "enumerators": {}}]
        enum = Enumerators(data)
        
        # Mock get_document to raise general Exception
        mock_get_document.side_effect = Exception("Unexpected error")
        
        # Act
        events = enum.save()
        
        # Assert
        self.assertEqual(len(events), 1)
        event = events[0]
        self.assertEqual(event.id, "ENU-03")
        self.assertEqual(event.type, "SAVE_ENUMERATORS")
        self.assertEqual(event.status, "FAILURE")
        self.assertEqual(event.data["error"], "unexpected error saving document")
        self.assertEqual(len(event.sub_events), 1)
        self.assertEqual(event.sub_events[0].id, "ENU-04")

    def test_version_returns_correct_version(self):
        data = [
            {"version": 0, "enumerators": {"a": 1}},
            {"version": 1, "enumerators": {"b": 2}}
        ]
        enum = Enumerators(data)
        # Test that version method returns the correct version
        result = enum.version(1)
        self.assertEqual(result.version, 1)
        self.assertEqual(result.enumerators, {"b": 2})

class TestEnumerations(unittest.TestCase):
    def test_init_with_valid_data(self):
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

    def test_init_with_invalid_data_raises(self):
        with self.assertRaises(ConfiguratorException):
            Enumerations(None)

    def test_get_enum_values_success(self):
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
        data = {
            "name": "test",
            "status": "active",
            "version": 1,
            "enumerators": {"foo": {"bar": 1}}
        }
        enum = Enumerations(data)
        with self.assertRaises(ConfiguratorException):
            enum.get_enum_values("not_a_key")

if __name__ == '__main__':
    unittest.main() 