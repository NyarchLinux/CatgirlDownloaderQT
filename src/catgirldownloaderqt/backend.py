# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Nyarch Linux

import threading
import uuid
from typing import Optional

import requests
from PySide6.QtCore import (
    QObject, Signal, Slot, Property, QTimer, QUrl, QMetaObject, Qt,
)

from .preferences import UserPreferences
from .types import NSFWOption
from .catgirl import CatgirlDownloaderAPI
from .waifu import WaifuDownloaderAPI
from .danbooru import DanbooruDownloaderAPI


SOURCES = [
    {"key": "catgirl", "name": "Catgirl", "description": "Images from nekos.moe"},
    {"key": "waifu", "name": "Waifu", "description": "Images from waifu.im"},
    {"key": "danbooru", "name": "Danbooru", "description": "Images from danbooru.donmai.us"},
]

NSFW_OPTIONS = [opt.value for opt in NSFWOption]


class Backend(QObject):
    imageChanged = Signal()
    loadingChanged = Signal()
    currentSourceChanged = Signal()
    autoReloadEnabledChanged = Signal()
    autoReloadIntervalChanged = Signal()
    nsfwModeIndexChanged = Signal()
    hasImageChanged = Signal()
    artistNameChanged = Signal()
    artistLinkChanged = Signal()
    danbooruTagsChanged = Signal()
    errorOccurred = Signal(str)
    imageSaved = Signal(str)

    def __init__(self, image_provider, parent=None):
        super().__init__(parent)
        self._image_provider = image_provider
        self._settings = UserPreferences()

        self._downloaders = {
            "catgirl": CatgirlDownloaderAPI(settings=self._settings),
            "waifu": WaifuDownloaderAPI(settings=self._settings),
            "danbooru": DanbooruDownloaderAPI(settings=self._settings),
        }

        self._loading = False
        self._image_id = ""
        self._has_image = False
        self._info: Optional[dict] = None
        self._current_source_index = 0
        self._image_extension = ""

        # Pending data from worker thread (written by thread, read by main thread slot)
        self._pending_data: Optional[bytes] = None
        self._pending_info: Optional[dict] = None
        self._pending_error: Optional[str] = None

        saved_source = self._settings.get_preference("source") or "catgirl"
        for i, src in enumerate(SOURCES):
            if src["key"] == saved_source:
                self._current_source_index = i
                break

        saved_nsfw = self._settings.get_preference("nsfw_mode") or "Block NSFW"
        self._nsfw_mode_index = 0
        try:
            self._nsfw_mode_index = NSFW_OPTIONS.index(saved_nsfw)
        except ValueError:
            pass

        self._auto_reload_enabled = bool(
            self._settings.get_preference("auto_reload_enabled")
        )
        interval = self._settings.get_preference("auto_reload_interval")
        try:
            self._auto_reload_interval = max(1, int(interval)) if interval is not None else 5
        except (ValueError, TypeError):
            self._auto_reload_interval = 5

        self._auto_timer = QTimer(self)
        self._auto_timer.setSingleShot(True)
        self._auto_timer.timeout.connect(self._on_auto_timer)

    # -- Properties --

    def _get_loading(self):
        return self._loading

    def _set_loading(self, val):
        if self._loading != val:
            self._loading = val
            self.loadingChanged.emit()

    loading = Property(bool, _get_loading, notify=loadingChanged)

    def _get_image_id(self):
        return self._image_id

    imageId = Property(str, _get_image_id, notify=imageChanged)

    def _get_has_image(self):
        return self._has_image

    hasImage = Property(bool, _get_has_image, notify=hasImageChanged)

    def _get_current_source(self):
        return self._current_source_index

    currentSource = Property(int, _get_current_source, notify=currentSourceChanged)

    def _get_auto_reload_enabled(self):
        return self._auto_reload_enabled

    autoReloadEnabled = Property(
        bool, _get_auto_reload_enabled, notify=autoReloadEnabledChanged
    )

    def _get_auto_reload_interval(self):
        return self._auto_reload_interval

    autoReloadInterval = Property(
        int, _get_auto_reload_interval, notify=autoReloadIntervalChanged
    )

    def _get_nsfw_mode_index(self):
        return self._nsfw_mode_index

    nsfwModeIndex = Property(int, _get_nsfw_mode_index, notify=nsfwModeIndexChanged)

    def _get_artist_name(self):
        key = SOURCES[self._current_source_index]["key"]
        dl = self._downloaders[key]
        return dl.get_artist(self._info) or ""

    artistName = Property(str, _get_artist_name, notify=artistNameChanged)

    def _get_artist_link(self):
        key = SOURCES[self._current_source_index]["key"]
        dl = self._downloaders[key]
        return dl.get_link(self._info) or ""

    artistLink = Property(str, _get_artist_link, notify=artistLinkChanged)

    def _get_danbooru_tags(self):
        dl = self._downloaders["danbooru"]
        return dl.get_tags()

    danbooruTags = Property(str, _get_danbooru_tags, notify=danbooruTagsChanged)

    @Slot(result="QVariantList")
    def sourceNames(self):
        return [s["name"] for s in SOURCES]

    @Slot(result="QVariantList")
    def sourceDescriptions(self):
        return [s["description"] for s in SOURCES]

    @Slot(result="QVariantList")
    def nsfwOptions(self):
        return list(NSFW_OPTIONS)

    @Slot(int, result=bool)
    def sourceHasSettings(self, index):
        if index < 0 or index >= len(SOURCES):
            return False
        key = SOURCES[index]["key"]
        dl = self._downloaders[key]
        return len(dl.get_settings_fields()) > 0

    @Slot(int, result="QVariantList")
    def sourceSettingsFields(self, index):
        if index < 0 or index >= len(SOURCES):
            return []
        key = SOURCES[index]["key"]
        dl = self._downloaders[key]
        return dl.get_settings_fields()

    @Slot(int, result=str)
    def sourceSettingsTitle(self, index):
        if index < 0 or index >= len(SOURCES):
            return ""
        return SOURCES[index]["name"] + " Settings"

    @Slot(int, str, result=str)
    def getSourceSetting(self, index, key):
        if index < 0 or index >= len(SOURCES):
            return ""
        source_key = SOURCES[index]["key"]
        dl = self._downloaders[source_key]
        val = dl.get_setting(key)
        return str(val) if val is not None else ""

    @Slot(int, str, str, result=bool)
    def setSourceSetting(self, index, key, value):
        if index < 0 or index >= len(SOURCES):
            return False
        source_key = SOURCES[index]["key"]
        dl = self._downloaders[source_key]
        return bool(dl.set_setting(key, value))

    # -- Slots --

    @Slot()
    def reload(self):
        if self._loading:
            return
        self._set_loading(True)
        self._cancel_auto_reload()

        key = SOURCES[self._current_source_index]["key"]
        t = threading.Thread(target=self._fetch_image, args=(key,), daemon=True)
        t.start()

    @Slot(int)
    def setSource(self, index):
        if index < 0 or index >= len(SOURCES):
            return
        self._current_source_index = index
        self._settings.set_preference("source", SOURCES[index]["key"])
        self.currentSourceChanged.emit()
        self.reload()

    @Slot(bool)
    def toggleAutoReload(self, enabled):
        self._auto_reload_enabled = enabled
        self._settings.set_preference("auto_reload_enabled", enabled)
        self.autoReloadEnabledChanged.emit()
        if not enabled:
            self._cancel_auto_reload()
        elif not self._loading:
            self._schedule_auto_reload()

    @Slot(int)
    def setAutoReloadInterval(self, seconds):
        seconds = max(1, min(3600, seconds))
        self._auto_reload_interval = seconds
        self._settings.set_preference("auto_reload_interval", seconds)
        self.autoReloadIntervalChanged.emit()
        if self._auto_reload_enabled and not self._loading:
            self._schedule_auto_reload()

    @Slot(int)
    def setNsfwMode(self, index):
        if index < 0 or index >= len(NSFW_OPTIONS):
            return
        self._nsfw_mode_index = index
        self._settings.set_preference("nsfw_mode", NSFW_OPTIONS[index])
        self.nsfwModeIndexChanged.emit()

    @Slot(str)
    def setDanbooruTags(self, tags):
        dl = self._downloaders["danbooru"]
        dl.set_tags(tags)
        self.danbooruTagsChanged.emit()

    @Slot(str)
    def save(self, file_url):
        path = QUrl(file_url).toLocalFile()
        if not path:
            return
        raw = self._image_provider.get_raw_bytes()
        if not raw:
            return
        try:
            with open(path, "wb") as f:
                f.write(raw)
            self.imageSaved.emit(path)
        except Exception as e:
            self.errorOccurred.emit(str(e))

    @Slot(result=str)
    def suggestedFilename(self):
        key = SOURCES[self._current_source_index]["key"]
        dl = self._downloaders[key]
        ext = self._image_extension or self._image_provider.get_extension()
        return dl.get_filename_suggestion(ext, self._info)

    @Slot()
    def openArtistLink(self):
        link = self._get_artist_link()
        if link:
            from PySide6.QtGui import QDesktopServices
            QDesktopServices.openUrl(QUrl(link))

    # -- Internal --

    def _get_nsfw_mode(self) -> NSFWOption:
        try:
            return list(NSFWOption)[self._nsfw_mode_index]
        except IndexError:
            return NSFWOption.BLOCK_NSFW

    def _fetch_image(self, source_key: str):
        """Runs in a worker thread."""
        try:
            dl = self._downloaders[source_key]
            nsfw_mode = self._get_nsfw_mode()
            url = dl.get_image_url(nsfw_mode)
            info = getattr(dl, "info", None)

            if not url:
                self._pending_error = "Could not retrieve image URL"
                QMetaObject.invokeMethod(
                    self, "_on_fetch_error_slot",
                    Qt.ConnectionType.QueuedConnection,
                )
                return

            response = requests.get(
                url,
                headers=dl.get_request_headers(),
                timeout=30,
            )
            response.raise_for_status()
            data = response.content

            self._pending_data = data
            self._pending_info = info
            QMetaObject.invokeMethod(
                self, "_on_fetch_success_slot",
                Qt.ConnectionType.QueuedConnection,
            )

        except Exception as e:
            self._pending_error = str(e)
            QMetaObject.invokeMethod(
                self, "_on_fetch_error_slot",
                Qt.ConnectionType.QueuedConnection,
            )

    @Slot()
    def _on_fetch_success_slot(self):
        """Runs on the main thread -- reads pending data set by the worker."""
        data = self._pending_data
        info = self._pending_info
        self._pending_data = None
        self._pending_info = None

        if data is None:
            self.errorOccurred.emit("No image data received")
            self._finish_loading()
            return

        self._info = info

        if self._image_provider.set_image(data):
            self._image_id = str(uuid.uuid4())
            self._has_image = True
            self._image_extension = self._image_provider.get_extension()
            self.imageChanged.emit()
            self.hasImageChanged.emit()
            self.artistNameChanged.emit()
            self.artistLinkChanged.emit()
        else:
            self.errorOccurred.emit("Failed to decode image")

        self._finish_loading()

    @Slot()
    def _on_fetch_error_slot(self):
        """Runs on the main thread -- reads pending error set by the worker."""
        message = self._pending_error or "Unknown error"
        self._pending_error = None
        print(f"Fetch error: {message}")
        self.errorOccurred.emit(message)
        self._finish_loading()

    def _finish_loading(self):
        self._set_loading(False)
        if self._auto_reload_enabled:
            self._schedule_auto_reload()

    def _schedule_auto_reload(self):
        self._cancel_auto_reload()
        if self._auto_reload_enabled:
            self._auto_timer.start(self._auto_reload_interval * 1000)

    def _cancel_auto_reload(self):
        self._auto_timer.stop()

    def _on_auto_timer(self):
        if self._auto_reload_enabled:
            self.reload()
