from stage0_py_utils import Config, MongoIO

import logging
logger = logging.getLogger(__name__)

class ChainServices:

    @staticmethod 
    def _check_user_access(token):
        """Role Based Access Control logic"""        
        return # No access control implemented yet

    @staticmethod
    def get_chains(token=None):
        """Get a list of chain names and ids"""
        ChainServices._check_user_access(token)
        config = Config.get_instance()
        mongo = MongoIO.get_instance()
        match = {}
        project = {"_id":1, "name":1}
        chains = mongo.get_documents(config.CHAIN_COLLECTION_NAME, match, project)
        return chains

    @staticmethod
    def get_chain(chain_id=None, token=None):
        """Get the specified chain"""
        ChainServices._check_user_access(token)
        config = Config.get_instance()
        mongo = MongoIO.get_instance()
        chain = mongo.get_document(config.CHAIN_COLLECTION_NAME, chain_id)
        return chain
