from typing import Dict, List
from stage0_py_utils import MongoIO

class MigrationManager:
    """Manages data migrations for collections using MongoDB aggregation pipelines."""
    
    @staticmethod
    def run_migration(collection_name: str, migration: Dict) -> Dict:
        """Run a single migration pipeline on a collection.
        
        Args:
            collection_name: Name of the collection
            migration: Migration configuration containing:
                - name: str (optional) - Name of the pipeline for logging
                - pipeline: List[Dict] - MongoDB aggregation pipeline stages
                See MongoDB's [Aggregation Pipeline](https://www.mongodb.com/docs/manual/core/aggregation-pipeline/)
                for details on supported stages.
        
        Returns:
            Dict containing operation result:
            {
                "status": "success",
                "operation": "migration",
                "collection": str,
                "pipeline": Dict  # Pipeline result with name and stages
            }
            
        Raises:
            ValueError: If migration is invalid or pipeline is empty
        """
        if not migration or "pipeline" not in migration:
            raise ValueError("Migration must contain a 'pipeline' field")
        
        pipeline_name = migration.get("name", "unnamed_pipeline")
        pipeline_stages = migration["pipeline"]
        
        if not pipeline_stages:
            raise ValueError(f"Pipeline '{pipeline_name}' cannot be empty")
        
        mongo = MongoIO.get_instance()
        
        try:
            # Execute the entire pipeline at once
            mongo.execute_pipeline(collection_name, pipeline_stages)
            return {
                "operation": "migration",
                "collection": collection_name,
                "pipeline": {
                    "name": pipeline_name,
                    "stages": len(pipeline_stages)
                },
                "status": "success"
            }
        except Exception as e:
            return {
                "operation": "migration",
                "collection": collection_name,
                "pipeline": {
                    "name": pipeline_name,
                    "stages": len(pipeline_stages)
                },
                "error": str(e),
                "status": "error"
            } 