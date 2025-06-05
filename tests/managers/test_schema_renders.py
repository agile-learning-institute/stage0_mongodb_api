import unittest
import os
import json
import yaml
from stage0_mongodb_api.managers.schema_manager import SchemaManager
from stage0_py_utils import Config

class TestSchemaRenders(unittest.TestCase):
    """Test suite for schema rendering functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = Config.get_instance()
        self.test_cases_dir = os.path.join(os.path.dirname(__file__), "..", "test_cases")
            
    def test_render_small_sample(self):
        """Test rendering small sample schema."""
        self._assert_rendered_schemas("small_sample")
                    
    def test_render_large_sample(self):
        """Test rendering large sample schema."""
        self._assert_rendered_schemas("large_sample")
        
    def _assert_rendered_schemas(self, test_case: str):
        """Helper method to assert rendered schemas match expected output.
        
        Args:
            test_case: Name of the test case directory (e.g. "minimum_valid")
        """
        # Arrange
        self.config.INPUT_FOLDER = os.path.join(self.test_cases_dir, test_case)
        schema_manager = SchemaManager()
        
        # Act
        rendered = schema_manager.render_all()
        
        # Assert BSON schemas
        for version_name, schema in rendered["bson"].items():
            expected_bson = self._load_json(
                os.path.join(self.config.INPUT_FOLDER, "expected", "bson_schema", f"{version_name}.json")
            )
            self.assertEqual(schema, expected_bson, f"BSON schema mismatch for {version_name}")
            
        # Assert JSON schemas
        for version_name, schema in rendered["json"].items():
            expected_json = self._load_yaml(
                os.path.join(self.config.INPUT_FOLDER, "expected", "json_schema", f"{version_name}.yaml")
            )
            self.assertEqual(schema, expected_json, f"JSON schema mismatch for {version_name}")

    def _load_json(self, file_path: str) -> dict:
        """Helper method to load JSON files."""
        with open(file_path, 'r') as f:
            return json.load(f)
            
    def _load_yaml(self, file_path: str) -> dict:
        """Helper method to load YAML files."""
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)
            
if __name__ == '__main__':
    unittest.main() 