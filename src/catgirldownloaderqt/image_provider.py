# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Nyarch Linux

import threading

from PySide6.QtCore import QSize
from PySide6.QtGui import QImage
from PySide6.QtQuick import QQuickImageProvider


class DownloaderImageProvider(QQuickImageProvider):
    """Serves downloaded images to QML via the image://downloader/<id> scheme."""

    def __init__(self):
        super().__init__(QQuickImageProvider.ImageType.Image)
        self._lock = threading.Lock()
        self._image = QImage()
        self._raw_bytes = b""
        self._extension = ""

    def set_image(self, data: bytes) -> bool:
        img = QImage()
        if not img.loadFromData(data):
            return False
        with self._lock:
            self._raw_bytes = data
            self._image = img
            self._extension = self._detect_format(data)
        return True

    def get_raw_bytes(self) -> bytes:
        with self._lock:
            return self._raw_bytes

    def get_extension(self) -> str:
        with self._lock:
            return self._extension

    def requestImage(self, id, size, requestedSize):
        with self._lock:
            if self._image.isNull():
                fallback = QImage(1, 1, QImage.Format.Format_ARGB32)
                fallback.fill(0)
                return fallback
            return self._image.copy()

    @staticmethod
    def _detect_format(data: bytes) -> str:
        if data[:8] == b"\x89PNG\r\n\x1a\n":
            return "png"
        if data[:2] == b"\xff\xd8":
            return "jpg"
        if data[:4] == b"GIF8":
            return "gif"
        if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
            return "webp"
        return "png"
