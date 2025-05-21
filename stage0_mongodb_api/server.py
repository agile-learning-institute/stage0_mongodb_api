import sys
import signal
from flask import Flask
from stage0_py_utils import Config, MongoIO, MongoJSONEncoder
from prometheus_flask_exporter import PrometheusMetrics

# Initialize Singletons
config = Config.get_instance()
mongo = MongoIO.get_instance()

# Initialize Logging
import logging
logger = logging.getLogger(__name__)
logger.info(f"============= Starting Server Initialization ===============")

# Initialize Flask App
app = Flask(__name__)
app.json = MongoJSONEncoder(app)

# Apply Prometheus monitoring middleware
metrics = PrometheusMetrics(app, path='/api/health')
metrics.info('app_info', 'Application info', version=config.BUILT_AT)

# Register flask routes
from stage0_py_utils import create_config_routes
from routes.collection_routes import create_collection_routes

app.register_blueprint(create_config_routes(), url_prefix='/api/config')
app.register_blueprint(create_collection_routes(), url_prefix='/api/collections')
logger.info(f"============= Routes Registered ===============")

# Define a signal handler for SIGTERM and SIGINT
def handle_exit(signum, frame):
    logger.info(f"Received signal {signum}. Initiating shutdown...")
    
    # Disconnect from MongoDB
    logger.info("Closing MongoDB connection.")
    mongo.disconnect()

    logger.info("Shutdown complete.")
    sys.exit(0)  

# Register the signal handler
signal.signal(signal.SIGTERM, handle_exit)
signal.signal(signal.SIGINT, handle_exit)

# Start the server
if __name__ == "__main__":
    logger.info(f"Starting Flask server on port {config.MONGODB_API_PORT}...")
    app.run(host="0.0.0.0", port=config.MONGODB_API_PORT)
    