import unittest
import os
import json
import tempfile
import shutil
from configurator.services.configuration_services import Configuration
from configurator.utils.mongo_io import MongoIO
from configurator.utils.config import Config
from configurator.utils.configurator_exception import ConfiguratorException
import logging
from unittest.mock import patch, Mock
from bson import json_util

# Suppress logging during tests
logging.getLogger().setLevel(logging.CRITICAL)


def set_config_input_folder(folder):
    """Set the input folder for configuration processing."""
    os.environ['INPUT_FOLDER'] = folder
    from configurator.utils.config import Config
    Config._instance = None
    return Config.get_instance()


def clear_config():
    """Clear the configuration environment."""
    for key in ['INPUT_FOLDER']:
        if key in os.environ:
            del os.environ[key]
    from configurator.utils.config import Config
    Config._instance = None


class DatabaseHarvester:
    """Utility class to harvest database state for comparison."""
    
    def __init__(self, mongo_io: MongoIO, config: Config):
        self.mongo_io = mongo_io
        self.config = config
    
    def harvest_collection_versions(self):
        """Harvest the CollectionVersions collection."""
        try:
            versions = self.mongo_io.get_documents(
                self.config.VERSION_COLLECTION_NAME,
                sort_by=[("collection_name", 1)]
            )
            # Serialize to Extended JSON format
            return json.loads(json_util.dumps(versions))
        except Exception as e:
            return []
    
    def harvest_collection_data(self, collection_name):
        """Harvest all documents from a collection."""
        try:
            documents = self.mongo_io.get_documents(
                collection_name,
                sort_by=[("_id", 1)]
            )
            # Serialize to Extended JSON format
            return json.loads(json_util.dumps(documents))
        except Exception as e:
            return []
    
    def harvest_all_collections(self):
        """Harvest all collections in the database."""
        result = {}
        
        # Harvest CollectionVersions
        versions = self.harvest_collection_versions()
        result[self.config.VERSION_COLLECTION_NAME] = versions
        
        # Get all collection names
        collection_names = self.mongo_io.db.list_collection_names()
        print(f"Harvester found collections: {collection_names}")
        
        # Harvest each collection (except CollectionVersions which we already did)
        for collection_name in collection_names:
            if collection_name != self.config.VERSION_COLLECTION_NAME:
                documents = self.harvest_collection_data(collection_name)
                print(f"Harvested {len(documents)} documents from {collection_name}")
                result[collection_name] = documents
        
        return result
    
    def save_harvested_data(self, output_dir: str, harvested_data: dict):
        """Save harvested data to JSON files for comparison."""
        os.makedirs(output_dir, exist_ok=True)
        
        for collection_name, documents in harvested_data.items():
            filename = f"{collection_name}.json"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w') as f:
                json.dump(documents, f, indent=2)


