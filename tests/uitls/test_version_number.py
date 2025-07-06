import unittest
from stage0_mongodb_api.managers.version_number import VersionNumber

class TestVersionNumber(unittest.TestCase):
    def test_valid_version(self):
        """Test valid version string parsing and access."""
        # Test without collection name
        version = VersionNumber("1.2.3.4")
        self.assertEqual(version.parts, [1, 2, 3, 4])
        self.assertEqual(str(version), "1.2.3.4")
        self.assertEqual(version.get_schema_version(), "1.2.3")
        self.assertEqual(version.get_enumerator_version(), 4)
        self.assertIsNone(version.collection_name)

        # Test with collection name
        version = VersionNumber("user.1.2.3.4")
        self.assertEqual(version.parts, [1, 2, 3, 4])
        self.assertEqual(str(version), "user.1.2.3.4")
        self.assertEqual(version.get_schema_version(), "user.1.2.3")
        self.assertEqual(version.get_enumerator_version(), 4)
        self.assertEqual(version.collection_name, "user")

    def test_invalid_format(self):
        """Test invalid version string formats."""
        invalid_versions = [
            "",           # Empty string
            "1.2.3",     # Too few components
            "1.2.3.4.5.6", # Too many components
            "a.b.c.d",   # Non-numeric
            "1.2.3.4.",  # Trailing dot
            "1..2.3.4",  # Double dot
            ".1.2.3.4",  # Leading dot
            "user.1.2.3", # Collection with too few components
            "user.1.2.3.4.5", # Collection with too many components
            "user..1.2.3.4", # Collection with double dot
            "user.1.2.3.4.", # Collection with trailing dot
            ".user.1.2.3.4", # Collection with leading dot
        ]
        
        for version in invalid_versions:
            with self.assertRaises(ValueError, msg=f"Valid version: {version}"):
                VersionNumber(version)

    def test_invalid_range(self):
        """Test version numbers exceeding maximum allowed value."""
        invalid_versions = [
            "1000.0.0.0", # Exceeds MAX_VERSION
            "0.1000.0.0", # Exceeds MAX_VERSION
            "0.0.1000.0", # Exceeds MAX_VERSION
            "0.0.0.1000", # Exceeds MAX_VERSION
            "user.1000.0.0.0", # Collection with exceeds MAX_VERSION
            "user.0.1000.0.0", # Collection with exceeds MAX_VERSION
            "user.0.0.1000.0", # Collection with exceeds MAX_VERSION
            "user.0.0.0.1000", # Collection with exceeds MAX_VERSION
        ]
        
        for version in invalid_versions:
            with self.assertRaises(ValueError):
                VersionNumber(version)

    def test_version_comparison_naked(self):
        """Test version comparison with naked version numbers (no collection name)."""
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

    def test_version_comparison_full(self):
        """Test version comparison with full version numbers (including collection name)."""
        v1 = VersionNumber("user.1.2.3.4")
        v2 = VersionNumber("user.1.2.3.5")
        v3 = VersionNumber("user.1.2.3.4")
        
        # Test less than
        self.assertTrue(v1 < v2)
        self.assertFalse(v2 < v1)
        
        # Test equality
        self.assertTrue(v1 == v3)
        self.assertFalse(v1 == v2)
        
        # Test string comparison
        self.assertTrue(v1 < "user.1.2.3.5")
        self.assertTrue(v1 == "user.1.2.3.4")

    def test_version_comparison_mixed(self):
        """Test version comparison between naked and full version numbers."""
        v1 = VersionNumber("1.2.3.4")
        v2 = VersionNumber("user.1.2.3.4")
        v3 = VersionNumber("other.1.2.3.4")
        v4 = VersionNumber("1.2.3.5")
        v5 = VersionNumber("user.1.2.3.5")
        
        # Test equality ignoring collection name
        self.assertTrue(v1 == v2)
        self.assertTrue(v1 == v3)
        self.assertTrue(v2 == v3)
        
        # Test less than ignoring collection name
        self.assertTrue(v1 < v4)
        self.assertTrue(v1 < v5)
        self.assertTrue(v2 < v4)
        self.assertTrue(v2 < v5)
        
        # Test greater than ignoring collection name
        self.assertTrue(v4 > v1)
        self.assertTrue(v4 > v2)
        self.assertTrue(v5 > v1)
        self.assertTrue(v5 > v2)

if __name__ == '__main__':
    unittest.main() 