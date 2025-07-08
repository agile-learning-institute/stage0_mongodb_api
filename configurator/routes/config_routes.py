from flask import Blueprint
from configurator.utils.config import Config
from configurator.utils.configurator_exception import ConfiguratorEvent, ConfiguratorException
from configurator.utils.route_decorators import event_route
import logging
logger = logging.getLogger(__name__)

# Define the Blueprint for config routes
def create_config_routes():
    config_routes = Blueprint('config_routes', __name__)
    config = Config.get_instance()
    
    # GET /api/config - Return the current configuration as JSON
    @config_routes.route('/', methods=['GET'])
    @event_route("CFG-00", "GET_CONFIG", "getting config")
    def get_config():
        return config.to_dict()
    
    logger.info("Config Flask Routes Registered")
    return config_routes