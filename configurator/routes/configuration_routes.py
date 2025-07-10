from flask import Blueprint, request
from configurator.services.configuration_services import Configuration
from configurator.services.template_service import TemplateService
from configurator.utils.configurator_exception import ConfiguratorEvent, ConfiguratorException
from configurator.utils.config import Config
from configurator.utils.file_io import FileIO
from configurator.utils.route_decorators import event_route
import logging

logger = logging.getLogger(__name__)

def create_configuration_routes():
    blueprint = Blueprint('configurations', __name__)
    config = Config.get_instance()

    @blueprint.route('/', methods=['GET'])
    @event_route("CFG-ROUTES-01", "GET_CONFIGURATIONS", "listing configurations")
    def list_configurations():
        configurations = FileIO.get_documents(config.CONFIGURATION_FOLDER)
        return [configuration.to_dict() for configuration in configurations]

    @blueprint.route('/', methods=['POST'])
    @event_route("CFG-ROUTES-02", "PROCESS_CONFIGURATIONS", "processing configurations")
    def process_configurations():
        results = ConfiguratorEvent(event_id="CFG-ROUTES-02", event_type="PROCESS_CONFIGURATIONS")
        files = FileIO.get_documents(config.CONFIGURATION_FOLDER)
        for file in files:
            configuration = Configuration(file.name)
            results.append_events([configuration.process()])
        results.record_success()
        return results.to_dict()

    @blueprint.route('/', methods=['PATCH'])
    @event_route("CFG-ROUTES-03", "CLEAN_CONFIGURATIONS", "cleaning configurations")
    def clean_configurations():
        files = FileIO.get_documents(config.CONFIGURATION_FOLDER)
        cleaned_files = []
        
        for file in files:
            try:
                configuration = Configuration(file.name)
                cleaned_file = configuration.save()
                cleaned_files.append(cleaned_file.to_dict())
            except Exception as e:
                # Raise to trigger 500 from decorator
                raise ConfiguratorException(f"Failed to clean configuration {file.name}: {str(e)}")
        
        return cleaned_files

    @blueprint.route('/collection/<file_name>/', methods=['POST'])
    @event_route("CFG-ROUTES-04", "CREATE_COLLECTION", "creating collection")
    def create_collection(file_name):
        template_service = TemplateService()
        result = template_service.create_collection(file_name)
        return result

    @blueprint.route('/<file_name>/', methods=['GET'])
    @event_route("CFG-ROUTES-05", "GET_CONFIGURATION", "getting configuration")
    def get_configuration(file_name):
        configuration = Configuration(file_name)
        return configuration

    @blueprint.route('/<file_name>/', methods=['PUT'])
    @event_route("CFG-ROUTES-06", "PUT_CONFIGURATION", "updating configuration")
    def put_configuration(file_name):
        configuration = Configuration(file_name, request.json)
        saved_file = configuration.save()
        return saved_file.to_dict()
    
    @blueprint.route('/<file_name>/', methods=['DELETE'])
    @event_route("CFG-ROUTES-07", "DELETE_CONFIGURATION", "deleting configuration")
    def delete_configuration(file_name):
        configuration = Configuration(file_name)
        deleted = configuration.delete()
        return deleted

    @blueprint.route('/<file_name>/', methods=['PATCH'])
    @event_route("CFG-ROUTES-08", "LOCK_UNLOCK_CONFIGURATION", "locking/unlocking configuration")
    def lock_unlock_configuration(file_name):
        configuration = Configuration(file_name)
        result = configuration.flip_lock()
        return result

    @blueprint.route('/<file_name>/', methods=['POST'])
    @event_route("CFG-ROUTES-09", "PROCESS_CONFIGURATION", "processing configuration")
    def process_configuration(file_name):
        configuration = Configuration(file_name)
        result = configuration.process()
        return result

    @blueprint.route('json_schema/<file_name>/<version>/', methods=['GET'])
    @event_route("CFG-ROUTES-10", "GET_JSON_SCHEMA", "getting JSON schema")
    def get_json_schema(file_name, version):
        configuration = Configuration(file_name)
        schema = configuration.get_json_schema(version)
        return schema

    @blueprint.route('bson_schema/<file_name>/<version>/', methods=['GET'])
    @event_route("CFG-ROUTES-11", "GET_BSON_SCHEMA", "getting BSON schema")
    def get_bson_schema(file_name, version):
        configuration = Configuration(file_name)
        schema = configuration.get_bson_schema_for_version(version)
        return schema

    logger.info("configuration Flask Routes Registered")
    return blueprint 