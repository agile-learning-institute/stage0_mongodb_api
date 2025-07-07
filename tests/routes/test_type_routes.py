import unittest
from unittest.mock import patch, Mock
from flask import Flask
from configurator.routes.type_routes import create_type_routes
from configurator.utils.configurator_exception import ConfiguratorException, ConfiguratorEvent


class TestTypeRoutes(unittest.TestCase):
    """Test cases for type routes."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = Flask(__name__)
        self.app.register_blueprint(create_type_routes(), url_prefix='/api/types')
        self.client = self.app.test_client()

    @patch.object(__import__('configurator.utils.file_io', fromlist=['FileIO']).FileIO, 'get_documents')
    def test_get_types_success(self, mock_get_documents):
        """Test successful GET /api/types."""
        # Arrange
        mock_get_documents.return_value = [
            {
                "name": "type1.yaml",
                "read_only": False,
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00",
                "size": 1024
            },
            {
                "name": "type2.yaml",
                "read_only": True,
                "created_at": "2023-01-02T00:00:00",
                "updated_at": "2023-01-02T00:00:00",
                "size": 2048
            }
        ]

        # Act
        response = self.client.get('/api/types/')

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 2)
        mock_get_documents.assert_called_once_with("types")

    @patch.object(__import__('configurator.utils.file_io', fromlist=['FileIO']).FileIO, 'get_documents')
    def test_get_types_configurator_exception(self, mock_get_documents):
        """Test GET /api/types when FileIO raises ConfiguratorException."""
        # Arrange
        event = ConfiguratorEvent("test", "file_error")
        mock_get_documents.side_effect = ConfiguratorException("File error", event)

        # Act
        response = self.client.get('/api/types/')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertIsInstance(response.json, dict)
        self.assertIn("id", response.json)
        self.assertIn("type", response.json)

    @patch.object(__import__('configurator.utils.file_io', fromlist=['FileIO']).FileIO, 'get_documents')
    def test_get_types_general_exception(self, mock_get_documents):
        """Test GET /api/types when FileIO raises a general exception."""
        # Arrange
        mock_get_documents.side_effect = Exception("Unexpected error")

        # Act
        response = self.client.get('/api/types/')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertIsInstance(response.json, str)
        self.assertIn("Unexpected error", response.json)

    @patch('configurator.routes.type_routes.Type')
    def test_get_type_success(self, mock_type_class):
        """Test successful GET /api/types/<file_name>."""
        # Arrange
        mock_type = {
            "name": "test_type",
            "description": "A test type",
            "fields": {"field1": "string"}
        }
        mock_type_class.return_value = mock_type

        # Act
        response = self.client.get('/api/types/test_type.yaml/')

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["name"], "test_type")
        mock_type_class.assert_called_once_with("test_type.yaml")

    @patch('configurator.routes.type_routes.Type')
    def test_get_type_configurator_exception(self, mock_type_class):
        """Test GET /api/types/<file_name> when Type raises ConfiguratorException."""
        # Arrange
        event = ConfiguratorEvent("test", "type_error")
        mock_type_class.side_effect = ConfiguratorException("Type error", event)

        # Act
        response = self.client.get('/api/types/test_type.yaml/')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertIsInstance(response.json, dict)
        self.assertIn("id", response.json)
        self.assertIn("type", response.json)

    @patch('configurator.routes.type_routes.Type')
    def test_get_type_general_exception(self, mock_type_class):
        """Test GET /api/types/<file_name> when Type raises a general exception."""
        # Arrange
        mock_type_class.side_effect = Exception("Unexpected error")

        # Act
        response = self.client.get('/api/types/test_type.yaml/')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertIsInstance(response.json, str)
        self.assertIn("Unexpected error", response.json)

    @patch('configurator.routes.type_routes.Type')
    def test_update_type_success(self, mock_type_class):
        """Test successful PUT /api/types/<file_name>."""
        # Arrange
        mock_type = Mock()
        mock_type.save.return_value = {
            "name": "test_type",
            "saved": True
        }
        mock_type_class.return_value = mock_type

        test_data = {
            "name": "test_type",
            "description": "Updated test type",
            "fields": {"field1": "string", "field2": "number"}
        }

        # Act
        response = self.client.put('/api/types/test_type.yaml/', json=test_data)

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["saved"], True)
        mock_type_class.assert_called_once_with("test_type.yaml", test_data)
        mock_type.save.assert_called_once()

    @patch('configurator.routes.type_routes.Type')
    def test_update_type_configurator_exception(self, mock_type_class):
        """Test PUT /api/types/<file_name> when Type raises ConfiguratorException."""
        # Arrange
        mock_type = Mock()
        event = ConfiguratorEvent("test", "save_error")
        mock_type.save.side_effect = ConfiguratorException("Save error", event)
        mock_type_class.return_value = mock_type

        test_data = {"name": "test_type"}

        # Act
        response = self.client.put('/api/types/test_type.yaml/', json=test_data)

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertIsInstance(response.json, dict)
        self.assertIn("id", response.json)
        self.assertIn("type", response.json)

    @patch('configurator.routes.type_routes.Type')
    def test_update_type_general_exception(self, mock_type_class):
        """Test PUT /api/types/<file_name> when Type raises a general exception."""
        # Arrange
        mock_type = Mock()
        mock_type.save.side_effect = Exception("Unexpected error")
        mock_type_class.return_value = mock_type

        test_data = {"name": "test_type"}

        # Act
        response = self.client.put('/api/types/test_type.yaml/', json=test_data)

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertIsInstance(response.json, str)
        self.assertIn("Unexpected error", response.json)

    @patch('configurator.routes.type_routes.Type')
    def test_delete_type_success(self, mock_type_class):
        """Test successful DELETE /api/types/<file_name>."""
        # Arrange
        mock_type = Mock()
        mock_type.delete.return_value = {
            "name": "test_type",
            "deleted": True
        }
        mock_type_class.return_value = mock_type

        # Act
        response = self.client.delete('/api/types/test_type.yaml/')

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["deleted"], True)
        mock_type_class.assert_called_once_with("test_type.yaml")
        mock_type.delete.assert_called_once()

    @patch('configurator.routes.type_routes.Type')
    def test_delete_type_configurator_exception(self, mock_type_class):
        """Test DELETE /api/types/<file_name> when Type raises ConfiguratorException."""
        # Arrange
        mock_type = Mock()
        event = ConfiguratorEvent("test", "delete_error")
        mock_type.delete.side_effect = ConfiguratorException("Delete error", event)
        mock_type_class.return_value = mock_type

        # Act
        response = self.client.delete('/api/types/test_type.yaml/')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertIsInstance(response.json, dict)
        self.assertIn("id", response.json)
        self.assertIn("type", response.json)

    @patch('configurator.routes.type_routes.Type')
    def test_delete_type_general_exception(self, mock_type_class):
        """Test DELETE /api/types/<file_name> when Type raises a general exception."""
        # Arrange
        mock_type = Mock()
        mock_type.delete.side_effect = Exception("Unexpected error")
        mock_type_class.return_value = mock_type

        # Act
        response = self.client.delete('/api/types/test_type.yaml/')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertIsInstance(response.json, str)
        self.assertIn("Unexpected error", response.json)

    @patch('configurator.routes.type_routes.Type')
    def test_lock_unlock_type_success(self, mock_type_class):
        """Test successful PATCH /api/types/<file_name>."""
        # Arrange
        mock_type = Mock()
        mock_type.flip_lock.return_value = {
            "name": "test_type",
            "read_only": True
        }
        mock_type_class.return_value = mock_type

        # Act
        response = self.client.patch('/api/types/test_type.yaml/')

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["read_only"], True)
        mock_type_class.assert_called_once_with("test_type.yaml")
        mock_type.flip_lock.assert_called_once()

    @patch('configurator.routes.type_routes.Type')
    def test_lock_unlock_type_configurator_exception(self, mock_type_class):
        """Test PATCH /api/types/<file_name> when Type raises ConfiguratorException."""
        # Arrange
        mock_type = Mock()
        event = ConfiguratorEvent("test", "lock_error")
        mock_type.flip_lock.side_effect = ConfiguratorException("Lock error", event)
        mock_type_class.return_value = mock_type

        # Act
        response = self.client.patch('/api/types/test_type.yaml/')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertIsInstance(response.json, dict)
        self.assertIn("id", response.json)
        self.assertIn("type", response.json)

    @patch('configurator.routes.type_routes.Type')
    def test_lock_unlock_type_general_exception(self, mock_type_class):
        """Test PATCH /api/types/<file_name> when Type raises a general exception."""
        # Arrange
        mock_type = Mock()
        mock_type.flip_lock.side_effect = Exception("Unexpected error")
        mock_type_class.return_value = mock_type

        # Act
        response = self.client.patch('/api/types/test_type.yaml/')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertIsInstance(response.json, str)
        self.assertIn("Unexpected error", response.json)

    def test_types_post_method_not_allowed(self):
        """Test that POST method is not allowed on /api/types."""
        # Act
        response = self.client.post('/api/types/')

        # Assert
        self.assertEqual(response.status_code, 405)

    def test_types_put_method_not_allowed_on_root(self):
        """Test that PUT method is not allowed on /api/types (root)."""
        # Act
        response = self.client.put('/api/types/')

        # Assert
        self.assertEqual(response.status_code, 405)

    def test_types_delete_method_not_allowed_on_root(self):
        """Test that DELETE method is not allowed on /api/types (root)."""
        # Act
        response = self.client.delete('/api/types/')

        # Assert
        self.assertEqual(response.status_code, 405)

    @patch.object(__import__('configurator.utils.file_io', fromlist=['FileIO']).FileIO, 'get_documents')
    @patch('configurator.routes.type_routes.Type')
    def test_clean_types_success(self, mock_type_class, mock_get_documents):
        """Test successful PATCH /api/types - Clean Types."""
        # Arrange
        mock_files = [
            Mock(name="type1.yaml"),
            Mock(name="type2.yaml")
        ]
        for f, n in zip(mock_files, ["type1.yaml", "type2.yaml"]):
            f.name = n
        mock_get_documents.return_value = mock_files
        
        mock_type1 = Mock()
        mock_type2 = Mock()
        mock_type_class.side_effect = [mock_type1, mock_type2]
        
        # Mock save methods returning events
        mock_event1 = Mock()
        mock_event1.to_dict.return_value = {"id": "TYP-03", "status": "SUCCESS"}
        mock_event2 = Mock()
        mock_event2.to_dict.return_value = {"id": "TYP-03", "status": "SUCCESS"}
        
        mock_type1.save.return_value = [mock_event1]
        mock_type2.save.return_value = [mock_event2]

        # Act
        response = self.client.patch('/api/types/')

        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = response.json
        self.assertEqual(response_data["id"], "TYP-04")
        self.assertEqual(response_data["type"], "CLEAN_TYPES")
        self.assertEqual(response_data["status"], "SUCCESS")
        self.assertEqual(len(response_data["sub_events"]), 2)
        
        mock_get_documents.assert_called_once_with("types")
        mock_type_class.assert_any_call("type1.yaml")
        mock_type_class.assert_any_call("type2.yaml")
        mock_type1.save.assert_called_once()
        mock_type2.save.assert_called_once()

    @patch.object(__import__('configurator.utils.file_io', fromlist=['FileIO']).FileIO, 'get_documents')
    def test_clean_types_configurator_exception(self, mock_get_documents):
        """Test PATCH /api/types when FileIO raises ConfiguratorException."""
        # Arrange
        event = ConfiguratorEvent("test", "file_error")
        mock_get_documents.side_effect = ConfiguratorException("File error", event)

        # Act
        response = self.client.patch('/api/types/')

        # Assert
        self.assertEqual(response.status_code, 500)
        response_data = response.json
        self.assertEqual(response_data["id"], "TYP-04")
        self.assertEqual(response_data["type"], "CLEAN_TYPES")
        self.assertEqual(response_data["status"], "FAILURE")
        self.assertEqual(response_data["data"], {"error": "Configurator error cleaning types"})

    @patch.object(__import__('configurator.utils.file_io', fromlist=['FileIO']).FileIO, 'get_documents')
    def test_clean_types_general_exception(self, mock_get_documents):
        """Test PATCH /api/types when FileIO raises a general exception."""
        # Arrange
        mock_get_documents.side_effect = Exception("Unexpected error")

        # Act
        response = self.client.patch('/api/types/')

        # Assert
        self.assertEqual(response.status_code, 500)
        response_data = response.json
        self.assertEqual(response_data["id"], "TYP-04")
        self.assertEqual(response_data["type"], "CLEAN_TYPES")
        self.assertEqual(response_data["status"], "FAILURE")
        self.assertEqual(response_data["data"], {"error": "Unexpected error"})

    @patch.object(__import__('configurator.utils.file_io', fromlist=['FileIO']).FileIO, 'get_documents')
    @patch('configurator.routes.type_routes.Type')
    def test_clean_types_with_type_save_exception(self, mock_type_class, mock_get_documents):
        """Test PATCH /api/types when Type.save() raises an exception."""
        # Arrange
        mock_files = [Mock(name="type1.yaml")]
        mock_files[0].name = "type1.yaml"
        mock_get_documents.return_value = mock_files
        
        mock_type = Mock()
        mock_type_class.return_value = mock_type
        
        # Mock Type.save() raising ConfiguratorException
        event = ConfiguratorEvent("test", "save_error")
        mock_type.save.side_effect = ConfiguratorException("Save error", event)

        # Act
        response = self.client.patch('/api/types/')

        # Assert
        self.assertEqual(response.status_code, 500)
        response_data = response.json
        self.assertEqual(response_data["id"], "TYP-04")
        self.assertEqual(response_data["type"], "CLEAN_TYPES")
        self.assertEqual(response_data["status"], "FAILURE")
        self.assertEqual(response_data["data"], {"error": "Configurator error cleaning types"})
        self.assertEqual(len(response_data["sub_events"]), 1)
        self.assertEqual(response_data["sub_events"][0]["id"], "test")

    @patch.object(__import__('configurator.utils.file_io', fromlist=['FileIO']).FileIO, 'get_documents')
    @patch('configurator.routes.type_routes.Type')
    def test_clean_types_with_type_save_general_exception(self, mock_type_class, mock_get_documents):
        """Test PATCH /api/types when Type.save() raises a general exception."""
        # Arrange
        mock_files = [Mock(name="type1.yaml")]
        mock_files[0].name = "type1.yaml"
        mock_get_documents.return_value = mock_files
        
        mock_type = Mock()
        mock_type_class.return_value = mock_type
        
        # Mock Type.save() raising general Exception
        mock_type.save.side_effect = Exception("Save failed")

        # Act
        response = self.client.patch('/api/types/')

        # Assert
        self.assertEqual(response.status_code, 500)
        response_data = response.json
        self.assertEqual(response_data["id"], "TYP-04")
        self.assertEqual(response_data["type"], "CLEAN_TYPES")
        self.assertEqual(response_data["status"], "FAILURE")
        self.assertEqual(response_data["data"], {"error": "Save failed"})


if __name__ == '__main__':
    unittest.main()