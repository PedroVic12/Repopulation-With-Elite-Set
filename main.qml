import QtQuick
import QtQuick.Controls
ApplicationWindow {
    visible: true
    width: 400
    height: 300
    title: "Batcaverna 2026 - Qt Quick Test"
    background: Rectangle {
        color: "#1e1e2e" // Tema escuro
    }
    Column {
        anchors.centerIn: parent
        spacing: 20
        Text {
            text: "Olá, Pedro!"
            font.pixelSize: 24
            font.bold: true
            color: "#cdd6f4"
            horizontalAlignment: Text.AlignHCenter
        }
        Text {
            text: "Qt Quick + PySide6 rodando com sucesso."
            font.pixelSize: 14
            color: "#a6adc8"
            horizontalAlignment: Text.AlignHCenter
        }
        Button {
            text: "Clique Aqui"
            onClicked: {
                console.log("Botão clicado!")
            }
        }
    }
}


