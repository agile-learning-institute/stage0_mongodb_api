import unittest
from datetime import datetime
from configurator.utils.configurator_exception import ConfiguratorEvent

class TestConfiguratorEvent(unittest.TestCase):
    def setUp(self):
        self.test_event_id = "test_event_123"
        self.test_event_type = "test_type"
        self.test_event_data = {"key": "value", "number": 42}

    def test_configurator_event_initialization(self):
        event = ConfiguratorEvent(self.test_event_id, self.test_event_type)
        self.assertEqual(event.id, self.test_event_id)
        self.assertEqual(event.type, self.test_event_type)
        self.assertIsNone(event.data)
        self.assertIsInstance(event.starts, datetime)
        self.assertIsNone(event.ends)
        self.assertEqual(event.status, "PENDING")
        self.assertEqual(event.sub_events, [])

    def test_configurator_event_initialization_with_data(self):
        event = ConfiguratorEvent(self.test_event_id, self.test_event_type, self.test_event_data)
        self.assertEqual(event.id, self.test_event_id)
        self.assertEqual(event.type, self.test_event_type)
        self.assertEqual(event.data, self.test_event_data)
        self.assertIsInstance(event.starts, datetime)
        self.assertIsNone(event.ends)
        self.assertEqual(event.status, "PENDING")
        self.assertEqual(event.sub_events, [])

    def test_append_events(self):
        event = ConfiguratorEvent(self.test_event_id, self.test_event_type)
        event.append_events([])
        self.assertEqual(event.sub_events, [])
        sub_event = ConfiguratorEvent("sub_event_1", "sub_type")
        event.append_events([sub_event])
        self.assertEqual(len(event.sub_events), 1)
        self.assertEqual(event.sub_events[0], sub_event)
        sub_event_2 = ConfiguratorEvent("sub_event_2", "sub_type_2")
        sub_event_3 = ConfiguratorEvent("sub_event_3", "sub_type_3")
        event.append_events([sub_event_2, sub_event_3])
        self.assertEqual(len(event.sub_events), 3)
        self.assertIn(sub_event_2, event.sub_events)
        self.assertIn(sub_event_3, event.sub_events)

    def test_record_success(self):
        event = ConfiguratorEvent(self.test_event_id, self.test_event_type)
        event.record_success()
        self.assertEqual(event.status, "SUCCESS")
        self.assertIsInstance(event.ends, datetime)
        self.assertLessEqual(event.starts, event.ends)

    def test_record_failure(self):
        event = ConfiguratorEvent(self.test_event_id, self.test_event_type)
        failure_message = "Something went wrong"
        failure_data = {"code": 500}
        event.record_failure(failure_message, failure_data)
        self.assertEqual(event.status, "FAILURE")
        self.assertIsInstance(event.ends, datetime)
        expected_data = {"error": failure_message, "code": 500}
        self.assertEqual(event.data, expected_data)
        self.assertLessEqual(event.starts, event.ends)

    def test_record_failure_overwrites_existing_data(self):
        initial_data = {"initial": "data"}
        event = ConfiguratorEvent(self.test_event_id, self.test_event_type, initial_data)
        failure_message = "Something went wrong"
        event.record_failure(failure_message)
        expected_data = {"error": failure_message}
        self.assertEqual(event.data, expected_data)
        self.assertNotEqual(event.data, initial_data)

    def test_to_dict_with_minimal_data(self):
        event = ConfiguratorEvent(self.test_event_id, self.test_event_type)
        result = event.to_dict()
        self.assertEqual(result["id"], self.test_event_id)
        self.assertEqual(result["type"], self.test_event_type)
        self.assertIsNone(result["data"])
        self.assertIsInstance(result["starts"], datetime)
        self.assertIsNone(result["ends"])
        self.assertEqual(result["status"], "PENDING")
        self.assertEqual(result["sub_events"], [])

    def test_to_dict_with_complete_data(self):
        event = ConfiguratorEvent(self.test_event_id, self.test_event_type, self.test_event_data)
        sub_event = ConfiguratorEvent("sub_event", "sub_type")
        event.sub_events = [sub_event]
        event.record_success()
        result = event.to_dict()
        self.assertEqual(result["id"], self.test_event_id)
        self.assertEqual(result["type"], self.test_event_type)
        self.assertEqual(result["data"], self.test_event_data)
        self.assertIsInstance(result["starts"], datetime)
        self.assertIsInstance(result["ends"], datetime)
        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(len(result["sub_events"]), 1)
        self.assertEqual(result["sub_events"][0]["id"], "sub_event")
        self.assertEqual(result["sub_events"][0]["type"], "sub_type")

    def test_to_dict_after_failure(self):
        event = ConfiguratorEvent(self.test_event_id, self.test_event_type)
        failure_message = "Test failure"
        event.record_failure(failure_message)
        result = event.to_dict()
        self.assertEqual(result["id"], self.test_event_id)
        self.assertEqual(result["type"], self.test_event_type)
        expected_data = {"error": failure_message}
        self.assertEqual(result["data"], expected_data)
        self.assertIsInstance(result["starts"], datetime)
        self.assertIsInstance(result["ends"], datetime)
        self.assertEqual(result["status"], "FAILURE")
        self.assertEqual(result["sub_events"], [])

    def test_event_lifecycle(self):
        event = ConfiguratorEvent(self.test_event_id, self.test_event_type, self.test_event_data)
        self.assertEqual(event.status, "PENDING")
        self.assertIsNone(event.ends)
        sub_event = ConfiguratorEvent("sub_event", "sub_type")
        event.append_events([sub_event])
        event.record_success()
        self.assertEqual(event.status, "SUCCESS")
        self.assertIsInstance(event.ends, datetime)
        self.assertEqual(len(event.sub_events), 1)
        result = event.to_dict()
        self.assertEqual(result["status"], "SUCCESS")
        self.assertIsInstance(result["ends"], datetime)
        self.assertEqual(len(result["sub_events"]), 1)

if __name__ == '__main__':
    unittest.main() 