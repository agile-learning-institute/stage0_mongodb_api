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

    @patch('stage0_mongodb_api.routes.collection_routes.CollectionService')
    def test_list_collections(self, mock_collection_service):
        """Test listing all collections"""
        # Arrange
        mock_collections = [
            {"name": "users", "current_version": "1.0.0.0"},
            {"name": "organizations", "current_version": "1.0.0.0"}
        ]
        mock_collection_service.return_value.list_collections.return_value = mock_collections

        # Act
        response = self.client.get('/api/collection')

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, mock_collections)
        mock_collection_service.return_value.list_collections.assert_called_once()

    @patch('stage0_mongodb_api.routes.collection_routes.CollectionService')
    def test_process_collections(self, mock_collection_service):
        """Test processing all collections"""
        # Arrange
        mock_results = [
            {"status": "success", "collection": "users", "operations": []},
            {"status": "success", "collection": "organizations", "operations": []}
        ]
        mock_collection_service.return_value.process_collections.return_value = mock_results

        # Act
        response = self.client.post('/api/collection')

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, mock_results)
        mock_collection_service.return_value.process_collections.assert_called_once()

    @patch('stage0_mongodb_api.routes.collection_routes.CollectionService')
    def test_process_specific_collection(self, mock_collection_service):
        """Test processing a specific collection"""
        # Arrange
        collection_name = "users"
        mock_result = {
            "status": "success",
            "collection": collection_name,
            "operations": []
        }
        mock_collection_service.return_value.process_collection.return_value = mock_result

        # Act
        response = self.client.post(f'/api/collection/{collection_name}')

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, mock_result)
        mock_collection_service.return_value.process_collection.assert_called_once_with(collection_name)

    @patch('stage0_mongodb_api.routes.collection_routes.CollectionService')
    def test_process_nonexistent_collection(self, mock_collection_service):
        """Test processing a collection that doesn't exist"""
        # Arrange
        collection_name = "nonexistent"
        mock_result = {
            "status": "error",
            "collection": collection_name,
            "error": "Collection configuration not found"
        }
        mock_collection_service.return_value.process_collection.return_value = mock_result

        # Act
        response = self.client.post(f'/api/collection/{collection_name}')

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, mock_result)
        mock_collection_service.return_value.process_collection.assert_called_once_with(collection_name)

if __name__ == '__main__':
    unittest.main()