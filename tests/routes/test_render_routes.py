import unittest
from unittest.mock import patch, MagicMock
from flask import Flask
from stage0_mongodb_api.routes.render_routes import create_render_routes

class TestRenderRoutes(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Mock RenderService before creating the blueprint
        self.render_service_patcher = patch('stage0_mongodb_api.routes.render_routes.RenderService')
        self.mock_render_service = self.render_service_patcher.start()
        self.mock_render_service_instance = self.mock_render_service.return_value
        
        self.app = Flask(__name__)
        self.app.register_blueprint(create_render_routes(), url_prefix='/api/render')
        self.client = self.app.test_client()

    def tearDown(self):
        """Clean up test fixtures after each test method."""
        self.render_service_patcher.stop()

    def test_render_json_schema(self):
        """Test rendering JSON schema for a collection."""
        # Arrange
        collection_name = "test_collection"
        mock_schema = {"test": "schema"}
        self.mock_render_service_instance.render_json_schema.return_value = mock_schema

        # Act
        response = self.client.get(f'/api/render/json_schema/{collection_name}')

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, mock_schema)
        self.mock_render_service_instance.render_json_schema.assert_called_once_with(collection_name)

    def test_render_bson_schema(self):
        """Test rendering BSON schema for a collection."""
        # Arrange
        collection_name = "test_collection"
        mock_schema = {"test": "schema"}
        self.mock_render_service_instance.render_bson_schema.return_value = mock_schema

        # Act
        response = self.client.get(f'/api/render/bson_schema/{collection_name}')

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, mock_schema)
        self.mock_render_service_instance.render_bson_schema.assert_called_once_with(collection_name)

    def test_render_openapi(self):
        """Test rendering OpenAPI specification for a collection."""
        # Arrange
        collection_name = "test_collection"
        mock_openapi = {"test": "openapi"}
        self.mock_render_service_instance.render_openapi.return_value = mock_openapi

        # Act
        response = self.client.get(f'/api/render/openapi/{collection_name}')

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.decode('utf-8'), 'test: openapi\n')
        self.mock_render_service_instance.render_openapi.assert_called_once_with(collection_name)

    def test_render_json_schema_error(self):
        """Test error handling when rendering JSON schema fails."""
        # Arrange
        collection_name = "test_collection"
        self.mock_render_service_instance.render_json_schema.side_effect = Exception("Test error")

        # Act
        response = self.client.get(f'/api/render/json_schema/{collection_name}')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.mock_render_service_instance.render_json_schema.assert_called_once_with(collection_name)

    def test_render_bson_schema_error(self):
        """Test error handling when rendering BSON schema fails."""
        # Arrange
        collection_name = "test_collection"
        self.mock_render_service_instance.render_bson_schema.side_effect = Exception("Test error")

        # Act
        response = self.client.get(f'/api/render/bson_schema/{collection_name}')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.mock_render_service_instance.render_bson_schema.assert_called_once_with(collection_name)

    def test_render_openapi_error(self):
        """Test error handling when rendering OpenAPI specification fails."""
        # Arrange
        collection_name = "test_collection"
        self.mock_render_service_instance.render_openapi.side_effect = Exception("Test error")

        # Act
        response = self.client.get(f'/api/render/openapi/{collection_name}')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.mock_render_service_instance.render_openapi.assert_called_once_with(collection_name)

if __name__ == '__main__':
    unittest.main() 