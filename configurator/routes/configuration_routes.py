from flask import Blueprint, jsonify, request
from configurator.services.configuration_services import Configuration
from configurator.services.template_service import TemplateService
from configurator.utils.configurator_exception import ConfiguratorException, ConfiguratorEvent
from configurator.utils.config import Config
from configurator.utils.file_io import FileIO
from configurator.utils.route_decorators import handle_errors

import logging

logger = logging.getLogger(__name__)

def create_configuration_routes():
    blueprint = Blueprint('configurations', __name__)
    config = Config.get_instance()

    @blueprint.route('/', methods=['GET'])
    @handle_errors("listing configurations")
    def list_configurations():
        configurations = FileIO.get_documents(config.CONFIGURATION_FOLDER)
        return jsonify(configurations), 200

    @blueprint.route('/', methods=['POST'])
    @handle_errors("processing configurations")
    def process_configurations():
        """Process all configured configurations"""
        results = []
        configurations = FileIO.get_documents(config.CONFIGURATION_FOLDER)
        for configuration_name in configurations:
            configuration = Configuration(configuration_name)
            results.append(configuration.process())
        return jsonify(results), 200

    @blueprint.route('/', methods=['PATCH'])
    def clean_configurations():
        event = ConfiguratorEvent(event_id="CFG-04", event_type="CLEAN_CONFIGURATIONS")
        try:
            files = FileIO.get_documents(config.CONFIGURATION_FOLDER)
            for file in files:
                configuration = Configuration(file.name)
                event.append_events(configuration.save())
            event.record_success()
            return jsonify(event.to_dict()), 200
        except ConfiguratorException as e:
            logger.error(f"Configurator error cleaning configurations: {e.event.to_dict()}")
            event.append_events([e.event])
            event.record_failure("Configurator error cleaning configurations")
            return jsonify(event.to_dict()), 500
        except Exception as e:
            logger.error(f"Unexpected error cleaning configurations: {str(e)}")
            event.record_failure("Unexpected error cleaning configurations", {"error": str(e)})
            return jsonify(event.to_dict()), 500

    @blueprint.route('/collection/<file_name>/', methods=['POST'])
    @handle_errors("creating collection")
    def create_collection(file_name):
        """Create a new collection with configuration and dictionary files from templates"""
        template_service = TemplateService()
        result = template_service.create_collection(file_name)
        return jsonify(result), 201

    @blueprint.route('/<file_name>/', methods=['GET'])
    @handle_errors("getting configuration")
    def get_configuration(file_name):
        """Get a specific configuration configuration"""
        configuration = Configuration(file_name)
        return jsonify(configuration), 200

    @blueprint.route('/<file_name>/', methods=['PUT'])
    @handle_errors("updating configuration")
    def put_configuration(file_name):
        """Put a specific configuration configuration"""
        configuration = Configuration(file_name, request.json)
        saved = configuration.save()
        return jsonify(saved), 200
        
    @blueprint.route('/<file_name>/', methods=['DELETE'])
    @handle_errors("deleting configuration")
    def delete_configuration(file_name):
        """Delete a specific configuration"""
        configuration = Configuration(file_name)
        deleted = configuration.delete()
        return jsonify(deleted), 200

    @blueprint.route('/<file_name>/', methods=['PATCH'])
    @handle_errors("locking/unlocking configuration")
    def lock_unlock_configuration(file_name):
        """Process a specific configuration"""
        configuration = Configuration(file_name)
        result = configuration.flip_lock()
        return jsonify(result), 200

    @blueprint.route('/<file_name>/', methods=['POST'])
    @handle_errors("processing configuration")
    def process_configuration(file_name):
        """Process a specific configuration"""
        configuration = Configuration(file_name)
        result = configuration.process()
        return jsonify(result), 200

    @blueprint.route('json_schema/<file_name>/<version>/', methods=['GET'])
    @handle_errors("getting JSON schema")
    def get_json_schema(file_name, version):
        """Get a specific JSON schema"""
        configuration = Configuration(file_name)
        schema = configuration.get_json_schema(version)
        return jsonify(schema), 200

    @blueprint.route('bson_schema/<file_name>/<version>/', methods=['GET'])
    @handle_errors("getting BSON schema")
    def get_bson_schema(file_name, version):
        """Get a specific JSON schema"""
        configuration = Configuration(file_name)
        schema = configuration.get_bson_schema(version)
        return jsonify(schema), 200

    logger.info("configuration Flask Routes Registered")
    return blueprint 