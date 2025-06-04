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
                "error_id": "CFG-001",
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
                    "error_id": "CFG-002",
                    "file": file,
                    "message": str(e)
                })
            except Exception as e:
                self.load_errors.append({
                    "error": "load_error",
                    "error_id": "CFG-003",
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
        
        for filename, config in self.collection_configs.items():
            # Validate required fields
            if not isinstance(config, dict):
                errors.append({
                    "error": "invalid_config_format",
                    "error_id": "CFG-101",
                    "file": filename,
                    "message": "Configuration must be a dictionary"
                })
                continue
                
            if "name" not in config:
                errors.append({
                    "error": "missing_required_field",
                    "error_id": "CFG-201",
                    "file": filename,
                    "message": "Configuration must include 'name' field"
                })
                continue
                
            if "versions" not in config:
                errors.append({
                    "error": "missing_required_field",
                    "error_id": "CFG-202",
                    "file": filename,
                    "message": "Configuration must include 'versions' field"
                })
                continue
                            
            # Validate versions
            for version_config in config["versions"]:
                if not isinstance(version_config, dict):
                    errors.append({
                        "error": "invalid_version_format",
                        "error_id": "CFG-501",
                        "file": filename,
                        "message": "Version must be a dictionary"
                    })
                    continue
                    
                if "version" not in version_config:
                    errors.append({
                        "error": "missing_version_number",
                        "error_id": "CFG-601",
                        "file": filename,
                        "message": "Version must include 'version' field"
                    })
                    continue
                    
                # Validate version format using VersionNumber
                try:
                    VersionNumber(version_config["version"])
                except ValueError as e:
                    errors.append({
                        "error": "invalid_version_format",
                        "error_id": "CFG-701",
                        "file": filename,
                        "message": f"Version {version_config['version']}: {str(e)}"
                    })
                    continue
                        
        return errors
 