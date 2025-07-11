import unittest
from unittest.mock import patch, Mock
from flask import Flask
from configurator.routes.dictionary_routes import create_dictionary_routes
from configurator.utils.configurator_exception import ConfiguratorException, ConfiguratorEvent


class TestDictionaryRoutes(unittest.TestCase):
    """Test cases for dictionary routes."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = Flask(__name__)
        self.app.register_blueprint(create_dictionary_routes(), url_prefix='/api/dictionaries')
        self.client = self.app.test_client()

    @patch('configurator.routes.dictionary_routes.FileIO')
    def test_get_dictionaries_success(self, mock_file_io):
        """Test successful GET /api/dictionaries."""
        # Arrange
        # Create mock File objects with to_dict() method
        mock_file1 = Mock()
        mock_file1.to_dict.return_value = {"name": "dict1.yaml"}
        mock_file2 = Mock()
        mock_file2.to_dict.return_value = {"name": "dict2.yaml"}
        mock_files = [mock_file1, mock_file2]
        mock_file_io.get_documents.return_value = mock_files

        # Act
        response = self.client.get('/api/dictionaries/')

        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = response.json
        # For successful responses, expect data directly, not wrapped in event envelope
        self.assertEqual(response_data, [{"name": "dict1.yaml"}, {"name": "dict2.yaml"}])

    @patch('configurator.routes.dictionary_routes.FileIO')
    def test_get_dictionaries_general_exception(self, mock_file_io):
        """Test GET /api/dictionaries when FileIO raises a general exception."""
        # Arrange
        mock_file_io.get_documents.side_effect = Exception("Unexpected error")

        # Act
        response = self.client.get('/api/dictionaries/')

        # Assert
        self.assertEqual(response.status_code, 500)
        response_data = response.json
        self.assertIn("id", response_data)
        self.assertIn("type", response_data)
        self.assertIn("status", response_data)
        self.assertIn("data", response_data)
        self.assertEqual(response_data["status"], "FAILURE")

    @patch('configurator.routes.dictionary_routes.Dictionary')
    def test_get_dictionary_success(self, mock_dictionary_class):
        """Test successful GET /api/dictionaries/<file_name>."""
        # Arrange
        mock_dictionary = Mock()
        mock_dictionary.to_dict.return_value = {"name": "test_dict", "version": "1.0.0"}
        mock_dictionary_class.return_value = mock_dictionary

        # Act
        response = self.client.get('/api/dictionaries/test_dict/')

        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = response.json
        self.assertEqual(response_data, {"name": "test_dict", "version": "1.0.0"})

    @patch('configurator.routes.dictionary_routes.Dictionary')
    def test_get_dictionary_general_exception(self, mock_dictionary_class):
        """Test GET /api/dictionaries/<file_name> when Dictionary raises a general exception."""
        # Arrange
        mock_dictionary_class.side_effect = Exception("Unexpected error")

        # Act
        response = self.client.get('/api/dictionaries/test_dict/')

        # Assert
        self.assertEqual(response.status_code, 500)
        response_data = response.json
        self.assertIn("id", response_data)
        self.assertIn("type", response_data)
        self.assertIn("status", response_data)
        self.assertIn("data", response_data)
        self.assertEqual(response_data["status"], "FAILURE")

    @patch('configurator.routes.dictionary_routes.Dictionary')
    def test_update_dictionary_success(self, mock_dictionary_class):
        """Test successful PUT /api/dictionaries/<file_name>."""
        # Arrange
        test_data = {"name": "test_dict", "version": "1.0.0"}
        mock_dictionary = Mock()
        mock_saved_file = Mock()
        mock_saved_file.to_dict.return_value = {"name": "test_dict.yaml", "path": "/path/to/test_dict.yaml"}
        mock_dictionary.save.return_value = mock_saved_file
        mock_dictionary_class.return_value = mock_dictionary

        # Act
        response = self.client.put('/api/dictionaries/test_dict/', json=test_data)

        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = response.json
        self.assertEqual(response_data, {"name": "test_dict.yaml", "path": "/path/to/test_dict.yaml"})

    @patch('configurator.routes.dictionary_routes.Dictionary')
    def test_update_dictionary_general_exception(self, mock_dictionary_class):
        """Test PUT /api/dictionaries/<file_name> when Dictionary raises a general exception."""
        # Arrange
        mock_dictionary_class.side_effect = Exception("Unexpected error")
        test_data = {"name": "test_dict", "version": "1.0.0"}

        # Act
        response = self.client.put('/api/dictionaries/test_dict/', json=test_data)

        # Assert
        self.assertEqual(response.status_code, 500)
        response_data = response.json
        self.assertIn("id", response_data)
        self.assertIn("type", response_data)
        self.assertIn("status", response_data)
        self.assertIn("data", response_data)
        self.assertEqual(response_data["status"], "FAILURE")

    @patch('configurator.routes.dictionary_routes.Dictionary')
    def test_delete_dictionary_success(self, mock_dictionary_class):
        """Test successful DELETE /api/dictionaries/<file_name>."""
        # Arrange
        mock_dictionary = Mock()
        mock_event = Mock()
        mock_event.to_dict.return_value = {"deleted": True}
        mock_dictionary.delete.return_value = mock_event
        mock_dictionary_class.return_value = mock_dictionary

        # Act
        response = self.client.delete('/api/dictionaries/test_dict/')

        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = response.json
        self.assertEqual(response_data, {"deleted": True})

    @patch('configurator.routes.dictionary_routes.Dictionary')
    def test_delete_dictionary_general_exception(self, mock_dictionary_class):
        """Test DELETE /api/dictionaries/<file_name> when Dictionary raises a general exception."""
        # Arrange
        mock_dictionary = Mock()
        mock_dictionary.delete.side_effect = Exception("Unexpected error")
        mock_dictionary_class.return_value = mock_dictionary

        # Act
        response = self.client.delete('/api/dictionaries/test_dict/')

        # Assert
        self.assertEqual(response.status_code, 500)
        response_data = response.json
        self.assertIn("id", response_data)
        self.assertIn("type", response_data)
        self.assertIn("status", response_data)
        self.assertIn("data", response_data)
        self.assertEqual(response_data["status"], "FAILURE")

    # Lock/unlock tests removed as functionality was removed

    @patch('configurator.routes.dictionary_routes.Dictionary')
    def test_lock_all_dictionaries(self, mock_dictionary_class):
        """Test locking all dictionaries."""
        # Arrange
        mock_event = ConfiguratorEvent("DIC-04", "LOCK_ALL_DICTIONARIES")
        mock_event.data = {
            "total_files": 2,
            "operation": "lock_all"
        }
        mock_event.record_success()
        mock_dictionary_class.lock_all.return_value = mock_event

        # Act
        response = self.client.patch('/api/dictionaries/')

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('id', data)
        self.assertIn('type', data)
        self.assertIn('status', data)
        self.assertIn('sub_events', data)
        self.assertIn('data', data)
        self.assertIn('total_files', data['data'])
        self.assertIn('operation', data['data'])


if __name__ == '__main__':
    unittest.main()