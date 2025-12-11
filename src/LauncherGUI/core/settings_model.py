import json
import os
from PySide6.QtCore import QObject, Signal

class SettingsModel(QObject):
    """
    Manages loading and saving application settings from a JSON file.
    Emits signals when settings are changed and saved.
    """
    settings_changed = Signal()

    def __init__(self, file_path="settings.json"):
        super().__init__()
        self.file_path = file_path
        
        # Default settings
        self.defaults = {
            "theme": "dark",
            "font_family": "Segoe UI",
            "font_size": 10
        }
        
        # Load settings or create the file with defaults
        self.settings = self.load()

    def load(self):
        """Loads settings from the JSON file. If the file doesn't exist, creates it."""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r') as f:
                    settings = json.load(f)
                    # Ensure all keys are present
                    for key, value in self.defaults.items():
                        settings.setdefault(key, value)
                    return settings
            except (json.JSONDecodeError, IOError):
                # If file is corrupted or unreadable, return defaults
                return self.defaults.copy()
        else:
            # File doesn't exist, create it with defaults
            self.save(self.defaults)
            return self.defaults.copy()

    def save(self, settings_dict=None):
        """Saves the provided dictionary to the JSON file."""
        if settings_dict is None:
            settings_dict = self.settings
        
        try:
            with open(self.file_path, 'w') as f:
                json.dump(settings_dict, f, indent=4)
        except IOError as e:
            print(f"Error saving settings: {e}")

    def get(self, key):
        """Gets a setting value by key."""
        return self.settings.get(key, self.defaults.get(key))

    def set_and_save(self, new_settings):
        """Updates the settings dictionary and saves everything to the file."""
        self.settings.update(new_settings)
        self.save()
        # Notify the application that settings have changed
        self.settings_changed.emit()
