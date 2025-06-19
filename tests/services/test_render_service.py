import unittest
from unittest.mock import patch, MagicMock
from stage0_mongodb_api.services.render_service import RenderService, RenderNotFoundError, RenderProcessingError

class TestRenderService(unittest.TestCase):
    """Test cases for RenderService static methods."""

    @patch('stage0_mongodb_api.services.render_service.ConfigManager')
    @patch('stage0_mongodb_api.services.render_service.SchemaManager')
    def test_render_json_schema_success(self, mock_schema_manager_class, mock_config_manager_class):
        """Test successful JSON schema rendering."""
        # Arrange
        schema_name = "test_collection.1.0.0.1"
        mock_schema = {"type": "object", "properties": {"test": {"type": "string"}}}
        
        mock_config_manager = MagicMock()
        mock_config_manager.load_errors = []
        mock_config_manager.validate_configs.return_value = []
        mock_config_manager_class.return_value = mock_config_manager
        
        mock_schema_manager = MagicMock()
        mock_schema_manager.render_one.return_value = mock_schema
        mock_schema_manager_class.return_value = mock_schema_manager

        # Act
        result = RenderService.render_json_schema(schema_name)

        # Assert
        self.assertEqual(result, mock_schema)
        # Check that render_one was called with the correct arguments
        mock_schema_manager.render_one.assert_called_once()
        call_args = mock_schema_manager.render_one.call_args
        self.assertEqual(call_args[0][0], schema_name)
        self.assertEqual(call_args[0][1].value, "json")

    @patch('stage0_mongodb_api.services.render_service.ConfigManager')
    @patch('stage0_mongodb_api.services.render_service.SchemaManager')
    def test_render_bson_schema_success(self, mock_schema_manager_class, mock_config_manager_class):
        """Test successful BSON schema rendering."""
        # Arrange
        schema_name = "test_collection.1.0.0.1"
        mock_schema = {"bsonType": "object", "properties": {"test": {"bsonType": "string"}}}
        
        mock_config_manager = MagicMock()
        mock_config_manager.load_errors = []
        mock_config_manager.validate_configs.return_value = []
        mock_config_manager_class.return_value = mock_config_manager
        
        mock_schema_manager = MagicMock()
        mock_schema_manager.render_one.return_value = mock_schema
        mock_schema_manager_class.return_value = mock_schema_manager

        # Act
        result = RenderService.render_bson_schema(schema_name)

        # Assert
        self.assertEqual(result, mock_schema)
        # Check that render_one was called with the correct arguments
        mock_schema_manager.render_one.assert_called_once()
        call_args = mock_schema_manager.render_one.call_args
        self.assertEqual(call_args[0][0], schema_name)
        self.assertEqual(call_args[0][1].value, "bson")

    @patch('stage0_mongodb_api.services.render_service.ConfigManager')
    def test_render_openapi_not_implemented(self, mock_config_manager_class):
        """Test that OpenAPI rendering returns a not implemented message."""
        # Arrange
        schema_name = "test_collection.1.0.0.1"
        expected_message = {"message": "OpenAPI rendering not yet implemented"}

        # Act
        result = RenderService.render_openapi(schema_name)

        # Assert
        self.assertEqual(result, expected_message)

    @patch('stage0_mongodb_api.services.render_service.ConfigManager')
    def test_render_json_schema_load_errors(self, mock_config_manager_class):
        """Test JSON schema rendering with load errors."""
        # Arrange
        schema_name = "test_collection.1.0.0.1"
        load_errors = [{"error": "load_error", "message": "Failed to load config"}]
        
        mock_config_manager = MagicMock()
        mock_config_manager.load_errors = load_errors
        mock_config_manager_class.return_value = mock_config_manager

        # Act & Assert
        with self.assertRaises(RenderProcessingError) as context:
            RenderService.render_json_schema(schema_name)
        
        self.assertEqual(context.exception.schema_name, schema_name)
        self.assertEqual(context.exception.errors, load_errors)

    @patch('stage0_mongodb_api.services.render_service.ConfigManager')
    def test_render_bson_schema_validation_errors(self, mock_config_manager_class):
        """Test BSON schema rendering with validation errors."""
        # Arrange
        schema_name = "test_collection.1.0.0.1"
        validation_errors = [{"error": "validation_error", "message": "Invalid schema"}]
        
        mock_config_manager = MagicMock()
        mock_config_manager.load_errors = []
        mock_config_manager.validate_configs.return_value = validation_errors
        mock_config_manager_class.return_value = mock_config_manager

        # Act & Assert
        with self.assertRaises(RenderProcessingError) as context:
            RenderService.render_bson_schema(schema_name)
        
        self.assertEqual(context.exception.schema_name, schema_name)
        self.assertEqual(context.exception.errors, validation_errors)

    @patch('stage0_mongodb_api.services.render_service.ConfigManager')
    @patch('stage0_mongodb_api.services.render_service.SchemaManager')
    def test_render_json_schema_rendering_error(self, mock_schema_manager_class, mock_config_manager_class):
        """Test JSON schema rendering when schema manager raises an exception."""
        # Arrange
        schema_name = "test_collection.1.0.0.1"
        
        mock_config_manager = MagicMock()
        mock_config_manager.load_errors = []
        mock_config_manager.validate_configs.return_value = []
        mock_config_manager_class.return_value = mock_config_manager
        
        mock_schema_manager = MagicMock()
        mock_schema_manager.render_one.side_effect = Exception("Schema rendering failed")
        mock_schema_manager_class.return_value = mock_schema_manager

        # Act & Assert
        with self.assertRaises(RenderProcessingError) as context:
            RenderService.render_json_schema(schema_name)
        
        self.assertEqual(context.exception.schema_name, schema_name)
        self.assertEqual(len(context.exception.errors), 1)
        self.assertEqual(context.exception.errors[0]["error"], "rendering_error")
        self.assertEqual(context.exception.errors[0]["error_id"], "RND-002")
        self.assertEqual(context.exception.errors[0]["message"], "Schema rendering failed")

    @patch('stage0_mongodb_api.services.render_service.ConfigManager')
    @patch('stage0_mongodb_api.services.render_service.SchemaManager')
    def test_render_bson_schema_rendering_error(self, mock_schema_manager_class, mock_config_manager_class):
        """Test BSON schema rendering when schema manager raises an exception."""
        # Arrange
        schema_name = "test_collection.1.0.0.1"
        
        mock_config_manager = MagicMock()
        mock_config_manager.load_errors = []
        mock_config_manager.validate_configs.return_value = []
        mock_config_manager_class.return_value = mock_config_manager
        
        mock_schema_manager = MagicMock()
        mock_schema_manager.render_one.side_effect = Exception("Schema rendering failed")
        mock_schema_manager_class.return_value = mock_schema_manager

        # Act & Assert
        with self.assertRaises(RenderProcessingError) as context:
            RenderService.render_bson_schema(schema_name)
        
        self.assertEqual(context.exception.schema_name, schema_name)
        self.assertEqual(len(context.exception.errors), 1)
        self.assertEqual(context.exception.errors[0]["error"], "rendering_error")
        self.assertEqual(context.exception.errors[0]["error_id"], "RND-003")
        self.assertEqual(context.exception.errors[0]["message"], "Schema rendering failed")

if __name__ == '__main__':
    unittest.main() 