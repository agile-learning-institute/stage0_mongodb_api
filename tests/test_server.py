import unittest
from unittest.mock import patch, MagicMock
import signal
import sys

# Patch MongoIO before importing server
with patch('stage0_py_utils.MongoIO.get_instance') as mock_get_instance:
    mock_get_instance.return_value = MagicMock()
    from stage0_mongodb_api.server import app, handle_exit

class TestServer(unittest.TestCase):
    """Test suite for server initialization and configuration."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = app.test_client()

    def test_app_initialization(self):
        """Test Flask app initialization."""
        # Assert
        self.assertIsNotNone(app)
        self.assertEqual(app.name, 'stage0_mongodb_api.server')

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

    def test_collection_routes_registered(self):
        """Test collection routes are registered."""
        # Act
        response = self.app.get('/api/collections')

        # Assert
        self.assertNotEqual(response.status_code, 404)

    def test_render_routes_registered(self):
        """Test render routes are registered."""
        # Act
        response = self.app.get('/api/render/json_schema/users')

        # Assert
        self.assertNotEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main()
