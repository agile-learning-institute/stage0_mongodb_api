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

    @patch.object(__import__('configurator.utils.file_io', fromlist=['FileIO']).FileIO, 'get_document')
    def test_get_enumerators_success(self, mock_get_document):
        """Test successful GET /api/enumerators."""
        # Arrange
        expected_content = {"foo": "bar"}
        mock_get_document.return_value = expected_content

        # Act
        response = self.client.get('/api/enumerators')

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, expected_content)
        mock_get_document.assert_called_once_with("test_data", "enumerators.json")

    @patch.object(__import__('configurator.utils.file_io', fromlist=['FileIO']).FileIO, 'get_document')
    def test_get_enumerators_not_found(self, mock_get_document):
        """Test GET /api/enumerators when file is not found."""
        # Arrange
        event = ConfiguratorEvent("FIL-02", "FILE_NOT_FOUND", {"file_path": "/input/test_data/enumerators.json"})
        mock_get_document.side_effect = ConfiguratorException("File not found", event)

        # Act
        response = self.client.get('/api/enumerators')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertIsInstance(response.json, dict)
        self.assertIn("message", response.json)
        self.assertIn("event", response.json)

    @patch.object(__import__('configurator.utils.file_io', fromlist=['FileIO']).FileIO, 'get_document')
    def test_get_enumerators_configurator_exception(self, mock_get_document):
        """Test GET /api/enumerators when FileIO raises ConfiguratorException."""
        # Arrange
        event = ConfiguratorEvent("TEST-01", "TEST", {"error": "test"})
        mock_get_document.side_effect = ConfiguratorException("Other error", event)

        # Act
        response = self.client.get('/api/enumerators')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertIsInstance(response.json, dict)
        self.assertIn("message", response.json)
        self.assertIn("event", response.json)

    @patch.object(__import__('configurator.utils.file_io', fromlist=['FileIO']).FileIO, 'get_document')
    def test_get_enumerators_general_exception(self, mock_get_document):
        """Test GET /api/enumerators when FileIO raises a general exception."""
        # Arrange
        mock_get_document.side_effect = Exception("Unexpected error")

        # Act
        response = self.client.get('/api/enumerators')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json, "Unexpected error")

    @patch.object(__import__('configurator.utils.file_io', fromlist=['FileIO']).FileIO, 'put_document')
    def test_put_enumerators_success(self, mock_put_document):
        """Test successful PUT /api/enumerators."""
        # Arrange
        mock_put_document.return_value = None
        test_data = {"foo": "bar"}

        # Act
        response = self.client.put('/api/enumerators', json=test_data)

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, test_data)
        mock_put_document.assert_called_once_with("test_data", "enumerators.json", test_data)

    @patch.object(__import__('configurator.utils.file_io', fromlist=['FileIO']).FileIO, 'put_document')
    def test_put_enumerators_configurator_exception(self, mock_put_document):
        """Test PUT /api/enumerators when FileIO raises ConfiguratorException."""
        # Arrange
        event = ConfiguratorEvent("TEST-01", "TEST", {"error": "test"})
        mock_put_document.side_effect = ConfiguratorException("Save error", event)
        test_data = {"foo": "bar"}

        # Act
        response = self.client.put('/api/enumerators', json=test_data)

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertIsInstance(response.json, dict)
        self.assertIn("message", response.json)
        self.assertIn("event", response.json)

    @patch.object(__import__('configurator.utils.file_io', fromlist=['FileIO']).FileIO, 'put_document')
    def test_put_enumerators_general_exception(self, mock_put_document):
        """Test PUT /api/enumerators when FileIO raises a general exception."""
        # Arrange
        mock_put_document.side_effect = Exception("Unexpected error")
        test_data = {"foo": "bar"}

        # Act
        response = self.client.put('/api/enumerators', json=test_data)

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json, "Unexpected error")

    def test_enumerators_delete_method_not_allowed(self):
        """Test that DELETE method is not allowed on /api/enumerators."""
        # Act
        response = self.client.delete('/api/enumerators')

        # Assert
        self.assertEqual(response.status_code, 405)

    @patch('configurator.routes.enumerator_routes.Enumerators')
    def test_clean_enumerators_success(self, mock_enumerators_class):
        """Test successful PATCH /api/enumerators - Clean Enumerators."""
        # Arrange
        mock_enumerators = Mock()
        mock_event = Mock()
        mock_event.to_dict.return_value = {"id": "ENU-03", "status": "SUCCESS"}
        mock_enumerators.save.return_value = [mock_event]
        mock_enumerators_class.return_value = mock_enumerators

        # Act
        response = self.client.patch('/api/enumerators')

        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = response.json
        self.assertEqual(response_data["id"], "ENU-04")
        self.assertEqual(response_data["type"], "CLEAN_ENUMERATORS")
        self.assertEqual(response_data["status"], "SUCCESS")
        self.assertEqual(len(response_data["sub_events"]), 1)
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
        response = self.client.patch('/api/enumerators')

        # Assert
        self.assertEqual(response.status_code, 500)
        response_data = response.json
        self.assertEqual(response_data["id"], "ENU-04")
        self.assertEqual(response_data["type"], "CLEAN_ENUMERATORS")
        self.assertEqual(response_data["status"], "FAILURE")
        self.assertEqual(response_data["data"], "Configurator error cleaning enumerators")
        self.assertEqual(len(response_data["sub_events"]), 1)
        self.assertEqual(response_data["sub_events"][0]["id"], "test")

    @patch('configurator.routes.enumerator_routes.Enumerators')
    def test_clean_enumerators_general_exception(self, mock_enumerators_class):
        """Test PATCH /api/enumerators when Enumerators.save() raises a general exception."""
        # Arrange
        mock_enumerators = Mock()
        mock_enumerators.save.side_effect = Exception("Save failed")
        mock_enumerators_class.return_value = mock_enumerators

        # Act
        response = self.client.patch('/api/enumerators')

        # Assert
        self.assertEqual(response.status_code, 500)
        response_data = response.json
        self.assertEqual(response_data["id"], "ENU-04")
        self.assertEqual(response_data["type"], "CLEAN_ENUMERATORS")
        self.assertEqual(response_data["status"], "FAILURE")
        self.assertEqual(response_data["data"], "Unexpected error cleaning enumerators")

    def test_enumerators_with_filename_not_allowed(self):
        """Test that /api/enumerators/<filename> is not allowed."""
        # Act
        response = self.client.get('/api/enumerators/test.json')

        # Assert
        self.assertEqual(response.status_code, 404)


if __name__ == '__main__':
    unittest.main()