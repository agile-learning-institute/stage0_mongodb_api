import re
import logging
from typing import Optional, Dict, List
from stage0_py_utils import MongoIO, Config

logger = logging.getLogger(__name__)

class VersionNumber:
    """Class for handling semantic version numbers with schema version.
    
    Version format: major.minor.patch.schema
    - major: Major version number
    - minor: Minor version number
    - patch: Patch version number
    - schema: Schema version number
    """
    
    def __init__(self, version: str):
        """Initialize a VersionNumber instance.
        
        Args:
            version: Version string in format major.minor.patch.schema
            
        Raises:
            ValueError: If version format is invalid
        """
        pattern = r'^\d+(\.\d+){0,3}$'
        if not re.match(pattern, version):
            raise ValueError(f"Invalid version format: {version}")
    
        self.version = version
        self.parts = self.parse(version)

    def parse(self, version: str) -> List[int]:
        """Parse a version string into major, minor, patch, and schema components."""
        if not version:
            return [0, 0, 0, 0]
            
        parts = version.split('.')
        # Convert parts to integers and pad with zeros to ensure 4 components
        return [int(part) for part in parts[:4]] + [0] * (4 - len(parts))

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
        
        Returns:
            str: Version string in format major.minor.patch.enums
                 Returns "0.0.0.0" if no version exists
        """
        version_docs = self.mongo.get_documents(
            self.config.VERSION_COLLECTION_NAME,
            match={"collection_name":collection_name}
        )
        
        if not version_docs:
            logger.warning(f"No version found for collection: {collection_name}")
            return "0.0.0.0"
        if len(version_docs) != 1:
            logger.warning(f"Multiple versions found for collection: {collection_name}")
            return "0.0.0.0"
        
        current_version = version_docs[0].get("current_version")
        print(f"Returning version: {current_version}")
        return current_version

    def update_version(self, collection_name: str, version: str) -> bool:
        """Update the version of a collection.
        
        Args:
            collection_name: Name of the collection
            version: Version string in format major.minor.patch.schema
            
        Returns:
            bool: True if update was successful
            
        Raises:
            ValueError: If version format is invalid
        """
        # Validate version by attempting to create a VersionNumber instance
        VersionNumber(version)
            
        # Upsert version document
        version_doc = self.mongo.upsert_document(
            self.config.VERSION_COLLECTION_NAME,
            match={"collection_name":collection_name},
            data= {"collection_name":collection_name,"current_version":version}
        )
        
        return True
