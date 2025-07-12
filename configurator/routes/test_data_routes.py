from flask import Blueprint, request, jsonify, abort, Response
from configurator.utils.config import Config
from configurator.utils.configurator_exception import ConfiguratorEvent, ConfiguratorException
from configurator.utils.file_io import FileIO, File
from configurator.utils.route_decorators import event_route
import json
import logging
import os
logger = logging.getLogger(__name__)

# Removed TestDataJSONEncoder as it's not being used and the global MongoJSONEncoder handles MongoDB objects

# Define the Blueprint for test_data routes
def create_test_data_routes():
    test_data_routes = Blueprint('test_data_routes', __name__)
    config = Config.get_instance()
    
    # GET /api/test_data - Return the current test_data files (only .json)
    @test_data_routes.route('/', methods=['GET'])
    @event_route("TST-01", "GET_TEST_DATA_FILES", "getting test data files")
    def get_data_files():
        files = FileIO.get_documents(config.TEST_DATA_FOLDER)
        # Only include .json files
        return jsonify([file.to_dict() for file in files if file.file_name.endswith('.json')])
        


        
    # GET /api/test_data/<file_name> - Return a test_data file (only .json)
    @test_data_routes.route('/<file_name>/', methods=['GET'])
    @event_route("TST-02", "GET_TEST_DATA", "getting test data")
    def get_test_data(file_name):
        if not file_name.endswith('.json'):
            abort(404)
        
        # Read the raw JSON file content to preserve MongoDB extended JSON format
        config = Config.get_instance()
        folder = os.path.join(config.INPUT_FOLDER, config.TEST_DATA_FOLDER)
        file_path = os.path.join(folder, file_name)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_content = f.read()
            return Response(raw_content, mimetype='application/json')
        except Exception as e:
            event = ConfiguratorEvent("TST-02", "GET_TEST_DATA")
            event.record_failure(f"Failed to read test data file {file_name}: {str(e)}")
            raise ConfiguratorException(f"Failed to read test data file {file_name}: {str(e)}", event)
        
    # PUT /api/test_data/<file_name> - Update a test_data file (only .json)
    @test_data_routes.route('/<file_name>/', methods=['PUT'])
    @event_route("TST-03", "PUT_TEST_DATA", "updating test data")
    def update_test_data(file_name):
        if not file_name.endswith('.json'):
            abort(400, description='Test data files must be .json')
        file = FileIO.put_document(config.TEST_DATA_FOLDER, file_name, request.json)
        return jsonify(file.to_dict())
        
    @test_data_routes.route('/<file_name>/', methods=['DELETE'])
    @event_route("TST-04", "DELETE_TEST_DATA", "deleting test data")
    def delete_test_data(file_name):
        if not file_name.endswith('.json'):
            abort(404)
        return jsonify(FileIO.delete_document(config.TEST_DATA_FOLDER, file_name).to_dict())
        
    logger.info("test_data Flask Routes Registered")
    return test_data_routes