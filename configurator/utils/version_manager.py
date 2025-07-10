import re
import logging
from typing import Optional, Dict, List

from configurator.utils.config import Config
from configurator.utils.configurator_exception import ConfiguratorEvent, ConfiguratorException
from configurator.utils.mongo_io import MongoIO
from configurator.utils.version_number import VersionNumber

logger = logging.getLogger(__name__)

class VersionManager:
    """Static class for managing collection version tracking in MongoDB.
    
    This class focuses on:
    1. Reading current versions from the database
    2. Updating version records
    3. Version comparison and validation
    """
    
    @staticmethod
    def get_current_version(mongo_io: MongoIO, collection_name: str) -> VersionNumber:
        """Get the current version of a collection."""
        config = Config.get_instance()
        version_docs = mongo_io.get_documents(
            config.VERSION_COLLECTION_NAME,
            match={"collection_name": collection_name}
        )
        if not version_docs or len(version_docs) == 0:
            return VersionNumber(f"{collection_name}.0.0.0.0")
        if len(version_docs) > 1:
            event = ConfiguratorEvent(event_id="VER-01", event_type="GET_CURRENT_VERSION", event_data=version_docs)
            raise ConfiguratorException(f"Multiple versions found for collection: {collection_name}", event)
        current_version = version_docs[0].get('current_version')
        return VersionNumber(current_version)

    @staticmethod
    def update_version(mongo_io: MongoIO, collection_name: str, version: str) -> str:
        """Update the version of a collection."""
        config = Config.get_instance()
        # version is now always expected to include the collection name
        version_obj = VersionNumber(version)
        version_doc = mongo_io.upsert(
            config.VERSION_COLLECTION_NAME,
            match={"collection_name": collection_name},
            data={"collection_name": collection_name, "current_version": version}
        )
        return VersionManager.get_current_version(mongo_io, collection_name)
