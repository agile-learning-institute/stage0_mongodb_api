from configurator.utils.configurator_exception import ConfiguratorEvent, ConfiguratorException
from configurator.utils.file_io import FileIO

class Enumerators:
    """ A list of versioned Enumerations"""
    def __init__(self, data: dict):
        if data is None:
            self.dict = FileIO.get_file(self.config.TEST_DATA_FOLDER, "enumerators.json")
        else:
            self.dict = data
        self.versions = []
        for enumerators in self.dict:
            self.versions.append = Enumerators(enumerators)
                
    def save(self):
        FileIO.put_file(self.config.TEST_DATA_FOLDER, "enumerators.json", self.dict)
        return self.dict
    
    def version(self, version: int):
        return self.versions[version]
    
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
        
    