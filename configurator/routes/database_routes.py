from flask import Blueprint, jsonify, request
from configurator.utils.config import Config
from configurator.utils.configurator_exception import ConfiguratorException
from configurator.utils.mongo_io import MongoIO
from configurator.utils.route_decorators import handle_errors

import logging
logger = logging.getLogger(__name__)

# Define the Blueprint for test_data routes
def create_database_routes():
    database_routes = Blueprint('database_routes', __name__)
    config = Config.get_instance()
    
    # DELETE /api/database - Drop the Database
    @database_routes.route('', methods=['DELETE'])
    @handle_errors("dropping database")
    def drop_database():
        mongo_io = MongoIO(config.MONGO_CONNECTION_STRING, config.MONGO_DB_NAME)
        mongo_io.drop_database()
        mongo_io.disconnect()
        return jsonify("Database Dropped"), 200
        
    logger.info("database Flask Routes Registered")
    return database_routes