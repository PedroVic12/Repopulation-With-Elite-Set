import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: journaltimelineRoot
    anchors.fill: parent

    Rectangle {
        anchors.fill: parent
        color: "#0f141c"

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 20
            spacing: 15

            Text {
                text: "JournalTimeline Module"
                color: "#00e5ff"
                font.pointSize: 20
                font.bold: true
            }

            Text {
                text: "Tela gerada via CLI para Serene & Performance Suite"
                color: "#a0aec0"
                font.pointSize: 12
            }

            Button {
                text: "Executar Ação Native (C++)"
                onClicked: {
                    Bridge.logAction("JournalTimelineView::execute");
                }
            }

            Item { Layout.fillHeight: true }
        }
    }
}
