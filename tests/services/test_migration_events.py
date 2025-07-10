import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import tempfile
import json

from configurator.services.configuration_services import Configuration, Version
from configurator.utils.mongo_io import MongoIO
from configurator.utils.config import Config


class TestMigrationEvents(unittest.TestCase):
    """Test migration event structure and nesting."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = Config.get_instance()
        self.config.INPUT_FOLDER = tempfile.mkdtemp()
        
        # Create a test migration file
        self.migration_file = os.path.join(self.config.INPUT_FOLDER, "migrations", "test_migration.json")
        os.makedirs(os.path.dirname(self.migration_file), exist_ok=True)
        
        # Create a simple migration pipeline
        migration_pipeline = [
            {"$addFields": {"test_field": "test_value"}},
            {"$out": "test_collection"}
        ]
        
        with open(self.migration_file, 'w') as f:
            json.dump(migration_pipeline, f)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.config.INPUT_FOLDER)
    
    @patch('configurator.utils.mongo_io.MongoClient')
    @patch('configurator.services.configuration_services.Enumerators')
    def test_migration_event_structure(self, mock_enumerators, mock_client):
        """Test that migration events are properly nested."""
        # Use MagicMock for __getitem__ support
        mock_client_instance = MagicMock()
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection
        mock_collection.aggregate.return_value = []
        
        # Mock the admin command for ping
        mock_admin = MagicMock()
        mock_client_instance.admin = mock_admin
        mock_admin.command.return_value = {"ok": 1}
        
        # Patch Enumerators.version to return a dummy enumerations object
        mock_enumerators.return_value.version.return_value = {}
        
        # Create a configuration with migrations
        config_data = {
            "title": "Test Collection",
            "description": "Test collection for migration events",
            "name": "test_collection",
            "versions": [
                {
                    "version": "1.0.0.1",
                    "migrations": ["test_migration.json"]
                }
            ]
        }
        
        # Create configuration and version objects
        config = Configuration("test.yaml", config_data)
        version = config.versions[0]
        
        # Patch get_bson_schema to return a minimal valid schema
        version.get_bson_schema = MagicMock(return_value={"type": "object", "properties": {}})
        
        # Mock MongoIO
        mongo_io = MongoIO("mongodb://localhost:27017", "test_db")
        
        # Process the version
        event = version.process(mongo_io)
        
        # Verify the main event structure
        self.assertEqual(event.id, "test.1.0.0.1")
        self.assertEqual(event.type, "PROCESS")
        self.assertEqual(event.status, "SUCCESS")
        
        # Find the EXECUTE_MIGRATIONS sub-event
        migrations_event = None
        for sub_event in event.sub_events:
            if sub_event.type == "EXECUTE_MIGRATIONS":
                migrations_event = sub_event
                break
        
        self.assertIsNotNone(migrations_event, "EXECUTE_MIGRATIONS event should exist")
        self.assertEqual(migrations_event.id, "PRO-03")
        self.assertEqual(migrations_event.status, "SUCCESS")
        
        # Verify migration file event (MON-14) exists and is nested
        migration_file_event = None
        for sub_event in migrations_event.sub_events:
            if sub_event.type == "EXECUTE_MIGRATION_FILE":
                migration_file_event = sub_event
                break
        
        self.assertIsNotNone(migration_file_event, "EXECUTE_MIGRATION_FILE event should exist")
        self.assertEqual(migration_file_event.id, "MON-14")
        self.assertEqual(migration_file_event.status, "SUCCESS")
        
        # Verify the migration file event has the correct data
        self.assertIn("migration_file", migration_file_event.data)
        self.assertEqual(migration_file_event.data["migration_file"], "test_migration.json")
        self.assertIn("pipeline_stages", migration_file_event.data)
        self.assertEqual(migration_file_event.data["pipeline_stages"], 2)
        
        # Verify that MON-13 (LOAD_MIGRATION) and MON-08 (EXECUTE_MIGRATION) events are nested
        load_event = None
        execute_event = None
        
        for sub_event in migration_file_event.sub_events:
            if sub_event.type == "LOAD_MIGRATION":
                load_event = sub_event
            elif sub_event.type == "EXECUTE_MIGRATION":
                execute_event = sub_event
        
        self.assertIsNotNone(load_event, "LOAD_MIGRATION event should be nested")
        self.assertIsNotNone(execute_event, "EXECUTE_MIGRATION event should be nested")
        self.assertEqual(load_event.id, "MON-13")
        self.assertEqual(execute_event.id, "MON-08")
        self.assertEqual(load_event.status, "SUCCESS")
        self.assertEqual(execute_event.status, "SUCCESS")


if __name__ == '__main__':
    unittest.main() 