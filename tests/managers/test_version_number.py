import unittest
from stage0_mongodb_api.managers.version_number import VersionNumber

class TestVersionNumber(unittest.TestCase):
    def test_valid_version(self):
        """Test valid version string parsing and access."""
        version = VersionNumber("1.2.3.4")
        self.assertEqual(version.parts, [1, 2, 3, 4])
        self.assertEqual(str(version), "1.2.3.4")
        self.assertEqual(version.get_schema_version(), "1.2.3")
        self.assertEqual(version.get_enumerator_version(), 4)

    def test_invalid_format(self):
        """Test invalid version string formats."""
        invalid_versions = [
            "",           # Empty string
            "1.2.3",     # Too few components
            "1.2.3.4.5", # Too many components
            "a.b.c.d",   # Non-numeric
            "1.2.3.4.",  # Trailing dot
            "1..2.3.4",  # Double dot
            ".1.2.3.4",  # Leading dot
        ]
        
        for version in invalid_versions:
            with self.assertRaises(ValueError):
                VersionNumber(version)

    def test_invalid_range(self):
        """Test version numbers exceeding maximum allowed value."""
        invalid_versions = [
            "1000.0.0.0", # Exceeds MAX_VERSION
            "0.1000.0.0", # Exceeds MAX_VERSION
            "0.0.1000.0", # Exceeds MAX_VERSION
            "0.0.0.1000", # Exceeds MAX_VERSION
        ]
        
        for version in invalid_versions:
            with self.assertRaises(ValueError):
                VersionNumber(version)

    def test_version_comparison(self):
        """Test version comparison operators."""
        v1 = VersionNumber("1.2.3.4")
        v2 = VersionNumber("1.2.3.5")
        v3 = VersionNumber("1.2.3.4")
        
        # Test less than
        self.assertTrue(v1 < v2)
        self.assertFalse(v2 < v1)
        
        # Test equality
        self.assertTrue(v1 == v3)
        self.assertFalse(v1 == v2)
        
        # Test string comparison
        self.assertTrue(v1 < "1.2.3.5")
        self.assertTrue(v1 == "1.2.3.4")

if __name__ == '__main__':
    unittest.main() 