from configurator.services.dictionary_services import Dictionary
from configurator.utils.config import Config
from configurator.utils.configurator_exception import ConfiguratorEvent, ConfiguratorException
from configurator.services.enumerator_service import Enumerators
from configurator.utils.file_io import FileIO
from configurator.utils.mongo_io import MongoIO
from configurator.utils.version_manager import VersionManager
from configurator.utils.version_number import VersionNumber
import os

class Configuration:
    def __init__(self, file_name: str, document: dict  = None):
        self.config = Config.get_instance()
        self.file_name = file_name
        if not document:
            document = FileIO.get_document(self.config.CONFIGURATIONS_FOLDER, file_name)
        self.name = document["name"]
        self.title = document["title"]
        self.description = document["description"]
        self.versions = []
        for version in document["versions"]:
            self.versions.append(Version(self.name, version))

    def to_dict(self):
        return {
            "name": self.name,
            "title": self.title,
            "description": self.description,
            "versions": [v.to_dict() for v in self.versions],
        }

    def save(self) -> list[ConfiguratorEvent]:
        event = ConfiguratorEvent(event_id="CFG-03", event_type="SAVE_CONFIGURATION")
        try:
            # Get original content before saving
            original_doc = FileIO.get_document(self.config.CONFIGURATIONS_FOLDER, self.file_name)
            
            # Save the cleaned content
            FileIO.save_document(self.config.CONFIGURATIONS_FOLDER, self.file_name, self.to_dict())
            
            # Re-read the saved content
            saved_doc = FileIO.get_document(self.config.CONFIGURATIONS_FOLDER, self.file_name)
            
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
            event.record_failure("error saving document")
        except Exception as e:
            event.append_events([ConfiguratorEvent(event_id="CFG-04", event_type="SAVE_CONFIGURATION", event_data={"error": str(e)})])
            event.record_failure("unexpected error saving document")
        return [event]
    
    def delete(self):
        FileIO.delete_document(self.config.CONFIGURATIONS_FOLDER, self.file_name)
        
    def lock_unlock(self):
        FileIO.lock_unlock(self.config.CONFIGURATIONS_FOLDER, self.file_name)
        
    def process(self) -> ConfiguratorEvent:
        try:
            event = ConfiguratorEvent(event_id="CFG-00", event_type="PROCESS")
            mongo_io = MongoIO(self.config.MONGO_CONNECTION_STRING, self.config.MONGO_DB_NAME)
            for version in self.versions:
                current_version = VersionManager.get_current_version(mongo_io, self.name)
                if version.collection_version <= current_version:
                    sub_event = ConfiguratorEvent(event_id="PRO-00", event_type="SKIP_VERSION", 
                        event_data={"version": version.to_dict(), "current_version": current_version.to_dict()})
                    sub_event.record_success()
                    event.append_events([sub_event])
                    continue
                event.append_events(version.process(mongo_io))
            event.record_success()
            mongo_io.disconnect()
            return event
        except ConfiguratorException as e:
            event.append_events([e.event])
            event.record_failure("error processing configuration")
            mongo_io.disconnect()
            return event
        except Exception as e:
            event.record_failure("unexpected error processing configuration", {"error": str(e)})
            mongo_io.disconnect()
            return event
    
    def get_json_schema(self, version: str) -> dict:
        version_obj = next((v for v in self.versions if v.version_str == version), None)
        if version_obj is None:
            data = {"message": f"Version {version} not found"}
            event = ConfiguratorEvent(event_id="CFG-01", event_type="RENDER", event_data=data)
            raise ConfiguratorException("Version not found", event, data)
        return version_obj.get_json_schema()
    
    def get_bson_schema(self, version: str):
        version_obj = next((v for v in self.versions if v.version_str == version), None)
        if version_obj is None:
            data = {"message": f"Version {version} not found"}
            event = ConfiguratorEvent(event_id="CFG-02", event_type="RENDER", event_data=data)
            raise ConfiguratorException("Version not found", event, data)
        return version_obj.get_bson_schema()

