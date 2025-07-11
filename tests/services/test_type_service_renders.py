import unittest
from configurator.services.type_services import Type
from configurator.utils.version_number import VersionNumber
import os
import yaml
import json


def load_yaml(path):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)

def set_config_input_folder(folder):
    os.environ['INPUT_FOLDER'] = folder
    from configurator.utils.config import Config
    Config._instance = None
    return Config.get_instance()

def clear_config():
    if 'INPUT_FOLDER' in os.environ:
        del os.environ['INPUT_FOLDER']
    from configurator.utils.config import Config
    Config._instance = None


class TestTypeRendering(unittest.TestCase):
    """Test type rendering against verified output files"""

    def setUp(self):
        self.config = set_config_input_folder("./tests/test_cases/type_unit_test")

    def tearDown(self):
        clear_config()

    def test_all_type_renders(self):
        """Test all individual type renders match actual renders"""
        # Test JSON schema type renders
        json_dir = f"{self.config.INPUT_FOLDER}/verified_output/type_renders/json_schema"
        for file in os.listdir(json_dir):
            if file.endswith('.yaml'):
                type_name = file.replace('.yaml', '')
                self._test_type_json_render(type_name, file)
        
        # Test BSON schema type renders
        bson_dir = f"{self.config.INPUT_FOLDER}/verified_output/type_renders/bson_schema"
        for file in os.listdir(bson_dir):
            if file.endswith('.json'):
                type_name = file.replace('.json', '')
                self._test_type_bson_render(type_name, file)

    def test_all_full_schemas(self):
        """Test all full schema renders match actual renders"""
        # Test JSON schema full renders
        json_dir = f"{self.config.INPUT_FOLDER}/verified_output/full_schemas/json_schema"
        if os.path.exists(json_dir):
            for file in os.listdir(json_dir):
                if file.endswith('.yaml'):
                    type_name = file.replace('.yaml', '')
                    self._test_full_json_render(type_name, file)
        
        # Test BSON schema full renders
        bson_dir = f"{self.config.INPUT_FOLDER}/verified_output/full_schemas/bson_schema"
        if os.path.exists(bson_dir):
            for file in os.listdir(bson_dir):
                if file.endswith('.json'):
                    type_name = file.replace('.json', '')
                    self._test_full_bson_render(type_name, file)

    def _test_type_json_render(self, type_name, expected_file):
        """Test individual type JSON schema render"""
        # Load type and render
        type_path = f"{self.config.INPUT_FOLDER}/types/{type_name}.yaml"
        type_data = load_yaml(type_path)
        type_instance = Type(type_name, type_data)
        actual = type_instance.get_json_schema()
        
        # Load expected
        expected_path = f"{self.config.INPUT_FOLDER}/verified_output/type_renders/json_schema/{expected_file}"
        expected = load_yaml(expected_path)
        
        # Compare
        self._assert_dict_equality(actual, expected, f"Type JSON schema for {type_name}")

    def _test_type_bson_render(self, type_name, expected_file):
        """Test individual type BSON schema render"""
        # Load type and render
        type_path = f"{self.config.INPUT_FOLDER}/types/{type_name}.yaml"
        type_data = load_yaml(type_path)
        type_instance = Type(type_name, type_data)
        actual = type_instance.get_bson_schema()
        
        # Load expected
        expected_path = f"{self.config.INPUT_FOLDER}/verified_output/type_renders/bson_schema/{expected_file}"
        expected = load_json(expected_path)
        
        # Compare
        self._assert_dict_equality(actual, expected, f"Type BSON schema for {type_name}")

    def _test_full_json_render(self, type_name, expected_file):
        """Test full JSON schema render with all references resolved"""
        # Load type and render with full resolution
        type_path = f"{self.config.INPUT_FOLDER}/types/{type_name}.yaml"
        type_data = load_yaml(type_path)
        type_instance = Type(type_name, type_data)
        actual = type_instance.get_json_schema()
        
        # Load expected
        expected_path = f"{self.config.INPUT_FOLDER}/verified_output/full_schemas/json_schema/{expected_file}"
        expected = load_yaml(expected_path)
        
        # Compare
        self._assert_dict_equality(actual, expected, f"Full JSON schema for {type_name}")

    def _test_full_bson_render(self, type_name, expected_file):
        """Test full BSON schema render with all references resolved"""
        # Load type and render with full resolution
        type_path = f"{self.config.INPUT_FOLDER}/types/{type_name}.yaml"
        type_data = load_yaml(type_path)
        type_instance = Type(type_name, type_data)
        actual = type_instance.get_bson_schema()
        
        # Load expected
        expected_path = f"{self.config.INPUT_FOLDER}/verified_output/full_schemas/bson_schema/{expected_file}"
        expected = load_json(expected_path)
        
        # Compare
        self._assert_dict_equality(actual, expected, f"Full BSON schema for {type_name}")

    def _assert_dict_equality(self, actual, expected, context):
        """Assert dictionary equality with detailed diff reporting"""
        if actual != expected:
            diff = self._dict_diff(actual, expected)
            self.fail(f"{context} mismatch:\n{diff}")

    def _dict_diff(self, dict1, dict2):
        """Generate a detailed diff between two dictionaries"""
        def _diff_dict(d1, d2, path=""):
            diff = []
            all_keys = set(d1.keys()) | set(d2.keys())
            
            for key in sorted(all_keys):
                current_path = f"{path}.{key}" if path else key
                
                if key not in d1:
                    diff.append(f"Missing in actual: {current_path}")
                elif key not in d2:
                    diff.append(f"Extra in actual: {current_path} = {d1[key]}")
                elif isinstance(d1[key], dict) and isinstance(d2[key], dict):
                    diff.extend(_diff_dict(d1[key], d2[key], current_path))
                elif d1[key] != d2[key]:
                    diff.append(f"Value mismatch at {current_path}:")
                    diff.append(f"  Expected: {d2[key]}")
                    diff.append(f"  Actual:   {d1[key]}")
            
            return diff
        
        return "\n".join(_diff_dict(dict1, dict2))


if __name__ == '__main__':
    unittest.main() 