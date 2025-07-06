import unittest
from configurator.utils.version_number import VersionNumber
from configurator.utils.configurator_exception import ConfiguratorException

class TestVersionNumber(unittest.TestCase):
    def test_valid_version(self):
        """Test valid version string parsing and access."""
        # Test with collection name
        version = VersionNumber("user.1.2.3.4")
        self.assertEqual(version.parts[0], "user")  # Collection name
        self.assertEqual(version.parts[1:], [1, 2, 3, 4])  # Numeric parts
        self.assertEqual(str(version), "user.1.2.3.yaml")
        self.assertEqual(version.get_schema_filename(), "user.1.2.3.yaml")
        self.assertEqual(version.get_enumerator_version(), 4)
        self.assertEqual(version.get_version_str(), "1.2.3.4")

    def test_invalid_format(self):
        """Test invalid version string formats."""
        invalid_versions = [
            "",           # Empty string
            "1.2.3.4",   # Too few components (needs 5)
            "1.2.3.4.5.6", # Too many components
            "user.a.2.3.4",   # Non-numeric part
            "user.1.2.3.4.",  # Trailing dot
            "user..1.2.3.4",  # Double dot
            ".user.1.2.3.4",  # Leading dot
        ]
        
        for version in invalid_versions:
            with self.assertRaises(ConfiguratorException, msg=f"Should fail for: {version}"):
                VersionNumber(version)

    def test_version_comparison(self):
        """Test version comparison."""
        v1 = VersionNumber("user.1.2.3.4")
        v2 = VersionNumber("user.1.2.3.5")
        v3 = VersionNumber("user.1.2.3.4")
        v4 = VersionNumber("other.1.2.3.4")
        
        # Test less than
        self.assertTrue(v1 < v2)
        self.assertFalse(v2 < v1)
        
        # Test equality (ignores collection name)
        self.assertTrue(v1 == v3)
        self.assertTrue(v1 == v4)  # Same numeric parts, different collection
        self.assertFalse(v1 == v2)
        
        # Test greater than
        self.assertTrue(v2 > v1)
        self.assertFalse(v1 > v2)
        
        # Test string comparison
        self.assertTrue(v1 < "user.1.2.3.5")
        self.assertTrue(v1 == "other.1.2.3.4")  # Same numeric parts

    def test_get_schema_filename(self):
        """Test schema filename generation."""
        version = VersionNumber("user.1.2.3.4")
        self.assertEqual(version.get_schema_filename(), "user.1.2.3.yaml")
        
        version2 = VersionNumber("collection.10.20.30.40")
        self.assertEqual(version2.get_schema_filename(), "collection.10.20.30.yaml")

    def test_get_enumerator_version(self):
        """Test enumerator version extraction."""
        version = VersionNumber("user.1.2.3.4")
        self.assertEqual(version.get_enumerator_version(), 4)
        
        version2 = VersionNumber("collection.10.20.30.40")
        self.assertEqual(version2.get_enumerator_version(), 40)

    def test_get_version_str(self):
        """Test version string without collection name."""
        version = VersionNumber("user.1.2.3.4")
        self.assertEqual(version.get_version_str(), "1.2.3.4")
        
        version2 = VersionNumber("collection.10.20.30.40")
        self.assertEqual(version2.get_version_str(), "10.20.30.40")

    def test_str_representation(self):
        """Test string representation."""
        version = VersionNumber("user.1.2.3.4")
        self.assertEqual(str(version), "user.1.2.3.yaml")

    def test_parts_structure(self):
        """Test the internal parts structure."""
        version = VersionNumber("user.1.2.3.4")
        self.assertEqual(len(version.parts), 5)
        self.assertEqual(version.parts[0], "user")  # Collection name (string)
        self.assertEqual(version.parts[1:], [1, 2, 3, 4])  # Numeric parts

if __name__ == '__main__':
    unittest.main() 