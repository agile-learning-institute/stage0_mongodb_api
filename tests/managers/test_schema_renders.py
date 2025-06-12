import unittest
import os
import json
import yaml
from stage0_mongodb_api.managers.schema_manager import SchemaManager
from stage0_mongodb_api.managers.schema_types import SchemaFormat
from stage0_py_utils import Config

class TestSchemaRenders(unittest.TestCase):
    """Test suite for schema rendering functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = Config.get_instance()
        self.test_cases_dir = os.path.join(os.path.dirname(__file__), "..", "test_cases")
        
    def test_render_simple(self):
        """Test simple rendering."""
        # Arrange
        self.config.INPUT_FOLDER = os.path.join(self.test_cases_dir, "small_sample")
        schema_manager = SchemaManager()
        version_name = "simple.1.0.0.1"
        
        # Act
        rendered_bson = schema_manager.render_one(version_name, SchemaFormat.BSON)
        rendered_json = schema_manager.render_one(version_name, SchemaFormat.JSON)
        
        # Assert
        expected_bson = self._load_bson(version_name)
        expected_json = self._load_json(version_name)

        self.assertEqual(rendered_bson, expected_bson, f"BSON schema mismatch, rendered: {rendered_bson}")
        self.assertEqual(rendered_json, expected_json, f"JSON schema mismatch, rendered: {rendered_json}")
        
    def test_render_organization(self):
        """Test rendering with complex custom types."""
        # Arrange
        self.config.INPUT_FOLDER = os.path.join(self.test_cases_dir, "large_sample")
        schema_manager = SchemaManager()
        version_name = "organization.1.0.0.1"

        # Act
        rendered_bson = schema_manager.render_one(version_name, SchemaFormat.BSON)
        rendered_json = schema_manager.render_one(version_name, SchemaFormat.JSON)
        
        # Assert
        expected_bson = self._load_bson(version_name)
        expected_json = self._load_json(version_name)

        self.assertEqual(rendered_bson, expected_bson, f"BSON schema mismatch, rendered: {rendered_bson}")
        self.assertEqual(rendered_json, expected_json, f"JSON schema mismatch, rendered: {rendered_json}")
        
    def test_render_media(self):
        """Test rendering with complex defined types."""
        # Arrange
        self.config.INPUT_FOLDER = os.path.join(self.test_cases_dir, "large_sample")
        schema_manager = SchemaManager()
        version_name = "media.1.0.0.1"

        # Act
        rendered_bson = schema_manager.render_one(version_name, SchemaFormat.BSON)
        rendered_json = schema_manager.render_one(version_name, SchemaFormat.JSON)
        
        # Assert
        expected_bson = self._load_bson(version_name)
        expected_json = self._load_json(version_name)

        self.assertEqual(rendered_bson, expected_bson, f"BSON schema mismatch, rendered: {rendered_bson}")
        self.assertEqual(rendered_json, expected_json, f"JSON schema mismatch, rendered: {rendered_json}")
        
    def test_render_user_1001(self):
        """Test rendering a complex schema."""
        # Arrange
        self.config.INPUT_FOLDER = os.path.join(self.test_cases_dir, "large_sample")
        schema_manager = SchemaManager()
        version_name = "user.1.0.0.1"
        
        # Act
        rendered_bson = schema_manager.render_one(version_name, SchemaFormat.BSON)
        rendered_json = schema_manager.render_one(version_name, SchemaFormat.JSON)
        
        # Assert
        expected_bson = self._load_bson(version_name)
        expected_json = self._load_json(version_name)

        self.assertEqual(rendered_bson, expected_bson, f"BSON schema mismatch, rendered: {rendered_bson}")
        self.assertEqual(rendered_json, expected_json, f"JSON schema mismatch, rendered: {rendered_json}")

    def test_render_user_1002(self):
        """Test rendering a complex schema."""
        # Arrange
        self.config.INPUT_FOLDER = os.path.join(self.test_cases_dir, "large_sample")
        schema_manager = SchemaManager()
        version_name = "user.1.0.0.2"
        
        # Act
        rendered_bson = schema_manager.render_one(version_name, SchemaFormat.BSON)
        rendered_json = schema_manager.render_one(version_name, SchemaFormat.JSON)
        
        # Assert
        expected_bson = self._load_bson(version_name)
        expected_json = self._load_json(version_name)

        self.assertEqual(rendered_bson, expected_bson, f"BSON schema mismatch, rendered: {rendered_bson}")
        self.assertEqual(rendered_json, expected_json, f"JSON schema mismatch, rendered: {rendered_json}")

    def test_render_user_1013(self):
        """Test rendering a complex schema."""
        # Arrange
        self.config.INPUT_FOLDER = os.path.join(self.test_cases_dir, "large_sample")
        schema_manager = SchemaManager()
        version_name = "user.1.0.1.3"
        
        # Act
        rendered_bson = schema_manager.render_one(version_name, SchemaFormat.BSON)
        rendered_json = schema_manager.render_one(version_name, SchemaFormat.JSON)
        
        # Assert
        expected_bson = self._load_bson(version_name)
        expected_json = self._load_json(version_name)

        self.assertEqual(rendered_bson, expected_bson, f"BSON schema mismatch, rendered: {rendered_bson}")
        self.assertEqual(rendered_json, expected_json, f"JSON schema mismatch, rendered: {rendered_json}")

    def test_render_search_1001(self):
        """Test rendering a complex schema."""
        # Arrange
        self.config.INPUT_FOLDER = os.path.join(self.test_cases_dir, "large_sample")
        schema_manager = SchemaManager()
        version_name = "search.1.0.0.1"
        
        # Act
        rendered_bson = schema_manager.render_one(version_name, SchemaFormat.BSON)
        rendered_json = schema_manager.render_one(version_name, SchemaFormat.JSON)
        
        # Assert
        expected_bson = self._load_bson(version_name)
        expected_json = self._load_json(version_name)

        self.assertEqual(rendered_bson, expected_bson, f"BSON schema mismatch, rendered: {rendered_bson}")
        self.assertEqual(rendered_json, expected_json, f"JSON schema mismatch, rendered: {rendered_json}")

    def test_render_search_1002(self):
        """Test rendering a complex schema."""
        # Arrange
        self.config.INPUT_FOLDER = os.path.join(self.test_cases_dir, "large_sample")
        schema_manager = SchemaManager()
        version_name = "search.1.0.0.2"
        
        # Act
        rendered_bson = schema_manager.render_one(version_name, SchemaFormat.BSON)
        rendered_json = schema_manager.render_one(version_name, SchemaFormat.JSON)
        
        # Assert
        expected_bson = self._load_bson(version_name)
        expected_json = self._load_json(version_name)

        self.assertEqual(rendered_bson, expected_bson, f"BSON schema mismatch, rendered: {rendered_bson}")
        self.assertEqual(rendered_json, expected_json, f"JSON schema mismatch, rendered: {rendered_json}")

    def test_render_search_1013(self):
        """Test rendering a complex schema."""
        # Arrange
        self.config.INPUT_FOLDER = os.path.join(self.test_cases_dir, "large_sample")
        schema_manager = SchemaManager()
        version_name = "search.1.0.1.3"
        
        # Act
        rendered_bson = schema_manager.render_one(version_name, SchemaFormat.BSON)
        rendered_json = schema_manager.render_one(version_name, SchemaFormat.JSON)
        
        # Assert
        expected_bson = self._load_bson(version_name)
        expected_json = self._load_json(version_name)

        self.assertEqual(rendered_bson, expected_bson, f"BSON schema mismatch, rendered: {rendered_bson}")
        self.assertEqual(rendered_json, expected_json, f"JSON schema mismatch, rendered: {rendered_json}")

    def _load_bson(self, version_name: str) -> dict:
        """Helper method to load bson schema JSON files."""
        file_path = os.path.join(self.config.INPUT_FOLDER, "expected", "bson_schema", f"{version_name}.json")
        with open(file_path, 'r') as f:
            return json.load(f)

    def _load_json(self, version_name: str) -> dict:
        """Helper method to load JSON Schema yaml files."""
        file_path = os.path.join(self.config.INPUT_FOLDER, "expected", "json_schema", f"{version_name}.yaml")
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)
            
if __name__ == '__main__':
    unittest.main() 