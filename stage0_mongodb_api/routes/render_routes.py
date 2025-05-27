from flask import Blueprint, jsonify, request
import yaml
from stage0_mongodb_api.services.render_service import CollectionService, RenderService

def create_render_routes():
    blueprint = Blueprint('renders', __name__)
    render_service = RenderService()

    @blueprint.route('json_schema/<collection_name>', methods=['GET'])
    def render_json_schema(collection_name):
        """Render Json Schema for a collection"""
        schema = render_service.render_json_schema(collection_name)
        return jsonify(schema)

    @blueprint.route('bson_schema/<collection_name>', methods=['GET'])
    def render_bson_schema(collection_name):
        """Render Bson Schema for a collection"""
        schema = render_service.render_bson_schema(collection_name)
        return jsonify(schema)

    @blueprint.route('openapi/<collection_name>', methods=['GET'])
    def render_openapi(collection_name):
        """Render OpenAPI for a collection"""
        openapi = render_service.render_bson_schema(collection_name)
        return yaml.dump(openapi)

    return blueprint 