import unittest
from configurator.services.dictionary_services import OneOf

class TestOneOfMinimal(unittest.TestCase):
    def test_basic_construction_and_to_dict(self):
        """Test array-based format"""
        data = [
            {'type': 'object', 'properties': {}},
            {'type': 'string', 'description': 'test'}
        ]
        one_of = OneOf(data)
        result = one_of.to_dict()
        
        # Check that the structure is correct
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['type'], 'object')
        self.assertEqual(result[1]['type'], 'string')

    def test_empty_array_handling(self):
        """Test that the class handles empty arrays gracefully"""
        data = []
        one_of = OneOf(data)
        self.assertEqual(len(one_of.schemas), 0)
        result = one_of.to_dict()
        self.assertEqual(result, [])

    def test_single_schema_array(self):
        """Test array with single schema"""
        data = [{'type': 'string', 'description': 'single schema'}]
        one_of = OneOf(data)
        result = one_of.to_dict()
        
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['type'], 'string')

if __name__ == '__main__':
    unittest.main() 