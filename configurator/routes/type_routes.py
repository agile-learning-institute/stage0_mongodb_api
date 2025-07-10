from flask import Blueprint, request, jsonify
from configurator.utils.config import Config
from configurator.utils.configurator_exception import ConfiguratorEvent, ConfiguratorException
from configurator.utils.file_io import FileIO
from configurator.services.type_services import Type
from configurator.utils.route_decorators import event_route
import logging
logger = logging.getLogger(__name__)

# Define the Blueprint for type routes
def create_type_routes():
    type_routes = Blueprint('type_routes', __name__)
    config = Config.get_instance()
    
    # GET /api/types/ - Return the current type files
    @type_routes.route('/', methods=['GET'])
    @event_route("TYP-01", "GET_TYPES", "listing types")
    def get_types():
        files = FileIO.get_documents(config.TYPE_FOLDER)
        return jsonify([file.to_dict() for file in files])

    # PATCH /api/types - Clean Types
    @type_routes.route('/', methods=['PATCH'])
    @event_route("TYP-04", "CLEAN_TYPES", "cleaning types")
    def clean_types():
        files = FileIO.get_documents(config.TYPE_FOLDER)
        cleaned_files = []
        
        for file in files:
            try:
                type_obj = Type(file.name)
                cleaned_file = type_obj.save()
                cleaned_files.append(cleaned_file.to_dict())
            except Exception as e:
                # Create event and raise ConfiguratorException to trigger 500 from decorator
                event = ConfiguratorEvent("TYP-04", "CLEAN_TYPES")
                event.record_failure(f"Failed to clean type {file.name}: {str(e)}")
                raise ConfiguratorException(f"Failed to clean type {file.name}: {str(e)}", event)
        
        return jsonify(cleaned_files)

    # GET /api/types/<file_name>/ - Return a type file
    @type_routes.route('/<file_name>/', methods=['GET'])
    @event_route("TYP-02", "GET_TYPE", "getting type")
    def get_type(file_name):
        type_obj = Type(file_name)
        return jsonify(type_obj.property.to_dict())
    
    # PUT /api/types/<file_name> - Update a type file
    @type_routes.route('/<file_name>/', methods=['PUT'])
    @event_route("TYP-03", "PUT_TYPE", "updating type")
    def update_type(file_name):
        type_obj = Type(file_name, request.json)
        saved_file = type_obj.save()
        return jsonify(saved_file.to_dict())
    
    @type_routes.route('/<file_name>/', methods=['DELETE'])
    @event_route("TYP-05", "DELETE_TYPE", "deleting type")
    def delete_type(file_name):
        type_obj = Type(file_name)
        deleted = type_obj.delete()
        return jsonify(deleted.to_dict())
    
    @type_routes.route('/<file_name>/', methods=['PATCH'])
    @event_route("TYP-06", "LOCK_UNLOCK_TYPE", "locking/unlocking type")
    def lock_unlock_type(file_name):
        type_obj = Type(file_name)
        result = type_obj.flip_lock()
        return jsonify(result.to_dict())
    
    logger.info("Type Flask Routes Registered")
    return type_routes