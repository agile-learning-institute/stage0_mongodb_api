import unittest
from unittest.mock import patch, Mock
from flask import Flask
from configurator.routes.database_routes import create_database_routes
from configurator.utils.configurator_exception import ConfiguratorException, ConfiguratorEvent


class TestDatabaseRoutes(unittest.TestCase):
    """Test cases for database routes."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = Flask(__name__)
        self.app.register_blueprint(create_database_routes(), url_prefix='/api/database')
        self.client = self.app.test_client()

    @patch('configurator.routes.database_routes.MongoIO')
    def test_drop_database_success(self, mock_mongo_io_class):
        """Test successful DELETE /api/database."""
        # Arrange
        mock_mongo_io = Mock()
        mock_mongo_io_class.return_value = mock_mongo_io

        # Act
        response = self.client.delete('/api/database/')

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, "Database Dropped")
        mock_mongo_io.drop_database.assert_called_once()
        mock_mongo_io.disconnect.assert_called_once()

    @patch('configurator.routes.database_routes.MongoIO')
    def test_drop_database_configurator_exception(self, mock_mongo_io_class):
        """Test DELETE /api/database when MongoIO raises ConfiguratorException."""
        # Arrange
        mock_mongo_io = Mock()
        mock_event = ConfiguratorEvent("TEST-01", "TEST", {"error": "test"})
        mock_mongo_io.drop_database.side_effect = ConfiguratorException("Database error", mock_event)
        mock_mongo_io_class.return_value = mock_mongo_io

        # Act
        response = self.client.delete('/api/database/')

        # Assert
        self.assertEqual(response.status_code, 500)
        # The response should contain the to_dict() structure from the exception
        self.assertIsInstance(response.json, dict)
        self.assertIn("id", response.json)
        self.assertIn("type", response.json)

    @patch('configurator.routes.database_routes.MongoIO')
    def test_drop_database_safety_limit_exceeded(self, mock_mongo_io_class):
        """Test DELETE /api/database when collections have more than 100 documents."""
        # Arrange
        mock_mongo_io = Mock()
        mock_event = ConfiguratorEvent(
            "MON-14", 
            "DROP_DATABASE", 
            {"collections_exceeding_limit": [
                {"collection": "users", "document_count": 150},
                {"collection": "orders", "document_count": 200}
            ]}
        )
        mock_mongo_io.drop_database.side_effect = ConfiguratorException(
            "Drop database Safety Limit Exceeded - Collections with >100 documents found", 
            mock_event
        )
        mock_mongo_io_class.return_value = mock_mongo_io

        # Act
        response = self.client.delete('/api/database/')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertIsInstance(response.json, dict)
        self.assertIn("id", response.json)
        self.assertIn("type", response.json)

    @patch('configurator.routes.database_routes.MongoIO')
    def test_drop_database_general_exception(self, mock_mongo_io_class):
        """Test DELETE /api/database when MongoIO raises a general exception."""
        # Arrange
        mock_mongo_io = Mock()
        mock_mongo_io.drop_database.side_effect = Exception("Unexpected error")
        mock_mongo_io_class.return_value = mock_mongo_io

        # Act
        response = self.client.delete('/api/database/')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertIsInstance(response.json, str)
        self.assertIn("Unexpected error", response.json)

    def test_drop_database_get_method_not_allowed(self):
        """Test that GET method is not allowed on /api/database."""
        # Act
        response = self.client.get('/api/database/')

        # Assert
        self.assertEqual(response.status_code, 405)

    def test_drop_database_post_method_not_allowed(self):
        """Test that POST method is not allowed on /api/database."""
        # Act
        response = self.client.post('/api/database/')

        # Assert
        self.assertEqual(response.status_code, 405)

    def test_drop_database_put_method_not_allowed(self):
        """Test that PUT method is not allowed on /api/database."""
        # Act
        response = self.client.put('/api/database/')

        # Assert
        self.assertEqual(response.status_code, 405)

    def test_drop_database_patch_method_not_allowed(self):
        """Test that PATCH method is not allowed on /api/database."""
        # Act
        response = self.client.patch('/api/database/')

        # Assert
        self.assertEqual(response.status_code, 405)


if __name__ == '__main__':
    unittest.main()