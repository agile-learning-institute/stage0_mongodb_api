import unittest
from unittest.mock import patch, Mock
from flask import Flask
from configurator.routes.configuration_routes import create_configuration_routes
from configurator.utils.configurator_exception import ConfiguratorException


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
        mock_file_io.get_files.return_value = [
            {
                "name": "config1.yaml",
                "read_only": False,
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00",
                "size": 1024
            },
            {
                "name": "config2.yaml",
                "read_only": True,
                "created_at": "2023-01-02T00:00:00",
                "updated_at": "2023-01-02T00:00:00",
                "size": 2048
            }
        ]

        # Act
        response = self.client.get('/api/configurations/')

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 2)
        mock_file_io.get_files.assert_called_once_with("configurations")

    @patch('configurator.routes.configuration_routes.FileIO')
    def test_list_configurations_configurator_exception(self, mock_file_io):
        """Test GET /api/configurations/ when FileIO raises ConfiguratorException."""
        # Arrange
        mock_file_io.get_files.side_effect = ConfiguratorException("File error", Mock())

        # Act
        response = self.client.get('/api/configurations/')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertIsInstance(response.json, list)

    @patch('configurator.routes.configuration_routes.FileIO')
    def test_list_configurations_general_exception(self, mock_file_io):
        """Test GET /api/configurations/ when FileIO raises a general exception."""
        # Arrange
        mock_file_io.get_files.side_effect = Exception("Unexpected error")

        # Act
        response = self.client.get('/api/configurations/')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json, "Undefined Exception")

    @patch('configurator.routes.configuration_routes.FileIO')
    @patch('configurator.routes.configuration_routes.Configuration')
    def test_process_configurations_success(self, mock_configuration_class, mock_file_io):
        """Test successful POST /api/configurations/."""
        # Arrange
        mock_file_io.get_documents.return_value = ["config1.yaml", "config2.yaml"]
        
        mock_config1 = Mock()
        mock_config1.process.return_value = {"status": "processed", "name": "config1"}
        mock_config2 = Mock()
        mock_config2.process.return_value = {"status": "processed", "name": "config2"}
        
        mock_configuration_class.side_effect = [mock_config1, mock_config2]

        # Act
        response = self.client.post('/api/configurations/')

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 2)
        mock_file_io.get_documents.assert_called_once_with("configurations")
        mock_configuration_class.assert_any_call("config1.yaml")
        mock_configuration_class.assert_any_call("config2.yaml")
        mock_config1.process.assert_called_once()
        mock_config2.process.assert_called_once()

    @patch('configurator.routes.configuration_routes.FileIO')
    def test_process_configurations_configurator_exception(self, mock_file_io):
        """Test POST /api/configurations/ when FileIO raises ConfiguratorException."""
        # Arrange
        mock_file_io.get_documents.side_effect = ConfiguratorException("File error", Mock())

        # Act
        response = self.client.post('/api/configurations/')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertIsInstance(response.json, list)

    @patch('configurator.routes.configuration_routes.FileIO')
    def test_process_configurations_general_exception(self, mock_file_io):
        """Test POST /api/configurations/ when FileIO raises a general exception."""
        # Arrange
        mock_file_io.get_documents.side_effect = Exception("Unexpected error")

        # Act
        response = self.client.post('/api/configurations/')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json, "Undefined Exception")

    @patch('configurator.routes.configuration_routes.Configuration')
    def test_get_configuration_success(self, mock_configuration_class):
        """Test successful GET /api/configurations/<file_name>/."""
        # Arrange
        mock_configuration = Mock()
        mock_configuration.to_dict.return_value = {
            "name": "test_config",
            "title": "Test Configuration",
            "description": "A test configuration",
            "versions": []
        }
        mock_configuration_class.return_value = mock_configuration

        # Act
        response = self.client.get('/api/configurations/test_config.yaml/')

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["name"], "test_config")
        mock_configuration_class.assert_called_once_with("test_config.yaml")

    @patch('configurator.routes.configuration_routes.Configuration')
    def test_get_configuration_configurator_exception(self, mock_configuration_class):
        """Test GET /api/configurations/<file_name>/ when Configuration raises ConfiguratorException."""
        # Arrange
        mock_configuration_class.side_effect = ConfiguratorException("Configuration error", Mock())

        # Act
        response = self.client.get('/api/configurations/test_config.yaml/')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertIsInstance(response.json, list)

    @patch('configurator.routes.configuration_routes.Configuration')
    def test_get_configuration_general_exception(self, mock_configuration_class):
        """Test GET /api/configurations/<file_name>/ when Configuration raises a general exception."""
        # Arrange
        mock_configuration_class.side_effect = Exception("Unexpected error")

        # Act
        response = self.client.get('/api/configurations/test_config.yaml/')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json, "Undefined Exception")

    @patch('configurator.routes.configuration_routes.Configuration')
    def test_put_configuration_success(self, mock_configuration_class):
        """Test successful PUT /api/configurations/<file_name>/."""
        # Arrange
        mock_configuration = Mock()
        mock_configuration.save.return_value = {
            "name": "test_config",
            "saved": True
        }
        mock_configuration_class.return_value = mock_configuration

        test_data = {
            "name": "test_config",
            "title": "Updated Test Configuration",
            "description": "Updated test configuration",
            "versions": []
        }

        # Act
        response = self.client.put('/api/configurations/test_config.yaml/', json=test_data)

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["saved"], True)
        mock_configuration_class.assert_called_once_with("test_config.yaml", test_data)
        mock_configuration.save.assert_called_once()

    @patch('configurator.routes.configuration_routes.Configuration')
    def test_put_configuration_configurator_exception(self, mock_configuration_class):
        """Test PUT /api/configurations/<file_name>/ when Configuration raises ConfiguratorException."""
        # Arrange
        mock_configuration = Mock()
        mock_configuration.save.side_effect = ConfiguratorException("Save error", Mock())
        mock_configuration_class.return_value = mock_configuration

        test_data = {"name": "test_config"}

        # Act
        response = self.client.put('/api/configurations/test_config.yaml/', json=test_data)

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertIsInstance(response.json, list)

    @patch('configurator.routes.configuration_routes.Configuration')
    def test_put_configuration_general_exception(self, mock_configuration_class):
        """Test PUT /api/configurations/<file_name>/ when Configuration raises a general exception."""
        # Arrange
        mock_configuration = Mock()
        mock_configuration.save.side_effect = Exception("Unexpected error")
        mock_configuration_class.return_value = mock_configuration

        test_data = {"name": "test_config"}

        # Act
        response = self.client.put('/api/configurations/test_config.yaml/', json=test_data)

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json, "Undefined Exception")

    @patch('configurator.routes.configuration_routes.Configuration')
    def test_delete_configuration_success(self, mock_configuration_class):
        """Test successful DELETE /api/configurations/<file_name>/."""
        # Arrange
        mock_configuration = Mock()
        mock_configuration.delete.return_value = {
            "name": "test_config",
            "deleted": True
        }
        mock_configuration_class.return_value = mock_configuration

        # Act
        response = self.client.delete('/api/configurations/test_config.yaml/')

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["deleted"], True)
        mock_configuration_class.assert_called_once_with("test_config.yaml")
        mock_configuration.delete.assert_called_once()

    @patch('configurator.routes.configuration_routes.Configuration')
    def test_delete_configuration_configurator_exception(self, mock_configuration_class):
        """Test DELETE /api/configurations/<file_name>/ when Configuration raises ConfiguratorException."""
        # Arrange
        mock_configuration = Mock()
        mock_configuration.delete.side_effect = ConfiguratorException("Delete error", Mock())
        mock_configuration_class.return_value = mock_configuration

        # Act
        response = self.client.delete('/api/configurations/test_config.yaml/')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertIsInstance(response.json, list)

    @patch('configurator.routes.configuration_routes.Configuration')
    def test_delete_configuration_general_exception(self, mock_configuration_class):
        """Test DELETE /api/configurations/<file_name>/ when Configuration raises a general exception."""
        # Arrange
        mock_configuration = Mock()
        mock_configuration.delete.side_effect = Exception("Unexpected error")
        mock_configuration_class.return_value = mock_configuration

        # Act
        response = self.client.delete('/api/configurations/test_config.yaml/')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json, "Undefined Exception")

    @patch('configurator.routes.configuration_routes.Configuration')
    def test_lock_unlock_configuration_success(self, mock_configuration_class):
        """Test successful PATCH /api/configurations/<file_name>/."""
        # Arrange
        mock_configuration = Mock()
        mock_configuration.flip_lock.return_value = {
            "name": "test_config",
            "read_only": True
        }
        mock_configuration_class.return_value = mock_configuration

        # Act
        response = self.client.patch('/api/configurations/test_config.yaml/')

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["read_only"], True)
        mock_configuration_class.assert_called_once_with("test_config.yaml")
        mock_configuration.flip_lock.assert_called_once()

    @patch('configurator.routes.configuration_routes.Configuration')
    def test_lock_unlock_configuration_configurator_exception(self, mock_configuration_class):
        """Test PATCH /api/configurations/<file_name>/ when Configuration raises ConfiguratorException."""
        # Arrange
        mock_configuration = Mock()
        mock_configuration.flip_lock.side_effect = ConfiguratorException("Lock error", Mock())
        mock_configuration_class.return_value = mock_configuration

        # Act
        response = self.client.patch('/api/configurations/test_config.yaml/')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertIsInstance(response.json, list)

    @patch('configurator.routes.configuration_routes.Configuration')
    def test_lock_unlock_configuration_general_exception(self, mock_configuration_class):
        """Test PATCH /api/configurations/<file_name>/ when Configuration raises a general exception."""
        # Arrange
        mock_configuration = Mock()
        mock_configuration.flip_lock.side_effect = Exception("Unexpected error")
        mock_configuration_class.return_value = mock_configuration

        # Act
        response = self.client.patch('/api/configurations/test_config.yaml/')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json, "Undefined Exception")

    @patch('configurator.routes.configuration_routes.Configuration')
    def test_process_configuration_success(self, mock_configuration_class):
        """Test successful POST /api/configurations/<file_name>/."""
        # Arrange
        mock_configuration = Mock()
        mock_configuration.process.return_value = {
            "status": "processed",
            "name": "test_config"
        }
        mock_configuration_class.return_value = mock_configuration

        # Act
        response = self.client.post('/api/configurations/test_config.yaml/')

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["status"], "processed")
        mock_configuration_class.assert_called_once_with("test_config.yaml")
        mock_configuration.process.assert_called_once()

    @patch('configurator.routes.configuration_routes.Configuration')
    def test_process_configuration_configurator_exception(self, mock_configuration_class):
        """Test POST /api/configurations/<file_name>/ when Configuration raises ConfiguratorException."""
        # Arrange
        mock_configuration = Mock()
        mock_configuration.process.side_effect = ConfiguratorException("Process error", Mock())
        mock_configuration_class.return_value = mock_configuration

        # Act
        response = self.client.post('/api/configurations/test_config.yaml/')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertIsInstance(response.json, list)

    @patch('configurator.routes.configuration_routes.Configuration')
    def test_process_configuration_general_exception(self, mock_configuration_class):
        """Test POST /api/configurations/<file_name>/ when Configuration raises a general exception."""
        # Arrange
        mock_configuration = Mock()
        mock_configuration.process.side_effect = Exception("Unexpected error")
        mock_configuration_class.return_value = mock_configuration

        # Act
        response = self.client.post('/api/configurations/test_config.yaml/')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json, "Undefined Exception")

    @patch('configurator.routes.configuration_routes.Configuration')
    def test_get_json_schema_success(self, mock_configuration_class):
        """Test successful GET /api/configurations/json_schema/<file_name>/<version>/."""
        # Arrange
        mock_configuration = Mock()
        mock_configuration.get_json_schema.return_value = {
            "type": "object",
            "properties": {"field1": {"type": "string"}}
        }
        mock_configuration_class.return_value = mock_configuration

        # Act
        response = self.client.get('/api/configurations/json_schema/test_config.yaml/1.0.0/')

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["type"], "object")
        mock_configuration_class.assert_called_once_with("test_config.yaml")
        mock_configuration.get_json_schema.assert_called_once_with("1.0.0")

    @patch('configurator.routes.configuration_routes.Configuration')
    def test_get_json_schema_configurator_exception(self, mock_configuration_class):
        """Test GET /api/configurations/json_schema/<file_name>/<version>/ when Configuration raises ConfiguratorException."""
        # Arrange
        mock_configuration = Mock()
        mock_configuration.get_json_schema.side_effect = ConfiguratorException("Schema error", Mock())
        mock_configuration_class.return_value = mock_configuration

        # Act
        response = self.client.get('/api/configurations/json_schema/test_config.yaml/1.0.0/')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertIsInstance(response.json, list)

    @patch('configurator.routes.configuration_routes.Configuration')
    def test_get_json_schema_general_exception(self, mock_configuration_class):
        """Test GET /api/configurations/json_schema/<file_name>/<version>/ when Configuration raises a general exception."""
        # Arrange
        mock_configuration = Mock()
        mock_configuration.get_json_schema.side_effect = Exception("Unexpected error")
        mock_configuration_class.return_value = mock_configuration

        # Act
        response = self.client.get('/api/configurations/json_schema/test_config.yaml/1.0.0/')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json, "Undefined Exception")

    @patch('configurator.routes.configuration_routes.Configuration')
    def test_get_bson_schema_success(self, mock_configuration_class):
        """Test successful GET /api/configurations/bson_schema/<file_name>/<version>/."""
        # Arrange
        mock_configuration = Mock()
        mock_configuration.get_bson_schema.return_value = {
            "bsonType": "object",
            "properties": {"field1": {"bsonType": "string"}}
        }
        mock_configuration_class.return_value = mock_configuration

        # Act
        response = self.client.get('/api/configurations/bson_schema/test_config.yaml/1.0.0/')

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["bsonType"], "object")
        mock_configuration_class.assert_called_once_with("test_config.yaml")
        mock_configuration.get_bson_schema.assert_called_once_with("1.0.0")

    @patch('configurator.routes.configuration_routes.Configuration')
    def test_get_bson_schema_configurator_exception(self, mock_configuration_class):
        """Test GET /api/configurations/bson_schema/<file_name>/<version>/ when Configuration raises ConfiguratorException."""
        # Arrange
        mock_configuration = Mock()
        mock_configuration.get_bson_schema.side_effect = ConfiguratorException("Schema error", Mock())
        mock_configuration_class.return_value = mock_configuration

        # Act
        response = self.client.get('/api/configurations/bson_schema/test_config.yaml/1.0.0/')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertIsInstance(response.json, list)

    @patch('configurator.routes.configuration_routes.Configuration')
    def test_get_bson_schema_general_exception(self, mock_configuration_class):
        """Test GET /api/configurations/bson_schema/<file_name>/<version>/ when Configuration raises a general exception."""
        # Arrange
        mock_configuration = Mock()
        mock_configuration.get_bson_schema.side_effect = Exception("Unexpected error")
        mock_configuration_class.return_value = mock_configuration

        # Act
        response = self.client.get('/api/configurations/bson_schema/test_config.yaml/1.0.0/')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json, "Undefined Exception")

    def test_configurations_method_not_allowed(self):
        """Test that methods not defined are not allowed."""
        # Test PUT on root
        response = self.client.put('/api/configurations/')
        self.assertEqual(response.status_code, 405)

        # Test DELETE on root
        response = self.client.delete('/api/configurations/')
        self.assertEqual(response.status_code, 405)

        # Test PATCH on root
        response = self.client.patch('/api/configurations/')
        self.assertEqual(response.status_code, 405)


if __name__ == '__main__':
    unittest.main()