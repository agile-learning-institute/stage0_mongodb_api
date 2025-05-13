from typing import Dict, List
from stage0_py_utils import MongoIO

class IndexManager:
    """Static class for managing MongoDB indexes."""
    
    @staticmethod
    def create_index(collection_name: str, index_config: Dict) -> Dict:
        """Create an index based on configuration."""
        mongo = MongoIO.get_instance()
        
        try:
            # Validate index configuration
            if "name" not in index_config:
                raise ValueError("Index configuration must include 'name'")
            if "keys" not in index_config:
                raise ValueError("Index configuration must include 'keys'")
                
            # Create the index
            mongo.create_index(collection_name, index_config)
            return {
                "status": "success",
                "index": index_config["name"]
            }
        except Exception as e:
            return {
                "status": "error",
                "index": index_config.get("name", "unknown"),
                "error": str(e)
            }

    @staticmethod
    def drop_index(collection_name: str, index_name: str) -> Dict:
        """Drop an index by name."""
        mongo = MongoIO.get_instance()
        
        try:
            mongo.drop_index(collection_name, index_name)
            return {
                "status": "success",
                "index": index_name
            }
        except Exception as e:
            return {
                "status": "error",
                "index": index_name,
                "error": str(e)
            }

    @staticmethod
    def list_indexes(collection_name: str) -> List[Dict]:
        """List all indexes for a collection."""
        mongo = MongoIO.get_instance()
        
        try:
            indexes = mongo.get_documents(
                collection_name,
                match={},
                project={"indexes": 1}
            )
            return indexes or []
        except Exception as e:
            return [{
                "status": "error",
                "error": str(e)
            }] 