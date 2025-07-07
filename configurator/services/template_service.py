"""
Template Service for processing configuration and dictionary templates.
"""
from configurator.utils.config import Config
from configurator.utils.file_io import FileIO
from configurator.utils.configurator_exception import ConfiguratorEvent, ConfiguratorException
import yaml


class TemplateService:
    """Service for processing templates and creating new collections."""
    
    def __init__(self):
        self.config = Config.get_instance()
    
    def create_collection(self, collection_name: str) -> dict:
        """
        Create a new collection with configuration and dictionary files.
        
        Args:
            collection_name: Name of the collection to create
            
        Returns:
            dict: Information about created files
        """
        # Validate collection name
        self._validate_collection_name(collection_name)
        
        # Check if files already exist
        self._check_existing_files(collection_name)
        
        # Process and save configuration template
        config_content = self.process_configuration_template(collection_name)
        config_filename = f"{collection_name}.yaml"
        FileIO.put_document(self.config.CONFIGURATION_FOLDER, config_filename, config_content)
        
        # Process and save dictionary template
        dict_content = self.process_dictionary_template(collection_name)
        dict_filename = f"{collection_name}.0.0.1.yaml"
        FileIO.put_document(self.config.DICTIONARY_FOLDER, dict_filename, dict_content)
        
        return {
            "collection_name": collection_name,
            "configuration_file": config_filename,
            "dictionary_file": dict_filename
        }
    
    def process_configuration_template(self, collection_name: str) -> dict:
        """
        Process the configuration template with the collection name.
        
        Args:
            collection_name: Name to replace in template
            
        Returns:
            dict: Processed configuration content
        """
        template_content = self._load_template("configuration.yaml")
        processed_content = self._replace_placeholders(template_content, collection_name)
        return yaml.safe_load(processed_content)
    
    def process_dictionary_template(self, collection_name: str) -> dict:
        """
        Process the dictionary template with the collection name.
        
        Args:
            collection_name: Name to replace in template
            
        Returns:
            dict: Processed dictionary content
        """
        template_content = self._load_template("dictionary.yaml")
        processed_content = self._replace_placeholders(template_content, collection_name)
        return yaml.safe_load(processed_content)
    
    def _load_template(self, template_name: str) -> str:
        """
        Load a template file from the template folder.
        
        Args:
            template_name: Name of the template file
            
        Returns:
            str: Template content
        """
        try:
            return FileIO.get_document(self.config.TEMPLATE_FOLDER, template_name)
        except Exception as e:
            event = ConfiguratorEvent("TPL-01", "TEMPLATE_NOT_FOUND", {"template": template_name})
            raise ConfiguratorException(f"Template {template_name} not found", event)
    
    def _replace_placeholders(self, content: str, collection_name: str) -> str:
        """
        Replace placeholders in template content.
        
        Args:
            content: Template content
            collection_name: Name to replace placeholders with
            
        Returns:
            str: Content with replaced placeholders
        """
        return content.replace("{{collection_name}}", collection_name)
    
    def _validate_collection_name(self, collection_name: str):
        """
        Validate the collection name format.
        
        Args:
            collection_name: Name to validate
        """
        if not collection_name or not collection_name.strip():
            event = ConfiguratorEvent("TPL-02", "INVALID_COLLECTION_NAME", {"name": collection_name})
            raise ConfiguratorException("Collection name cannot be empty", event)
        
        # Check for valid characters (alphanumeric, underscore, hyphen)
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', collection_name):
            event = ConfiguratorEvent("TPL-02", "INVALID_COLLECTION_NAME", {"name": collection_name})
            raise ConfiguratorException("Collection name can only contain letters, numbers, underscores, and hyphens", event)
    
    def _check_existing_files(self, collection_name: str):
        """
        Check if configuration or dictionary files already exist.
        
        Args:
            collection_name: Name to check
        """
        config_filename = f"{collection_name}.yaml"
        dict_filename = f"{collection_name}.0.0.1.yaml"
        
        try:
            FileIO.get_document(self.config.CONFIGURATION_FOLDER, config_filename)
            event = ConfiguratorEvent("TPL-03", "CONFIGURATION_EXISTS", {"file": config_filename})
            raise ConfiguratorException(f"Configuration file {config_filename} already exists", event)
        except ConfiguratorException as e:
            # If it's a file not found exception, that's what we want
            if e.event.id == "FIL-02":
                pass  # File doesn't exist, which is what we want
            else:
                # Re-raise other ConfiguratorExceptions
                raise
        
        try:
            FileIO.get_document(self.config.DICTIONARY_FOLDER, dict_filename)
            event = ConfiguratorEvent("TPL-03", "DICTIONARY_EXISTS", {"file": dict_filename})
            raise ConfiguratorException(f"Dictionary file {dict_filename} already exists", event)
        except ConfiguratorException as e:
            # If it's a file not found exception, that's what we want
            if e.event.id == "FIL-02":
                pass  # File doesn't exist, which is what we want
            else:
                # Re-raise other ConfiguratorExceptions
                raise 