from flask import Blueprint, request, jsonify
from configurator.utils.config import Config
from configurator.utils.configurator_exception import ConfiguratorEvent, ConfiguratorException
from configurator.utils.file_io import FileIO
from configurator.services.dictionary_services import Dictionary
from configurator.utils.route_decorators import event_route
import logging
logger = logging.getLogger(__name__)

# Define the Blueprint for dictionary routes
def create_dictionary_routes():
    dictionary_routes = Blueprint('dictionary_routes', __name__)
    config = Config.get_instance()
    
    # GET /api/dictionaries - Return the current dictionary files
    @dictionary_routes.route('/', methods=['GET'])
    @event_route("DIC-01", "GET_DICTIONARIES", "listing dictionaries")
    def get_dictionaries():
        files = FileIO.get_documents(config.DICTIONARY_FOLDER)
        return jsonify([file.to_dict() for file in files])
    
    # PATCH /api/dictionaries - Clean Dictionaries
    @dictionary_routes.route('/', methods=['PATCH'])
    @event_route("DIC-04", "CLEAN_DICTIONARIES", "cleaning dictionaries")
    def clean_dictionaries():
        files = FileIO.get_documents(config.DICTIONARY_FOLDER)
        cleaned_files = []
        
        for file in files:
            try:
                dictionary = Dictionary(file.name)
                cleaned_file = dictionary.save()
                cleaned_files.append(cleaned_file.to_dict())
            except Exception as e:
                # Raise to trigger 500 from decorator
                raise ConfiguratorException(f"Failed to clean dictionary {file.name}: {str(e)}")
        
        return jsonify(cleaned_files)
    
    # GET /api/dictionaries/<file_name> - Return a dictionary file
    @dictionary_routes.route('/<file_name>/', methods=['GET'])
    @event_route("DIC-02", "GET_DICTIONARY", "getting dictionary")
    def get_dictionary(file_name):
        dictionary = Dictionary(file_name)
        return jsonify(dictionary.to_dict())
    
    # PUT /api/dictionaries/<file_name> - Update a dictionary file
    @dictionary_routes.route('/<file_name>/', methods=['PUT'])
    @event_route("DIC-03", "PUT_DICTIONARY", "updating dictionary")
    def update_dictionary(file_name):
        dictionary = Dictionary(file_name, request.json)
        saved_file = dictionary.save()
        return jsonify(saved_file.to_dict())
    
    @dictionary_routes.route('/<file_name>/', methods=['DELETE'])
    @event_route("DIC-05", "DELETE_DICTIONARY", "deleting dictionary")
    def delete_dictionary(file_name):
        dictionary = Dictionary(file_name)
        deleted = dictionary.delete()
        return jsonify(deleted.to_dict())
    
    @dictionary_routes.route('/<file_name>/', methods=['PATCH'])
    @event_route("DIC-06", "LOCK_UNLOCK_DICTIONARY", "locking/unlocking dictionary")
    def lock_unlock_dictionary(file_name):
        dictionary = Dictionary(file_name)
        result = dictionary.lock_unlock()
        return jsonify(result.to_dict())
    
    logger.info("dictionary Flask Routes Registered")
    return dictionary_routes