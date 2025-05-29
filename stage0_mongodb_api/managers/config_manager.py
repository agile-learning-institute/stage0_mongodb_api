from typing import Dict, List, Optional
from stage0_py_utils import Config
import yaml
import os
import logging
from stage0_mongodb_api.managers.version_number import VersionNumber

logger = logging.getLogger(__name__)

class ConfigManager:
    """Manages collection configurations and version resolution.
    
    This class handles:
    1. Loading and validating collection configurations
    2. Resolving schema and enumerator versions
    3. Providing configuration data to other services
    """
    
    def __init__(self):
        """Initialize the config manager."""
        self.config = Config.get_instance()
        self.collection_configs: Dict[str, Dict] = {}
        self.load_errors: List[Dict] = []
        self._load_collection_configs()
        
    def _load_collection_configs(self) -> None:
        """Load collection configurations from the input folder.
        
        Only performs basic file existence and YAML parsing checks.
        All other validation is handled by validate_configs().
        """
        collections_folder = os.path.join(self.config.INPUT_FOLDER, "collections")
        logger.info(f"Loading collections from {collections_folder}")
        
        if not os.path.exists(collections_folder):
            self.load_errors.append({
                "error": "directory_not_found",
                "path": collections_folder
            })
            return
            
        # Load all YAML files from collections folder
        for file in os.listdir(collections_folder):
            if not file.endswith(".yaml"):
                continue
                
            file_path = os.path.join(collections_folder, file)
            try:
                with open(file_path, "r") as f:
                    data = yaml.safe_load(f)
                    key = os.path.splitext(file)[0]
                    self.collection_configs[key] = data
            except yaml.YAMLError as e:
                self.load_errors.append({
                    "error": "parse_error",
                    "file": file,
                    "message": str(e)
                })
            except Exception as e:
                self.load_errors.append({
                    "error": "load_error",
                    "file": file,
                    "message": str(e)
                })
                
        logger.info(f"Loaded {len(self.collection_configs)} collection configurations")
        
    def validate_configs(self) -> List[Dict]:
        """Validate all loaded collection configurations.
        
        Validates:
        1. Required fields are present and have correct types
        2. No additional properties beyond those defined in schema
        3. Version format is valid
        
        Returns:
            List of validation errors, empty if all valid
        """
        errors = []
        allowed_fields = {
            "name": str,
            "versions": list,
            "title": str,
            "description": str
        }
        allowed_version_fields = {
            "version": str,
            "add_indexes": list,
            "drop_indexes": list,
            "aggregations": list,
            "test_data": str
        }
        
        for filename, config in self.collection_configs.items():
            # Validate required fields
            if not isinstance(config, dict):
                errors.append({
                    "error": "Invalid configuration format",
                    "details": f"Configuration in {filename} must be a dictionary"
                })
                continue
                
            if "name" not in config:
                errors.append({
                    "error": "Missing required field",
                    "details": f"Configuration in {filename} must include 'name' field"
                })
                continue
                
            if "versions" not in config:
                errors.append({
                    "error": "Missing required field",
                    "details": f"Configuration in {filename} must include 'versions' field"
                })
                continue
                
            # Validate field types and check for additional properties
            for field, value in config.items():
                if field not in allowed_fields:
                    errors.append({
                        "error": "Invalid field",
                        "details": f"Field '{field}' is not allowed in collection configuration in {filename}"
                    })
                    continue
                    
                if not isinstance(value, allowed_fields[field]):
                    errors.append({
                        "error": "Invalid field type",
                        "details": f"Field '{field}' in {filename} must be of type {allowed_fields[field].__name__}"
                    })
                    continue
            
            # Validate versions
            for version_config in config["versions"]:
                if not isinstance(version_config, dict):
                    errors.append({
                        "error": "Invalid version format",
                        "details": f"Version in {filename} must be a dictionary"
                    })
                    continue
                    
                if "version" not in version_config:
                    errors.append({
                        "error": "Missing version number",
                        "details": f"Version in {filename} must include 'version' field"
                    })
                    continue
                    
                # Validate version format using VersionNumber
                try:
                    VersionNumber(version_config["version"])
                except ValueError as e:
                    errors.append({
                        "error": "Invalid version format",
                        "details": f"Version {version_config['version']} in {filename}: {str(e)}"
                    })
                    continue
                
                # Check for additional properties in version config
                for field in version_config:
                    if field not in allowed_version_fields:
                        errors.append({
                            "error": "Invalid field",
                            "details": f"Field '{field}' is not allowed in version configuration in {filename}"
                        })
                        continue
                        
                    if not isinstance(version_config[field], allowed_version_fields[field]):
                        errors.append({
                            "error": "Invalid field type",
                            "details": f"Field '{field}' in {filename} must be of type {allowed_version_fields[field].__name__}"
                        })
                        continue
        
        return errors
        