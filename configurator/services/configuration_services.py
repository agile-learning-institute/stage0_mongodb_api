from configurator.services.dictionary_services import Dictionary
from configurator.utils.config import Config
from configurator.utils.configurator_exception import ConfiguratorEvent, ConfiguratorException
from configurator.services.enumerator_service import Enumerators
from configurator.utils.file_io import FileIO
from configurator.utils.mongo_io import MongoIO
from configurator.utils.version_number import VersionNumber
import os

class Configuration:
    def __init__(self, file_name: str, document: dict = None):
        self.config = Config.get_instance()
        self.file_name = file_name
        
        try:
            if not document:
                document = FileIO.get_document(self.config.CONFIGURATION_FOLDER, file_name)
            
            self.title = document.get("title", "")
            self.description = document.get("description", "")
            self.versions = [Version(file_name.replace('.yaml', ''), v, self.config) for v in document.get("versions", [])]
            self._locked = document.get("_locked", False)
        except ConfiguratorException as e:
            # Re-raise with additional context about the configuration file
            event = ConfiguratorEvent(event_id=f"CFG-CONSTRUCTOR-{file_name}", event_type="CONFIGURATION_CONSTRUCTOR")
            event.record_failure(f"Failed to construct configuration from {file_name}")
            event.append_events([e.event])
            raise ConfiguratorException(f"Failed to construct configuration from {file_name}: {str(e)}", event)
        except Exception as e:
            # Handle unexpected errors during construction
            event = ConfiguratorEvent(event_id=f"CFG-CONSTRUCTOR-{file_name}", event_type="CONFIGURATION_CONSTRUCTOR")
            event.record_failure(f"Unexpected error constructing configuration from {file_name}: {str(e)}")
            raise ConfiguratorException(f"Unexpected error constructing configuration from {file_name}: {str(e)}", event)

    def to_dict(self):
        return {
            "file_name": self.file_name,
            "title": self.title,
            "description": self.description,
            "versions": [v.to_dict() for v in self.versions],
            "_locked": bool(self._locked),
        }

    def save(self):
        """Save the configuration and return the File object."""
        try:
            file_obj = FileIO.put_document(self.config.CONFIGURATION_FOLDER, self.file_name, self.to_dict())
            return file_obj
        except Exception as e:
            event = ConfiguratorEvent("CFG-ROUTES-06", "PUT_CONFIGURATION")
            event.record_failure(f"Failed to save configuration {self.file_name}: {str(e)}")
            raise ConfiguratorException(f"Failed to save configuration {self.file_name}: {str(e)}", event)
    
    @staticmethod
    def lock_all():
        """Lock all configuration files."""
        config = Config.get_instance()
        files = FileIO.get_documents(config.CONFIGURATION_FOLDER)
        event = ConfiguratorEvent("CFG-07", "LOCK_ALL_CONFIGURATIONS")
        
        for file in files:
            try:
                sub_event = ConfiguratorEvent(f"CFG-{file.file_name}", "LOCK_CONFIGURATION")
                event.append_events([sub_event])
                configuration = Configuration(file.file_name)
                configuration._locked = True
                configuration.save()
                sub_event.record_success()
            except ConfiguratorException as ce:
                sub_event.record_failure(f"ConfiguratorException locking configuration {file.file_name}")
                event.append_events([ce.event])
                event.record_failure(f"ConfiguratorException locking configuration {file.file_name}")
                raise ConfiguratorException(f"ConfiguratorException locking configuration {file.file_name}", event)
            except Exception as e:
                sub_event.record_failure(f"Failed to lock configuration {file.file_name}: {str(e)}")
                event.record_failure(f"Unexpected error locking configuration {file.file_name}")
                raise ConfiguratorException(f"Unexpected error locking configuration {file.file_name}", event)
        
        event.record_success()
        return event

    @staticmethod
    def process_all():
        """Process all configuration files."""
        config = Config.get_instance()
        files = FileIO.get_documents(config.CONFIGURATION_FOLDER)
        event = ConfiguratorEvent("CFG-ROUTES-02", "PROCESS_ALL_CONFIGURATIONS")
        
        for file in files:
            try:
                sub_event = ConfiguratorEvent(f"CFG-{file.file_name}", "PROCESS_CONFIGURATION")
                event.append_events([sub_event])
                configuration = Configuration(file.file_name)
                process_event = configuration.process()
                sub_event.data = process_event.data
                sub_event.append_events([process_event])
                sub_event.record_success()
            except ConfiguratorException as ce:
                sub_event.record_failure(f"ConfiguratorException processing configuration {file.file_name}")
                event.append_events([ce.event])
                event.record_failure(f"ConfiguratorException processing configuration {file.file_name}")
                raise ConfiguratorException(f"ConfiguratorException processing configuration {file.file_name}", event)
            except Exception as e:
                sub_event.record_failure(f"Failed to process configuration {file.file_name}: {str(e)}")
                event.record_failure(f"Unexpected error processing configuration {file.file_name}")
                raise ConfiguratorException(f"Unexpected error processing configuration {file.file_name}", event)
        
        event.record_success()
        return event
    

    
    def delete(self):
        if self._locked:
            event = ConfiguratorEvent(event_id="CFG-ROUTES-07", event_type="DELETE_CONFIGURATION")
            event.record_failure("Cannot delete locked configuration")
            raise ConfiguratorException("Cannot delete locked configuration", event)
        
        event = ConfiguratorEvent(event_id="CFG-ROUTES-07", event_type="DELETE_CONFIGURATION")
        try:
            delete_event = FileIO.delete_document(self.config.CONFIGURATION_FOLDER, self.file_name)
            if delete_event.status == "SUCCESS":
                event.record_success()
            else:
                event.append_events([delete_event])
                event.record_failure("error deleting configuration")
        except ConfiguratorException as e:
            event.append_events([e.event])
            event.record_failure("error deleting configuration")
        except Exception as e:
            event.record_failure("unexpected error deleting configuration", {"error": str(e)})
        return event
        
    def process(self) -> ConfiguratorEvent:
        """Process all versions of this configuration."""
        event = ConfiguratorEvent(event_id=f"CFG-{self.file_name}", event_type="PROCESS_CONFIGURATION")
        event.data = {"configuration_name": self.file_name, "version_count": len(self.versions)}
        
        # Create MongoIO instance with proper parameters
        mongo_io = MongoIO(self.config.MONGO_CONNECTION_STRING, self.config.MONGO_DB_NAME)

        # Upsert enumerators to database ONCE per configuration
        enumerators = Enumerators()
        event.append_events([enumerators.upsert_all_to_database(mongo_io)])
        
        for version in self.versions:
            event.append_events([version.process(mongo_io)])
        
        event.record_success()
        return event

    def get_json_schema(self, version_str: str) -> dict:
        """Get JSON schema for a specific version."""
        for version in self.versions:
            if version.version_str == version_str:
                enumerations = Enumerators().getVersion(version.collection_version.get_enumerator_version())
                return version.get_json_schema(enumerations)
        
        event = ConfiguratorEvent("CFG-08", "GET_JSON_SCHEMA")
        event.record_failure(f"Version {version_str} not found")
        raise ConfiguratorException(f"Version {version_str} not found", event)

    def get_bson_schema_for_version(self, version_str: str) -> dict:
        """Get BSON schema for a specific version."""
        for version in self.versions:
            if version.version_str == version_str:
                enumerations = Enumerators().getVersion(version.collection_version.get_enumerator_version())
                return version.get_bson_schema(enumerations)
        
        event = ConfiguratorEvent("CFG-09", "GET_BSON_SCHEMA")
        event.record_failure(f"Version {version_str} not found")
        raise ConfiguratorException(f"Version {version_str} not found", event)

