from configurator.utils.configurator_exception import ConfiguratorEvent, ConfiguratorException
from configurator.utils.file_io import FileIO, File
from configurator.utils.config import Config
import os

class Enumerators:
    """ A list of versioned Enumerations"""
    def __init__(self, data: dict):
        self.config = Config.get_instance()
        
        if data is None:
            loaded_data = FileIO.get_document(self.config.TEST_DATA_FOLDER, "enumerators.json")
            # Handle both list and dict formats
            if isinstance(loaded_data, dict):
                self.dict = loaded_data.get("enumerators", [])
            else:
                self.dict = loaded_data
        else:
            # Handle both list and dict formats
            if isinstance(data, dict):
                self.dict = data.get("enumerators", [])
            else:
                self.dict = data
                
        self.versions = []
        for enumerators in self.dict:
            self.versions.append(Enumerations(enumerators))
            
    def version(self, version_number: int):
        """Get a specific version of enumerations"""
        for version in self.versions:
            if version.version == version_number:
                return version
        raise ConfiguratorException(f"Version {version_number} not found")
        
    def save(self):
        """Save the enumerators and return self"""
        try:
            # Save the cleaned content
            FileIO.put_document(self.config.TEST_DATA_FOLDER, "enumerators.json", self.to_dict())
            return self
        except Exception as e:
            event = ConfiguratorEvent("ENU-02", "PUT_ENUMERATORS")
            event.record_failure(f"Failed to save enumerators: {str(e)}")
            raise ConfiguratorException(f"Failed to save enumerators: {str(e)}", event)
            
    def to_dict(self):
        """Return the enumerators data"""
        return self.dict


class Enumerations:
    """ A versioned collection of enumerations"""
    def __init__(self, data: dict):
        self.config = Config.get_instance()
        self._locked = False  # Default to unlocked
        
        if data is None:
            event = ConfiguratorEvent("ENU-01", "INIT_ENUMERATIONS", {"error": "Enumerations data cannot be None"})
            raise ConfiguratorException("Enumerations data cannot be None", event)
        if not isinstance(data, dict):
            event = ConfiguratorEvent("ENU-01", "INIT_ENUMERATIONS", {"error": "Enumerations data must be a dictionary"})
            raise ConfiguratorException("Enumerations data must be a dictionary", event)
            
        self.name = data.get("name", "Enumerations")
        self.status = data.get("status", "Active")
        self.version = data.get("version", 0)
        self.enumerators = data.get("enumerators", {})
        # Extract _locked from document if present
        self._locked = data.get("_locked", False)
        
    def get_enum_values(self, enum_name: str):
        """Get the values for a specific enum"""
        if self.enumerators is None:
            event = ConfiguratorEvent("ENU-01", "GET_ENUM_VALUES", {"error": "Enumerators is None"})
            raise ConfiguratorException("Enumerators is None", event)
        if enum_name not in self.enumerators:
            event = ConfiguratorEvent("ENU-01", "GET_ENUM_VALUES", {"error": f"Enum '{enum_name}' not found"})
            raise ConfiguratorException(f"Enum '{enum_name}' not found", event)
        # Return the keys (values) as a list, not the full object
        return list(self.enumerators[enum_name].keys())
        
    def to_dict(self):
        """Return the enumerations data"""
        return {
            "name": self.name,
            "status": self.status,
            "version": self.version,
            "enumerators": self.enumerators,
            "_locked": self._locked  # Always include _locked
        }
        
    