// SPDX-License-Identifier: GPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Nyarch Linux

import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import QtQuick.Dialogs as Dialogs
import org.kde.kirigami as Kirigami

Kirigami.ApplicationWindow {
    id: root

    title: qsTr("Catgirl Downloader")

    minimumWidth: Kirigami.Units.gridUnit * 28
    minimumHeight: Kirigami.Units.gridUnit * 24
    width: Kirigami.Units.gridUnit * 40
    height: Kirigami.Units.gridUnit * 32

    property var sourceNames: backend.sourceNames()
    property var nsfwOpts: backend.nsfwOptions()

    header: Controls.ToolBar {
        id: toolbar

        RowLayout {
            anchors.fill: parent
            spacing: Kirigami.Units.smallSpacing

            Controls.ToolButton {
                icon.name: "view-refresh-symbolic"
                enabled: !backend.loading
                onClicked: backend.reload()

                Controls.ToolTip.visible: hovered
                Controls.ToolTip.text: qsTr("Refresh (Ctrl+R)")
            }

            Controls.BusyIndicator {
                running: backend.loading
                visible: backend.loading
                Layout.preferredWidth: Kirigami.Units.iconSizes.medium
                Layout.preferredHeight: Kirigami.Units.iconSizes.medium
            }

            Item { Layout.fillWidth: true }

            Controls.Label {
                text: qsTr("Auto")
                opacity: 0.7
            }

            Controls.Switch {
                id: autoReloadSwitch
                checked: backend.autoReloadEnabled
                onToggled: backend.toggleAutoReload(checked)

                Controls.ToolTip.visible: hovered
                Controls.ToolTip.text: qsTr("Auto reload")
            }

            Controls.ComboBox {
                id: sourceCombo
                model: root.sourceNames
                currentIndex: backend.currentSource
                onActivated: function(index) {
                    backend.setSource(index)
                }
                Layout.preferredWidth: Kirigami.Units.gridUnit * 8

                Controls.ToolTip.visible: hovered
                Controls.ToolTip.text: qsTr("Image source")
            }

            Controls.ToolButton {
                icon.name: "emblem-system-symbolic"
                visible: backend.sourceHasSettings(sourceCombo.currentIndex)
                onClicked: {
                    sourceSettingsDialog.sourceIndex = sourceCombo.currentIndex
                    sourceSettingsDialog.open()
                }

                Controls.ToolTip.visible: hovered
                Controls.ToolTip.text: qsTr("Source settings")
            }

            Controls.ToolButton {
                icon.name: "document-save-symbolic"
                enabled: backend.hasImage && !backend.loading
                onClicked: {
                    saveDialog.currentFile = "file:///" + backend.suggestedFilename()
                    saveDialog.open()
                }

                Controls.ToolTip.visible: hovered
                Controls.ToolTip.text: qsTr("Save image (Ctrl+S)")
            }

            Controls.ToolButton {
                icon.name: "application-menu"
                onClicked: optionMenu.popup()

                Controls.ToolTip.visible: hovered
                Controls.ToolTip.text: qsTr("Menu")

                Controls.Menu {
                    id: optionMenu

                    Controls.MenuItem {
                        text: qsTr("About Art")
                        icon.name: "preferences-desktop-icons"
                        enabled: backend.hasImage
                        onTriggered: artDialog.open()
                    }

                    Controls.MenuSeparator {}

                    Controls.MenuItem {
                        text: qsTr("Settings")
                        icon.name: "configure"
                        onTriggered: settingsSheet.open()
                    }

                    Controls.MenuSeparator {}

                    Controls.MenuItem {
                        text: qsTr("About Catgirl Downloader")
                        icon.name: "help-about"
                        onTriggered: aboutDialog.open()
                    }

                    Controls.MenuItem {
                        text: qsTr("Quit")
                        icon.name: "application-exit"
                        onTriggered: Qt.quit()
                    }
                }
            }
        }
    }

    // Main content: image display
    Item {
        anchors.fill: parent

        Image {
            id: mainImage
            anchors.fill: parent
            anchors.margins: Kirigami.Units.largeSpacing
            fillMode: Image.PreserveAspectFit
            source: backend.imageId !== "" ? "image://downloader/" + backend.imageId : ""
            asynchronous: false
            cache: false
            visible: backend.hasImage
        }

        Kirigami.PlaceholderMessage {
            anchors.centerIn: parent
            visible: !backend.hasImage && !backend.loading
            text: qsTr("No image loaded")
            explanation: qsTr("Click the refresh button to load an image")
            icon.name: "image-x-generic"
        }

        Controls.BusyIndicator {
            anchors.centerIn: parent
            running: backend.loading && !backend.hasImage
            visible: running
            Layout.preferredWidth: Kirigami.Units.gridUnit * 4
            Layout.preferredHeight: Kirigami.Units.gridUnit * 4
        }
    }

    // Save file dialog
    Dialogs.FileDialog {
        id: saveDialog
        title: qsTr("Save Image")
        fileMode: Dialogs.FileDialog.SaveFile
        onAccepted: backend.save(selectedFile)
    }

    // About Art dialog
    Kirigami.Dialog {
        id: artDialog
        title: qsTr("About Art")
        standardButtons: Kirigami.Dialog.Close
        preferredWidth: Kirigami.Units.gridUnit * 20

        ColumnLayout {
            spacing: Kirigami.Units.largeSpacing

            Kirigami.Icon {
                source: "preferences-desktop-icons"
                Layout.preferredWidth: Kirigami.Units.gridUnit * 4
                Layout.preferredHeight: Kirigami.Units.gridUnit * 4
                Layout.alignment: Qt.AlignHCenter
            }

            Kirigami.Heading {
                text: qsTr("Art Information")
                level: 2
                Layout.alignment: Qt.AlignHCenter
            }

            Kirigami.FormLayout {
                Controls.Label {
                    Kirigami.FormData.label: qsTr("Artist:")
                    text: backend.artistName || qsTr("Unknown")
                    wrapMode: Text.WordWrap
                }
                Controls.Label {
                    Kirigami.FormData.label: qsTr("Source:")
                    text: backend.artistLink || qsTr("Unknown")
                    wrapMode: Text.WrapAnywhere
                    color: backend.artistLink ? Kirigami.Theme.linkColor : Kirigami.Theme.textColor
                    MouseArea {
                        anchors.fill: parent
                        cursorShape: backend.artistLink ? Qt.PointingHandCursor : Qt.ArrowCursor
                        onClicked: {
                            if (backend.artistLink) {
                                backend.openArtistLink()
                            }
                        }
                    }
                }
            }
        }
    }

    // About app dialog
    Kirigami.Dialog {
        id: aboutDialog
        title: qsTr("About Catgirl Downloader")
        standardButtons: Kirigami.Dialog.Close
        preferredWidth: Kirigami.Units.gridUnit * 22

        ColumnLayout {
            spacing: Kirigami.Units.largeSpacing

            Kirigami.Icon {
                source: "moe.nyarchlinux.catgirldownloaderqt"
                Layout.preferredWidth: Kirigami.Units.gridUnit * 6
                Layout.preferredHeight: Kirigami.Units.gridUnit * 6
                Layout.alignment: Qt.AlignHCenter
                fallback: "image-x-generic"
            }

            Kirigami.Heading {
                text: qsTr("Catgirl Downloader")
                level: 1
                Layout.alignment: Qt.AlignHCenter
            }

            Controls.Label {
                text: qsTr("Version 0.1.0")
                Layout.alignment: Qt.AlignHCenter
                opacity: 0.7
            }

            Controls.Label {
                text: qsTr("Browse and save anime-style images from multiple sources including nekos.moe, waifu.im, and Danbooru.")
                wrapMode: Text.WordWrap
                horizontalAlignment: Text.AlignHCenter
                Layout.fillWidth: true
            }

            Controls.Label {
                text: qsTr("Built with Kirigami for KDE Plasma")
                Layout.alignment: Qt.AlignHCenter
                opacity: 0.7
            }

            Controls.Label {
                text: "\u00A9 2026 Nyarch Linux"
                Layout.alignment: Qt.AlignHCenter
                opacity: 0.5
            }
        }
    }

    // Settings overlay sheet
    SettingsPage {
        id: settingsSheet
    }

    // Per-source settings dialog
    SourceSettingsDialog {
        id: sourceSettingsDialog
    }

    // Keyboard shortcuts
    Shortcut {
        sequence: "Ctrl+R"
        onActivated: backend.reload()
    }

    Shortcut {
        sequence: "Ctrl+S"
        onActivated: {
            if (backend.hasImage) {
                saveDialog.currentFile = "file:///" + backend.suggestedFilename()
                saveDialog.open()
            }
        }
    }

    Shortcut {
        sequence: StandardKey.Quit
        onActivated: Qt.quit()
    }

    Component.onCompleted: {
        backend.reload()
    }
}
