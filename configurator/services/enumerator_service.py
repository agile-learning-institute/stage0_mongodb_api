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
            FileIO.put_document(self.config.TEST_DATA_FOLDER, "enumerators.json", self.dict)
            event.data = self.dict
            event.record_success()
        except ConfiguratorException as e:
            event.append_events(e.event.to_dict())
            event.record_failure(message="error saving document")
        except Exception as e:
            event.append_events(ConfiguratorEvent(event_id="ENU-04", event_type="SAVE_ENUMERATORS", data=e))
            event.record_failure(message="unexpected error saving document")
        return [event]
    
    def version(self, version: int):
        return self.versions[version]
    
    def to_dict(self):
        return self.dict
    
    def clean(self) -> list[ConfiguratorEvent]:
        """Clean this enumerators by saving it (which normalizes the content)"""
        return self.save()

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
        
    