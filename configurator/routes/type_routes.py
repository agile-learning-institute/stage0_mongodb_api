from flask import Blueprint, jsonify, request
from configurator.utils.config import Config
from configurator.utils.configurator_exception import ConfiguratorException
from configurator.utils.file_io import FileIO
from configurator.services.type_services import Type

import logging
logger = logging.getLogger(__name__)

# Define the Blueprint for type routes
def create_type_routes():
    type_routes = Blueprint('type_routes', __name__)
    config = Config.get_instance()
    
    # GET /api/types - Return the current type files
    @type_routes.route('', methods=['GET'])
    def get_types():
        try:
            files = FileIO.get_files(config.CONFIGURATIONS_FOLDER)
            return jsonify(files), 200
        except ConfiguratorException as e:
            logger.error(f"Configurator error listing configurations: {str(e)}")
            return jsonify(e.events), 500
        except Exception as e:
            logger.error(f"Unexpected error listing configurations: {str(e)}")
            return jsonify("Undefined Exception"), 500
        
    # GET /api/types/<file_name> - Return a type file
    @type_routes.route('/<file_name>', methods=['GET'])
    def get_type(file_name):
        try:
            type = Type(file_name)
            return jsonify(type), 200
        except ConfiguratorException as e:
            logger.error(f"Configurator error getting type {file_name}: {str(e)}")
            return jsonify(e.events), 500
        except Exception as e:
            logger.error(f"Unexpected error getting type {file_name}: {str(e)}")
            return jsonify("Undefined Exception"), 500
        
    # PUT /api/types/<file_name> - Update a type file
    @type_routes.route('/<file_name>', methods=['PUT'])
    def update_type(file_name):
        try:
            type = Type(file_name, request.json)
            saved = type.save()
            return jsonify(saved), 200
        except ConfiguratorException as e:
            logger.error(f"Configurator error updating type {file_name}: {str(e)}")
            return jsonify(e.events), 500
        except Exception as e:
            logger.error(f"Unexpected error updating type {file_name}: {str(e)}")
            return jsonify("Undefined Exception"), 500
        
    @type_routes.route('/<file_name>', methods=['DELETE'])
    def delete_type(file_name):
        try:
            type = Type(file_name)
            deleted = type.delete()
            return jsonify(deleted), 200
        except ConfiguratorException as e:
            logger.error(f"Configurator error deleting type {file_name}: {str(e)}")
            return jsonify(e.events), 500
        except Exception as e:
            logger.error(f"Unexpected error deleting type {file_name}: {str(e)}")
            return jsonify("Undefined Exception"), 500
        
    @type_routes.route('/<file_name>', methods=['PATCH'])
    def lock_unlock_type(file_name):
        try:
            type = Type(file_name)
            result = type.flip_lock()
            return jsonify(result), 200
        except ConfiguratorException as e:
            logger.error(f"Configurator error locking/unlocking type {file_name}: {str(e)}")
            return jsonify(e.events), 500
        except Exception as e:
            logger.error(f"Unexpected error locking/unlocking type {file_name}: {str(e)}")
            return jsonify("Undefined Exception"), 500
        
    logger.info("Type Flask Routes Registered")
    return type_routes