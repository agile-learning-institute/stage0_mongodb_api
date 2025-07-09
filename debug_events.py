#!/usr/bin/env python3

import os
from configurator.services.configuration_services import Configuration
from configurator.utils.config import Config
from configurator.utils.mongo_io import MongoIO

# Set up environment for large_sample
os.environ['INPUT_FOLDER'] = './tests/test_cases/large_sample'
Config._instance = None
config = Config.get_instance()

print(f"BUILT_AT: {config.BUILT_AT}")
print(f"ENABLE_DROP_DATABASE: {config.ENABLE_DROP_DATABASE}")

# Drop database first
mongo_io = MongoIO(config.MONGO_CONNECTION_STRING, config.MONGO_DB_NAME)
mongo_io.drop_database()
mongo_io.disconnect()

print("Database dropped. Starting processing...")

# Process user.yaml
configuration = Configuration('user.yaml')
event = configuration.process()

def print_event(event, indent=0):
    prefix = "  " * indent
    print(f"{prefix}Event {event.type}: {event.status}")
    if event.data:
        print(f"{prefix}  Data: {event.data}")
    for sub_event in event.sub_events:
        print_event(sub_event, indent + 1)

print("=== EVENT STRUCTURE ===")
print_event(event) 