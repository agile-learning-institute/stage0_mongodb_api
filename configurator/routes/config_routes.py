from flask import Blueprint, jsonify
from configurator.utils.config import Config
from configurator.utils.configurator_exception import ConfiguratorException
from configurator.utils.route_decorators import handle_errors

import logging
logger = logging.getLogger(__name__)

# Define the Blueprint for config routes
def create_config_routes():
    config_routes = Blueprint('config_routes', __name__)
    config = Config.get_instance()
    
    # GET /api/config - Return the current configuration as JSON
    @config_routes.route('/', methods=['GET'])
    @handle_errors("getting config")
    def get_config():
        # Return the JSON representation of the config object
        return jsonify(config.to_dict()), 200
        
    logger.info("Config Flask Routes Registered")
    return config_routes