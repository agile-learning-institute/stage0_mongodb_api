import unittest
from unittest.mock import patch, MagicMock
from stage0_mongodb_api.managers.migration_manager import MigrationManager

class TestMigrationManager(unittest.TestCase):
    """Test cases for the MigrationManager class."""

    def setUp(self):
        self.collection_name = "test_collection"

    @patch('stage0_py_utils.MongoIO.get_instance')
    def test_run_migration_single_pipeline(self, mock_get_instance):
        """Test running a single migration pipeline."""
        mock_mongo = MagicMock()
        mock_get_instance.return_value = mock_mongo
        migration = {
            "name": "test_pipeline",
            "pipeline": [
                {"$addFields": {"test_field": "value"}},
                {"$out": "test_collection"}
            ]
        }
        result = MigrationManager.run_migration(self.collection_name, migration)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["operation"], "migration")
        self.assertEqual(result["collection"], self.collection_name)
        self.assertEqual(result["pipeline"]["name"], "test_pipeline")
        self.assertEqual(result["pipeline"]["stages"], 2)
        self.assertEqual(mock_mongo.execute_pipeline.call_count, 1)
        mock_mongo.execute_pipeline.assert_called_once_with(self.collection_name, migration["pipeline"])

    def test_run_migration_empty_migration(self):
        """Test that empty migration raises ValueError."""
        with self.assertRaises(ValueError) as context:
            MigrationManager.run_migration(self.collection_name, {})
        self.assertIn("Migration must contain a 'pipeline' field", str(context.exception))

    def test_run_migration_missing_pipeline(self):
        """Test that migration without pipeline field raises ValueError."""
        migration = {"name": "test_pipeline"}
        with self.assertRaises(ValueError) as context:
            MigrationManager.run_migration(self.collection_name, migration)
        self.assertIn("Migration must contain a 'pipeline' field", str(context.exception))

    def test_run_migration_empty_pipeline(self):
        """Test that empty pipeline raises ValueError."""
        migration = {
            "name": "empty_pipeline",
            "pipeline": []
        }
        with self.assertRaises(ValueError) as context:
            MigrationManager.run_migration(self.collection_name, migration)
        self.assertIn("Pipeline 'empty_pipeline' cannot be empty", str(context.exception))

    @patch('stage0_py_utils.MongoIO.get_instance')
    def test_run_migration_unnamed_pipeline(self, mock_get_instance):
        """Test running a migration pipeline without a name."""
        mock_mongo = MagicMock()
        mock_get_instance.return_value = mock_mongo
        migration = {
            "pipeline": [
                {"$addFields": {"test_field": "value"}},
                {"$out": "test_collection"}
            ]
        }
        result = MigrationManager.run_migration(self.collection_name, migration)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["operation"], "migration")
        self.assertEqual(result["collection"], self.collection_name)
        self.assertEqual(result["pipeline"]["name"], "unnamed_pipeline")
        self.assertEqual(result["pipeline"]["stages"], 2)
        self.assertEqual(mock_mongo.execute_pipeline.call_count, 1)
        mock_mongo.execute_pipeline.assert_called_once_with(self.collection_name, migration["pipeline"])

    @patch('stage0_py_utils.MongoIO.get_instance')
    def test_run_migration_complex_pipeline(self, mock_get_instance):
        """Test running a complex migration pipeline with multiple stages."""
        mock_mongo = MagicMock()
        mock_get_instance.return_value = mock_mongo
        migration = {
            "name": "complex_pipeline",
            "pipeline": [
                {"$match": {"status": "active"}},
                {"$set": {"status": "inactive"}},
                {"$set": {"updated_at": "$$NOW"}},
                {"$unset": ["old_field"]},
                {"$merge": {"into": "archive"}}
            ]
        }
        result = MigrationManager.run_migration(self.collection_name, migration)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["operation"], "migration")
        self.assertEqual(result["collection"], self.collection_name)
        self.assertEqual(result["pipeline"]["name"], "complex_pipeline")
        self.assertEqual(result["pipeline"]["stages"], 5)
        self.assertEqual(mock_mongo.execute_pipeline.call_count, 1)
        mock_mongo.execute_pipeline.assert_called_once_with(self.collection_name, migration["pipeline"])

if __name__ == '__main__':
    unittest.main() 