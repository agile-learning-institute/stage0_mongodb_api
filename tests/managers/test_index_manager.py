import unittest
from unittest.mock import patch, MagicMock
from stage0_mongodb_api.managers.index_manager import IndexManager

class TestIndexManager(unittest.TestCase):
    """Test cases for the IndexManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.collection_name = "test_collection"
        self.index_name = "test_index"
        self.index_config = {
            "name": self.index_name,
            "key": {"field": 1},
            "unique": True
        }

    @patch('stage0_mongodb_api.managers.index_manager.MongoIO')
    def test_create_index(self, mock_mongo):
        """Test creating an index."""
        # Arrange
        mock_mongo.get_instance.return_value = MagicMock()
        
        # Act
        result = IndexManager.create_index(self.collection_name, [self.index_config])
        
        # Assert
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["operation"], "create_index")
        self.assertEqual(result["collection"], self.collection_name)
        self.assertIn(self.index_name, result["indexes"])
        mock_mongo.get_instance.return_value.create_index.assert_called_once_with(
            self.collection_name, [self.index_config]
        )

    def test_create_index_missing_name(self):
        """Test creating an index without a name."""
        # Arrange
        config_without_name = {"key": {"field": 1}}
        
        # Act & Assert
        with self.assertRaises(ValueError) as context:
            IndexManager.create_index(self.collection_name, [config_without_name])
        self.assertEqual(str(context.exception), "Index configuration must include 'name' field")

    def test_create_index_missing_key(self):
        """Test creating an index without a key."""
        # Arrange
        config_without_key = {"name": self.index_name}
        
        # Act & Assert
        with self.assertRaises(ValueError) as context:
            IndexManager.create_index(self.collection_name, [config_without_key])
        self.assertEqual(str(context.exception), "Index configuration must include 'key' field")

    @patch('stage0_mongodb_api.managers.index_manager.MongoIO')
    def test_drop_index(self, mock_mongo):
        """Test dropping an index."""
        # Arrange
        mock_mongo.get_instance.return_value = MagicMock()

        # Act
        result = IndexManager.drop_index(self.collection_name, self.index_name)

        # Assert
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["operation"], "drop_index")
        self.assertEqual(result["collection"], self.collection_name)
        self.assertEqual(result["index"], self.index_name)
        mock_mongo.get_instance.return_value.drop_index.assert_called_once_with(
            self.collection_name, self.index_name
        )

    @patch('stage0_mongodb_api.managers.index_manager.MongoIO')
    def test_list_indexes(self, mock_mongo):
        """Test listing indexes."""
        # Arrange
        mock_indexes = [
            {"name": "index1", "key": {"field1": 1}},
            {"name": "index2", "key": {"field2": -1}}
        ]
        mock_mongo.get_instance.return_value = MagicMock()
        mock_mongo.get_instance.return_value.get_indexes.return_value = mock_indexes
        
        # Act
        result = IndexManager.list_indexes(self.collection_name)
        
        # Assert
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["operation"], "list_indexes")
        self.assertEqual(result["collection"], self.collection_name)
        self.assertEqual(result["indexes"], mock_indexes)
        mock_mongo.get_instance.return_value.get_indexes.assert_called_once_with(
            collection_name=self.collection_name
        )

if __name__ == '__main__':
    unittest.main()
