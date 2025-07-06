"""
MongoIO Integration Tests

These tests require a running MongoDB instance accessible via the configured connection string.
Tests will create, modify, and delete documents and indexes within a test collection.
"""
import unittest
import tempfile
import json
from datetime import datetime
from pymongo import ASCENDING, DESCENDING
from configurator.utils.config import Config
from configurator.utils.mongo_io import MongoIO
from configurator.utils.configurator_exception import ConfiguratorException


class TestMongoIO(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = Config.get_instance()
        self.test_collection_name = "test_collection"
        
        # Create MongoIO instance using config values
        self.mongo_io = MongoIO(
            self.config.MONGO_CONNECTION_STRING, 
            self.config.MONGO_DB_NAME
        )
        
        # Clear any existing test data
        try:
            self.mongo_io.drop_database()
        except:
            pass  # Database might not exist
        
        # Recreate the database
        self.mongo_io = MongoIO(
            self.config.MONGO_CONNECTION_STRING, 
            self.config.MONGO_DB_NAME
        )
        
        self._setup_test_documents()

    def tearDown(self):
        """Clean up test fixtures."""
        if hasattr(self, 'mongo_io'):
            self.mongo_io.disconnect()

    def _setup_test_documents(self):
        """Set up test documents."""
        # Insert test documents
        docs = [
            {"name": "Alpha", "sort_value": 1, "status": "active"},
            {"name": "Bravo", "sort_value": 2, "status": "active"},
            {"name": "Charlie", "sort_value": 3, "status": "inactive"},
            {"name": "Delta", "sort_value": 4, "status": "archived"},
            {"name": "Echo", "sort_value": 5, "status": "active"}
        ]
        
        collection = self.mongo_io.get_collection(self.test_collection_name)
        collection.insert_many(docs)

    def test_connection_and_disconnect(self):
        """Test MongoDB connection and disconnection."""
        # Connection is tested in setUp
        self.assertIsNotNone(self.mongo_io.client)
        self.assertIsNotNone(self.mongo_io.db)
        
        # Test disconnect
        self.mongo_io.disconnect()
        self.assertIsNone(self.mongo_io.client)

    def test_get_collection(self):
        """Test getting a collection."""
        collection = self.mongo_io.get_collection(self.test_collection_name)
        self.assertIsNotNone(collection)
        self.assertEqual(collection.name, self.test_collection_name)

    def test_get_documents(self):
        """Test retrieving documents."""
        # Get all documents
        docs = self.mongo_io.get_documents(self.test_collection_name)
        self.assertEqual(len(docs), 5)
        
        # Get documents with match
        active_docs = self.mongo_io.get_documents(
            self.test_collection_name, 
            match={"status": "active"}
        )
        self.assertEqual(len(active_docs), 3)
        
        # Get documents with projection
        projected_docs = self.mongo_io.get_documents(
            self.test_collection_name,
            project={"name": 1, "_id": 0}
        )
        self.assertEqual(len(projected_docs), 5)
        self.assertIn("name", projected_docs[0])
        self.assertNotIn("_id", projected_docs[0])
        
        # Get documents with sorting
        sorted_docs = self.mongo_io.get_documents(
            self.test_collection_name,
            sort_by=[("sort_value", DESCENDING)]
        )
        self.assertEqual(sorted_docs[0]["sort_value"], 5)

    def test_upsert(self):
        """Test upserting documents."""
        # Insert new document
        result = self.mongo_io.upsert(
            self.test_collection_name,
            {"name": "Foxtrot"},
            {"name": "Foxtrot", "sort_value": 6, "status": "active"}
        )
        self.assertEqual(result["name"], "Foxtrot")
        
        # Update existing document
        result = self.mongo_io.upsert(
            self.test_collection_name,
            {"name": "Alpha"},
            {"name": "Alpha", "sort_value": 1, "status": "updated"}
        )
        self.assertEqual(result["status"], "updated")

    def test_remove_schema_validation(self):
        """Test removing schema validation."""
        event = self.mongo_io.remove_schema_validation(self.test_collection_name)
        self.assertEqual(event.status, "SUCCESS")

    def test_remove_index(self):
        """Test removing an index."""
        # First create an index
        collection = self.mongo_io.get_collection(self.test_collection_name)
        collection.create_index("name", name="test_index")
        
        # Then remove it
        event = self.mongo_io.remove_index(self.test_collection_name, "test_index")
        self.assertEqual(event.status, "SUCCESS")

    def test_execute_migration(self):
        """Test executing a migration pipeline."""
        pipeline = [
            {"$match": {"status": "active"}},
            {"$count": "active_count"}
        ]
        
        event = self.mongo_io.execute_migration(self.test_collection_name, pipeline)
        self.assertEqual(event.status, "SUCCESS")

    def test_add_index(self):
        """Test adding an index."""
        index_spec = {
            "name": "test_index",
            "key": [("name", ASCENDING)]
        }
        
        event = self.mongo_io.add_index(self.test_collection_name, index_spec)
        self.assertEqual(event.status, "SUCCESS")

    def test_apply_schema_validation(self):
        """Test applying schema validation."""
        event = self.mongo_io.apply_schema_validation(self.test_collection_name)
        self.assertEqual(event.status, "SUCCESS")

    def test_load_json_data(self):
        """Test loading JSON data from file."""
        # Create a temporary JSON file
        test_data = [
            {"name": "Test1", "value": 1},
            {"name": "Test2", "value": 2}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_file = f.name
        
        try:
            event = self.mongo_io.load_json_data("test_load_collection", temp_file)
            self.assertEqual(event.status, "SUCCESS")
            self.assertEqual(event.data["documents_loaded"], 2)
        finally:
            import os
            os.unlink(temp_file)

    def test_drop_database(self):
        """Test dropping the database."""
        self.mongo_io.drop_database()
        
        # Verify database is dropped by checking if it exists in the client
        # The database should no longer exist in the list of databases
        database_names = [db['name'] for db in self.mongo_io.client.list_databases()]
        self.assertNotIn(self.config.MONGO_DB_NAME, database_names)

    def test_error_handling(self):
        """Test error handling for invalid operations."""
        # Test invalid collection name
        with self.assertRaises(ConfiguratorException):
            self.mongo_io.get_documents("")
        
        # Test invalid index name
        event = self.mongo_io.remove_index(self.test_collection_name, "nonexistent_index")
        self.assertEqual(event.status, "FAILURE")


if __name__ == '__main__':
    unittest.main()