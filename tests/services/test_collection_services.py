import unittest
from unittest.mock import patch, MagicMock
from src.services.collection_service import CollectionService

class TestCollectionServices(unittest.TestCase):

    def test_something(self):
        """Test Something"""
        # Arrange

        # Act
        response = self.client.get('/api/workshop?query=name')

        # Assert
        self.assertTrue(False)

if __name__ == '__main__':
    unittest.main()
