import os
import json
from pathlib import Path

import logging
logger = logging.getLogger(__name__)

class Config:
    _instance = None  # Singleton instance

    def __init__(self):
        if Config._instance is not None:
            raise Exception("This class is a singleton!")
        else:
            Config._instance = self
            self.config_items = []
            self.INPUT_FOLDER = "./input"
            
            # Declare instance variables to support IDE code assist
            self.BUILT_AT = ''
            self.LOGGING_LEVEL = ''
            self.MONGO_DB_NAME = ''
            self.MONGO_CONNECTION_STRING = ''
            self.ENUMERATORS_COLLECTION_NAME = ''
            self.VERSION_COLLECTION_NAME = ''
            self.TYPE_FOLDER = ''
            self.DICTIONARY_FOLDER = ''
            self.CONFIGURATION_FOLDER = ''
            self.TEST_DATA_FOLDER = ''
            self.API_PORT = 0
            self.SPA_PORT = 0
            self.AUTO_PROCESS = False
            self.EXIT_AFTER_PROCESSING = False
            self.LOAD_TEST_DATA = False
            self.ENABLE_DROP_DATABASE = False
            self.RENDER_STACK_MAX_DEPTH = 0
    
            # Default Values grouped by value type            
            self.config_strings = {
                "BUILT_AT": "DEFAULT! Set in code",
                "INPUT_FOLDER": "/input",
                "LOGGING_LEVEL": "INFO", 
                "MONGO_DB_NAME": "configurator",
                "VERSION_COLLECTION_NAME": "CollectionVersions",
                "TYPE_FOLDER": "types",
                "DICTIONARY_FOLDER": "dictionaries",
                "CONFIGURATION_FOLDER": "configurations",
                "TEST_DATA_FOLDER": "test_data"
            }
            self.config_ints = {
                "API_PORT": "8081",
                "SPA_PORT": "8082",
                "RENDER_STACK_MAX_DEPTH": "100",
            }
            self.config_booleans = {
                "AUTO_PROCESS": "false",
                "EXIT_AFTER_PROCESSING": "false",
                "LOAD_TEST_DATA": "false",
                "ENABLE_DROP_DATABASE": "false",
            }            
            self.config_string_secrets = {  
                "MONGO_CONNECTION_STRING": "mongodb://mongodb:27017/"
            }

            # Initialize configuration
            self.initialize()
            self.configure_logging()

    def initialize(self):
        """Initialize configuration values."""
        self.config_items = []

        # Initialize Config Strings
        for key, default in self.config_strings.items():
            value = self._get_config_value(key, default, False)
            setattr(self, key, value)
            
        # Initialize Config Integers
        for key, default in self.config_ints.items():
            value = int(self._get_config_value(key, default, False))
            setattr(self, key, value)
            
        # Initialize Config Booleans
        for key, default in self.config_booleans.items():
            value = (self._get_config_value(key, default, False)).lower() == "true"
            setattr(self, key, value)
            
        # Initialize String Secrets
        for key, default in self.config_string_secrets.items():
            value = self._get_config_value(key, default, True)
            setattr(self, key, value)
        
        return

    def configure_logging(self):        
        # Reset logging handlers
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        # Configure logger
        logging.basicConfig(
            level=self.LOGGING_LEVEL,
            format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Suppress noisy http logging
        logging.getLogger("httpcore").setLevel(logging.WARNING)  
        logging.getLogger("httpx").setLevel(logging.WARNING)  

        # Log configuration
        logger.info(f"Configuration Initialized: {self.config_items}")
        
        return
            
    def _get_config_value(self, name, default_value, is_secret):
        """Retrieve a configuration value, first from a file, then environment variable, then default."""
        value = default_value
        from_source = "default"

        # Check for config file first
        file_path = Path(self.INPUT_FOLDER, name) 
        if file_path.exists():
            value = file_path.read_text().strip()
            from_source = "file"
            
        # If no file, check for environment variable
        elif os.getenv(name):
            value = os.getenv(name)
            from_source = "environment"

        # Record the source of the config value
        self.config_items.append({
            "name": name,
            "value": "secret" if is_secret else value,
            "from": from_source
        })
        return value
    
    # Serializer
    def to_dict(self):
        """Convert the Config object to a dictionary with the required fields."""
        return {
            "config_items": self.config_items,
        }    

    # Singleton Getter
    @staticmethod
    def get_instance():
        """Get the singleton instance of the Config class."""
        if Config._instance is None:
            Config()
            

        return Config._instance
        