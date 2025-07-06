from flask import Blueprint, jsonify, request
from configurator.utils.config import Config
from configurator.utils.configurator_exception import ConfiguratorException
from configurator.utils.file_io import FileIO

import logging
logger = logging.getLogger(__name__)

# Define the Blueprint for test_data routes
def create_test_data_routes():
    test_data_routes = Blueprint('test_data_routes', __name__)
    config = Config.get_instance()
    
    # GET /api/dictionaries - Return the current test_data files
    @test_data_routes.route('', methods=['GET'])
    def get_data_files():
        try:
            files = FileIO.get_files(config.TEST_DATA_FOLDER)
            return jsonify(files), 200
        except ConfiguratorException as e:
            logger.error(f"Configurator error getting test data files: {str(e)}")
            return jsonify(e.events), 500
        except Exception as e:
            logger.error(f"Unexpected error getting test data files: {str(e)}")
            return jsonify("Undefined Exception"), 500
        
    # GET /api/dictionaries/<file_name> - Return a test_data file
    @test_data_routes.route('/<file_name>', methods=['GET'])
    def get_test_data(file_name):
        try:
            file = FileIO.get_file(config.TEST_DATA_FOLDER, file_name)
            return jsonify(file), 200
        except ConfiguratorException as e:
            logger.error(f"Configurator error getting test data {file_name}: {str(e)}")
            return jsonify(e.events), 500
        except Exception as e:
            logger.error(f"Unexpected error getting test data {file_name}: {str(e)}")
            return jsonify("Undefined Exception"), 500
        
    # PUT /api/dictionaries/<file_name> - Update a test_data file
    @test_data_routes.route('/<file_name>', methods=['PUT'])
    def update_test_data(file_name):
        try:
            file = FileIO.put_file(config.TEST_DATA_FOLDER, request.json)
            return jsonify(file), 200
        except ConfiguratorException as e:
            logger.error(f"Configurator error updating test data {file_name}: {str(e)}")
            return jsonify(e.events), 500
        except Exception as e:
            logger.error(f"Unexpected error updating test data {file_name}: {str(e)}")
            return jsonify({"error": "A processing error occurred"}), 500
        
    @test_data_routes.route('/<file_name>', methods=['DELETE'])
    def delete_test_data(file_name):
        try:
            file = FileIO.delete_file(config.TEST_DATA_FOLDER, file_name)
            return jsonify(file), 200
        except ConfiguratorException as e:
            logger.error(f"Configurator error deleting test data {file_name}: {str(e)}")
            return jsonify(e.events), 500
        except Exception as e:
            logger.error(f"Unexpected error deleting test data {file_name}: {str(e)}")
            return jsonify("Undefined Exception"), 500
        
    @test_data_routes.route('/<file_name>', methods=['PATCH'])
    def lock_unlock_test_data(file_name):
        try:
            file = FileIO.lock_unlock_file(config.TEST_DATA_FOLDER, file_name)
            return jsonify(file), 200
        except ConfiguratorException as e:
            logger.error(f"Configurator error locking/unlocking test data {file_name}: {str(e)}")
            return jsonify(e.events), 500
        except Exception as e:
            logger.error(f"Unexpected error locking/unlocking test data {file_name}: {str(e)}")
            return jsonify("Undefined Exception"), 500
        
    logger.info("test_data Flask Routes Registered")
    return test_data_routes