import unittest
import os
from stage0_mongodb_api.managers.schema_manager import SchemaManager
from stage0_mongodb_api.managers.config_manager import ConfigManager

class TestSchemaValidation(unittest.TestCase):
    """Test suite for schema validation functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config_manager = ConfigManager()
        self.schema_manager = SchemaManager(self.config_manager)
        self.test_cases_dir = os.path.join(os.path.dirname(__file__), "..", "test_cases")
        
    def test_validate_minimum_valid(self):
        """Test validation of minimum valid schema."""
        # Arrange
        self.schema_manager.config_manager.schema_dir = os.path.join(self.test_cases_dir, "minimum_valid")
        self.schema_manager.load_schemas()
        
        # Act
        errors = self.schema_manager.validate_schema()
        
        # Assert
        self.assertEqual(self.schema_manager.load_errors, [])
        self.assertEqual(errors, [])
        
    def test_validate_small_sample(self):
        """Test validation of small sample schema."""
        # Arrange
        self.schema_manager.config_manager.schema_dir = os.path.join(self.test_cases_dir, "small_sample")
        self.schema_manager.load_schemas()
        
        # Act
        errors = self.schema_manager.validate_schema()
        
        # Assert
        self.assertEqual(self.schema_manager.load_errors, [])
        self.assertEqual(errors, [])
        
    def test_validate_large_sample(self):
        """Test validation of large sample schema."""
        # Arrange
        self.schema_manager.config_manager.schema_dir = os.path.join(self.test_cases_dir, "large_sample")
        self.schema_manager.load_schemas()
        
        # Act
        errors = self.schema_manager.validate_schema()
        
        # Assert
        self.assertEqual(self.schema_manager.load_errors, [])
        self.assertEqual(errors, [])
        
    def test_validation_errors(self):
        """Test validation with all validation errors."""
        # Arrange
        self.schema_manager.config_manager.schema_dir = os.path.join(self.test_cases_dir, "validation_errors")
        self.schema_manager.load_schemas()
        
        # Act
        errors = self.schema_manager.validate_schema()
        
        # Assert
        expected_error_ids = {
            # Schema Manager validation errors
            "SCH-013", "SCH-014", "SCH-015", "SCH-016", "SCH-017", "SCH-023",
            "SCH-026", "SCH-033", "SCH-034", "SCH-035", "SCH-036", "SCH-038",
            "SCH-039", "SCH-040", "SCH-024", "SCH-025", "SCH-027", "SCH-028",
            "SCH-029",
            
            # Config Manager validation errors
            "CFG-004", "CFG-005", "CFG-006", "CFG-007", "CFG-008", "CFG-009",
            "CFG-010", "CFG-011", "CFG-012", "CFG-013"
        }
        actual_error_ids = {error.get('error_id') for error in errors if 'error_id' in error}
        self.assertEqual(expected_error_ids, actual_error_ids)

if __name__ == '__main__':
    unittest.main() 