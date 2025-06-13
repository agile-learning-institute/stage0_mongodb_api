import unittest
import os
from unittest.mock import MagicMock, patch
from stage0_mongodb_api.managers.schema_manager import SchemaManager
from stage0_py_utils import Config

class TestSchemaLoading(unittest.TestCase):
    """Test suite for schema loading functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = Config.get_instance()
        self.test_cases_dir = os.path.join(os.path.dirname(__file__), "..", "test_cases")
        
    @patch('stage0_py_utils.MongoIO.get_instance')
    def test_load_minimum_valid(self, mock_get_instance):
        """Test loading minimum valid schema structure."""
        # Arrange
        mock_get_instance.return_value = MagicMock()
        self.config.INPUT_FOLDER = os.path.join(self.test_cases_dir, "minimum_valid")
        
        # Act
        schema_manager = SchemaManager()
        
        # Assert
        self.assertEqual(schema_manager.load_errors, [])
        self.assertEqual(len(schema_manager.dictionaries), 0)
        self.assertEqual(len(schema_manager.types), 0)
        self.assertEqual(len(schema_manager.enumerators), 0)
        
    @patch('stage0_py_utils.MongoIO.get_instance')
    def test_load_small_sample(self, mock_get_instance):
        """Test loading small sample schema."""
        # Arrange
        mock_get_instance.return_value = MagicMock()
        self.config.INPUT_FOLDER = os.path.join(self.test_cases_dir, "small_sample")
        
        # Act
        schema_manager = SchemaManager()
        
        # Assert
        self.assertEqual(schema_manager.load_errors, [])
        self.assertEqual(len(schema_manager.dictionaries), 1)
        self.assertEqual(len(schema_manager.types), 2)
        self.assertEqual(len(schema_manager.enumerators), 2)
        
    @patch('stage0_py_utils.MongoIO.get_instance')
    def test_load_large_sample(self, mock_get_instance):
        """Test loading large sample schema."""
        # Arrange
        mock_get_instance.return_value = MagicMock()
        self.config.INPUT_FOLDER = os.path.join(self.test_cases_dir, "large_sample")
        
        # Act
        schema_manager = SchemaManager()
        
        # Assert
        self.assertEqual(schema_manager.load_errors, [])
        self.assertEqual(len(schema_manager.dictionaries), 6)
        self.assertEqual(len(schema_manager.types), 10)
        self.assertEqual(len(schema_manager.enumerators), 4)
        
    @patch('stage0_py_utils.MongoIO.get_instance')
    def test_empty_input(self, mock_get_instance):
        """Test loading with empty input."""
        # Arrange
        mock_get_instance.return_value = MagicMock()
        self.config.INPUT_FOLDER = os.path.join(self.test_cases_dir, "empty_input")
        
        # Act
        schema_manager = SchemaManager()
        
        # Assert
        expected_error_ids = {"CFG-001", "SCH-001", "SCH-004", "SCH-009"}
        actual_error_ids = {error.get('error_id') for error in schema_manager.load_errors if 'error_id' in error}
        missing_error_ids = expected_error_ids - actual_error_ids
        extra_error_ids = actual_error_ids - expected_error_ids
        self.assertEqual(missing_error_ids, set(), f"Missing error IDs: {missing_error_ids}")
        self.assertEqual(extra_error_ids, set(), f"Extra error IDs: {extra_error_ids}")

    @patch('stage0_py_utils.MongoIO.get_instance')
    def test_missing_sub_folders(self, mock_get_instance):
        """Test loading with empty sub-folders."""
        # Arrange
        mock_get_instance.return_value = MagicMock()
        self.config.INPUT_FOLDER = os.path.join(self.test_cases_dir, "missing_folders")
        
        # Act
        schema_manager = SchemaManager()
        
        # Assert
        expected_error_ids = {"SCH-001", "SCH-004"}
        actual_error_ids = {error.get('error_id') for error in schema_manager.load_errors if 'error_id' in error}
        missing_error_ids = expected_error_ids - actual_error_ids
        extra_error_ids = actual_error_ids - expected_error_ids
        self.assertEqual(missing_error_ids, set(), f"Missing error IDs: {missing_error_ids}")
        self.assertEqual(extra_error_ids, set(), f"Extra error IDs: {extra_error_ids}")

    @patch('stage0_py_utils.MongoIO.get_instance')
    def test_load_errors(self, mock_get_instance):
        """Test loading with unparsable input files."""
        # Arrange
        mock_get_instance.return_value = MagicMock()
        self.config.INPUT_FOLDER = os.path.join(self.test_cases_dir, "unparsable_files")
        
        # Act
        schema_manager = SchemaManager()
        
        # Assert
        expected_error_ids = {"CFG-002", "SCH-002", "SCH-007", "SCH-011"}
        actual_error_ids = {error.get('error_id') for error in schema_manager.load_errors if 'error_id' in error}
        missing_error_ids = expected_error_ids - actual_error_ids
        extra_error_ids = actual_error_ids - expected_error_ids
        self.assertEqual(missing_error_ids, set(), f"Missing error IDs: {missing_error_ids}")
        self.assertEqual(extra_error_ids, set(), f"Extra error IDs: {extra_error_ids}")
        
if __name__ == '__main__':
    unittest.main() 