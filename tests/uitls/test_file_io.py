import os
import unittest
from datetime import datetime
from configurator.utils.config import Config
from configurator.utils.file_io import FileIO, File
import tempfile
import json
import yaml
from unittest.mock import Mock, patch, mock_open
from configurator.utils.configurator_exception import ConfiguratorException

class TestFile(unittest.TestCase):
    """Test cases for File class"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file_path = os.path.join(self.temp_dir, "test_file.txt")
        self.test_yaml_path = os.path.join(self.temp_dir, "test.yaml")
        self.test_json_path = os.path.join(self.temp_dir, "test.json")

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_file_initialization_existing_file(self):
        """Test File initialization with existing file"""
        # Create a test file
        with open(self.test_file_path, 'w') as f:
            f.write("test content")
        
        file_obj = File(self.test_file_path)
        
        self.assertEqual(file_obj.name, "test_file.txt")
        self.assertGreater(file_obj.size, 0)
        self.assertIsInstance(file_obj.created_at, str)
        self.assertIsInstance(file_obj.updated_at, str)

    def test_file_initialization_nonexistent_file(self):
        """Test File initialization with non-existent file"""
        with self.assertRaises(ConfiguratorException) as context:
            file_obj = File(self.test_file_path)
        
        self.assertIn("Failed to get file properties", str(context.exception))

    def test_file_read_only_property(self):
        """Test file read-only property detection"""
        # Create a test file
        with open(self.test_file_path, 'w') as f:
            f.write("test content")
        
        # Make file read-only
        os.chmod(self.test_file_path, 0o444)
        
        file_obj = File(self.test_file_path)
        self.assertTrue(file_obj.read_only)
        
        # Make file writable
        os.chmod(self.test_file_path, 0o666)
        file_obj = File(self.test_file_path)
        self.assertFalse(file_obj.read_only)

    def test_file_to_dict(self):
        """Test file to_dict method"""
        # Create a test file
        with open(self.test_file_path, 'w') as f:
            f.write("test content")
        
        file_obj = File(self.test_file_path)
        file_dict = file_obj.to_dict()
        
        expected_keys = ["name", "read_only", "created_at", "updated_at", "size"]
        for key in expected_keys:
            self.assertIn(key, file_dict)
        
        self.assertEqual(file_dict["name"], "test_file.txt")
        self.assertGreater(file_dict["size"], 0)

    def test_file_with_different_extensions(self):
        """Test File class with different file extensions"""
        extensions = [".yaml", ".yml", ".json", ".txt", ".md", ".py"]
        
        for ext in extensions:
            file_path = os.path.join(self.temp_dir, f"test{ext}")
            with open(file_path, 'w') as f:
                f.write("content")
            
            file_obj = File(file_path)
            self.assertEqual(file_obj.name, f"test{ext}")


class TestFileIO(unittest.TestCase):
    """Test cases for FileIO class"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.file_io = FileIO()
        
        # Create test files
        self.test_yaml_path = os.path.join(self.temp_dir, "test.yaml")
        self.test_json_path = os.path.join(self.temp_dir, "test.json")
        self.test_txt_path = os.path.join(self.temp_dir, "test.txt")
        
        # Create test data
        self.yaml_data = {"name": "test", "value": 42}
        self.json_data = {"key": "value", "number": 123}

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('configurator.utils.file_io.Config')
    def test_get_documents_empty_folder(self, mock_config):
        """Test get_documents with empty folder"""
        mock_config.get_instance.return_value.INPUT_FOLDER = self.temp_dir
        
        files = self.file_io.get_documents("nonexistent_folder")
        self.assertEqual(files, [])

    @patch('configurator.utils.file_io.Config')
    def test_get_documents_with_files(self, mock_config):
        """Test get_documents with existing files"""
        mock_config.get_instance.return_value.INPUT_FOLDER = self.temp_dir
        
        # Create test files
        with open(self.test_yaml_path, 'w') as f:
            yaml.dump(self.yaml_data, f)
        with open(self.test_json_path, 'w') as f:
            json.dump(self.json_data, f)
        
        files = self.file_io.get_documents("")
        self.assertEqual(len(files), 2)
        
        file_names = [f.name for f in files]
        self.assertIn("test.yaml", file_names)
        self.assertIn("test.json", file_names)

    @patch('configurator.utils.file_io.Config')
    def test_get_document_yaml(self, mock_config):
        """Test get_document with YAML file"""
        mock_config.get_instance.return_value.INPUT_FOLDER = self.temp_dir
        
        # Create test YAML file
        with open(self.test_yaml_path, 'w') as f:
            yaml.dump(self.yaml_data, f)
        
        result = self.file_io.get_document("", "test.yaml")
        self.assertEqual(result, self.yaml_data)

    @patch('configurator.utils.file_io.Config')
    def test_get_document_json(self, mock_config):
        """Test get_document with JSON file"""
        mock_config.get_instance.return_value.INPUT_FOLDER = self.temp_dir
        
        # Create test JSON file
        with open(self.test_json_path, 'w') as f:
            json.dump(self.json_data, f)
        
        result = self.file_io.get_document("", "test.json")
        self.assertEqual(result, self.json_data)

    @patch('configurator.utils.file_io.Config')
    def test_get_document_unsupported_type(self, mock_config):
        """Test get_document with unsupported file type"""
        mock_config.get_instance.return_value.INPUT_FOLDER = self.temp_dir
        
        # Create test file with unsupported extension
        with open(self.test_txt_path, 'w') as f:
            f.write("test content")
        
        with self.assertRaises(ConfiguratorException) as context:
            self.file_io.get_document("", "test.txt")
        
        self.assertEqual(context.exception.event.type, "UNSUPPORTED_FILE_TYPE")

    @patch('configurator.utils.file_io.Config')
    def test_get_document_file_not_found(self, mock_config):
        """Test get_document with non-existent file"""
        mock_config.get_instance.return_value.INPUT_FOLDER = self.temp_dir
        
        with self.assertRaises(ConfiguratorException) as context:
            self.file_io.get_document("", "nonexistent.yaml")
        
        self.assertIn("File not found", str(context.exception))

    @patch('configurator.utils.file_io.Config')
    def test_put_document_yaml(self, mock_config):
        """Test put_document with YAML file"""
        mock_config.get_instance.return_value.INPUT_FOLDER = self.temp_dir
        
        result = self.file_io.put_document("", "test.yaml", self.yaml_data)
        
        self.assertIsInstance(result, File)
        self.assertEqual(result.name, "test.yaml")
        self.assertGreaterEqual(result.size, 0)
        
        # Verify file content
        with open(self.test_yaml_path, 'r') as f:
            content = yaml.safe_load(f)
        self.assertEqual(content, self.yaml_data)

    @patch('configurator.utils.file_io.Config')
    def test_put_document_json(self, mock_config):
        """Test put_document with JSON file"""
        mock_config.get_instance.return_value.INPUT_FOLDER = self.temp_dir
        
        result = self.file_io.put_document("", "test.json", self.json_data)
        
        self.assertIsInstance(result, File)
        self.assertEqual(result.name, "test.json")
        self.assertGreaterEqual(result.size, 0)
        
        # Verify file content
        with open(self.test_json_path, 'r') as f:
            content = json.load(f)
        self.assertEqual(content, self.json_data)

    @patch('configurator.utils.file_io.Config')
    def test_put_document_unsupported_type(self, mock_config):
        """Test put_document with unsupported file type"""
        mock_config.get_instance.return_value.INPUT_FOLDER = self.temp_dir
        
        with self.assertRaises(ConfiguratorException) as context:
            self.file_io.put_document("", "test.txt", {"data": "test"})
        
        self.assertEqual(context.exception.event.type, "UNSUPPORTED_FILE_TYPE")

    @patch('configurator.utils.file_io.Config')
    def test_delete_document_success(self, mock_config):
        """Test delete_document with existing file"""
        mock_config.get_instance.return_value.INPUT_FOLDER = self.temp_dir
        
        # Create test file
        with open(self.test_yaml_path, 'w') as f:
            f.write("test content")
        
        result = self.file_io.delete_document("", "test.yaml")
        
        self.assertEqual(result.status, "SUCCESS")
        self.assertFalse(os.path.exists(self.test_yaml_path))

    @patch('configurator.utils.file_io.Config')
    def test_delete_document_file_not_found(self, mock_config):
        """Test delete_document with non-existent file"""
        mock_config.get_instance.return_value.INPUT_FOLDER = self.temp_dir
        
        result = self.file_io.delete_document("", "nonexistent.yaml")
        
        self.assertEqual(result.status, "FAILURE")
        self.assertIn("File not found", str(result.data))

    @patch('configurator.utils.file_io.Config')
    def test_lock_unlock_success(self, mock_config):
        """Test lock_unlock functionality"""
        mock_config.get_instance.return_value.INPUT_FOLDER = self.temp_dir
        
        # Create test file
        with open(self.test_yaml_path, 'w') as f:
            f.write("test content")
        
        # Test locking (making read-only)
        result = self.file_io.lock_unlock("", "test.yaml")
        self.assertIsInstance(result, File)
        self.assertEqual(result.name, "test.yaml")
        self.assertTrue(result.read_only)
        
        # Test unlocking (making writable)
        result = self.file_io.lock_unlock("", "test.yaml")
        self.assertIsInstance(result, File)
        self.assertEqual(result.name, "test.yaml")
        self.assertFalse(result.read_only)

    @patch('configurator.utils.file_io.Config')
    def test_lock_unlock_file_not_found(self, mock_config):
        """Test lock_unlock with non-existent file"""
        mock_config.get_instance.return_value.INPUT_FOLDER = self.temp_dir
        
        with self.assertRaises(ConfiguratorException) as context:
            self.file_io.lock_unlock("", "nonexistent.yaml")
        
        self.assertIn("File not found", str(context.exception))


if __name__ == '__main__':
    unittest.main()