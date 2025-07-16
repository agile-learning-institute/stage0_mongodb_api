from configurator.utils.config import Config
from configurator.services.type_services import Type
from configurator.utils.file_io import FileIO
import unittest
import os
import json
import tempfile
import shutil
import yaml
from bson import json_util

class TestTypeRender(unittest.TestCase):
    """Test Type rendering of input files"""

    def setUp(self):
        """Set up test environment."""
        self.test_case = getattr(self, 'test_case', 'passing_type_renders')
        os.environ['INPUT_FOLDER'] = f"./tests/test_cases/{self.test_case}"
        Config._instance = None
        self.config = Config.get_instance()
        
        # Clean up environment variable after Config.get_instance()
        if 'INPUT_FOLDER' in os.environ:
            del os.environ['INPUT_FOLDER']
        
        # Create temporary directory for test output
        self.temp_dir = tempfile.mkdtemp(prefix="test_type_render_")

    def tearDown(self):
        """Clean up after tests."""
        # Clean up temporary directory
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        
        Config._instance = None

    def test_type_rendering(self):
        """Test rendering of all type files to JSON and BSON schemas"""
        # Arrange
        type_files = FileIO.get_documents(self.config.TYPE_FOLDER)
        
        # Act & Assert
        for type_file in type_files:
            type_name = type_file.file_name.replace('.yaml', '')
            type_service = Type(type_file.file_name)
            
            # Render JSON schema
            json_schema = type_service.get_json_schema()
            self.assertIsNotNone(json_schema)
            
            # Render BSON schema
            bson_schema = type_service.get_bson_schema()
            self.assertIsNotNone(bson_schema)
            
            # Compare against verified output
            self._compare_json_schema(type_name, json_schema)
            self._compare_bson_schema(type_name, bson_schema)

    def _compare_json_schema(self, type_name: str, actual_schema: dict):
        """Compare actual JSON schema against verified output."""
        verified_path = f"{self.config.INPUT_FOLDER}/verified_output/json_schema/{type_name}.yaml"
        
        if not os.path.exists(verified_path):
            self.fail(f"Expected verified JSON schema file not found: {verified_path}")
        
        with open(verified_path, 'r') as f:
            expected_schema = yaml.safe_load(f)
        
        self.assertEqual(actual_schema, expected_schema, 
                        f"JSON schema for {type_name} does not match verified output")

    def _compare_bson_schema(self, type_name: str, actual_schema: dict):
        """Compare actual BSON schema against verified output."""
        verified_path = f"{self.config.INPUT_FOLDER}/verified_output/bson_schema/{type_name}.json"
        
        if not os.path.exists(verified_path):
            self.fail(f"Expected verified BSON schema file not found: {verified_path}")
        
        with open(verified_path, 'r') as f:
            expected_schema = json.load(f)
        
        self.assertEqual(actual_schema, expected_schema, 
                        f"BSON schema for {type_name} does not match verified output")

class TestTypeRenderTemplate(TestTypeRender):
    """Test Type Render of passing_type_renders"""

    def setUp(self):
        self.test_case = 'passing_type_renders'
        super().setUp()

    def tearDown(self):
        super().tearDown()

if __name__ == '__main__':
    unittest.main() 