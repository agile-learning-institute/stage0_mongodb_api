import unittest
import tempfile
import os
from pathlib import Path
from configurator.utils.config import Config

class TestApiBuiltAt(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures."""
        # Clear the singleton instance to ensure clean state
        Config._instance = None
        self.config = Config.get_instance()

    def tearDown(self):
        """Clean up after tests."""
        # Clear the singleton instance
        Config._instance = None

    def test_api_built_at_missing_file_exits(self):
        """Test that API_BUILT_AT missing file causes fatal exit."""
        configurator_dir = Path(__file__).parent.parent.parent / "configurator"
        api_built_at_path = configurator_dir / "API_BUILT_AT"
        
        if api_built_at_path.exists():
            # Rename the file temporarily
            temp_path = api_built_at_path.with_suffix('.tmp')
            api_built_at_path.rename(temp_path)
            try:
                Config._instance = None
                with self.assertRaises(SystemExit):
                    Config.get_instance()
            finally:
                temp_path.rename(api_built_at_path)
        else:
            # If the file is already missing, just check for SystemExit
            Config._instance = None
            with self.assertRaises(SystemExit):
                Config.get_instance()

    def test_api_built_at_reads_from_file(self):
        """Test that API_BUILT_AT reads from the file when it exists."""
        configurator_dir = Path(__file__).parent.parent.parent / "configurator"
        api_built_at_path = configurator_dir / "API_BUILT_AT"
        
        # Test that the file exists and contains expected value
        self.assertTrue(api_built_at_path.exists())
        
        # Re-initialize config
        Config._instance = None
        config = Config.get_instance()
        
        # Test that API_BUILT_AT reads from file
        self.assertEqual(config.API_BUILT_AT, "Local")
        
        # Test that it's recorded as coming from file
        api_built_at_item = next((item for item in config.config_items if item['name'] == 'API_BUILT_AT'), None)
        self.assertIsNotNone(api_built_at_item)
        self.assertEqual(api_built_at_item['from'], 'file')
        self.assertEqual(api_built_at_item['value'], 'Local')

    def test_api_built_at_is_included_in_config_items(self):
        """Test that API_BUILT_AT is included in the config_items list."""
        config = Config.get_instance()
        
        # Check that API_BUILT_AT is in the config_items
        api_built_at_item = next((item for item in config.config_items if item['name'] == 'API_BUILT_AT'), None)
        self.assertIsNotNone(api_built_at_item)
        self.assertEqual(api_built_at_item['name'], 'API_BUILT_AT')
        self.assertIn(api_built_at_item['from'], ['file', 'default'])

if __name__ == '__main__':
    unittest.main() 