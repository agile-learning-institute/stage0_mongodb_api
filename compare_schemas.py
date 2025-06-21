#!/usr/bin/env python3

import json
import os
import sys
from unittest.mock import MagicMock, patch

# Add current directory to path
sys.path.insert(0, '.')

from stage0_mongodb_api.managers.schema_manager import SchemaManager
from stage0_mongodb_api.managers.schema_types import SchemaFormat
from stage0_py_utils import Config

def load_bson(version_name: str) -> dict:
    """Helper method to load bson schema JSON files."""
    file_path = os.path.join("tests/test_cases/large_sample/expected/bson_schema", f"{version_name}.json")
    with open(file_path, 'r') as f:
        return json.load(f)

def main():
    # Set up config
    config = Config.get_instance()
    config.INPUT_FOLDER = os.path.join("tests/test_cases/large_sample")
    
    with patch('stage0_py_utils.MongoIO.get_instance') as mock_get_instance:
        mock_get_instance.return_value = MagicMock()
        
        # Set up schema manager
        schema_manager = SchemaManager()
        version_name = "organization.1.0.0.1"
        
        # Get rendered and expected schemas
        rendered_bson = schema_manager.render_one(version_name, SchemaFormat.BSON)
        expected_bson = load_bson(version_name)
        
        print("RENDERED:")
        print(json.dumps(rendered_bson, indent=2))
        print("\n" + "="*80 + "\n")
        print("EXPECTED:")
        print(json.dumps(expected_bson, indent=2))
        
        # Compare
        print("\n" + "="*80 + "\n")
        print("EQUAL:", rendered_bson == expected_bson)

if __name__ == "__main__":
    main() 