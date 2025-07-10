import os
import shutil
import tempfile
import json
import unittest
from flask import Flask
from configurator.server import app as real_app
from configurator.utils.config import Config
from unittest.mock import patch, Mock
from configurator.routes.migration_routes import create_migration_routes
from configurator.utils.configurator_exception import ConfiguratorException, ConfiguratorEvent

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
        """Test GET /api/migrations/ endpoint."""
        resp = self.app.get("/api/migrations/")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        # For successful responses, expect data directly, not wrapped in event envelope
        self.assertIn("mig1.json", data)
        self.assertIn("mig2.json", data)

    def test_get_migration(self):
        resp = self.app.get("/api/migrations/mig1.json/")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        # For successful responses, expect data directly, not wrapped in event envelope
        self.assertIsInstance(data, list)
        self.assertEqual(data, [{"$addFields": {"foo": "bar"}}])

    def test_get_migration_not_found(self):
        resp = self.app.get("/api/migrations/doesnotexist.json/")
        self.assertEqual(resp.status_code, 500)
        data = resp.get_json()
        self.assertIn("id", data)
        self.assertIn("type", data)
        self.assertIn("status", data)
        self.assertIn("data", data)
        self.assertEqual(data["status"], "FAILURE")

    def test_put_migration(self):
        resp = self.app.put("/api/migrations/mig1.json/", json=[{"$addFields": {"foo": "bar"}}])
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        # For successful responses, expect File object dict, not wrapped in event envelope
        self.assertIsInstance(data, dict)
        self.assertIn("name", data)

    def test_delete_migration(self):
        resp = self.app.delete("/api/migrations/mig1.json/")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        # For successful responses, expect ConfiguratorEvent with SUCCESS status
        self.assertIn("id", data)
        self.assertIn("type", data)
        self.assertIn("status", data)
        self.assertIn("data", data)
        self.assertEqual(data["status"], "SUCCESS")

    def test_delete_migration_not_found(self):
        resp = self.app.delete("/api/migrations/doesnotexist.json/")
        self.assertEqual(resp.status_code, 200)  # Now returns 200 with failure event
        data = resp.get_json()
        self.assertIn("id", data)
        self.assertIn("type", data)
        self.assertIn("status", data)
        self.assertIn("data", data)
        self.assertEqual(data["status"], "FAILURE")

