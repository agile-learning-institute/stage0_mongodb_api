"""This is a simple command line utility to *unlock* all lockable files."""
from typing import Type
from configurator.services.configuration_services import Configuration
from configurator.services.dictionary_services import Dictionary
from configurator.services.enumerator_service import Enumerators
from configurator.utils.configurator_exception import ConfiguratorEvent, ConfiguratorException
from configurator.utils.file_io import File, FileIO
from configurator.utils.config import Config

import logging
import sys
import signal
import os

fileIO = FileIO()
config = Config.get_instance()

def unlock_everything():
    """Unlock all lockable files."""
    event = ConfiguratorEvent(event_id="UNLOCK-01", event_type="UNLOCK_EVERYTHING", event_description="Unlocking all lockable files.")
    event.append_events(unlock_all_configurations())
    event.append_events(unlock_all_dictionaries())
    event.append_events(unlock_all_types())
    event.append_events(unlock_all_enumerators())
    return event

def unlock_all_configurations():
    """Unlock all lockable files in a folder."""
    events = []
    try:
        for file in FileIO.get_files(config.CONFIGURATION_FOLDER):
            sub_event = ConfiguratorEvent(event_id=f"UNLOCK-02", event_type="UNLOCK_EVERYTHING", event_description=f"Unlocking configuration {file.file_name}.")
            events.append(sub_event)
            configuration = Configuration(file_name=file.file_name)
            configuration._locked = False
            configuration.save()
            sub_event.record_success()
        return events
    except ConfiguratorException as e:
        sub_event.append_events(e.events)
        sub_event.record_failure(message=f"Error unlocking configuration {file.file_name}: {e}")
        return events
    except Exception as e:
        sub_event.record_failure(message=f"Error unlocking configuration {file.file_name}: {e}")
        return events
    
def unlock_all_dictionaries(): 
    events = []
    try:
        for file in FileIO.get_files(config.DICTIONARY_FOLDER):
            sub_event = ConfiguratorEvent(event_id=f"UNLOCK-03", event_type="UNLOCK_EVERYTHING", event_description=f"Unlocking dictionary {file.file_name}.")
            events.append(sub_event)
            dictionary = Dictionary(file_name=file.file_name)
            dictionary._locked = False
            dictionary.save()
            sub_event.record_success()
        return events
    except ConfiguratorException as e:
        sub_event.append_events(e.events)
        sub_event.record_failure(message=f"Error unlocking dictionary {file.file_name}: {e}")
        return events
    except Exception as e:
        sub_event.record_failure(message=f"Error unlocking dictionary {file.file_name}: {e}")
        return events

def unlock_all_types():
    """Unlock all lockable files in a folder."""
    events = []
    try:
        for file in FileIO.get_files(config.TYPE_FOLDER):
            sub_event = ConfiguratorEvent(event_id=f"UNLOCK-04", event_type="UNLOCK_EVERYTHING", event_description=f"Unlocking type {file.file_name}.")
            events.append(sub_event)
            type = Type(file_name=file.file_name)
            type._locked = False
            type.save()
            sub_event.record_success()
        return events
    except ConfiguratorException as e:
        sub_event.append_events(e.events)
        sub_event.record_failure(message=f"Error unlocking type {file.file_name}: {e}")
        return events
    except Exception as e:
        sub_event.record_failure(message=f"Error unlocking type {file.file_name}: {e}")
        return events

def unlock_all_enumerators():
    """Unlock all lockable files in a folder."""
    events = []
    try:
        for file in FileIO.get_files(config.ENUMERATOR_FOLDER):
            sub_event = ConfiguratorEvent(event_id=f"UNLOCK-05", event_type="UNLOCK_EVERYTHING", event_description=f"Unlocking enumerator {file.file_name}.")
            events.append(sub_event)
            enumerator = Enumerators(file_name=file.file_name)
            enumerator._locked = False
            enumerator.save()
            sub_event.record_success()
        return events
    except ConfiguratorException as e:
        sub_event.append_events(e.events)
        sub_event.record_failure(message=f"Error unlocking enumerator {file.file_name}: {e}")
        return events
    except Exception as e:
        sub_event.record_failure(message=f"Error unlocking enumerator {file.file_name}: {e}")
        return events

if __name__ == "__main__":
    logging.info(unlock_everything().to_json())
    