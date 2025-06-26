from flask import Blueprint, jsonify, request
import yaml
from stage0_mongodb_api.managers.config_manager import ConfigManager
from stage0_mongodb_api.services.render_service import RenderService, RenderNotFoundError, RenderProcessingError
from stage0_py_utils import create_flask_breadcrumb, create_flask_token
import logging

logger = logging.getLogger(__name__)

def create_render_routes():
    blueprint = Blueprint('renders', __name__)

    @blueprint.route('json_schema/<schema_name>/', methods=['GET'])
    def render_json_schema(schema_name):
        """Render Json Schema for a schema"""
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        try:
            schema = RenderService.render_json_schema(schema_name, token)
            logger.info(f"{breadcrumb} Successfully rendered JSON schema for: {schema_name}")
            return jsonify(schema)
        except RenderNotFoundError:
            logger.warning(f"{breadcrumb} Schema not found for JSON schema rendering: {schema_name}")
            return "Schema not found", 404
        except RenderProcessingError as e:
            logger.error(f"{breadcrumb} Error rendering JSON schema for {schema_name}: {str(e)}")
            return jsonify(e.errors), 500
        except Exception as e:
            logger.error(f"{breadcrumb} Unexpected error rendering JSON schema for {schema_name}: {str(e)}")
            return jsonify([{
                "error": "Failed to render JSON schema",
                "error_id": "API-005",
                "message": str(e)
            }]), 500

    @blueprint.route('bson_schema/<schema_name>/', methods=['GET'])
    def render_bson_schema(schema_name):
        """Render Bson Schema for a schema"""
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        try:
            schema = RenderService.render_bson_schema(schema_name, token)
            logger.info(f"{breadcrumb} Successfully rendered BSON schema for: {schema_name}")
            return jsonify(schema)
        except RenderNotFoundError:
            logger.warning(f"{breadcrumb} Schema not found for BSON schema rendering: {schema_name}")
            return "Schema not found", 404
        except RenderProcessingError as e:
            logger.error(f"{breadcrumb} Error rendering BSON schema for {schema_name}: {str(e)}")
            return jsonify(e.errors), 500
        except Exception as e:
            logger.error(f"{breadcrumb} Unexpected error rendering BSON schema for {schema_name}: {str(e)}")
            return jsonify([{
                "error": "Failed to render BSON schema",
                "error_id": "API-006",
                "message": str(e)
            }]), 500

    @blueprint.route('openapi/<schema_name>/', methods=['GET'])
    def render_openapi(schema_name):
        """Render OpenAPI for a schema"""
        token = create_flask_token()
        breadcrumb = create_flask_breadcrumb(token)
        
        try:
            openapi = RenderService.render_openapi(schema_name, token)
            logger.info(f"{breadcrumb} Successfully rendered OpenAPI for: {schema_name}")
            return yaml.dump(openapi)
        except RenderNotFoundError:
            logger.warning(f"{breadcrumb} Schema not found for OpenAPI rendering: {schema_name}")
            return "Schema not found", 404
        except RenderProcessingError as e:
            logger.error(f"{breadcrumb} Error rendering OpenAPI for {schema_name}: {str(e)}")
            return jsonify(e.errors), 500
        except Exception as e:
            logger.error(f"{breadcrumb} Unexpected error rendering OpenAPI for {schema_name}: {str(e)}")
            return jsonify([{
                "error": "Failed to render OpenAPI",
                "error_id": "API-007",
                "message": str(e)
            }]), 500

    logger.info("Render Flask Routes Registered")
    return blueprint 