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

    @patch('configurator.routes.type_routes.FileIO')
    def test_get_types_success(self, mock_file_io):
        """Test successful GET /api/types."""
        # Arrange
        mock_files = [{"name": "type1.yaml"}, {"name": "type2.yaml"}]
        mock_file_io.get_documents.return_value = mock_files

        # Act
        response = self.client.get('/api/types/')

        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = response.json
        self.assertEqual(response_data, mock_files)

    @patch('configurator.routes.type_routes.FileIO')
    def test_get_types_general_exception(self, mock_file_io):
        """Test GET /api/types when FileIO raises a general exception."""
        # Arrange
        mock_file_io.get_documents.side_effect = Exception("Unexpected error")

        # Act
        response = self.client.get('/api/types/')

        # Assert
        self.assertEqual(response.status_code, 500)
        response_data = response.json
        self.assertIn("id", response_data)
        self.assertIn("type", response_data)
        self.assertIn("status", response_data)
        self.assertIn("data", response_data)
        self.assertEqual(response_data["status"], "FAILURE")

    @patch('configurator.routes.type_routes.Type')
    def test_get_type_success(self, mock_type_class):
        """Test successful GET /api/types/<file_name>."""
        # Arrange
        mock_type = {"name": "test_type", "version": "1.0.0"}
        mock_type_class.return_value = mock_type

        # Act
        response = self.client.get('/api/types/test_type/')

        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = response.json
        self.assertEqual(response_data, mock_type)

    @patch('configurator.routes.type_routes.Type')
    def test_get_type_general_exception(self, mock_type_class):
        """Test GET /api/types/<file_name> when Type raises a general exception."""
        # Arrange
        mock_type_class.side_effect = Exception("Unexpected error")

        # Act
        response = self.client.get('/api/types/test_type/')

        # Assert
        self.assertEqual(response.status_code, 500)
        response_data = response.json
        self.assertIn("id", response_data)
        self.assertIn("type", response_data)
        self.assertIn("status", response_data)
        self.assertIn("data", response_data)
        self.assertEqual(response_data["status"], "FAILURE")

    @patch('configurator.routes.type_routes.Type')
    def test_update_type_success(self, mock_type_class):
        """Test successful PUT /api/types/<file_name>."""
        # Arrange
        test_data = {"name": "test_type", "version": "1.0.0"}
        mock_type = Mock()
        mock_event = Mock()
        mock_event.data = test_data
        mock_type.save.return_value = [mock_event]
        mock_type_class.return_value = mock_type

        # Act
        response = self.client.put('/api/types/test_type/', json=test_data)

        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = response.json
        self.assertEqual(response_data, test_data)

    @patch('configurator.routes.type_routes.Type')
    def test_update_type_general_exception(self, mock_type_class):
        """Test PUT /api/types/<file_name> when Type raises a general exception."""
        # Arrange
        mock_type_class.side_effect = Exception("Unexpected error")
        test_data = {"name": "test_type", "version": "1.0.0"}

        # Act
        response = self.client.put('/api/types/test_type/', json=test_data)

        # Assert
        self.assertEqual(response.status_code, 500)
        response_data = response.json
        self.assertIn("id", response_data)
        self.assertIn("type", response_data)
        self.assertIn("status", response_data)
        self.assertIn("data", response_data)
        self.assertEqual(response_data["status"], "FAILURE")

    @patch('configurator.routes.type_routes.Type')
    def test_delete_type_success(self, mock_type_class):
        """Test successful DELETE /api/types/<file_name>."""
        # Arrange
        mock_type = Mock()
        mock_type.delete.return_value = {"deleted": True}
        mock_type_class.return_value = mock_type

        # Act
        response = self.client.delete('/api/types/test_type/')

        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = response.json
        self.assertEqual(response_data, {"deleted": True})

    @patch('configurator.routes.type_routes.Type')
    def test_delete_type_general_exception(self, mock_type_class):
        """Test DELETE /api/types/<file_name> when Type raises a general exception."""
        # Arrange
        mock_type = Mock()
        mock_type.delete.side_effect = Exception("Unexpected error")
        mock_type_class.return_value = mock_type

        # Act
        response = self.client.delete('/api/types/test_type/')

        # Assert
        self.assertEqual(response.status_code, 500)
        response_data = response.json
        self.assertIn("id", response_data)
        self.assertIn("type", response_data)
        self.assertIn("status", response_data)
        self.assertIn("data", response_data)
        self.assertEqual(response_data["status"], "FAILURE")

    @patch('configurator.routes.type_routes.Type')
    def test_lock_unlock_type_success(self, mock_type_class):
        """Test successful PATCH /api/types/<file_name>."""
        # Arrange
        mock_type = Mock()
        mock_type.flip_lock.return_value = {"read_only": True}
        mock_type_class.return_value = mock_type

        # Act
        response = self.client.patch('/api/types/test_type/')

        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = response.json
        self.assertEqual(response_data, {"read_only": True})

    @patch('configurator.routes.type_routes.Type')
    def test_lock_unlock_type_general_exception(self, mock_type_class):
        """Test PATCH /api/types/<file_name> when Type raises a general exception."""
        # Arrange
        mock_type = Mock()
        mock_type.flip_lock.side_effect = Exception("Unexpected error")
        mock_type_class.return_value = mock_type

        # Act
        response = self.client.patch('/api/types/test_type/')

        # Assert
        self.assertEqual(response.status_code, 500)
        response_data = response.json
        self.assertIn("id", response_data)
        self.assertIn("type", response_data)
        self.assertIn("status", response_data)
        self.assertIn("data", response_data)
        self.assertEqual(response_data["status"], "FAILURE")

    @patch('configurator.routes.type_routes.FileIO')
    @patch('configurator.routes.type_routes.Type')
    def test_clean_types_success(self, mock_type_class, mock_file_io):
        """Test successful PATCH /api/types - Clean Types."""
        # Arrange
        # Create mock file objects with name attribute
        mock_file1 = Mock()
        mock_file1.name = "type1.yaml"
        mock_file2 = Mock()
        mock_file2.name = "type2.yaml"
        mock_files = [mock_file1, mock_file2]
        mock_file_io.get_documents.return_value = mock_files
        
        mock_type = Mock()
        mock_event = ConfiguratorEvent("TYP-03", "SUCCESS")
        mock_type.save.return_value = [mock_event]
        mock_type_class.return_value = mock_type

        # Act
        response = self.client.patch('/api/types/')

        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = response.json
        self.assertEqual(response_data["id"], "TYP-04")
        self.assertEqual(response_data["type"], "CLEAN_TYPES")
        self.assertEqual(response_data["status"], "SUCCESS")
        self.assertIn("sub_events", response_data)

    @patch('configurator.routes.type_routes.FileIO')
    @patch('configurator.routes.type_routes.Type')
    def test_clean_types_with_type_save_general_exception(self, mock_type_class, mock_file_io):
        """Test PATCH /api/types when Type.save() raises a general exception."""
        # Arrange
        # Create mock file object with name attribute
        mock_file = Mock()
        mock_file.name = "type1.yaml"
        mock_files = [mock_file]
        mock_file_io.get_documents.return_value = mock_files
        
        mock_type = Mock()
        mock_type.save.side_effect = Exception("Save failed")
        mock_type_class.return_value = mock_type

        # Act
        response = self.client.patch('/api/types/')

        # Assert
        self.assertEqual(response.status_code, 500)
        response_data = response.json
        self.assertEqual(response_data["id"], "TYP-04")
        self.assertEqual(response_data["type"], "CLEAN_TYPES")
        self.assertEqual(response_data["status"], "FAILURE")
        self.assertIn("data", response_data)


if __name__ == '__main__':
    unittest.main()