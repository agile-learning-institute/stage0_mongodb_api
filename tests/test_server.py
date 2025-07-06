import unittest
from unittest.mock import patch, MagicMock

# Patch Config before importing the app
with patch('configurator.utils.config.Config.get_instance') as mock_config_get:
    mock_config = MagicMock()
    mock_config.AUTO_PROCESS = False
    mock_config.EXIT_AFTER_PROCESSING = False
    mock_config.API_PORT = 8081
    mock_config.BUILT_AT = "test"
    mock_config_get.return_value = mock_config
    from configurator.server import app

class TestServer(unittest.TestCase):
    """Test suite for server initialization and configuration."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = app.test_client()

    def test_app_initialization(self):
        """Test Flask app initialization."""
        # Assert
        self.assertIsNotNone(app)
        self.assertEqual(app.name, 'configurator.server')

    def test_health_endpoint(self):
        """Test health check endpoint."""
        # Act
        response = self.app.get('/api/health')

        # Assert
        self.assertEqual(response.status_code, 200)

    def test_config_routes_registered(self):
        """Test config routes are registered."""
        # Act
        response = self.app.get('/api/config')

        # Assert
        self.assertNotEqual(response.status_code, 404)

    def test_configuration_routes_registered(self):
        """Test configuration routes are registered."""
        # Act
        response = self.app.get('/api/configurations')

        # Assert
        self.assertNotEqual(response.status_code, 404)

    def test_dictionary_routes_registered(self):
        """Test dictionary routes are registered."""
        # Act
        response = self.app.get('/api/dictionaries')

        # Assert
        self.assertNotEqual(response.status_code, 404)

    def test_type_routes_registered(self):
        """Test type routes are registered."""
        # Act
        response = self.app.get('/api/types')

        # Assert
        self.assertNotEqual(response.status_code, 404)

    def test_database_routes_registered(self):
        """Test database routes are registered."""
        # Act
        response = self.app.get('/api/database')

        # Assert
        self.assertNotEqual(response.status_code, 404)

    def test_enumerator_routes_registered(self):
        """Test enumerator routes are registered."""
        # Act
        response = self.app.get('/api/enumerators')

        # Assert
        self.assertNotEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main()
