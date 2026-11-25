import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

ApplicationWindow {
    id: window
    visible: true
    width: 440
    height: 860
    title: "Bem vindo a nova era digital com Veras Tecnologia!"
    color: "#0f141c"

    header: ToolBar {
        background: Rectangle { color: "#161f2e" }
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 12
            anchors.rightMargin: 12

            ToolButton {
                text: "☰"
                contentItem: Text {
                    text: "☰"
                    color: "#ffffff"
                    font.pointSize: 16
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                onClicked: drawer.open()
            }

            Text {
                id: headerTitle
                text: "Bem vindo a nova era digital com Veras Tecnologia!"
                color: "#ffffff"
                font.bold: true
                font.pointSize: 14
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
            }
        }
    }

    Drawer {
        id: drawer
        width: 280
        height: window.height
        background: Rectangle { color: "#121824" }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 16
            spacing: 12

            Text {
                text: "Módulos do App"
                color: "#00e5ff"
                font.bold: true
                font.pointSize: 16
            }

            ListView {
                id: menuList
                Layout.fillWidth: true
                Layout.fillHeight: true
                model: screenModel
                delegate: ItemDelegate {
                    width: parent.width
                    contentItem: Text {
                        text: model.title
                        color: "#ffffff"
                        font.pointSize: 13
                    }
                    onClicked: {
                        headerTitle.text = model.title;
                        screenStack.replace(Qt.resolvedUrl(model.componentUrl));
                        drawer.close();
                    }
                }
            }
        }
    }

    ListModel {
        id: screenModel
        ListElement { title: "Home"; componentUrl: "HomeView.qml" }
    }

    StackView {
        id: screenStack
        anchors.fill: parent
        initialItem: Qt.resolvedUrl("HomeView.qml")
    }
}
