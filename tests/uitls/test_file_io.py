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
        
        self.assertEqual(file_obj.file_name, "test_file.txt")
        self.assertGreater(file_obj.size, 0)
        self.assertIsInstance(file_obj.created_at, str)
        self.assertIsInstance(file_obj.updated_at, str)

    def test_file_initialization_nonexistent_file(self):
        """Test File initialization with non-existent file"""
        with self.assertRaises(ConfiguratorException) as context:
            file_obj = File(self.test_file_path)
        
        self.assertIn("Failed to get file properties", str(context.exception))

    def test_file_read_only_property(self):
        """Test file read-only property detection - removed as no longer supported"""
        # This test is no longer applicable as we removed read_only functionality
        pass

    def test_file_to_dict(self):
        """Test file to_dict method"""
        # Create a test file
        with open(self.test_file_path, 'w') as f:
            f.write("test content")
        
        file_obj = File(self.test_file_path)
        file_dict = file_obj.to_dict()
        
        expected_keys = ["file_name", "created_at", "updated_at", "size"]
        for key in expected_keys:
            self.assertIn(key, file_dict)
        
        self.assertEqual(file_dict["file_name"], "test_file.txt")
        self.assertGreater(file_dict["size"], 0)

    def test_file_with_different_extensions(self):
        """Test File class with different file extensions"""
        extensions = [".yaml", ".yml", ".json", ".txt", ".md", ".py"]
        
        for ext in extensions:
            file_path = os.path.join(self.temp_dir, f"test{ext}")
            with open(file_path, 'w') as f:
                f.write("content")
            
            file_obj = File(file_path)
            self.assertEqual(file_obj.file_name, f"test{ext}")


class TestFileIO(unittest.TestCase):
    """Test cases for FileIO class
    NOTE: Config is never mocked in these tests. The real Config singleton is used, and INPUT_FOLDER is set to a temp directory in setUp and restored in tearDown.
    """

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.file_io = FileIO()
        self.config = Config.get_instance()
        self._original_input_folder = self.config.INPUT_FOLDER
        self.config.INPUT_FOLDER = self.temp_dir
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
        self.config.INPUT_FOLDER = self._original_input_folder

    def test_get_documents_empty_folder(self):
        """Test get_documents with empty folder"""
        with self.assertRaises(ConfiguratorException) as context:
            self.file_io.get_documents("nonexistent_folder")
        self.assertIn("Folder not found", str(context.exception))

    def test_get_documents_with_files(self):
        """Test get_documents with existing files"""
        # Create test files
        with open(self.test_yaml_path, 'w') as f:
            yaml.dump(self.yaml_data, f)
        with open(self.test_json_path, 'w') as f:
            json.dump(self.json_data, f)
        
        files = self.file_io.get_documents("")
        self.assertEqual(len(files), 2)
        
        file_names = [f.file_name for f in files]
        self.assertIn("test.yaml", file_names)
        self.assertIn("test.json", file_names)

    def test_get_document_yaml(self):
        """Test get_document with YAML file"""
        # Create test YAML file
        with open(self.test_yaml_path, 'w') as f:
            yaml.dump(self.yaml_data, f)
        
        result = self.file_io.get_document("", "test.yaml")
        self.assertEqual(result, self.yaml_data)

    def test_get_document_json(self):
        """Test get_document with JSON file"""
        # Create test JSON file
        with open(self.test_json_path, 'w') as f:
            json.dump(self.json_data, f)
        
        result = self.file_io.get_document("", "test.json")
        self.assertEqual(result, self.json_data)

    def test_get_document_unsupported_type(self):
        """Test get_document with unsupported file type"""
        # Create test file with unsupported extension
        with open(self.test_txt_path, 'w') as f:
            f.write("test content")
        
        with self.assertRaises(ConfiguratorException) as context:
            self.file_io.get_document("", "test.txt")
        
        self.assertEqual(context.exception.event.type, "UNSUPPORTED_FILE_TYPE")

    def test_get_document_file_not_found(self):
        """Test get_document with non-existent file"""
        with self.assertRaises(ConfiguratorException) as context:
            self.file_io.get_document("", "nonexistent.yaml")
        
        self.assertIn("File not found", str(context.exception))

    def test_put_document_yaml(self):
        """Test put_document with YAML file"""
        result = self.file_io.put_document("", "test.yaml", self.yaml_data)
        
        self.assertIsInstance(result, File)
        self.assertEqual(result.file_name, "test.yaml")
        self.assertGreaterEqual(result.size, 0)
        
        # Verify file content
        with open(self.test_yaml_path, 'r') as f:
            content = yaml.safe_load(f)
        self.assertEqual(content, self.yaml_data)

    def test_put_document_json(self):
        """Test put_document with JSON file"""
        result = self.file_io.put_document("", "test.json", self.json_data)
        
        self.assertIsInstance(result, File)
        self.assertEqual(result.file_name, "test.json")
        self.assertGreaterEqual(result.size, 0)
        
        # Verify file content
        with open(self.test_json_path, 'r') as f:
            content = json.load(f)
        self.assertEqual(content, self.json_data)

    def test_put_document_unsupported_type(self):
        """Test put_document with unsupported file type"""
        with self.assertRaises(ConfiguratorException) as context:
            self.file_io.put_document("", "test.txt", {"data": "test"})
        
        self.assertEqual(context.exception.event.type, "UNSUPPORTED_FILE_TYPE")

    def test_delete_document_success(self):
        """Test delete_document with existing file"""
        # Create test file
        with open(self.test_yaml_path, 'w') as f:
            f.write("test content")
        
        result = self.file_io.delete_document("", "test.yaml")
        
        self.assertEqual(result.status, "SUCCESS")
        self.assertFalse(os.path.exists(self.test_yaml_path))

    def test_delete_document_file_not_found(self):
        """Test delete_document with non-existent file"""
        result = self.file_io.delete_document("", "nonexistent.yaml")
        
        self.assertEqual(result.status, "FAILURE")
        self.assertIn("File not found", str(result.data))

    def test_lock_unlock_success(self):
        """Test lock_unlock functionality - removed as no longer supported"""
        # This test is no longer applicable as we removed lock/unlock functionality
        pass

    def test_lock_unlock_file_not_found(self):
        """Test lock_unlock with non-existent file - removed as no longer supported"""
        # This test is no longer applicable as we removed lock/unlock functionality
        pass


if __name__ == '__main__':
    unittest.main()