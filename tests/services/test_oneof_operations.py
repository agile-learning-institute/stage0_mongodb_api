import unittest
from configurator.services.dictionary_services import OneOf

class TestOneOfMinimal(unittest.TestCase):
    def test_basic_construction_and_to_dict(self):
        data = {'schemas': {'foo': {'type': 'object', 'properties': {}}}}
        one_of = OneOf(data)
        result = one_of.to_dict()
        
        # Check that the structure is correct
        self.assertIn('schemas', result)
        self.assertIn('foo', result['schemas'])
        self.assertEqual(result['schemas']['foo']['type'], 'object')
        self.assertIn('properties', result['schemas']['foo'])

if __name__ == '__main__':
    unittest.main() 