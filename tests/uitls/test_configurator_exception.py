import unittest
from datetime import datetime
from configurator.utils.configurator_exception import ConfiguratorException, ConfiguratorEvent


class TestConfiguratorException(unittest.TestCase):
    """Test cases for ConfiguratorException class"""

    def test_configurator_exception_initialization(self):
        """Test ConfiguratorException initialization with message and event"""
        event = ConfiguratorEvent("test_id", "test_type")
        exception = ConfiguratorException("Test error message", event)
        
        self.assertEqual(exception.message, "Test error message")
        self.assertEqual(exception.event, event)
        self.assertIsInstance(exception, Exception)

    def test_configurator_exception_str_representation(self):
        """Test string representation of ConfiguratorException"""
        event = ConfiguratorEvent("test_id", "test_type")
        exception = ConfiguratorException("Test error message", event)
        
        self.assertEqual(str(exception), "Test error message")

    def test_configurator_exception_with_empty_message(self):
        """Test ConfiguratorException with empty message"""
        event = ConfiguratorEvent("test_id", "test_type")
        exception = ConfiguratorException("", event)
        
        self.assertEqual(exception.message, "")
        self.assertEqual(str(exception), "")


class TestConfiguratorEvent(unittest.TestCase):
    """Test cases for ConfiguratorEvent class"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_event_id = "test_event_123"
        self.test_event_type = "test_type"
        self.test_event_data = {"key": "value", "number": 42}

    def test_configurator_event_initialization(self):
        """Test ConfiguratorEvent initialization with required parameters"""
        event = ConfiguratorEvent(self.test_event_id, self.test_event_type)
        
        self.assertEqual(event.id, self.test_event_id)
        self.assertEqual(event.type, self.test_event_type)
        self.assertIsNone(event.data)
        self.assertIsInstance(event.starts, datetime)
        self.assertIsNone(event.ends)
        self.assertEqual(event.status, "PENDING")
        self.assertEqual(event.sub_events, [])

    def test_configurator_event_initialization_with_data(self):
        """Test ConfiguratorEvent initialization with optional data parameter"""
        event = ConfiguratorEvent(self.test_event_id, self.test_event_type, self.test_event_data)
        
        self.assertEqual(event.id, self.test_event_id)
        self.assertEqual(event.type, self.test_event_type)
        self.assertEqual(event.data, self.test_event_data)
        self.assertIsInstance(event.starts, datetime)
        self.assertIsNone(event.ends)
        self.assertEqual(event.status, "PENDING")
        self.assertEqual(event.sub_events, [])

    def test_append_events(self):
        """Test append_events method"""
        event = ConfiguratorEvent(self.test_event_id, self.test_event_type)
        
        # Test with empty list
        event.append_events([])
        self.assertEqual(event.sub_events, [])
        
        # Test with single event
        sub_event = ConfiguratorEvent("sub_event_1", "sub_type")
        event.append_events([sub_event])
        self.assertEqual(len(event.sub_events), 1)
        self.assertEqual(event.sub_events[0], sub_event)
        
        # Test with multiple events
        sub_event_2 = ConfiguratorEvent("sub_event_2", "sub_type_2")
        sub_event_3 = ConfiguratorEvent("sub_event_3", "sub_type_3")
        event.append_events([sub_event_2, sub_event_3])
        self.assertEqual(len(event.sub_events), 3)
        self.assertIn(sub_event_2, event.sub_events)
        self.assertIn(sub_event_3, event.sub_events)

    def test_record_success(self):
        """Test record_success method"""
        event = ConfiguratorEvent(self.test_event_id, self.test_event_type)
        event.record_success()
        self.assertEqual(event.status, "SUCCESS")
        self.assertIsInstance(event.ends, datetime)
        self.assertLessEqual(event.starts, event.ends)

    def test_record_failure(self):
        """Test record_failure method"""
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
        """Test that record_failure overwrites existing data"""
        initial_data = {"initial": "data"}
        event = ConfiguratorEvent(self.test_event_id, self.test_event_type, initial_data)
        
        failure_message = "Something went wrong"
        event.record_failure(failure_message)
        
        expected_data = {"error": failure_message}
        self.assertEqual(event.data, expected_data)
        self.assertNotEqual(event.data, initial_data)

    def test_to_dict_with_minimal_data(self):
        """Test to_dict method with minimal event data"""
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
        """Test to_dict method with complete event data"""
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
        """Test to_dict method after recording failure"""
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
        """Test complete event lifecycle from creation to completion"""
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
