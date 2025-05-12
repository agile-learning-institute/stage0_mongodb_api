from stage0_py_utils import Config, MongoIO

import logging
logger = logging.getLogger(__name__)

class ExerciseServices:

    @staticmethod 
    def _check_user_access(token):
        """Role Based Access Control logic"""
        return # No RBAC yet

    @staticmethod
    def get_exercises(token=None):
        """Get a list of all exercises"""
        ExerciseServices._check_user_access(token)
        config = Config.get_instance()
        mongo = MongoIO.get_instance()
        match = { "status": config.ACTIVE_STATUS}
        project = {"_id":1, "name":1}
        exercises = mongo.get_documents(config.EXERCISE_COLLECTION_NAME, match=match, project=project)
        return exercises

    @staticmethod
    def get_exercise(exercise_id=None, token=None):
        """Get the specified exercise"""
        ExerciseServices._check_user_access(token)
        config = Config.get_instance()
        mongo = MongoIO.get_instance()
        exercise = mongo.get_document(config.EXERCISE_COLLECTION_NAME, exercise_id)
        return exercise
