from configurator.utils.configurator_exception import ConfiguratorEvent, ConfiguratorException
from configurator.utils.file_io import FileIO, File
from configurator.utils.config import Config
from configurator.utils.mongo_io import MongoIO
import os

class Enumerators:
    """A list of versioned Enumerations - loads enumerations on demand"""
    def __init__(self):
        self.config = Config.get_instance()
        files = FileIO.get_documents(self.config.ENUMERATOR_FOLDER)
        self.enumerations = [Enumerations(file_name=file.file_name) for file in files]

    def lock_all(self):
        """Lock all enumerations and return a ConfiguratorEvent with sub-events for each file."""
        event = ConfiguratorEvent("ENU-04", "LOCK_ENUMERATIONS")
        success_count = 0
        
        for enumeration in self.enumerations:
            sub_event = ConfiguratorEvent(f"ENU-{enumeration.file_name}", "LOCK_ENUMERATION")
            try:
                enumeration._locked = True
                enumeration.save()
                sub_event.record_success()
                success_count += 1
            except ConfiguratorException as ce:
                sub_event.record_failure(f"ConfiguratorException locking enumeration {enumeration.file_name}")
                event.append_events([ce.event])
            except Exception as e:
                sub_event.record_failure(f"Failed to lock enumeration {enumeration.file_name}: {str(e)}")
            event.append_events([sub_event])
        
        # Record overall success/failure based on whether all enumerations were locked
        if success_count == len(self.enumerations):
            event.record_success()
        else:
            event.record_failure(f"Failed to lock {len(self.enumerations) - success_count} out of {len(self.enumerations)} enumerations")
        
        return event

    def upsert_all_to_database(self, mongo_io: MongoIO) -> ConfiguratorEvent:
        """Upsert all enumerators to the database."""
        event = ConfiguratorEvent("ENU-05", "UPSERT_ENUMERATORS_TO_DATABASE")
        
        for enumeration in self.enumerations:
            sub_event = ConfiguratorEvent(f"ENU-UPSERT-{enumeration.file_name}", "UPSERT_ENUMERATION")
            try:
                # Use the enumeration's upsert method
                result = enumeration.upsert(mongo_io)
                
                sub_event.data = {
                    "version": enumeration.version,
                    "enumerators_count": len(enumeration.enumerators),
                    "result": result
                }
                sub_event.record_success()
            except ConfiguratorException as ce:
                sub_event.record_failure(f"ConfiguratorException upserting enumeration {enumeration.file_name}")
                event.append_events([ce.event])
                # Re-raise to halt processing
                raise
            except Exception as e:
                sub_event.record_failure(f"Failed to upsert enumeration {enumeration.file_name}: {str(e)}")
                # Re-raise to halt processing
                raise ConfiguratorException(f"Failed to upsert enumeration {enumeration.file_name}: {str(e)}", sub_event)
            event.append_events([sub_event])
        
        event.record_success()
        return event

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

        try:
            if data:
                self._load_from_document(data)
            else:
                document = FileIO.get_document(self.config.ENUMERATOR_FOLDER, file_name)
                self._load_from_document(document)
        except ConfiguratorException as e:
            # Re-raise with additional context about the enumerations file
            event = ConfiguratorEvent(event_id=f"ENU-CONSTRUCTOR-{file_name}", event_type="ENUMERATIONS_CONSTRUCTOR")
            event.record_failure(f"Failed to construct enumerations from {file_name}")
            event.append_events([e.event])
            raise ConfiguratorException(f"Failed to construct enumerations from {file_name}: {str(e)}", event)

    def _load_from_document(self, data: dict):
        """Load enumerations data from document"""
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
        result = {
            "version": self.version,
            "enumerators": self.enumerators,
            "_locked": self._locked
        }
        # Only include file_name if it's not None
        if self.file_name is not None:
            result["file_name"] = self.file_name
        return result

    def upsert(self, mongo_io: MongoIO):
        """Upsert this enumeration to the database using to_dict() to create the document."""
        # Create document for database using to_dict()
        doc = self.to_dict()
        
        # Upsert to database
        return mongo_io.upsert(
            self.config.ENUMERATORS_COLLECTION_NAME,
            {"version": self.version},
            doc
        )

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
        
    