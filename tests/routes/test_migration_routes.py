import os
import shutil
import tempfile
import json
import unittest
from flask import Flask
from configurator.server import app as real_app
from configurator.utils.config import Config

class MigrationRoutesTestCase(unittest.TestCase):
    def setUp(self):
        # Create a temp directory for migrations
        self.temp_dir = tempfile.mkdtemp()
        self.migrations_dir = os.path.join(self.temp_dir, "migrations")
        os.makedirs(self.migrations_dir, exist_ok=True)
        # Patch config to use temp dir
        self._original_input_folder = Config.get_instance().INPUT_FOLDER
        Config.get_instance().INPUT_FOLDER = self.temp_dir
        # Create some fake migration files
        self.migration1 = os.path.join(self.migrations_dir, "mig1.json")
        self.migration2 = os.path.join(self.migrations_dir, "mig2.json")
        with open(self.migration1, "w") as f:
            json.dump([{"$addFields": {"foo": "bar"}}], f)
        with open(self.migration2, "w") as f:
            json.dump([{"$unset": ["foo"]}], f)
        # Use Flask test client
        self.app = real_app.test_client()

    def tearDown(self):
        Config.get_instance().INPUT_FOLDER = self._original_input_folder
        shutil.rmtree(self.temp_dir)

    def test_list_migrations(self):
        resp = self.app.get("/api/migrations/")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("mig1.json", data)
        self.assertIn("mig2.json", data)

    def test_get_migration(self):
        resp = self.app.get("/api/migrations/mig1.json/")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIsInstance(data, list)
        self.assertEqual(data[0]["$addFields"], {"foo": "bar"})

    def test_get_migration_not_found(self):
        resp = self.app.get("/api/migrations/doesnotexist.json/")
        self.assertEqual(resp.status_code, 404)
        data = resp.get_json()
        self.assertIn("error", str(data))

    def test_put_migration(self):
        new_content = [{"$addFields": {"bar": "baz"}}]
        resp = self.app.put(
            "/api/migrations/newmig.json/",
            data=json.dumps(new_content),
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, 200)
        new_file = os.path.join(self.migrations_dir, "newmig.json")
        self.assertTrue(os.path.exists(new_file))
        with open(new_file, "r") as f:
            loaded = json.load(f)
        self.assertEqual(loaded[0]["$addFields"], {"bar": "baz"})

    def test_delete_migration(self):
        resp = self.app.delete("/api/migrations/mig1.json/")
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(os.path.exists(self.migration1))
        # Should not affect other file
        self.assertTrue(os.path.exists(self.migration2))

    def test_delete_migration_not_found(self):
        resp = self.app.delete("/api/migrations/doesnotexist.json/")
        self.assertEqual(resp.status_code, 404)
        data = resp.get_json()
        self.assertIn("error", str(data))

    def test_clean_migrations(self):
        resp = self.app.patch("/api/migrations/")
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(os.path.exists(self.migration1))
        self.assertFalse(os.path.exists(self.migration2))

if __name__ == "__main__":
    unittest.main() 