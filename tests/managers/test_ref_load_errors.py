import unittest
import os
from unittest.mock import MagicMock, patch
from stage0_mongodb_api.managers.schema_manager import SchemaManager
from stage0_py_utils import Config


class TestRefLoadErrors(unittest.TestCase):
    """Test cases for $ref load errors during schema loading."""
    
    def setUp(self):
        """Set up test environment."""
        self.config = Config.get_instance()
        self.test_cases_dir = os.path.join(os.path.dirname(__file__), "..", "test_cases")
        
    @patch('stage0_py_utils.MongoIO.get_instance')
    def test_ref_load_errors(self, mock_get_instance):
        """Test that $ref load errors are properly caught and reported."""
        # Arrange
        mock_get_instance.return_value = MagicMock()
        self.config.INPUT_FOLDER = os.path.join(self.test_cases_dir, "ref_load_errors")
        
        # Act
        schema_manager = SchemaManager()
        
        # Assert
        # Check that we have load errors
        self.assertGreater(len(schema_manager.load_errors), 0, 
                          "Should have load errors for $ref issues")
        
        # Check for specific error types
        error_codes = [error.get('error_id') for error in schema_manager.load_errors]
        
        # Should have SCH-013 (circular reference) and SCH-014 (missing reference)
        self.assertIn('SCH-013', error_codes, 
                     "Should have circular reference error (SCH-013)")
        self.assertIn('SCH-014', error_codes, 
                     "Should have missing reference error (SCH-014)")
        
        # Verify error details
        circular_error = next((e for e in schema_manager.load_errors if e.get('error_id') == 'SCH-013'), None)
        missing_error = next((e for e in schema_manager.load_errors if e.get('error_id') == 'SCH-014'), None)
        
        self.assertIsNotNone(circular_error, "Should have circular reference error")
        self.assertEqual(circular_error['error'], 'circular_reference')
        self.assertEqual(circular_error['ref_name'], 'circular_ref.1.0.0')
        
        self.assertIsNotNone(missing_error, "Should have missing reference error")
        self.assertEqual(missing_error['error'], 'ref_not_found')
        self.assertEqual(missing_error['ref_name'], 'does_not_exist.1.0.0')


if __name__ == '__main__':
    unittest.main() 