from typing import Dict, List
from stage0_py_utils import MongoIO

class IndexManager:
    """Static class for managing MongoDB indexes."""
    
    @staticmethod
    def create_index(collection_name: str, index_config: Dict) -> bool:
        """Create an index based on configuration."""
        mongo = MongoIO.get_instance()
        
        # Create the index
        mongo.create_index(collection_name, index_config)
        return True

    @staticmethod
    def drop_index(collection_name: str, index_name: str) -> bool:
        """Drop an index by name."""
        mongo = MongoIO.get_instance()
        
        mongo.drop_index(collection_name, index_name)
        return True

    @staticmethod
    def list_indexes(collection_name: str) -> List[Dict]:
        """List all indexes for a collection."""
        mongo = MongoIO.get_instance()

        indexes = mongo.get_indexes(collection_name=collection_name)        
        return indexes