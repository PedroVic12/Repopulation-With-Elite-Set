import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

ApplicationWindow {
    id: root
    width: 1500
    height: 920
    minimumWidth: 1120
    minimumHeight: 700
    visible: true
    title: "Smart Grid Studio | Diagrama Unifilar"
    color: "#edf1f3"
    property var topology: JSON.parse(smartEngine.networkTopology)
    property string lastMessage: "Importe um deck ANAREDE ou selecione um exemplo."

    Connections {
        target: smartEngine
        function onNetworkUpdated() {
            root.topology = JSON.parse(smartEngine.networkTopology)
            if (!deckEditor.activeFocus)
                deckEditor.text = smartEngine.deckText
            topologyCanvas.requestPaint()
        }
        function onLogMessage(message) {
            root.lastMessage = message
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 76
            color: "#172a36"

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 24
                anchors.rightMargin: 24
                spacing: 18

                ColumnLayout {
                    spacing: 2
                    Text {
                        text: "SMART GRID STUDIO"
                        color: "#f2f6f8"
                        font.pixelSize: 21
                        font.bold: true
                    }
                    Text {
                        text: "Editor ANAREDE · Pandapower · diagrama unifilar"
                        color: "#b8c9d2"
                        font.pixelSize: 12
                    }
                }

                Item { Layout.fillWidth: true }

                Text {
                    text: root.topology.buses.length + " barras   |   "
                        + root.topology.lines.length + " linhas   |   "
                        + root.topology.transformers.length + " trafos"
                    color: "#9ce4cc"
                    font.pixelSize: 14
                    font.bold: true
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.margins: 16
            spacing: 14

            Rectangle {
                Layout.preferredWidth: 410
                Layout.fillHeight: true
                color: "#ffffff"
                border.color: "#d5dfe4"
                radius: 5

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 14
                    spacing: 10

                    RowLayout {
                        Layout.fillWidth: true
                        Text {
                            text: "DECK ANAREDE"
                            color: "#172a36"
                            font.bold: true
                            font.pixelSize: 14
                        }
                        Item { Layout.fillWidth: true }
                        ComboBox {
                            id: examplePicker
                            model: ["Exemplo: 3 barras", "Exemplo: 5 barras", "Exemplo: 10 barras"]
                            implicitWidth: 170
                            onActivated: {
                                if (currentIndex > 0)
                                    smartEngine.load_example_deck(["3", "5", "10"][currentIndex - 1])
                            }
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        Button {
                            text: "Abrir PWF"
                            onClicked: smartEngine.open_deck_file()
                        }
                        Button {
                            text: "Salvar PWF"
                            onClicked: smartEngine.save_deck_file()
                        }
                        Item { Layout.fillWidth: true }
                        Button {
                            text: "Importar"
                            onClicked: smartEngine.parse_anarede_deck(deckEditor.text)
                            background: Rectangle {
                                color: "#147d68"
                                radius: 4
                            }
                            contentItem: Text {
                                text: parent.text
                                color: "#ffffff"
                                font.bold: true
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                        }
                    }

                    TextArea {
                        id: deckEditor
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        Layout.minimumHeight: 260
                        color: "#e3edf2"
                        selectionColor: "#267e71"
                        selectedTextColor: "#ffffff"
                        font.family: "Consolas"
                        font.pixelSize: 12
                        wrapMode: TextEdit.NoWrap
                        selectByMouse: true
                        background: Rectangle {
                            color: "#15232d"
                            border.color: "#344a57"
                            radius: 3
                        }
                        Component.onCompleted: text = smartEngine.deckText
                        onTextChanged: {
                            if (activeFocus)
                                smartEngine.set_deck_text(text)
                        }
                    }

                    Text {
                        Layout.fillWidth: true
                        text: "DBAR define as barras; DLIN define linhas e transformadores (por nível de tensão/tap)."
                        color: "#586b75"
                        font.pixelSize: 11
                        wrapMode: Text.WordWrap
                    }

                    Text {
                        Layout.fillWidth: true
                        text: smartEngine.resultsSummary
                        color: smartEngine.resultsSummary.indexOf("Falha") >= 0
                            || smartEngine.resultsSummary.indexOf("Erro") >= 0 ? "#a33d32" : "#286d5c"
                        font.pixelSize: 12
                        wrapMode: Text.WordWrap
                    }

                    Text {
                        id: statusText
                        Layout.fillWidth: true
                        text: root.lastMessage
                        color: "#647984"
                        font.pixelSize: 11
                        wrapMode: Text.WordWrap
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: "#ffffff"
                border.color: "#d5dfe4"
                radius: 5

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 14
                    spacing: 8

                    RowLayout {
                        Layout.fillWidth: true
                        Text {
                            text: "DIAGRAMA UNIFILAR"
                            color: "#172a36"
                            font.bold: true
                            font.pixelSize: 14
                        }
                        Item { Layout.fillWidth: true }
                        Text { text: "━ Barramento"; color: "#354c58"; font.pixelSize: 11 }
                        Text { text: "━━ Linha"; color: "#607b89"; font.pixelSize: 11 }
                        Text { text: "◎ Trafo"; color: "#b66f26"; font.pixelSize: 11 }
                    }

                    Flickable {
                        id: diagramViewport
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        contentWidth: topologyCanvas.width
                        contentHeight: topologyCanvas.height
                        boundsBehavior: Flickable.StopAtBounds
                        ScrollBar.horizontal: ScrollBar { }
                        ScrollBar.vertical: ScrollBar { }

                        Canvas {
                            id: topologyCanvas
                            width: Math.max(diagramViewport.width, (root.topology.layoutWidth + 1) * 220 + 140)
                            height: Math.max(diagramViewport.height, (root.topology.layoutHeight + 1) * 150 + 120)

                            onPaint: {
                                var ctx = getContext("2d")
                                ctx.clearRect(0, 0, width, height)
                                ctx.fillStyle = "#fbfcfd"
                                ctx.fillRect(0, 0, width, height)

                                ctx.strokeStyle = "#edf1f3"
                                ctx.lineWidth = 1
                                for (var gridX = 20; gridX < width; gridX += 24) {
                                    ctx.beginPath()
                                    ctx.moveTo(gridX, 0)
                                    ctx.lineTo(gridX, height)
                                    ctx.stroke()
                                }
                                for (var gridY = 20; gridY < height; gridY += 24) {
                                    ctx.beginPath()
                                    ctx.moveTo(0, gridY)
                                    ctx.lineTo(width, gridY)
                                    ctx.stroke()
                                }

                                var data = root.topology
                                var positions = ({})
                                var leftMargin = 70
                                var topMargin = 60
                                var columnSpacing = 220
                                var rowSpacing = 150
                                for (var i = 0; i < data.buses.length; ++i) {
                                    var bus = data.buses[i]
                                    positions[String(bus.id)] = {
                                        x: leftMargin + bus.x * columnSpacing,
                                        y: topMargin + bus.y * rowSpacing
                                    }
                                }

                                function drawBranch(edge, isTransformer, branchIndex) {
                                    var from = positions[String(edge.from)]
                                    var to = positions[String(edge.to)]
                                    if (!from || !to)
                                        return

                                    var busbarHalfWidth = 48
                                    var startX
                                    var endX
                                    var routeX
                                    var start = from
                                    var finish = to
                                    if (Math.abs(from.x - to.x) < 96) {
                                        startX = from.x + busbarHalfWidth
                                        endX = to.x + busbarHalfWidth
                                        routeX = Math.max(from.x, to.x) + 82 + (branchIndex % 4) * 13
                                        ctx.beginPath()
                                        ctx.moveTo(startX, from.y)
                                        ctx.lineTo(routeX, from.y)
                                        ctx.lineTo(routeX, to.y)
                                        ctx.lineTo(endX, to.y)
                                    } else {
                                        if (from.x > to.x) {
                                            start = to
                                            finish = from
                                        }
                                        startX = start.x + busbarHalfWidth
                                        endX = finish.x - busbarHalfWidth
                                        routeX = (startX + endX) / 2
                                        ctx.beginPath()
                                        ctx.moveTo(startX, start.y)
                                        ctx.lineTo(routeX, start.y)
                                        ctx.lineTo(routeX, finish.y)
                                        ctx.lineTo(endX, finish.y)
                                    }

                                    ctx.strokeStyle = isTransformer ? "#bd772e" : "#607b89"
                                    ctx.lineWidth = isTransformer ? 2.5 : 2
                                    ctx.stroke()

                                    var symbolX = routeX
                                    var symbolY = (start.y + finish.y) / 2
                                    if (isTransformer) {
                                        ctx.fillStyle = "#fbfcfd"
                                        ctx.strokeStyle = "#bd772e"
                                        ctx.lineWidth = 2
                                        ctx.beginPath()
                                        ctx.arc(symbolX - 7, symbolY, 8, 0, 2 * Math.PI)
                                        ctx.fill()
                                        ctx.stroke()
                                        ctx.beginPath()
                                        ctx.arc(symbolX + 7, symbolY, 8, 0, 2 * Math.PI)
                                        ctx.fill()
                                        ctx.stroke()
                                    }

                                    ctx.fillStyle = "#526773"
                                    ctx.font = "10px 'Segoe UI'"
                                    ctx.textAlign = "center"
                                    ctx.textBaseline = "bottom"
                                    ctx.fillText(edge.name || (isTransformer ? "Trafo" : "Linha"), symbolX, symbolY - 12)
                                }

                                for (var lineIndex = 0; lineIndex < data.lines.length; ++lineIndex)
                                    drawBranch(data.lines[lineIndex], false, lineIndex)
                                for (var trafoIndex = 0; trafoIndex < data.transformers.length; ++trafoIndex)
                                    drawBranch(data.transformers[trafoIndex], true, trafoIndex)

                                for (var busIndex = 0; busIndex < data.buses.length; ++busIndex) {
                                    var busData = data.buses[busIndex]
                                    var point = positions[String(busData.id)]
                                    var color = busData.kind === "reference" ? "#c58b25"
                                        : busData.kind === "generator" ? "#27856d"
                                        : busData.kind === "load" ? "#4b82a1" : "#344d5b"

                                    ctx.strokeStyle = color
                                    ctx.lineWidth = 7
                                    ctx.lineCap = "square"
                                    ctx.beginPath()
                                    ctx.moveTo(point.x - 48, point.y)
                                    ctx.lineTo(point.x + 48, point.y)
                                    ctx.stroke()
                                    ctx.lineCap = "butt"

                                    ctx.fillStyle = "#172a36"
                                    ctx.font = "bold 12px 'Segoe UI'"
                                    ctx.textAlign = "center"
                                    ctx.textBaseline = "bottom"
                                    ctx.fillText("DBAR " + busData.id, point.x, point.y - 9)
                                    ctx.font = "11px 'Segoe UI'"
                                    ctx.textBaseline = "top"
                                    ctx.fillText(busData.name, point.x, point.y + 9)
                                    ctx.fillStyle = "#627984"
                                    ctx.font = "10px 'Segoe UI'"
                                    ctx.fillText(busData.kv + " kV  ·  " + busData.kind.toUpperCase(), point.x, point.y + 24)
                                }
                            }

                            Component.onCompleted: requestPaint()
                        }
                    }
                }
            }
        }
    }
}
