import re
from typing import List, Optional

class VersionNumber:
    """Class for handling four-part version numbers.
    
    Version format: major.minor.patch.enumerator
    Example: 1.0.0.1
    Also supports collection.major.minor.patch.enumerator
    Example: user.1.0.0.1
    """
    
    MAX_VERSION = 999
    VERSION_PATTERN = r'^\d+\.\d+\.\d+\.\d+$'
    
    def __init__(self, version: str):
        """Initialize a VersionNumber instance.
        
        Args:
            version: Version string in format major.minor.patch.enumerator or collection.major.minor.patch.enumerator
            
        Raises:
            ValueError: If version format is invalid or numbers exceed MAX_VERSION
        """
        if not version:
            raise ValueError("Version string cannot be empty")
            
        # Check for invalid dot patterns first
        if version.startswith('.') or version.endswith('.') or '..' in version:
            raise ValueError(f"Invalid version format: {version} - cannot have leading/trailing dots or consecutive dots")
            
        # Split into parts and check if first part is a collection name
        parts = version.split('.')
        if len(parts) == 5:  # collection.major.minor.patch.enumerator
            self.collection_name = parts[0]
            version_str = '.'.join(parts[1:])
        else:
            self.collection_name = None
            version_str = version
                
        if not re.match(self.VERSION_PATTERN, version_str):
            raise ValueError(f"Invalid version format: {version_str}")
            
        self.version = version_str
        self.parts = [int(part) for part in version_str.split('.')]

        # Validate that all version parts are within acceptable range.
        if any(part > self.MAX_VERSION for part in self.parts):
            raise ValueError(f"Version components must not exceed {self.MAX_VERSION}")

    def get_schema_version(self) -> str:
        """Get the three-part schema version, including collection name if present."""
        schema_version = '.'.join(str(p) for p in self.parts[:3])
        if self.collection_name:
            return f"{self.collection_name}.{schema_version}"
        return schema_version

    def get_enumerator_version(self) -> int:
        """Get the enumerator version."""
        return self.parts[3]

    def get_full_version(self) -> str:
        """Get the full version string including collection name if present."""
        if self.collection_name:
            return f"{self.collection_name}.{self.version}"
        return self.version

    def __lt__(self, other: 'VersionNumber') -> bool:
        """Compare if this version is less than another version.
        
        Comparison is based on version numbers only, ignoring collection names.
        """
        if not isinstance(other, VersionNumber):
            other = VersionNumber(other)
        return self.parts < other.parts

    def __gt__(self, other: 'VersionNumber') -> bool:
        """Compare if this version is greater than another version.
        
        Comparison is based on version numbers only, ignoring collection names.
        """
        if not isinstance(other, VersionNumber):
            other = VersionNumber(other)
        return self.parts > other.parts

    def __eq__(self, other: 'VersionNumber') -> bool:
        """Compare if this version equals another version.
        
        Comparison is based on version numbers only, ignoring collection names.
        """
        if not isinstance(other, VersionNumber):
            other = VersionNumber(other)
        return self.parts == other.parts

    def __le__(self, other: 'VersionNumber') -> bool:
        """Compare if this version is less than or equal to another version.
        
        Comparison is based on version numbers only, ignoring collection names.
        """
        return self < other or self == other

    def __ge__(self, other: 'VersionNumber') -> bool:
        """Compare if this version is greater than or equal to another version.
        
        Comparison is based on version numbers only, ignoring collection names.
        """
        return self > other or self == other

    def __str__(self) -> str:
        """Return the version string."""
        return self.get_full_version() 