class Version:
    def __init__(self, collection_name: str, version: dict, config):
        self.config = config
        self.collection_name = collection_name
        
        try:
            # Always construct VersionNumber with 4-part version string
            self.collection_version = VersionNumber(f"{collection_name}.{version['version']}")
            self.version_str = self.collection_version.get_version_str()
            self.drop_indexes = version.get("drop_indexes", [])
            self.add_indexes = version.get("add_indexes", [])
            self.migrations = version.get("migrations", [])
            self.test_data = version.get("test_data", None)
            self._locked = version.get("_locked", False)
        except ConfiguratorException as e:
            # Re-raise with additional context about the version being constructed
            event = ConfiguratorEvent(event_id=f"VER-CONSTRUCTOR-{collection_name}", event_type="VERSION_CONSTRUCTOR")
            event.record_failure(f"Failed to construct version for collection {collection_name}")
            event.append_events([e.event])
            raise ConfiguratorException(f"Failed to construct version for collection {collection_name}: {str(e)}", event)
        except Exception as e:
            # Handle unexpected errors during construction
            event = ConfiguratorEvent(event_id=f"VER-CONSTRUCTOR-{collection_name}", event_type="VERSION_CONSTRUCTOR")
            event.record_failure(f"Unexpected error constructing version for collection {collection_name}: {str(e)}")
            raise ConfiguratorException(f"Unexpected error constructing version for collection {collection_name}: {str(e)}", event)

    def to_dict(self):
        return {
            "version": self.collection_version.get_version_str(),
            "drop_indexes": self.drop_indexes,
            "add_indexes": self.add_indexes,
            "migrations": self.migrations,
            "test_data": self.test_data,
            "_locked": self._locked,
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
        
        try:
            # Remove schema validation
            sub_event = ConfiguratorEvent(event_id="PRO-01", event_type="REMOVE_SCHEMA_VALIDATION")
            event.append_events([sub_event])
            sub_event.append_events(mongo_io.remove_schema_validation(self.collection_name))
            sub_event.record_success()

            # Remove indexes
            if self.drop_indexes:
                sub_event = ConfiguratorEvent(event_id="PRO-02", event_type="REMOVE_INDEXES")
                event.append_events([sub_event])
                for index_name in self.drop_indexes:
                    sub_event.append_events(mongo_io.remove_index(self.collection_name, index_name))                    
                sub_event.record_success()

            # Execute migrations
            if self.migrations:
                sub_event = ConfiguratorEvent(event_id="PRO-03", event_type="EXECUTE_MIGRATIONS")
                event.append_events([sub_event])
                for filename in self.migrations:
                    migration_file = os.path.join(self.config.INPUT_FOLDER, self.config.MIGRATIONS_FOLDER, filename)
                    sub_event.append_events(mongo_io.execute_migration_from_file(self.collection_name, migration_file))
                    sub_event.record_success()

            # Add indexes
            if self.add_indexes:
                sub_event = ConfiguratorEvent(event_id="PRO-04", event_type="ADD_INDEXES")
                event.append_events([sub_event])
                for index in self.add_indexes:
                    sub_event.append_events(mongo_io.add_index(self.collection_name, index))
                sub_event.record_success()

            # Apply schema validation
            sub_event = ConfiguratorEvent(event_id="PRO-06", event_type="APPLY_SCHEMA_VALIDATION")
            event.append_events([sub_event])
            enumerations = Enumerators().getVersion(self.collection_version.get_enumerator_version())
            bson_schema: dict = self.get_bson_schema(enumerations)
            
            # Add schema context to event
            sub_event.append_events(mongo_io.apply_schema_validation(self.collection_name, bson_schema))
            sub_event.record_success()

            # Load test data
            if self.test_data:
                sub_event = ConfiguratorEvent(event_id="PRO-07", event_type="LOAD_TEST_DATA")
                event.append_events([sub_event])
                test_data_path = os.path.join(self.config.INPUT_FOLDER, self.config.TEST_DATA_FOLDER, self.test_data)
                sub_event.data = {"test_data_path": test_data_path}
                sub_event.append_events(mongo_io.load_json_data(self.collection_name, test_data_path))
                sub_event.record_success()

            # Update version
            sub_event = ConfiguratorEvent(event_id="PRO-08", event_type="UPDATE_VERSION")
            event.append_events([sub_event])
            result = mongo_io.upsert(
                self.config.VERSION_COLLECTION_NAME,
                {"collection_name": self.collection_name},
                {"collection_name": self.collection_name, "current_version": self.collection_version.version}
            )
            sub_event.data = result
            sub_event.record_success()

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