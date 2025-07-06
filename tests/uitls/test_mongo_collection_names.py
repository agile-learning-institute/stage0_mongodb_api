import unittest
from stage0_py_utils import Config

class TestMongoCollectionNames(unittest.TestCase):

    def setUp(self):
        """Re-initialize the config for each test."""
        self.config = Config.get_instance()
        self.config.initialize()

    def test_mongo_collection_names_is_list(self):
        """Test that MONGO_COLLECTION_NAMES is a list."""
        self.assertIsInstance(self.config.MONGO_COLLECTION_NAMES, list)

    def test_mongo_collection_names_contains_all_collections(self):
        """Test that MONGO_COLLECTION_NAMES contains all expected collection names."""
        expected_collections = [
            self.config.BOT_COLLECTION_NAME,
            self.config.CHAIN_COLLECTION_NAME,
            self.config.CONVERSATION_COLLECTION_NAME,
            self.config.EXECUTION_COLLECTION_NAME,
            self.config.EXERCISE_COLLECTION_NAME,
            self.config.RUNBOOK_COLLECTION_NAME,
            self.config.TEMPLATE_COLLECTION_NAME,
            self.config.USER_COLLECTION_NAME,
            self.config.WORKSHOP_COLLECTION_NAME
        ]
        
        self.assertEqual(self.config.MONGO_COLLECTION_NAMES, expected_collections)

    def test_mongo_collection_names_contains_default_values(self):
        """Test that MONGO_COLLECTION_NAMES contains the default collection names."""
        expected_defaults = [
            "bot",
            "chain",
            "conversation",
            "execution",
            "exercise",
            "runbook",
            "template",
            "user",
            "workshop"
        ]
        
        self.assertEqual(self.config.MONGO_COLLECTION_NAMES, expected_defaults)

    def test_mongo_collection_names_no_duplicates(self):
        """Test that MONGO_COLLECTION_NAMES contains no duplicate values."""
        collection_names = self.config.MONGO_COLLECTION_NAMES
        unique_names = list(set(collection_names))
        self.assertEqual(len(collection_names), len(unique_names))

    def test_mongo_collection_names_not_empty(self):
        """Test that MONGO_COLLECTION_NAMES is not empty."""
        self.assertGreater(len(self.config.MONGO_COLLECTION_NAMES), 0)

    def test_mongo_collection_names_all_strings(self):
        """Test that all values in MONGO_COLLECTION_NAMES are strings."""
        for collection_name in self.config.MONGO_COLLECTION_NAMES:
            self.assertIsInstance(collection_name, str)

if __name__ == '__main__':
    unittest.main() 