# core/settings_manager.py
import os
import json
from datetime import datetime

class SettingsManager:
    def __init__(self, settings_path="settings.json"):
        self.settings_path = settings_path
        self.default_settings = {
            'min_minutes': 30,
            'max_minutes': 60,
            'snooze_minutes': 10,
            'daily_goal': 15,
            'sound_enabled': True,
            'sound_choice': "assets/sounds/normal.wav",
            'log_count': 0,
            'last_log_date': datetime.now().isoformat(),
            'history': {},
            'theme': "Ocean",
            'show_progress_text': True,
            # New settings:
            'start_at_login': True,
            'notification_style': "Standard",  # Options: "Legacy", "Standard", "Over the Top"
            'achievements': [],
            'user_profile': {
                'name': '',
                'photo_path': '',
                'joined_date': datetime.now().isoformat()
            },
            'has_early_drink': False,
            'has_late_drink': False,
            'consistent_intervals': 0,
        }
        self.settings = self.load_settings()

    def load_settings(self):
        if os.path.exists(self.settings_path):
            try:
                with open(self.settings_path, "r") as f:
                    settings = json.load(f)
                # Ensure all keys are present
                for key, value in self.default_settings.items():
                    if key not in settings:
                        settings[key] = value
                return settings
            except (json.JSONDecodeError, Exception) as e:
                print("Error loading settings, using defaults:", e)
                return self.default_settings.copy()
        else:
            return self.default_settings.copy()

    def save_settings(self):
        try:
            with open(self.settings_path, "w") as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print("Error saving settings:", e)

    def get(self, key):
        return self.settings.get(key, self.default_settings.get(key))

    def set(self, key, value):
        self.settings[key] = value

    def update_last_log_date(self):
        self.settings["last_log_date"] = datetime.now().isoformat()
