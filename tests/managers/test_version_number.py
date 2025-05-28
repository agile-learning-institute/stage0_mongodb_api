import unittest
from stage0_mongodb_api.managers.version_number import VersionNumber

class TestVersionNumber(unittest.TestCase):
    def test_schema_version_parsing(self):
        """Test parsing of schema version strings (three parts)"""
        # Test valid schema versions
        version = VersionNumber("1.2.3", is_collection_version=False)
        self.assertEqual(version.parts, [1, 2, 3])
        self.assertEqual(str(version), "1.2.3")
        self.assertEqual(version.get_schema_version(), "1.2.3")
        self.assertIsNone(version.get_enumerator_version())
        
        # Test single digit versions
        version = VersionNumber("1.0.0", is_collection_version=False)
        self.assertEqual(version.parts, [1, 0, 0])
        
        # Test maximum values
        version = VersionNumber("999.999.999", is_collection_version=False)
        self.assertEqual(version.parts, [999, 999, 999])

    def test_collection_version_parsing(self):
        """Test parsing of collection version strings (four parts)"""
        # Test valid collection versions
        version = VersionNumber("1.2.3.4", is_collection_version=True)
        self.assertEqual(version.parts, [1, 2, 3, 4])
        self.assertEqual(str(version), "1.2.3.4")
        self.assertEqual(version.get_schema_version(), "1.2.3")
        self.assertEqual(version.get_enumerator_version(), 4)
        
        # Test single digit versions
        version = VersionNumber("1.0.0.1", is_collection_version=True)
        self.assertEqual(version.parts, [1, 0, 0, 1])
        
        # Test maximum values
        version = VersionNumber("999.999.999.999", is_collection_version=True)
        self.assertEqual(version.parts, [999, 999, 999, 999])

    def test_invalid_schema_version_constructor(self):
        """Test that invalid schema version strings raise ValueError"""
        invalid_versions = [
            "",           # Empty string
            "1.2",       # Too few components
            "1.2.3.4",   # Too many components
            "a.b.c",     # Non-numeric
            "1.2.3.",    # Trailing dot
            "1..2.3",    # Double dot
            ".1.2.3",    # Leading dot
            "1000.0.0",  # Exceeds MAX_VERSION
            "0.1000.0",  # Exceeds MAX_VERSION
            "0.0.1000",  # Exceeds MAX_VERSION
        ]
        
        for invalid_version in invalid_versions:
            with self.assertRaises(ValueError):
                VersionNumber(invalid_version, is_collection_version=False)

    def test_invalid_collection_version_constructor(self):
        """Test that invalid collection version strings raise ValueError"""
        invalid_versions = [
            "",           # Empty string
            "1.2.3",     # Too few components
            "1.2.3.4.5", # Too many components
            "a.b.c.d",   # Non-numeric
            "1.2.3.4.",  # Trailing dot
            "1..2.3.4",  # Double dot
            ".1.2.3.4",  # Leading dot
            "1000.0.0.0", # Exceeds MAX_VERSION
            "0.1000.0.0", # Exceeds MAX_VERSION
            "0.0.1000.0", # Exceeds MAX_VERSION
            "0.0.0.1000", # Exceeds MAX_VERSION
        ]
        
        for invalid_version in invalid_versions:
            with self.assertRaises(ValueError):
                VersionNumber(invalid_version, is_collection_version=True)

    def test_version_comparison(self):
        """Test version comparison operators"""
        # Schema version comparisons
        v1 = VersionNumber("1.2.3", is_collection_version=False)
        v2 = VersionNumber("1.2.4", is_collection_version=False)
        v3 = VersionNumber("1.2.3", is_collection_version=False)
        
        self.assertTrue(v1 < v2)
        self.assertFalse(v2 < v1)
        self.assertTrue(v1 == v3)
        self.assertFalse(v1 == v2)
        
        # Collection version comparisons
        v4 = VersionNumber("1.2.3.4", is_collection_version=True)
        v5 = VersionNumber("1.2.3.5", is_collection_version=True)
        v6 = VersionNumber("1.2.3.4", is_collection_version=True)
        
        self.assertTrue(v4 < v5)
        self.assertFalse(v5 < v4)
        self.assertTrue(v4 == v6)
        self.assertFalse(v4 == v5)
        
        # Test string comparison
        self.assertTrue(v1 < "1.2.4")
        self.assertTrue(v1 == "1.2.3")
        self.assertTrue(v4 < "1.2.3.5")
        self.assertTrue(v4 == "1.2.3.4")

    def test_from_schema_name(self):
        """Test parsing schema names into collection name and version"""
        # Test valid schema names
        collection_name, version = VersionNumber.from_schema_name("user.1.2.3")
        self.assertEqual(collection_name, "user")
        self.assertEqual(str(version), "1.2.3")
        self.assertFalse(version.is_collection_version)
        
        # Test invalid schema names
        invalid_names = [
            "",              # Empty string
            "user",         # No version
            "user.1.2",     # Too few components
            "user.1.2.3.4", # Too many components
            "user.a.b.c",   # Non-numeric version
        ]
        
        for invalid_name in invalid_names:
            with self.assertRaises(ValueError):
                VersionNumber.from_schema_name(invalid_name)

    def test_from_collection_config(self):
        """Test parsing collection configs into collection name and version"""
        # Test valid collection configs
        collection_name, version = VersionNumber.from_collection_config("user", "1.2.3.4")
        self.assertEqual(collection_name, "user")
        self.assertEqual(str(version), "1.2.3.4")
        self.assertTrue(version.is_collection_version)
        
        # Test invalid collection configs
        invalid_configs = [
            ("", "1.2.3.4"),      # Empty collection name
            ("user", ""),         # Empty version
            ("user", "1.2.3"),    # Too few components
            ("user", "1.2.3.4.5"), # Too many components
            ("user", "a.b.c.d"),  # Non-numeric version
        ]
        
        for collection_name, version in invalid_configs:
            with self.assertRaises(ValueError):
                VersionNumber.from_collection_config(collection_name, version)

if __name__ == '__main__':
    unittest.main() 