import unittest
from unittest.mock import patch, MagicMock
from stage0_mongodb_api.managers.migration_manager import MigrationManager

class TestMigrationManager(unittest.TestCase):
    """Test cases for the MigrationManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.collection_name = "test_collection"
        self.migration = [
            {"$match": {"status": "active"}},
            {"$set": {"status": "inactive"}}
        ]

    @patch('stage0_mongodb_api.managers.migration_manager.MongoIO')
    def test_run_migration(self, mock_mongo):
        """Test running a migration pipeline."""
        # Arrange
        mock_mongo.get_instance.return_value = MagicMock()
        
        # Act
        result = MigrationManager.run_migration(self.collection_name, self.migration)
        
        # Assert
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["operation"], "migration")
        self.assertEqual(result["collection"], self.collection_name)
        self.assertEqual(result["stages"], len(self.migration))
        
        # Verify each pipeline stage was executed
        mock_mongo.get_instance.return_value.execute_pipeline.assert_has_calls([
            unittest.mock.call(self.collection_name, self.migration[0]),
            unittest.mock.call(self.collection_name, self.migration[1])
        ])
        self.assertEqual(
            mock_mongo.get_instance.return_value.execute_pipeline.call_count,
            len(self.migration)
        )

    def test_run_migration_empty_pipeline(self):
        """Test that running an empty migration pipeline raises an exception."""
        # Arrange
        empty_migration = []
        
        # Act & Assert
        with self.assertRaises(ValueError) as context:
            MigrationManager.run_migration(self.collection_name, empty_migration)
        self.assertEqual(str(context.exception), "Migration pipeline cannot be empty")

    @patch('stage0_mongodb_api.managers.migration_manager.MongoIO')
    def test_run_migration_single_stage(self, mock_mongo):
        """Test running a migration with a single pipeline stage."""
        # Arrange
        mock_mongo.get_instance.return_value = MagicMock()
        single_stage_migration = [{"$match": {"status": "active"}}]
        
        # Act
        result = MigrationManager.run_migration(self.collection_name, single_stage_migration)
        
        # Assert
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["operation"], "migration")
        self.assertEqual(result["collection"], self.collection_name)
        self.assertEqual(result["stages"], 1)
        mock_mongo.get_instance.return_value.execute_pipeline.assert_called_once_with(
            self.collection_name, single_stage_migration[0]
        )

    @patch('stage0_mongodb_api.managers.migration_manager.MongoIO')
    def test_run_migration_complex_pipeline(self, mock_mongo):
        """Test running a complex migration pipeline with multiple stages."""
        # Arrange
        mock_mongo.get_instance.return_value = MagicMock()
        complex_migration = [
            {"$match": {"status": "active"}},
            {"$set": {"status": "inactive"}},
            {"$set": {"updated_at": "$$NOW"}},
            {"$unset": ["old_field"]},
            {"$merge": {"into": "archive"}}
        ]
        
        # Act
        result = MigrationManager.run_migration(self.collection_name, complex_migration)
        
        # Assert
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["operation"], "migration")
        self.assertEqual(result["collection"], self.collection_name)
        self.assertEqual(result["stages"], len(complex_migration))
        
        # Verify each pipeline stage was executed in order
        mock_mongo.get_instance.return_value.execute_pipeline.assert_has_calls([
            unittest.mock.call(self.collection_name, stage)
            for stage in complex_migration
        ])
        self.assertEqual(
            mock_mongo.get_instance.return_value.execute_pipeline.call_count,
            len(complex_migration)
        )

if __name__ == '__main__':
    unittest.main() 