import unittest
import os
from unittest.mock import MagicMock, patch
from stage0_mongodb_api.managers.schema_manager import SchemaManager
from stage0_mongodb_api.managers.config_manager import ConfigManager
from stage0_py_utils import Config
from stage0_mongodb_api.managers.schema_validator import SchemaValidator, SchemaValidationError
from stage0_mongodb_api.managers.schema_types import SchemaType, ValidationContext

class TestSchemaValidation(unittest.TestCase):
    """Test suite for schema validation functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = Config.get_instance()
        self.test_cases_dir = os.path.join(os.path.dirname(__file__), "..", "test_cases")
        
    @patch('stage0_py_utils.MongoIO.get_instance')
    def test_validate_minimum_valid(self, mock_get_instance):
        """Test validation of minimum valid schema."""
        # Arrange
        mock_get_instance.return_value = MagicMock()
        self.config.INPUT_FOLDER = os.path.join(self.test_cases_dir, "minimum_valid")
        schema_manager = SchemaManager()
        
        # Act
        errors = schema_manager.validate_schema()
        
        # Assert
        self.assertEqual(schema_manager.load_errors, [])
        self.assertEqual(errors, [])
        
    @patch('stage0_py_utils.MongoIO.get_instance')
    def test_validate_small_sample(self, mock_get_instance):
        """Test validation of small sample schema."""
        # Arrange
        self.config.INPUT_FOLDER = os.path.join(self.test_cases_dir, "small_sample")
        mock_get_instance.return_value = MagicMock()
        schema_manager = SchemaManager()
        
        # Act
        errors = schema_manager.validate_schema()
        
        # Assert
        self.assertEqual(schema_manager.load_errors, [])
        self.assertEqual(errors, [])
        
    @patch('stage0_py_utils.MongoIO.get_instance')
    def test_validate_large_sample(self, mock_get_instance):
        """Test validation of large sample schema."""
        # Arrange
        self.config.INPUT_FOLDER = os.path.join(self.test_cases_dir, "large_sample")
        mock_get_instance.return_value = MagicMock()
        schema_manager = SchemaManager()
        
        # Act
        errors = schema_manager.validate_schema()
        
        # Assert
        self.assertEqual(schema_manager.load_errors, [])
        self.assertEqual(errors, [])
        
    @patch('stage0_py_utils.MongoIO.get_instance')
    def test_validate_complex_refs(self, mock_get_instance):
        """Test validation of complex nested $refs."""
        # Arrange
        self.config.INPUT_FOLDER = os.path.join(self.test_cases_dir, "complex_refs")
        mock_get_instance.return_value = MagicMock()
        schema_manager = SchemaManager()
        
        # Act
        errors = schema_manager.validate_schema()
        
        # Assert
        self.assertEqual(schema_manager.load_errors, [])
        self.assertEqual(errors, [])
        
    @patch('stage0_py_utils.MongoIO.get_instance')
    def test_validation_errors(self, mock_get_instance):
        """Test validation with all validation errors."""
        # Arrange
        self.config.INPUT_FOLDER = os.path.join(self.test_cases_dir, "validation_errors")
        mock_get_instance.return_value = MagicMock()
        schema_manager = SchemaManager()
        config_manager = ConfigManager()
        
        # Act
        schema_errors = schema_manager.validate_schema()
        config_errors = config_manager.validate_configs()
        
        # Assert - Schema validation errors
        expected_schema_error_ids = {
            # Schema Validator validation errors
            "VLD-001", "VLD-002", "VLD-003", "VLD-004", "VLD-005",  # Schema validation errors
            "VLD-101", "VLD-102", "VLD-103", "VLD-104", "VLD-106",  # Enumerator validation errors
            "VLD-108",  # Enumerator description type error
            "VLD-201", "VLD-202", "VLD-203", "VLD-204",  # Primitive type validation errors
            "VLD-301",  # Complex type basic validation
            "VLD-401",  # Required fields validation
            "VLD-601",  # Custom type validation
            "VLD-701",  # Object type validation
            "VLD-801",  # Array type validation
            "VLD-901", "VLD-902",  # Enum type validation
            "VLD-1001", "VLD-1002", "VLD-1003",  # OneOf type validation
        }
        actual_schema_error_ids = {error.get('error_id') for error in schema_errors if 'error_id' in error}
        missing_schema_error_ids = expected_schema_error_ids - actual_schema_error_ids
        extra_schema_error_ids = actual_schema_error_ids - expected_schema_error_ids
        self.assertEqual(missing_schema_error_ids, set())
        self.assertEqual(extra_schema_error_ids, set())
        
        # Assert - Config validation errors
        expected_config_error_ids = {
            # Config Manager validation errors
            "CFG-101",  # Invalid config format
            "CFG-201", "CFG-202",  # Missing required fields
            "CFG-501",  # Invalid version format
            "CFG-601",  # Missing version number
            "CFG-701",  # Invalid version format
        }
        actual_config_error_ids = {error.get('error_id') for error in config_errors if 'error_id' in error}
        missing_config_error_ids = expected_config_error_ids - actual_config_error_ids
        extra_config_error_ids = actual_config_error_ids - expected_config_error_ids
        self.assertEqual(missing_config_error_ids, set())
        
        # Config validation now includes schema validation errors, so we expect both
        # Check that config errors are present
        self.assertTrue(expected_config_error_ids.issubset(actual_config_error_ids))
        
        # Check that schema validation errors are also included
        schema_error_ids_in_config = {error.get('error_id') for error in config_errors 
                                    if 'error_id' in error and error.get('error_id', '').startswith('VLD-')}
        self.assertTrue(len(schema_error_ids_in_config) > 0, "Schema validation errors should be included in config validation")

if __name__ == '__main__':
    unittest.main() 