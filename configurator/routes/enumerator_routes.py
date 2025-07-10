from flask import Blueprint, request, jsonify
from configurator.utils.config import Config
from configurator.utils.configurator_exception import ConfiguratorEvent, ConfiguratorException
from configurator.services.enumerator_service import Enumerators
from configurator.utils.route_decorators import event_route
import logging
logger = logging.getLogger(__name__)

def create_enumerator_routes():
    enumerator_routes = Blueprint('enumerator_routes', __name__)
    config = Config.get_instance()
    
    # GET /api/enumerators - Return the content of enumerators.json
    @enumerator_routes.route('/', methods=['GET'])
    @event_route("ENU-01", "GET_ENUMERATORS", "getting enumerators")
    def get_enumerators():
        enumerators = Enumerators(None)
        return jsonify(enumerators.to_dict())
    
    # PUT /api/enumerators - Overwrite enumerators.json
    @enumerator_routes.route('/', methods=['PUT'])
    @event_route("ENU-02", "PUT_ENUMERATORS", "saving enumerators")
    def put_enumerators():
        enumerators = Enumerators(data=request.get_json(force=True))
        saved_enumerators = enumerators.save()
        return jsonify(saved_enumerators.to_dict())
    
    logger.info("Enumerator Flask Routes Registered")
    return enumerator_routes