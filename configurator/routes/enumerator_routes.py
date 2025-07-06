from flask import Blueprint, jsonify, request
from configurator.utils.config import Config
from configurator.utils.configurator_exception import ConfiguratorException
from configurator.utils.file_io import FileIO
import logging
logger = logging.getLogger(__name__)

def create_enumerator_routes():
    enumerator_routes = Blueprint('enumerator_routes', __name__)
    config = Config.get_instance()
    file_io = FileIO()
    
    # GET /api/enumerators - Return the content of enumerators.json
    @enumerator_routes.route('', methods=['GET'])
    def get_enumerators():
        try:
            content = file_io.get_document(config.TEST_DATA_FOLDER, "enumerators.json")
            return jsonify(content), 200
        except ConfiguratorException as e:
            logger.error(f"Configurator error getting enumerators: {str(e)}")
            # If file not found, return 404
            if e.event and e.event.type == "FILE_NOT_FOUND":
                return jsonify(e.to_dict()), 404
            return jsonify(e.to_dict()), 500
        except Exception as e:
            logger.error(f"Unexpected error getting enumerators: {str(e)}")
            return jsonify("Undefined Exception"), 500
    
    # PUT /api/enumerators - Overwrite enumerators.json
    @enumerator_routes.route('', methods=['PUT'])
    def put_enumerators():
        try:
            data = request.get_json(force=True)
            file_io.put_document(config.TEST_DATA_FOLDER, "enumerators.json", data)
            return jsonify(data), 200
        except ConfiguratorException as e:
            logger.error(f"Configurator error saving enumerators: {str(e)}")
            return jsonify(e.to_dict()), 500
        except Exception as e:
            logger.error(f"Unexpected error saving enumerators: {str(e)}")
            return jsonify("Undefined Exception"), 500
    
    logger.info("Enumerator Flask Routes Registered")
    return enumerator_routes