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
        self.mongo_io = MongoIO.get_instance()
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
                "path": collections_folder,
                "message": f"Collections directory not found: {collections_folder}"
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
                        
        # Add schema validation errors if schema manager is available
        if hasattr(self, "schema_manager") and self.schema_manager:
            schema_errors = self.schema_manager.validate_schema()
            errors.extend(schema_errors)
                        
        return errors

    def get_collection_config(self, collection_name: str) -> Optional[Dict]:
        """Get a specific collection configuration.
        
        Args:
            collection_name: Name of the collection to retrieve
            
        Returns:
            Dict containing the collection configuration, or None if not found
        """
        return self.collection_configs.get(collection_name)

    def process_all_collections(self) -> Dict[str, List[Dict]]:
        """Process all collections that have pending versions.
        
        Returns:
            Dict[str, List[Dict]]: Dictionary mapping collection names to their operation results
        """
        results = {}
        any_collection_failed = False
        
        # Process enumerators first
        enumerators_result = self._process_enumerators()
        results["enumerators"] = [enumerators_result]
        
        # Check if enumerators processing failed
        if enumerators_result.get("status") == "error":
            any_collection_failed = True
        
        # Process all collections
        for collection_name in self.collection_configs.keys():
            try:
                results[collection_name] = self.process_collection_versions(collection_name)
                
                # Check if this collection had any errors
                if any(isinstance(op, dict) and op.get("status") == "error" for op in results[collection_name]):
                    any_collection_failed = True
                    
            except Exception as e:
                logger.error(f"Error processing collection {collection_name}: {str(e)}")
                results[collection_name] = [{
                    "operation": "collection_processing",
                    "collection": collection_name,
                    "message": f"Error processing collection: {str(e)}",
                    "details_type": "error",
                    "details": {
                        "error": str(e)
                    },
                    "status": "error"
                }]
                any_collection_failed = True
                
        # Add final overall status operation
        overall_status = "error" if any_collection_failed else "success"
        overall_message = "Some collections failed to process" if any_collection_failed else "All collections processed successfully"
        
        # Add the overall status only to collections that actually failed
        for collection_name in results.keys():
            # Check if this collection had any errors (excluding overall_status operations)
            collection_has_errors = any(
                isinstance(op, dict) and op.get("status") == "error" 
                and op.get("operation") != "overall_status"
                for op in results[collection_name]
            )
            
            # Only add overall_status to collections that failed
            if collection_has_errors:
                results[collection_name].append({
                    "operation": "overall_status",
                    "message": overall_message,
                    "details_type": "overall",
                    "details": {
                        "collections_processed": len(self.collection_configs),
                        "collections_failed": sum(1 for result in results.values() 
                                                if any(isinstance(op, dict) and op.get("status") == "error" 
                                                      and op.get("operation") != "overall_status"
                                                      for op in result))
                    },
                    "status": overall_status
                })
                
        return results

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
                operations.append({
                    "operation": "evaluate_version",
                    "collection": collection_name,
                    "message": f"Evaluating version {version_number}",
                    "details_type": "version",
                    "details": {
                        "version": str(version_number),
                        "current_version": current_version
                    },
                    "status": "success"
                })
                
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
                    operations.append({
                        "operation": "evaluate_version",
                        "collection": collection_name,
                        "message": f"Skipping version {version_number} - already processed",
                        "details_type": "version",
                        "details": {
                            "version": str(version_number),
                            "current_version": current_version,
                            "skipped": True
                        },
                        "status": "skipped"
                    })
                    
        except Exception as e:
            logger.error(f"Error during version processing for {collection_name}: {str(e)}")
            operations.append({
                "operation": "version_processing",
                "collection": collection_name,
                "message": f"Error during version processing: {str(e)}",
                "details_type": "error",
                "details": {
                    "error": str(e),
                    "version": "unknown"
                },
                "status": "error"
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
            operations.append({
                "operation": "remove_schema",
                "collection": collection_name,
                "message": f"Removing schema validation for {collection_name}",
                "status": "success"
            })
            remove_result = self.schema_manager.remove_schema(collection_name)
            operations.append(remove_result)
            self._assert_no_errors(operations)
            
            # Optional: Process drop_indexes if present
            if "drop_indexes" in version_config:
                for index in version_config["drop_indexes"]:
                    operations.append({
                        "operation": "drop_index",
                        "collection": collection_name,
                        "message": f"Dropping index {index} for {collection_name}",
                        "status": "success"
                    })
                    drop_result = self.index_manager.drop_index(collection_name, index)
                    operations.append(drop_result)
                    self._assert_no_errors(operations)
                
            # Optional: Process aggregations if present
            if "aggregations" in version_config:
                for migration in version_config["aggregations"]:
                    pipeline_name = migration.get("name", "unnamed_pipeline")
                    operations.append({
                        "operation": "run_migration",
                        "collection": collection_name,
                        "message": f"Running Aggregation Pipeline '{pipeline_name}' for {collection_name}",
                        "status": "success"
                    })
                    migration_result = self.migration_manager.run_migration(collection_name, migration)
                    operations.append(migration_result)
                    self._assert_no_errors(operations)
                
            # Optional: Process add_indexes if present
            if "add_indexes" in version_config:
                operations.append({
                    "operation": "create_index",
                    "collection": collection_name,
                    "message": f"Creating indexes for {collection_name}",
                    "status": "success"
                })
                create_result = self.index_manager.create_index(collection_name, version_config["add_indexes"])
                operations.append(create_result)
                self._assert_no_errors(operations)
                
            # Required: Apply schema validation
            operations.append({
                "operation": "apply_schema",
                "collection": collection_name,
                "message": f"Applying schema for {collection_name}",
                "status": "success"
            })
            apply_result = self.schema_manager.apply_schema(f"{collection_name}.{version_config.get("version")}")
            operations.append(apply_result)
            self._assert_no_errors(operations)
                
            # Optional: Load test data if enabled and present
            if "test_data" in version_config and self.config.LOAD_TEST_DATA:
                operations.append({
                    "operation": "load_test_data",
                    "collection": collection_name,
                    "message": f"Loading test data for {collection_name} - {version_config['test_data']}",
                    "status": "success"
                })
                test_data_result = self._load_test_data(collection_name, version_config["test_data"])
                operations.append(test_data_result)
                self._assert_no_errors(operations)
                
            # Update version if version string is present
            operations.append({
                "operation": "update_version",
                "collection": collection_name,
                "message": f"Updating version for {collection_name}",
                "status": "success"
            })
            version_result = self.version_manager.update_version(collection_name, version_config["version"])
            operations.append(version_result)
            self._assert_no_errors(operations)
            
        except Exception as e:
            logger.error(f"Error processing version for {collection_name}: {str(e)}")
            operations.append({
                "operation": "version_processing",
                "collection": collection_name,
                "message": f"Error processing version: {str(e)}",
                "details_type": "error",
                "details": {
                    "error": str(e)
                },
                "status": "error"
            })
        
        return operations

    def _load_test_data(self, collection_name: str, test_data_file: str) -> Dict:
        """Load test data for a collection.
        
        Args:
            collection_name: Name of the collection
            test_data_file: Name of the test data file
            
        Returns:
            Dict containing operation result in consistent format
        """
        from stage0_py_utils.mongo_utils.mongo_io import TestDataLoadError
        try:
            data_file = os.path.join(self.config.INPUT_FOLDER, "data", test_data_file)
            results = self.mongo_io.load_test_data(collection_name, data_file)
            
            return {
                "operation": "load_test_data",
                "collection": collection_name,
                "message": f"Test data loaded successfully from {test_data_file}",
                "details_type": "test_data",
                "details": {
                    "test_data_file": str(data_file),
                    "results": results,
                    "documents_loaded": results.get("documents_loaded", 0),
                    "inserted_ids": results.get("inserted_ids", []),
                    "acknowledged": results.get("acknowledged", False)
                },
                "status": "success"
            }
            
        except TestDataLoadError as e:
            return {
                "operation": "load_test_data",
                "collection": collection_name,
                "message": str(e),
                "details_type": "error",
                "details": {
                    "error": str(e),
                    "test_data_file": str(data_file),
                    "details": e.details
                },
                "status": "error"
            }
        except Exception as e:
            error_message = str(e)
            logger.error(f"Failed to load test data for {collection_name}: {error_message}")
            return {
                "operation": "load_test_data",
                "collection": collection_name,
                "message": error_message,
                "details_type": "error",
                "details": {
                    "error": error_message,
                    "test_data_file": str(data_file)
                },
                "status": "error"
            }

    def _process_enumerators(self) -> Dict:
        """Process enumerators from the enumerators.json file.
        
        Returns:
            Dict containing operation result in consistent format
        """
        try:
            # Use the already-loaded enumerators from schema_manager
            enumerators = self.schema_manager.enumerators
            
            # Process each enumerator version
            processed_count = 0
            
            for document in enumerators:
                version = document.get("version")
                    
                # Upsert the document using version as the key
                result = self.mongo_io.upsert_document(
                    self.config.ENUMERATORS_COLLECTION_NAME,
                    {"version": version},
                    document
                )
                
                # upsert_document returns the document itself, so if we get a result, it succeeded
                if result and isinstance(result, dict):
                    processed_count += 1
                else:
                    raise Exception(f"Failed to upsert version {version}")
            
            return {
                "operation": "process_enumerators",
                "collection": self.config.ENUMERATORS_COLLECTION_NAME,
                "message": f"Successfully processed {processed_count} enumerator versions",
                "details_type": "success",
                "details": {
                    "processed_count": processed_count,
                    "total_count": len(enumerators)
                },
                "status": "success"
            }
                
        except Exception as e:
            return {
                "operation": "process_enumerators",
                "collection": self.config.ENUMERATORS_COLLECTION_NAME,
                "message": f"Error processing enumerators: {str(e)}",
                "details_type": "error",
                "details": {
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                "status": "error"
            }

    def _assert_no_errors(self, operations: List[Dict]) -> None:
        """Check the last operation for errors and raise an exception if found.
        
        Args:
            operations: List of operations to check
            
        Raises:
            Exception: If the last operation has status "error"
        """
        if operations and isinstance(operations[-1], dict) and operations[-1].get("status") == "error":
            error_op = operations[-1]
            raise Exception(f"Operation failed: {error_op.get('operation', 'unknown')} - {error_op.get('error', 'Unknown error')}")

 