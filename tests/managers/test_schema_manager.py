import unittest
from unittest.mock import patch, MagicMock
from stage0_mongodb_api.managers.schema_manager import SchemaManager

class TestSchemaManager(unittest.TestCase):

    def test_something(self):
        """Test Something"""
        # Arrange

        # Act
        response = self.client.get('/api/workshop?query=name')

        # Assert
        self.assertTrue(False)

if __name__ == '__main__':
    unittest.main()
