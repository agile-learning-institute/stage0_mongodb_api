import re
from typing import List, Optional

from configurator.utils.configurator_exception import ConfiguratorException, ConfiguratorEvent

class VersionNumber:
    """Class for handling version numbers."""
    
    def __init__(self, version: str):
        """Initialize a VersionNumber instance.
        
        Args:
            version: Version string collection.major.minor.patch.enumerator
            
        """
        self.version = version
        parts = version.split('.')
        if len(parts) != 5:
            event = ConfiguratorEvent(event_id="VER-01", event_type="VALIDATION")
            raise ConfiguratorException(f"Invalid version format {version}", event)
        
        # Initialize parts list
        self.parts = [None] * 5
        self.parts[0] = parts[0]  # Collection name
        
        # Validate that parts 1-4 are digits
        for i, part in enumerate(parts[1:], 1):
            if not part.isdigit():
                event = ConfiguratorEvent(event_id="VER-01", event_type="VALIDATION")
                raise ConfiguratorException(f"Invalid version format {version}", event)
            self.parts[i] = int(part)

    def get_schema_filename(self) -> str:
        """Get the schema file name - without enumerator version."""
        return '.'.join(str(part) for part in self.parts[0:4]) + ".yaml"

    def get_enumerator_version(self) -> int:
        """Get the enumerator version."""
        return self.parts[4]

    def get_version_str(self) -> str:
        """Get the four part version without collection name."""
        return '.'.join(str(part) for part in self.parts[1:5])

    def __lt__(self, other: 'VersionNumber') -> bool:
        if not isinstance(other, VersionNumber):
            other = VersionNumber(other)
        return self.parts[1:] < other.parts[1:]

    def __gt__(self, other: 'VersionNumber') -> bool:
        if not isinstance(other, VersionNumber):
            other = VersionNumber(other)
        return self.parts[1:] > other.parts[1:]

    def __eq__(self, other: 'VersionNumber') -> bool:
        if not isinstance(other, VersionNumber):
            other = VersionNumber(other)
        return self.parts[1:] == other.parts[1:]

    def __str__(self) -> str:
        return self.get_schema_filename() 