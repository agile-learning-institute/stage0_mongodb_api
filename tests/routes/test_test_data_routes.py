import unittest
from unittest.mock import patch, Mock
from flask import Flask
from configurator.routes.test_data_routes import create_test_data_routes
from configurator.utils.configurator_exception import ConfiguratorException, ConfiguratorEvent


class TestTestDataRoutes(unittest.TestCase):
    """Test cases for test data routes."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = Flask(__name__)
        self.app.register_blueprint(create_test_data_routes(), url_prefix='/api/test_data')
        self.client = self.app.test_client()

    @patch.object(__import__('configurator.utils.file_io', fromlist=['FileIO']).FileIO, 'get_documents')
    def test_get_data_files_success(self, mock_get_documents):
        """Test successful GET /api/test_data."""
        # Arrange
        mock_get_documents.return_value = [
            {
                "name": "test1.json",
                "read_only": False,
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00",
                "size": 1024
            },
            {
                "name": "test2.json",
                "read_only": True,
                "created_at": "2023-01-02T00:00:00",
                "updated_at": "2023-01-02T00:00:00",
                "size": 2048
            }
        ]

        # Act
        response = self.client.get('/api/test_data/')

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 2)
        mock_get_documents.assert_called_once_with("test_data")

    @patch.object(__import__('configurator.utils.file_io', fromlist=['FileIO']).FileIO, 'get_documents')
    def test_get_data_files_configurator_exception(self, mock_get_documents):
        """Test GET /api/test_data when FileIO raises ConfiguratorException."""
        # Arrange
        event = ConfiguratorEvent("test", "file_error")
        mock_get_documents.side_effect = ConfiguratorException("File error", event)

        # Act
        response = self.client.get('/api/test_data/')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertIsInstance(response.json, dict)
        self.assertIn("id", response.json)
        self.assertIn("type", response.json)

    @patch.object(__import__('configurator.utils.file_io', fromlist=['FileIO']).FileIO, 'get_documents')
    def test_get_data_files_general_exception(self, mock_get_documents):
        """Test GET /api/test_data when FileIO raises a general exception."""
        # Arrange
        mock_get_documents.side_effect = Exception("Unexpected error")

        # Act
        response = self.client.get('/api/test_data/')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertIsInstance(response.json, str)
        self.assertIn("Unexpected error", response.json)

    @patch.object(__import__('configurator.utils.file_io', fromlist=['FileIO']).FileIO, 'get_document')
    def test_get_test_data_success(self, mock_get_document):
        """Test successful GET /api/test_data/<file_name>."""
        # Arrange
        mock_get_document.return_value = {
            "name": "test.json",
            "read_only": False,
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00",
            "size": 1024
        }

        # Act
        response = self.client.get('/api/test_data/test.json/')

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["name"], "test.json")
        mock_get_document.assert_called_once_with("test_data", "test.json")

    @patch.object(__import__('configurator.utils.file_io', fromlist=['FileIO']).FileIO, 'get_document')
    def test_get_test_data_configurator_exception(self, mock_get_document):
        """Test GET /api/test_data/<file_name> when FileIO raises ConfiguratorException."""
        # Arrange
        event = ConfiguratorEvent("test", "file_error")
        mock_get_document.side_effect = ConfiguratorException("File error", event)

        # Act
        response = self.client.get('/api/test_data/test.json/')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertIsInstance(response.json, dict)
        self.assertIn("id", response.json)
        self.assertIn("type", response.json)

    @patch.object(__import__('configurator.utils.file_io', fromlist=['FileIO']).FileIO, 'get_document')
    def test_get_test_data_general_exception(self, mock_get_document):
        """Test GET /api/test_data/<file_name> when FileIO raises a general exception."""
        # Arrange
        mock_get_document.side_effect = Exception("Unexpected error")

        # Act
        response = self.client.get('/api/test_data/test.json/')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertIsInstance(response.json, str)
        self.assertIn("Unexpected error", response.json)

    @patch.object(__import__('configurator.utils.file_io', fromlist=['FileIO']).FileIO, 'put_document')
    def test_update_test_data_success(self, mock_put_document):
        """Test successful PUT /api/test_data/<file_name>."""
        # Arrange
        mock_put_document.return_value = {
            "name": "test.json",
            "read_only": False,
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00",
            "size": 1024
        }

        test_data = {"test": "data"}

        # Act
        response = self.client.put('/api/test_data/test.json/', json=test_data)

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["name"], "test.json")
        mock_put_document.assert_called_once_with("test_data", "test.json", test_data)

    @patch.object(__import__('configurator.utils.file_io', fromlist=['FileIO']).FileIO, 'put_document')
    def test_update_test_data_configurator_exception(self, mock_put_document):
        """Test PUT /api/test_data/<file_name> when FileIO raises ConfiguratorException."""
        # Arrange
        event = ConfiguratorEvent("test", "file_error")
        mock_put_document.side_effect = ConfiguratorException("File error", event)

        test_data = {"test": "data"}

        # Act
        response = self.client.put('/api/test_data/test.json/', json=test_data)

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertIsInstance(response.json, dict)
        self.assertIn("id", response.json)
        self.assertIn("type", response.json)

    @patch.object(__import__('configurator.utils.file_io', fromlist=['FileIO']).FileIO, 'put_document')
    def test_update_test_data_general_exception(self, mock_put_document):
        """Test PUT /api/test_data/<file_name> when FileIO raises a general exception."""
        # Arrange
        mock_put_document.side_effect = Exception("Unexpected error")

        test_data = {"test": "data"}

        # Act
        response = self.client.put('/api/test_data/test.json/', json=test_data)

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertIsInstance(response.json, str)
        self.assertIn("Unexpected error", response.json)

    @patch.object(__import__('configurator.utils.file_io', fromlist=['FileIO']).FileIO, 'delete_document')
    def test_delete_test_data_success(self, mock_delete_document):
        """Test successful DELETE /api/test_data/<file_name>."""
        # Arrange
        mock_delete_document.return_value = {
            "name": "test.json",
            "deleted": True
        }

        # Act
        response = self.client.delete('/api/test_data/test.json/')

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["deleted"], True)
        mock_delete_document.assert_called_once_with("test_data", "test.json")

    @patch.object(__import__('configurator.utils.file_io', fromlist=['FileIO']).FileIO, 'delete_document')
    def test_delete_test_data_configurator_exception(self, mock_delete_document):
        """Test DELETE /api/test_data/<file_name> when FileIO raises ConfiguratorException."""
        # Arrange
        event = ConfiguratorEvent("test", "file_error")
        mock_delete_document.side_effect = ConfiguratorException("File error", event)

        # Act
        response = self.client.delete('/api/test_data/test.json/')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertIsInstance(response.json, dict)
        self.assertIn("id", response.json)
        self.assertIn("type", response.json)

    @patch.object(__import__('configurator.utils.file_io', fromlist=['FileIO']).FileIO, 'delete_document')
    def test_delete_test_data_general_exception(self, mock_delete_document):
        """Test DELETE /api/test_data/<file_name> when FileIO raises a general exception."""
        # Arrange
        mock_delete_document.side_effect = Exception("Unexpected error")

        # Act
        response = self.client.delete('/api/test_data/test.json/')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertIsInstance(response.json, str)
        self.assertIn("Unexpected error", response.json)

    @patch.object(__import__('configurator.utils.file_io', fromlist=['FileIO']).FileIO, 'lock_unlock')
    def test_lock_unlock_test_data_success(self, mock_lock_unlock):
        """Test successful PATCH /api/test_data/<file_name>."""
        # Arrange
        mock_lock_unlock.return_value = {
            "name": "test.json",
            "read_only": True,
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00",
            "size": 1024
        }

        # Act
        response = self.client.patch('/api/test_data/test.json/')

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["read_only"], True)
        mock_lock_unlock.assert_called_once_with("test_data", "test.json")

    @patch.object(__import__('configurator.utils.file_io', fromlist=['FileIO']).FileIO, 'lock_unlock')
    def test_lock_unlock_test_data_configurator_exception(self, mock_lock_unlock):
        """Test PATCH /api/test_data/<file_name> when FileIO raises ConfiguratorException."""
        # Arrange
        event = ConfiguratorEvent("test", "file_error")
        mock_lock_unlock.side_effect = ConfiguratorException("File error", event)

        # Act
        response = self.client.patch('/api/test_data/test.json/')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertIsInstance(response.json, dict)
        self.assertIn("id", response.json)
        self.assertIn("type", response.json)

    @patch.object(__import__('configurator.utils.file_io', fromlist=['FileIO']).FileIO, 'lock_unlock')
    def test_lock_unlock_test_data_general_exception(self, mock_lock_unlock):
        """Test PATCH /api/test_data/<file_name> when FileIO raises a general exception."""
        # Arrange
        mock_lock_unlock.side_effect = Exception("Unexpected error")

        # Act
        response = self.client.patch('/api/test_data/test.json/')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertIsInstance(response.json, str)
        self.assertIn("Unexpected error", response.json)

    def test_test_data_post_method_not_allowed(self):
        """Test that POST method is not allowed on /api/test_data."""
        # Act
        response = self.client.post('/api/test_data/')

        # Assert
        self.assertEqual(response.status_code, 405)

    def test_test_data_put_method_not_allowed_on_root(self):
        """Test that PUT method is not allowed on /api/test_data (root)."""
        # Act
        response = self.client.put('/api/test_data/')

        # Assert
        self.assertEqual(response.status_code, 405)

    def test_test_data_delete_method_not_allowed_on_root(self):
        """Test that DELETE method is not allowed on /api/test_data (root)."""
        # Act
        response = self.client.delete('/api/test_data/')

        # Assert
        self.assertEqual(response.status_code, 405)

    def test_test_data_patch_method_not_allowed_on_root(self):
        """Test that PATCH method is not allowed on /api/test_data (root)."""
        # Act
        response = self.client.patch('/api/test_data/')

        # Assert
        self.assertEqual(response.status_code, 405)


if __name__ == '__main__':
    unittest.main() 