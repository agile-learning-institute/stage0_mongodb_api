from typing import Dict, List
from stage0_py_utils import MongoIO

class IndexManager:
    """Manages MongoDB indexes for collections."""
    
    @staticmethod
    def create_index(collection_name: str, index_config: Dict) -> Dict:
        """Create an index based on configuration.
        
        Args:
            collection_name: Name of the collection
            index_config: Index configuration dictionary passed directly to MongoDB.
                See MongoDB's [Index Specifications](https://www.mongodb.com/docs/manual/reference/method/db.collection.createIndex/)
                for details on supported options.
                Must contain 'name' and 'key' fields.
        
        Returns:
            Dict containing operation result:
            {
                "status": "success",
                "operation": "create_index",
                "collection": str,
                "index": str
            }
            
        Raises:
            ValueError: If index_config is missing required fields
        """
        if "name" not in index_config:
            raise ValueError("Index configuration must include 'name' field")
        if "key" not in index_config:
            raise ValueError("Index configuration must include 'key' field")
            
        mongo = MongoIO.get_instance()
        mongo.create_index(collection_name, index_config)
        
        return {
            "status": "success",
            "operation": "create_index",
            "collection": collection_name,
            "index": index_config["name"]
        }

    @staticmethod
    def drop_index(collection_name: str, index_name: str) -> Dict:
        """Drop an index by name.
        
        Args:
            collection_name: Name of the collection
            index_name: Name of the index to drop
        
        Returns:
            Dict containing operation result:
            {
                "status": "success",
                "operation": "drop_index",
                "collection": str,
                "index": str
            }
        """
        mongo = MongoIO.get_instance()
        mongo.drop_index(collection_name, index_name)
        
        return {
            "status": "success",
            "operation": "drop_index",
            "collection": collection_name,
            "index": index_name
        }

    @staticmethod
    def list_indexes(collection_name: str) -> Dict:
        """List all indexes for a collection.
        
        Args:
            collection_name: Name of the collection
        
        Returns:
            Dict containing operation result:
            {
                "status": "success",
                "operation": "list_indexes",
                "collection": str,
                "indexes": List[Dict]  # List of index configurations
            }
        """
        mongo = MongoIO.get_instance()
        indexes = mongo.get_indexes(collection_name=collection_name)
        
        return {
            "status": "success",
            "operation": "list_indexes",
            "collection": collection_name,
            "indexes": indexes
        }