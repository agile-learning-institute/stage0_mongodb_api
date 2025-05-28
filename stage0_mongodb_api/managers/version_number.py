import re
from typing import List, Optional, Tuple

class VersionNumber:
    """Class for handling semantic version numbers with schema and enumerator versions.
    see /docs/versioning.md for more information on versioning.
    
    Version formats:
    - Schema file: major.minor.patch
    - Collection config: major.minor.patch.enumerator
    """
    
    MAX_VERSION = 999
    SCHEMA_VERSION_PATTERN = r'^\d+\.\d+\.\d+$'  # Three-part version for schema files
    COLLECTION_VERSION_PATTERN = r'^\d+\.\d+\.\d+\.\d+$'  # Four-part version for collection configs
    
    def __init__(self, version: str, is_collection_version: bool = False):
        """Initialize a VersionNumber instance.
        
        Args:
            version: Version string in format major.minor.patch or major.minor.patch.enumerator
            is_collection_version: Whether this is a collection version (four parts) or schema version (three parts)
            
        Raises:
            ValueError: If version format is invalid or numbers exceed MAX_VERSION
        """
        self.is_collection_version = is_collection_version
        self.version = version
        self.parts = self.parse(version)
        self._validate_parts()

    def parse(self, version: str) -> List[int]:
        """Parse a version string into components.
        
        For schema versions: [major, minor, patch]
        For collection versions: [major, minor, patch, enumerator]
        """
        if not version:
            raise ValueError("Version string cannot be empty")
            
        parts = version.split('.')
        expected_parts = 4 if self.is_collection_version else 3
        
        if len(parts) != expected_parts:
            raise ValueError(f"Version must have {expected_parts} parts for {'collection' if self.is_collection_version else 'schema'} version")
            
        # Convert parts to integers
        try:
            return [int(part) for part in parts]
        except ValueError:
            raise ValueError(f"Version components must be numeric: {version}")

    def _validate_parts(self):
        """Validate that all version parts are within acceptable range."""
        for i, part in enumerate(self.parts):
            if part > self.MAX_VERSION:
                raise ValueError(f"Version component {i} ({part}) exceeds maximum allowed value of {self.MAX_VERSION}")

    def get_schema_version(self) -> str:
        """Get the three-part schema version."""
        return '.'.join(str(p) for p in self.parts[:3])

    def get_enumerator_version(self) -> Optional[int]:
        """Get the enumerator version if this is a collection version."""
        if not self.is_collection_version:
            return None
        return self.parts[3]

    def __lt__(self, other: 'VersionNumber') -> bool:
        """Compare if this version is less than another version."""
        if not isinstance(other, VersionNumber):
            other = VersionNumber(other, self.is_collection_version)
        return self.parts < other.parts

    def __eq__(self, other: 'VersionNumber') -> bool:
        """Compare if this version equals another version."""
        if not isinstance(other, VersionNumber):
            other = VersionNumber(other, self.is_collection_version)
        return self.parts == other.parts

    def __str__(self) -> str:
        """Return the version string."""
        return self.version

    @classmethod
    def from_schema_name(cls, schema_name: str) -> Tuple[str, 'VersionNumber']:
        """Parse a schema name into collection name and version.
        
        Args:
            schema_name: Schema name in format collection.major.minor.patch
            
        Returns:
            Tuple of (collection_name, VersionNumber)
            
        Raises:
            ValueError: If schema name format is invalid
        """
        parts = schema_name.split('.')
        if len(parts) != 4:
            raise ValueError(f"Invalid schema name format: {schema_name}")
            
        collection_name = parts[0]
        version = '.'.join(parts[1:])
        
        return collection_name, cls(version, is_collection_version=False)

    @classmethod
    def from_collection_config(cls, collection_name: str, version: str) -> Tuple[str, 'VersionNumber']:
        """Parse a collection config into collection name and version.
        
        Args:
            collection_name: Name of the collection
            version: Version string in format major.minor.patch.enumerator
            
        Returns:
            Tuple of (collection_name, VersionNumber)
            
        Raises:
            ValueError: If version format is invalid or collection_name is empty
        """
        if not collection_name:
            raise ValueError("Collection name cannot be empty")
            
        return collection_name, cls(version, is_collection_version=True) 