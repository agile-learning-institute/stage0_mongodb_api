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
    def test_save_calls_put_document(self, mock_put_document):
        data = [{"version": 0, "enumerators": {}}]
        enum = Enumerators(data)
        enum.save()
        mock_put_document.assert_called_once()

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