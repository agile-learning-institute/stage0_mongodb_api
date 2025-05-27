import re
import logging
from typing import Optional, Dict, List
from stage0_py_utils import MongoIO, Config
from stage0_mongodb_api.managers.schema_manager import SchemaManager
from stage0_mongodb_api.managers.index_manager import IndexManager
from stage0_mongodb_api.managers.migration_manager import MigrationManager
from stage0_mongodb_api.managers.version_number import VersionNumber

logger = logging.getLogger(__name__)

class VersionManager:
    """Class for managing collection versions."""
    
    def __init__(self):
        self.mongo = MongoIO.get_instance()
        self.config = Config.get_instance()
        self.schema_manager = SchemaManager(self.config.INPUT_FOLDER)
        self.index_manager = IndexManager()
        self.migration_manager = MigrationManager()
    
    def get_current_version(self, collection_name: str) -> str:
        """Get the current version of a collection.
        
        Args:
            collection_name: Name of the collection to get version for
        
        Returns:
            str: Version string in format major.minor.patch.schema
            
        Raises:
            ValueError: If collection_name is empty or invalid
            RuntimeError: If multiple versions exist for collection
        """
        if not collection_name:
            raise ValueError("Collection name cannot be empty")
            
        version_docs = self.mongo.get_documents(
            self.config.VERSION_COLLECTION_NAME,
            match={"collection_name": collection_name}
        )
        
        if not version_docs:
            return "0.0.0.0"
            
        if len(version_docs) > 1:
            raise RuntimeError(f"Multiple versions found for collection: {collection_name}")
        
        current_version = version_docs[0].get("current_version")
        if not current_version:
            raise RuntimeError(f"Invalid version document for collection: {collection_name}")
            
        return current_version

    def update_version(self, collection_name: str, version: str) -> Dict:
        """Update the version of a collection.
        
        Args:
            collection_name: Name of the collection
            version: Version string in format major.minor.patch.schema
            
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
        VersionNumber(version)
            
        # Upsert version document
        version_doc = self.mongo.upsert_document(
            self.config.VERSION_COLLECTION_NAME,
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

    def process_versions(self, collection_name: str, versions: List[Dict]) -> List[Dict]:
        """Process a list of versions for a collection.
        see docs/processing.md for more information on processing.
        
        Args:
            collection_name: Name of the collection
            versions: List of version configurations to process
            
        Returns:
            List[Dict]: List of operation results
            
        Raises:
            ValueError: If collection_name is empty or versions is invalid
        """
        if not collection_name:
            raise ValueError("Collection name cannot be empty")
            
        if not versions:
            logger.error(f"No versions provided for collection: {collection_name}")
            return [{
                "status": "error",
                "operation": "version_processing",
                "collection": collection_name,
                "version": "unknown",
                "error": "No versions provided"
            }]
            
        operations = []
        current_version = VersionNumber(self.get_current_version(collection_name))
        
        try:
            # Process each version in sequence
            for version in versions:                
                version_number = VersionNumber(version.get("version"))
                
                # Only process versions greater than current version
                if version_number > current_version:
                    logger.info(f"Processing version {str(version_number)} for {collection_name}")
                    operations.extend(self._process_version(collection_name, version))
                    current_version = self.get_current_version(collection_name)
                else:
                    logger.info(f"Skipping version {str(version_number)} for {collection_name} - already processed")
                    
        except Exception as e:
            logger.error(f"Error during version processing for {collection_name}: {str(e)}")
            operations.append({
                "status": "error",
                "operation": "version_processing",
                "collection": collection_name,
                "version": "unknown",
                "error": f"Error during version processing: {str(e)}"
            })
            
        return operations
        
    def _process_version(self, collection_name: str, version: Dict) -> List[Dict]:
        """Process a single version of a collection.
        
        Args:
            collection_name: Name of the collection
            version: Version configuration to process
            
        Returns:
            List[Dict]: List of operation results, including any errors that occurred
        """
        operations = []

        try:
            # Required: Remove existing schema validation
            operations.append(self.schema_manager.remove_schema(collection_name))
            
            # Optional: Process drop_indexes if present
            if "drop_indexes" in version:
                for index in version["drop_indexes"]:
                    operations.append(self.index_manager.drop_index(collection_name, index))
                
            # Optional: Process aggregations if present
            if "aggregations" in version:
                for pipeline in version["aggregations"]:
                    operations.append(self.migration_manager.run_aggregation(collection_name, pipeline))
                
            # Optional: Process add_indexes if present
            if "add_indexes" in version:
                for index in version["add_indexes"]:
                    operations.append(self.index_manager.create_index(collection_name, index))
                
            # Required: Apply schema validation
            operations.append(self.schema_manager.apply_schema(collection_name, version.get("schema")))
                
            # Update version if version string is present
            if "version" in version:
                operations.append(self.update_version(collection_name, version["version"]))
                
        except Exception as e:
            logger.error(f"Error processing version for {collection_name}: {str(e)}")
            operations.append({
                "status": "error",
                "operation": "version_processing",
                "collection": collection_name,
                "version": version.get("version", "unknown"),
                "error": str(e)
            })
        
        return operations
