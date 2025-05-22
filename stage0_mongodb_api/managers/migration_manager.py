from typing import Dict, List
from stage0_py_utils import MongoIO

class MigrationManager:
    """Manages data migrations for collections using MongoDB aggregation pipelines."""
    
    @staticmethod
    def run_migration(collection_name: str, migration: List[Dict]) -> Dict:
        """Run a migration pipeline on a collection.
        
        Args:
            collection_name: Name of the collection
            migration: List of MongoDB aggregation pipeline stages.
                See MongoDB's [Aggregation Pipeline](https://www.mongodb.com/docs/manual/core/aggregation-pipeline/)
                for details on supported stages.
                Must not be empty.
        
        Returns:
            Dict containing operation result:
            {
                "status": "success",
                "operation": "migration",
                "collection": str,
                "stages": int  # Number of pipeline stages executed
            }
            
        Raises:
            ValueError: If migration is empty
        """
        if not migration:
            raise ValueError("Migration pipeline cannot be empty")
            
        mongo = MongoIO.get_instance()
        
        # Execute each pipeline stage in sequence
        for stage in migration:
            mongo.execute_pipeline(collection_name, stage)
        
        return {
            "status": "success",
            "operation": "migration",
            "collection": collection_name,
            "stages": len(migration)
        } 