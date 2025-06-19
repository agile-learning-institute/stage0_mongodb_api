import unittest
from unittest.mock import patch, MagicMock
from flask import Flask
from stage0_mongodb_api.routes.collection_routes import create_collection_routes
from stage0_mongodb_api.services.collection_service import CollectionNotFoundError, CollectionProcessingError

class TestCollectionRoutes(unittest.TestCase):
    def setUp(self):
        """Set up the Flask test client and app context."""
        self.app = Flask(__name__)
        self.app.register_blueprint(create_collection_routes(), url_prefix='/api/collections')
        self.client = self.app.test_client()

    @patch('stage0_mongodb_api.routes.collection_routes.CollectionService')
    def test_list_collections_success(self, mock_collection_service):
        """Test listing all collections successfully"""
        # Arrange
        mock_collections = {
            "users": "1.0.0.1",
            "organizations": "1.0.0.1"
        }
        mock_collection_service.list_collections.return_value = mock_collections

        # Act
        response = self.client.get('/api/collections/')

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, mock_collections)
        mock_collection_service.list_collections.assert_called_once()

    @patch('stage0_mongodb_api.routes.collection_routes.CollectionService')
    def test_list_collections_processing_error(self, mock_collection_service):
        """Test listing collections with processing error"""
        # Arrange
        errors = [{"error": "load_error", "error_id": "CFG-001", "message": "Failed to load configs"}]
        mock_collection_service.list_collections.side_effect = CollectionProcessingError("collections", errors)

        # Act
        response = self.client.get('/api/collections/')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json, errors)

    @patch('stage0_mongodb_api.routes.collection_routes.CollectionService')
    def test_list_collections_unexpected_error(self, mock_collection_service):
        """Test listing collections with unexpected error"""
        # Arrange
        mock_collection_service.list_collections.side_effect = Exception("Unexpected error")

        # Act
        response = self.client.get('/api/collections/')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json[0]["error"], "Failed to list collections")
        self.assertEqual(response.json[0]["error_id"], "API-001")

    @patch('stage0_mongodb_api.routes.collection_routes.CollectionService')
    def test_process_collections_success(self, mock_collection_service):
        """Test processing all collections successfully"""
        # Arrange
        mock_results = [
            {"status": "success", "collection": "users", "operations": []},
            {"status": "success", "collection": "organizations", "operations": []}
        ]
        mock_collection_service.process_collections.return_value = mock_results

        # Act
        response = self.client.post('/api/collections/')

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, mock_results)
        mock_collection_service.process_collections.assert_called_once()

    @patch('stage0_mongodb_api.routes.collection_routes.CollectionService')
    def test_process_collections_processing_error(self, mock_collection_service):
        """Test processing collections with processing error"""
        # Arrange
        errors = [{"error": "validation_error", "error_id": "CFG-101", "message": "Invalid config format"}]
        mock_collection_service.process_collections.side_effect = CollectionProcessingError("collections", errors)

        # Act
        response = self.client.post('/api/collections/')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json, errors)

    @patch('stage0_mongodb_api.routes.collection_routes.CollectionService')
    def test_get_collection_success(self, mock_collection_service):
        """Test getting a specific collection successfully"""
        # Arrange
        collection_name = "users"
        mock_collection = {"name": "users", "versions": [{"version": "1.0.0.1"}]}
        mock_collection_service.get_collection.return_value = mock_collection

        # Act
        response = self.client.get(f'/api/collections/users')

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, mock_collection)
        mock_collection_service.get_collection.assert_called_once()

    @patch('stage0_mongodb_api.routes.collection_routes.CollectionService')
    def test_get_collection_not_found(self, mock_collection_service):
        """Test getting a collection that doesn't exist"""
        # Arrange
        collection_name = "nonexistent"
        mock_collection_service.get_collection.side_effect = CollectionNotFoundError(collection_name)

        # Act
        response = self.client.get(f'/api/collections/{collection_name}')

        # Assert
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data.decode(), "Collection not found")

    @patch('stage0_mongodb_api.routes.collection_routes.CollectionService')
    def test_get_collection_processing_error(self, mock_collection_service):
        """Test getting a collection with processing error"""
        # Arrange
        collection_name = "users"
        errors = [{"error": "load_error", "error_id": "CFG-001", "message": "Failed to load configs"}]
        mock_collection_service.get_collection.side_effect = CollectionProcessingError(collection_name, errors)

        # Act
        response = self.client.get(f'/api/collections/{collection_name}')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json, errors)

    @patch('stage0_mongodb_api.routes.collection_routes.CollectionService')
    def test_process_specific_collection_success(self, mock_collection_service):
        """Test processing a specific collection successfully"""
        # Arrange
        collection_name = "users"
        mock_result = {
            "status": "success",
            "collection": collection_name,
            "operations": [{"operation": "apply_schema", "status": "success"}]
        }
        mock_collection_service.process_collection.return_value = mock_result

        # Act
        response = self.client.post(f'/api/collections/{collection_name}')

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, mock_result)
        mock_collection_service.process_collection.assert_called_once()

    @patch('stage0_mongodb_api.routes.collection_routes.CollectionService')
    def test_process_specific_collection_not_found(self, mock_collection_service):
        """Test processing a collection that doesn't exist"""
        # Arrange
        collection_name = "nonexistent"
        mock_collection_service.process_collection.side_effect = CollectionNotFoundError(collection_name)

        # Act
        response = self.client.post(f'/api/collections/{collection_name}')

        # Assert
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data.decode(), "Collection not found")

    @patch('stage0_mongodb_api.routes.collection_routes.CollectionService')
    def test_process_specific_collection_processing_error(self, mock_collection_service):
        """Test processing a specific collection with processing error"""
        # Arrange
        collection_name = "users"
        errors = [{"error": "processing_error", "error_id": "API-005", "message": "Failed to process collection"}]
        mock_collection_service.process_collection.side_effect = CollectionProcessingError(collection_name, errors)

        # Act
        response = self.client.post(f'/api/collections/{collection_name}')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json, errors)

    @patch('stage0_mongodb_api.routes.collection_routes.CollectionService')
    def test_process_specific_collection_unexpected_error(self, mock_collection_service):
        """Test processing a specific collection with unexpected error"""
        # Arrange
        collection_name = "users"
        mock_collection_service.process_collection.side_effect = Exception("Unexpected error")

        # Act
        response = self.client.post(f'/api/collections/{collection_name}')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json[0]["error"], "Failed to process collection")
        self.assertEqual(response.json[0]["error_id"], "API-004")

if __name__ == '__main__':
    unittest.main()