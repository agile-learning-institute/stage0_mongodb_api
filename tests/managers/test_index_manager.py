import unittest
from unittest.mock import patch, MagicMock
from src.managers.index_manager import IndexManager

class TestIndexManager(unittest.TestCase):

    def test_something(self):
        """Test Something"""
        # Arrange

        # Act
        response = self.client.get('/api/workshop?query=name')

        # Assert
        self.assertTrue(False)

if __name__ == '__main__':
    unittest.main()
