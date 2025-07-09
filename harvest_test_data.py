#!/usr/bin/env python3
import os
import json
import tempfile
from pathlib import Path
from configurator.utils.config import Config
from configurator.utils.mongo_io import MongoIO
from configurator.services.configuration_services import Configuration
from bson import json_util

def harvest_test_data(test_case='large_sample'):
    """Harvest test data after processing for manual review."""
    
    # Set up environment
    os.environ['INPUT_FOLDER'] = f'./tests/test_cases/{test_case}'
    os.environ['LOAD_TEST_DATA'] = 'true'
    
    # Reset Config singleton
    Config._instance = None
    config = Config.get_instance()
    
    print(f"Processing test case: {test_case}")
    print(f"INPUT_FOLDER: {config.INPUT_FOLDER}")
    print(f"BUILT_AT: {config.BUILT_AT}")
    print(f"ENABLE_DROP_DATABASE: {config.ENABLE_DROP_DATABASE}")
    print()
    
    # Drop database to start clean
    mongo_io = MongoIO(config.MONGO_CONNECTION_STRING, config.MONGO_DB_NAME)
    mongo_io.drop_database()
    mongo_io.disconnect()
    
    print("Database dropped. Starting processing...")
    print()
    
    # Process all configurations
    config_dir = f"{config.INPUT_FOLDER}/configurations"
    config_files = [f for f in os.listdir(config_dir) if f.endswith('.yaml')]
    
    # For large_sample, process in dependency order
    if test_case == 'large_sample':
        dependency_order = [
            'media.yaml', 
            'organization.yaml',
            'user.yaml',
            'notification.yaml',
            'content.yaml',
            'search.yaml'
        ]
        ordered_files = [f for f in dependency_order if f in config_files]
        remaining_files = [f for f in config_files if f not in dependency_order]
        ordered_files.extend(remaining_files)
    else:
        ordered_files = sorted(config_files)
    
    # Process each configuration
    for filename in ordered_files:
        print(f"Processing {filename}...")
        try:
            configuration = Configuration(filename)
            event = configuration.process()
            
            print(f"  Status: {event.status}")
            for sub_event in event.sub_events:
                print(f"    {sub_event.type}: {sub_event.status}")
                if hasattr(sub_event, 'data') and sub_event.data:
                    print(f"      Data: {sub_event.data}")
            
            if event.status == "FAILURE":
                print(f"  ERROR: Processing failed for {filename}")
                return False
                
        except Exception as e:
            print(f"  ERROR: Exception processing {filename}: {str(e)}")
            return False
    
    print()
    print("Processing complete. Harvesting data...")
    
    # Harvest all collections
    mongo_io = MongoIO(config.MONGO_CONNECTION_STRING, config.MONGO_DB_NAME)
    
    # Get all collection names
    collection_names = mongo_io.db.list_collection_names()
    print(f"Found collections: {collection_names}")
    
    harvested_data = {}
    
    # Harvest each collection
    for collection_name in collection_names:
        try:
            documents = mongo_io.get_documents(collection_name, sort_by=[("_id", 1)])
            # Convert to Extended JSON format
            json_docs = json.loads(json_util.dumps(documents))
            harvested_data[collection_name] = json_docs
            print(f"Harvested {len(json_docs)} documents from {collection_name}")
        except Exception as e:
            print(f"Error harvesting {collection_name}: {e}")
            harvested_data[collection_name] = []
    
    mongo_io.disconnect()
    
    # Save harvested data to file
    output_file = f"harvested_{test_case}_data.json"
    with open(output_file, 'w') as f:
        json.dump(harvested_data, f, indent=2, default=str)
    
    print(f"\nHarvested data saved to: {output_file}")
    
    # Print summary
    print("\nSummary:")
    for collection_name, documents in harvested_data.items():
        print(f"  {collection_name}: {len(documents)} documents")
    
    return True

if __name__ == "__main__":
    # Test with large_sample
    success = harvest_test_data('large_sample')
    if success:
        print("\nHarvesting completed successfully!")
    else:
        print("\nHarvesting failed!") 