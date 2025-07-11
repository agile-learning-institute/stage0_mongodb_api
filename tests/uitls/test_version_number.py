import unittest
from configurator.utils.version_number import VersionNumber
from configurator.utils.configurator_exception import ConfiguratorException

class TestVersionNumber(unittest.TestCase):
    def test_valid_version(self):
        """Test valid version string parsing and access."""
        # Test with collection name and enumerator
        version = VersionNumber("user.1.2.3.4")
        self.assertEqual(version.parts[0], "user")  # Collection name
        self.assertEqual(version.parts[1:], [1, 2, 3, 4])  # Numeric parts
        self.assertEqual(str(version), "user.1.2.3.yaml")
        self.assertEqual(version.get_schema_filename(), "user.1.2.3.yaml")
        self.assertEqual(version.get_enumerator_version(), 4)
        self.assertEqual(version.get_version_str(), "1.2.3.4")
        
        # Test with collection name without enumerator (defaults to 0)
        version_no_enum = VersionNumber("user.1.2.3")
        self.assertEqual(version_no_enum.parts[0], "user")  # Collection name
        self.assertEqual(version_no_enum.parts[1:], [1, 2, 3, 0])  # Numeric parts with default enumerator
        self.assertEqual(str(version_no_enum), "user.1.2.3.yaml")
        self.assertEqual(version_no_enum.get_schema_filename(), "user.1.2.3.yaml")
        self.assertEqual(version_no_enum.get_enumerator_version(), 0)
        self.assertEqual(version_no_enum.get_version_str(), "1.2.3.0")

    def test_invalid_format(self):
        """Test invalid version string formats."""
        invalid_versions = [
            "",           # Empty string
            "1.2.3",     # Too few components (needs at least 4)
            "1.2.3.4.5.6", # Too many components
            "user.a.2.3.4",   # Non-numeric part
            "user.1.2.3.4.",  # Trailing dot
            "user..1.2.3.4",  # Double dot
            ".user.1.2.3.4",  # Leading dot
            "user.1.2.a.4",   # Non-numeric part in middle
            "user.1.2.3.a",   # Non-numeric enumerator
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
        v5 = VersionNumber("user.1.2.3")  # Default enumerator 0
        
        # Test less than
        self.assertTrue(v1 < v2)
        self.assertFalse(v2 < v1)
        
        # Test equality (ignores collection name)
        self.assertTrue(v1 == v3)
        self.assertTrue(v1 == v4)  # Same numeric parts, different collection
        self.assertFalse(v1 == v2)
        
        # Test with default enumerator
        self.assertTrue(v5 < v1)  # 1.2.3.0 < 1.2.3.4
        self.assertTrue(v1 > v5)  # 1.2.3.4 > 1.2.3.0
        
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
        
        # Test with default enumerator
        version3 = VersionNumber("user.1.2.3")
        self.assertEqual(version3.get_schema_filename(), "user.1.2.3.yaml")

    def test_get_enumerator_version(self):
        """Test enumerator version extraction."""
        version = VersionNumber("user.1.2.3.4")
        self.assertEqual(version.get_enumerator_version(), 4)
        
        version2 = VersionNumber("collection.10.20.30.40")
        self.assertEqual(version2.get_enumerator_version(), 40)
        
        # Test with default enumerator
        version3 = VersionNumber("user.1.2.3")
        self.assertEqual(version3.get_enumerator_version(), 0)

    def test_get_version_str(self):
        """Test version string without collection name."""
        version = VersionNumber("user.1.2.3.4")
        self.assertEqual(version.get_version_str(), "1.2.3.4")
        
        version2 = VersionNumber("collection.10.20.30.40")
        self.assertEqual(version2.get_version_str(), "10.20.30.40")
        
        # Test with default enumerator
        version3 = VersionNumber("user.1.2.3")
        self.assertEqual(version3.get_version_str(), "1.2.3.0")

    def test_str_representation(self):
        """Test string representation."""
        version = VersionNumber("user.1.2.3.4")
        self.assertEqual(str(version), "user.1.2.3.yaml")
        
        # Test with default enumerator
        version2 = VersionNumber("user.1.2.3")
        self.assertEqual(str(version2), "user.1.2.3.yaml")

    def test_parts_structure(self):
        """Test the internal parts structure."""
        version = VersionNumber("user.1.2.3.4")
        self.assertEqual(len(version.parts), 5)
        self.assertEqual(version.parts[0], "user")  # Collection name (string)
        self.assertEqual(version.parts[1:], [1, 2, 3, 4])  # Numeric parts
        
        # Test with default enumerator
        version2 = VersionNumber("user.1.2.3")
        self.assertEqual(len(version2.parts), 5)
        self.assertEqual(version2.parts[0], "user")  # Collection name (string)
        self.assertEqual(version2.parts[1:], [1, 2, 3, 0])  # Numeric parts with default enumerator

if __name__ == '__main__':
    unittest.main() 