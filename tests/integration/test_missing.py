from configurator.utils.config import Config
import unittest
import os

class TestMissing(unittest.TestCase):
    """Test Missing input folders"""

    def setUp(self):
        os.environ['INPUT_FOLDER'] = "./tests/test_cases/failing_empty"
        Config._instance = None
        self.config = Config.get_instance()
        os.environ['INPUT_FOLDER'].delete()

    def tearDown(self):
        pass

    def test_failing_empty(self):
        """Test Failing Empty"""
        # Arrange
        value = True

        # Act
        result = False
    
        # Assert
        self.assertEqual(result, value)

if __name__ == '__main__':
    unittest.main() 