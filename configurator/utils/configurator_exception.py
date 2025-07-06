import datetime

class ConfiguratorEvent:
    def __init__(self, event_id: str, event_type: str, event_data: dict = None):
        self.id = event_id
        self.type = event_type
        self.data = event_data
        self.starts = datetime.datetime.now()
        self.ends = None
        self.status = "PENDING"
        self.sub_events = []
    
    def append_events(self, events: list):
        self.sub_events.extend(events)
        
    def record_success(self):
        self.status = "SUCCESS"
        self.ends = datetime.datetime.now()
            
    def record_failure(self, message: str, event_data: object = {}):
        self.data = {"error": message, **(event_data if isinstance(event_data, dict) else {})}
        self.status = "FAILURE"
        self.ends = datetime.datetime.now()
        
    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "data": self.data,
            "starts": self.starts,
            "ends": self.ends,
            "status": self.status,
            "sub_events": [event.to_dict() for event in self.sub_events]
        }


class ConfiguratorException(Exception):
    def __init__(self, message: str, event: ConfiguratorEvent):
        self.message = message
        self.event = event

    def __str__(self):
        return self.message
        
    def to_dict(self):
        return {
            "message": self.message,
            "event": self.event.to_dict() if self.event else None
        }