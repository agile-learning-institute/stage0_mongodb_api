import json
import sys
import signal
from flask import Flask
from stage0_py_utils import Config, MongoIO, MongoJSONEncoder
from prometheus_flask_exporter import PrometheusMetrics
from stage0_mongodb_api.managers.config_manager import ConfigManager

# Initialize Singletons
config = Config.get_instance()
mongo = MongoIO.get_instance()

# Initialize Logging
import logging
logger = logging.getLogger(__name__)
logger.info(f"============= Starting Server Initialization ===============")

# Define a signal handler for SIGTERM and SIGINT
def handle_exit(signum, frame):
    logger.info(f"Received signal {signum}. Initiating shutdown...")
    
    # Disconnect from MongoDB
    logger.info("Closing MongoDB connection.")
    mongo.disconnect()

    logger.info("============= Shutdown complete. ===============")
    sys.exit(0)  

# Register the signal handler
signal.signal(signal.SIGTERM, handle_exit)
signal.signal(signal.SIGINT, handle_exit)

# Initialize Flask App
app = Flask(__name__)
app.json = MongoJSONEncoder(app)

# Configure Flask to be strict about trailing slashes
app.url_map.strict_slashes = False

# Auto-processing logic - runs when module is imported (including by Gunicorn)
if config.AUTO_PROCESS:
    logger.info(f"============= Auto Processing is Enabled ===============")
    config_manager = ConfigManager()
    
    # Check for load errors
    if len(config_manager.load_errors) > 0:
        logger.error(f"Auto Processing Failed to Load Configurations! {config_manager.load_errors}")
        sys.exit(1)

    # Check for schema validation errors
    validate_errors = config_manager.schema_manager.validate_schema()
    if len(validate_errors) > 0:
        logger.error(f"Auto Processing Failed to Validate Schema! {validate_errors}")
        sys.exit(1)

    # Process all collections
    processing_output = config_manager.process_all_collections()
    logger.info(f"Processing Output: {app.json.dumps(processing_output)}")
    logger.info(f"============= Auto Processing is Completed ===============")

if config.EXIT_AFTER_PROCESSING:
    logger.info(f"============= Exiting After Processing ===============")
    sys.exit(0)

# Apply Prometheus monitoring middleware
metrics = PrometheusMetrics(app, path='/api/health')
metrics.info('app_info', 'Application info', version=config.BUILT_AT)

# Register flask routes
from stage0_py_utils import create_config_routes
from stage0_mongodb_api.routes.collection_routes import create_collection_routes
from stage0_mongodb_api.routes.render_routes import create_render_routes

app.register_blueprint(create_config_routes(), url_prefix='/api/config')
app.register_blueprint(create_collection_routes(), url_prefix='/api/collections')
app.register_blueprint(create_render_routes(), url_prefix='/api/render')
logger.info(f"============= Routes Registered ===============")
# Start the server (only when run directly, not when imported by Gunicorn)
if __name__ == "__main__":
    logger.info(f"============= Starting Server ===============")
    logger.info(f"Starting Flask server on port {config.MONGODB_API_PORT}...")
    app.run(host="0.0.0.0", port=config.MONGODB_API_PORT)
    