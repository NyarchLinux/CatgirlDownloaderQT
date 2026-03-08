# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Nyarch Linux

import os
import json

from PySide6.QtCore import QStandardPaths


class UserPreferences:
    def __init__(self):
        self._defaults = {
            "nsfw_mode": "Block NSFW",
            "auto_reload_enabled": False,
            "auto_reload_interval": 5,
            "danbooru_tags": "",
        }
        self.preferences = dict(self._defaults)

        config_base = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.ConfigLocation
        )
        self.directory = os.path.join(config_base, "catgirldownloaderqt")
        os.makedirs(self.directory, exist_ok=True)
        self.file = os.path.join(self.directory, "config.json")

        if not os.path.exists(self.file):
            with open(self.file, "w") as f:
                json.dump(self.preferences, f)

        try:
            with open(self.file, "r") as f:
                self.preferences = json.load(f)
            changed = False
            for k, v in self._defaults.items():
                if k not in self.preferences:
                    self.preferences[k] = v
                    changed = True
            if changed:
                self._write()
        except Exception as e:
            print(e)

    def reload_preferences(self):
        try:
            with open(self.file, "r") as f:
                self.preferences = json.load(f)
            for k, v in self._defaults.items():
                if k not in self.preferences:
                    self.preferences[k] = v
        except Exception as e:
            print(e)

    def get_preference(self, key):
        self.reload_preferences()
        return self.preferences.get(key)

    def set_preference(self, key, value):
        self.preferences[key] = value
        self._write()

    def set_preference_batch(self, prefs: dict):
        self.preferences = prefs
        self._write()

    def _write(self):
        try:
            with open(self.file, "w") as f:
                json.dump(self.preferences, f)
        except Exception as e:
            print(e)
