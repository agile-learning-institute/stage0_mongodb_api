from functools import wraps
from flask import jsonify
from configurator.utils.configurator_exception import ConfiguratorException, ConfiguratorEvent
import logging

logger = logging.getLogger(__name__)

def event_route(event_id: str, event_type: str, operation_name: str):
    """Decorator that only handles exceptions, routes handle their own serialization."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                result = f(*args, **kwargs)
                # Routes are responsible for their own serialization
                return result
            except ConfiguratorException as e:
                logger.error(f"Configurator error in {operation_name}: {str(e)}")
                event = ConfiguratorEvent(event_id=event_id, event_type=event_type)
                if hasattr(e, 'event') and e.event:
                    event.append_events([e.event])
                event.record_failure(f"Configurator error in {operation_name}")
                return jsonify(event.to_dict()), 500
            except Exception as e:
                logger.error(f"Unexpected error in {operation_name}: {str(e)}")
                event = ConfiguratorEvent(event_id=event_id, event_type=event_type)
                event.record_failure(f"Unexpected error in {operation_name}", {"details": str(e)})
                return jsonify(event.to_dict()), 500
        return wrapper
    return decorator 