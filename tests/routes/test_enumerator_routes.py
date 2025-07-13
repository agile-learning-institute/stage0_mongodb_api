import unittest
from unittest.mock import patch, Mock
from flask import Flask
from configurator.routes.enumerator_routes import create_enumerator_routes
from configurator.utils.configurator_exception import ConfiguratorException, ConfiguratorEvent


class TestEnumeratorRoutes(unittest.TestCase):
    """Test cases for enumerator routes."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = Flask(__name__)
        self.app.register_blueprint(create_enumerator_routes(), url_prefix='/api/enumerations')
        self.client = self.app.test_client()

    @patch('configurator.routes.enumerator_routes.FileIO.get_documents')
    def test_get_enumerations_success(self, mock_get_documents):
        """Test successful GET /api/enumerations - Get enumeration files."""
        # Arrange
        mock_files = [
            Mock(file_name="test1.yaml", to_dict=lambda: {"name": "test1.yaml", "path": "/path/to/test1.yaml"}),
            Mock(file_name="test2.yaml", to_dict=lambda: {"name": "test2.yaml", "path": "/path/to/test2.yaml"})
        ]
        mock_get_documents.return_value = mock_files
        
        # Act
        response = self.client.get('/api/enumerations/')
        
        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = response.json
        self.assertEqual(len(response_data), 2)
        self.assertEqual(response_data[0]["name"], "test1.yaml")
        self.assertEqual(response_data[1]["name"], "test2.yaml")

    @patch('configurator.routes.enumerator_routes.FileIO.get_documents')
    def test_get_enumerations_exception(self, mock_get_documents):
        """Test GET /api/enumerations when FileIO raises exception."""
        # Arrange
        mock_get_documents.side_effect = Exception("File error")

        # Act
        response = self.client.get('/api/enumerations/')

        # Assert
        self.assertEqual(response.status_code, 500)
        response_data = response.json
        self.assertIn("id", response_data)
        self.assertIn("type", response_data)
        self.assertIn("status", response_data)
        self.assertIn("data", response_data)
        self.assertEqual(response_data["status"], "FAILURE")

    @patch('configurator.routes.enumerator_routes.Enumerations')
    def test_get_enumeration_success(self, mock_enumerations_class):
        """Test successful GET /api/enumerations/{name} - Get specific enumeration."""
        # Arrange
        mock_enumeration = Mock()
        mock_enumeration.to_dict.return_value = {
            "name": "test",
            "status": "active",
            "version": 1,
            "enumerators": {"test_enum": {"value1": True}}
        }
        mock_enumerations_class.return_value = mock_enumeration
        
        # Act
        response = self.client.get('/api/enumerations/test/')
        
        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = response.json
        self.assertEqual(response_data["name"], "test")
        self.assertEqual(response_data["status"], "active")
        self.assertEqual(response_data["version"], 1)
        mock_enumerations_class.assert_called_once_with(file_name="test")

    @patch('configurator.routes.enumerator_routes.Enumerations')
    def test_get_enumeration_exception(self, mock_enumerations_class):
        """Test GET /api/enumerations/{name} when Enumerations raises exception."""
        # Arrange
        event = ConfiguratorEvent("ENU-02", "GET_ENUMERATION")
        mock_enumerations_class.side_effect = ConfiguratorException("File not found", event)

        # Act
        response = self.client.get('/api/enumerations/test/')

        # Assert
        self.assertEqual(response.status_code, 500)
        response_data = response.json
        self.assertIn("id", response_data)
        self.assertIn("type", response_data)
        self.assertIn("status", response_data)
        self.assertIn("data", response_data)
        self.assertEqual(response_data["status"], "FAILURE")

    @patch('configurator.routes.enumerator_routes.Enumerations')
    def test_put_enumeration_success(self, mock_enumerations_class):
        """Test successful PUT /api/enumerations/{name} - Update specific enumeration."""
        # Arrange
        test_data = {
            "name": "test",
            "status": "active",
            "version": 1,
            "enumerators": {"test_enum": {"value1": True}}
        }
        mock_enumeration = Mock()
        mock_enumeration.to_dict.return_value = test_data
        mock_enumeration.save.return_value = mock_enumeration
        mock_enumerations_class.return_value = mock_enumeration

        # Act
        response = self.client.put('/api/enumerations/test/', json=test_data)

        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = response.json
        self.assertEqual(response_data, test_data)
        mock_enumerations_class.assert_called_once_with(data=test_data, file_name="test")

    @patch('configurator.routes.enumerator_routes.Enumerations')
    def test_put_enumeration_exception(self, mock_enumerations_class):
        """Test PUT /api/enumerations/{name} when Enumerations raises exception."""
        # Arrange
        event = ConfiguratorEvent("ENU-03", "PUT_ENUMERATION")
        mock_enumerations_class.side_effect = ConfiguratorException("Save error", event)
        test_data = {"name": "test", "status": "active", "version": 1, "enumerators": {}}

        # Act
        response = self.client.put('/api/enumerations/test/', json=test_data)

        # Assert
        self.assertEqual(response.status_code, 500)
        response_data = response.json
        self.assertIn("id", response_data)
        self.assertIn("type", response_data)
        self.assertIn("status", response_data)
        self.assertIn("data", response_data)
        self.assertEqual(response_data["status"], "FAILURE")

    @patch('configurator.routes.enumerator_routes.Enumerators')
    def test_lock_enumerations_success(self, mock_enumerators_class):
        """Test successful PATCH /api/enumerations - Lock all enumerations."""
        # Arrange
        mock_event = Mock()
        mock_event.to_dict.return_value = {
            "id": "ENU-04",
            "type": "LOCK_ENUMERATIONS",
            "status": "SUCCESS",
            "data": {},
            "events": []
        }
        mock_enumerators = Mock()
        mock_enumerators.lock_all.return_value = mock_event
        mock_enumerators_class.return_value = mock_enumerators

        # Act
        response = self.client.patch('/api/enumerations/')

        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = response.json
        self.assertIn("id", response_data)
        self.assertIn("type", response_data)
        self.assertIn("status", response_data)
        self.assertEqual(response_data["status"], "SUCCESS")
        mock_enumerators.lock_all.assert_called_once()

    @patch('configurator.routes.enumerator_routes.Enumerators')
    def test_lock_enumerations_exception(self, mock_enumerators_class):
        """Test PATCH /api/enumerations when Enumerators raises exception."""
        # Arrange
        event = ConfiguratorEvent("ENU-04", "LOCK_ENUMERATIONS")
        mock_enumerators_class.side_effect = ConfiguratorException("Lock error", event)

        # Act
        response = self.client.patch('/api/enumerations/')

        # Assert
        self.assertEqual(response.status_code, 500)
        response_data = response.json
        self.assertIn("id", response_data)
        self.assertIn("type", response_data)
        self.assertIn("status", response_data)
        self.assertIn("data", response_data)
        self.assertEqual(response_data["status"], "FAILURE")

    def test_enumerations_with_filename_not_allowed(self):
        """Test that enumerations with filename is not allowed."""
        # Act
        response = self.client.get('/api/enumerations/test.json')

        # Assert
        self.assertEqual(response.status_code, 308)  # Redirect to trailing slash


if __name__ == '__main__':
    unittest.main()