from flask import Blueprint, jsonify, request
from configurator.services.configuration_services import Configuration
from configurator.utils.configurator_exception import ConfiguratorException
from configurator.utils.config import Config
from configurator.utils.file_io import FileIO

import logging

logger = logging.getLogger(__name__)

def create_configuration_routes():
    blueprint = Blueprint('configurations', __name__)
    config = Config.get_instance()

    @blueprint.route('/', methods=['GET'])
    def list_configurations():
        try:
            configurations = FileIO.get_documents(config.CONFIGURATION_FOLDER)
            return jsonify(configurations)
        except ConfiguratorException as e:
            logger.error(f"Configurator error listing configurations: {str(e)}")
            return jsonify(e.to_dict()), 500
        except Exception as e:
            logger.error(f"Unexpected error listing configurations: {str(e)}")
            return jsonify("Undefined Exception"), 500

    @blueprint.route('/', methods=['POST'])
    def process_configurations():
        """Process all configured configurations"""
        try:
            results = []
            configurations = FileIO.get_documents(config.CONFIGURATION_FOLDER)
            for configuration_name in configurations:
                configuration = Configuration(configuration_name)
                results.append(configuration.process())
            return jsonify(results)
        except ConfiguratorException as e:
            logger.error(f"Configurator error processing configurations: {str(e)}")
            return jsonify(e.to_dict()), 500
        except Exception as e:
            logger.error(f"Unexpected error processing configurations: {str(e)}")
            return jsonify("Undefined Exception"), 500

    @blueprint.route('/<file_name>/', methods=['GET'])
    def get_configuration(file_name):
        """Get a specific configuration configuration"""
        try:
            configuration = Configuration(file_name)
            return jsonify(configuration)
        except ConfiguratorException as e:
            logger.error(f"Configurator error getting configuration {file_name}: {str(e)}")
            return jsonify(e.to_dict()), 500
        except Exception as e:
            logger.error(f"Unexpected error getting configuration {file_name}: {str(e)}")
            return jsonify("Undefined Exception"), 500

    @blueprint.route('/<file_name>/', methods=['PUT'])
    def put_configuration(file_name):
        """Put a specific configuration configuration"""
        try:
            configuration = Configuration(file_name, request.json)
            saved = configuration.save()
            return jsonify(saved)
        except ConfiguratorException as e:
            logger.error(f"Configurator error getting configuration {file_name}: {str(e)}")
            return jsonify(e.to_dict()), 500
        except Exception as e:
            logger.error(f"Unexpected error getting configuration {file_name}: {str(e)}")
            return jsonify("Undefined Exception"), 500
        
    @blueprint.route('/<file_name>/', methods=['DELETE'])
    def delete_configuration(file_name):
        """Delete a specific configuration"""
        try:
            configuration = Configuration(file_name)
            deleted = configuration.delete()
            return jsonify(deleted) 
        except ConfiguratorException as e:
            logger.error(f"Configurator error deleting configuration {file_name}: {str(e)}")
            return jsonify(e.to_dict()), 500
        except Exception as e:
            logger.error(f"Unexpected error deleting configuration {file_name}: {str(e)}")
            return jsonify("Undefined Exception"), 500

    @blueprint.route('/<file_name>/', methods=['PATCH'])
    def lock_unlock_configuration(file_name):
        """Process a specific configuration"""
        try:
            configuration = Configuration(file_name)
            result = configuration.flip_lock()
            return jsonify(result)
        except ConfiguratorException as e:
            logger.error(f"Configurator error locking/unlocking configuration {file_name}: {str(e)}")
            return jsonify(e.to_dict()), 500
        except Exception as e:
            logger.error(f"Unexpected error locking/unlocking configuration {file_name}: {str(e)}")
            return jsonify("Undefined Exception"), 500

    @blueprint.route('/<file_name>/', methods=['POST'])
    def process_configuration(file_name):
        """Process a specific configuration"""
        try:
            configuration = Configuration(file_name)
            result = configuration.process()
            return jsonify(result)
        except ConfiguratorException as e:
            logger.error(f"Configurator error processing configuration {file_name}: {str(e)}")
            return jsonify(e.to_dict()), 500
        except Exception as e:
            logger.error(f"Unexpected error processing configuration {file_name}: {str(e)}")
            return jsonify("Undefined Exception"), 500

    @blueprint.route('json_schema/<file_name>/<version>/', methods=['GET'])
    def get_json_schema(file_name, version):
        """Get a specific JSON schema"""
        try:
            configuration = Configuration(file_name)
            schema = configuration.get_json_schema(version)
            return jsonify(schema)
        except ConfiguratorException as e:
            logger.error(f"Configurator error getting JSON schema {file_name}, {version}: {str(e)}")
            return jsonify(e.to_dict()), 500
        except Exception as e:
            logger.error(f"Unexpected error getting JSON schema {file_name}, {version}: {str(e)}")
            return jsonify("Undefined Exception"), 500

    @blueprint.route('bson_schema/<file_name>/<version>/', methods=['GET'])
    def get_bson_schema(file_name, version):
        """Get a specific JSON schema"""
        try:
            configuration = Configuration(file_name)
            schema = configuration.get_bson_schema(version)
            return jsonify(schema)
        except ConfiguratorException as e:
            logger.error(f"Configurator error getting BSON schema {file_name}, {version}: {str(e)}")
            return jsonify(e.to_dict()), 500
        except Exception as e:
            logger.error(f"Unexpected error getting BSON schema {file_name}, {version}: {str(e)}")
            return jsonify("Undefined Exception"), 500

    logger.info("configuration Flask Routes Registered")
    return blueprint 