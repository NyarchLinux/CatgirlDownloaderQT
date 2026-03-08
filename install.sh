#!/bin/bash
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Nyarch Linux

# Catgirl Downloader QT - Flatpak build and install script

set -e

APP_ID="moe.nyarchlinux.catgirldownloaderqt"
BUILD_DIR="flatpak-build-dir"
REPO_DIR="repo"

echo "Building Catgirl Downloader QT flatpak..."

# Build the flatpak
flatpak-builder --force-clean --install-deps-from flathub "$BUILD_DIR" "$APP_ID.json"

# Check if we should create a bundle
if [ "$1" == "--bundle" ]; then
    echo "Creating flatpak bundle..."
    flatpak-builder --repo="$REPO_DIR" --force-clean "$BUILD_DIR" "$APP_ID.json"
    flatpak build-bundle "$REPO_DIR" catgirldownloaderqt.flatpak "$APP_ID"
    echo "Bundle created: catgirldownloaderqt.flatpak"
fi

# Check if we should install
if [ "$1" == "--install" ]; then
    echo "Installing flatpak..."
    flatpak-builder --user --install --force-clean "$BUILD_DIR" "$APP_ID.json"
    echo "Installed! Run with: flatpak run $APP_ID"
fi

# Run if requested
if [ "$1" == "--run" ] || [ -z "$1" ]; then
    echo "Running Catgirl Downloader QT..."
    flatpak-builder --run "$BUILD_DIR" "$APP_ID.json" catgirldownloaderqt
fi

echo "Done!"
