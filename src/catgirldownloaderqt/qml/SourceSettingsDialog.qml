// SPDX-License-Identifier: GPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Nyarch Linux

import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami

Kirigami.Dialog {
    id: sourceSettingsDialog

    property int sourceIndex: -1
    property bool forbiddenTagsRemoved: false

    title: sourceIndex >= 0 ? backend.sourceSettingsTitle(sourceIndex) : ""
    standardButtons: Kirigami.Dialog.Close
    preferredWidth: Kirigami.Units.gridUnit * 24

    onOpened: forbiddenTagsRemoved = false
    onClosed: {
        if (forbiddenTagsRemoved) {
            forbiddenTagsDialog.open()
        }
    }

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
                        id: fieldLoader
                        property var fieldData: field
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
            Kirigami.FormData.label: (parent && parent.fieldData ? parent.fieldData.label : "") + ":"
            text: parent && parent.fieldData ? backend.getSourceSetting(sourceSettingsDialog.sourceIndex, parent.fieldData.key) : ""
            placeholderText: parent && parent.fieldData ? (parent.fieldData.placeholder || "") : ""
            onTextEdited: {
                if (parent && parent.fieldData) {
                    if (backend.setSourceSetting(sourceSettingsDialog.sourceIndex, parent.fieldData.key, text)) {
                        sourceSettingsDialog.forbiddenTagsRemoved = true
                    }
                }
            }
        }
    }

    Component {
        id: spinBoxComponent

        Controls.SpinBox {
            Kirigami.FormData.label: (parent && parent.fieldData ? parent.fieldData.label : "") + ":"
            from: 0
            to: 99999
            value: parent && parent.fieldData ? (parseInt(backend.getSourceSetting(sourceSettingsDialog.sourceIndex, parent.fieldData.key)) || 0) : 0
            editable: true
            onValueModified: {
                if (parent && parent.fieldData) {
                    backend.setSourceSetting(sourceSettingsDialog.sourceIndex, parent.fieldData.key, value.toString())
                }
            }
        }
    }

    Component {
        id: switchComponent

        Controls.Switch {
            Kirigami.FormData.label: (parent && parent.fieldData ? parent.fieldData.label : "") + ":"
            checked: parent && parent.fieldData ? (backend.getSourceSetting(sourceSettingsDialog.sourceIndex, parent.fieldData.key) === "true") : false
            onToggled: {
                if (parent && parent.fieldData) {
                    backend.setSourceSetting(sourceSettingsDialog.sourceIndex, parent.fieldData.key, checked ? "true" : "false")
                }
            }
        }
    }

    Kirigami.Dialog {
        id: forbiddenTagsDialog
        title: qsTr("Danbooru Settings")
        standardButtons: Kirigami.Dialog.Ok
        preferredWidth: Kirigami.Units.gridUnit * 24

        Controls.Label {
            text: qsTr("Due to a limitation of Danbooru, certain tags have been automatically removed from your settings. For more information, visit <a href=\"https://danbooru.donmai.us/wiki_pages/help:censored_tags\">Danbooru's censored tags help page</a>.")
            textFormat: Text.RichText
            wrapMode: Text.WordWrap
            Layout.fillWidth: true
            onLinkActivated: function(link) { Qt.openUrlExternally(link) }
        }
    }
}
