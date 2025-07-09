#!/usr/bin/env python3

import os
import json
from configurator.services.configuration_services import Configuration
from configurator.utils.config import Config

# Set up environment for large_sample
os.environ['INPUT_FOLDER'] = './tests/test_cases/large_sample'
Config._instance = None
config = Config.get_instance()

# Get the BSON schema for user version 1.0.0.1
configuration = Configuration('user.yaml')
schema = configuration.get_bson_schema_for_version('1.0.0.1')

print("=== RENDERED BSON SCHEMA ===")
print(json.dumps(schema, indent=2))

# Check if there's any $and operator in the schema
def find_and_operator(obj, path=""):
    if isinstance(obj, dict):
        for key, value in obj.items():
            current_path = f"{path}.{key}" if path else key
            if key == "$and":
                print(f"FOUND $and at {current_path}: {value}")
            find_and_operator(value, current_path)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            current_path = f"{path}[{i}]"
            find_and_operator(item, current_path)

print("\n=== CHECKING FOR $and OPERATORS ===")
find_and_operator(schema) 