import unittest
from unittest.mock import patch, MagicMock
from flask import Flask
from stage0_mongodb_api.routes.render_routes import create_render_routes
from stage0_mongodb_api.services.render_service import RenderNotFoundError, RenderProcessingError

class TestRenderRoutes(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.app = Flask(__name__)
        self.app.register_blueprint(create_render_routes(), url_prefix='/api/render')
        self.client = self.app.test_client()

    @patch('stage0_mongodb_api.routes.render_routes.RenderService')
    def test_render_json_schema(self, mock_render_service):
        """Test rendering JSON schema for a schema."""
        # Arrange
        schema_name = "test_collection.1.0.0.1"
        mock_schema = {"test": "schema"}
        mock_render_service.render_json_schema.return_value = mock_schema

        # Act
        response = self.client.get(f'/api/render/json_schema/{schema_name}/')

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, mock_schema)
        mock_render_service.render_json_schema.assert_called_once()

    @patch('stage0_mongodb_api.routes.render_routes.RenderService')
    def test_render_bson_schema(self, mock_render_service):
        """Test rendering BSON schema for a schema."""
        # Arrange
        schema_name = "test_collection.1.0.0.1"
        mock_schema = {"test": "schema"}
        mock_render_service.render_bson_schema.return_value = mock_schema

        # Act
        response = self.client.get(f'/api/render/bson_schema/{schema_name}/')

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, mock_schema)
        mock_render_service.render_bson_schema.assert_called_once()

    @patch('stage0_mongodb_api.routes.render_routes.RenderService')
    def test_render_openapi(self, mock_render_service):
        """Test rendering OpenAPI specification for a schema."""
        # Arrange
        schema_name = "test_collection.1.0.0.1"
        expected_message = {"message": "OpenAPI rendering not yet implemented"}
        mock_render_service.render_openapi.return_value = expected_message

        # Act
        response = self.client.get(f'/api/render/openapi/{schema_name}/')

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.decode('utf-8'), 'message: OpenAPI rendering not yet implemented\n')
        mock_render_service.render_openapi.assert_called_once()

    @patch('stage0_mongodb_api.routes.render_routes.RenderService')
    def test_render_json_schema_not_found(self, mock_render_service):
        """Test error handling when schema is not found for JSON schema."""
        # Arrange
        schema_name = "nonexistent_collection.1.0.0.1"
        mock_render_service.render_json_schema.side_effect = RenderNotFoundError(schema_name)

        # Act
        response = self.client.get(f'/api/render/json_schema/{schema_name}/')

        # Assert
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data.decode('utf-8'), 'Schema not found')
        mock_render_service.render_json_schema.assert_called_once()

    @patch('stage0_mongodb_api.routes.render_routes.RenderService')
    def test_render_bson_schema_not_found(self, mock_render_service):
        """Test error handling when schema is not found for BSON schema."""
        # Arrange
        schema_name = "nonexistent_collection.1.0.0.1"
        mock_render_service.render_bson_schema.side_effect = RenderNotFoundError(schema_name)

        # Act
        response = self.client.get(f'/api/render/bson_schema/{schema_name}/')

        # Assert
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data.decode('utf-8'), 'Schema not found')
        mock_render_service.render_bson_schema.assert_called_once()

    @patch('stage0_mongodb_api.routes.render_routes.RenderService')
    def test_render_json_schema_processing_error(self, mock_render_service):
        """Test error handling when JSON schema processing fails."""
        # Arrange
        schema_name = "test_collection.1.0.0.1"
        errors = [{"error": "processing_error", "message": "Test error"}]
        mock_render_service.render_json_schema.side_effect = RenderProcessingError(schema_name, errors)

        # Act
        response = self.client.get(f'/api/render/json_schema/{schema_name}/')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json, errors)
        mock_render_service.render_json_schema.assert_called_once()

    @patch('stage0_mongodb_api.routes.render_routes.RenderService')
    def test_render_bson_schema_processing_error(self, mock_render_service):
        """Test error handling when BSON schema processing fails."""
        # Arrange
        schema_name = "test_collection.1.0.0.1"
        errors = [{"error": "processing_error", "message": "Test error"}]
        mock_render_service.render_bson_schema.side_effect = RenderProcessingError(schema_name, errors)

        # Act
        response = self.client.get(f'/api/render/bson_schema/{schema_name}/')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json, errors)
        mock_render_service.render_bson_schema.assert_called_once()

    @patch('stage0_mongodb_api.routes.render_routes.RenderService')
    def test_render_openapi_not_found(self, mock_render_service):
        """Test error handling when schema is not found for OpenAPI."""
        # Arrange
        schema_name = "nonexistent_collection.1.0.0.1"
        mock_render_service.render_openapi.side_effect = RenderNotFoundError(schema_name)

        # Act
        response = self.client.get(f'/api/render/openapi/{schema_name}/')

        # Assert
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data.decode('utf-8'), 'Schema not found')
        mock_render_service.render_openapi.assert_called_once()

    @patch('stage0_mongodb_api.routes.render_routes.RenderService')
    def test_render_openapi_processing_error(self, mock_render_service):
        """Test error handling when OpenAPI processing fails."""
        # Arrange
        schema_name = "test_collection.1.0.0.1"
        errors = [{"error": "processing_error", "message": "Test error"}]
        mock_render_service.render_openapi.side_effect = RenderProcessingError(schema_name, errors)

        # Act
        response = self.client.get(f'/api/render/openapi/{schema_name}/')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json, errors)
        mock_render_service.render_openapi.assert_called_once()

    @patch('stage0_mongodb_api.routes.render_routes.RenderService')
    def test_render_json_schema_unexpected_error(self, mock_render_service):
        """Test error handling when unexpected error occurs during JSON schema rendering."""
        # Arrange
        schema_name = "test_collection.1.0.0.1"
        mock_render_service.render_json_schema.side_effect = Exception("Unexpected error")

        # Act
        response = self.client.get(f'/api/render/json_schema/{schema_name}/')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json[0]["error"], "Failed to render JSON schema")
        self.assertEqual(response.json[0]["error_id"], "API-005")
        mock_render_service.render_json_schema.assert_called_once()

    @patch('stage0_mongodb_api.routes.render_routes.RenderService')
    def test_render_bson_schema_unexpected_error(self, mock_render_service):
        """Test error handling when unexpected error occurs during BSON schema rendering."""
        # Arrange
        schema_name = "test_collection.1.0.0.1"
        mock_render_service.render_bson_schema.side_effect = Exception("Unexpected error")

        # Act
        response = self.client.get(f'/api/render/bson_schema/{schema_name}/')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json[0]["error"], "Failed to render BSON schema")
        self.assertEqual(response.json[0]["error_id"], "API-006")
        mock_render_service.render_bson_schema.assert_called_once()

    @patch('stage0_mongodb_api.routes.render_routes.RenderService')
    def test_render_openapi_unexpected_error(self, mock_render_service):
        """Test error handling when unexpected error occurs during OpenAPI rendering."""
        # Arrange
        schema_name = "test_collection.1.0.0.1"
        mock_render_service.render_openapi.side_effect = Exception("Unexpected error")

        # Act
        response = self.client.get(f'/api/render/openapi/{schema_name}/')

        # Assert
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json[0]["error"], "Failed to render OpenAPI")
        self.assertEqual(response.json[0]["error_id"], "API-007")
        mock_render_service.render_openapi.assert_called_once()

if __name__ == '__main__':
    unittest.main() 