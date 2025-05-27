import re
import logging
from typing import Optional, Dict, List
from stage0_py_utils import MongoIO, Config

logger = logging.getLogger(__name__)

class VersionNumber:
    """Class for handling semantic version numbers with schema version.
    
    Version format: major.minor.patch.schema
    - major: Major version number (0-999)
    - minor: Minor version number (0-999)
    - patch: Patch version number (0-999)
    - schema: Schema version number (0-999)
    """
    
    MAX_VERSION = 999
    VERSION_PATTERN = r'^\d+(\.\d+){0,3}$'
    
    def __init__(self, version: str):
        """Initialize a VersionNumber instance.
        
        Args:
            version: Version string in format major.minor.patch.schema
            
        Raises:
            ValueError: If version format is invalid or numbers exceed MAX_VERSION
        """
        if not re.match(self.VERSION_PATTERN, version):
            raise ValueError(f"Invalid version format: {version}")
    
        self.version = version
        self.parts = self.parse(version)
        self._validate_parts()

    def parse(self, version: str) -> List[int]:
        """Parse a version string into major, minor, patch, and schema components."""
        if not version:
            raise ValueError("Version string cannot be empty")
            
        parts = version.split('.')
        # Convert parts to integers and pad with zeros to ensure 4 components
        return [int(part) for part in parts[:4]] + [0] * (4 - len(parts))

    def _validate_parts(self):
        """Validate that all version parts are within acceptable range."""
        for i, part in enumerate(self.parts):
            if part > self.MAX_VERSION:
                raise ValueError(f"Version component {i} ({part}) exceeds maximum allowed value of {self.MAX_VERSION}")

    def __lt__(self, other: 'VersionNumber') -> bool:
        """Compare if this version is less than another version."""
        if not isinstance(other, VersionNumber):
            other = VersionNumber(other)
        return self.parts < other.parts

    def __eq__(self, other: 'VersionNumber') -> bool:
        """Compare if this version equals another version."""
        if not isinstance(other, VersionNumber):
            other = VersionNumber(other)
        return self.parts == other.parts

class VersionManager:
    """Class for managing collection versions."""
    
    def __init__(self):
        self.mongo = MongoIO.get_instance()
        self.config = Config.get_instance()
    
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
