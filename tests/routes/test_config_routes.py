import unittest
from flask import Flask
from configurator.routes.config_routes import create_config_routes


class TestConfigRoutes(unittest.TestCase):
    """Test cases for config routes."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = Flask(__name__)
        self.app.register_blueprint(create_config_routes(), url_prefix='/api/config')
        self.client = self.app.test_client()

    def test_get_config_success(self):
        """Test successful GET /api/config."""
        # Act
        response = self.client.get('/api/config')

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertIn("config_items", response.json)
        self.assertIsInstance(response.json["config_items"], list)
        # Check that at least one expected config item is present
        config_names = [item["name"] for item in response.json["config_items"]]
        self.assertIn("MONGO_DB_NAME", config_names)
        self.assertIn("API_PORT", config_names)

    def test_get_config_method_not_allowed(self):
        """Test that POST method is not allowed on /api/config."""
        # Act
        response = self.client.post('/api/config')

        # Assert
        self.assertEqual(response.status_code, 405)

    def test_get_config_put_method_not_allowed(self):
        """Test that PUT method is not allowed on /api/config."""
        # Act
        response = self.client.put('/api/config')

        # Assert
        self.assertEqual(response.status_code, 405)

    def test_get_config_delete_method_not_allowed(self):
        """Test that DELETE method is not allowed on /api/config."""
        # Act
        response = self.client.delete('/api/config')

        # Assert
        self.assertEqual(response.status_code, 405)

    def test_get_config_configurator_exception(self):
        """Test GET /api/config when ConfiguratorException is raised."""
        # Patch Config.get_instance().to_dict to raise ConfiguratorException
        from configurator.utils.configurator_exception import ConfiguratorException, ConfiguratorEvent
        import configurator.routes.config_routes as config_routes_mod
        orig_get_instance = config_routes_mod.Config.get_instance
        class DummyConfig:
            def to_dict(self):
                raise ConfiguratorException("Config error", ConfiguratorEvent("CFG-01", "CONFIG_ERROR"))
        config_routes_mod.Config.get_instance = staticmethod(lambda: DummyConfig())
        try:
            app = Flask(__name__)
            app.register_blueprint(config_routes_mod.create_config_routes(), url_prefix='/api/config')
            client = app.test_client()
            response = client.get('/api/config')
            self.assertEqual(response.status_code, 500)
            self.assertIsInstance(response.json, dict)
            self.assertIn("id", response.json)
            self.assertIn("type", response.json)
        finally:
            config_routes_mod.Config.get_instance = orig_get_instance

    def test_get_config_general_exception(self):
        """Test GET /api/config when a general Exception is raised."""
        import configurator.routes.config_routes as config_routes_mod
        orig_get_instance = config_routes_mod.Config.get_instance
        class DummyConfig:
            def to_dict(self):
                raise Exception("General error")
        config_routes_mod.Config.get_instance = staticmethod(lambda: DummyConfig())
        try:
            app = Flask(__name__)
            app.register_blueprint(config_routes_mod.create_config_routes(), url_prefix='/api/config')
            client = app.test_client()
            response = client.get('/api/config')
            self.assertEqual(response.status_code, 500)
            self.assertEqual(response.json, "General error")
        finally:
            config_routes_mod.Config.get_instance = orig_get_instance


if __name__ == '__main__':
    unittest.main()