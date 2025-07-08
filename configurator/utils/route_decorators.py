from functools import wraps
from flask import jsonify
from configurator.utils.configurator_exception import ConfiguratorException, ConfiguratorEvent
import logging

logger = logging.getLogger(__name__)

def event_route(event_id: str, event_type: str, operation_name: str):
    """Unified decorator to wrap all route responses in a ConfiguratorEvent, with sub_events if needed."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            event = ConfiguratorEvent(event_id=event_id, event_type=event_type)
            try:
                result = f(*args, **kwargs)
                # If result is a list of ConfiguratorEvent, add as sub_events
                if isinstance(result, list) and all(isinstance(e, ConfiguratorEvent) for e in result):
                    event.append_events(result)
                # If result is a dict or other data, set as event data
                elif result is not None:
                    event.data = result
                event.record_success()
                return jsonify(event.to_dict()), 200
            except ConfiguratorException as e:
                logger.error(f"Configurator error in {operation_name}: {str(e)}")
                if hasattr(e, 'event') and e.event:
                    event.append_events([e.event])
                event.record_failure(f"Configurator error in {operation_name}")
                return jsonify(event.to_dict()), 500
            except Exception as e:
                logger.error(f"Unexpected error in {operation_name}: {str(e)}")
                event.record_failure(f"Unexpected error in {operation_name}")
                return jsonify(event.to_dict()), 500
        return wrapper
    return decorator 