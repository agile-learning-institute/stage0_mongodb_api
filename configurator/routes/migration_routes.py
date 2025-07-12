from flask import Blueprint, request, jsonify
from configurator.utils.config import Config
from configurator.utils.configurator_exception import ConfiguratorEvent, ConfiguratorException
from configurator.utils.file_io import FileIO, File
from configurator.utils.route_decorators import event_route
import logging
import os
logger = logging.getLogger(__name__)

# Define the Blueprint for migration routes
def create_migration_routes():
    migration_routes = Blueprint('migration_routes', __name__)
    config = Config.get_instance()
    
    # GET /api/migrations/ - List all migration files
    @migration_routes.route('/', methods=['GET'])
    @event_route("MIG-01", "GET_MIGRATIONS", "listing migrations")
    def get_migrations():
        files = FileIO.get_documents(config.MIGRATIONS_FOLDER)
        return jsonify([file.to_dict() for file in files])

    # GET /api/migrations/<file_name>/ - Get a migration file
    @migration_routes.route('/<file_name>/', methods=['GET'])
    @event_route("MIG-02", "GET_MIGRATION", "getting migration")
    def get_migration(file_name):
        try:
            content = FileIO.get_document(config.MIGRATIONS_FOLDER, file_name)
            return jsonify(content)
        except Exception as e:
            raise ConfiguratorException(f"Migration file {file_name} not found", ConfiguratorEvent(event_id="MIG-01", event_type="MIGRATION_NOT_FOUND"))

    # PUT /api/migrations/<file_name>/ - Update or create a migration file
    @migration_routes.route('/<file_name>/', methods=['PUT'])
    @event_route("MIG-08", "UPDATE_MIGRATION", "updating migration")
    def put_migration(file_name):
        content = request.get_json(force=True)
        file = FileIO.put_document(config.MIGRATIONS_FOLDER, file_name, content)
        return jsonify(file.to_dict())

    # DELETE /api/migrations/<file_name>/ - Delete a migration file
    @migration_routes.route('/<file_name>/', methods=['DELETE'])
    @event_route("MIG-06", "DELETE_MIGRATION", "deleting migration")
    def delete_migration(file_name):
        return jsonify(FileIO.delete_document(config.MIGRATIONS_FOLDER, file_name).to_dict())
    
    logger.info("Migration Flask Routes Registered")
    return migration_routes 