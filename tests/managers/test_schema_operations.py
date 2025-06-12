import unittest
from unittest.mock import patch, MagicMock
import os
import json
from stage0_mongodb_api.managers.schema_manager import SchemaManager
from stage0_mongodb_api.managers.config_manager import ConfigManager

class TestSchemaOperations(unittest.TestCase):
    """Test suite for schema operations (MongoDB operations)."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_cases_dir = os.path.join(os.path.dirname(__file__), "..", "test_cases")
        
    def _load_json(self, file_path: str) -> dict:
        """Helper method to load JSON files."""
        with open(file_path, 'r') as f:
            return json.load(f)

    @patch('stage0_py_utils.MongoIO')
    def test_apply_schema_success(self, mock_mongo):
        """Test successful schema application."""
        # Arrange
        self.config.INPUT_FOLDER = os.path.join(self.test_cases_dir, "small_sample")
        schema_manager = SchemaManager()
        mock_mongo.get_instance.return_value = MagicMock()
        
        # Act
        result = schema_manager.apply_schema("simple.1.0.0.1")
        
        # Assert
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["operation"], "apply_schema")
        self.assertEqual(result["collection"], "simple")
        self.assertIn("schema", result)
        mock_mongo.get_instance.return_value.apply_schema.assert_called_once()

    @patch('stage0_py_utils.MongoIO')
    def test_apply_schema_empty_version(self, mock_mongo):
        """Test applying schema with empty version name."""
        # Arrange
        schema_manager = SchemaManager(self.config)
        
        # Act
        result = schema_manager.apply_schema("")
        
        # Assert
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["operation"], "apply_schema")
        self.assertEqual(result["collection"], "")
        self.assertIn("cannot be empty", result["message"])
        mock_mongo.get_instance.return_value.apply_schema.assert_not_called()

    @patch('stage0_py_utils.MongoIO')
    def test_apply_schema_invalid_format(self, mock_mongo):
        """Test applying schema with invalid version format."""
        # Arrange
        schema_manager = SchemaManager(self.config)
        
        # Act
        result = schema_manager.apply_schema("invalid_format")
        
        # Assert
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["operation"], "apply_schema")
        self.assertEqual(result["collection"], "invalid_format")
        self.assertIn("Invalid version name format", result["message"])
        mock_mongo.get_instance.return_value.apply_schema.assert_not_called()

    @patch('stage0_py_utils.MongoIO')
    def test_apply_schema_not_found(self, mock_mongo):
        """Test applying non-existent schema."""
        # Arrange
        schema_manager = SchemaManager(self.config)
        
        # Act
        result = schema_manager.apply_schema("nonexistent.1.0.0")
        
        # Assert
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["operation"], "apply_schema")
        self.assertEqual(result["collection"], "nonexistent")
        self.assertIn("No schema found", result["message"])
        mock_mongo.get_instance.return_value.apply_schema.assert_not_called()

    @patch('stage0_py_utils.MongoIO')
    def test_apply_schema_mongo_error(self, mock_mongo):
        """Test schema application with MongoDB error."""
        # Arrange
        schema_manager = SchemaManager(self.config)
        schema_manager.load_schemas()
        mock_mongo.get_instance.return_value = MagicMock()
        mock_mongo.get_instance.return_value.apply_schema.side_effect = Exception("MongoDB error")
        
        # Act
        result = schema_manager.apply_schema("simple.1.0.0.1")
        
        # Assert
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["operation"], "apply_schema")
        self.assertEqual(result["collection"], "simple")
        self.assertIn("MongoDB error", result["message"])

    @patch('stage0_py_utils.MongoIO')
    def test_remove_schema_success(self, mock_mongo):
        """Test successful schema removal."""
        # Arrange
        schema_manager = SchemaManager(self.config)
        mock_mongo.get_instance.return_value = MagicMock()
        
        # Act
        result = schema_manager.remove_schema("simple")
        
        # Assert
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["operation"], "remove_schema")
        self.assertEqual(result["collection"], "simple")
        mock_mongo.get_instance.return_value.remove_schema.assert_called_once_with("simple")

    @patch('stage0_py_utils.MongoIO')
    def test_remove_schema_empty_name(self, mock_mongo):
        """Test schema removal with empty collection name."""
        # Arrange
        schema_manager = SchemaManager(self.config)
        
        # Act
        result = schema_manager.remove_schema("")
        
        # Assert
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["operation"], "remove_schema")
        self.assertEqual(result["collection"], "")
        self.assertIn("cannot be empty", result["message"])
        mock_mongo.get_instance.return_value.remove_schema.assert_not_called()

    @patch('stage0_py_utils.MongoIO')
    def test_remove_schema_mongo_error(self, mock_mongo):
        """Test schema removal with MongoDB error."""
        # Arrange
        schema_manager = SchemaManager(self.config)
        mock_mongo.get_instance.return_value = MagicMock()
        mock_mongo.get_instance.return_value.remove_schema.side_effect = Exception("MongoDB error")
        
        # Act
        result = schema_manager.remove_schema("simple")
        
        # Assert
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["operation"], "remove_schema")
        self.assertEqual(result["collection"], "simple")
        self.assertIn("MongoDB error", result["message"])

if __name__ == '__main__':
    unittest.main() 