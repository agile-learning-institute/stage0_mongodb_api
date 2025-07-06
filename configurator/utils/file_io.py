import json
import os

import yaml

from configurator.utils.config import Config
from configurator.utils.configurator_exception import ConfiguratorEvent, ConfiguratorException
from configurator.utils.file import File

class FileIO:
    def __init__(self):
        pass
    
    def get_documents(self, folder_name: str) -> list[File]:
        config = Config.get_instance()
        folder = os.path.join(config.CONFIG_FOLDER, folder_name)
        files = []
        
        try:
            for file in os.listdir(folder):
                files.append(File(os.path.join(folder, file)))
            return files
        except Exception as e:
            event = ConfiguratorEvent(event_id="FIL-01", event_type="GET_DOCUMENTS", event_data=e)
            raise ConfiguratorException(f"Failed to get documents from {folder}", event)
    
    def get_document(self, folder_name: str, file_name: str) -> dict:
        config = Config.get_instance()
        folder = os.path.join(config.CONFIG_FOLDER, folder_name)
        file = os.path.join(folder, file_name)
        document = {}
        try:
            with open(file, 'r') as f:
                if file.extension == ".yaml":
                    document = yaml.load(f)
                elif file.extension == ".json":
                    document = json.load(f)
                else:
                    event = ConfiguratorEvent(event_id="FIL-02", event_type="UNSUPPORTED_FILE_TYPE", 
                        event_data={"file_name": file.file_name, "extension": file.extension})
                    raise ConfiguratorException(f"Unsupported file type: {file.extension}", event)
            return document
        except Exception as e:
            event = ConfiguratorEvent(event_id="FIL-03", event_type="GET_DOCUMENT", event_data=e)
            raise ConfiguratorException(f"Failed to get document from {file}", event)
    
    def put_document(self, folder_name: str, file_name: str, document: dict) -> File:
        config = Config.get_instance()
        folder = os.path.join(config.CONFIG_FOLDER, folder_name)
        file = os.path.join(folder, file_name)
        try:
            with open(file, 'w') as f:
                if file.extension == ".yaml":
                    yaml.dump(document, f)
                elif file.extension == ".json":
                    json.dump(document, f)
                else:
                    event = ConfiguratorEvent(event_id="FIL-04", event_type="UNSUPPORTED_FILE_TYPE", 
                    event_data={"file_name": file.file_name, "extension": file.extension})
                    raise ConfiguratorException(f"Unsupported file type: {file.extension}", event)
            return File(file)
        except Exception as e:
            event = ConfiguratorEvent(event_id="FIL-05", event_type="PUT_DOCUMENT", event_data=e)
            raise ConfiguratorException(f"Failed to put document to {file}", event)
    
    def delete_document(self, folder_name: str, file_name: str) -> ConfiguratorEvent:
        config = Config.get_instance()
        folder = os.path.join(config.CONFIG_FOLDER, folder_name)
        file = os.path.join(folder, file_name)
        event = ConfiguratorEvent(event_id="FIL-06", event_type="DELETE_DOCUMENT")
        try:
            os.remove(file)
            event.record_success()
            return event
        except Exception as e:
            event.record_failure(e)
            return event
    
    def lock_unlock(self, folder_name: str, file_name: str) -> ConfiguratorEvent:
        config = Config.get_instance()
        folder = os.path.join(config.CONFIG_FOLDER, folder_name)
        file = os.path.join(folder, file_name)
        event = ConfiguratorEvent(event_id="FIL-07", event_type="LOCK_UNLOCK")
        try:
            file_stats = File(file)
            if file_stats.read_only:
                os.chmod(file, 0o666)
            else:
                os.chmod(file, 0o444)
            event.record_success()
            return event
        except Exception as e:
            event.record_failure(e)
            return event

class File:
    def __init__(self, file_name: str):
        # TODO: Get File Properties
        self.file_name = file_name
        self.read_only = False
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.size = 0

    def to_dict(self):
        return {
            "file_name": self.file_name,
            "read_only": self.read_only,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "size": self.size
        }
    