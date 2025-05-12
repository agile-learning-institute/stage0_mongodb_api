from stage0_py_utils import create_flask_breadcrumb, create_flask_token
from stage0_fran.services.workshop_services import WorkshopServices
from flask import Blueprint, Response, jsonify, request

import logging
logger = logging.getLogger(__name__)


# Define the Blueprint for workshop routes
def create_workshop_routes():
    workshop_routes = Blueprint('workshop_routes', __name__)

    # GET /api/workshop - Return a list of workshops that match query
    @workshop_routes.route('', methods=['GET'])
    def get_workshops():
        try:
            token = create_flask_token()
            breadcrumb = create_flask_breadcrumb(token)
            query = request.args.get('query') or ""
            workshops = WorkshopServices.get_workshops(query=query, token=token)
            logger.info(f"get_workshops Success {query}{str(breadcrumb["atTime"])}, {breadcrumb["correlationId"]}")   
            return jsonify(workshops), 200
        except Exception as e:
            logger.warning(f"get_workshops Error has occurred: {e}")
            return jsonify({"error": "A processing error occurred"}), 500
        
    # GET /api/workshop/id - Return a specific workshop
    @workshop_routes.route('/<string:id>', methods=['GET'])
    def get_workshop(id):
        try:
            token = create_flask_token()
            breadcrumb = create_flask_breadcrumb(token)
            workshop = WorkshopServices.get_workshop(workshop_id=id, token=token)
            logger.info(f"get_workshop Success {str(breadcrumb["atTime"])}, {breadcrumb["correlationId"]}")
            return jsonify(workshop), 200
        except Exception as e:
            logger.warning(f"get_workshop Error has occurred: {e}")
            return jsonify({"error": "A processing error occurred"}), 500

    # POST /api/workshop/new/{chain} - Add a new workshop from the chain
    @workshop_routes.route('new/<string:chain>', methods=['POST'])
    def add_workshop(chain):
        try:
            token = create_flask_token()
            breadcrumb = create_flask_breadcrumb(token)
            workshop_data = request.get_json()
            workshop = WorkshopServices.add_workshop(chain_id=chain, data=workshop_data, token=token, breadcrumb=breadcrumb)
            logger.info(f"add_workshop Success {str(breadcrumb["atTime"])}, {breadcrumb["correlationId"]}")
            return jsonify(workshop), 200
        except Exception as e:
            logger.warning(f"add_workshop Error has occurred: {e}")
            return jsonify({"error": "A processing error occurred"}), 500
        
    # PATCH /api/workshop/{id} - Update a workshop
    @workshop_routes.route('/<string:id>', methods=['PATCH'])
    def update_workshop(id):
        try:
            token = create_flask_token()
            breadcrumb = create_flask_breadcrumb(token)
            patch_data = request.get_json()
            workshop = WorkshopServices.update_workshop(workshop_id=id, data=patch_data, token=token, breadcrumb=breadcrumb)
            logger.info(f"update_workshop Successful {str(breadcrumb["atTime"])}, {breadcrumb["correlationId"]}")
            return jsonify(workshop), 200
        except Exception as e:
            logger.warning(f"update_workshop A processing error occurred {e}")
            return jsonify({"error": "A processing error occurred"}), 500
        
    # POST /api/workshop/{id}/start - Update a workshop status
    @workshop_routes.route('/<string:id>/start', methods=['POST'])
    def start_workshop(id):
        try:
            token = create_flask_token()
            breadcrumb = create_flask_breadcrumb(token)
            workshop = WorkshopServices.start_workshop(workshop_id=id, token=token, breadcrumb=breadcrumb)
            logger.info(f"start_workshop Successful {str(breadcrumb["atTime"])}, {breadcrumb["correlationId"]}")
            return jsonify(workshop), 200
        except Exception as e:
            logger.warning(f"start_workshop A processing error occurred {e}")
            return jsonify({"error": "A processing error occurred"}), 500
        
    # POST /api/workshop/{id}/next - Update a workshop, advance current_exercise
    @workshop_routes.route('/<string:id>/next', methods=['POST'])
    def advance_workshop(id):
        try:
            token = create_flask_token()
            breadcrumb = create_flask_breadcrumb(token)
            workshop = WorkshopServices.advance_workshop(workshop_id=id, token=token, breadcrumb=breadcrumb)
            logger.info(f"advance_workshop Successful {str(breadcrumb["atTime"])}, {breadcrumb["correlationId"]}")
            return jsonify(workshop), 200
        except Exception as e:
            logger.warning(f"advance_workshop A processing error occurred {e}")
            return jsonify({"error": "A processing error occurred"}), 500
        
    # POST /api/workshop/{id}/observation - Add a observation to a workshop
    @workshop_routes.route('/<string:id>/observation', methods=['POST'])
    def add_observation(id):
        try:
            token = create_flask_token()
            breadcrumb = create_flask_breadcrumb(token)
            observation = request.get_json()
            workshop = WorkshopServices.add_observation(workshop_id=id, observation=observation, token=token, breadcrumb=breadcrumb)
            logger.info(f"add_observation to workshop Successful {str(breadcrumb["atTime"])}, {breadcrumb["correlationId"]}")
            return jsonify(workshop), 200
        except Exception as e:
            logger.warning(f"add_observation A processing error occurred {e}")
            return jsonify({"error": "A processing error occurred"}), 500
                
    logger.info("Workshop Flask Routes Registered")
    return workshop_routes