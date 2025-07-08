from flask import Blueprint, request
from configurator.utils.config import Config
from configurator.utils.configurator_exception import ConfiguratorEvent, ConfiguratorException
from configurator.utils.file_io import FileIO
from configurator.utils.route_decorators import event_route
import os
import logging
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
        filenames = [file.name for file in files]
        return filenames

    # PATCH /api/migrations/ - Clean all migration files (delete all)
    @migration_routes.route('/', methods=['PATCH'])
    @event_route("MIG-04", "CLEAN_MIGRATIONS", "cleaning migrations")
    def clean_migrations():
        files = FileIO.get_documents(config.MIGRATIONS_FOLDER)
        events = []
        for file in files:
            file_path = os.path.join(config.INPUT_FOLDER, config.MIGRATIONS_FOLDER, file.name)
            if os.path.exists(file_path):
                os.remove(file_path)
                sub_event = ConfiguratorEvent(event_id="MIG-05", event_type="DELETE_MIGRATION")
                sub_event.record_success()
                events.append(sub_event)
        return events

    # GET /api/migrations/<file_name>/ - Get a migration file
    @migration_routes.route('/<file_name>/', methods=['GET'])
    @event_route("MIG-02", "GET_MIGRATION", "getting migration")
    def get_migration(file_name):
        migration_path = os.path.join(config.INPUT_FOLDER, config.MIGRATIONS_FOLDER, file_name)
        if not os.path.exists(migration_path):
            raise ConfiguratorException(f"Migration file {file_name} not found", ConfiguratorEvent(event_id="MIG-01", event_type="MIGRATION_NOT_FOUND"))
        with open(migration_path, 'r') as file:
            from bson import json_util
            content = json_util.loads(file.read())
        return content

    # PUT /api/migrations/<file_name>/ - Update or create a migration file
    @migration_routes.route('/<file_name>/', methods=['PUT'])
    @event_route("MIG-08", "UPDATE_MIGRATION", "updating migration")
    def put_migration(file_name):
        migration_path = os.path.join(config.INPUT_FOLDER, config.MIGRATIONS_FOLDER, file_name)
        content = request.get_json(force=True)
        from bson import json_util
        with open(migration_path, 'w') as file:
            file.write(json_util.dumps(content))
        return {"message": "Migration updated"}

    # DELETE /api/migrations/<file_name>/ - Delete a migration file
    @migration_routes.route('/<file_name>/', methods=['DELETE'])
    @event_route("MIG-06", "DELETE_MIGRATION", "deleting migration")
    def delete_migration(file_name):
        migration_path = os.path.join(config.INPUT_FOLDER, config.MIGRATIONS_FOLDER, file_name)
        if not os.path.exists(migration_path):
            raise ConfiguratorException(f"Migration file {file_name} not found", ConfiguratorEvent(event_id="MIG-03", event_type="MIGRATION_NOT_FOUND"))
        os.remove(migration_path)
        return {"message": "Migration deleted"}
    
    logger.info("Migration Flask Routes Registered")
    return migration_routes 