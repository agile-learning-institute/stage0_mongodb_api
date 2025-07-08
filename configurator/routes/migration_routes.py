from flask import Blueprint, jsonify, request
from configurator.utils.config import Config
from configurator.utils.configurator_exception import ConfiguratorEvent, ConfiguratorException
from configurator.utils.file_io import FileIO
from configurator.utils.route_decorators import handle_errors
import os

import logging
logger = logging.getLogger(__name__)

# Define the Blueprint for migration routes
def create_migration_routes():
    migration_routes = Blueprint('migration_routes', __name__)
    config = Config.get_instance()
    
    # GET /api/migrations/ - List all migration files
    @migration_routes.route('/', methods=['GET'])
    @handle_errors("listing migrations")
    def get_migrations():
        files = FileIO.get_documents(config.MIGRATIONS_FOLDER)
        # Convert File objects to filenames for JSON serialization
        filenames = [file.name for file in files]
        return jsonify(filenames), 200

    # PATCH /api/migrations/ - Clean all migration files (delete all)
    @migration_routes.route('/', methods=['PATCH'])
    def clean_migrations():
        event = ConfiguratorEvent(event_id="MIG-04", event_type="CLEAN_MIGRATIONS")
        try:
            files = FileIO.get_documents(config.MIGRATIONS_FOLDER)
            for file in files:
                file_path = os.path.join(config.INPUT_FOLDER, config.MIGRATIONS_FOLDER, file.name)
                if os.path.exists(file_path):
                    os.remove(file_path)
                    sub_event = ConfiguratorEvent(event_id="MIG-05", event_type="DELETE_MIGRATION")
                    sub_event.record_success()
                    event.append_events([sub_event])
            event.record_success()
            return jsonify(event.to_dict()), 200
        except ConfiguratorException as e:
            logger.error(f"Configurator error cleaning migrations: {e.event.to_dict()}")
            event.append_events([e.event])
            event.record_failure("Configurator error cleaning migrations")
            return jsonify(event.to_dict()), 500
        except Exception as e:
            logger.error(f"Unexpected error cleaning migrations: {str(e)}")
            event.record_failure("Unexpected error cleaning migrations", {"error": str(e)})
            return jsonify(event.to_dict()), 500

    # GET /api/migrations/<file_name>/ - Get a migration file
    @migration_routes.route('/<file_name>/', methods=['GET'])
    @handle_errors("getting migration")
    def get_migration(file_name):
        try:
            migration_path = os.path.join(config.INPUT_FOLDER, config.MIGRATIONS_FOLDER, file_name)
            if not os.path.exists(migration_path):
                event = ConfiguratorEvent(event_id="MIG-01", event_type="MIGRATION_NOT_FOUND")
                event.record_failure({"error": f"Migration file {file_name} not found"})
                return jsonify(event.to_dict()), 404
            
            with open(migration_path, 'r') as file:
                from bson import json_util
                content = json_util.loads(file.read())
            
            return jsonify(content), 200
        except Exception as e:
            event = ConfiguratorEvent(event_id="MIG-02", event_type="LOAD_MIGRATION")
            event.record_failure({"error": str(e), "file": file_name})
            return jsonify(event.to_dict()), 500
        
    # PUT /api/migrations/<file_name>/ - Update or create a migration file
    @migration_routes.route('/<file_name>/', methods=['PUT'])
    @handle_errors("updating migration")
    def put_migration(file_name):
        try:
            migration_path = os.path.join(config.INPUT_FOLDER, config.MIGRATIONS_FOLDER, file_name)
            # Accept JSON body
            content = request.get_json(force=True)
            from bson import json_util
            with open(migration_path, 'w') as file:
                file.write(json_util.dumps(content))
            event = ConfiguratorEvent(event_id="MIG-08", event_type="UPDATE_MIGRATION")
            event.record_success()
            return jsonify(event.to_dict()), 200
        except Exception as e:
            event = ConfiguratorEvent(event_id="MIG-09", event_type="UPDATE_MIGRATION")
            event.record_failure({"error": str(e), "file": file_name})
            return jsonify(event.to_dict()), 500

    # DELETE /api/migrations/<file_name>/ - Delete a migration file
    @migration_routes.route('/<file_name>/', methods=['DELETE'])
    @handle_errors("deleting migration")
    def delete_migration(file_name):
        try:
            migration_path = os.path.join(config.INPUT_FOLDER, config.MIGRATIONS_FOLDER, file_name)
            if not os.path.exists(migration_path):
                event = ConfiguratorEvent(event_id="MIG-03", event_type="MIGRATION_NOT_FOUND")
                event.record_failure({"error": f"Migration file {file_name} not found"})
                return jsonify(event.to_dict()), 404
            
            os.remove(migration_path)
            event = ConfiguratorEvent(event_id="MIG-06", event_type="DELETE_MIGRATION")
            event.record_success()
            return jsonify(event.to_dict()), 200
        except Exception as e:
            event = ConfiguratorEvent(event_id="MIG-07", event_type="DELETE_MIGRATION")
            event.record_failure({"error": str(e), "file": file_name})
            return jsonify(event.to_dict()), 500
        
    logger.info("Migration Flask Routes Registered")
    return migration_routes 