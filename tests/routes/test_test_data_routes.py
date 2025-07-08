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

    @patch('configurator.routes.test_data_routes.FileIO')
    def test_get_data_files_success(self, mock_file_io):
        """Test successful GET /api/test_data."""
        # Arrange
        mock_files = [{"name": "data1.json"}, {"name": "data2.json"}]
        mock_file_io.get_documents.return_value = mock_files

        # Act
        response = self.client.get('/api/test_data/')

        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = response.json
        self.assertIn("id", response_data)
        self.assertIn("type", response_data)
        self.assertIn("status", response_data)
        self.assertIn("data", response_data)
        self.assertEqual(response_data["status"], "SUCCESS")
        self.assertEqual(response_data["data"], mock_files)

    @patch('configurator.routes.test_data_routes.FileIO')
    def test_get_data_files_general_exception(self, mock_file_io):
        """Test GET /api/test_data when FileIO raises a general exception."""
        # Arrange
        mock_file_io.get_documents.side_effect = Exception("Unexpected error")

        # Act
        response = self.client.get('/api/test_data/')

        # Assert
        self.assertEqual(response.status_code, 500)
        response_data = response.json
        self.assertIn("id", response_data)
        self.assertIn("type", response_data)
        self.assertIn("status", response_data)
        self.assertIn("data", response_data)
        self.assertEqual(response_data["status"], "FAILURE")

    @patch('configurator.routes.test_data_routes.FileIO')
    def test_get_data_file_success(self, mock_file_io):
        """Test successful GET /api/test_data/<file_name>."""
        # Arrange
        mock_data = {"test": "data"}
        mock_file_io.get_document.return_value = mock_data

        # Act
        response = self.client.get('/api/test_data/test_file.json/')

        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = response.json
        self.assertIn("id", response_data)
        self.assertIn("type", response_data)
        self.assertIn("status", response_data)
        self.assertIn("data", response_data)
        self.assertEqual(response_data["status"], "SUCCESS")
        self.assertEqual(response_data["data"], mock_data)

    @patch('configurator.routes.test_data_routes.FileIO')
    def test_get_data_file_general_exception(self, mock_file_io):
        """Test GET /api/test_data/<file_name> when FileIO raises a general exception."""
        # Arrange
        mock_file_io.get_document.side_effect = Exception("Unexpected error")

        # Act
        response = self.client.get('/api/test_data/test_file.json/')

        # Assert
        self.assertEqual(response.status_code, 500)
        response_data = response.json
        self.assertIn("id", response_data)
        self.assertIn("type", response_data)
        self.assertIn("status", response_data)
        self.assertIn("data", response_data)
        self.assertEqual(response_data["status"], "FAILURE")

    @patch('configurator.routes.test_data_routes.FileIO')
    def test_put_data_file_success(self, mock_file_io):
        """Test successful PUT /api/test_data/<file_name>."""
        # Arrange
        test_data = {"test": "data"}
        mock_file_io.put_document.return_value = {"saved": True}

        # Act
        response = self.client.put('/api/test_data/test_file.json/', json=test_data)

        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = response.json
        self.assertIn("id", response_data)
        self.assertIn("type", response_data)
        self.assertIn("status", response_data)
        self.assertIn("data", response_data)
        self.assertEqual(response_data["status"], "SUCCESS")
        self.assertEqual(response_data["data"], {"saved": True})

    @patch('configurator.routes.test_data_routes.FileIO')
    def test_put_data_file_general_exception(self, mock_file_io):
        """Test PUT /api/test_data/<file_name> when FileIO raises a general exception."""
        # Arrange
        mock_file_io.save_document.side_effect = Exception("Unexpected error")
        test_data = {"test": "data"}

        # Act
        response = self.client.put('/api/test_data/test_file.json/', json=test_data)

        # Assert
        self.assertEqual(response.status_code, 500)
        response_data = response.json
        self.assertIn("id", response_data)
        self.assertIn("type", response_data)
        self.assertIn("status", response_data)
        self.assertIn("data", response_data)
        self.assertEqual(response_data["status"], "FAILURE")

    @patch('configurator.routes.test_data_routes.FileIO')
    def test_delete_data_file_success(self, mock_file_io):
        """Test successful DELETE /api/test_data/<file_name>."""
        # Arrange
        mock_file_io.delete_document.return_value = {"deleted": True}

        # Act
        response = self.client.delete('/api/test_data/test_file.json/')

        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = response.json
        self.assertIn("id", response_data)
        self.assertIn("type", response_data)
        self.assertIn("status", response_data)
        self.assertIn("data", response_data)
        self.assertEqual(response_data["status"], "SUCCESS")
        self.assertEqual(response_data["data"], {"deleted": True})

    @patch('configurator.routes.test_data_routes.FileIO')
    def test_delete_data_file_general_exception(self, mock_file_io):
        """Test DELETE /api/test_data/<file_name> when FileIO raises a general exception."""
        # Arrange
        mock_file_io.delete_document.side_effect = Exception("Unexpected error")

        # Act
        response = self.client.delete('/api/test_data/test_file.json/')

        # Assert
        self.assertEqual(response.status_code, 500)
        response_data = response.json
        self.assertIn("id", response_data)
        self.assertIn("type", response_data)
        self.assertIn("status", response_data)
        self.assertIn("data", response_data)
        self.assertEqual(response_data["status"], "FAILURE")

    def test_test_data_post_method_not_allowed(self):
        """Test that POST method is not allowed on /api/test_data."""
        # Act
        response = self.client.post('/api/test_data/')

        # Assert
        self.assertEqual(response.status_code, 405)

    def test_test_data_patch_method_not_allowed(self):
        """Test that PATCH method is not allowed on /api/test_data."""
        # Act
        response = self.client.patch('/api/test_data/')

        # Assert
        self.assertEqual(response.status_code, 405)


if __name__ == '__main__':
    unittest.main() 