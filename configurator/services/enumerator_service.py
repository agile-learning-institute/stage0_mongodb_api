from configurator.utils.configurator_exception import ConfiguratorEvent, ConfiguratorException
from configurator.utils.file_io import FileIO
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
                
    def save(self) -> list[ConfiguratorEvent]:
        event = ConfiguratorEvent(event_id="ENU-03", event_type="SAVE_ENUMERATORS")
        try:
            # Get original content before saving
            original_doc = FileIO.get_document(self.config.TEST_DATA_FOLDER, "enumerators.json")
            
            # Save the cleaned content
            FileIO.put_document(self.config.TEST_DATA_FOLDER, "enumerators.json", self.dict)
            
            # Re-read the saved content
            saved_doc = FileIO.get_document(self.config.TEST_DATA_FOLDER, "enumerators.json")
            
            # Compare and set event data
            original_keys = set(original_doc.keys())
            saved_keys = set(saved_doc.keys())
            
            added = saved_keys - original_keys
            removed = original_keys - saved_keys
            
            event.data = {
                "added": {k: saved_doc[k] for k in added},
                "removed": {k: original_doc[k] for k in removed}
            }
            
            event.record_success()
        except ConfiguratorException as e:
            event.append_events([e.event])
            event.record_failure(message="error saving document")
        except Exception as e:
            event.append_events(ConfiguratorEvent(event_id="ENU-04", event_type="SAVE_ENUMERATORS", data=e))
            event.record_failure(message="unexpected error saving document")
        return [event]
    
    def version(self, version: int):
        return self.versions[version]
    
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
            return self.enumerators[enum_name].keys()
        except Exception as e:
            event = ConfiguratorEvent(event_id="ENU-02", event_type="INVALID_ENUMERATOR_NAME", event_data=e)
            raise ConfiguratorException("Invalid enumerator name", event)
        
    