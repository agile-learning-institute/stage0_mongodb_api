import unittest
from unittest.mock import Mock
import datetime
from bson.objectid import ObjectId
from configurator.utils.ejson_encoder import MongoJSONEncoder


class TestMongoJSONEncoder(unittest.TestCase):
    """Test suite for MongoJSONEncoder."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock Flask app for the encoder
        mock_app = Mock()
        self.encoder = MongoJSONEncoder(mock_app)

    def test_objectid_encoding(self):
        """Test ObjectId encoding."""
        # Create a test ObjectId
        test_id = ObjectId()
        
        # Encode it
        result = self.encoder.default(test_id)
        
        # Should be converted to string
        self.assertIsInstance(result, str)
        self.assertEqual(result, str(test_id))

    def test_datetime_encoding(self):
        """Test datetime encoding."""
        # Create a test datetime
        test_datetime = datetime.datetime(2023, 1, 15, 12, 30, 45)
        
        # Encode it
        result = self.encoder.default(test_datetime)
        
        # Should be converted to string
        self.assertIsInstance(result, str)
        self.assertEqual(result, str(test_datetime))

    def test_date_encoding(self):
        """Test date encoding."""
        # Create a test date
        test_date = datetime.date(2023, 1, 15)
        
        # Encode it
        result = self.encoder.default(test_date)
        
        # Should be converted to string
        self.assertIsInstance(result, str)
        self.assertEqual(result, str(test_date))

    def test_object_with_isoformat_method(self):
        """Test object with isoformat method."""
        # Create a mock object with isoformat method
        mock_obj = Mock()
        mock_obj.isoformat.return_value = "2023-01-15T12:30:45"
        
        # Encode it
        result = self.encoder.default(mock_obj)
        
        # Should be converted to string
        self.assertIsInstance(result, str)
        self.assertEqual(result, str(mock_obj))

    def test_regular_object_falls_back_to_parent(self):
        """Test that regular objects fall back to parent default method."""
        # Create a regular object
        regular_obj = {"key": "value"}
        
        # This should raise TypeError (parent's default behavior for dict)
        with self.assertRaises(TypeError):
            self.encoder.default(regular_obj)

    def test_string_object(self):
        """Test string object (should fall back to parent)."""
        # String should fall back to parent
        with self.assertRaises(TypeError):
            self.encoder.default("test string")

    def test_int_object(self):
        """Test int object (should fall back to parent)."""
        # Int should fall back to parent
        with self.assertRaises(TypeError):
            self.encoder.default(42)

    def test_list_object(self):
        """Test list object (should fall back to parent)."""
        # List should fall back to parent
        with self.assertRaises(TypeError):
            self.encoder.default([1, 2, 3])

    def test_none_object(self):
        """Test None object (should fall back to parent)."""
        # None should fall back to parent
        with self.assertRaises(TypeError):
            self.encoder.default(None)

    def test_multiple_objectid_encoding(self):
        """Test multiple ObjectId encoding."""
        # Create multiple ObjectIds
        ids = [ObjectId() for _ in range(3)]
        
        for obj_id in ids:
            result = self.encoder.default(obj_id)
            self.assertIsInstance(result, str)
            self.assertEqual(result, str(obj_id))

    def test_edge_case_datetime(self):
        """Test edge case datetime (epoch time)."""
        # Test epoch time
        epoch_datetime = datetime.datetime(1970, 1, 1, 0, 0, 0)
        
        result = self.encoder.default(epoch_datetime)
        self.assertIsInstance(result, str)
        self.assertEqual(result, str(epoch_datetime))

    def test_future_datetime(self):
        """Test future datetime."""
        # Test future date
        future_datetime = datetime.datetime(2030, 12, 31, 23, 59, 59)
        
        result = self.encoder.default(future_datetime)
        self.assertIsInstance(result, str)
        self.assertEqual(result, str(future_datetime))

    def test_custom_object_with_isoformat(self):
        """Test custom object with isoformat method."""
        class CustomDate:
            def __init__(self, year, month, day):
                self.year = year
                self.month = month
                self.day = day
            
            def isoformat(self):
                return f"{self.year:04d}-{self.month:02d}-{self.day:02d}"
        
        custom_date = CustomDate(2023, 1, 15)
        
        result = self.encoder.default(custom_date)
        self.assertIsInstance(result, str)
        self.assertEqual(result, str(custom_date))


if __name__ == '__main__':
    unittest.main() 