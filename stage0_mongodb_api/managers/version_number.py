import re
from typing import List

class VersionNumber:
    """Class for handling four-part version numbers.
    
    Version format: major.minor.patch.enumerator
    Example: 1.0.0.1
    """
    
    MAX_VERSION = 999
    VERSION_PATTERN = r'^\d+\.\d+\.\d+\.\d+$'
    
    def __init__(self, version: str):
        """Initialize a VersionNumber instance.
        
        Args:
            version: Version string in format major.minor.patch.enumerator
            
        Raises:
            ValueError: If version format is invalid or numbers exceed MAX_VERSION
        """
        if not version:
            raise ValueError("Version string cannot be empty")
            
        if not re.match(self.VERSION_PATTERN, version):
            raise ValueError(f"Invalid version format: {version}")
            
        self.version = version
        self.parts = [int(part) for part in version.split('.')]

        # Validate that all version parts are within acceptable range.
        if any(part > self.MAX_VERSION for part in self.parts):
            raise ValueError(f"Version components must not exceed {self.MAX_VERSION}")

    def get_schema_version(self) -> str:
        """Get the three-part schema version."""
        return '.'.join(str(p) for p in self.parts[:3])

    def get_enumerator_version(self) -> int:
        """Get the enumerator version."""
        return self.parts[3]

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

    def __str__(self) -> str:
        """Return the version string."""
        return self.version 