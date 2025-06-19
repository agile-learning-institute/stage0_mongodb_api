import re
import logging
from typing import Optional, Dict, List
from stage0_py_utils import MongoIO, Config
from stage0_mongodb_api.managers.version_number import VersionNumber

logger = logging.getLogger(__name__)

class VersionManager:
    """Static class for managing collection version tracking in MongoDB.
    
    This class focuses on:
    1. Reading current versions from the database
    2. Updating version records
    3. Version comparison and validation
    """
    
    @staticmethod
    def get_current_version(collection_name: str) -> str:
        """Get the current version of a collection.
        
        Args:
            collection_name: Name of the collection to get version for
        
        Returns:
            str: Version string in format major.minor.patch.schema or collection.major.minor.patch.schema
            
        Raises:
            ValueError: If collection_name is empty or invalid
            RuntimeError: If multiple versions exist for collection
        """
        if not collection_name:
            raise ValueError("Collection name cannot be empty")
            
        mongo = MongoIO.get_instance()
        config = Config.get_instance()
            
        version_docs = mongo.get_documents(
            config.VERSION_COLLECTION_NAME,
            match={"collection_name": collection_name}
        )
        
        if not version_docs:
            return f"{collection_name}.0.0.0.0"
            
        if len(version_docs) > 1:
            raise RuntimeError(f"Multiple versions found for collection: {collection_name}")
        
        current_version = version_docs[0].get("current_version")
        if not current_version:
            raise RuntimeError(f"Invalid version document for collection: {collection_name}")
            
        # Ensure version includes collection name
        version = VersionNumber(current_version)
        if not version.collection_name:
            return f"{collection_name}.{current_version}"
        return current_version

    @staticmethod
    def update_version(collection_name: str, version: str) -> Dict:
        """Update the version of a collection.
        
        Args:
            collection_name: Name of the collection
            version: Version string in format major.minor.patch.schema or collection.major.minor.patch.schema
            
        Returns:
            Dict containing operation result:
            {
                "status": "success",
                "operation": "version_update",
                "collection": str,
                "version": str
            }
            
        Raises:
            ValueError: If version format is invalid or collection_name is empty
        """
        if not collection_name:
            raise ValueError("Collection name cannot be empty")
            
        # Validate version by attempting to create a VersionNumber instance
        version_obj = VersionNumber(version)
        
        # Ensure version includes collection name
        if not version_obj.collection_name:
            version = f"{collection_name}.{version}"
            
        mongo = MongoIO.get_instance()
        config = Config.get_instance()
            
        # Upsert version document
        version_doc = mongo.upsert_document(
            config.VERSION_COLLECTION_NAME,
            match={"collection_name": collection_name},
            data={"collection_name": collection_name, "current_version": version}
        )
        
        if not version_doc:
            raise RuntimeError(f"Failed to update version for collection: {collection_name}")
        
        return {
            "status": "success",
            "operation": "version_update",
            "collection": collection_name,
            "version": version
        }

    @staticmethod
    def get_pending_versions(collection_name: str, available_versions: List[str]) -> List[str]:
        """Get list of versions that need to be processed for a collection.
        
        Args:
            collection_name: Name of the collection
            available_versions: List of available version strings to check
            
        Returns:
            List[str]: List of version strings that are newer than current version
        """
        current_version = VersionNumber(VersionManager.get_current_version(collection_name))
        pending_versions = []
        
        for version_str in available_versions:
            version_number = VersionNumber(version_str)
            if version_number > current_version:
                pending_versions.append(version_str)
                
        return sorted(pending_versions, key=lambda v: VersionNumber(v))
