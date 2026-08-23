# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Nyarch Linux

import base64
import json
import time
from typing import Optional

import requests

from .types import NSFWOption
from .api_base import BaseDownloaderAPI

_FORBIDDEN_TAG_1 = base64.b64decode("c2hvdGE=").decode("utf-8")
_FORBIDDEN_TAG_2 = base64.b64decode("bG9saQ==").decode("utf-8")
_FORBIDDEN_TAGS = {_FORBIDDEN_TAG_1, _FORBIDDEN_TAG_2}
_REQUEST_HEADERS = {
    "User-Agent": "CatgirlDownloaderQT/0.1 (+https://github.com/FrancescoCaracciolo/CatgirlDownloaderQT)"
}


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

    def set_tags(self, tags: str) -> bool:
        tag_list = tags.lower().split()
        filtered_tags = [tag for tag in tag_list if tag not in _FORBIDDEN_TAGS]
        removed_forbidden_tags = len(filtered_tags) != len(tag_list)
        self.tags = " ".join(filtered_tags)
        if self._settings:
            self._settings.set_preference("danbooru_tags", self.tags)
        return removed_forbidden_tags

    def get_tags(self) -> str:
        return self.tags

    def get_request_headers(self) -> dict[str, str]:
        return dict(_REQUEST_HEADERS)

    def _build_tags_query(self, nsfw_mode: NSFWOption) -> str:
        tags = self.tags.strip() if self.tags else ""

        if nsfw_mode == NSFWOption.BLOCK_NSFW or nsfw_mode == NSFWOption.BLOCK_NSFW.value:
            rating_tag = "rating:general"
        elif nsfw_mode == NSFWOption.ONLY_NSFW or nsfw_mode == NSFWOption.ONLY_NSFW.value:
            rating_tag = "rating:explicit"
        else:
            rating_tag = None

        if tags and rating_tag:
            return f"{tags} {rating_tag}"
        elif rating_tag:
            return rating_tag
        return tags

    def get_random_post(
        self,
        nsfw_mode: NSFWOption = NSFWOption.BLOCK_NSFW,
        max_retries: int = 5,
    ) -> Optional[dict]:
        for attempt in range(max_retries):
            try:
                tags = self._build_tags_query(nsfw_mode)
                params = {"limit": 1, "random": "true"}
                if tags:
                    params["tags"] = tags

                r = requests.get(
                    f"{self.endpoint}/posts.json",
                    params=params,
                    headers=_REQUEST_HEADERS,
                    timeout=10,
                )
                if r.status_code != 200:
                    return None
            except Exception as e:
                print(e)
                return None

            try:
                data = json.loads(r.text)
                if isinstance(data, list) and len(data) > 0:
                    post = data[0]
                    post_tags = post.get("tag_string", "").split()
                    if any(tag in _FORBIDDEN_TAGS for tag in post_tags):
                        print(
                            f"Attempt {attempt + 1}: Forbidden tags in post, retrying..."
                        )
                        continue

                    self.info = post
                    return post
                return None
            except Exception:
                return None
        print(f"Could not find suitable post after {max_retries} attempts")
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

    def set_setting(self, key: str, value) -> bool:
        if key == "danbooru_tags":
            return self.set_tags(str(value))
        return False