class TestConfigurationIntegration(unittest.TestCase):
    """Test configuration processing integration against verified output files"""

    def setUp(self):
        # Default to small_sample for backward compatibility
        self.test_case = getattr(self, 'test_case', 'small_sample')
        self.config = set_config_input_folder(f"./tests/test_cases/{self.test_case}")
        
        # Drop the database before starting
        mongo_io = MongoIO(self.config.MONGO_CONNECTION_STRING, self.config.MONGO_DB_NAME)
        mongo_io.drop_database()
        mongo_io.disconnect()
        
        # Add a pause after dropping the database
        import time
        time.sleep(1)
        
        # Create temporary directory for test output
        self.temp_dir = tempfile.mkdtemp(prefix="test_config_integration_")
        
        # Initialize MongoDB connection
        self.mongo_io = MongoIO(self.config.MONGO_CONNECTION_STRING, self.config.MONGO_DB_NAME)
        self.harvester = DatabaseHarvester(self.mongo_io, self.config)

    def tearDown(self):
        """Clean up after tests."""
        # Note: Database is NOT dropped here to allow inspection of final state
        # Database is only dropped in setUp for clean start
        
        # Clean up temporary directory
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        
        clear_config()

    def test_configuration_processing_integration(self):
        """Test configuration processing integration against verified output."""
        # Step 1: Process all configurations
        self._process_all_configurations()
        
        # Step 2: Harvest database state
        harvested_data = self.harvester.harvest_all_collections()
        
        # Step 3: Compare against verified output
        self._compare_against_verified_output(harvested_data)

    def _process_all_configurations(self):
        """Process all configuration files in the test case."""
        config_dir = f"{self.config.INPUT_FOLDER}/configurations"
        
        if not os.path.exists(config_dir):
            self.skipTest(f"No configurations directory found: {config_dir}")
        
        config_files = [f for f in os.listdir(config_dir) if f.endswith('.yaml')]
        
        if not config_files:
            self.skipTest(f"No configuration files found in: {config_dir}")
        
        # For large_sample, process in dependency order to handle one_of schemas
        if self.test_case == 'large_sample':
            # Define dependency order: process dependencies first
            dependency_order = [
                'media.yaml', 
                'organization.yaml',
                'user.yaml',  # user must be processed before notification
                'notification.yaml',  # notification depends on user
                'content.yaml',  # content depends on user
                'search.yaml'  # Process search last as it depends on others
            ]
            
            # Filter to only include files that exist
            ordered_files = [f for f in dependency_order if f in config_files]
            
            # Add any remaining files not in the dependency order
            remaining_files = [f for f in config_files if f not in dependency_order]
            ordered_files.extend(remaining_files)
            
            for filename in ordered_files:
                self._process_configuration(filename)
        else:
            # For other test cases, process in alphabetical order
            for filename in sorted(config_files):
                self._process_configuration(filename)

    def _process_configuration(self, config_filename):
        """Process a single configuration file."""
        try:
            configuration = Configuration(config_filename)
            event = configuration.process()
            
            # Debug: Print the result events
            print(f"Processing {config_filename} - status: {event.status}")
            for sub_event in event.sub_events:
                print(f"  Sub-event: {sub_event.type} - {sub_event.status}")
                if hasattr(sub_event, 'data') and sub_event.data:
                    print(f"    Data: {sub_event.data}")
            
            if event.status == "FAILURE":
                self.fail(f"Configuration processing failed for {config_filename}: {event.data.get('error', 'Unknown error')}")
            
        except Exception as e:
            self.fail(f"Exception processing configuration {config_filename}: {str(e)}")

    def _compare_against_verified_output(self, harvested_data):
        """Compare harvested data against verified output files."""
        verified_dir = f"{self.config.INPUT_FOLDER}/verified_output/test_database"
        
        if not os.path.exists(verified_dir):
            self.skipTest(f"No verified output directory found: {verified_dir}")
        
        # Compare each collection
        for collection_name, documents in harvested_data.items():
            self._compare_collection(collection_name, documents, verified_dir)

    def _compare_collection(self, collection_name, actual_documents, verified_dir):
        """Compare a collection's actual data against verified output."""
        verified_file = os.path.join(verified_dir, f"{collection_name}.json")
        
        if not os.path.exists(verified_file):
            # If no verified file exists, save the actual data for review
            self.harvester.save_harvested_data(self.temp_dir, {collection_name: actual_documents})
            self.fail(f"No verified output file found for {collection_name}. "
                     f"Actual data saved to {self.temp_dir}/{collection_name}.json")
        
        # Load verified data
        with open(verified_file, 'r') as f:
            expected_documents = json.load(f)
        
        # Debug: Print what we're comparing
        print(f"Comparing {collection_name}:")
        print(f"  Expected count: {len(expected_documents)}")
        print(f"  Actual count: {len(actual_documents)}")
        if actual_documents:
            print(f"  Actual documents: {actual_documents}")
        
        # Compare document counts
        self.assertEqual(
            len(actual_documents), 
            len(expected_documents),
            f"Document count mismatch for {collection_name}: "
            f"expected {len(expected_documents)}, got {len(actual_documents)}"
        )
        
        # Sort documents by collection_name for consistent comparison
        actual_sorted = sorted(actual_documents, key=lambda x: x.get('collection_name', ''))
        expected_sorted = sorted(expected_documents, key=lambda x: x.get('collection_name', ''))
        
        # Compare each document
        for i, (actual_doc, expected_doc) in enumerate(zip(actual_sorted, expected_sorted)):
            self._assert_document_equality(
                actual_doc, 
                expected_doc, 
                f"{collection_name}[{i}]"
            )

    def _assert_document_equality(self, actual, expected, context):
        """Assert document equality with detailed diff reporting."""
        # Remove _id fields for comparison since MongoDB generates new ObjectIds
        actual_copy = actual.copy()
        expected_copy = expected.copy()
        
        if '_id' in actual_copy:
            del actual_copy['_id']
        if '_id' in expected_copy:
            del expected_copy['_id']
            
        if actual_copy != expected_copy:
            diff = self._dict_diff(actual_copy, expected_copy)
            self.fail(f"{context} mismatch:\n{diff}")

    def _dict_diff(self, dict1, dict2):
        """Generate a detailed diff between two dictionaries."""
        def _diff_dict(d1, d2, path=""):
            diff = []
            all_keys = set(d1.keys()) | set(d2.keys())
            
            for key in sorted(all_keys):
                current_path = f"{path}.{key}" if path else key
                
                if key not in d1:
                    diff.append(f"Missing in actual: {current_path}")
                elif key not in d2:
                    diff.append(f"Extra in actual: {current_path} = {d1[key]}")
                elif isinstance(d1[key], dict) and isinstance(d2[key], dict):
                    diff.extend(_diff_dict(d1[key], d2[key], current_path))
                elif d1[key] != d2[key]:
                    diff.append(f"Value mismatch at {current_path}:")
                    diff.append(f"  Expected: {d2[key]}")
                    diff.append(f"  Actual:   {d1[key]}")
            
            return diff
        
        return "\n".join(_diff_dict(dict1, dict2))


class TestSmallSampleConfigurationIntegration(TestConfigurationIntegration):
    """Test configuration processing integration for small_sample test case."""
    test_case = 'small_sample'


class TestLargeSampleConfigurationIntegration(TestConfigurationIntegration):
    """Test configuration processing integration for large_sample test case with advanced features."""
    test_case = 'large_sample'


if __name__ == '__main__':
    unittest.main() 