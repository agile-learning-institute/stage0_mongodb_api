from typing import Dict, List, Optional
from stage0_py_utils import Config
import yaml
import os
import logging
from stage0_py_utils import MongoIO
from stage0_mongodb_api.managers.version_number import VersionNumber
from stage0_mongodb_api.managers.version_manager import VersionManager
from stage0_mongodb_api.managers.schema_manager import SchemaManager
from stage0_mongodb_api.managers.index_manager import IndexManager
from stage0_mongodb_api.managers.migration_manager import MigrationManager

logger = logging.getLogger(__name__)

class ConfigManager:
    """Manages collection configurations and version processing.
    
    This class handles:
    1. Loading and validating collection configurations
    2. Resolving schema and enumerator versions
    3. Processing version updates for collections
    4. Coordinating schema, index, and migration operations
    """
    
    def __init__(self):
        """Initialize the config manager."""
        self.config = Config.get_instance()
        self.mongo_io = MongoIO()
        self.collection_configs: Dict[str, Dict] = {}
        self.load_errors: List[Dict] = []
        self.version_manager = VersionManager()
        self.index_manager = IndexManager()
        self.migration_manager = MigrationManager()
        self._load_collection_configs()
        
        # Create schema manager with our collection configs
        self.schema_manager = SchemaManager(self.collection_configs)
        
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

    def get_collection_config(self, collection_name: str) -> Optional[Dict]:
        """Get a specific collection configuration.
        
        Args:
            collection_name: Name of the collection to retrieve
            
        Returns:
            Dict containing the collection configuration, or None if not found
        """
        return self.collection_configs.get(collection_name)

    def process_collection_versions(self, collection_name: str) -> List[Dict]:
        """Process all pending versions for a collection.
        
        This method coordinates the processing workflow by:
        1. Getting current version from database
        2. Identifying pending versions from config
        3. Processing each version in sequence
        4. Updating version records
        
        Args:
            collection_name: Name of the collection to process
            
        Returns:
            List[Dict]: List of operation results
            
        Raises:
            ValueError: If collection_name is empty or not found in configs
        """
        if not collection_name:
            raise ValueError("Collection name cannot be empty")
            
        if collection_name not in self.collection_configs:
            raise ValueError(f"Collection '{collection_name}' not found in configurations")
            
        collection_config = self.collection_configs[collection_name]
        versions = collection_config.get("versions", [])        
        operations = []
        
        try:
            # Process each version in sequence
            for version_config in versions:
                current_version = VersionManager.get_current_version(collection_name)
                version_number = VersionNumber(version_config.get("version"))
                operations.append(f"Evaluating version {version_number}")
                
                # Only process versions greater than current version
                if version_number > current_version:
                    logger.info(f"Processing version {str(version_number)} for {collection_name}")
                    version_operations = self._process_version(collection_name, version_config)
                    operations.extend(version_operations)
                    
                    # Check if any operation in this version failed
                    if any(isinstance(op, dict) and op.get("status") == "error" for op in version_operations):
                        logger.error(f"Version {version_number} processing failed for {collection_name}, stopping version processing")
                        break
                        
                    current_version = VersionNumber(self.version_manager.get_current_version(collection_name))
                else:
                    logger.info(f"Skipping version {str(version_number)} for {collection_name} - already processed")
                    
        except Exception as e:
            logger.error(f"Error during version processing for {collection_name}: {str(e)}")
            operations.append({
                "status": "error",
                "operation": "version_processing",
                "collection": collection_name,
                "version": "unknown",
                "error": f"Error during version processing: {str(e)}"
            })
            
        return operations
        
    def _process_version(self, collection_name: str, version_config: Dict) -> List[Dict]:
        """Process a single version configuration for a collection.
        
        Args:
            collection_name: Name of the collection
            version_config: Version configuration to process
            
        Returns:
            List[Dict]: List of operation results, including any errors that occurred
        """
        operations = []

        try:
            # Required: Remove existing schema validation
            operations.append(self.schema_manager.remove_schema(collection_name))
            
            # Optional: Process drop_indexes if present
            if "drop_indexes" in version_config:
                for index in version_config["drop_indexes"]:
                    operations.append(f"Dropping index {index} for {collection_name}")
                    operations.append(self.index_manager.drop_index(collection_name, index))
                
            # Optional: Process aggregations if present
            if "aggregations" in version_config:
                for pipeline in version_config["aggregations"]:
                    operations.append(f"Running Aggregation Pipeline for {collection_name}")
                    operations.append(self.migration_manager.run_migration(collection_name, pipeline))
                
            # Optional: Process add_indexes if present
            if "add_indexes" in version_config:
                operations.append(f"Creating indexes for {collection_name}")
                operations.append(self.index_manager.create_index(collection_name, version_config["add_indexes"]))
                
            # Required: Apply schema validation
            operations.append(f"Applying schema for {collection_name}")
            operations.append(self.schema_manager.apply_schema(f"{collection_name}.{version_config.get("version")}"))
                
            # Update version if version string is present
            operations.append(f"Updating version for {collection_name}")
            operations.append(self.version_manager.update_version(collection_name, version_config["version"]))
            
            # Optional: Load test data if enabled and present
            if "test_data" in version_config and self.config.LOAD_TEST_DATA:
                operations.append(self._load_test_data(collection_name, version_config["test_data"]))
                
        except Exception as e:
            logger.error(f"Error processing version for {collection_name}: {str(e)}")
            operations.append({
                "status": "error",
                "operation": "version_processing",
                "collection": collection_name,
                "error": str(e)
            })
        
        return operations

    def _load_test_data(self, collection_name: str, test_data_file: str) -> Dict:
        """Load test data for a collection.
        
        Args:
            collection_name: Name of the collection
            test_data_file: Name of the test data file
            
        Returns:
            Dict containing operation result with proper error handling for bulk write errors
        """
        from stage0_py_utils.mongo_utils.mongo_io import TestDataLoadError
        try:
            data_file = os.path.join(self.config.INPUT_FOLDER, "data", test_data_file)
            results = self.mongo_io.load_test_data(collection_name, data_file)
            
            return {
                "status": "success",
                "operation": "load_test_data",
                "collection": collection_name,
                "test_data": str(data_file),
                "results": results
            }
            
        except TestDataLoadError as e:
            return {
                "status": "error",
                "operation": "load_test_data",
                "collection": collection_name,
                "test_data": str(data_file),
                "error": str(e),
                "details": e.details
            }
        except Exception as e:
            error_message = str(e)
            logger.error(f"Failed to load test data for {collection_name}: {error_message}")
            return {
                "status": "error",
                "operation": "load_test_data",
                "collection": collection_name,
                "test_data": str(data_file),
                "error": error_message
            }

    def process_all_collections(self) -> Dict[str, List[Dict]]:
        """Process all collections that have pending versions.
        
        Returns:
            Dict[str, List[Dict]]: Dictionary mapping collection names to their operation results
        """
        results = {}
        
        for collection_name in self.collection_configs.keys():
            try:
                results[collection_name] = self.process_collection_versions(collection_name)
            except Exception as e:
                logger.error(f"Error processing collection {collection_name}: {str(e)}")
                results[collection_name] = [{
                    "status": "error",
                    "operation": "collection_processing",
                    "collection": collection_name,
                    "error": str(e)
                }]
                
        return results
 