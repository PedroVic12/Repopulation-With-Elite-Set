import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

ApplicationWindow {
    id: window
    visible: true
    width: 420
    height: 860
    title: "Serene & Performance Suite"
    color: "#0f141c"

    StackView {
        id: screenStack
        anchors.fill: parent
        initialItem: homeViewComponent
    }

    Component {
        id: homeViewComponent
        Rectangle {
            color: "#0f141c"
            ColumnLayout {
                anchors.centerIn: parent
                spacing: 16

                Text {
                    text: "Serene Core Online"
                    color: "#ffffff"
                    font.bold: true
                    font.pointSize: 16
                    Layout.alignment: Qt.AlignHCenter
                }

                Button {
                    text: "Disparar Ação C++"
                    onClicked: Bridge.logAction("Botão Inicial Pressionado")
                    Layout.alignment: Qt.AlignHCenter
                }
            }
        }
    }
}
