"""
MongoIO Integration Tests

These tests require a running MongoDB instance accessible via the configured connection string.
Tests will create, modify, and delete documents and indexes within a test collection.
"""
import unittest
import tempfile
import json
import os
from datetime import datetime
from unittest.mock import patch, Mock
from pymongo import ASCENDING, DESCENDING
from configurator.utils.config import Config
from configurator.utils.mongo_io import MongoIO
from configurator.utils.configurator_exception import ConfiguratorException


class TestMongoIO(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        # Reset Config singleton to ensure we get default values, not test file values
        Config._instance = None
        
        os.environ['ENABLE_DROP_DATABASE'] = 'true'
        os.environ['BUILT_AT'] = 'Local'
        self.config = Config.get_instance()
        self.config.initialize()
        self.test_collection_name = "test_collection"
        
        # Create MongoIO instance using config values
        self.mongo_io = MongoIO(
            self.config.MONGO_CONNECTION_STRING, 
            self.config.MONGO_DB_NAME
        )
        
        # Clear any existing test data by dropping the database
        try:
            self.mongo_io.drop_database()
        except Exception as e:
            # Database might not exist, which is fine for testing
            pass

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

    def tearDown(self):
        """Clean up test fixtures."""
        if hasattr(self, 'mongo_io'):
            try:
                # Drop the test database
                self.mongo_io.drop_database()
            except:
                pass  # Database might not drop..
            self.mongo_io.disconnect()
        
        # Clean up environment variables set in setUp
        if 'ENABLE_DROP_DATABASE' in os.environ:
            del os.environ['ENABLE_DROP_DATABASE']
        if 'BUILT_AT' in os.environ:
            del os.environ['BUILT_AT']

    def test_connection_and_disconnect(self):
        """Test MongoDB connection and disconnection."""
        # Connection is tested in setUp
        self.assertIsNotNone(self.mongo_io.client)
        self.assertIsNotNone(self.mongo_io.db)
        
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
        events = self.mongo_io.remove_schema_validation(self.test_collection_name)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].status, "SUCCESS")

    def test_remove_index(self):
        """Test removing an index."""
        # First create an index
        collection = self.mongo_io.get_collection(self.test_collection_name)
        collection.create_index("name", name="test_index")
        
        # Then remove it
        events = self.mongo_io.remove_index(self.test_collection_name, "test_index")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].status, "SUCCESS")

    def test_execute_migration(self):
        """Test executing a migration pipeline."""
        pipeline = [
            {"$match": {"status": "active"}},
            {"$count": "active_count"}
        ]
        
        events = self.mongo_io.execute_migration(self.test_collection_name, pipeline)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].status, "SUCCESS")

    def test_add_index(self):
        """Test adding an index."""
        index_spec = {
            "name": "test_index",
            "key": [("name", ASCENDING)]
        }
        
        events = self.mongo_io.add_index(self.test_collection_name, index_spec)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].status, "SUCCESS")

    def test_apply_schema_validation(self):
        """Test applying schema validation."""
        # Create a simple test schema
        test_schema = {
            "bsonType": "object",
            "required": ["name"],
            "properties": {
                "name": {"bsonType": "string"},
                "sort_value": {"bsonType": "int"},
                "status": {"bsonType": "string"}
            }
        }
        
        events = self.mongo_io.apply_schema_validation(self.test_collection_name, test_schema)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].status, "SUCCESS")
        
        # Verify the event data includes the full BSON schema
        self.assertIn("bson_schema", events[0].data)
        self.assertEqual(events[0].data["bson_schema"], test_schema)
        self.assertEqual(events[0].data["collection"], self.test_collection_name)
        self.assertEqual(events[0].data["operation"], "schema_validation_applied")

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
            events = self.mongo_io.load_json_data("test_load_collection", temp_file)
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0].status, "SUCCESS")
            self.assertEqual(events[0].data["documents_loaded"], 2)
            
            # Verify the event data includes the full insert result
            self.assertIn("insert_many_result", events[0].data)
            self.assertIn("collection", events[0].data)
            self.assertIn("data_file", events[0].data)
            self.assertIn("documents_loaded", events[0].data)
            self.assertEqual(events[0].data["collection"], "test_load_collection")
            self.assertEqual(events[0].data["documents_loaded"], 2)
            self.assertIn("inserted_ids", events[0].data["insert_many_result"])
            self.assertIn("acknowledged", events[0].data["insert_many_result"])
        finally:
            import os
            os.unlink(temp_file)

if __name__ == '__main__':
    unittest.main()