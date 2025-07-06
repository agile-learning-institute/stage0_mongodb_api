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
            
            # For enumerators, we're dealing with a list of versioned enumerations
            # Compare the content directly since it's a list structure
            if original_doc != saved_doc:
                event.data = {
                    "original": original_doc,
                    "saved": saved_doc,
                    "changed": True
                }
            else:
                event.data = {
                    "changed": False
                }
            
            event.record_success()
        except ConfiguratorException as e:
            event.append_events([e.event])
            event.record_failure("error saving document")
        except Exception as e:
            event.append_events([ConfiguratorEvent(event_id="ENU-04", event_type="SAVE_ENUMERATORS", event_data={"error": str(e)})])
            event.record_failure("unexpected error saving document")
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
        
    