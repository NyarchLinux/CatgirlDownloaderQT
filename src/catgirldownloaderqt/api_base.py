# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Nyarch Linux

from abc import ABC, abstractmethod
from typing import Any, Optional

import requests

from .types import NSFWOption


class BaseDownloaderAPI(ABC):
    def __init__(self) -> None:
        self.endpoint: str = ""
        self.info: Optional[dict[str, Any]] = None

    @abstractmethod
    def get_image_url(
        self, nsfw_mode: NSFWOption = NSFWOption.BLOCK_NSFW
    ) -> Optional[str]:
        pass

    @abstractmethod
    def get_artist(self, info: Optional[dict] = None) -> Optional[str]:
        pass

    @abstractmethod
    def get_link(self, info: Optional[dict] = None) -> Optional[str]:
        pass

    def get_image(self, url: str) -> Optional[bytes]:
        try:
            r = requests.get(url, timeout=20)
            if r.status_code == 200:
                return r.content
            return None
        except Exception as e:
            print(f"Error downloading image: {e}")
            return None

    @abstractmethod
    def get_filename_suggestion(
        self, extension: Optional[str], info: Optional[dict] = None
    ) -> str:
        pass

    def get_settings_fields(self) -> list[dict[str, str]]:
        """Return a list of field descriptors for this source's custom settings.

        Each field is a dict with keys:
          - key: preference storage key
          - type: "text", "number", or "bool"
          - label: human-readable label
          - placeholder: (optional) placeholder text for text fields
          - description: (optional) help text shown below the control

        Sources with no custom settings return an empty list.
        """
        return []

    def get_setting(self, key: str) -> Any:
        """Get the current value of a source-specific setting by key."""
        return None

    def set_setting(self, key: str, value: Any) -> None:
        """Set a source-specific setting by key."""
        pass
