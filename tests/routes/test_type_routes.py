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
        response = self.client.get('/api/types')

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
        response = self.client.get('/api/types')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertIsInstance(response.json, dict)
        self.assertIn("message", response.json)
        self.assertIn("event", response.json)

    @patch.object(__import__('configurator.utils.file_io', fromlist=['FileIO']).FileIO, 'get_documents')
    def test_get_types_general_exception(self, mock_get_documents):
        """Test GET /api/types when FileIO raises a general exception."""
        # Arrange
        mock_get_documents.side_effect = Exception("Unexpected error")

        # Act
        response = self.client.get('/api/types')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json, "Undefined Exception")

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
        response = self.client.get('/api/types/test_type.yaml')

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
        response = self.client.get('/api/types/test_type.yaml')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertIsInstance(response.json, dict)
        self.assertIn("message", response.json)
        self.assertIn("event", response.json)

    @patch('configurator.routes.type_routes.Type')
    def test_get_type_general_exception(self, mock_type_class):
        """Test GET /api/types/<file_name> when Type raises a general exception."""
        # Arrange
        mock_type_class.side_effect = Exception("Unexpected error")

        # Act
        response = self.client.get('/api/types/test_type.yaml')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json, "Undefined Exception")

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
        response = self.client.put('/api/types/test_type.yaml', json=test_data)

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
        response = self.client.put('/api/types/test_type.yaml', json=test_data)

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertIsInstance(response.json, dict)
        self.assertIn("message", response.json)
        self.assertIn("event", response.json)

    @patch('configurator.routes.type_routes.Type')
    def test_update_type_general_exception(self, mock_type_class):
        """Test PUT /api/types/<file_name> when Type raises a general exception."""
        # Arrange
        mock_type = Mock()
        mock_type.save.side_effect = Exception("Unexpected error")
        mock_type_class.return_value = mock_type

        test_data = {"name": "test_type"}

        # Act
        response = self.client.put('/api/types/test_type.yaml', json=test_data)

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json, "Undefined Exception")

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
        response = self.client.delete('/api/types/test_type.yaml')

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
        response = self.client.delete('/api/types/test_type.yaml')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertIsInstance(response.json, dict)
        self.assertIn("message", response.json)
        self.assertIn("event", response.json)

    @patch('configurator.routes.type_routes.Type')
    def test_delete_type_general_exception(self, mock_type_class):
        """Test DELETE /api/types/<file_name> when Type raises a general exception."""
        # Arrange
        mock_type = Mock()
        mock_type.delete.side_effect = Exception("Unexpected error")
        mock_type_class.return_value = mock_type

        # Act
        response = self.client.delete('/api/types/test_type.yaml')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json, "Undefined Exception")

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
        response = self.client.patch('/api/types/test_type.yaml')

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
        response = self.client.patch('/api/types/test_type.yaml')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertIsInstance(response.json, dict)
        self.assertIn("message", response.json)
        self.assertIn("event", response.json)

    @patch('configurator.routes.type_routes.Type')
    def test_lock_unlock_type_general_exception(self, mock_type_class):
        """Test PATCH /api/types/<file_name> when Type raises a general exception."""
        # Arrange
        mock_type = Mock()
        mock_type.flip_lock.side_effect = Exception("Unexpected error")
        mock_type_class.return_value = mock_type

        # Act
        response = self.client.patch('/api/types/test_type.yaml')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json, "Undefined Exception")

    def test_types_post_method_not_allowed(self):
        """Test that POST method is not allowed on /api/types."""
        # Act
        response = self.client.post('/api/types')

        # Assert
        self.assertEqual(response.status_code, 405)

    def test_types_put_method_not_allowed_on_root(self):
        """Test that PUT method is not allowed on /api/types (root)."""
        # Act
        response = self.client.put('/api/types')

        # Assert
        self.assertEqual(response.status_code, 405)

    def test_types_delete_method_not_allowed_on_root(self):
        """Test that DELETE method is not allowed on /api/types (root)."""
        # Act
        response = self.client.delete('/api/types')

        # Assert
        self.assertEqual(response.status_code, 405)

    def test_types_patch_method_not_allowed_on_root(self):
        """Test that PATCH method is not allowed on /api/types (root)."""
        # Act
        response = self.client.patch('/api/types')

        # Assert
        self.assertEqual(response.status_code, 405)


if __name__ == '__main__':
    unittest.main()