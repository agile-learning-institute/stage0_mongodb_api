from flask import Blueprint, request, jsonify
from configurator.services.configuration_services import Configuration
from configurator.services.dictionary_services import Dictionary
from configurator.services.template_service import TemplateService
from configurator.services.enumerator_service import Enumerators
from configurator.utils.configurator_exception import ConfiguratorEvent
from configurator.utils.config import Config
from configurator.utils.file_io import FileIO, File
from configurator.utils.route_decorators import event_route
from configurator.utils.version_number import VersionNumber
import logging


logger = logging.getLogger(__name__)

def create_configuration_routes():
    blueprint = Blueprint('configurations', __name__)
    config = Config.get_instance()

    # GET /api/configurations - Return the current configuration files
    @blueprint.route('/', methods=['GET'])
    @event_route("CFG-01", "GET_CONFIGURATIONS", "listing configurations")
    def get_configurations():
        files = FileIO.get_documents(config.CONFIGURATION_FOLDER)
        return jsonify([file.to_dict() for file in files])

    @blueprint.route('/', methods=['POST'])
    @event_route("CFG-ROUTES-02", "PROCESS_ALL_CONFIGURATIONS", "processing all configurations")
    def process_configurations():
        result = Configuration.process_all()
        return jsonify(result.to_dict())

    @blueprint.route('/', methods=['PATCH'])
    @event_route("CFG-ROUTES-03", "LOCK_ALL_CONFIGURATIONS", "locking all configurations")
    def lock_all_configurations():
        result = Configuration.lock_all()
        return jsonify(result.to_dict())


    @blueprint.route('/collection/<file_name>/', methods=['POST'])
    @event_route("CFG-ROUTES-04", "CREATE_COLLECTION", "creating collection")
    def create_collection(file_name):
        template_service = TemplateService()
        result = template_service.create_collection(file_name)
        return jsonify(result)

    @blueprint.route('/<file_name>/', methods=['GET'])
    @event_route("CFG-ROUTES-05", "GET_CONFIGURATION", "getting configuration")
    def get_configuration(file_name):
        configuration = Configuration(file_name)
        return jsonify(configuration.to_dict())

    # PUT /api/configurations/<file_name> - Update a configuration file
    @blueprint.route('/<file_name>/', methods=['PUT'])
    @event_route("CFG-ROUTES-06", "PUT_CONFIGURATION", "updating configuration")
    def update_configuration(file_name):
        configuration = Configuration(file_name, request.json)
        file_obj = configuration.save()
        return jsonify(file_obj.to_dict())
    
    @blueprint.route('/<file_name>/', methods=['DELETE'])
    @event_route("CFG-ROUTES-07", "DELETE_CONFIGURATION", "deleting configuration")
    def delete_configuration(file_name):
        configuration = Configuration(file_name)
        event = configuration.delete()
        return jsonify(event.to_dict())

    @blueprint.route('/<file_name>/', methods=['POST'])
    @event_route("CFG-ROUTES-09", "PROCESS_CONFIGURATION", "processing configuration")
    def process_configuration(file_name):
        configuration = Configuration(file_name)
        result = configuration.process()
        return jsonify(result.to_dict())

    @blueprint.route('json_schema/<file_name>/<version>/', methods=['GET'])
    @event_route("CFG-ROUTES-10", "GET_JSON_SCHEMA", "getting JSON schema")
    def get_json_schema(file_name, version):
        configuration = Configuration(file_name)
        schema = configuration.get_json_schema(version)
        return jsonify(schema)

    @blueprint.route('bson_schema/<file_name>/<version>/', methods=['GET'])
    @event_route("CFG-ROUTES-11", "GET_BSON_SCHEMA", "getting BSON schema")
    def get_bson_schema(file_name, version):
        configuration = Configuration(file_name)
        schema = configuration.get_bson_schema_for_version(version)
        return jsonify(schema)

    logger.info("configuration Flask Routes Registered")
    return blueprint 