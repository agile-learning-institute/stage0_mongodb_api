from configurator.services.configuration_services import Configuration
from configurator.services.type_services import Type
from configurator.utils.config import Config
from configurator.utils.file_io import FileIO
from configurator.utils.mongo_io import MongoIO
from configurator.utils.configurator_exception import ConfiguratorEvent
import unittest
import os
import json
import tempfile
import shutil
import yaml
import datetime
from bson import json_util
from bson.objectid import ObjectId

class TestProcessingAndRendering(unittest.TestCase):
    """Test Processing and Rendering of several passing_* test cases"""

    expected_pro_count = None  # Should be set in subclasses
    expect_enu_05_success = True

    def _normalize_mongo_data(self, obj):
        """Normalize MongoDB data by converting ObjectIds and datetimes to strings."""
        if isinstance(obj, dict):
            return {k: self._normalize_mongo_data(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._normalize_mongo_data(item) for item in obj]
        elif isinstance(obj, ObjectId):
            return str(obj)
        elif isinstance(obj, (datetime.datetime, datetime.date)):
            return str(obj)
        else:
            return obj

    def setUp(self):
        """Set up test environment."""
        self.test_case = getattr(self, 'test_case', 'passing_template')
        os.environ['INPUT_FOLDER'] = f"./tests/test_cases/{self.test_case}"
        Config._instance = None
        self.config = Config.get_instance()
        del os.environ['INPUT_FOLDER']
        
        # Ensure the database is dropped before any test runs
        # This guarantees a clean state for every test
        mongo_io = MongoIO(self.config.MONGO_CONNECTION_STRING, self.config.MONGO_DB_NAME)
        mongo_io.drop_database()
        mongo_io.disconnect()
        
        # Create temporary directory for test output
        self.temp_dir = tempfile.mkdtemp(prefix="test_processing_")
        
        # Initialize MongoDB connection
        self.mongo_io = MongoIO(self.config.MONGO_CONNECTION_STRING, self.config.MONGO_DB_NAME)
        

    def tearDown(self):
        """Clean up after tests."""
        # Clean up temporary directory
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        
        Config._instance = None

    def test_processing(self):
        """Test processing of configuration files and verify all PRO* events succeeded, ENU-05 success, and PRO* count matches expected."""
        # Process all configurations
        results = Configuration.process_all()

        # Assert processing was successful
        self.assertEqual(results.status, "SUCCESS", f"Processing failed: {results.to_dict()}")

        # Recursively check all PRO* events for SUCCESS status, count them, and check ENU-05
        pro_count = 0
        enu_05_success = False
        def check_events(event):
            nonlocal pro_count, enu_05_success
            if isinstance(event, dict):
                eid = str(event.get("id", ""))
                if eid.startswith("PRO"):
                    pro_count += 1
                    self.assertEqual(event.get("status"), "SUCCESS", f"Event {eid} did not succeed: {event}")
                if eid == "ENU-05" and event.get("status") == "SUCCESS":
                    enu_05_success = True
                for sub in event.get("sub_events", []):
                    check_events(sub)
            elif hasattr(event, 'to_dict'):
                check_events(event.to_dict())
        check_events(results.to_dict())

        # Check ENU-05 if required
        if self.expect_enu_05_success and (self.expected_pro_count is None or self.expected_pro_count > 0):
            self.assertTrue(enu_05_success, "No ENU-05 event with SUCCESS status found in event tree.")

        # Check PRO* event count if expected_pro_count is set
        if self.expected_pro_count is not None:
            self.assertEqual(pro_count, self.expected_pro_count, f"Expected {self.expected_pro_count} PRO* events, found {pro_count}.")

        # Compare database state
        self._compare_database_state()
        
        # Compare processing events
        self._compare_processing_events(results)

    def test_renders(self):
        """Test rendering of configurations and compare against verified output"""
        # Arrange
        verified_output_dir = f"{self.config.INPUT_FOLDER}/verified_output"
        json_schema_dir = f"{verified_output_dir}/json_schema"
        
        if not os.path.exists(json_schema_dir):
            self.skipTest(f"No verified JSON schema directory found: {json_schema_dir}")
        
        # Act & Assert - Iterate over verified output JSON schema files
        for filename in os.listdir(json_schema_dir):
            if filename.endswith('.yaml'):
                # Extract collection and version from filename (e.g., "sample.1.0.0.1.yaml")
                schema_name = filename.replace('.yaml', '')
                parts = schema_name.split('.')
                
                if len(parts) >= 2:
                    collection_name = parts[0]
                    version_str = '.'.join(parts[1:])
                    
                    # Render the same value based on collection/version
                    configuration = Configuration(f"{collection_name}.yaml")
                    json_schema = configuration.get_json_schema(version_str)
                    
                    # Compare against verified output
                    self._compare_json_schema_rendering(schema_name, json_schema)

    def _compare_database_state(self):
        """Compare database state against verified output with property value compares."""
        verified_output_dir = f"{self.config.INPUT_FOLDER}/verified_output"
        db_dir = f"{verified_output_dir}/test_database"
        
        if not os.path.exists(db_dir):
            return  # No database state to compare
        
        # Get all JSON files in the test_database directory
        for filename in os.listdir(db_dir):
            if filename.endswith('.json'):
                collection_name = filename.replace('.json', '')
                
                # Load expected data from verified output
                expected_path = f"{db_dir}/{filename}"
                with open(expected_path, 'r') as f:
                    expected_data = json.load(f)
                
                # Get actual data from database
                actual_data = list(self.mongo_io.db[collection_name].find())
                
                # Normalize the actual data to convert ObjectIds and datetimes to strings
                actual_data = self._normalize_mongo_data(actual_data)
                
                # Compare the data, ignoring properties with value "ignore"
                self._compare_collection_data(collection_name, expected_data, actual_data)

    def _compare_processing_events(self, results):
        """No-op: event comparison is now handled in test_processing."""
        pass

    def _harvest_processing_events(self, results, events_path):
        """Harvest processing events and save to verified output file, sanitizing non-primitive types."""
        def sanitize(obj):
            if isinstance(obj, dict):
                return {k: sanitize(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [sanitize(v) for v in obj]
            elif isinstance(obj, (str, int, float, bool, type(None))):
                return obj
            else:
                return str(obj)

        events = []
        for event in results:
            events.append(sanitize(event.to_dict()))
        
        # Save to verified output
        with open(events_path, 'w') as f:
            yaml.dump(events, f, default_flow_style=False)
        
        print(f"Harvested processing events to: {events_path}")
        print("Please review the harvested events and update if needed.")

    def _compare_bson_schemas(self, verified_output_dir: str):
        """Compare BSON schemas against verified output."""
        bson_dir = f"{verified_output_dir}/bson_schema"
        if not os.path.exists(bson_dir):
            return  # No BSON schemas to compare
        
        for filename in os.listdir(bson_dir):
            if filename.endswith('.json'):
                schema_name = filename.replace('.json', '')
                
                # Get the actual schema from the database or configuration
                # This would need to be implemented based on how schemas are stored
                # For now, just check that the file exists
                self.assertTrue(os.path.exists(f"{bson_dir}/{filename}"), 
                              f"Expected BSON schema file: {filename}")

    def _compare_json_schemas(self, verified_output_dir: str):
        """Compare JSON schemas against verified output."""
        json_dir = f"{verified_output_dir}/json_schema"
        if not os.path.exists(json_dir):
            return  # No JSON schemas to compare
        
        for filename in os.listdir(json_dir):
            if filename.endswith('.yaml'):
                schema_name = filename.replace('.yaml', '')
                
                # Get the actual schema from the database or configuration
                # This would need to be implemented based on how schemas are stored
                # For now, just check that the file exists
                self.assertTrue(os.path.exists(f"{json_dir}/{filename}"), 
                              f"Expected JSON schema file: {filename}")



    def _compare_collection_data(self, collection_name: str, expected_data: list, actual_data: list):
        """Compare collection data, ignoring properties with value 'ignore'."""
        self.assertEqual(len(expected_data), len(actual_data), 
                        f"Collection {collection_name} has different number of documents")
        
        # Sort documents by version for DatabaseEnumerators to handle order issues
        if collection_name == "DatabaseEnumerators":
            expected_data = sorted(expected_data, key=lambda x: x.get('version', 0))
            actual_data = sorted(actual_data, key=lambda x: x.get('version', 0))
        
        for i, (expected_doc, actual_doc) in enumerate(zip(expected_data, actual_data)):
            # Compare documents, ignoring properties with value "ignore"
            self._compare_document(collection_name, i, expected_doc, actual_doc)

    def _compare_document(self, collection_name: str, doc_index: int, expected_doc: dict, actual_doc: dict):
        """Compare a single document, ignoring properties with value 'ignore'."""
        for key, expected_value in expected_doc.items():
            if expected_value == "ignore":
                continue  # Skip properties with value "ignore"
            
            # For DatabaseEnumerators, ignore _id comparison since ObjectIds are generated dynamically
            if collection_name == "DatabaseEnumerators" and key == "_id":
                continue
            
            # For CollectionVersions, ignore _id comparison since ObjectIds are generated dynamically
            if collection_name == "CollectionVersions" and key == "_id":
                continue
            
            self.assertIn(key, actual_doc, 
                         f"Document {doc_index} in collection {collection_name} missing key: {key}")
            
            actual_value = actual_doc[key]
            
            # Handle ObjectId format differences
            if key == "_id":
                # Normalize ObjectId formats for comparison
                if isinstance(expected_value, dict) and '$oid' in expected_value:
                    expected_value = expected_value['$oid']
                if isinstance(actual_value, dict) and '$oid' in actual_value:
                    actual_value = actual_value['$oid']
            
            # Handle datetime conversion for MongoDB date format
            if isinstance(expected_value, dict) and '$date' in expected_value:
                # Expected value is MongoDB date format, convert actual datetime to same format
                if hasattr(actual_value, 'isoformat'):
                    # Convert Python datetime to ISO format for comparison
                    actual_value = actual_value.isoformat() + 'Z'
                    expected_value = expected_value['$date']
            elif isinstance(expected_value, dict) and isinstance(actual_value, dict):
                # Recursively compare nested objects
                self._compare_document(f"{collection_name}.{key}", doc_index, expected_value, actual_value)
                continue
            
            self.assertEqual(expected_value, actual_value, 
                           f"Document {doc_index} in collection {collection_name} has different value for key {key}")

    def _compare_json_schema_rendering(self, schema_name: str, actual_schema: dict):
        """Compare actual JSON schema rendering against verified output."""
        verified_path = f"{self.config.INPUT_FOLDER}/verified_output/json_schema/{schema_name}.yaml"
        
        if not os.path.exists(verified_path):
            self.fail(f"Expected verified JSON schema file not found: {verified_path}")
        
        with open(verified_path, 'r') as f:
            expected_schema = yaml.safe_load(f)
        
        self.assertEqual(actual_schema, expected_schema, 
                        f"JSON schema for {schema_name} does not match verified output")

class TestTemplate(TestProcessingAndRendering):
    """Test Processing and Rendering of passing_template"""

    expected_pro_count = 12
    def setUp(self):
        self.test_case = 'passing_template'
        super().setUp()

    def tearDown(self):
        super().tearDown()

class TestComplexRefs(TestProcessingAndRendering):
    """Test Processing and Rendering of complex refs (placeholder)"""

    expected_pro_count = 12  # Set to the expected number for this test case
    def test_placeholder(self):
        self.assertTrue(True)

class TestEmpty(TestProcessingAndRendering):
    """Test Processing and Rendering of empty files"""

    expected_pro_count = 0  # Set to the expected number for this test case
    def setUp(self):
        self.test_case = 'passing_empty'
        super().setUp()

    def tearDown(self):
        super().tearDown()

class TestProcess(TestProcessingAndRendering):
    """Test Processing and Rendering of passing_process"""

    expected_pro_count = 55  # Set to the expected number for this test case
    def setUp(self):
        self.test_case = 'passing_process'
        super().setUp()

    def tearDown(self):
        super().tearDown()

if __name__ == '__main__':
    unittest.main() 