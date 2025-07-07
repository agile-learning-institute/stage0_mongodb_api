import unittest
from flask import Flask, jsonify
from configurator.utils.route_decorators import handle_errors
from configurator.utils.configurator_exception import ConfiguratorException, ConfiguratorEvent

class TestRouteDecorator(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        self.app = app
        
        @app.route('/config-exception')
        @handle_errors("test config exception")
        def config_exception():
            event = ConfiguratorEvent(event_id="TEST-01", event_type="TEST_EVENT")
            raise ConfiguratorException("Test error", event)
        
        @app.route('/generic-exception')
        @handle_errors("test generic exception")
        def generic_exception():
            raise Exception("Generic error")
        
        self.client = app.test_client()

    def test_configurator_exception(self):
        resp = self.client.get('/config-exception')
        self.assertEqual(resp.status_code, 500)
        data = resp.get_json()
        self.assertIn('id', data)
        self.assertEqual(data['id'], 'TEST-01')
        self.assertEqual(data['type'], 'TEST_EVENT')

    def test_generic_exception(self):
        resp = self.client.get('/generic-exception')
        self.assertEqual(resp.status_code, 500)
        data = resp.get_json()
        self.assertIsInstance(data, str)
        self.assertIn('Generic error', data)

if __name__ == '__main__':
    unittest.main() 