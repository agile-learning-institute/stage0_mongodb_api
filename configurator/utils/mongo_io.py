import sys
from bson import ObjectId 
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.operations import IndexModel
from bson import json_util
from configurator.utils.configurator_exception import ConfiguratorEvent, ConfiguratorException

import logging

from configurator.utils.configurator_exception import ConfiguratorException
logger = logging.getLogger(__name__)

class MongoIO:

    def __init__(self, connection_string, database_name):
        try:
            self.client = MongoClient(
                connection_string,
                serverSelectionTimeoutMS=2000, 
                socketTimeoutMS=5000
            )
            self.client.admin.command('ping')  # Force connection
            self.db = self.client.get_database(database_name)
        except Exception as e:
            event = ConfiguratorEvent(event_id="MON-01", event_type="CONNECTION", event_data=e)
            raise ConfiguratorException("Failed to connect to MongoDB", event, e)
        
        logger.info(f"Connected to MongoDB")

    def disconnect(self):
        """Disconnect from MongoDB."""
        try:
            if self.client:
                self.client.close()
                logger.info("Disconnected from MongoDB")
        except Exception as e:
            event = ConfiguratorEvent(event_id="MON-02", event_type="CONNECTION", event_data=e)
            raise ConfiguratorException("Failed to disconnect to MongoDB", event)

    def get_collection(self, collection_name):
        """Get a collection, creating it if it doesn't exist."""
        try:
            if collection_name not in self.db.list_collection_names():
                self.db.create_collection(collection_name)
                logger.info(f"Created collection: {collection_name}")
            
            return self.db.get_collection(collection_name)
        except Exception as e:
            event = ConfiguratorEvent(event_id="MON-03", event_type="COLLECTION", event_data=e)
            raise ConfiguratorException(f"Failed get/create collection {collection_name}", event)
      
    def get_documents(self, collection_name, match=None, project=None, sort_by=None):
        """Retrieve a list of documents based on a match, projection, and optional sorting.

        Args:
            collection_name (str): Name of the collection to query.
            match (dict, optional): MongoDB match filter. Defaults to {}.
            project (dict, optional): Fields to include or exclude. Defaults to None.
            sort_by (list of tuple, optional): Sorting criteria (e.g., [('field1', ASCENDING), ('field2', DESCENDING)]). Defaults to None.

        Returns:
            list: List of documents matching the query.
        """
        # Default match and projection
        match = match or {}
        project = project or None
        sort_by = sort_by or None
        try:
            collection = self.get_collection(collection_name)
            cursor = collection.find(match, project)
            if sort_by: cursor = cursor.sort(sort_by)

            documents = list(cursor)
            return documents
        except Exception as e:
            event = ConfiguratorEvent(event_id="MON-04", event_type="GET_DOCUMENTS", event_data=e)
            raise ConfiguratorException(f"Failed get/create collection {collection_name}", event)
                
    def upsert_document(self, collection_name, match, data):
        """Upsert a document - create if not exists, update if exists.
        
        Args:
            collection_name (str): Name of the collection
            match (dict): Match criteria to find existing document
            data (dict): Data to insert or update
            
        Returns:
            dict: The upserted document
        """
        if not self.connected: raise Exception("upsert_document when Mongo Not Connected")
        
        try:
            collection = self.get_collection(collection_name)
            result = collection.find_one_and_update(
                match,
                {"$set": data},
                upsert=True,
                return_document=True
            )
            return result
        except Exception as e:
            logger.error(f"Failed to upsert document: {e}")
            raise e

    def apply_schema(self, collection_name, schema):
        """Apply schema validation to a collection.
        
        Args:
            collection_name (str): Name of the collection
            schema (dict): MongoDB JSON Schema validation rules
        """
        if not self.connected: raise Exception("apply_schema when Mongo Not Connected")
        
        try:
            # Get collection (creates if doesn't exist)
            self.get_collection(collection_name)
            
            command = {
                "collMod": collection_name,
                "validator": {"$jsonSchema": schema}
            }
            
            result = self.db.command(command)
            logger.info(f"Schema validation applied successfully: {collection_name} {result}")
        except Exception as e:
            logger.error(f"Failed to apply schema validation: {collection_name} {e} {schema}")
            raise e

    def get_schema(self, collection_name):
        """Get the current schema validation rules for a collection.
        
        Args:
            collection_name (str): Name of the collection
            
        Returns:
            dict: The current schema validation rules
        """
        if not self.connected: raise Exception("get_schema when Mongo Not Connected")
        
        try:
            # Get collection (creates if doesn't exist)
            collection = self.get_collection(collection_name)
            options = collection.options()
            validation_rules = options.get("validator", {})
            
            return validation_rules
        except Exception as e:
            logger.error(f"Failed to get schema validation: {collection_name} {e}")
            raise e

    def remove_schema(self, collection_name):
        """Remove schema validation from a collection.
        
        Args:
            collection_name (str): Name of the collection
        """
        if not self.connected: raise Exception("remove_schema when Mongo Not Connected")
        
        try:
            # Get collection (creates if doesn't exist)
            self.get_collection(collection_name)
            
            command = {
                "collMod": collection_name,
                "validator": {}
            }
            
            result = self.db.command(command)
            logger.info(f"Schema validation cleared successfully: {result}")
        except Exception as e:
            logger.error(f"Failed to clear schema validation: {e}")
            raise e

    def create_index(self, collection_name, indexes):
        """Create indexes on a collection.
        
        Args:
            collection_name (str): Name of the collection
            indexes (list): List of index specifications, each containing 'name' and 'key' fields
        """
        if not self.connected: raise Exception("create_index when Mongo Not Connected")
        
        try:
            collection = self.get_collection(collection_name)
            index_models = [IndexModel(index["key"], name=index["name"]) for index in indexes]
            collection.create_indexes(index_models)
            logger.info(f"Created {len(indexes)} indexes")
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
            raise e

    def drop_index(self, collection_name, index_name):
        """Drop an index from a collection.
        
        Args:
            collection_name (str): Name of the collection
            index_name (str): Name of the index to drop
        """
        if not self.connected: raise Exception("drop_index when Mongo Not Connected")
        
        try:
            collection = self.get_collection(collection_name)
            collection.drop_index(index_name)
            logger.info(f"Dropped index {index_name} from collection: {collection_name}")
        except Exception as e:
            logger.error(f"Failed to drop index: {e}")
            raise e

    def get_indexes(self, collection_name):
        """Get all indexes for a collection.
        
        Args:
            collection_name (str): Name of the collection
            
        Returns:
            list: List of index configurations
        """
        if not self.connected: raise Exception("get_indexes when Mongo Not Connected")
        
        try:
            collection = self.get_collection(collection_name)
            return list(collection.list_indexes())
        except Exception as e:
            logger.error(f"Failed to get indexes: {e}")
            raise e

    def execute_pipeline(self, collection_name, pipeline):
        """Execute a MongoDB aggregation pipeline.
        
        Args:
            collection_name (str): Name of the collection
            pipeline (list): List of pipeline stages to execute
        """
        if not self.connected: raise Exception("execute_pipeline when Mongo Not Connected")
        
        try:
            collection = self.get_collection(collection_name)
            result = list(collection.aggregate(pipeline))
            logger.info(f"Executed pipeline on collection: {collection_name}")
            return result
        except Exception as e:
            logger.error(f"Failed to execute pipeline: {e}")
            raise e
    
    def load_test_data(self, collection_name, data_file):
        """Load test data from a file into a collection."""
        if not self.connected: raise Exception("load_test_data when Mongo Not Connected")
        from pymongo.errors import BulkWriteError
        try:
            collection = self.get_collection(collection_name)
            with open(data_file, 'r') as file:
                # Use bson.json_util.loads to handle MongoDB Extended JSON format
                data = json_util.loads(file.read())
            
            logger.info(f"Loading {len(data)} documents from {data_file} into collection: {collection_name}")
            result = collection.insert_many(data)
            
            return {
                "status": "success",
                "operation": "load_test_data",
                "collection": collection_name,
                "documents_loaded": len(data),
                "inserted_ids": [str(oid) for oid in result.inserted_ids],
                "acknowledged": result.acknowledged
            }
        except BulkWriteError as bwe:
            logger.error(f"Schema validation failed for {data_file}: {bwe.details}")
            raise TestDataLoadError("Schema validation failed during test data load", details=bwe.details)
        except Exception as e:
            logger.error(f"Failed to load test data: {e}")
            raise e
            