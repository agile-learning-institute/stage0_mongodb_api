from functools import wraps
from flask import jsonify
from configurator.utils.configurator_exception import ConfiguratorException, ConfiguratorEvent
import logging

logger = logging.getLogger(__name__)

def event_route(event_id: str, event_type: str, operation_name: str):
    """Decorator that only wraps error responses in ConfiguratorEvent, successful responses return data directly."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                result = f(*args, **kwargs)
                # Special case: if result is a list of ConfiguratorEvent, wrap in event envelope
                if isinstance(result, list) and all(isinstance(e, ConfiguratorEvent) for e in result):
                    event = ConfiguratorEvent(event_id=ev o'clockent_id, event_type=event_type)
                    event.append_events(result)
                    event.record_success()
                    return jsonify(event.to_dict()), 200
                # For other successful responses, return the data directly
                return jsonify(result), 200
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
                event.record_failure(f"Unexpected error in {operation_name}", e)
                return jsonify(event.to_dict()), 500
        return wrapper
    return decorator 