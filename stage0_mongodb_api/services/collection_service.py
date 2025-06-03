from typing import Dict, List, Optional
import logging
from stage0_py_utils import Config
from stage0_mongodb_api.managers.version_manager import VersionManager
from stage0_mongodb_api.managers.config_manager import ConfigManager

logger = logging.getLogger(__name__)

class CollectionService:
    """
    Utility class that backs the API collection routes.
    """
    
    @staticmethod
    def list_collections() -> Dict:
        """List all configured collections.
        
        Returns:
            Dictionary of collection configurations
        """
        config_manager = ConfigManager()
        return config_manager.collection_configs

    @staticmethod
    def process_collections() -> List[Dict]:
        """Process all configured collections.
        
        Returns:
            List of processing results for each collection
        """
        config_manager = ConfigManager()
        
        results = []
        for collection_name, collection in config_manager.collection_configs.items():
            try:
                result = CollectionService.process_collection(collection_name)
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing collection {collection_name}: {str(e)}")
                results.append({
                    "status": "error",
                    "collection": collection_name,
                    "error": str(e)
                })
        return results

    @staticmethod
    def process_collection(collection_name: str) -> Dict:
        """Process a collection configuration.
        
        Args:
            collection_name: Name of the collection to process
            
        Returns:
            Dict containing processing results:
            {
                "status": "success",
                "collection": str,
                "operations": List[Dict]  # List of operation results
            }
        """
        config_manager = ConfigManager()
        version_manager = VersionManager()
        
        # Get collection configuration
        collection = config_manager.get_collection_config(collection_name)
        if not collection:
            return {
                "status": "error",
                "collection": collection_name,
                "error": "Collection configuration not found"
            }
            
        # Process versions through version manager
        operations = version_manager.process_versions(collection_name, collection.get("versions", []))
            
        return {
            "status": "success",
            "collection": collection_name,
            "operations": operations
        }
