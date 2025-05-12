from datetime import datetime, timezone
from bson import ObjectId
from stage0_py_utils import Config, MongoIO
from stage0_fran.services.chain_services import ChainServices

import logging
logger = logging.getLogger(__name__)

class WorkshopServices:

    @staticmethod 
    def _check_user_access(token):
        """Role Based Access Control logic"""
        return # No RBAC implemented yet

    @staticmethod
    def get_workshops(query=None, token=None):
        """Get a list of workshops that have name that matches the provided query"""
        WorkshopServices._check_user_access(token)
        config = Config.get_instance()
        mongo = MongoIO.get_instance()
        match = {"name": {"$regex": query}} if query else None
        project = {"_id":1, "name": 1}
        workshops = mongo.get_documents(config.WORKSHOP_COLLECTION_NAME, match=match, project=project)
        return workshops

    @staticmethod
    def get_workshop(workshop_id=None, token=None):
        """Get the specified workshop"""
        WorkshopServices._check_user_access(token)
        config = Config.get_instance()
        mongo = MongoIO.get_instance()
        workshop = mongo.get_document(config.WORKSHOP_COLLECTION_NAME, workshop_id)
        return workshop


    @staticmethod
    def add_workshop(chain_id=None, data=None, token=None, breadcrumb=None):
        """Create a new workshop based on the provided chain of exercise and workshop data"""
        WorkshopServices._check_user_access(token)
        config = Config.get_instance()
        mongo = MongoIO.get_instance()
        
        def _create_exercise(exercise_id):
            """Create a single exercises based on the exercise ID"""
            new_exercise = {
                "status": config.PENDING_STATUS,
                "exercise_id": exercise_id,
                "observations": []
            }
            return new_exercise
            
        # Build the list of exercises
        exercises = []
        chain = ChainServices.get_chain(chain_id, token)
        for exercise_id in chain["exercises"]: 
            exercises.append(_create_exercise(exercise_id))

        # Build the new Workshop document        
        data["status"] = config.PENDING_STATUS
        data["current_exercise"] = 0
        data["exercises"] = exercises
        data["last_saved"] = breadcrumb

        workshop_id = mongo.create_document(config.WORKSHOP_COLLECTION_NAME, data)
        workshop = WorkshopServices.get_workshop(workshop_id, token) 
        return workshop
    
    @staticmethod
    def update_workshop(workshop_id=None, data=None, token=None, breadcrumb=None):
        """Update the specified workshop"""        
        WorkshopServices._check_user_access(token)
        config = Config.get_instance()
        mongo = MongoIO.get_instance()
        data["last_saved"] = breadcrumb
        
        workshop = mongo.update_document(config.WORKSHOP_COLLECTION_NAME, workshop_id, set_data=data)
        return workshop

    @staticmethod
    def start_workshop(workshop_id=None, token=None, breadcrumb=None):
        """Update the specified workshop Status to Active, record start time"""
        WorkshopServices._check_user_access(token)
        config = Config.get_instance()
        data = {
            "status": config.ACTIVE_STATUS,
            "when": {
                "from": datetime.now(timezone.utc)
            }
        }
        return WorkshopServices.update_workshop(workshop_id=workshop_id, data=data, token=token, breadcrumb=breadcrumb)

    @staticmethod
    def advance_workshop(workshop_id=None, token=None, breadcrumb=None):
        """Advance a workshop to the next current exercise"""
        WorkshopServices._check_user_access(token)
        config = Config.get_instance()
        mongo = MongoIO.get_instance()
        workshop = mongo.get_document(config.WORKSHOP_COLLECTION_NAME, workshop_id)
        index = workshop["current_exercise"]
        next_index = index + 1
        set_data = {"last_saved": breadcrumb}
        
        if workshop["status"] != config.ACTIVE_STATUS:
            raise Exception(f"Workshop status {workshop['status']} is not Active")

        set_data[f"exercises.{index}.status"] = config.COMPLETED_STATUS

        if next_index >= len(workshop["exercises"]):
            set_data["status"] = config.COMPLETED_STATUS
            
        else:
            set_data["current_exercise"] = next_index
            set_data[f"exercises.{next_index}.status"] = config.PENDING_STATUS
        
        return mongo.update_document(config.WORKSHOP_COLLECTION_NAME, workshop_id, set_data=set_data)
    
    @staticmethod
    def add_observation(workshop_id=None, observation=None, token=None, breadcrumb=None):
        """Add an observation to the observations list"""
        WorkshopServices._check_user_access(token)
        config = Config.get_instance()
        mongo = MongoIO.get_instance()
        workshop = WorkshopServices.get_workshop(workshop_id, token)
        index = workshop["current_exercise"]
        set_data = {"last_saved": breadcrumb}
        push_data = {f"exercises.{index}.observations": observation}        
        workshop = mongo.update_document(config.WORKSHOP_COLLECTION_NAME, workshop_id, set_data=set_data, push_data=push_data)
        return workshop
