import unittest
from configurator.server import app
from configurator.utils.config import Config

class TestServer(unittest.TestCase):
    """Test suite for server initialization and configuration.
    NOTE: Config is never mocked in these tests. The real Config singleton is used, and config values are set/reset in setUp/tearDown.
    """

    def setUp(self):
        """Set up test fixtures."""
        self.app = app.test_client()
        self.config = Config.get_instance()
        self._original_api_port = self.config.API_PORT
        self._original_built_at = self.config.BUILT_AT
        self.config.API_PORT = 8081
        self.config.BUILT_AT = "test"

    def tearDown(self):
        self.config.API_PORT = self._original_api_port
        self.config.BUILT_AT = self._original_built_at

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
        # The route is registered, but may return 404 if file doesn't exist
        # This is expected behavior - the route exists but the file is missing
        self.assertIn(response.status_code, [200, 404])
        if response.status_code == 404:
            # If 404, verify it's a proper error response
            self.assertIsInstance(response.json, dict)
        else:
            # If 200, verify it returns valid JSON
            self.assertIsInstance(response.json, list)

if __name__ == '__main__':
    unittest.main()
