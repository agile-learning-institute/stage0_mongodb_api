from flask import Blueprint, jsonify, request
from configurator.utils.config import Config
from configurator.utils.configurator_exception import ConfiguratorException
from configurator.utils.file_io import FileIO
from configurator.utils.route_decorators import handle_errors

import logging
logger = logging.getLogger(__name__)

# Define the Blueprint for test_data routes
def create_test_data_routes():
    test_data_routes = Blueprint('test_data_routes', __name__)
    config = Config.get_instance()
    
    # GET /api/dictionaries - Return the current test_data files
    @test_data_routes.route('', methods=['GET'])
    @handle_errors("getting test data files")
    def get_data_files():
        files = FileIO.get_documents(config.TEST_DATA_FOLDER)
        return jsonify(files), 200
        
    # GET /api/dictionaries/<file_name> - Return a test_data file
    @test_data_routes.route('/<file_name>', methods=['GET'])
    @handle_errors("getting test data")
    def get_test_data(file_name):
        file = FileIO.get_document(config.TEST_DATA_FOLDER, file_name)
        return jsonify(file), 200
        
    # PUT /api/dictionaries/<file_name> - Update a test_data file
    @test_data_routes.route('/<file_name>', methods=['PUT'])
    @handle_errors("updating test data")
    def update_test_data(file_name):
        file = FileIO.put_document(config.TEST_DATA_FOLDER, file_name, request.json)
        return jsonify(file), 200
        
    @test_data_routes.route('/<file_name>', methods=['DELETE'])
    @handle_errors("deleting test data")
    def delete_test_data(file_name):
        file = FileIO.delete_document(config.TEST_DATA_FOLDER, file_name)
        return jsonify(file), 200
        
    @test_data_routes.route('/<file_name>', methods=['PATCH'])
    @handle_errors("locking/unlocking test data")
    def lock_unlock_test_data(file_name):
        file = FileIO.lock_unlock(config.TEST_DATA_FOLDER, file_name)
        return jsonify(file), 200
        
    logger.info("test_data Flask Routes Registered")
    return test_data_routes