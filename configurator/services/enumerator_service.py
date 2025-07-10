from configurator.utils.configurator_exception import ConfiguratorEvent, ConfiguratorException
from configurator.utils.file_io import FileIO, File
from configurator.utils.config import Config
import os

class Enumerators:
    """ A list of versioned Enumerations"""
    def __init__(self, data: dict):
        self.config = Config.get_instance()
        if data is None:
            self.dict = FileIO.get_document(self.config.TEST_DATA_FOLDER, "enumerators.json")
        else:
            self.dict = data
        self.versions = []
        for enumerators in self.dict:
            self.versions.append(Enumerations(enumerators))
                
    def save(self) -> File:
        """Save the enumerators and return the File object."""
        try:
            # Save the cleaned content
            return FileIO.put_document(self.config.TEST_DATA_FOLDER, "enumerators.json", self.dict)
        except Exception as e:
            event = ConfiguratorEvent("ENU-03", "SAVE_ENUMERATORS", {"error": str(e)})
            raise ConfiguratorException(f"Failed to save enumerators: {str(e)}", event)
    
    def version(self, version: int):
        return self.versions[version]
    
    def get_enum_values(self, enum_name: str):
        """Get enum values from the active version (version 0)."""
        return self.versions[0].get_enum_values(enum_name)
    
    def to_dict(self):
        return self.dict

class Enumerations:
    def __init__(self, data: dict):
        try:
            self.name = data.get("name")
            self.status = data.get("status")
            self.version = data.get("version")
            self.enumerators = data.get("enumerators")
        except Exception as e:
            event = ConfiguratorEvent(event_id="ENU-01", event_type="INVALID_ENUMERATOR_DATA", event_data=e)
            raise ConfiguratorException("Invalid enumerator data", event)
        
    def get_enum_values(self, enum_name: str):
        try:
            return list(self.enumerators[enum_name].keys())
        except Exception as e:
            event = ConfiguratorEvent(event_id="ENU-02", event_type="INVALID_ENUMERATOR_NAME", event_data=e)
            raise ConfiguratorException("Invalid enumerator name", event)
        
    