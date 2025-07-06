from flask import Blueprint, jsonify, request
from configurator.utils.config import Config
from configurator.utils.configurator_exception import ConfiguratorException
from configurator.utils.file_io import FileIO
from configurator.services.dictionary_services import Dictionary

import logging
logger = logging.getLogger(__name__)

# Define the Blueprint for dictionary routes
def create_dictionary_routes():
    dictionary_routes = Blueprint('dictionary_routes', __name__)
    config = Config.get_instance()
    
    # GET /api/dictionaries - Return the current dictionary files
    @dictionary_routes.route('', methods=['GET'])
    def get_dictionaries():
        try:
            files = FileIO.get_documents(config.DICTIONARY_FOLDER)
            return jsonify(files), 200
        except ConfiguratorException as e:
            logger.error(f"Configurator error listing configurations: {str(e)}")
            return jsonify(e.to_dict()), 500
        except Exception as e:
            logger.error(f"Unexpected error listing configurations: {str(e)}")
            return jsonify(str(e)), 500
        
    # GET /api/dictionaries/<file_name> - Return a dictionary file
    @dictionary_routes.route('/<file_name>', methods=['GET'])
    def get_dictionary(file_name):
        try:
            dictionary = Dictionary(file_name)
            return jsonify(dictionary), 200
        except ConfiguratorException as e:
            logger.error(f"Configurator error getting dictionary {file_name}: {str(e)}")
            return jsonify(e.to_dict()), 500
        except Exception as e:
            logger.error(f"Unexpected error getting dictionary {file_name}: {str(e)}")
            return jsonify(str(e)), 500
        
    # PUT /api/dictionaries/<file_name> - Update a dictionary file
    @dictionary_routes.route('/<file_name>', methods=['PUT'])
    def update_dictionary(file_name):
        try:
            dictionary = Dictionary(file_name, request.json)
            saved = dictionary.save()
            return jsonify(saved), 200
        except ConfiguratorException as e:
            logger.error(f"Configurator error updating dictionary {file_name}: {str(e)}")
            return jsonify(e.to_dict()), 500
        except Exception as e:
            logger.error(f"Unexpected error updating dictionary {file_name}: {str(e)}")
            return jsonify(str(e)), 500
        
    @dictionary_routes.route('/<file_name>', methods=['DELETE'])
    def delete_dictionary(file_name):
        try:
            dictionary = Dictionary(file_name)
            deleted = dictionary.delete()
            return jsonify(deleted), 200
        except ConfiguratorException as e:
            logger.error(f"Configurator error deleting dictionary {file_name}: {str(e)}")
            return jsonify(e.to_dict()), 500
        except Exception as e:
            logger.error(f"Unexpected error deleting dictionary {file_name}: {str(e)}")
            return jsonify(str(e)), 500
        
    @dictionary_routes.route('/<file_name>', methods=['PATCH'])
    def lock_unlock_dictionary(file_name):
        try:
            dictionary = Dictionary(file_name)
            result = dictionary.flip_lock()
            return jsonify(result), 200
        except ConfiguratorException as e:
            logger.error(f"Configurator error locking/unlocking dictionary {file_name}: {str(e)}")
            return jsonify(e.to_dict()), 500
        except Exception as e:
            logger.error(f"Unexpected error locking/unlocking dictionary {file_name}: {str(e)}")
            return jsonify(str(e)), 500
        
    logger.info("dictionary Flask Routes Registered")
    return dictionary_routes