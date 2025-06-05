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
        self.config_manager = ConfigManager()
        self.schema_manager = SchemaManager(self.config_manager)
        self.test_cases_dir = os.path.join(os.path.dirname(__file__), "..", "test_cases")
        
        # Mock MongoIO for apply/remove schema tests
        self.mongo_patcher = patch('stage0_py_utils.MongoIO')
        self.mock_mongo = self.mongo_patcher.start()
        self.mock_mongo.get_instance.return_value = MagicMock()
        
    def tearDown(self):
        """Clean up test fixtures."""
        self.mongo_patcher.stop()
        
    def _load_json(self, file_path: str) -> dict:
        """Helper method to load JSON files."""
        with open(file_path, 'r') as f:
            return json.load(f)
            
    def test_apply_schema_minimum_valid(self):
        """Test applying minimum valid schema."""
        # Arrange
        self.schema_manager.config_manager.schema_dir = os.path.join(self.test_cases_dir, "minimum_valid")
        self.schema_manager.load_schemas()
        
        # Load expected BSON schema
        bson_schema = self._load_json(os.path.join(self.test_cases_dir, "minimum_valid", "expected", "dictionary", "user.1.0.0.bson.json"))
        
        # Act
        result = self.schema_manager.apply_schema("test_collection", bson_schema)
        
        # Assert
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["operation"], "apply_schema")
        self.assertEqual(result["collection"], "test_collection")
        self.assertEqual(result["schema"], bson_schema)
        self.mock_mongo.get_instance.return_value.update_document.assert_called_once_with(
            "test_collection",
            set_data={"validator": {"$jsonSchema": bson_schema}}
        )
        
    def test_apply_schema_error(self):
        """Test schema application error handling."""
        # Arrange
        self.mock_mongo.get_instance.return_value.update_document.side_effect = Exception("MongoDB error")
        
        # Act
        result = self.schema_manager.apply_schema("test_collection", {})
        
        # Assert
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["operation"], "apply_schema")
        self.assertEqual(result["collection"], "test_collection")
        self.assertIn("MongoDB error", result["message"])
        
    def test_remove_schema_success(self):
        """Test successful schema removal."""
        # Arrange
        self.mock_mongo.get_instance.return_value.remove_schema.return_value = None
        
        # Act
        result = self.schema_manager.remove_schema("test_collection")
        
        # Assert
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["operation"], "remove_schema")
        self.assertEqual(result["collection"], "test_collection")
        self.mock_mongo.get_instance.return_value.remove_schema.assert_called_once_with("test_collection")
        
    def test_remove_schema_error(self):
        """Test schema removal error handling."""
        # Arrange
        self.mock_mongo.get_instance.return_value.remove_schema.side_effect = Exception("MongoDB error")
        
        # Act
        result = self.schema_manager.remove_schema("test_collection")
        
        # Assert
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["operation"], "remove_schema")
        self.assertEqual(result["collection"], "test_collection")
        self.assertIn("MongoDB error", result["message"])

if __name__ == '__main__':
    unittest.main() 