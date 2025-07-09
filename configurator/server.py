import json
import sys
import signal

# Initialize Singletons
from configurator.services.configuration_services import Configuration
from configurator.utils.config import Config
from configurator.utils.configurator_exception import ConfiguratorException
from configurator.utils.file_io import FileIO
config = Config.get_instance()

# Initialize Logging
import logging
logger = logging.getLogger(__name__)
logger.info(f"============= Starting Server Initialization ===============")

# Define a signal handler for SIGTERM and SIGINT
def handle_exit(signum, frame):
    logger.info(f"Received signal {signum}. Initiating shutdown...")
    
    logger.info("============= Shutdown complete. ===============")
    sys.exit(0)  

# Register the signal handler
signal.signal(signal.SIGTERM, handle_exit)
signal.signal(signal.SIGINT, handle_exit)

# Initialize Flask App
from flask import Flask
from configurator.utils.ejson_encoder import MongoJSONEncoder
app = Flask(__name__)
app.json = MongoJSONEncoder(app)

# Auto-processing logic - runs when module is imported (including by Gunicorn)
if config.AUTO_PROCESS:
    try:
        logger.info(f"============= Auto Processing is Starting ===============")
        processing_events = []
        configurations = FileIO.get_documents(config.CONFIGURATION_FOLDER)
        for configuration_name in configurations:
            configuration = Configuration(configuration_name)
            processing_events.append(configuration.process())
        logger.info(f"Processing Output: {app.json.dumps(processing_events)}")
        logger.info(f"============= Auto Processing is Completed ===============")
    except ConfiguratorException as e:
        logger.error(f"Configurator error processing all configurations: {app.json.dumps(e.to_dict())}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error processing all configurations: {str(e)}") 
        sys.exit(1)

if config.EXIT_AFTER_PROCESSING:
    logger.info(f"============= Exiting After Processing ===============")
    sys.exit(0)

# Apply Prometheus monitoring middleware
from prometheus_flask_exporter import PrometheusMetrics
metrics = PrometheusMetrics(app, path='/api/health')
metrics.info('app_info', 'Application info', version=config.BUILT_AT)

# Register flask routes
from configurator.routes.config_routes import create_config_routes
from configurator.routes.configuration_routes import create_configuration_routes
from configurator.routes.dictionary_routes import create_dictionary_routes
from configurator.routes.type_routes import create_type_routes
from configurator.routes.test_data_routes import create_test_data_routes
from configurator.routes.database_routes import create_database_routes
from configurator.routes.enumerator_routes import create_enumerator_routes
from configurator.routes.migration_routes import create_migration_routes

app.register_blueprint(create_config_routes(), url_prefix='/api/config')
app.register_blueprint(create_configuration_routes(), url_prefix='/api/configurations')
app.register_blueprint(create_dictionary_routes(), url_prefix='/api/dictionaries')
app.register_blueprint(create_type_routes(), url_prefix='/api/types')
app.register_blueprint(create_test_data_routes(), url_prefix='/api/test_data')
app.register_blueprint(create_database_routes(), url_prefix='/api/database')
app.register_blueprint(create_enumerator_routes(), url_prefix='/api/enumerators')
app.register_blueprint(create_migration_routes(), url_prefix='/api/migrations')
logger.info(f"============= Routes Registered ===============")

# Start the server (only when run directly, not when imported by Gunicorn)
if __name__ == "__main__":
    logger.info(f"============= Starting Server ===============")
    logger.info(f"Starting Flask server on port {config.API_PORT}...")
    app.run(host="0.0.0.0", port=config.API_PORT)
    