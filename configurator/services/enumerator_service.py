from configurator.utils.configurator_exception import ConfiguratorEvent, ConfiguratorException
from configurator.utils.file_io import FileIO, File
from configurator.utils.config import Config
import os

class Enumerators:
    """A list of versioned Enumerations - loads enumerations on demand"""
    def __init__(self):
        self.config = Config.get_instance()
        files = FileIO.get_documents(self.config.ENUMERATOR_FOLDER)
        self.enumerations = [Enumerations(file_name=file.file_name) for file in files]

    def lock_all(self):
        """Lock all enumerations"""
        for enumeration in self.enumerations:
            enumeration._locked = True
            enumeration.save()
        return self


    def getVersion(self, version_number: int):
        """Get a specific version of enumerations"""
        for enumeration in self.enumerations:
            if enumeration.version == version_number:
                return enumeration
        
        event = ConfiguratorEvent("ENU-01", "GET_VERSION")
        event.record_failure(f"Version {version_number} not found")
        raise ConfiguratorException(f"Version {version_number} not found", event)

    def version(self, version_number: int):
        """Alias for getVersion for backward compatibility"""
        return self.getVersion(version_number)

class Enumerations:
    """A versioned collection of enumerations with file operations"""
    def __init__(self, data: dict = None, file_name: str = None):
        self.config = Config.get_instance()
        self._locked = False
        self.file_name = file_name

        if data:
            self._load_from_document(data)
        else:
            document = FileIO.get_document(self.config.ENUMERATOR_FOLDER, file_name)
            self._load_from_document(document)

    def _load_from_document(self, data: dict):
        """Load enumerations data from document"""
        self.name = data.get("name", "Enumerations")
        self.status = data.get("status", "Active")
        self.version = data.get("version", 0)
        self.enumerators = data.get("enumerators", {})
        self._locked = data.get("_locked", False)

    def get_enum_values(self, enum_name: str):
        """Get the values for a specific enum"""
        if enum_name not in self.enumerators:
            event = ConfiguratorEvent("ENU-02", "GET_ENUM_VALUES", {"error": f"Enum '{enum_name}' not found"})
            raise ConfiguratorException(f"Enum '{enum_name}' not found", event)
        return list(self.enumerators[enum_name].keys())

    def to_dict(self):
        """Return the enumerations data"""
        return {
            "name": self.name,
            "status": self.status,
            "version": self.version,
            "enumerators": self.enumerators,
            "_locked": self._locked
        }

    def save(self):
        """Save the enumerations to its file and return the File object."""
        try:
            file_obj = FileIO.put_document(self.config.ENUMERATOR_FOLDER, self.file_name, self.to_dict())
            return file_obj
        except ConfiguratorException as e:
            event = ConfiguratorEvent("ENU-03", "PUT_ENUMERATIONS")
            event.append_events([e.event])
            event.record_failure(f"Failed to save enumerations {self.file_name}: {str(e)}")
            raise ConfiguratorException(f"Failed to save enumerations {self.file_name}: {str(e)}", event)
        except Exception as e:
            event = ConfiguratorEvent("ENU-04", "PUT_ENUMERATIONS")
            event.record_failure(f"Failed to save enumerations {self.file_name}: {str(e)}")
            raise ConfiguratorException(f"Failed to save enumerations {self.file_name}: {str(e)}", event)
        
    