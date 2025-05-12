import sys
import signal
import threading
from werkzeug.serving import make_server

# Initialize Singletons
from stage0_py_utils import Config, MongoIO
config = Config.get_instance()
mongo = MongoIO.get_instance()

# Initialize Logging
import logging
logger = logging.getLogger(__name__)
logger.info(f"============= Starting Server Initialization ===============")

# Initialize Echo Discord Bot
from stage0_py_utils import Echo
from stage0_py_utils import OllamaLLMClient
llm_client = OllamaLLMClient(base_url=config.OLLAMA_HOST, model=config.FRAN_MODEL_NAME)
echo = Echo("Fran", bot_id=config.FRAN_BOT_ID, model=config.FRAN_MODEL_NAME, client=llm_client)

# Register Agents
from stage0_py_utils import create_config_agent
from stage0_fran.agents.chain_agent import create_chain_agent
from stage0_fran.agents.exercise_agent import create_exercise_agent
from stage0_fran.agents.workshop_agent import create_workshop_agent

echo.register_agent(create_config_agent(agent_name="config"))
echo.register_agent(create_chain_agent(agent_name="chain"))
echo.register_agent(create_exercise_agent(agent_name="exercise"))
echo.register_agent(create_workshop_agent(agent_name="workshop"))
logger.info(f"============= Agents Initialized ===============")

# Initialize Flask App
from flask import Flask
from stage0_py_utils import MongoJSONEncoder
from prometheus_flask_exporter import PrometheusMetrics
app = Flask(__name__)
app.json = MongoJSONEncoder(app)

# Apply Prometheus monitoring middleware
metrics = PrometheusMetrics(app, path='/api/health/')
metrics.info('app_info', 'Application info', version=config.BUILT_AT)

# Register flask routes
from stage0_py_utils import create_config_routes
from stage0_fran.routes.chain_routes import create_chain_routes
from stage0_fran.routes.exercise_routes import create_exercise_routes
from stage0_fran.routes.workshop_routes import create_workshop_routes

echo.register_default_routes(app=app)
app.register_blueprint(create_config_routes(), url_prefix='/api/config')
app.register_blueprint(create_chain_routes(), url_prefix='/api/chain')
app.register_blueprint(create_exercise_routes(), url_prefix='/api/exercise')
app.register_blueprint(create_workshop_routes(), url_prefix='/api/workshop')
logger.info(f"============= Routes Registered ===============")

# Flask server run's in it's own thread
server = make_server("0.0.0.0", config.FRAN_API_PORT, app)
flask_thread = threading.Thread(target=server.serve_forever)

# Define a signal handler for SIGTERM and SIGINT
def handle_exit(signum, frame):
    logger.info(f"Received signal {signum}. Initiating shutdown...")

    # Shutdown Flask gracefully
    if flask_thread.is_alive():
        logger.info("Stopping Flask server...")
        server.shutdown()
        flask_thread.join()

    # Disconnect from MongoDB
    logger.info("Closing MongoDB connection.")
    mongo.disconnect()

    # Close the Discord bot
    logger.info("Closing Discord connection.")
    echo.close(timeout=0.1) # TODO Add DISCORD_TIMEOUT config value with this default value

    logger.info("Shutdown complete.")
    sys.exit(0)  

# Register the signal handler
signal.signal(signal.SIGTERM, handle_exit)
signal.signal(signal.SIGINT, handle_exit)

# Start the bot and expose the app object for Gunicorn
if __name__ == "__main__":
    flask_thread.start()
    logger.info("Flask server started.")

    # Run Discord bot in the main thread
    echo.run(token=config.DISCORD_FRAN_TOKEN)
    