import unittest
from unittest.mock import patch, Mock
from flask import Flask
from configurator.routes.configuration_routes import create_configuration_routes
from configurator.utils.configurator_exception import ConfiguratorException, ConfiguratorEvent


class TestConfigurationRoutes(unittest.TestCase):
    """Test cases for configuration routes."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = Flask(__name__)
        self.app.register_blueprint(create_configuration_routes(), url_prefix='/api/configurations')
        self.client = self.app.test_client()

    @patch('configurator.routes.configuration_routes.FileIO')
    def test_list_configurations_success(self, mock_file_io):
        """Test successful GET /api/configurations/."""
        # Arrange
        # Create mock File objects with to_dict method
        mock_file1 = Mock()
        mock_file1.to_dict.return_value = {"name": "config1.yaml", "read_only": False, "size": 100, "created_at": "2023-01-01T00:00:00", "updated_at": "2023-01-01T00:00:00"}
        mock_file2 = Mock()
        mock_file2.to_dict.return_value = {"name": "config2.yaml", "read_only": False, "size": 200, "created_at": "2023-01-01T00:00:00", "updated_at": "2023-01-01T00:00:00"}
        mock_files = [mock_file1, mock_file2]
        mock_file_io.get_documents.return_value = mock_files

        # Act
        response = self.client.get('/api/configurations/')

        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = response.json
        # For successful responses, expect data directly, not wrapped in event envelope
        expected_data = [mock_file1.to_dict.return_value, mock_file2.to_dict.return_value]
        self.assertEqual(response_data, expected_data)

    @patch('configurator.routes.configuration_routes.FileIO')
    def test_list_configurations_general_exception(self, mock_file_io):
        """Test GET /api/configurations/ when FileIO raises a general exception."""
        # Arrange
        mock_file_io.get_documents.side_effect = Exception("Unexpected error")

        # Act
        response = self.client.get('/api/configurations/')

        # Assert
        self.assertEqual(response.status_code, 500)
        response_data = response.json
        self.assertIn("id", response_data)
        self.assertIn("type", response_data)
        self.assertIn("status", response_data)
        self.assertIn("data", response_data)
        self.assertEqual(response_data["status"], "FAILURE")

    @patch('configurator.routes.configuration_routes.FileIO')
    @patch('configurator.routes.configuration_routes.Configuration')
    def test_process_configurations_success(self, mock_configuration_class, mock_file_io):
        """Test successful POST /api/configurations/."""
        # Arrange
        # Create mock File objects with name attribute
        mock_file1 = Mock()
        mock_file1.name = "config1.yaml"
        mock_file2 = Mock()
        mock_file2.name = "config2.yaml"
        mock_files = [mock_file1, mock_file2]
        mock_file_io.get_documents.return_value = mock_files
        
        # Mock Configuration.process() to return ConfiguratorEvent objects
        mock_config1 = Mock()
        mock_event1 = ConfiguratorEvent("CFG-00", "PROCESS")
        mock_event1.record_success()
        mock_config1.process.return_value = mock_event1
        
        mock_config2 = Mock()
        mock_event2 = ConfiguratorEvent("CFG-00", "PROCESS")
        mock_event2.record_success()
        mock_config2.process.return_value = mock_event2
        
        mock_configuration_class.side_effect = [mock_config1, mock_config2]

        # Act
        response = self.client.post('/api/configurations/')

        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = response.json
        # For endpoints that return events, expect event envelope structure
        self.assertIn("id", response_data)
        self.assertIn("type", response_data)
        self.assertIn("status", response_data)
        self.assertEqual(response_data["status"], "SUCCESS")
        self.assertEqual(response_data["type"], "PROCESS_CONFIGURATIONS")
        self.assertIn("sub_events", response_data)

    @patch('configurator.routes.configuration_routes.FileIO')
    def test_process_configurations_general_exception(self, mock_file_io):
        """Test POST /api/configurations/ when FileIO raises a general exception."""
        # Arrange
        mock_file_io.get_documents.side_effect = Exception("Unexpected error")

        # Act
        response = self.client.post('/api/configurations/')

        # Assert
        self.assertEqual(response.status_code, 500)
        response_data = response.json
        self.assertIn("id", response_data)
        self.assertIn("type", response_data)
        self.assertIn("status", response_data)
        self.assertIn("data", response_data)
        self.assertEqual(response_data["status"], "FAILURE")

    @patch('configurator.routes.configuration_routes.Configuration')
    def test_get_configuration_success(self, mock_configuration_class):
        """Test successful GET /api/configurations/<file_name>/."""
        # Arrange
        mock_configuration = Mock()
        mock_configuration.to_dict.return_value = {"name": "test_config", "version": "1.0.0"}
        mock_configuration_class.return_value = mock_configuration

        # Act
        response = self.client.get('/api/configurations/test_config/')

        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = response.json
        # For successful responses, expect data directly, not wrapped in event envelope
        self.assertEqual(response_data, {"name": "test_config", "version": "1.0.0"})

    @patch('configurator.routes.configuration_routes.Configuration')
    def test_get_configuration_general_exception(self, mock_configuration_class):
        """Test GET /api/configurations/<file_name>/ when Configuration raises a general exception."""
        # Arrange
        mock_configuration_class.side_effect = Exception("Unexpected error")

        # Act
        response = self.client.get('/api/configurations/test_config/')

        # Assert
        self.assertEqual(response.status_code, 500)
        response_data = response.json
        self.assertIn("id", response_data)
        self.assertIn("type", response_data)
        self.assertIn("status", response_data)
        self.assertIn("data", response_data)
        self.assertEqual(response_data["status"], "FAILURE")

    @patch('configurator.routes.configuration_routes.Configuration')
    def test_put_configuration_success(self, mock_configuration_class):
        """Test successful PUT /api/configurations/<file_name>/."""
        # Arrange
        test_data = {"name": "test_config", "version": "1.0.0", "_locked": False}
        mock_configuration = Mock()
        mock_configuration.to_dict.return_value = {"name": "test_config", "version": "1.0.0", "_locked": False}
        mock_configuration.save.return_value = mock_configuration
        mock_configuration_class.return_value = mock_configuration

        # Act
        response = self.client.put('/api/configurations/test_config/', json=test_data)

        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = response.json
        # For successful responses, expect configuration data directly
        self.assertEqual(response_data, {"name": "test_config", "version": "1.0.0", "_locked": False})

    @patch('configurator.routes.configuration_routes.Configuration')
    def test_put_configuration_general_exception(self, mock_configuration_class):
        """Test PUT /api/configurations/<file_name>/ when Configuration raises a general exception."""
        # Arrange
        mock_configuration_class.side_effect = Exception("Unexpected error")
        test_data = {"name": "test_config", "version": "1.0.0"}

        # Act
        response = self.client.put('/api/configurations/test_config/', json=test_data)

        # Assert
        self.assertEqual(response.status_code, 500)
        response_data = response.json
        self.assertIn("id", response_data)
        self.assertIn("type", response_data)
        self.assertIn("status", response_data)
        self.assertIn("data", response_data)
        self.assertEqual(response_data["status"], "FAILURE")

    @patch('configurator.routes.configuration_routes.Configuration')
    def test_delete_configuration_success(self, mock_configuration_class):
        """Test successful DELETE /api/configurations/<file_name>/."""
        # Arrange
        mock_configuration = Mock()
        mock_event = Mock()
        mock_event.to_dict.return_value = {
            "id": "CFG-ROUTES-07",
            "type": "DELETE_CONFIGURATION",
            "status": "SUCCESS",
            "data": {},
            "sub_events": []
        }
        mock_configuration.delete.return_value = mock_event
        mock_configuration_class.return_value = mock_configuration

        # Act
        response = self.client.delete('/api/configurations/test_config/')

        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = response.json
        self.assertIn("id", response_data)
        self.assertIn("type", response_data)
        self.assertIn("status", response_data)
        self.assertIn("data", response_data)
        self.assertEqual(response_data["status"], "SUCCESS")

    @patch('configurator.routes.configuration_routes.Configuration')
    def test_delete_configuration_general_exception(self, mock_configuration_class):
        """Test DELETE /api/configurations/<file_name>/ when Configuration raises a general exception."""
        # Arrange
        mock_configuration = Mock()
        mock_configuration.delete.side_effect = Exception("Unexpected error")
        mock_configuration_class.return_value = mock_configuration

        # Act
        response = self.client.delete('/api/configurations/test_config/')

        # Assert
        self.assertEqual(response.status_code, 500)
        response_data = response.json
        self.assertIn("id", response_data)
        self.assertIn("type", response_data)
        self.assertIn("status", response_data)
        self.assertIn("data", response_data)
        self.assertEqual(response_data["status"], "FAILURE")

    @patch('configurator.routes.configuration_routes.Configuration')
    def test_lock_unlock_configuration_success(self, mock_configuration_class):
        """Test successful PATCH /api/configurations/<file_name>/ - removed as no longer supported."""
        # This test is no longer applicable as we removed lock/unlock functionality
        pass

    @patch('configurator.routes.configuration_routes.Configuration')
    def test_lock_unlock_configuration_general_exception(self, mock_configuration_class):
        """Test PATCH /api/configurations/<file_name>/ when Configuration raises a general exception - removed as no longer supported."""
        # This test is no longer applicable as we removed lock/unlock functionality
        pass

    @patch('configurator.routes.configuration_routes.Configuration')
    def test_process_configuration_success(self, mock_configuration_class):
        """Test successful POST /api/configurations/<file_name>/."""
        # Arrange
        mock_configuration = Mock()
        mock_event = Mock()
        mock_event.to_dict.return_value = {"result": "success"}
        mock_configuration.process.return_value = mock_event
        mock_configuration_class.return_value = mock_configuration

        # Act
        response = self.client.post('/api/configurations/test_config/')

        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = response.json
        # For successful responses, expect data directly, not wrapped in event envelope
        self.assertEqual(response_data, {"result": "success"})

    @patch('configurator.routes.configuration_routes.Configuration')
    def test_process_configuration_general_exception(self, mock_configuration_class):
        """Test POST /api/configurations/<file_name>/ when Configuration raises a general exception."""
        # Arrange
        mock_configuration = Mock()
        mock_configuration.process.side_effect = Exception("Unexpected error")
        mock_configuration_class.return_value = mock_configuration

        # Act
        response = self.client.post('/api/configurations/test_config/')

        # Assert
        self.assertEqual(response.status_code, 500)
        response_data = response.json
        self.assertIn("id", response_data)
        self.assertIn("type", response_data)
        self.assertIn("status", response_data)
        self.assertIn("data", response_data)
        self.assertEqual(response_data["status"], "FAILURE")

    @patch('configurator.routes.configuration_routes.Configuration')
    def test_get_json_schema_success(self, mock_configuration_class):
        """Test successful GET /api/configurations/json_schema/<file_name>/<version>/."""
        # Arrange
        mock_configuration = Mock()
        mock_configuration.get_json_schema.return_value = {"type": "object"}
        mock_configuration_class.return_value = mock_configuration

        # Act
        response = self.client.get('/api/configurations/json_schema/test_config/1.0.0/')

        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = response.json
        # For successful responses, expect data directly, not wrapped in event envelope
        self.assertEqual(response_data, {"type": "object"})

    @patch('configurator.routes.configuration_routes.Configuration')
    def test_get_json_schema_general_exception(self, mock_configuration_class):
        """Test GET /api/configurations/json_schema/<file_name>/<version>/ when Configuration raises a general exception."""
        # Arrange
        mock_configuration = Mock()
        mock_configuration.get_json_schema.side_effect = Exception("Unexpected error")
        mock_configuration_class.return_value = mock_configuration

        # Act
        response = self.client.get('/api/configurations/json_schema/test_config/1.0.0/')

        # Assert
        self.assertEqual(response.status_code, 500)
        response_data = response.json
        self.assertIn("id", response_data)
        self.assertIn("type", response_data)
        self.assertIn("status", response_data)
        self.assertIn("data", response_data)
        self.assertEqual(response_data["status"], "FAILURE")

    @patch('configurator.routes.configuration_routes.Configuration')
    def test_get_bson_schema_success(self, mock_configuration_class):
        """Test successful GET /api/configurations/bson_schema/<file_name>/<version>/."""
        # Arrange
        mock_configuration = Mock()
        mock_configuration.get_bson_schema_for_version.return_value = {"type": "object"}
        mock_configuration_class.return_value = mock_configuration

        # Act
        response = self.client.get('/api/configurations/bson_schema/test_config/1.0.0/')

        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = response.json
        # For successful responses, expect data directly, not wrapped in event envelope
        self.assertEqual(response_data, {"type": "object"})

    @patch('configurator.routes.configuration_routes.Configuration')
    def test_get_bson_schema_general_exception(self, mock_configuration_class):
        """Test GET /api/configurations/bson_schema/<file_name>/<version>/ when Configuration raises a general exception."""
        # Arrange
        mock_configuration = Mock()
        mock_configuration.get_bson_schema_for_version.side_effect = Exception("Unexpected error")
        mock_configuration_class.return_value = mock_configuration

        # Act
        response = self.client.get('/api/configurations/bson_schema/test_config/1.0.0/')

        # Assert
        self.assertEqual(response.status_code, 500)
        response_data = response.json
        self.assertIn("id", response_data)
        self.assertIn("type", response_data)
        self.assertIn("status", response_data)
        self.assertIn("data", response_data)
        self.assertEqual(response_data["status"], "FAILURE")

    @patch('configurator.routes.configuration_routes.TemplateService')
    def test_create_collection_success(self, mock_template_service_class):
        """Test successful POST /api/configurations/collection/<file_name>."""
        # Arrange
        mock_template_service = Mock()
        mock_template_service.create_collection.return_value = {"created": True}
        mock_template_service_class.return_value = mock_template_service

        # Act
        response = self.client.post('/api/configurations/collection/test_collection/')

        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = response.json
        # For successful responses, expect data directly, not wrapped in event envelope
        self.assertEqual(response_data, {"created": True})

    @patch('configurator.routes.configuration_routes.TemplateService')
    def test_create_collection_configurator_exception(self, mock_template_service_class):
        """Test POST /api/configurations/collection/<file_name> when TemplateService raises ConfiguratorException."""
        # Arrange
        mock_template_service = Mock()
        event = ConfiguratorEvent("TPL-01", "TEMPLATE_ERROR")
        mock_template_service.create_collection.side_effect = ConfiguratorException("Template error", event)
        mock_template_service_class.return_value = mock_template_service

        # Act
        response = self.client.post('/api/configurations/collection/test_collection/')

        # Assert
        self.assertEqual(response.status_code, 500)
        response_data = response.json
        self.assertIn("id", response_data)
        self.assertIn("type", response_data)
        self.assertIn("status", response_data)
        self.assertIn("data", response_data)
        self.assertEqual(response_data["status"], "FAILURE")

    @patch('configurator.routes.configuration_routes.TemplateService')
    def test_create_collection_general_exception(self, mock_template_service_class):
        """Test POST /api/configurations/collection/<file_name> when TemplateService raises a general exception."""
        # Arrange
        mock_template_service = Mock()
        mock_template_service.create_collection.side_effect = Exception("Unexpected error")
        mock_template_service_class.return_value = mock_template_service

        # Act
        response = self.client.post('/api/configurations/collection/test_collection/')

        # Assert
        self.assertEqual(response.status_code, 500)
        response_data = response.json
        self.assertIn("id", response_data)
        self.assertIn("type", response_data)
        self.assertIn("status", response_data)
        self.assertIn("data", response_data)
        self.assertEqual(response_data["status"], "FAILURE")

    @patch('configurator.routes.configuration_routes.Configuration')
    def test_lock_all_configurations(self, mock_configuration_class):
        """Test locking all configurations."""
        # Arrange
        mock_event = ConfiguratorEvent("CFG-ROUTES-03", "LOCK_ALL_CONFIGURATIONS")
        mock_event.data = {
            "total_files": 2,
            "operation": "lock_all"
        }
        mock_event.record_success()
        mock_configuration_class.lock_all.return_value = mock_event

        # Act
        response = self.client.patch('/api/configurations/')

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('id', data)
        self.assertIn('type', data)
        self.assertIn('status', data)
        self.assertIn('sub_events', data)
        self.assertIn('data', data)
        self.assertIn('total_files', data['data'])
        self.assertIn('operation', data['data'])


if __name__ == '__main__':
    unittest.main()