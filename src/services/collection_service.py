import logging
import os
import yaml
from stage0_py_utils import MongoIO, Config
from managers.version_manager import VersionManager
from managers.index_manager import IndexManager
from managers.schema_manager import SchemaManager

logger = logging.getLogger(__name__)

class CollectionService:
    def __init__(self):
        self.mongo = MongoIO.get_instance()
        self.config = Config.get_instance()
        self.version_manager = VersionManager()
        self.configs = {}
        self.collections = {}
        self._load_collections()

    def _load_collections(self):
        """Load collection configurations from the input folder"""
        try:
            input_folder = os.getenv("INPUT_FOLDER", "/input")
            logger.info(f"Loading collections from {input_folder}")

            # Load all YAML files from input folder
            for root, _, files in os.walk(input_folder):
                for file in files:
                    if file.endswith(".yaml"):
                        file_path = os.path.join(root, file)
                        with open(file_path, "r") as f:
                            data = yaml.safe_load(f)
                            collection_name = os.path.splitext(file)[0]
                            self.configs[collection_name] = data
                            self.collections[collection_name] = {
                                "name": collection_name,
                                "versions": data.get("versions", []),
                                "dropIndexes": data.get("dropIndexes", []),
                                "migrations": data.get("migrations", []),
                                "addIndexes": data.get("addIndexes", [])
                            }

            # Get current versions from MongoDB
            for collection_name in self.collections:
                current_version = self.version_manager.get_current_version(collection_name)
                if current_version:
                    self.collections[collection_name]["current_version"] = current_version

            logger.info(f"Loaded {len(self.collections)} collections")
        except Exception as e:
            logger.error(f"Error loading collections: {str(e)}")
            raise

    def list_collections(self):
        """List all configured collections"""
        return [{
            "name": name,
            "current_version": config.get("current_version", "unknown"),
            "versions": config.get("versions", [])
        } for name, config in self.collections.items()]

    def get_collection(self, collection_name):
        """Get collection configuration by name"""
        if collection_name not in self.collections:
            raise ValueError(f"Collection {collection_name} not found")
        return self.collections[collection_name]

    def process_collections(self):
        """Process all configured collections"""
        results = {}
        for collection_name in self.collections:
            try:
                results[collection_name] = self.process_collection(collection_name)
            except Exception as e:
                logger.error(f"Error processing collection {collection_name}: {str(e)}")
                results[collection_name] = {"error": str(e)}
        return results

    def process_collection(self, collection_name):
        """Process a specific collection"""
        if collection_name not in self.collections:
            raise ValueError(f"Collection {collection_name} not found")

        collection_config = self.collections[collection_name]
        results = []

        try:
            # Process each version in the collection configuration
            for version in collection_config.get("versions", []):
                version_result = self._process_version(collection_name, version)
                results.append(version_result)
        except Exception as e:
            logger.error(f"Error processing collection {collection_name}: {str(e)}")
            raise

        return results

    def _process_version(self, collection_name, version_config):
        """Process a specific version of a collection"""
        results = []

        # Drop indexes if specified
        if "dropIndexes" in version_config:
            for index_name in version_config["dropIndexes"]:
                result = IndexManager.drop_index(collection_name, index_name)
                results.append(result)

        # Run migrations if specified
        if "migrations" in version_config:
            for migration in version_config["migrations"]:
                result = SchemaManager.run_migration(collection_name, migration)
                results.append(result)

        # Add indexes if specified
        if "addIndexes" in version_config:
            for index_config in version_config["addIndexes"]:
                result = IndexManager.create_index(collection_name, index_config)
                results.append(result)

        # Update version if specified
        if "version" in version_config:
            self.version_manager.update_version(collection_name, version_config["version"])

        return {
            "version": version_config.get("version", "unknown"),
            "results": results
        } 