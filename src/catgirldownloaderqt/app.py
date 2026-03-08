#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Nyarch Linux

"""Main application entry point for Catgirl Downloader QT"""

import os
import sys
import signal
from importlib import resources

from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtCore import QUrl, QCoreApplication
from PySide6.QtQml import QQmlApplicationEngine

from catgirldownloaderqt.image_provider import DownloaderImageProvider
from catgirldownloaderqt.backend import Backend


def run() -> int:
    QCoreApplication.setApplicationName("Catgirl Downloader")
    QCoreApplication.setOrganizationName("Nyarch Linux")
    QCoreApplication.setOrganizationDomain("nyarchlinux.moe")
    QCoreApplication.setApplicationVersion("0.1.0")

    os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "org.kde.desktop")

    app = QGuiApplication(sys.argv)
    app.setDesktopFileName("moe.nyarchlinux.catgirldownloaderqt")
    app.setWindowIcon(QIcon.fromTheme("moe.nyarchlinux.catgirldownloaderqt"))

    engine = QQmlApplicationEngine()

    signal.signal(signal.SIGINT, signal.SIG_DFL)

    image_provider = DownloaderImageProvider()
    engine.addImageProvider("downloader", image_provider)

    backend = Backend(image_provider)
    engine.rootContext().setContextProperty("backend", backend)

    pkg_files = resources.files("catgirldownloaderqt")
    main_qml = pkg_files.joinpath("qml/main.qml")
    engine.load(QUrl.fromLocalFile(str(main_qml)))

    if not engine.rootObjects():
        return 1

    return app.exec()


def main() -> None:
    raise SystemExit(run())
