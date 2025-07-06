from flask import Blueprint, jsonify, request
from configurator.utils.config import Config
from configurator.utils.configurator_exception import ConfiguratorException
from configurator.utils.mongo_io import MongoIO

import logging
logger = logging.getLogger(__name__)

# Define the Blueprint for test_data routes
def create_database_routes():
    database_routes = Blueprint('database_routes', __name__)
    config = Config.get_instance()
    
    # DELETE /api/database - Drop the Database
    @database_routes.route('', methods=['DELETE'])
    def drop_database():
        try:
            mongo_io = MongoIO(config.MONGO_CONNECTION_STRING, config.MONGO_DB_NAME)
            mongo_io.drop_database()
            mongo_io.disconnect()
            return jsonify("Database Dropped"), 200
        except ConfiguratorException as e:
            logger.error(f"Configurator error dropping database: {str(e)}")
            return jsonify(e.to_dict()), 500
        except Exception as e:
            logger.error(f"Unexpected error dropping the database: {str(e)}")
            return jsonify("Undefined Exception"), 500
        
    logger.info("database Flask Routes Registered")
    return database_routes