class TestMigrationRoutes(unittest.TestCase):
    """Test cases for migration routes."""

    def setUp(self):
        """Set up test fixtures."""
        self.app = Flask(__name__)
        self.app.register_blueprint(create_migration_routes(), url_prefix='/api/migrations')
        self.client = self.app.test_client()

    @patch('configurator.routes.migration_routes.FileIO')
    def test_list_migrations_success(self, mock_file_io):
        """Test successful GET /api/migrations/."""
        # Arrange
        mock_file1 = Mock()
        mock_file1.name = "migration1.json"
        mock_file2 = Mock()
        mock_file2.name = "migration2.json"
        mock_files = [mock_file1, mock_file2]
        
        with patch('configurator.routes.migration_routes.FileIO') as mock_file_io:
            mock_file_io.get_documents.return_value = mock_files
            
            # Act
            response = self.client.get('/api/migrations/')
            
            # Assert
            self.assertEqual(response.status_code, 200)
            response_data = response.json
            self.assertEqual(response_data, ["migration1.json", "migration2.json"])

    @patch('configurator.routes.migration_routes.FileIO')
    def test_list_migrations_general_exception(self, mock_file_io):
        """Test GET /api/migrations/ when FileIO raises a general exception."""
        # Arrange
        mock_file_io.get_documents.side_effect = Exception("Unexpected error")

        # Act
        response = self.client.get('/api/migrations/')

        # Assert
        self.assertEqual(response.status_code, 500)
        response_data = response.json
        self.assertIn("id", response_data)
        self.assertIn("type", response_data)
        self.assertIn("status", response_data)
        self.assertIn("data", response_data)
        self.assertEqual(response_data["status"], "FAILURE")

    @patch('configurator.routes.migration_routes.FileIO')
    def test_get_migration_success(self, mock_file_io):
        """Test successful GET /api/migrations/<file_name>."""
        # Arrange
        mock_file_io.get_document.return_value = {"name": "test_migration", "operations": []}

        # Act
        response = self.client.get('/api/migrations/test_migration.json/')

        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = response.json
        self.assertEqual(response_data, {"name": "test_migration", "operations": []})

    @patch('configurator.routes.migration_routes.FileIO')
    def test_get_migration_general_exception(self, mock_file_io):
        """Test GET /api/migrations/<file_name> when FileIO raises a general exception."""
        # Arrange
        mock_file_io.get_document.side_effect = Exception("Unexpected error")

        # Act
        response = self.client.get('/api/migrations/test_migration.json/')

        # Assert
        self.assertEqual(response.status_code, 500)
        response_data = response.json
        self.assertIn("id", response_data)
        self.assertIn("type", response_data)
        self.assertIn("status", response_data)
        self.assertIn("data", response_data)
        self.assertEqual(response_data["status"], "FAILURE")

    @patch('configurator.routes.migration_routes.FileIO')
    def test_put_migration_success(self, mock_file_io):
        """Test successful PUT /api/migrations/<file_name>."""
        # Arrange
        test_data = {"name": "test_migration", "operations": []}
        mock_file = Mock()
        mock_file.to_dict.return_value = {"name": "test_migration.json", "size": 100}
        mock_file_io.put_document.return_value = mock_file

        # Act
        response = self.client.put('/api/migrations/test_migration.json/', json=test_data)

        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = response.json
        self.assertIsInstance(response_data, dict)
        self.assertIn("name", response_data)

    @patch('configurator.routes.migration_routes.FileIO')
    def test_put_migration_general_exception(self, mock_file_io):
        """Test PUT /api/migrations/<file_name> when FileIO raises a general exception."""
        # Arrange
        mock_file_io.put_document.side_effect = Exception("Unexpected error")
        test_data = {"name": "test_migration", "operations": []}

        # Act
        response = self.client.put('/api/migrations/test_migration.json/', json=test_data)

        # Assert
        self.assertEqual(response.status_code, 500)
        response_data = response.json
        self.assertIn("id", response_data)
        self.assertIn("type", response_data)
        self.assertIn("status", response_data)
        self.assertIn("data", response_data)
        self.assertEqual(response_data["status"], "FAILURE")

    @patch('configurator.routes.migration_routes.os.path.exists')
    @patch('configurator.routes.migration_routes.FileIO')
    def test_delete_migration_success(self, mock_file_io, mock_exists):
        """Test successful DELETE /api/migrations/<file_name>."""
        # Arrange
        mock_exists.return_value = True
        mock_event = Mock()
        mock_event.status = "SUCCESS"
        mock_file_io.delete_document.return_value = mock_event

        # Act
        response = self.client.delete('/api/migrations/test_migration.json/')

        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = response.json
        self.assertIn("id", response_data)
        self.assertIn("type", response_data)
        self.assertIn("status", response_data)
        self.assertIn("data", response_data)
        self.assertEqual(response_data["status"], "SUCCESS")

    @patch('configurator.routes.migration_routes.FileIO')
    def test_delete_migration_general_exception(self, mock_file_io):
        """Test DELETE /api/migrations/<file_name> when FileIO raises a general exception."""
        # Arrange
        mock_file_io.delete_document.side_effect = Exception("Unexpected error")

        # Act
        response = self.client.delete('/api/migrations/test_migration.json/')

        # Assert
        self.assertEqual(response.status_code, 200)  # Now returns 200 with failure event
        response_data = response.json
        self.assertIn("id", response_data)
        self.assertIn("type", response_data)
        self.assertIn("status", response_data)
        self.assertIn("data", response_data)
        self.assertEqual(response_data["status"], "FAILURE")

    def test_migrations_post_method_not_allowed(self):
        """Test that POST method is not allowed."""
        response = self.client.post('/api/migrations/')
        self.assertEqual(response.status_code, 405)

    def test_migrations_patch_method_not_allowed(self):
        """Test that PATCH method is not allowed for individual migrations."""
        response = self.client.patch('/api/migrations/test_migration.json/')
        self.assertEqual(response.status_code, 405)

    def test_get_migrations_success(self):
        """Test successful GET /api/migrations/."""
        # Arrange
        mock_file1 = Mock()
        mock_file1.name = "migration1.json"
        mock_file2 = Mock()
        mock_file2.name = "migration2.json"
        mock_files = [mock_file1, mock_file2]
        
        with patch('configurator.routes.migration_routes.FileIO') as mock_file_io:
            mock_file_io.get_documents.return_value = mock_files
            
            # Act
            response = self.client.get('/api/migrations/')
            
            # Assert
            self.assertEqual(response.status_code, 200)
            response_data = response.json
            self.assertEqual(response_data, ["migration1.json", "migration2.json"])

if __name__ == "__main__":
    unittest.main() 