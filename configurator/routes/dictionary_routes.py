from flask import Blueprint, request
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
        return [file.to_dict() for file in files]
    
    # PATCH /api/dictionaries - Clean Dictionaries
    @dictionary_routes.route('/', methods=['PATCH'])
    @event_route("DIC-04", "CLEAN_DICTIONARIES", "cleaning dictionaries")
    def clean_dictionaries():
        files = FileIO.get_documents(config.DICTIONARY_FOLDER)
        events = []
        for file in files:
            dictionary = Dictionary(file.name)
            events.extend(dictionary.save())
        return events
    
    # GET /api/dictionaries/<file_name> - Return a dictionary file
    @dictionary_routes.route('/<file_name>/', methods=['GET'])
    @event_route("DIC-02", "GET_DICTIONARY", "getting dictionary")
    def get_dictionary(file_name):
        dictionary = Dictionary(file_name)
        return dictionary
    
    # PUT /api/dictionaries/<file_name> - Update a dictionary file
    @dictionary_routes.route('/<file_name>/', methods=['PUT'])
    @event_route("DIC-03", "PUT_DICTIONARY", "updating dictionary")
    def update_dictionary(file_name):
        dictionary = Dictionary(file_name, request.json)
        saved = dictionary.save()
        return saved[0].data if saved else {}
    
    @dictionary_routes.route('/<file_name>/', methods=['DELETE'])
    @event_route("DIC-05", "DELETE_DICTIONARY", "deleting dictionary")
    def delete_dictionary(file_name):
        dictionary = Dictionary(file_name)
        deleted = dictionary.delete()
        return deleted
    
    @dictionary_routes.route('/<file_name>/', methods=['PATCH'])
    @event_route("DIC-06", "LOCK_UNLOCK_DICTIONARY", "locking/unlocking dictionary")
    def lock_unlock_dictionary(file_name):
        dictionary = Dictionary(file_name)
        result = dictionary.flip_lock()
        return result
    
    logger.info("dictionary Flask Routes Registered")
    return dictionary_routes