// SPDX-License-Identifier: GPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Nyarch Linux

import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami

Kirigami.Dialog {
    id: sourceSettingsDialog

    property int sourceIndex: -1

    title: sourceIndex >= 0 ? backend.sourceSettingsTitle(sourceIndex) : ""
    standardButtons: Kirigami.Dialog.Close
    preferredWidth: Kirigami.Units.gridUnit * 24

    onSourceIndexChanged: {
        if (sourceIndex >= 0) {
            fieldsRepeater.model = backend.sourceSettingsFields(sourceIndex)
        } else {
            fieldsRepeater.model = []
        }
    }

    ColumnLayout {
        spacing: Kirigami.Units.largeSpacing

        Kirigami.FormLayout {
            id: formLayout

            Repeater {
                id: fieldsRepeater

                delegate: ColumnLayout {
                    spacing: Kirigami.Units.smallSpacing
                    Layout.fillWidth: true

                    property var field: modelData

                    Loader {
                        Layout.fillWidth: true
                        sourceComponent: {
                            if (field.type === "text")
                                return textFieldComponent
                            if (field.type === "number")
                                return spinBoxComponent
                            if (field.type === "bool")
                                return switchComponent
                            return textFieldComponent
                        }
                    }

                    Controls.Label {
                        visible: field.description !== undefined && field.description !== ""
                        text: field.description || ""
                        wrapMode: Text.WordWrap
                        opacity: 0.6
                        font: Kirigami.Theme.smallFont
                        Layout.fillWidth: true
                    }
                }
            }
        }
    }

    Component {
        id: textFieldComponent

        Controls.TextField {
            Kirigami.FormData.label: field.label + ":"
            text: backend.getSourceSetting(sourceSettingsDialog.sourceIndex, field.key)
            placeholderText: field.placeholder || ""
            onTextEdited: backend.setSourceSetting(sourceSettingsDialog.sourceIndex, field.key, text)
        }
    }

    Component {
        id: spinBoxComponent

        Controls.SpinBox {
            Kirigami.FormData.label: field.label + ":"
            from: 0
            to: 99999
            value: parseInt(backend.getSourceSetting(sourceSettingsDialog.sourceIndex, field.key)) || 0
            editable: true
            onValueModified: backend.setSourceSetting(sourceSettingsDialog.sourceIndex, field.key, value.toString())
        }
    }

    Component {
        id: switchComponent

        Controls.Switch {
            Kirigami.FormData.label: field.label + ":"
            checked: backend.getSourceSetting(sourceSettingsDialog.sourceIndex, field.key) === "true"
            onToggled: backend.setSourceSetting(sourceSettingsDialog.sourceIndex, field.key, checked ? "true" : "false")
        }
    }
}
