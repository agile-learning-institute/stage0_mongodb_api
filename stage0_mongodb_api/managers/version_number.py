import re
from typing import List

class VersionNumber:
    """Class for handling semantic version numbers with schema version.
    see /docs/versioning.md for more information on versioning.
    
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