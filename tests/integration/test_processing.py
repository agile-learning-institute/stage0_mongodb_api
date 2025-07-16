from configurator.services.configuration_services import Configuration
from configurator.utils.config import Config
from configurator.utils.file_io import FileIO
import unittest
import os

class TestProcessing(unittest.TestCase):
    """Test Processing of several passing_* test cases"""

    def test_processing(self):
        """Test Processing"""
        # Arrange
        config = Config.get_instance()
        files = FileIO.get_documents(config.CONFIGURATION_FOLDER)
        results = []
        # Act
        for file in files:
            configuration = Configuration(file.name)
            results.append(configuration.process())
        
        # Assert
        # Assert results = verified_output/processing_events.yaml
        # Assert database contents = verified_output/test_database/
        # For file in verfied_output/bson_schema Assert file contents == ConfigurationVersion().render bson
        # For file in verfied_output/json_schema Assert file contents == ConfigurationVersion().render json

class TestComplexRefs(TestProcessing):
    """Test Processing of complex refs"""

    def setUp(self):
        os.environ['INPUT_FOLDER'] = "./tests/test_cases/passing_complex_refs"
        Config._instance = None
        self.config = Config.get_instance()
        os.environ['INPUT_FOLDER'].delete()

    def tearDown(self):
        pass

class TestEmpty(TestProcessing):
    """Test Processing of empty files"""

    def setUp(self):
        os.environ['INPUT_FOLDER'] = "./tests/test_cases/passing_empty"
        Config._instance = None
        self.config = Config.get_instance()
        os.environ['INPUT_FOLDER'].delete()

    def tearDown(self):
        pass

class TestProcess(TestProcessing):
    """Test Processing"""

    def setUp(self):
        os.environ['INPUT_FOLDER'] = "./tests/test_cases/passing_process"
        Config._instance = None
        self.config = Config.get_instance()
        os.environ['INPUT_FOLDER'].delete()

    def tearDown(self):
        pass

class TestTemplate(TestProcessing):
    """Test Template"""

    def setUp(self):
        os.environ['INPUT_FOLDER'] = "./tests/test_cases/template"
        Config._instance = None
        self.config = Config.get_instance()
        os.environ['INPUT_FOLDER'].delete()

    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main() 