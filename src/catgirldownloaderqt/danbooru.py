# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Nyarch Linux

import json
import time
from typing import Optional

import requests

from .types import NSFWOption
from .api_base import BaseDownloaderAPI


class DanbooruDownloaderAPI(BaseDownloaderAPI):
    def __init__(self, settings=None) -> None:
        super().__init__()
        self.endpoint = "https://danbooru.donmai.us"
        self._settings = settings
        self._load_tags()

    def _load_tags(self) -> None:
        if self._settings:
            self.tags = self._settings.get_preference("danbooru_tags") or ""
        else:
            self.tags = ""

    def set_tags(self, tags: str) -> None:
        self.tags = tags
        if self._settings:
            self._settings.set_preference("danbooru_tags", self.tags)

    def get_tags(self) -> str:
        return self.tags

    def _build_tags_query(self, nsfw_mode: NSFWOption) -> str:
        tags = self.tags.strip() if self.tags else ""

        if nsfw_mode == NSFWOption.BLOCK_NSFW:
            rating_tag = "rating:safe"
        elif nsfw_mode == NSFWOption.ONLY_NSFW:
            rating_tag = "rating:explicit"
        else:
            rating_tag = None

        if tags and rating_tag:
            return f"{tags} {rating_tag}"
        elif rating_tag:
            return rating_tag
        return tags

    def get_random_post(
        self, nsfw_mode: NSFWOption = NSFWOption.BLOCK_NSFW
    ) -> Optional[dict]:
        try:
            tags = self._build_tags_query(nsfw_mode)
            params = {"limit": 1, "random": "true"}
            if tags:
                params["tags"] = tags

            r = requests.get(
                f"{self.endpoint}/posts.json", params=params, timeout=10
            )
            if r.status_code != 200:
                return None
        except Exception as e:
            print(e)
            return None

        try:
            data = json.loads(r.text)
            if isinstance(data, list) and len(data) > 0:
                self.info = data[0]
                return data[0]
            return None
        except Exception:
            return None

    def get_image_url(
        self, nsfw_mode: NSFWOption = NSFWOption.BLOCK_NSFW
    ) -> Optional[str]:
        post = self.get_random_post(nsfw_mode)
        if post:
            return post.get("file_url")
        return None

    def get_artist(self, info: Optional[dict] = None) -> Optional[str]:
        data = info if info else self.info
        if not data:
            return None
        try:
            artist_tags = data.get("tag_string_artist", "")
            if artist_tags:
                return artist_tags.split(" ")[0]
            return None
        except Exception:
            return None

    def get_link(self, info: Optional[dict] = None) -> Optional[str]:
        data = info if info else self.info
        if not data:
            return None
        try:
            post_id = data.get("id")
            if post_id:
                return f"{self.endpoint}/posts/{post_id}"
            return None
        except Exception:
            return None

    def get_filename_suggestion(
        self, extension: Optional[str], info: Optional[dict] = None
    ) -> str:
        data = info if info else self.info
        if not data:
            post_id = str(int(time.time()))
        else:
            try:
                post_id = str(data.get("id", int(time.time())))
            except Exception:
                post_id = str(int(time.time()))

        if extension:
            return f"danbooru_{post_id}.{extension}"
        return f"danbooru_{post_id}"

    def get_settings_fields(self) -> list[dict[str, str]]:
        return [
            {
                "key": "danbooru_tags",
                "type": "text",
                "label": "Search Tags",
                "placeholder": "e.g., cat_ears solo 1girl",
                "description": "Enter tags separated by spaces.",
            },
        ]

    def get_setting(self, key: str):
        if key == "danbooru_tags":
            return self.get_tags()
        return None

    def set_setting(self, key: str, value) -> None:
        if key == "danbooru_tags":
            self.set_tags(str(value))
