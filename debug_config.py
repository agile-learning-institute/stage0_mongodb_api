#!/usr/bin/env python3
import os
import sys
from pathlib import Path
from configurator.utils.config import Config

def test_config_loading():
    """Test configuration loading from api_config files."""
    
    # Set up the input folder to point to large_sample
    os.environ['INPUT_FOLDER'] = './tests/test_cases/large_sample'
    os.environ['LOAD_TEST_DATA'] = 'true'
    
    # Debug: Check if the files exist
    input_folder = './tests/test_cases/large_sample'
    api_config_path = Path(input_folder, "api_config", "BUILT_AT")
    root_path = Path(input_folder, "BUILT_AT")
    
    print(f"Checking file paths:")
    print(f"  api_config_path: {api_config_path} (exists: {api_config_path.exists()})")
    print(f"  root_path: {root_path} (exists: {root_path.exists()})")
    
    if api_config_path.exists():
        print(f"  api_config_path content: '{api_config_path.read_text().strip()}'")
    
    # Reset the Config singleton
    Config._instance = None
    
    # Get the config instance
    config = Config.get_instance()
    
    # Print the configuration details
    print("\nConfiguration loaded:")
    print(f"BUILT_AT: {config.BUILT_AT}")
    print(f"ENABLE_DROP_DATABASE: {config.ENABLE_DROP_DATABASE}")
    print(f"INPUT_FOLDER: {config.INPUT_FOLDER}")
    print(f"LOAD_TEST_DATA: {config.LOAD_TEST_DATA}")
    
    print("\nConfig items:")
    for item in config.config_items:
        print(f"  {item['name']}: {item['value']} (from {item['from']})")
    
    # Test the to_dict method
    config_dict = config.to_dict()
    print(f"\nConfig.to_dict(): {config_dict}")

if __name__ == "__main__":
    test_config_loading() 