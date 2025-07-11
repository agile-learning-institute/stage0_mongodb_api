from flask import Blueprint, request, jsonify
from configurator.utils.config import Config
from configurator.utils.configurator_exception import ConfiguratorEvent, ConfiguratorException
from configurator.services.enumerator_service import Enumerators, Enumerations
from configurator.utils.route_decorators import event_route
from configurator.utils.file_io import FileIO
import logging
logger = logging.getLogger(__name__)

def create_enumerator_routes():
    enumerator_routes = Blueprint('enumerator_routes', __name__)
    config = Config.get_instance()
    
    # GET /api/enumerations - Return list of enumeration files
    @enumerator_routes.route('/', methods=['GET'])
    @event_route("ENU-01", "GET_ENUMERATIONS", "getting enumerations")
    def get_enumerations():
        files = FileIO.get_documents(config.ENUMERATOR_FOLDER)
        return jsonify([file.to_dict() for file in files])
    
    # PATCH /api/enumerations - Lock all enumerations
    @enumerator_routes.route('/', methods=['PATCH'])
    @event_route("ENU-04", "LOCK_ENUMERATIONS", "locking all enumerations")
    def lock_enumerations():
        event = ConfiguratorEvent("ENU-04", "LOCK_ENUMERATIONS")
        enumerators = Enumerators()
        enumerators.lock_all()
        event.record_success()
        return jsonify(event.to_dict())
    
    # GET /api/enumerations/<file_name> - Get specific enumeration file
    @enumerator_routes.route('/<file_name>/', methods=['GET'])
    @event_route("ENU-02", "GET_ENUMERATION", "getting enumeration")
    def get_enumeration(file_name):
        enumerations = Enumerations(file_name=file_name)
        return jsonify(enumerations.to_dict())    
    
    # PUT /api/enumerations/<file_name> - Update specific enumeration file
    @enumerator_routes.route('/<file_name>/', methods=['PUT'])
    @event_route("ENU-03", "PUT_ENUMERATION", "updating enumeration")
    def put_enumeration(file_name):
        data = request.get_json(force=True)
        enumerations = Enumerations(data=data, file_name=file_name)
        saved_enumerations = enumerations.save()
        return jsonify(saved_enumerations.to_dict())
    
    # DELETE /api/enumerations/<file_name> - Delete specific enumeration file
    @enumerator_routes.route('/<file_name>/', methods=['DELETE'])
    @event_route("ENU-05", "DELETE_ENUMERATION", "deleting enumeration")
    def delete_enumeration(file_name):
        enumerators = Enumerators()
        event = enumerators.delete(file_name)
        event.record_success()
        return jsonify(event.to_dict())

    logger.info("Enumerator Flask Routes Registered")
    return enumerator_routes