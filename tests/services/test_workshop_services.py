import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from stage0_py_utils import Config
from stage0_fran.services.workshop_services import WorkshopServices

class TestWorkshopServices(unittest.IsolatedAsyncioTestCase):

    @patch('stage0_fran.services.workshop_services.MongoIO.get_instance')
    @patch('stage0_fran.services.workshop_services.Config.get_instance')
    def test_get_workshops(self, mock_config, mock_mongo):
        mock_mongo_instance = MagicMock()
        mock_mongo.return_value = mock_mongo_instance
        mock_config.return_value = MagicMock()
        mock_mongo_instance.get_documents.return_value = [{"_id": "ws1", "name": "Workshop 1"}]

        token = {"user_id": "test_user"}
        result = WorkshopServices.get_workshops("Workshop", token)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "Workshop 1")

    @patch('stage0_fran.services.workshop_services.MongoIO.get_instance')
    @patch('stage0_fran.services.workshop_services.Config.get_instance')
    def test_get_workshop(self, mock_config, mock_mongo):
        mock_mongo_instance = MagicMock()
        mock_mongo.return_value = mock_mongo_instance
        mock_config.return_value = MagicMock()
        mock_mongo_instance.get_document.return_value = {"_id": "ws1", "name": "Workshop 1"}

        token = {"user_id": "test_user"}
        result = WorkshopServices.get_workshop("ws1", token)
        self.assertEqual(result["_id"], "ws1")

    @patch('stage0_fran.services.workshop_services.MongoIO.get_instance')
    @patch('stage0_fran.services.workshop_services.ChainServices.get_chain')
    @patch('stage0_fran.services.workshop_services.Config.get_instance')
    def test_add_workshop(self, mock_config, mock_get_chain, mock_mongo):
        mock_config_instance = MagicMock()
        mock_config.return_value = mock_config_instance
        mock_mongo_instance = MagicMock()
        mock_mongo.return_value = mock_mongo_instance
        mock_get_chain.return_value = {"exercises": ["exercise1"]}
        mock_mongo_instance.create_document.return_value = "ws1"
        mock_mongo_instance.get_document.return_value = {"_id": "ws1", "name": "New Workshop"}

        token = {"user_id": "test_user"}
        breadcrumb = {"timestamp": "now"}
        data = {"name": "New Workshop"}

        result = WorkshopServices.add_workshop("chain1", data, token, breadcrumb)
        self.assertEqual(result["_id"], "ws1")

    @patch('stage0_fran.services.workshop_services.MongoIO.get_instance')
    @patch('stage0_fran.services.workshop_services.Config.get_instance')
    def test_update_workshop(self, mock_config, mock_mongo):
        mock_mongo_instance = MagicMock()
        mock_mongo.return_value = mock_mongo_instance
        mock_config.return_value = MagicMock()
        mock_mongo_instance.update_document.return_value = {"_id": "ws1", "updated": True}

        token = {"user_id": "test_user"}
        breadcrumb = {"timestamp": "now"}
        data = {"name": "Updated Workshop"}

        result = WorkshopServices.update_workshop("ws1", data, token, breadcrumb)
        self.assertEqual(result["updated"], True)

    @patch('stage0_fran.services.workshop_services.MongoIO.get_instance')
    def test_start_workshop(self, mock_get_instance):
        config = Config.get_instance()
        mock_mongo_instance = mock_get_instance.return_value
        expected_data = {
            "status": config.ACTIVE_STATUS,
            "when": {"from": datetime.now(timezone.utc)}
        }
        expected_data["last_saved"] = {"timestamp": "now"}
        token = {"user_id": "test_user"}
        breadcrumb = {"timestamp": "now"}
        mock_mongo_instance.update_document.return_value = {"_id": "ws1", "status": config.ACTIVE_STATUS}

        result = WorkshopServices.start_workshop("ws1", token, breadcrumb)

        self.assertEqual(result["status"], config.ACTIVE_STATUS)
        mock_mongo_instance.update_document.assert_called_once()

    def _assert_update(self, mock_get_instance, current_workshop, expected_update, token, breadcrumb):
        # Create the instance mock and attach it to the return value
        mock_mongo_instance = mock_get_instance.return_value
        mock_mongo_instance.get_document.return_value = current_workshop
        mock_mongo_instance.update_document.return_value = {"_id": "ws1", "updated": True}

        # Execute
        result = WorkshopServices.advance_workshop("ws1", token, breadcrumb)

        # Validate
        self.assertEqual(result["updated"], True)
        mock_mongo_instance.update_document.assert_called_once()
        _, kwargs = mock_mongo_instance.update_document.call_args
        self.assertEqual(kwargs["set_data"], expected_update)

    @patch('stage0_fran.services.workshop_services.MongoIO.get_instance')
    def test_advance_workshop_starting(self, mock_get_instance):
        # Setup Test Data
        config = Config.get_instance()
        token = {"user_id": "test_user"}
        breadcrumb = {"timestamp": "now"}
        current_workshop = {
            "_id": "ws1",
            "status": config.ACTIVE_STATUS,
            "current_exercise": 0,
            "exercises": [{"status": config.ACTIVE_STATUS}, {"status": config.PENDING_STATUS}, {"status": config.PENDING_STATUS}]
        }
        expected_update = {
            "last_saved": breadcrumb,
            "exercises.0.status": config.COMPLETED_STATUS,
            "current_exercise": 1,
            "exercises.1.status": config.PENDING_STATUS
        }
        self._assert_update(mock_get_instance, current_workshop, expected_update, token, breadcrumb)

    @patch('stage0_fran.services.workshop_services.MongoIO.get_instance')
    def test_advance_workshop_progress(self, mock_get_instance):
        # Setup Test Data
        config = Config.get_instance()
        token = {"user_id": "test_user"}
        breadcrumb = {"timestamp": "now"}
        current_workshop = {
            "_id": "ws1",
            "status": config.ACTIVE_STATUS,
            "current_exercise": 1,
            "exercises": [{"status": config.COMPLETED_STATUS}, {"status": config.ACTIVE_STATUS}, {"status": config.PENDING_STATUS}]
        }
        expected_update = {
            "last_saved": breadcrumb,
            "exercises.1.status": config.COMPLETED_STATUS,
            "current_exercise": 2,
            "exercises.2.status": config.PENDING_STATUS
        }
        self._assert_update(mock_get_instance, current_workshop, expected_update, token, breadcrumb)
        
    @patch('stage0_fran.services.workshop_services.MongoIO.get_instance')
    def test_advance_workshop_finish(self, mock_get_instance):
        # Setup Test Data
        config = Config.get_instance()
        token = {"user_id": "test_user"}
        breadcrumb = {"timestamp": "now"}
        current_workshop = {
            "_id": "ws1",
            "status": config.ACTIVE_STATUS,
            "current_exercise": 2,
            "exercises": [{"status": config.COMPLETED_STATUS}, {"status": config.COMPLETED_STATUS}, {"status": config.ACTIVE_STATUS}]
        }
        expected_update = {
            "last_saved": breadcrumb,
            "status": config.COMPLETED_STATUS,
            "exercises.2.status": config.COMPLETED_STATUS,
        }
        self._assert_update(mock_get_instance, current_workshop, expected_update, token, breadcrumb)

    @patch('stage0_fran.services.workshop_services.MongoIO.get_instance')
    def test_advance_workshop_not_active(self, mock_mongo):
        mock_mongo_instance = MagicMock()
        mock_mongo.return_value = mock_mongo_instance

        from stage0_py_utils import Config
        config = Config.get_instance()

        mock_mongo_instance.get_document.return_value = {
            "_id": "ws1",
            "current_exercise": 0,
            "status": "inactive",
            "exercises": [{"status": config.PENDING_STATUS}]
        }

        token = {"user_id": "test_user"}
        breadcrumb = {"timestamp": "now"}

        with self.assertRaises(Exception) as context:
            WorkshopServices.advance_workshop("ws1", token, breadcrumb)

        self.assertEqual(str(context.exception), "Workshop status inactive is not Active")
      
    @patch('stage0_fran.services.workshop_services.MongoIO.get_instance')
    @patch('stage0_fran.services.workshop_services.Config.get_instance')
    def test_add_observation(self, mock_config, mock_mongo):
        mock_mongo_instance = MagicMock()
        mock_mongo.return_value = mock_mongo_instance
        mock_config.return_value = MagicMock()

        token = {"user_id": "test_user"}
        breadcrumb = {"timestamp": "now"}
        observation = {"text": "New observation"}

        WorkshopServices.add_observation("ws1", token, breadcrumb, observation)

if __name__ == '__main__':
    unittest.main()
