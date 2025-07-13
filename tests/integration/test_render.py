from configurator.utils.config import Config
import unittest
import os

class TestRender(unittest.TestCase):
    """Test Render of input files"""

    def test_something(self):
        """Test Something"""
        # Arrange
        value = True

        # Act
        result = False
    
        # Assert
        self.assertEqual(result, value)

class TestComplexRefs(TestRender):
    """Test Render of complex refs"""

    def setUp(self):
        os.environ['INPUT_FOLDER'] = "./tests/test_cases/passing_complex_refs"
        Config._instance = None
        self.config = Config.get_instance()
        os.environ['INPUT_FOLDER'].delete()

    def tearDown(self):
        pass

class TestEmpty(TestRender):
    """Test Render of empty files"""

    def setUp(self):
        os.environ['INPUT_FOLDER'] = "./tests/test_cases/passing_empty"
        Config._instance = None
        self.config = Config.get_instance()
        os.environ['INPUT_FOLDER'].delete()

    def tearDown(self):
        pass

class TestProcess(TestRender):
    """Test Processing"""

    def setUp(self):
        os.environ['INPUT_FOLDER'] = "./tests/test_cases/passing_process"
        Config._instance = None
        self.config = Config.get_instance()
        os.environ['INPUT_FOLDER'].delete()

    def tearDown(self):
        pass

class TestTemplate(TestRender):
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