import unittest
from unittest.mock import patch, MagicMock
from stage0_fran.services.exercise_services import ExerciseServices

class TestExerciseServices(unittest.TestCase):

    @patch('stage0_fran.services.exercise_services.MongoIO.get_instance')
    @patch('stage0_fran.services.exercise_services.Config.get_instance')
    def test_get_exercises(self, mock_config, mock_mongo):
        mock_mongo_instance = MagicMock()
        mock_mongo.return_value = mock_mongo_instance
        mock_config.return_value = MagicMock()
        mock_mongo_instance.get_documents.return_value = [{"_id": "exercise1", "name": "Test Exercise"}]

        token = {"user_id": "test_user"}
        result = ExerciseServices.get_exercises(token)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "Test Exercise")
        mock_mongo_instance.get_documents.assert_called_once()

    @patch('stage0_fran.services.exercise_services.MongoIO.get_instance')
    @patch('stage0_fran.services.exercise_services.Config.get_instance')
    def test_get_exercise(self, mock_config, mock_mongo):
        mock_mongo_instance = MagicMock()
        mock_mongo.return_value = mock_mongo_instance
        mock_config.return_value = MagicMock()
        mock_mongo_instance.get_document.return_value = {"_id": "exercise1", "name": "Test Exercise"}

        token = {"user_id": "test_user"}
        result = ExerciseServices.get_exercise("exercise1", token)

        self.assertEqual(result["_id"], "exercise1")
        self.assertEqual(result["name"], "Test Exercise")
        mock_mongo_instance.get_document.assert_called_once()

if __name__ == '__main__':
    unittest.main()
