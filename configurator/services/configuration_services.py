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
            # Add configuration context to main event
            event.data = {
                "configuration_file": self.file_name,
                "configuration_name": self.name,
                "configuration_title": self.title,
                "version_count": len(self.versions)
            }
            
            for version in self.versions:
                current_version = VersionManager.get_current_version(mongo_io, self.name)
                if version.collection_version <= current_version:
                    sub_event = ConfiguratorEvent(
                        event_id="PRO-00",
                        event_type="SKIP_VERSION",
                        event_data={
                            "configuration_file": self.file_name,
                            "version": version.to_dict(),
                            "current_version": current_version.get_version_str(),
                            "skip_reason": "version_already_processed"
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
                sub_event.data = {
                    "configuration_file": self.file_name,
                    "enumerator_count": len(enumerators.dict),
                    "enumerator_versions": [enum_doc["version"] for enum_doc in enumerators.dict]
                }
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
        # Get the correct enumerations version for this configuration version
        enumerations = Enumerators(None).version(version_obj.collection_version.get_enumerator_version())
        return version_obj.get_json_schema(enumerations)
    
    def get_bson_schema_for_version(self, version: str):
        version_obj = next((v for v in self.versions if v.version_str == version), None)
        if version_obj is None:
            data = {"message": f"Version {version} not found"}
            event = ConfiguratorEvent(event_id="CFG-02", event_type="RENDER", event_data=data)
            raise ConfiguratorException("Version not found", event, data)
        # Get the correct enumerations version for this configuration version
        enumerations = Enumerators(None).version(version_obj.collection_version.get_enumerator_version())
        return version_obj.get_bson_schema(enumerations)

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

    def get_json_schema(self, enumerations) -> dict:
        """Get JSON schema for this version with provided enumerations."""
        # Load dictionary data first
        dictionary_filename: str = self.collection_version.get_schema_filename()
        dictionary_data: dict = FileIO.get_document(self.config.DICTIONARY_FOLDER, dictionary_filename)
        dictionary: Dictionary = Dictionary(dictionary_filename, dictionary_data)
        return dictionary.get_json_schema(enumerations)

    def get_bson_schema(self, enumerations) -> dict:
        """Get BSON schema for this version with provided enumerations."""
        # Load dictionary data first
        dictionary_filename: str = self.collection_version.get_schema_filename()
        dictionary_data: dict = FileIO.get_document(self.config.DICTIONARY_FOLDER, dictionary_filename)
        dictionary: Dictionary = Dictionary(dictionary_filename, dictionary_data)
        return dictionary.get_bson_schema(enumerations)

    def process(self, mongo_io: MongoIO) -> ConfiguratorEvent:
        """Process this version with proper event nesting."""
        event = ConfiguratorEvent(event_id=f"{self.collection_name}.{self.version_str}", event_type="PROCESS")
        
        # Add version context to main event
        event.data = {
            "collection_name": self.collection_name,
            "version": self.version_str,
            "drop_indexes_count": len(self.drop_indexes),
            "add_indexes_count": len(self.add_indexes),
            "migrations_count": len(self.migrations),
            "has_test_data": self.test_data is not None,
            "test_data_file": self.test_data
        }
        
        try:
            # Remove schema validation
            sub_event = ConfiguratorEvent(event_id="PRO-01", event_type="REMOVE_SCHEMA_VALIDATION")
            sub_event.data = {
                "collection_name": self.collection_name,
                "version": self.version_str
            }
            sub_event.append_events(mongo_io.remove_schema_validation(self.collection_name))
            sub_event.record_success()
            event.append_events([sub_event])

            # Remove indexes
            sub_event = ConfiguratorEvent(event_id="PRO-02", event_type="REMOVE_INDEXES")
            if self.drop_indexes:
                sub_event.data = {
                    "collection_name": self.collection_name,
                    "version": self.version_str,
                    "indexes_to_drop": self.drop_indexes,
                    "index_count": len(self.drop_indexes)
                }
                for index in self.drop_indexes:
                    sub_event.append_events(mongo_io.remove_index(self.collection_name, index))
                # Check if any child events failed
                if any(child.status == "FAILURE" for child in sub_event.sub_events):
                    sub_event.record_failure("One or more index removal operations failed")
                else:
                    sub_event.record_success()
            else:
                sub_event.data = {
                    "collection_name": self.collection_name,
                    "version": self.version_str,
                    "message": "No indexes to drop"
                }
                sub_event.record_success()
            event.append_events([sub_event])

            # Execute migrations
            sub_event = ConfiguratorEvent(event_id="PRO-03", event_type="EXECUTE_MIGRATIONS")
            if self.migrations:
                sub_event.data = {
                    "collection_name": self.collection_name,
                    "version": self.version_str,
                    "migration_files": self.migrations,
                    "migration_count": len(self.migrations)
                }
                for filename in self.migrations:
                    migration_file = os.path.join(self.config.INPUT_FOLDER, self.config.MIGRATIONS_FOLDER, filename)
                    sub_event.append_events(mongo_io.execute_migration_from_file(self.collection_name, migration_file))
                # Check if any child events failed
                if any(child.status == "FAILURE" for child in sub_event.sub_events):
                    sub_event.record_failure("One or more migration operations failed")
                else:
                    sub_event.record_success()
            else:
                sub_event.data = {
                    "collection_name": self.collection_name,
                    "version": self.version_str,
                    "message": "No migrations to execute"
                }
                sub_event.record_success()
            event.append_events([sub_event])

            # Add indexes
            sub_event = ConfiguratorEvent(event_id="PRO-04", event_type="ADD_INDEXES")
            if self.add_indexes:
                sub_event.data = {
                    "collection_name": self.collection_name,
                    "version": self.version_str,
                    "indexes_to_add": self.add_indexes,
                    "index_count": len(self.add_indexes)
                }
                for index in self.add_indexes:
                    sub_event.append_events(mongo_io.add_index(self.collection_name, index))
                # Check if any child events failed
                if any(child.status == "FAILURE" for child in sub_event.sub_events):
                    sub_event.record_failure("One or more index creation operations failed")
                else:
                    sub_event.record_success()
            else:
                sub_event.data = {
                    "collection_name": self.collection_name,
                    "version": self.version_str,
                    "message": "No indexes to add"
                }
                sub_event.record_success()
            event.append_events([sub_event])

            # Apply schema validation
            sub_event = ConfiguratorEvent(event_id="PRO-05", event_type="APPLY_SCHEMA_VALIDATION")
            try:
                # Get the correct enumerations version for this version
                enumerations = Enumerators(None).version(self.collection_version.get_enumerator_version())
                # Render the BSON schema for this version
                bson_schema: dict = self.get_bson_schema(enumerations)
                
                # Add schema context to event
                sub_event.data = {"collection_name": self.collection_name, "version": self.collection_version.get_version_str()}
                sub_event.append_events(mongo_io.apply_schema_validation(self.collection_name, bson_schema))
                sub_event.record_success()
            except ConfiguratorException as e:
                # Properly nest the exception event
                sub_event.append_events([e.event])
                sub_event.record_failure("error rendering schema")
                event.append_events([sub_event])
                event.record_failure("error processing version")
                return event
            except Exception as e:
                # Handle unexpected exceptions
                sub_event.record_failure("unexpected error rendering schema", {"error": str(e)})
                event.append_events([sub_event])
                event.record_failure("error processing version")
                return event
            event.append_events([sub_event])

            # Load test data
            sub_event = ConfiguratorEvent(event_id="PRO-06", event_type="LOAD_TEST_DATA")
            if self.test_data:
                test_data_path = os.path.join(self.config.INPUT_FOLDER, self.config.TEST_DATA_FOLDER, self.test_data)
                sub_event.data = {
                    "collection_name": self.collection_name,
                    "version": self.version_str,
                    "test_data_file": self.test_data,
                    "test_data_path": test_data_path
                }
                sub_event.append_events(mongo_io.load_json_data(self.collection_name, test_data_path))
                # Check if any child events failed
                if any(child.status == "FAILURE" for child in sub_event.sub_events):
                    sub_event.record_failure("Test data loading operation failed")
                else:
                    sub_event.record_success()
            else:
                sub_event.data = {
                    "collection_name": self.collection_name,
                    "version": self.version_str,
                    "message": "No test data to load"
                }
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
                sub_event.data = {
                    "collection_name": self.collection_name,
                    "new_version": self.collection_version.get_version_str(),
                    "version_number": self.collection_version.version
                }
                sub_event.record_success()
            except Exception as e:
                sub_event.record_failure({"error": str(e)})
            event.append_events([sub_event])

            event.record_success()
            return event
        
        except ConfiguratorException as e:
            # This should not happen since we handle ConfiguratorException above
            event.append_events([e.event])
            event.record_failure("error processing version")
            return event
        except Exception as e:
            event.record_failure("unexpected error processing version", {"error": str(e)})
            return event