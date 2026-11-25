import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: homeRoot
    anchors.fill: parent

    Rectangle {
        anchors.fill: parent
        color: "#0f141c"

        ColumnLayout {
            anchors.centerIn: parent
            spacing: 16

            Text {
                text: "Serene Core Online"
                color: "#00e5ff"
                font.bold: true
                font.pointSize: 18
                Layout.alignment: Qt.AlignHCenter
            }

            Text {
                text: "Selecione uma tela no menu superior (☰)"
                color: "#a0aec0"
                font.pointSize: 12
                Layout.alignment: Qt.AlignHCenter
            }

            Button {
                text: "Disparar Ação C++"
                onClicked: Bridge.logAction("Botão Home Pressionado")
                Layout.alignment: Qt.AlignHCenter
            }
        }
    }
}
