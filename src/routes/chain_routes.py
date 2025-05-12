from stage0_py_utils import create_flask_breadcrumb, create_flask_token
from stage0_fran.services.chain_services import ChainServices
from flask import Blueprint, Response, jsonify, request

import logging
logger = logging.getLogger(__name__)


# Define the Blueprint for chain routes
def create_chain_routes():
    chain_routes = Blueprint('chain_routes', __name__)

    # GET /api/chain - Return a list of chains that match query
    @chain_routes.route('', methods=['GET'])
    def get_chains():
        try:
            token = create_flask_token()
            breadcrumb = create_flask_breadcrumb(token)
            chains = ChainServices.get_chains(token=token)
            logger.info(f"get_chains Success {str(breadcrumb["atTime"])}, {breadcrumb["correlationId"]}")
            return jsonify(chains), 200
        except Exception as e:
            logger.warning(f"get_chains Error has occurred: {e}")
            return jsonify({"error": "A processing error occurred"}), 500
        
    # GET /api/chain/{id} - Return a specific chain
    @chain_routes.route('/<string:id>', methods=['GET'])
    def get_chain(id):
        try:
            token = create_flask_token()
            breadcrumb = create_flask_breadcrumb(token)
            chain = ChainServices.get_chain(chain_id=id, token=token)
            logger.info(f"get_chain Success {str(breadcrumb["atTime"])}, {breadcrumb["correlationId"]}")
            return jsonify(chain), 200
        except Exception as e:
            logger.warning(f"get_chain Error has occurred: {e}")
            return jsonify({"error": "A processing error occurred"}), 500
        
    logger.info("Chain Flask Routes Registered")
    return chain_routes