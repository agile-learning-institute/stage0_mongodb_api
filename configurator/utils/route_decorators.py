from functools import wraps
from flask import jsonify
from configurator.utils.configurator_exception import ConfiguratorException
import logging

logger = logging.getLogger(__name__)

def handle_errors(operation_name: str):
    """Decorator to handle common error patterns in routes."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except ConfiguratorException as e:
                logger.error(f"Configurator error in {operation_name}: {str(e)}")
                return jsonify(e.event.to_dict()), 500
            except Exception as e:
                logger.error(f"Unexpected error in {operation_name}: {str(e)}")
                return jsonify(str(e)), 500
        return wrapper
    return decorator 