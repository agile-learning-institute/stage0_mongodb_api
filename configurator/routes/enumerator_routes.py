from flask import Blueprint, jsonify, request
from configurator.services.enumerator_service import Enumerators
from configurator.utils.config import Config
from configurator.utils.configurator_exception import ConfiguratorException
from configurator.utils.file_io import FileIO
from configurator.services.type_services import Type

import logging
logger = logging.getLogger(__name__)

# Define the Blueprint for type routes
def create_enumerator_routes():
    enumerator_routes = Blueprint('enumerator_routes', __name__)
    config = Config.get_instance()
    
    # GET /api/enumerators/ - Return the current enumerator file
    @enumerator_routes.route('', methods=['GET'])
    def get_enumerators():
        try:
            enumerators = FileIO.get_files(config.TEST_DATA_FOLDER, "enumerators.json")
            return jsonify(enumerators), 200
        except ConfiguratorException as e:
            logger.error(f"Configurator error getting enumerators: {str(e)}")
            return jsonify(e.events), 500
        except Exception as e:
            logger.error(f"Unexpected error getting enumerators: {str(e)}")
            return jsonify("Undefined Exception"), 500
        
    # PUT /api/enumerators/ - Update the enumerator file
    @enumerator_routes.route('', methods=['PUT'])
    def update_enumerator():
        try:
            enumerator = Enumerators(request.json)
            updated = enumerator.save()
            return jsonify(updated), 200
        except ConfiguratorException as e:
            logger.error(f"Configurator error getting type {file_name}: {str(e)}")
            return jsonify(e.events), 500
        except Exception as e:
            logger.error(f"Unexpected error getting type {file_name}: {str(e)}")
            return jsonify("Undefined Exception"), 500
        
    logger.info("Enumerator Flask Routes Registered")
    return enumerator_routes