class Version:
    def __init__(self, collection_name: str, version: dict):
        self.collection_name = collection_name
        self.collection_version = VersionNumber(f"{collection_name}.{version["version"]}")
        self.version_str = self.collection_version.get_version_str()
        self.drop_indexes = version["drop_indexes"]
        self.add_indexes = version["add_indexes"]
        self.migrations = version["migrations"]
        self.test_data = version["test_data"]
        
    def __eq__(self, other):
        if not isinstance(other, Version):
            return False
        return self.collection_version == other.collection_version
            
    def version_str(self):
        return self.collection_version.get_version_str()
    
    def enumerator(self) -> int:
        return self.parts[4]
    
    def to_dict(self):
        return {
            "version": self.collection_version.get_version_str(),
            "drop_indexes": self.drop_indexes,
            "add_indexes": self.add_indexes,
            "migrations": self.migrations,
            "test_data": self.test_data,
        }
    
    def get_json_schema(self):
        enumerators = Enumerators().enumerations.version(self.enumerator())
        dictionary = Dictionary(self.config.DICTIONARIES_FOLDER, self.collection_version.get_schema_filename())
        return dictionary.get_json_schema(enumerators)
    
    def get_bson_schema(self): 
        enumerators = Enumerators().enumerations.version(self.enumerator())
        dictionary = Dictionary(self.config.DICTIONARIES_FOLDER, self.collection_version.get_schema_filename())
        return dictionary.get_bson_schema(enumerators)
    
    def process(self, mongo_io: MongoIO):
        try:
            event = ConfiguratorEvent(event_id=f"{self.collection_name}.{self.version}", event_type="PROCESS")

            sub_event = ConfiguratorEvent(event_id="PRO-01", event_type="REMOVE_SCHEMA_VALIDATION")
            event.append_events([sub_event])
            sub_event.append_events(mongo_io.remove_schema_validation(self.collection_name))
            sub_event.record_success()

            sub_event = ConfiguratorEvent(event_id="PRO-02", event_type="REMOVE_INDEXES")
            event.append_events([sub_event])
            for index in self.drop_indexes:
                sub_event.append_events(mongo_io.remove_index(self.collection_name, index))
            sub_event.record_success()

            sub_event = ConfiguratorEvent(event_id="PRO-03", event_type="EXECUTE_MIGRATIONS")
            event.append_events([sub_event])
            for migration in self.migrations:
                sub_event.append_events(mongo_io.execute_migration(self.collection_name, migration))
            sub_event.record_success()
                
            sub_event = ConfiguratorEvent(event_id="PRO-04", event_type="ADD_INDEXES")
            event.append_events([sub_event])
            for index in self.add_indexes:
                sub_event.append_events(mongo_io.add_index(self.collection_name, index))
            sub_event.record_success()

            sub_event = ConfiguratorEvent(event_id="PRO-05", event_type="APPLY_SCHEMA_VALIDATION")
            event.append_events([sub_event])
            event.append_events(mongo_io.apply_schema_validation(self.collection_name))
            sub_event.record_success()

            sub_event = ConfiguratorEvent(event_id="PRO-06", event_type="LOAD_TEST_DATA")
            event.append_events([sub_event])
            event.append_events(mongo_io.load_json_data(self.collection_name, self.test_data))
            sub_event.record_success()

            sub_event = ConfiguratorEvent(event_id="PRO-07", event_type="UPDATE_VERSION")
            event.append_events([sub_event])
            event.append_events(mongo_io.upsert(self.config.VERSIONS_COLLECTION, {"name": self.collection_name}, {"$set": {"version": self.version}}))
            sub_event.record_success()

            return event
        
        except ConfiguratorException as e:
            event.append_events([e.event])
            event.record_failure("error processing version")
            return event
        except Exception as e:
            event.append_events([ConfiguratorEvent(event_id="CFG-04", event_type="SAVE_CONFIGURATION", event_data={"error": str(e)})])
            event.record_failure("unexpected error processing version")
            return event