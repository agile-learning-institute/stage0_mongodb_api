from typing import Dict, List
from stage0_py_utils import MongoIO

class IndexManager:
    """Manages MongoDB indexes for collections."""
    
    @staticmethod
    def create_index(collection_name: str, index_configs: list) -> Dict:
        """Create one or more indexes based on configuration.
        
        Args:
            collection_name: Name of the collection
            index_configs: List of index configuration dictionaries. Each dict must contain 'name' and 'key' fields.
        
        Returns:
            Dict containing operation result in consistent format
            
        Raises:
            ValueError: If any index_config is missing required fields
        """
        for idx in index_configs:
            if "name" not in idx:
                raise ValueError("Index configuration must include 'name' field")
            if "key" not in idx:
                raise ValueError("Index configuration must include 'key' field")
        
        mongo = MongoIO.get_instance()
        mongo.create_index(collection_name, index_configs)
        
        return {
            "operation": "create_index",
            "collection": collection_name,
            "message": f"Created {len(index_configs)} index(es) for {collection_name}",
            "details_type": "index",
            "details": {
                "indexes": [idx["name"] for idx in index_configs],
                "index_configs": index_configs
            },
            "status": "success"
        }

    @staticmethod
    def drop_index(collection_name: str, index_name: str) -> Dict:
        """Drop an index by name.
        
        Args:
            collection_name: Name of the collection
            index_name: Name of the index to drop
        
        Returns:
            Dict containing operation result in consistent format
        """
        mongo = MongoIO.get_instance()
        try:
            mongo.drop_index(collection_name, index_name)
        except Exception as e:
            return {
                "operation": "drop_index",
                "collection": collection_name,
                "message": str(e),
                "details_type": "error",
                "details": {
                    "error": str(e),
                    "index": index_name
                },
                "status": "error"
            }
        
        return {
            "operation": "drop_index",
            "collection": collection_name,
            "message": f"Dropped index '{index_name}' from {collection_name}",
            "details_type": "index",
            "details": {
                "index": index_name
            },
            "status": "success"
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
            "operation": "list_indexes",
            "collection": collection_name,
            "indexes": indexes,
            "status": "success"
        }