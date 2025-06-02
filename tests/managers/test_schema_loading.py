import unittest
import os
from stage0_mongodb_api.managers.schema_manager import SchemaManager
from stage0_mongodb_api.managers.config_manager import ConfigManager
from stage0_py_utils import Config

class TestSchemaLoading(unittest.TestCase):
    """Test suite for schema loading functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = Config.get_instance()
        self.config_manager = ConfigManager()
        self.test_cases_dir = os.path.join(os.path.dirname(__file__), "..", "test_cases")
        
    def test_load_minimum_valid(self):
        """Test loading minimum valid schema structure."""
        # Arrange
        self.config.INPUT_FOLDER = os.path.join(self.test_cases_dir, "minimum_valid")
        schema_manager = SchemaManager(self.config_manager)
        
        # Act
        schema_manager.load_schemas()
        
        # Assert
        self.assertEqual(self.schema_manager.load_errors, [])
        self.assertEqual(len(self.schema_manager.dictionaries), 0)
        self.assertEqual(len(self.schema_manager.types), 0)
        self.assertEqual(len(self.schema_manager.enumerators), 0)
        
    def test_load_small_sample(self):
        """Test loading small sample schema."""
        # Arrange
        self.config.INPUT_FOLDER = os.path.join(self.test_cases_dir, "small_sample")
        schema_manager = SchemaManager(self.config_manager)
        
        # Act
        schema_manager.load_schemas()
        
        # Assert
        self.assertEqual(schema_manager.load_errors, [])
        self.assertEqual(len(schema_manager.dictionaries), 1)
        self.assertEqual(len(schema_manager.types), 2)
        self.assertEqual(len(schema_manager.enumerators), 2)
        
    def test_load_large_sample(self):
        """Test loading large sample schema."""
        # Arrange
        self.schema_manager.config_manager.schema_dir = os.path.join(self.test_cases_dir, "large_sample")
        
        # Act
        self.schema_manager.load_schemas()
        
        # Assert
        self.assertEqual(self.schema_manager.load_errors, [])
        self.assertEqual(len(self.schema_manager.dictionaries), 6)
        self.assertEqual(len(self.schema_manager.types), 10)
        self.assertEqual(len(self.schema_manager.enumerators), 4)
        
    def test_load_errors(self):
        """Test loading with all load errors."""
        # Arrange
        self.schema_manager.config_manager.schema_dir = os.path.join(self.test_cases_dir, "load_errors")
        
        # Act
        self.schema_manager.load_schemas()
        
        # Assert
        expected_error_ids = {
            "CFG-001", "CFG-002", "CFG-003", "CFG-004", "CFG-005", "CFG-006",
            "SCH-001", "SCH-002", "SCH-003", "SCH-004", "SCH-005", "SCH-006",
            "SCH-007", "SCH-008", "SCH-009", "SCH-010", "SCH-011", "SCH-012"
        }
        actual_error_ids = {error.get('error_id') for error in self.schema_manager.load_errors if 'error_id' in error}
        self.assertEqual(expected_error_ids, actual_error_ids)
        
    def test_empty_input(self):
        """Test loading with empty input."""
        # Arrange
        self.schema_manager.config_manager.schema_dir = os.path.join(self.test_cases_dir, "empty_input")
        
        # Act
        self.schema_manager.load_schemas()
        
        # Assert
        expected_error_ids = {
            "CFG-001", 
            "SCH-001", "SCH-002", "SCH-003", "SCH-004", "SCH-005", "SCH-006",
            "SCH-007", "SCH-008", "SCH-009", "SCH-010", "SCH-011", "SCH-012"
        }
        actual_error_ids = {error.get('error_id') for error in self.schema_manager.load_errors if 'error_id' in error}
        self.assertEqual(expected_error_ids, actual_error_ids)

if __name__ == '__main__':
    unittest.main() 