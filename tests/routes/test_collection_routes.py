import unittest
from unittest.mock import patch, MagicMock
from flask import Flask
from stage0_mongodb_api.routes.collection_routes import create_collection_routes

class TestCollectionRoutes(unittest.TestCase):
    def setUp(self):
        """Set up the Flask test client and app context."""
        self.app = Flask(__name__)
        self.app.register_blueprint(create_collection_routes(), url_prefix='/api/collection')
        self.client = self.app.test_client()

    def test_something(self):
        """Test Something"""
        # Arrange

        # Act
        response = self.client.get('/api/workshop?query=name')

        # Assert
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()