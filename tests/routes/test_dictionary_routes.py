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

    @patch.object(__import__('configurator.utils.file_io', fromlist=['FileIO']).FileIO, 'get_documents')
    def test_get_dictionaries_success(self, mock_get_documents):
        """Test successful GET /api/dictionaries."""
        # Arrange
        mock_get_documents.return_value = [
            {
                "name": "dict1.yaml",
                "read_only": False,
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00",
                "size": 1024
            },
            {
                "name": "dict2.yaml",
                "read_only": True,
                "created_at": "2023-01-02T00:00:00",
                "updated_at": "2023-01-02T00:00:00",
                "size": 2048
            }
        ]

        # Act
        response = self.client.get('/api/dictionaries')

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 2)
        mock_get_documents.assert_called_once_with("dictionaries")

    @patch.object(__import__('configurator.utils.file_io', fromlist=['FileIO']).FileIO, 'get_documents')
    def test_get_dictionaries_configurator_exception(self, mock_get_documents):
        """Test GET /api/dictionaries when FileIO raises ConfiguratorException."""
        # Arrange
        event = ConfiguratorEvent("test", "file_error")
        mock_get_documents.side_effect = ConfiguratorException("File error", event)

        # Act
        response = self.client.get('/api/dictionaries')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertIsInstance(response.json, dict)
        self.assertIn("id", response.json)
        self.assertIn("type", response.json)

    @patch.object(__import__('configurator.utils.file_io', fromlist=['FileIO']).FileIO, 'get_documents')
    def test_get_dictionaries_general_exception(self, mock_get_documents):
        """Test GET /api/dictionaries when FileIO raises a general exception."""
        # Arrange
        mock_get_documents.side_effect = Exception("Unexpected error")

        # Act
        response = self.client.get('/api/dictionaries')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertIsInstance(response.json, str)
        self.assertIn("Unexpected error", response.json)

    @patch('configurator.routes.dictionary_routes.Dictionary')
    def test_get_dictionary_success(self, mock_dictionary_class):
        """Test successful GET /api/dictionaries/<file_name>."""
        # Arrange
        mock_dictionary = {
            "name": "test_dict",
            "description": "A test dictionary",
            "fields": {"field1": "string"}
        }
        mock_dictionary_class.return_value = mock_dictionary

        # Act
        response = self.client.get('/api/dictionaries/test_dict.yaml')

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["name"], "test_dict")
        mock_dictionary_class.assert_called_once_with("test_dict.yaml")

    @patch('configurator.routes.dictionary_routes.Dictionary')
    def test_get_dictionary_configurator_exception(self, mock_dictionary_class):
        """Test GET /api/dictionaries/<file_name> when Dictionary raises ConfiguratorException."""
        # Arrange
        event = ConfiguratorEvent("test", "dictionary_error")
        mock_dictionary_class.side_effect = ConfiguratorException("Dictionary error", event)

        # Act
        response = self.client.get('/api/dictionaries/test_dict.yaml')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertIsInstance(response.json, dict)
        self.assertIn("id", response.json)
        self.assertIn("type", response.json)

    @patch('configurator.routes.dictionary_routes.Dictionary')
    def test_get_dictionary_general_exception(self, mock_dictionary_class):
        """Test GET /api/dictionaries/<file_name> when Dictionary raises a general exception."""
        # Arrange
        mock_dictionary_class.side_effect = Exception("Unexpected error")

        # Act
        response = self.client.get('/api/dictionaries/test_dict.yaml')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertIsInstance(response.json, str)
        self.assertIn("Unexpected error", response.json)

    @patch('configurator.routes.dictionary_routes.Dictionary')
    def test_update_dictionary_success(self, mock_dictionary_class):
        """Test successful PUT /api/dictionaries/<file_name>."""
        # Arrange
        mock_dictionary = Mock()
        mock_dictionary.save.return_value = {
            "name": "test_dict",
            "saved": True
        }
        mock_dictionary_class.return_value = mock_dictionary

        test_data = {
            "name": "test_dict",
            "description": "Updated test dictionary",
            "fields": {"field1": "string", "field2": "number"}
        }

        # Act
        response = self.client.put('/api/dictionaries/test_dict.yaml', json=test_data)

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["saved"], True)
        mock_dictionary_class.assert_called_once_with("test_dict.yaml", test_data)
        mock_dictionary.save.assert_called_once()

    @patch('configurator.routes.dictionary_routes.Dictionary')
    def test_update_dictionary_configurator_exception(self, mock_dictionary_class):
        """Test PUT /api/dictionaries/<file_name> when Dictionary raises ConfiguratorException."""
        # Arrange
        mock_dictionary = Mock()
        event = ConfiguratorEvent("test", "save_error")
        mock_dictionary.save.side_effect = ConfiguratorException("Save error", event)
        mock_dictionary_class.return_value = mock_dictionary

        test_data = {"name": "test_dict"}

        # Act
        response = self.client.put('/api/dictionaries/test_dict.yaml', json=test_data)

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertIsInstance(response.json, dict)
        self.assertIn("id", response.json)
        self.assertIn("type", response.json)

    @patch('configurator.routes.dictionary_routes.Dictionary')
    def test_update_dictionary_general_exception(self, mock_dictionary_class):
        """Test PUT /api/dictionaries/<file_name> when Dictionary raises a general exception."""
        # Arrange
        mock_dictionary = Mock()
        mock_dictionary.save.side_effect = Exception("Unexpected error")
        mock_dictionary_class.return_value = mock_dictionary

        test_data = {"name": "test_dict"}

        # Act
        response = self.client.put('/api/dictionaries/test_dict.yaml', json=test_data)

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json, "Unexpected error")

    @patch('configurator.routes.dictionary_routes.Dictionary')
    def test_delete_dictionary_success(self, mock_dictionary_class):
        """Test successful DELETE /api/dictionaries/<file_name>."""
        # Arrange
        mock_dictionary = Mock()
        mock_dictionary.delete.return_value = {
            "name": "test_dict",
            "deleted": True
        }
        mock_dictionary_class.return_value = mock_dictionary

        # Act
        response = self.client.delete('/api/dictionaries/test_dict.yaml')

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["deleted"], True)
        mock_dictionary_class.assert_called_once_with("test_dict.yaml")
        mock_dictionary.delete.assert_called_once()

    @patch('configurator.routes.dictionary_routes.Dictionary')
    def test_delete_dictionary_configurator_exception(self, mock_dictionary_class):
        """Test DELETE /api/dictionaries/<file_name> when Dictionary raises ConfiguratorException."""
        # Arrange
        mock_dictionary = Mock()
        event = ConfiguratorEvent("test", "delete_error")
        mock_dictionary.delete.side_effect = ConfiguratorException("Delete error", event)
        mock_dictionary_class.return_value = mock_dictionary

        # Act
        response = self.client.delete('/api/dictionaries/test_dict.yaml')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertIsInstance(response.json, dict)
        self.assertIn("id", response.json)
        self.assertIn("type", response.json)

    @patch('configurator.routes.dictionary_routes.Dictionary')
    def test_delete_dictionary_general_exception(self, mock_dictionary_class):
        """Test DELETE /api/dictionaries/<file_name> when Dictionary raises a general exception."""
        # Arrange
        mock_dictionary = Mock()
        mock_dictionary.delete.side_effect = Exception("Unexpected error")
        mock_dictionary_class.return_value = mock_dictionary

        # Act
        response = self.client.delete('/api/dictionaries/test_dict.yaml')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json, "Unexpected error")

    @patch('configurator.routes.dictionary_routes.Dictionary')
    def test_lock_unlock_dictionary_success(self, mock_dictionary_class):
        """Test successful PATCH /api/dictionaries/<file_name>."""
        # Arrange
        mock_dictionary = Mock()
        mock_dictionary.flip_lock.return_value = {
            "name": "test_dict",
            "read_only": True
        }
        mock_dictionary_class.return_value = mock_dictionary

        # Act
        response = self.client.patch('/api/dictionaries/test_dict.yaml')

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["read_only"], True)
        mock_dictionary_class.assert_called_once_with("test_dict.yaml")
        mock_dictionary.flip_lock.assert_called_once()

    @patch('configurator.routes.dictionary_routes.Dictionary')
    def test_lock_unlock_dictionary_configurator_exception(self, mock_dictionary_class):
        """Test PATCH /api/dictionaries/<file_name> when Dictionary raises ConfiguratorException."""
        # Arrange
        mock_dictionary = Mock()
        event = ConfiguratorEvent("test", "lock_error")
        mock_dictionary.flip_lock.side_effect = ConfiguratorException("Lock error", event)
        mock_dictionary_class.return_value = mock_dictionary

        # Act
        response = self.client.patch('/api/dictionaries/test_dict.yaml')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertIsInstance(response.json, dict)
        self.assertIn("id", response.json)
        self.assertIn("type", response.json)

    @patch('configurator.routes.dictionary_routes.Dictionary')
    def test_lock_unlock_dictionary_general_exception(self, mock_dictionary_class):
        """Test PATCH /api/dictionaries/<file_name> when Dictionary raises a general exception."""
        # Arrange
        mock_dictionary = Mock()
        mock_dictionary.flip_lock.side_effect = Exception("Unexpected error")
        mock_dictionary_class.return_value = mock_dictionary

        # Act
        response = self.client.patch('/api/dictionaries/test_dict.yaml')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json, "Unexpected error")

    def test_dictionaries_post_method_not_allowed(self):
        """Test that POST method is not allowed on /api/dictionaries."""
        # Act
        response = self.client.post('/api/dictionaries')

        # Assert
        self.assertEqual(response.status_code, 405)

    def test_dictionaries_put_method_not_allowed_on_root(self):
        """Test that PUT method is not allowed on /api/dictionaries (root)."""
        # Act
        response = self.client.put('/api/dictionaries')

        # Assert
        self.assertEqual(response.status_code, 405)

    def test_dictionaries_delete_method_not_allowed_on_root(self):
        """Test that DELETE method is not allowed on /api/dictionaries (root)."""
        # Act
        response = self.client.delete('/api/dictionaries')

        # Assert
        self.assertEqual(response.status_code, 405)

    @patch.object(__import__('configurator.utils.file_io', fromlist=['FileIO']).FileIO, 'get_documents')
    @patch('configurator.routes.dictionary_routes.Dictionary')
    def test_clean_dictionaries_success(self, mock_dictionary_class, mock_get_documents):
        """Test successful PATCH /api/dictionaries - Clean Dictionaries."""
        # Arrange
        mock_files = [
            Mock(name="dict1.yaml"),
            Mock(name="dict2.yaml")
        ]
        for f, n in zip(mock_files, ["dict1.yaml", "dict2.yaml"]):
            f.name = n
        mock_get_documents.return_value = mock_files
        
        mock_dict1 = Mock()
        mock_dict2 = Mock()
        mock_dictionary_class.side_effect = [mock_dict1, mock_dict2]
        
        # Mock save methods returning events
        mock_event1 = Mock()
        mock_event1.to_dict.return_value = {"id": "DIC-03", "status": "SUCCESS"}
        mock_event2 = Mock()
        mock_event2.to_dict.return_value = {"id": "DIC-03", "status": "SUCCESS"}
        
        mock_dict1.save.return_value = [mock_event1]
        mock_dict2.save.return_value = [mock_event2]

        # Act
        response = self.client.patch('/api/dictionaries')

        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = response.json
        self.assertEqual(response_data["id"], "DIC-04")
        self.assertEqual(response_data["type"], "CLEAN_DICTIONARIES")
        self.assertEqual(response_data["status"], "SUCCESS")
        self.assertEqual(len(response_data["sub_events"]), 2)
        
        mock_get_documents.assert_called_once_with("dictionaries")
        mock_dictionary_class.assert_any_call("dict1.yaml")
        mock_dictionary_class.assert_any_call("dict2.yaml")
        mock_dict1.save.assert_called_once()
        mock_dict2.save.assert_called_once()

    @patch.object(__import__('configurator.utils.file_io', fromlist=['FileIO']).FileIO, 'get_documents')
    def test_clean_dictionaries_configurator_exception(self, mock_get_documents):
        """Test PATCH /api/dictionaries when FileIO raises ConfiguratorException."""
        # Arrange
        event = ConfiguratorEvent("test", "file_error")
        mock_get_documents.side_effect = ConfiguratorException("File error", event)

        # Act
        response = self.client.patch('/api/dictionaries')

        # Assert
        self.assertEqual(response.status_code, 500)
        response_data = response.json
        self.assertEqual(response_data["id"], "DIC-04")
        self.assertEqual(response_data["type"], "CLEAN_DICTIONARIES")
        self.assertEqual(response_data["status"], "FAILURE")
        self.assertEqual(response_data["data"], {"error": "Configurator error cleaning dictionaries"})

    @patch.object(__import__('configurator.utils.file_io', fromlist=['FileIO']).FileIO, 'get_documents')
    def test_clean_dictionaries_general_exception(self, mock_get_documents):
        """Test PATCH /api/dictionaries when FileIO raises a general exception."""
        # Arrange
        mock_get_documents.side_effect = Exception("Unexpected error")

        # Act
        response = self.client.patch('/api/dictionaries')

        # Assert
        self.assertEqual(response.status_code, 500)
        response_data = response.json
        self.assertEqual(response_data["id"], "DIC-04")
        self.assertEqual(response_data["type"], "CLEAN_DICTIONARIES")
        self.assertEqual(response_data["status"], "FAILURE")
        self.assertEqual(response_data["data"], {"error": "Unexpected error"})

    @patch.object(__import__('configurator.utils.file_io', fromlist=['FileIO']).FileIO, 'get_documents')
    @patch('configurator.routes.dictionary_routes.Dictionary')
    def test_clean_dictionaries_with_dictionary_save_exception(self, mock_dictionary_class, mock_get_documents):
        """Test PATCH /api/dictionaries when Dictionary.save() raises an exception."""
        # Arrange
        mock_files = [Mock(name="dict1.yaml")]
        mock_files[0].name = "dict1.yaml"
        mock_get_documents.return_value = mock_files
        
        mock_dictionary = Mock()
        mock_dictionary_class.return_value = mock_dictionary
        
        # Mock Dictionary.save() raising ConfiguratorException
        event = ConfiguratorEvent("test", "save_error")
        mock_dictionary.save.side_effect = ConfiguratorException("Save error", event)

        # Act
        response = self.client.patch('/api/dictionaries')

        # Assert
        self.assertEqual(response.status_code, 500)
        response_data = response.json
        self.assertEqual(response_data["id"], "DIC-04")
        self.assertEqual(response_data["type"], "CLEAN_DICTIONARIES")
        self.assertEqual(response_data["status"], "FAILURE")
        self.assertEqual(response_data["data"], {"error": "Configurator error cleaning dictionaries"})
        self.assertEqual(len(response_data["sub_events"]), 1)
        self.assertEqual(response_data["sub_events"][0]["id"], "test")

    @patch.object(__import__('configurator.utils.file_io', fromlist=['FileIO']).FileIO, 'get_documents')
    @patch('configurator.routes.dictionary_routes.Dictionary')
    def test_clean_dictionaries_with_dictionary_save_general_exception(self, mock_dictionary_class, mock_get_documents):
        """Test PATCH /api/dictionaries when Dictionary.save() raises a general exception."""
        # Arrange
        mock_files = [Mock(name="dict1.yaml")]
        mock_files[0].name = "dict1.yaml"
        mock_get_documents.return_value = mock_files
        
        mock_dictionary = Mock()
        mock_dictionary_class.return_value = mock_dictionary
        
        # Mock Dictionary.save() raising general Exception
        mock_dictionary.save.side_effect = Exception("Save failed")

        # Act
        response = self.client.patch('/api/dictionaries')

        # Assert
        self.assertEqual(response.status_code, 500)
        response_data = response.json
        self.assertEqual(response_data["id"], "DIC-04")
        self.assertEqual(response_data["type"], "CLEAN_DICTIONARIES")
        self.assertEqual(response_data["status"], "FAILURE")
        self.assertEqual(response_data["data"], {"error": "Save failed"})


if __name__ == '__main__':
    unittest.main()