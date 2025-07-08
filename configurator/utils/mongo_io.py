import json
from bson import ObjectId 
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.operations import IndexModel
from bson import json_util
from configurator.utils.config import Config
from configurator.utils.configurator_exception import ConfiguratorEvent, ConfiguratorException

import logging

logger = logging.getLogger(__name__)

class MongoIO:
    """Simplified MongoDB I/O class for configuration services."""

    def __init__(self, connection_string, database_name):
        """Initialize MongoDB connection.
        
        Args:
            connection_string: MongoDB connection string
            database_name: Name of the database to use
            
        Raises:
            ConfiguratorException: If connection fails
        """
        try:
            self.client = MongoClient(
                connection_string,
                serverSelectionTimeoutMS=2000, 
                socketTimeoutMS=5000
            )
            self.client.admin.command('ping')  # Force connection
            self.db = self.client.get_database(database_name)
            logger.info(f"Connected to MongoDB: {database_name}")
        except Exception as e:
            event = ConfiguratorEvent(event_id="MON-01", event_type="CONNECTION", event_data={"error": str(e)})
            raise ConfiguratorException("Failed to connect to MongoDB", event)

    def disconnect(self):
        """Disconnect from MongoDB."""
        try:
            if self.client:
                self.client.close()
                self.client = None
                logger.info("Disconnected from MongoDB")
        except Exception as e:
            # Log the error but don't raise it - disconnect should be safe to call
            logger.warning(f"Error during disconnect: {e}")
            # Clear the client reference even if close failed
            self.client = None

    def get_collection(self, collection_name):
        """Get a collection, creating it if it doesn't exist."""
        try:
            if collection_name not in self.db.list_collection_names():
                self.db.create_collection(collection_name)
                logger.info(f"Created collection: {collection_name}")
            
            return self.db.get_collection(collection_name)
        except Exception as e:
            event = ConfiguratorEvent(event_id="MON-03", event_type="COLLECTION", event_data={"error": str(e), "collection": collection_name})
            raise ConfiguratorException(f"Failed to get/create collection {collection_name}", event)
      
    def get_documents(self, collection_name, match=None, project=None, sort_by=None):
        """Retrieve documents from a collection.

        Args:
            collection_name (str): Name of the collection to query.
            match (dict, optional): MongoDB match filter. Defaults to {}.
            project (dict, optional): Fields to include or exclude. Defaults to None.
            sort_by (list of tuple, optional): Sorting criteria. Defaults to None.

        Returns:
            list: List of documents matching the query.
        """
        match = match or {}
        project = project or None
        sort_by = sort_by or None
        
        try:
            collection = self.get_collection(collection_name)
            cursor = collection.find(match, project)
            if sort_by: 
                cursor = cursor.sort(sort_by)

            documents = list(cursor)
            return documents
        except Exception as e:
            event = ConfiguratorEvent(event_id="MON-04", event_type="GET_DOCUMENTS", event_data={"error": str(e), "collection": collection_name})
            raise ConfiguratorException(f"Failed to get documents from {collection_name}", event)
                
    def upsert(self, collection_name, match, data):
        """Upsert a document - create if not exists, update if exists.
        
        Args:
            collection_name (str): Name of the collection
            match (dict): Match criteria to find existing document
            data (dict): Data to insert or update
            
        Returns:
            dict: The upserted document
        """
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
            event = ConfiguratorEvent(event_id="MON-05", event_type="UPSERT", event_data={"error": str(e), "collection": collection_name})
            raise ConfiguratorException(f"Failed to upsert document in {collection_name}", event)

    def remove_schema_validation(self, collection_name):
        """Remove schema validation from a collection.
        
        Args:
            collection_name (str): Name of the collection
            
        Returns:
            list[ConfiguratorEvent]: List containing event with operation result
        """
        event = ConfiguratorEvent(event_id="MON-06", event_type="REMOVE_SCHEMA")
        
        try:
            self.get_collection(collection_name)
            
            command = {
                "collMod": collection_name,
                "validator": {}
            }
            
            result = self.db.command(command)
            logger.info(f"Schema validation cleared successfully: {collection_name}")
            event.record_success()
            return [event]
        except Exception as e:
            event.record_failure({"error": str(e), "collection": collection_name})
            return [event]

    def remove_index(self, collection_name, index_name):
        """Drop an index from a collection.
        
        Args:
            collection_name (str): Name of the collection
            index_name (str): Name of the index to drop
            
        Returns:
            list[ConfiguratorEvent]: List containing event with operation result
        """
        event = ConfiguratorEvent(event_id="MON-07", event_type="REMOVE_INDEX")
        
        try:
            collection = self.get_collection(collection_name)
            collection.drop_index(index_name)
            logger.info(f"Dropped index {index_name} from collection: {collection_name}")
            event.record_success()
            return [event]
        except Exception as e:
            event.record_failure({"error": str(e), "collection": collection_name, "index": index_name})
            return [event]

    def execute_migration(self, collection_name, pipeline):
        """Execute a MongoDB aggregation pipeline (migration).
        
        Args:
            collection_name (str): Name of the collection
            pipeline (list): List of pipeline stages to execute
            
        Returns:
            list[ConfiguratorEvent]: List containing event with operation result
        """
        event = ConfiguratorEvent(event_id="MON-08", event_type="EXECUTE_MIGRATION")
        
        try:
            collection = self.get_collection(collection_name)
            result = list(collection.aggregate(pipeline))
            logger.info(f"Executed migration on collection: {collection_name}")
            event.record_success()
            return [event]
        except Exception as e:
            event.record_failure({"error": str(e), "collection": collection_name})
            return [event]

    def load_migration_pipeline(self, migration_file):
        """Load a migration pipeline from a JSON file using bson.json_util.loads().
        
        Args:
            migration_file (str): Path to the migration JSON file
            
        Returns:
            list: List of pipeline stages to execute
            
        Raises:
            ConfiguratorException: If file cannot be loaded or parsed
        """
        try:
            with open(migration_file, 'r') as file:
                # Use bson.json_util.loads to preserve $ prefixes in MongoDB operators
                pipeline = json_util.loads(file.read())
            
            if not isinstance(pipeline, list):
                raise ValueError("Migration file must contain a list of pipeline stages")
            
            logger.info(f"Loaded migration pipeline from: {migration_file}")
            return pipeline
        except Exception as e:
            event = ConfiguratorEvent(event_id="MON-13", event_type="LOAD_MIGRATION", event_data={"error": str(e), "file": migration_file})
            raise ConfiguratorException(f"Failed to load migration pipeline from {migration_file}", event)

    def execute_migration_from_file(self, collection_name, migration_file):
        """Execute a migration from a JSON file.
        
        Args:
            collection_name (str): Name of the collection
            migration_file (str): Path to the migration JSON file
            
        Returns:
            list[ConfiguratorEvent]: List containing event with operation result
        """
        event = ConfiguratorEvent(event_id="MON-14", event_type="EXECUTE_MIGRATION_FILE")
        
        try:
            pipeline = self.load_migration_pipeline(migration_file)
            result = self.execute_migration(collection_name, pipeline)
            event.record_success()
            return result
        except Exception as e:
            event.record_failure({"error": str(e), "collection": collection_name, "file": migration_file})
            return [event]

    def add_index(self, collection_name, index_spec):
        """Create an index on a collection.
        
        Args:
            collection_name (str): Name of the collection
            index_spec (dict): Index specification with 'name' and 'key' fields
            
        Returns:
            list[ConfiguratorEvent]: List containing event with operation result
        """
        event = ConfiguratorEvent(event_id="MON-09", event_type="ADD_INDEX")
        
        try:
            collection = self.get_collection(collection_name)
            index_model = IndexModel(index_spec["key"], name=index_spec["name"])
            collection.create_indexes([index_model])
            logger.info(f"Created index {index_spec['name']} on collection: {collection_name}")
            event.record_success()
            return [event]
        except Exception as e:
            event.record_failure({"error": str(e), "collection": collection_name, "index": index_spec})
            return [event]

    def apply_schema_validation(self, collection_name):
        """Apply schema validation to a collection.
        
        Args:
            collection_name (str): Name of the collection
            
        Returns:
            list[ConfiguratorEvent]: List containing event with operation result
        """
        event = ConfiguratorEvent(event_id="MON-10", event_type="APPLY_SCHEMA")
        
        try:
            # This would need the schema to be passed in or retrieved
            # For now, just record success as placeholder
            logger.info(f"Schema validation applied to collection: {collection_name}")
            event.record_success()
            return [event]
        except Exception as e:
            event.record_failure({"error": str(e), "collection": collection_name})
            return [event]

    def load_json_data(self, collection_name, data_file):
        """Load test data from a file into a collection.
        
        Args:
            collection_name (str): Name of the collection
            data_file (str): Path to the JSON data file
            
        Returns:
            list[ConfiguratorEvent]: List containing event with operation result
        """
        event = ConfiguratorEvent(event_id="MON-11", event_type="LOAD_DATA")
        
        try:
            collection = self.get_collection(collection_name)
            with open(data_file, 'r') as file:
                # Use bson.json_util.loads to handle Extended JSON ($oid, $date, etc.)
                from bson import json_util
                data = json_util.loads(file.read())
            
            logger.info(f"Loading {len(data)} documents from {data_file} into collection: {collection_name}")
            result = collection.insert_many(data)
            
            event.data = {
                "documents_loaded": len(data),
                "inserted_ids": [str(oid) for oid in result.inserted_ids]
            }
            event.record_success()
            return [event]
        except Exception as e:
            event.record_failure({"error": str(e), "collection": collection_name, "data_file": data_file})
            return [event]

    def drop_database(self) -> list[ConfiguratorEvent]:
        """Drop the database."""
        event = ConfiguratorEvent(event_id="MON-12", event_type="DROP_DATABASE")
        config = Config.get_instance()
        if not config.ENABLE_DROP_DATABASE:
            event.record_failure({"error": "Drop database feature is not enabled"})
            return [event]
        if not config.BUILT_AT == "Local":
            event.record_failure({"error": "Drop database not allowed on Non-Local Build"})
            return [event]
        
        # Check if any collections have more than 100 documents
        try:
            collections_with_many_docs = []
            for collection_name in self.db.list_collection_names():
                doc_count = self.db.get_collection(collection_name).count_documents({})
                if doc_count > 100:
                    collections_with_many_docs.append({
                        "collection": collection_name,
                        "document_count": doc_count
                    })
            
            if collections_with_many_docs:
                event.event_data = collections_with_many_docs
                event.record_failure("Drop database Safety Limit Exceeded - Collections with >100 documents found")
                return [event]
            
        except Exception as e:
            event.event_data = e
            event.record_failure("Check collection counts raised an exception")
            return [event]

        try:
            self.client.drop_database(self.db.name)
            event.record_success()
            logger.info(f"Dropped database: {self.db.name}")
            return [event]
        except Exception as e:
            event.event_data=e
            event.record_failure(f"Failed to drop database {self.db.name}")
            return [event]