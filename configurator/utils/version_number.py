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
            data = {"message": f"Invalid version format {version}"}
            event = ConfiguratorEvent(event_id="VER-01", event_type="VALIDATION", event_data=data)
            raise ConfiguratorException("Invalid version format", event, data)
                
        self.parts[0] = parts[0]
        if not parts[1:].isdigit():
            data = {"message": f"Invalid version format {version}"}
            event = ConfiguratorEvent(event_id="VER-01", event_type="VALIDATION", event_data=data)
            raise ConfiguratorException("Invalid version format", event, data)
        self.parts[1:] = [int(part) for part in parts[1:]]

    def get_schema_filename(self) -> str:
        """Get the schema file name - without enumerator version."""
        return '.'.join(self.parts[0:4],".yaml")

    def get_enumerator_version(self) -> int:
        """Get the enumerator version."""
        return int(self.parts[5])

    def get_version_str(self) -> str:
        """Get the four part version without collection name."""
        return '.'.join(self.parts[1:5])

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