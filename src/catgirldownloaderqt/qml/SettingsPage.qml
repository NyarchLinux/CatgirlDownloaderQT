// SPDX-License-Identifier: GPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Nyarch Linux

import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami

Kirigami.Dialog {
    id: settingsDialog

    title: qsTr("Settings")
    standardButtons: Kirigami.Dialog.Close
    preferredWidth: Kirigami.Units.gridUnit * 24

    ColumnLayout {
        spacing: Kirigami.Units.largeSpacing

        Kirigami.Heading {
            text: qsTr("Images")
            level: 3
        }

        Kirigami.Separator {
            Layout.fillWidth: true
        }

        Kirigami.FormLayout {

            Controls.ComboBox {
                Kirigami.FormData.label: qsTr("NSFW Mode:")
                model: root.nsfwOpts
                currentIndex: backend.nsfwModeIndex
                onActivated: function(index) {
                    backend.setNsfwMode(index)
                }
                Layout.fillWidth: true
            }

            Controls.SpinBox {
                Kirigami.FormData.label: qsTr("Auto reload interval (seconds):")
                from: 1
                to: 3600
                value: backend.autoReloadInterval
                editable: true
                onValueModified: backend.setAutoReloadInterval(value)
                Layout.fillWidth: true
            }
        }

        Controls.Label {
            visible: backend.sourceHasSettings(sourceCombo.currentIndex)
            text: qsTr("Source-specific settings are available via the gear icon next to the source selector in the toolbar.")
            wrapMode: Text.WordWrap
            opacity: 0.6
            font: Kirigami.Theme.smallFont
            Layout.fillWidth: true
            Layout.topMargin: Kirigami.Units.largeSpacing
        }
    }
}
