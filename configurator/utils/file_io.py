import json
import os
from datetime import datetime
from pathlib import Path

import yaml

from configurator.utils.config import Config
from configurator.utils.configurator_exception import ConfiguratorEvent, ConfiguratorException


class File:
    """Class representing a file with its properties."""
    
    def __init__(self, file_path: str):
        """Initialize a File instance with file properties.
        
        Args:
            file_path: Path to the file
        """
        self.name = os.path.basename(file_path)
        self.read_only = False
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
        self.size = 0
        
        # Get file properties if file exists
        try:
            stat = os.stat(file_path)
            self.size = stat.st_size
            self.created_at = datetime.fromtimestamp(stat.st_ctime).isoformat()
            self.updated_at = datetime.fromtimestamp(stat.st_mtime).isoformat()
            self.read_only = not os.access(file_path, os.W_OK)
        except Exception as e:
            event = ConfiguratorEvent(event_id="FIL-01", event_type="GET_FILE_PROPERTIES", event_data={"error": str(e)})
            raise ConfiguratorException(f"Failed to get file properties for {file_path}", event)

    def to_dict(self):
        """Convert file properties to dictionary matching OpenAPI schema (flat)."""
        return {
            "name": self.name,
            "read_only": self.read_only,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "size": self.size
        }


class FileIO:
    """Class for file I/O operations."""
    
    def __init__(self):
        pass
    
    def get_documents(self, folder_name: str) -> list[File]:
        """Get all files from a folder.
        
        Args:
            folder_name: Name of the folder to scan
            
        Returns:
            List of File objects
            
        Raises:
            ConfiguratorException: If folder access fails
        """
        config = Config.get_instance()
        folder = os.path.join(config.INPUT_FOLDER, folder_name)
        files = []
        
        try:
            if not os.path.exists(folder):
                return files
                
            for file_name in os.listdir(folder):
                file_path = os.path.join(folder, file_name)
                if os.path.isfile(file_path):
                    files.append(File(file_path))
            return files
        except Exception as e:
            event = ConfiguratorEvent(event_id="FIL-01", event_type="GET_DOCUMENTS", event_data={"error": str(e)})
            raise ConfiguratorException(f"Failed to get documents from {folder}", event)
    
    def get_document(self, folder_name: str, file_name: str) -> dict:
        """Read document content from a file.
        
        Args:
            folder_name: Name of the folder to read from
            file_name: Name of the file to read
            
        Returns:
            Document content as dict
            
        Raises:
            ConfiguratorException: If file read fails or unsupported file type
        """
        config = Config.get_instance()
        folder = os.path.join(config.INPUT_FOLDER, folder_name)
        file_path = os.path.join(folder, file_name)
        
        # Check if file exists
        if not os.path.exists(file_path):
            event = ConfiguratorEvent(event_id="FIL-02", event_type="FILE_NOT_FOUND", 
                event_data={"file_path": file_path})
            raise ConfiguratorException(f"File not found: {file_path}", event)
        
        # Get extension from file path
        extension = os.path.splitext(file_path)[1].lower()
        
        # Only allow .yaml and .json
        if extension not in [".yaml", ".json"]:
            event = ConfiguratorEvent(event_id="FIL-03", event_type="UNSUPPORTED_FILE_TYPE", 
                event_data={"file_name": file_name, "extension": extension})
            raise ConfiguratorException(f"Unsupported file type: {extension}", event)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if extension == ".yaml":
                    return yaml.safe_load(f)
                elif extension == ".json":
                    return json.load(f)
        except Exception as e:
            event = ConfiguratorEvent(event_id="FIL-04", event_type="GET_DOCUMENT", event_data={"error": str(e)})
            raise ConfiguratorException(f"Failed to get document from {file_path}", event)
    
    def put_document(self, folder_name: str, file_name: str, document: dict) -> File:
        """Write document content to a file.
        
        Args:
            folder_name: Name of the folder to write to
            file_name: Name of the file to write
            document: Document content to write
            
        Returns:
            File object representing the written file
            
        Raises:
            ConfiguratorException: If file write fails or unsupported file type
        """
        config = Config.get_instance()
        folder = os.path.join(config.INPUT_FOLDER, folder_name)
        file_path = os.path.join(folder, file_name)
        
        # Get extension from file path
        extension = os.path.splitext(file_path)[1].lower()
        
        # Only allow .yaml and .json
        if extension not in [".yaml", ".json"]:
            event = ConfiguratorEvent(event_id="FIL-05", event_type="UNSUPPORTED_FILE_TYPE", event_data=file_name)
            raise ConfiguratorException(f"Unsupported file type: {extension}", event)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                if extension == ".yaml":
                    yaml.dump(document, f, default_flow_style=False, allow_unicode=True)
                elif extension == ".json":
                    json.dump(document, f, indent=2, ensure_ascii=False)
            
            # Return updated file object with current properties
            return File(file_path)
        except Exception as e:
            event = ConfiguratorEvent(event_id="FIL-06", event_type="PUT_DOCUMENT", event_data={"error": str(e)})
            raise ConfiguratorException(f"Failed to put document to {file_path}", event)
    
    def delete_document(self, folder_name: str, file_name: str) -> ConfiguratorEvent:
        """Delete a file.
        
        Args:
            folder_name: Name of the folder containing the file
            file_name: Name of the file to delete
            
        Returns:
            ConfiguratorEvent with operation result
        """
        config = Config.get_instance()
        folder = os.path.join(config.INPUT_FOLDER, folder_name)
        file_path = os.path.join(folder, file_name)
        event = ConfiguratorEvent(event_id="FIL-07", event_type="DELETE_DOCUMENT")
        
        try:
            if not os.path.exists(file_path):
                event.record_failure({"error": "File not found", "file_path": file_path})
                return event
                
            os.remove(file_path)
            event.record_success()
            return event
        except Exception as e:
            event.record_failure({"error": str(e), "file_path": file_path})
            return event
    
    def lock_unlock(self, folder_name: str, file_name: str) -> File:
        """Toggle file read-only status.
        
        Args:
            folder_name: Name of the folder containing the file
            file_name: Name of the file to lock/unlock
            
        Returns:
            Updated File object
            
        Raises:
            ConfiguratorException: If file does not exist or error occurs
        """
        config = Config.get_instance()
        folder = os.path.join(config.INPUT_FOLDER, folder_name)
        file_path = os.path.join(folder, file_name)
        
        if not os.path.exists(file_path):
            event = ConfiguratorEvent(event_id="FIL-08", event_type="LOCK_UNLOCK", event_data={"error": "File not found", "file_path": file_path})
            raise ConfiguratorException(f"File not found: {file_path}", event)
        
        try:
            file_stats = File(file_path)
            if file_stats.read_only:
                os.chmod(file_path, 0o666)  # Make writable
            else:
                os.chmod(file_path, 0o444)  # Make read-only
            return File(file_path)
        except Exception as e:
            event = ConfiguratorEvent(event_id="FIL-08", event_type="LOCK_UNLOCK", event_data={"error": str(e), "file_path": file_path})
            raise ConfiguratorException(f"Failed to lock/unlock file: {file_path}", event)
    