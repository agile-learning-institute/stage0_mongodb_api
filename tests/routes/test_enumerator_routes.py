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
        self.app.register_blueprint(create_enumerator_routes(), url_prefix='/api/enumerators')
        self.client = self.app.test_client()

    @patch('configurator.routes.enumerator_routes.Enumerators')
    def test_get_enumerators_success(self, mock_enumerators_class):
        """Test successful GET /api/enumerators."""
        # Arrange
        expected_content = [{"name": "enum1", "status": "active", "version": 1, "enumerators": {}}]
        mock_enumerators = Mock()
        mock_enumerators.to_dict.return_value = expected_content
        mock_enumerators_class.return_value = mock_enumerators

        # Act
        response = self.client.get('/api/enumerators/')

        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = response.json
        self.assertEqual(response_data, expected_content)
        mock_enumerators_class.assert_called_once_with(None)

    @patch('configurator.routes.enumerator_routes.Enumerators')
    def test_get_enumerators_not_found(self, mock_enumerators_class):
        """Test GET /api/enumerators when file is not found."""
        # Arrange
        event = ConfiguratorEvent("FIL-02", "FILE_NOT_FOUND", {"file_path": "/input/test_data/enumerators.json"})
        mock_enumerators_class.side_effect = ConfiguratorException("File not found", event)

        # Act
        response = self.client.get('/api/enumerators/')

        # Assert
        self.assertEqual(response.status_code, 500)
        response_data = response.json
        self.assertIn("id", response_data)
        self.assertIn("type", response_data)
        self.assertIn("status", response_data)
        self.assertIn("data", response_data)
        self.assertEqual(response_data["status"], "FAILURE")

    @patch('configurator.routes.enumerator_routes.Enumerators')
    def test_get_enumerators_configurator_exception(self, mock_enumerators_class):
        """Test GET /api/enumerators when Enumerators raises ConfiguratorException."""
        # Arrange
        event = ConfiguratorEvent("TEST-01", "TEST", {"error": "test"})
        mock_enumerators_class.side_effect = ConfiguratorException("Other error", event)

        # Act
        response = self.client.get('/api/enumerators/')

        # Assert
        self.assertEqual(response.status_code, 500)
        response_data = response.json
        self.assertIn("id", response_data)
        self.assertIn("type", response_data)
        self.assertIn("status", response_data)
        self.assertIn("data", response_data)
        self.assertEqual(response_data["status"], "FAILURE")

    @patch('configurator.routes.enumerator_routes.Enumerators')
    def test_get_enumerators_general_exception(self, mock_enumerators_class):
        """Test GET /api/enumerators when Enumerators raises a general exception."""
        # Arrange
        mock_enumerators_class.side_effect = Exception("Unexpected error")

        # Act
        response = self.client.get('/api/enumerators/')

        # Assert
        self.assertEqual(response.status_code, 500)
        response_data = response.json
        self.assertIn("id", response_data)
        self.assertIn("type", response_data)
        self.assertIn("status", response_data)
        self.assertIn("data", response_data)
        self.assertEqual(response_data["status"], "FAILURE")

    @patch('configurator.routes.enumerator_routes.Enumerators')
    def test_put_enumerators_success(self, mock_enumerators_class):
        """Test successful PUT /api/enumerators."""
        # Arrange
        test_data = [{"name": "enum1", "status": "active", "version": 1, "enumerators": {}}]
        mock_enumerators = Mock()
        mock_event = Mock()
        mock_event.data = test_data
        mock_enumerators.save.return_value = [mock_event]
        mock_enumerators_class.return_value = mock_enumerators

        # Act
        response = self.client.put('/api/enumerators/', json=test_data)

        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = response.json
        self.assertEqual(response_data, test_data)
        mock_enumerators_class.assert_called_once_with(data=test_data)

    @patch('configurator.routes.enumerator_routes.Enumerators')
    def test_put_enumerators_configurator_exception(self, mock_enumerators_class):
        """Test PUT /api/enumerators when Enumerators raises ConfiguratorException."""
        # Arrange
        event = ConfiguratorEvent("TEST-01", "TEST", {"error": "test"})
        mock_enumerators_class.side_effect = ConfiguratorException("Save error", event)
        test_data = [{"name": "enum1", "status": "active", "version": 1, "enumerators": {}}]

        # Act
        response = self.client.put('/api/enumerators/', json=test_data)

        # Assert
        self.assertEqual(response.status_code, 500)
        response_data = response.json
        self.assertIn("id", response_data)
        self.assertIn("type", response_data)
        self.assertIn("status", response_data)
        self.assertIn("data", response_data)
        self.assertEqual(response_data["status"], "FAILURE")

    @patch('configurator.routes.enumerator_routes.Enumerators')
    def test_put_enumerators_general_exception(self, mock_enumerators_class):
        """Test PUT /api/enumerators when Enumerators raises a general exception."""
        # Arrange
        mock_enumerators_class.side_effect = Exception("Unexpected error")
        test_data = [{"name": "enum1", "status": "active", "version": 1, "enumerators": {}}]

        # Act
        response = self.client.put('/api/enumerators/', json=test_data)

        # Assert
        self.assertEqual(response.status_code, 500)
        response_data = response.json
        self.assertIn("id", response_data)
        self.assertIn("type", response_data)
        self.assertIn("status", response_data)
        self.assertIn("data", response_data)
        self.assertEqual(response_data["status"], "FAILURE")

    def test_enumerators_delete_method_not_allowed(self):
        """Test that DELETE method is not allowed on /api/enumerators."""
        # Act
        response = self.client.delete('/api/enumerators/')

        # Assert
        self.assertEqual(response.status_code, 405)

    @patch('configurator.routes.enumerator_routes.Enumerators')
    def test_clean_enumerators_success(self, mock_enumerators_class):
        """Test successful PATCH /api/enumerators - Clean Enumerators."""
        # Arrange
        mock_enumerators = Mock()
        mock_event = ConfiguratorEvent("ENU-03", "SUCCESS")
        mock_enumerators.save.return_value = [mock_event]
        mock_enumerators_class.return_value = mock_enumerators

        # Act
        response = self.client.patch('/api/enumerators/')

        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = response.json
        self.assertEqual(response_data["id"], "ENU-04")
        self.assertEqual(response_data["type"], "CLEAN_ENUMERATORS")
        self.assertEqual(response_data["status"], "SUCCESS")
        self.assertIn("sub_events", response_data)
        mock_enumerators_class.assert_called_once()
        mock_enumerators.save.assert_called_once()

    @patch('configurator.routes.enumerator_routes.Enumerators')
    def test_clean_enumerators_configurator_exception(self, mock_enumerators_class):
        """Test PATCH /api/enumerators when Enumerators.save() raises ConfiguratorException."""
        # Arrange
        mock_enumerators = Mock()
        event = ConfiguratorEvent("test", "save_error")
        mock_enumerators.save.side_effect = ConfiguratorException("Save error", event)
        mock_enumerators_class.return_value = mock_enumerators

        # Act
        response = self.client.patch('/api/enumerators/')

        # Assert
        self.assertEqual(response.status_code, 500)
        response_data = response.json
        self.assertEqual(response_data["id"], "ENU-04")
        self.assertEqual(response_data["type"], "CLEAN_ENUMERATORS")
        self.assertEqual(response_data["status"], "FAILURE")
        self.assertIn("data", response_data)
        self.assertIn("sub_events", response_data)

    @patch('configurator.routes.enumerator_routes.Enumerators')
    def test_clean_enumerators_general_exception(self, mock_enumerators_class):
        """Test PATCH /api/enumerators when Enumerators.save() raises a general exception."""
        # Arrange
        mock_enumerators = Mock()
        mock_enumerators.save.side_effect = Exception("Save failed")
        mock_enumerators_class.return_value = mock_enumerators

        # Act
        response = self.client.patch('/api/enumerators/')

        # Assert
        self.assertEqual(response.status_code, 500)
        response_data = response.json
        self.assertEqual(response_data["id"], "ENU-04")
        self.assertEqual(response_data["type"], "CLEAN_ENUMERATORS")
        self.assertEqual(response_data["status"], "FAILURE")
        self.assertIn("data", response_data)

    def test_enumerators_with_filename_not_allowed(self):
        """Test that enumerators with filename is not allowed."""
        # Act
        response = self.client.get('/api/enumerators/test.json')

        # Assert
        self.assertEqual(response.status_code, 404)


if __name__ == '__main__':
    unittest.main()