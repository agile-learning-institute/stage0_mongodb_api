from flask import Blueprint, jsonify
from configurator.utils.config import Config

import logging
logger = logging.getLogger(__name__)

# Define the Blueprint for config routes
def create_config_routes():
    config_routes = Blueprint('config_routes', __name__)
    config = Config.get_instance()
    
    # GET /api/config - Return the current configuration as JSON
    @config_routes.route('', methods=['GET'])
    def get_config():
        try:
            # Return the JSON representation of the config object
            return jsonify(config.to_dict()), 200
        except Exception as e:
            logger.warning(f"get_config Error has occurred: {e}")
            return jsonify(str(e)), 500
        
    logger.info("Config Flask Routes Registered")
    return config_routes