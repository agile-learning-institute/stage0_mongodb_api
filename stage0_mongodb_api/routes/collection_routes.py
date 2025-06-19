from flask import Blueprint, jsonify, request
from stage0_mongodb_api.services.collection_service import CollectionService, CollectionNotFoundError, CollectionProcessingError
from stage0_py_utils import create_flask_breadcrumb, create_flask_token
import logging

logger = logging.getLogger(__name__)

def create_collection_routes():
    blueprint = Blueprint('collections', __name__)

    @blueprint.route('/', methods=['GET'])
    def list_collections():
        """List all configured collections"""
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        try:
            collections = CollectionService.list_collections(token)
            logger.info(f"{breadcrumb} Successfully listed collections")
            return jsonify(collections)
        except CollectionProcessingError as e:
            logger.error(f"{breadcrumb} Error listing collections: {str(e)}")
            return jsonify(e.errors), 500
        except Exception as e:
            logger.error(f"{breadcrumb} Unexpected error listing collections: {str(e)}")
            return jsonify([{
                "error": "Failed to list collections",
                "error_id": "API-001",
                "message": str(e)
            }]), 500

    @blueprint.route('/', methods=['POST'])
    def process_collections():
        """Process all configured collections"""
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        try:
            result = CollectionService.process_collections(token)
            logger.info(f"{breadcrumb} Successfully processed collections")
            return jsonify(result)
        except CollectionProcessingError as e:
            logger.error(f"{breadcrumb} Error processing collections: {str(e)}")
            return jsonify(e.errors), 500
        except Exception as e:
            logger.error(f"{breadcrumb} Unexpected error processing collections: {str(e)}")
            return jsonify([{
                "error": "Failed to process collections",
                "error_id": "API-002",
                "message": str(e)
            }]), 500

    @blueprint.route('/<collection_name>', methods=['GET'])
    def get_collection(collection_name):
        """Get a specific collection configuration"""
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        try:
            result = CollectionService.get_collection(collection_name, token)
            logger.info(f"{breadcrumb} Successfully retrieved collection: {collection_name}")
            return jsonify(result)
        except CollectionNotFoundError:
            logger.warning(f"{breadcrumb} Collection not found: {collection_name}")
            return "Collection not found", 404
        except CollectionProcessingError as e:
            logger.error(f"{breadcrumb} Error getting collection {collection_name}: {str(e)}")
            return jsonify(e.errors), 500
        except Exception as e:
            logger.error(f"{breadcrumb} Unexpected error getting collection {collection_name}: {str(e)}")
            return jsonify([{
                "error": "Failed to get collection",
                "error_id": "API-003",
                "message": str(e)
            }]), 500

    @blueprint.route('/<collection_name>', methods=['POST'])
    def process_collection(collection_name):
        """Process a specific collection"""
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        try:
            result = CollectionService.process_collection(collection_name, token)
            logger.info(f"{breadcrumb} Successfully processed collection: {collection_name}")
            return jsonify(result)
        except CollectionNotFoundError:
            logger.warning(f"{breadcrumb} Collection not found: {collection_name}")
            return "Collection not found", 404
        except CollectionProcessingError as e:
            logger.error(f"{breadcrumb} Error processing collection {collection_name}: {str(e)}")
            return jsonify(e.errors), 500
        except Exception as e:
            logger.error(f"{breadcrumb} Unexpected error processing collection {collection_name}: {str(e)}")
            return jsonify([{
                "error": "Failed to process collection",
                "error_id": "API-004",
                "message": str(e)
            }]), 500

    logger.info("Collection Flask Routes Registered")
    return blueprint 