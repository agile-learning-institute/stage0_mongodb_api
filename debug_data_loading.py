#!/usr/bin/env python3
import os
import json
from configurator.utils.config import Config
from configurator.utils.mongo_io import MongoIO
from bson import json_util

def test_data_loading():
    """Test data loading directly."""
    
    # Set up environment
    os.environ['INPUT_FOLDER'] = './tests/test_cases/large_sample'
    os.environ['LOAD_TEST_DATA'] = 'true'
    
    # Reset Config singleton
    Config._instance = None
    config = Config.get_instance()
    
    print(f"Testing data loading...")
    print(f"BUILT_AT: {config.BUILT_AT}")
    print(f"ENABLE_DROP_DATABASE: {config.ENABLE_DROP_DATABASE}")
    
    # Drop database
    mongo_io = MongoIO(config.MONGO_CONNECTION_STRING, config.MONGO_DB_NAME)
    mongo_io.drop_database()
    
    # Test loading organization data
    data_file = "./tests/test_cases/large_sample/test_data/organization.1.0.0.1.json"
    
    print(f"\nLoading data from: {data_file}")
    
    # Check if file exists
    if not os.path.exists(data_file):
        print(f"ERROR: File does not exist: {data_file}")
        return
    
    # Read and parse the file
    with open(data_file, 'r') as f:
        content = f.read()
        print(f"File content length: {len(content)}")
        print(f"First 200 chars: {content[:200]}")
    
    try:
        # Parse with json_util
        data = json_util.loads(content)
        print(f"Parsed {len(data)} documents")
        print(f"First document: {data[0] if data else 'None'}")
        
        # Try to insert
        collection = mongo_io.get_collection("organization")
        result = collection.insert_many(data)
        print(f"Inserted {len(result.inserted_ids)} documents")
        
        # Check what's in the collection
        docs = collection.find()
        doc_list = list(docs)
        print(f"Collection now has {len(doc_list)} documents")
        if doc_list:
            print(f"First doc in collection: {doc_list[0]}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    mongo_io.disconnect()

if __name__ == "__main__":
    test_data_loading() 