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
        mock_files = [{"name": "dict1.yaml"}, {"name": "dict2.yaml"}]
        mock_file_io.get_documents.return_value = mock_files

        # Act
        response = self.client.get('/api/dictionaries/')

        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = response.json
        self.assertIn("id", response_data)
        self.assertIn("type", response_data)
        self.assertIn("status", response_data)
        self.assertIn("data", response_data)
        self.assertEqual(response_data["status"], "SUCCESS")
        self.assertEqual(response_data["data"], mock_files)

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
        mock_dictionary = {"name": "test_dict", "version": "1.0.0"}
        mock_dictionary_class.return_value = mock_dictionary

        # Act
        response = self.client.get('/api/dictionaries/test_dict/')

        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = response.json
        self.assertIn("id", response_data)
        self.assertIn("type", response_data)
        self.assertIn("status", response_data)
        self.assertIn("data", response_data)
        self.assertEqual(response_data["status"], "SUCCESS")
        self.assertEqual(response_data["data"], mock_dictionary)

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
        mock_event = Mock()
        mock_event.data = test_data
        mock_dictionary.save.return_value = [mock_event]
        mock_dictionary_class.return_value = mock_dictionary

        # Act
        response = self.client.put('/api/dictionaries/test_dict/', json=test_data)

        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = response.json
        self.assertIn("id", response_data)
        self.assertIn("type", response_data)
        self.assertIn("status", response_data)
        self.assertIn("data", response_data)
        self.assertEqual(response_data["status"], "SUCCESS")
        self.assertEqual(response_data["data"], test_data)

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
        mock_dictionary.delete.return_value = {"deleted": True}
        mock_dictionary_class.return_value = mock_dictionary

        # Act
        response = self.client.delete('/api/dictionaries/test_dict/')

        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = response.json
        self.assertIn("id", response_data)
        self.assertIn("type", response_data)
        self.assertIn("status", response_data)
        self.assertIn("data", response_data)
        self.assertEqual(response_data["status"], "SUCCESS")
        self.assertEqual(response_data["data"], {"deleted": True})

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

    @patch('configurator.routes.dictionary_routes.Dictionary')
    def test_lock_unlock_dictionary_success(self, mock_dictionary_class):
        """Test successful PATCH /api/dictionaries/<file_name>."""
        # Arrange
        mock_dictionary = Mock()
        mock_dictionary.flip_lock.return_value = {"read_only": True}
        mock_dictionary_class.return_value = mock_dictionary

        # Act
        response = self.client.patch('/api/dictionaries/test_dict/')

        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = response.json
        self.assertIn("id", response_data)
        self.assertIn("type", response_data)
        self.assertIn("status", response_data)
        self.assertIn("data", response_data)
        self.assertEqual(response_data["status"], "SUCCESS")
        self.assertEqual(response_data["data"], {"read_only": True})

    @patch('configurator.routes.dictionary_routes.Dictionary')
    def test_lock_unlock_dictionary_general_exception(self, mock_dictionary_class):
        """Test PATCH /api/dictionaries/<file_name> when Dictionary raises a general exception."""
        # Arrange
        mock_dictionary = Mock()
        mock_dictionary.flip_lock.side_effect = Exception("Unexpected error")
        mock_dictionary_class.return_value = mock_dictionary

        # Act
        response = self.client.patch('/api/dictionaries/test_dict/')

        # Assert
        self.assertEqual(response.status_code, 500)
        response_data = response.json
        self.assertIn("id", response_data)
        self.assertIn("type", response_data)
        self.assertIn("status", response_data)
        self.assertIn("data", response_data)
        self.assertEqual(response_data["status"], "FAILURE")

    @patch('configurator.routes.dictionary_routes.FileIO')
    @patch('configurator.routes.dictionary_routes.Dictionary')
    def test_clean_dictionaries_success(self, mock_dictionary_class, mock_file_io):
        """Test successful PATCH /api/dictionaries - Clean Dictionaries."""
        # Arrange
        # Create mock file objects with name attribute
        mock_file1 = Mock()
        mock_file1.name = "dict1.yaml"
        mock_file2 = Mock()
        mock_file2.name = "dict2.yaml"
        mock_files = [mock_file1, mock_file2]
        mock_file_io.get_documents.return_value = mock_files
        
        mock_dictionary = Mock()
        mock_event = ConfiguratorEvent("DIC-03", "SUCCESS")
        mock_dictionary.save.return_value = [mock_event]
        mock_dictionary_class.return_value = mock_dictionary

        # Act
        response = self.client.patch('/api/dictionaries/')

        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = response.json
        self.assertEqual(response_data["id"], "DIC-04")
        self.assertEqual(response_data["type"], "CLEAN_DICTIONARIES")
        self.assertEqual(response_data["status"], "SUCCESS")
        self.assertIn("sub_events", response_data)

    @patch('configurator.routes.dictionary_routes.FileIO')
    @patch('configurator.routes.dictionary_routes.Dictionary')
    def test_clean_dictionaries_with_dictionary_save_exception(self, mock_dictionary_class, mock_file_io):
        """Test PATCH /api/dictionaries when Dictionary.save() raises an exception."""
        # Arrange
        # Create mock file object with name attribute
        mock_file = Mock()
        mock_file.name = "dict1.yaml"
        mock_files = [mock_file]
        mock_file_io.get_documents.return_value = mock_files
        
        mock_dictionary = Mock()
        event = ConfiguratorEvent("test", "save_error")
        mock_dictionary.save.side_effect = ConfiguratorException("Save error", event)
        mock_dictionary_class.return_value = mock_dictionary

        # Act
        response = self.client.patch('/api/dictionaries/')

        # Assert
        self.assertEqual(response.status_code, 500)
        response_data = response.json
        self.assertEqual(response_data["id"], "DIC-04")
        self.assertEqual(response_data["type"], "CLEAN_DICTIONARIES")
        self.assertEqual(response_data["status"], "FAILURE")
        self.assertIn("data", response_data)
        self.assertIn("sub_events", response_data)

    @patch('configurator.routes.dictionary_routes.FileIO')
    @patch('configurator.routes.dictionary_routes.Dictionary')
    def test_clean_dictionaries_with_dictionary_save_general_exception(self, mock_dictionary_class, mock_file_io):
        """Test PATCH /api/dictionaries when Dictionary.save() raises a general exception."""
        # Arrange
        # Create mock file object with name attribute
        mock_file = Mock()
        mock_file.name = "dict1.yaml"
        mock_files = [mock_file]
        mock_file_io.get_documents.return_value = mock_files
        
        mock_dictionary = Mock()
        mock_dictionary.save.side_effect = Exception("Save failed")
        mock_dictionary_class.return_value = mock_dictionary

        # Act
        response = self.client.patch('/api/dictionaries/')

        # Assert
        self.assertEqual(response.status_code, 500)
        response_data = response.json
        self.assertEqual(response_data["id"], "DIC-04")
        self.assertEqual(response_data["type"], "CLEAN_DICTIONARIES")
        self.assertEqual(response_data["status"], "FAILURE")
        self.assertIn("data", response_data)


if __name__ == '__main__':
    unittest.main()