from configurator.utils.config import Config
import unittest
import os

class TestValidation(unittest.TestCase):
    """Test Validation of input files"""

    def setUp(self):
        os.environ['INPUT_FOLDER'] = "./tests/test_cases/failing_validation"
        Config._instance = None
        self.config = Config.get_instance()
        os.environ['INPUT_FOLDER'].delete()

    def tearDown(self):
        pass

    def test_something(self):
        """Test Something"""
        # Arrange
        value = True

        # Act
        result = False
    
        # Assert
        self.assertEqual(result, value)

if __name__ == '__main__':
    unittest.main() 