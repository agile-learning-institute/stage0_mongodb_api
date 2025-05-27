from flask import Blueprint, jsonify, request
from stage0_mongodb_api.services.collection_service import CollectionService

def create_collection_routes():
    blueprint = Blueprint('collections', __name__)

    @blueprint.route('', methods=['GET'])
    def list_collections():
        """List all configured collections"""
        collection_service = CollectionService()
        collections = collection_service.list_collections()
        return jsonify(collections)

    @blueprint.route('', methods=['POST'])
    def process_collections():
        """Process all configured collections"""
        collection_service = CollectionService()
        result = collection_service.process_collections()
        return jsonify(result)

    @blueprint.route('/<collection_name>', methods=['POST'])
    def process_collection(collection_name):
        """Process a specific collection"""
        collection_service = CollectionService()
        result = collection_service.process_collection(collection_name)
        return jsonify(result)

    return blueprint 