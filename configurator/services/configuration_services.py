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
    def __init__(self, file_name: str, document: dict = None):
        self.config = Config.get_instance()
        self.file_name = file_name
        if not document:
            document = FileIO.get_document(self.config.CONFIGURATION_FOLDER, file_name)
        self.name = document["name"]
        self.title = document.get("title", "")
        self.description = document["description"]
        self.versions = [Version(self.name, v, self.config) for v in document["versions"]]

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
            original_doc = FileIO.get_document(self.config.CONFIGURATION_FOLDER, self.file_name)
            
            # Save the cleaned content
            FileIO.save_document(self.config.CONFIGURATION_FOLDER, self.file_name, self.to_dict())
            
            # Re-read the saved content
            saved_doc = FileIO.get_document(self.config.CONFIGURATION_FOLDER, self.file_name)
            
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
        FileIO.delete_document(self.config.CONFIGURATION_FOLDER, self.file_name)
        
    def lock_unlock(self):
        FileIO.lock_unlock(self.config.CONFIGURATION_FOLDER, self.file_name)
        
    def process(self) -> ConfiguratorEvent:
        event = ConfiguratorEvent(event_id="CFG-00", event_type="PROCESS")
        mongo_io = MongoIO(self.config.MONGO_CONNECTION_STRING, self.config.MONGO_DB_NAME)
        try:
            for version in self.versions:
                current_version = VersionManager.get_current_version(mongo_io, self.name)
                if version.collection_version <= current_version:
                    sub_event = ConfiguratorEvent(
                        event_id="PRO-00",
                        event_type="SKIP_VERSION",
                        event_data={
                            "version": version.to_dict(),
                            "current_version": current_version.get_version_str(),
                        },
                    )
                    sub_event.record_success()
                    event.append_events([sub_event])
                    continue
                event.append_events([version.process(mongo_io)])
            
            # Load enumerators into database
            sub_event = ConfiguratorEvent(event_id="PRO-08", event_type="LOAD_ENUMERATORS")
            try:
                enumerators = Enumerators(None)
                for enum_doc in enumerators.dict:
                    # Upsert based on version field
                    mongo_io.upsert(
                        "enumerators",
                        {"version": enum_doc["version"]},
                        enum_doc
                    )
                sub_event.record_success()
            except Exception as e:
                sub_event.record_failure({"error": str(e)})
            event.append_events([sub_event])
            
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
    def __init__(self, collection_name: str, version: dict, config):
        self.config = config
        self.collection_name = collection_name
        # Always construct VersionNumber with 4-part version string
        self.collection_version = VersionNumber(f"{collection_name}.{version['version']}")
        self.version_str = self.collection_version.get_version_str()
        self.drop_indexes = version.get("drop_indexes", [])
        self.add_indexes = version.get("add_indexes", [])
        self.migrations = version.get("migrations", [])
        self.test_data = version.get("test_data", None)

    def to_dict(self):
        return {
            "version": self.collection_version.get_version_str(),
            "drop_indexes": self.drop_indexes,
            "add_indexes": self.add_indexes,
            "migrations": self.migrations,
            "test_data": self.test_data,
        }

    def get_json_schema(self):
        enumerators = Enumerators(None).version(self.collection_version.get_enumerator_version())
        # Load dictionary data first
        dictionary_filename = self.collection_version.get_schema_filename()
        dictionary_data = FileIO.get_document(self.config.DICTIONARY_FOLDER, dictionary_filename)
        dictionary = Dictionary(dictionary_filename, dictionary_data)
        return dictionary.get_json_schema(enumerators)

    def get_bson_schema(self):
        enumerators = Enumerators(None).version(self.collection_version.get_enumerator_version())
        # Load dictionary data first
        dictionary_filename = self.collection_version.get_schema_filename()
        dictionary_data = FileIO.get_document(self.config.DICTIONARY_FOLDER, dictionary_filename)
        dictionary = Dictionary(dictionary_filename, dictionary_data)
        return dictionary.get_bson_schema(enumerators)

    def process(self, mongo_io: MongoIO):
        event = ConfiguratorEvent(event_id=f"{self.collection_name}.{self.version_str}", event_type="PROCESS")
        try:
            # Remove schema validation
            sub_event = ConfiguratorEvent(event_id="PRO-01", event_type="REMOVE_SCHEMA_VALIDATION")
            sub_event.append_events(mongo_io.remove_schema_validation(self.collection_name))
            event.append_events([sub_event])

            # Remove indexes
            sub_event = ConfiguratorEvent(event_id="PRO-02", event_type="REMOVE_INDEXES")
            for index in self.drop_indexes:
                sub_event.append_events(mongo_io.remove_index(self.collection_name, index))
            event.append_events([sub_event])

            # Execute migrations
            sub_event = ConfiguratorEvent(event_id="PRO-03", event_type="EXECUTE_MIGRATIONS")
            for filename in self.migrations:
                migration_file = os.path.join(self.config.INPUT_FOLDER, self.config.MIGRATIONS_FOLDER, filename)
                sub_event.append_events(mongo_io.execute_migration_from_file(self.collection_name, migration_file))
            event.append_events([sub_event])

            # Add indexes
            sub_event = ConfiguratorEvent(event_id="PRO-04", event_type="ADD_INDEXES")
            for index in self.add_indexes:
                sub_event.append_events(mongo_io.add_index(self.collection_name, index))
            event.append_events([sub_event])

            # Apply schema validation
            sub_event = ConfiguratorEvent(event_id="PRO-05", event_type="APPLY_SCHEMA_VALIDATION")
            sub_event.append_events(mongo_io.apply_schema_validation(self.collection_name))
            event.append_events([sub_event])

            # Load test data
            sub_event = ConfiguratorEvent(event_id="PRO-06", event_type="LOAD_TEST_DATA")
            if self.test_data:
                test_data_path = os.path.join(self.config.INPUT_FOLDER, self.config.TEST_DATA_FOLDER, self.test_data)
                sub_event.append_events(mongo_io.load_json_data(self.collection_name, test_data_path))
            else:
                sub_event.record_success()
            event.append_events([sub_event])

            # Update version
            sub_event = ConfiguratorEvent(event_id="PRO-07", event_type="UPDATE_VERSION")
            try:
                mongo_io.upsert(
                    self.config.VERSION_COLLECTION_NAME,
                    {"collection_name": self.collection_name},
                    {"collection_name": self.collection_name, "current_version": self.collection_version.version}
                )
                sub_event.record_success()
            except Exception as e:
                sub_event.record_failure({"error": str(e)})
            event.append_events([sub_event])

            event.record_success()
            return event
        
        except ConfiguratorException as e:
            event.append_events([e.event])
            event.record_failure("error processing version")
            return event
        except Exception as e:
            event.record_failure("unexpected error processing version", {"error": str(e)})
            return event