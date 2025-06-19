from typing import Dict, List, Optional
import logging
from stage0_py_utils import Config
from stage0_mongodb_api.managers.config_manager import ConfigManager
from stage0_mongodb_api.managers.version_manager import VersionManager

logger = logging.getLogger(__name__)

class CollectionNotFoundError(Exception):
    """Raised when a collection is not found."""
    def __init__(self, collection_name: str, errors: List[Dict] = None):
        self.collection_name = collection_name
        self.errors = errors or []
        super().__init__(f"Collection '{collection_name}' not found")

class CollectionProcessingError(Exception):
    """Raised when collection processing fails."""
    def __init__(self, collection_name: str, errors: List[Dict]):
        self.collection_name = collection_name
        self.errors = errors
        super().__init__(f"Failed to process collection '{collection_name}'")

class CollectionService:
    """
    Utility class that backs the API collection routes.
    """
    
    @staticmethod
    def list_collections(token: Dict = None) -> Dict:
        """List all configured collections.
        
        Args:
            token: Authentication token for RBAC enforcement
            
        Returns:
            Dictionary of collection name: version string
            
        Raises:
            CollectionProcessingError: If there are load or validation errors
        """
        config_manager = ConfigManager()
        
        # Check for load errors
        if config_manager.load_errors:
            raise CollectionProcessingError("collections", config_manager.load_errors)
            
        # Check for validation errors
        validation_errors = config_manager.validate_configs()
        if validation_errors:
            raise CollectionProcessingError("collections", validation_errors)
            
        # Create a dict of collection name: version string
        collections = {}
        for collection_name, collection in config_manager.collection_configs.items():
            collections[collection_name] = VersionManager.get_current_version(collection_name)
        return collections

    @staticmethod
    def get_collection(collection_name: str, token: Dict = None) -> Dict:
        """Get a collection configuration.
        
        Args:
            collection_name: Name of the collection to get
            token: Authentication token for RBAC enforcement
            
        Returns:
            Dict containing collection configuration
            
        Raises:
            CollectionNotFoundError: If collection is not found
            CollectionProcessingError: If there are load or validation errors
        """
        config_manager = ConfigManager()
        
        # Check for load errors
        if config_manager.load_errors:
            raise CollectionProcessingError(collection_name, config_manager.load_errors)
            
        # Check for validation errors
        validation_errors = config_manager.validate_configs()
        if validation_errors:
            raise CollectionProcessingError(collection_name, validation_errors)
        
        collection = config_manager.get_collection_config(collection_name)
        if not collection:
            raise CollectionNotFoundError(collection_name)
            
        return collection

    @staticmethod
    def process_collections(token: Dict = None) -> List[Dict]:
        """Process all configured collections.
        
        Args:
            token: Authentication token for RBAC enforcement
            
        Returns:
            List of processing results for each collection
            
        Raises:
            CollectionProcessingError: If there are load or validation errors
        """
        config_manager = ConfigManager()
        
        # Check for load errors
        if config_manager.load_errors:
            raise CollectionProcessingError("collections", config_manager.load_errors)
            
        # Check for validation errors
        validation_errors = config_manager.validate_configs()
        if validation_errors:
            raise CollectionProcessingError("collections", validation_errors)
        
        results = []
        for collection_name, collection in config_manager.collection_configs.items():
            try:
                result = CollectionService.process_collection(collection_name, token)
                results.append(result)
            except CollectionNotFoundError:
                # Skip collections that don't exist
                continue
            except Exception as e:
                logger.error(f"Error processing collection {collection_name}: {str(e)}")
                results.append({
                    "status": "error",
                    "collection": collection_name,
                    "error": str(e)
                })
        return results

    @staticmethod
    def process_collection(collection_name: str, token: Dict = None) -> Dict:
        """Process a collection configuration.
        
        Args:
            collection_name: Name of the collection to process
            token: Authentication token for RBAC enforcement
            
        Returns:
            Dict containing processing results:
            {
                "status": "success",
                "collection": str,
                "operations": List[Dict]  # List of operation results
            }
            
        Raises:
            CollectionNotFoundError: If collection is not found
            CollectionProcessingError: If there are load, validation, or processing errors
        """
        config_manager = ConfigManager()
        
        # Check for load errors
        if config_manager.load_errors:
            raise CollectionProcessingError(collection_name, config_manager.load_errors)
            
        # Check for validation errors
        validation_errors = config_manager.validate_configs()
        if validation_errors:
            raise CollectionProcessingError(collection_name, validation_errors)
        
        # Process collection versions through config manager
        try:
            operations = config_manager.process_collection_versions(collection_name)
        except ValueError as e:
            # ConfigManager.process_collection_versions raises ValueError for not found collections
            if "not found in configurations" in str(e):
                raise CollectionNotFoundError(collection_name)
            else:
                logger.error(f"Error processing collection {collection_name}: {str(e)}")
                raise CollectionProcessingError(collection_name, [{
                    "error": "processing_error",
                    "error_id": "API-005",
                    "message": str(e)
                }])
        except Exception as e:
            logger.error(f"Error processing collection {collection_name}: {str(e)}")
            raise CollectionProcessingError(collection_name, [{
                "error": "processing_error",
                "error_id": "API-005",
                "message": str(e)
            }])
            
        return {
            "status": "success",
            "collection": collection_name,
            "operations": operations
        }
