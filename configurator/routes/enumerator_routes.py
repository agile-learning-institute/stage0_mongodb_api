from flask import Blueprint, jsonify, request
from configurator.utils.config import Config
from configurator.utils.configurator_exception import ConfiguratorException, ConfiguratorEvent
from configurator.utils.file_io import FileIO
from configurator.services.enumerator_service import Enumerators
from configurator.utils.route_decorators import handle_errors
import logging
logger = logging.getLogger(__name__)

def create_enumerator_routes():
    enumerator_routes = Blueprint('enumerator_routes', __name__)
    config = Config.get_instance()
    
    # GET /api/enumerators - Return the content of enumerators.json
    @enumerator_routes.route('', methods=['GET'])
    @handle_errors("getting enumerators")
    def get_enumerators():
        enumerators = Enumerators(None)
        return jsonify(enumerators.to_dict()), 200
    
    # PATCH /api/enumerators - Clean Enumerators
    @enumerator_routes.route('', methods=['PATCH'])
    def clean_enumerators():
        event = ConfiguratorEvent(event_id="ENU-04", event_type="CLEAN_ENUMERATORS")
        try:
            enumerators = Enumerators(None)
            event.append_events(enumerators.save())
            event.record_success()
            return jsonify(event.to_dict()), 200
        except ConfiguratorException as e:
            logger.error(f"Configurator error cleaning enumerators: {e.event.to_dict()}")
            event.append_events([e.event])
            event.record_failure("Configurator error cleaning enumerators")
            return jsonify(event.to_dict()), 500
        except Exception as e:
            logger.error(f"Unexpected error cleaning enumerators: {str(e)}")
            event.record_failure("Unexpected error cleaning enumerators", {"error": str(e)})
            return jsonify(event.to_dict()), 500
    
    # PUT /api/enumerators - Overwrite enumerators.json
    @enumerator_routes.route('', methods=['PUT'])
    @handle_errors("saving enumerators")
    def put_enumerators():
        enumerators = Enumerators(data=request.get_json(force=True))
        events = enumerators.save()
        return jsonify(events[0].data), 200
    
    logger.info("Enumerator Flask Routes Registered")
    return enumerator_routes