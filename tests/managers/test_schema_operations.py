import unittest
from unittest.mock import patch, MagicMock
import os
from stage0_py_utils import Config
from stage0_mongodb_api.managers.schema_manager import SchemaManager

class TestSchemaOperations(unittest.TestCase):
    """Test suite for schema operations (MongoDB operations)."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = Config.get_instance()
        self.test_cases_dir = os.path.join(os.path.dirname(__file__), "..", "test_cases")
        self.config.INPUT_FOLDER = os.path.join(self.test_cases_dir, "small_sample")

    @patch('stage0_py_utils.MongoIO.get_instance')
    def test_apply_schema_success(self, mock_get_instance):
        """Test successful schema application."""
        # Arrange
        mock_mongo = MagicMock()
        mock_get_instance.return_value = mock_mongo
        schema_manager = SchemaManager()
        self.assertEqual(schema_manager.load_errors, [])
        self.assertEqual(schema_manager.validate_schema(), [])

        # Act
        result = schema_manager.apply_schema("simple.1.0.0.1")
        
        # Assert
        self.assertEqual(result["status"], "success", f"Expected success, got {result}")
        self.assertEqual(result["operation"], "apply_schema", f"Expected apply_schema, got {result}")
        self.assertEqual(result["collection"], "simple", f"Expected simple, got {result}")
        mock_mongo.apply_schema.assert_called_once()

    @patch('stage0_py_utils.MongoIO.get_instance')
    def test_apply_schema_value_error(self, mock_get_instance):
        """Test applying schema with empty version name."""
        # Arrange
        mock_mongo = MagicMock()
        mock_get_instance.return_value = mock_mongo
        schema_manager = SchemaManager()
        
        # Act
        result = schema_manager.apply_schema("invalid_format")
        
        # Assert
        self.assertEqual(result["status"], "error") 
        self.assertEqual(result["operation"], "apply_schema")
        self.assertEqual(result["collection"], "invalid_format")
        self.assertIn("Invalid version format", result["message"])
        mock_mongo.apply_schema.assert_not_called()

    @patch('stage0_py_utils.MongoIO.get_instance')
    def test_apply_schema_exception(self, mock_get_instance):
        """Test applying schema exception handling."""
        # Arrange
        mock_mongo = MagicMock()
        mock_get_instance.return_value = mock_mongo
        mock_mongo.apply_schema.side_effect = Exception("mock exception")
        schema_manager = SchemaManager()

        # Act
        result = schema_manager.apply_schema("simple.1.0.0.1")
        
        # Assert
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["operation"], "apply_schema")
        self.assertEqual(result["collection"], "simple")
        self.assertIn("mock exception", result["message"])

    @patch('stage0_py_utils.MongoIO.get_instance')
    def test_remove_schema_success(self, mock_get_instance):
        """Test successful schema removal."""
        # Arrange
        mock_mongo = MagicMock()
        mock_get_instance.return_value = mock_mongo
        schema_manager = SchemaManager()
        
        # Act
        result = schema_manager.remove_schema("simple")
        
        # Assert
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["operation"], "remove_schema")
        self.assertEqual(result["collection"], "simple")
        mock_mongo.remove_schema.assert_called_once_with("simple")

    @patch('stage0_py_utils.MongoIO.get_instance')
    def test_remove_schema_exception(self, mock_get_instance):
        """Test exception handling."""
        # Arrange
        mock_mongo = MagicMock()
        mock_get_instance.return_value = mock_mongo
        mock_mongo.remove_schema.side_effect = Exception("mock exception")
        schema_manager = SchemaManager()

        # Act
        result = schema_manager.remove_schema("simple.1.0.0.1")
        
        # Assert
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["operation"], "remove_schema")
        self.assertEqual(result["collection"], "simple.1.0.0.1")
        self.assertIn("mock exception", result["message"])


if __name__ == '__main__':
    unittest.main() 