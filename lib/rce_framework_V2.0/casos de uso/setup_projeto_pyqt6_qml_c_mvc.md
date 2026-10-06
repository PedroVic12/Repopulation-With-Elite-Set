#!/usr/bin/env bash
# ==============================================================================
# Script de Inicialização Automatizada - Painel EA FC com PyQt6, QML & C++
# Arquitetura MVC com integração de Telemetria Arduino/ESP32 via Rede
# ==============================================================================

set -e

PROJECT_NAME="fc_telemetry_app"
echo "=========================================================="
echo "  Iniciando criação do projeto: ${PROJECT_NAME}"
echo "=========================================================="

# Verificação de dependências essenciais do sistema
echo "[1/6] Verificando dependências do sistema operacional..."
MISSING_DEPS=0

for cmd in python3 g++ make; do
    if ! command -v $cmd &> /dev/null; then
        echo " [ERRO] O utilitário '$cmd' não foi encontrado no sistema."
        MISSING_DEPS=1
    fi
done

if [ $MISSING_DEPS -ne 0 ]; then
    echo ""
    echo "Instale os pacotes necessários no Ubuntu/Debian com:"
    echo "  sudo apt update && sudo apt install -y python3 python3-pip python3-venv build-essential"
    exit 1
fi

echo " Dependências nativas verificadas (python3, g++, make)."

# STREAMING_CHUNK:Creating project directory structure
echo "[2/6] Criando estrutura de pastas padrão MVC..."
mkdir -p ${PROJECT_NAME}/{cpp/{include,src},app/{models,controllers,views/qml/{components,pages}}}

cd ${PROJECT_NAME}

# STREAMING_CHUNK:Writing the C++ telemetry engine header
echo "[3/6] Gerando motor de rede C++ (include/TelemetryBridge.hpp)..."
cat << 'EOF' > cpp/include/TelemetryBridge.hpp
#ifndef TELEMETRY_BRIDGE_HPP
#define TELEMETRY_BRIDGE_HPP

#include <cstdint>
#include <string>

// Estrutura de dados de telemetria alinhada com memória binária ou JSON do Arduino
struct TelemetryPacket {
    float batteryVoltage;
    float ultrasonicDistance;
    int32_t motorLeftPwm;
    int32_t motorRightPwm;
    uint8_t lineSensorTriggered;
    uint8_t statusFlag; // 0=Parado, 1=Buscando, 2=Ataque
    uint32_t packetsReceived;
};

// Interface C para exportação simplificada para o Python via ctypes
#ifdef __cplusplus
extern "C" {
#endif

    // Inicializa o socket UDP/TCP cliente para conectar ao Arduino/ESP32
    bool Telemetry_Connect(const char* host, int port);
    
    // Lê o pacote mais recente recebido via buffer de rede
    bool Telemetry_Poll(TelemetryPacket* outPacket);
    
    // Envia comandos de controle (Start/Stop/PWM) para o microcontrolador
    bool Telemetry_SendCommand(const char* commandStr);
    
    // Finaliza o socket
    void Telemetry_Disconnect();

#ifdef __cplusplus
}
#endif

#endif // TELEMETRY_BRIDGE_HPP
EOF

# STREAMING_CHUNK:Writing the C++ network implementation
echo " Gerando implementação C++ de alto desempenho (src/TelemetryBridge.cpp)..."
cat << 'EOF' > cpp/src/TelemetryBridge.cpp
#include "../include/TelemetryBridge.hpp"
#include <iostream>
#include <cstring>
#include <unistd.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <fcntl.h>
#include <chrono>

static int g_socketFd = -1;
static struct sockaddr_in g_serverAddr;
static uint32_t g_packetCounter = 0;
static TelemetryPacket g_lastPacket = {12.4f, 45.0f, 0, 0, 0, 0, 0};

bool Telemetry_Connect(const char* host, int port) {
    if (g_socketFd >= 0) {
        close(g_socketFd);
    }

    g_socketFd = socket(AF_INET, SOCK_DGRAM, 0); // UDP não bloqueante para baixa latência
    if (g_socketFd < 0) {
        return false;
    }

    // Configura o socket para modo Não-Bloqueante
    int flags = fcntl(g_socketFd, F_GETFL, 0);
    fcntl(g_socketFd, F_SETFL, flags | O_NONBLOCK);

    std::memset(&g_serverAddr, 0, sizeof(g_serverAddr));
    g_serverAddr.sin_family = AF_INET;
    g_serverAddr.sin_port = htons(port);
    inet_pton(AF_INET, host, &g_serverAddr.sin_addr);

    return true;
}

bool Telemetry_Poll(TelemetryPacket* outPacket) {
    if (!outPacket) return false;

    if (g_socketFd >= 0) {
        char buffer[256];
        socklen_t addrLen = sizeof(g_serverAddr);
        ssize_t bytesRead = recvfrom(g_socketFd, buffer, sizeof(buffer) - 1, 0, 
                                     (struct sockaddr*)&g_serverAddr, &addrLen);
        
        if (bytesRead > 0) {
            buffer[bytesRead] = '\0';
            // Formato esperado de pacote textual do Arduino: "BAT,DIST,PWM_L,PWM_R,LINE,STATUS"
            // Ex: "11.8,25.4,128,128,0,1"
            float bat = 0, dist = 0;
            int ml = 0, mr = 0, line = 0, st = 0;
            if (sscanf(buffer, "%f,%f,%d,%d,%d,%d", &bat, &dist, &ml, &mr, &line, &st) == 6) {
                g_lastPacket.batteryVoltage = bat;
                g_lastPacket.ultrasonicDistance = dist;
                g_lastPacket.motorLeftPwm = ml;
                g_lastPacket.motorRightPwm = mr;
                g_lastPacket.lineSensorTriggered = (uint8_t)line;
                g_lastPacket.statusFlag = (uint8_t)st;
                g_packetCounter++;
            }
        }
    }

    g_lastPacket.packetsReceived = g_packetCounter;
    *outPacket = g_lastPacket;
    return true;
}

bool Telemetry_SendCommand(const char* commandStr) {
    if (g_socketFd < 0 || !commandStr) return false;
    ssize_t sent = sendto(g_socketFd, commandStr, std::strlen(commandStr), 0,
                          (struct sockaddr*)&g_serverAddr, sizeof(g_serverAddr));
    return (sent > 0);
}

void Telemetry_Disconnect() {
    if (g_socketFd >= 0) {
        close(g_socketFd);
        g_socketFd = -1;
    }
}
EOF

# STREAMING_CHUNK:Creating Makefile for C++ compilation
cat << 'EOF' > cpp/Makefile
CXX = g++
CXXFLAGS = -O3 -Wall -fPIC -std=c++17 -I./include
LDFLAGS = -shared

TARGET = ../libtelemetry.so
SRCS = src/TelemetryBridge.cpp

all: $(TARGET)

$(TARGET): $(SRCS)
	$(CXX) $(CXXFLAGS) $(LDFLAGS) $(SRCS) -o $(TARGET)
	@echo " [C++] Biblioteca dinâmica libtelemetry.so compilada com sucesso."

clean:
	rm -f $(TARGET)
EOF

# STREAMING_CHUNK:Writing Python Model with C++ ctypes binding
echo "[4/6] Gerando camada MVC em Python..."
cat << 'EOF' > app/models/telemetry_model.py
import ctypes
import os
import random
from PyQt6.QtCore import QObject, pyqtSignal, pyqtProperty

class CTelemetryPacket(ctypes.Structure):
    _fields_ = [
        ("batteryVoltage", ctypes.c_float),
        ("ultrasonicDistance", ctypes.c_float),
        ("motorLeftPwm", ctypes.c_int32),
        ("motorRightPwm", ctypes.c_int32),
        ("lineSensorTriggered", ctypes.c_uint8),
        ("statusFlag", ctypes.c_uint8),
        ("packetsReceived", ctypes.c_uint32)
    ]

class TelemetryModel(QObject):
    dataChanged = pyqtSignal()

    def __init__(self, use_mock=True, host="127.0.0.1", port=8888):
        super().__init__()
        self._use_mock = use_mock
        self._battery = 12.6
        self._distance = 45.0
        self._motor_l = 0
        self._motor_r = 0
        self._line = False
        self._status = "STANDBY"
        self._packets = 0

        self._lib = None
        self._init_cpp_library(host, port)

    def _init_cpp_library(self, host, port):
        lib_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../libtelemetry.so"))
        if os.path.exists(lib_path):
            try:
                self._lib = ctypes.CDLL(lib_path)
                self._lib.Telemetry_Connect.argtypes = [ctypes.c_char_p, ctypes.c_int]
                self._lib.Telemetry_Connect.restype = ctypes.c_bool
                self._lib.Telemetry_Poll.argtypes = [ctypes.POINTER(CTelemetryPacket)]
                self._lib.Telemetry_Poll.restype = ctypes.c_bool
                self._lib.Telemetry_SendCommand.argtypes = [ctypes.c_char_p]
                self._lib.Telemetry_SendCommand.restype = ctypes.c_bool

                if not self._use_mock:
                    self._lib.Telemetry_Connect(host.encode('utf-8'), port)
            except Exception as e:
                print(f"[Model Warning] Falha ao carregar C++ lib: {e}. Usando mock.")
                self._use_mock = True
        else:
            self._use_mock = True

    def update_telemetry(self):
        if self._use_mock:
            # Simulação física e visual de robô em ringue
            self._distance = max(5.0, min(120.0, self._distance + random.uniform(-4.0, 3.5)))
            self._battery = max(10.5, self._battery - 0.001)
            if self._distance < 40.0:
                self._status = "ATACANDO (POTÊNCIA MÁXIMA)"
                self._motor_l = 255
                self._motor_r = 255
            else:
                self._status = "BUSCANDO OPONENTE (50% PWM)"
                self._motor_l = -128
                self._motor_r = 128
            self._line = (random.random() < 0.05)
            self._packets += 1
        elif self._lib:
            packet = CTelemetryPacket()
            if self._lib.Telemetry_Poll(ctypes.byref(packet)):
                self._battery = packet.batteryVoltage
                self._distance = packet.ultrasonicDistance
                self._motor_l = packet.motorLeftPwm
                self._motor_r = packet.motorRightPwm
                self._line = bool(packet.lineSensorTriggered)
                status_map = {0: "PARADO", 1: "BUSCANDO (50% PWM)", 2: "AVANÇO MÁXIMO"}
                self._status = status_map.get(packet.statusFlag, "OPERANDO")
                self._packets = packet.packetsReceived

        self.dataChanged.emit()

    @pyqtProperty(float, notify=dataChanged)
    def batteryVoltage(self): return round(self._battery, 2)

    @pyqtProperty(float, notify=dataChanged)
    def ultrasonicDistance(self): return round(self._distance, 1)

    @pyqtProperty(int, notify=dataChanged)
    def motorLeftPwm(self): return self._motor_l

    @pyqtProperty(int, notify=dataChanged)
    def motorRightPwm(self): return self._motor_r

    @pyqtProperty(bool, notify=dataChanged)
    def lineTriggered(self): return self._line

    @pyqtProperty(str, notify=dataChanged)
    def robotStatus(self): return self._status

    @pyqtProperty(int, notify=dataChanged)
    def packetsCount(self): return self._packets
EOF

# STREAMING_CHUNK:Writing Python Controller
cat << 'EOF' > app/controllers/app_controller.py
from PyQt6.QtCore import QObject, pyqtSlot, pyqtProperty, pyqtSignal, QTimer

class AppController(QObject):
    activeTabChanged = pyqtSignal(int)
    athletesDataChanged = pyqtSignal()

    def __init__(self, model):
        super().__init__()
        self._model = model
        self._active_tab = 0  # 0 = Início (Hub), 1 = Temporada/Estatísticas

        # Timer de alta taxa de atualização para sincronia de telemetria
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._model.update_telemetry)
        self._timer.start(100) # 10Hz

        # Modelo estático/dinâmico de atletas/robôs para a tela de tabela (Image 2)
        self._athletes = [
            {"rank": 1, "nome": "VIDANINHO", "pais": "🇧🇷", "time": "Swindon Town", "gols": 11, "partidas": 6, "avatar": "⚡"},
            {"rank": 2, "nome": "JAMIE WALKER", "pais": "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "time": "Grimsby Town", "gols": 5, "partidas": 6, "avatar": "🎯"},
            {"rank": 3, "nome": "CHARLIE MCNEILL", "pais": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "time": "Crewe Alexandra", "gols": 5, "partidas": 6, "avatar": "🔥"},
            {"rank": 4, "nome": "PAUL GLATZEL", "pais": "🇩🇪", "time": "Swindon Town", "gols": 4, "partidas": 3, "avatar": "⭐"},
            {"rank": 5, "nome": "FLETCHER HOLMAN", "pais": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "time": "Swindon Town", "gols": 4, "partidas": 5, "avatar": "🚀"}
        ]

    @pyqtProperty(int, notify=activeTabChanged)
    def activeTab(self):
        return self._active_tab

    @activeTab.setter
    def activeTab(self, index):
        if self._active_tab != index:
            self._active_tab = index
            self.activeTabChanged.emit(index)

    @pyqtProperty(list, notify=athletesDataChanged)
    def athletesList(self):
        return self._athletes

    @pyqtSlot(int)
    def selectTab(self, index):
        self.activeTab = index

    @pyqtSlot(str)
    def sendRobotCommand(self, cmd):
        print(f"[Controller] Enviando comando: {cmd}")
        # Notifica ponte C++
        if self._model._lib:
            self._model._lib.Telemetry_SendCommand(cmd.encode('utf-8'))
EOF

# STREAMING_CHUNK:Writing QML Top Navigation Bar component
echo "[5/6] Gerando componentes QML modernos estilo EA FC..."
cat << 'EOF' > app/views/qml/components/TopNavBar.qml
import QtQuick 2.15
import QtQuick.Layouts 1.15

Item {
    id: root
    height: 60
    anchors.left: parent.left
    anchors.right: parent.right

    readonly property var tabs: ["Início", "Central", "Notificações", "Craque", "Temporada", "Personalizar"]

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 28
        anchors.rightMargin: 28
        spacing: 16

        // Logo PC estilizado
        Rectangle {
            width: 36
            height: 36
            radius: 18
            color: "#18242b"
            border.color: "#38e07b"
            border.width: 1.5

            Text {
                anchors.centerIn: parent
                text: "PC"
                font.bold: true
                font.pixelSize: 13
                color: "#ffffff"
            }
        }

        // Abas principais do menu estilo EA FC
        Row {
            Layout.fillWidth: true
            spacing: 8

            Repeater {
                model: root.tabs
                delegate: Rectangle {
                    id: tabItem
                    width: tabText.implicitWidth + 28
                    height: 38
                    radius: 6

                    readonly property bool isSelected: (controller.activeTab === index || (index === 4 && controller.activeTab === 1))

                    color: isSelected ? "#3a4750" : (mouseArea.containsMouse ? "#202c34" : "transparent")
                    border.color: isSelected ? "#38e07b" : "transparent"
                    border.width: isSelected ? 1.5 : 0

                    Text {
                        id: tabText
                        anchors.centerIn: parent
                        text: modelData
                        font.pixelSize: 15
                        font.bold: isSelected
                        color: isSelected ? "#ffffff" : "#8e9ea8"
                    }

                    MouseArea {
                        id: mouseArea
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            if (index === 0) controller.selectTab(0)
                            else if (index === 4) controller.selectTab(1)
                            else controller.selectTab(0)
                        }
                    }
                }
            }
        }

        // Ícone de usuário e status online
        Rectangle {
            width: 38
            height: 38
            radius: 8
            color: "#152026"
            border.color: "#283842"

            Text {
                anchors.centerIn: parent
                text: "🍔"
                font.pixelSize: 18
            }
        }
    }
}
EOF

# STREAMING_CHUNK:Writing QML Bottom Bar gamepad hints component
cat << 'EOF' > app/views/qml/components/BottomBar.qml
import QtQuick 2.15
import QtQuick.Layouts 1.15

Item {
    id: root
    height: 48
    anchors.left: parent.left
    anchors.right: parent.right

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 30
        anchors.rightMargin: 30
        spacing: 24

        Row {
            spacing: 8
            Rectangle {
                width: 20; height: 20; radius: 10; color: "#2d3a42"
                Text { anchors.centerIn: parent; text: "B"; color: "#fff"; font.pixelSize: 10; font.bold: true }
            }
            Text { text: "Voltar"; color: "#a5b4bc"; font.pixelSize: 13; anchors.verticalCenter: parent.verticalCenter }
        }

        Row {
            spacing: 8
            Rectangle {
                width: 20; height: 20; radius: 10; color: "#2d3a42"
                Text { anchors.centerIn: parent; text: "X"; color: "#fff"; font.pixelSize: 10; font.bold: true }
            }
            Text { text: "Escolher Opção"; color: "#a5b4bc"; font.pixelSize: 13; anchors.verticalCenter: parent.verticalCenter }
        }

        Row {
            spacing: 8
            Rectangle {
                width: 26; height: 20; radius: 4; color: "#2d3a42"
                Text { anchors.centerIn: parent; text: "LT"; color: "#fff"; font.pixelSize: 9; font.bold: true }
            }
            Text { text: "(Manter) Atalhos"; color: "#a5b4bc"; font.pixelSize: 13; anchors.verticalCenter: parent.verticalCenter }
        }

        Item { Layout.fillWidth: true }

        // Indicador de status de rede Arduino
        Row {
            spacing: 8
            Rectangle {
                width: 10; height: 10; radius: 5
                color: telemetry.packetsCount > 0 ? "#38e07b" : "#e63946"
                anchors.verticalCenter: parent.verticalCenter
            }
            Text { 
                text: "Arduino Link: " + telemetry.packetsCount + " pcts"
                color: "#8e9ea8"
                font.pixelSize: 12
                anchors.verticalCenter: parent.verticalCenter
            }
        }
    }
}
EOF

# STREAMING_CHUNK:Writing QML Home View (Image 1 style)
cat << 'EOF' > app/views/qml/pages/HomeView.qml
import QtQuick 2.15
import QtQuick.Layouts 1.15

Item {
    id: root

    // Moldura curvada futurista estilo EA FC Hub
    Rectangle {
        id: curvedDisplay
        anchors.fill: parent
        anchors.margins: 24
        radius: 16
        clip: true

        gradient: Gradient {
            GradientStop { position: 0.0; color: "#0c1d22" }
            GradientStop { position: 0.5; color: "#112a32" }
            GradientStop { position: 1.0; color: "#081318" }
        }
        border.color: "#1d444e"
        border.width: 1.5

        // Padrão geométrico suave no fundo
        Column {
            anchors.centerIn: parent
            spacing: 18

            Text {
                text: "MINI-SUMÔ FC"
                font.pixelSize: 42
                font.bold: true
                color: "#183e45"
                anchors.horizontalCenter: parent.horizontalCenter
            }

            Text {
                text: "TELEMETRIA EM TEMPO REAL"
                font.pixelSize: 16
                font.letterSpacing: 4
                color: "#38e07b"
                anchors.horizontalCenter: parent.horizontalCenter
            }

            // Cards de Telemetria ao vivo
            Row {
                spacing: 20
                anchors.horizontalCenter: parent.horizontalCenter

                // Card Distância
                Rectangle {
                    width: 190; height: 120; radius: 12
                    color: "#13232a"; border.color: "#284450"
                    Column {
                        anchors.centerIn: parent
                        spacing: 8
                        Text { text: "ULTRASSOM"; color: "#8a9ea8"; font.pixelSize: 11; font.bold: true; anchors.horizontalCenter: parent.horizontalCenter }
                        Text { text: telemetry.ultrasonicDistance + " cm"; color: "#ffffff"; font.pixelSize: 26; font.bold: true; anchors.horizontalCenter: parent.horizontalCenter }
                        Text { text: telemetry.ultrasonicDistance < 40.0 ? "ALERTA: D < 40cm" : "Área Livre"; color: telemetry.ultrasonicDistance < 40.0 ? "#e63946" : "#38e07b"; font.pixelSize: 12; anchors.horizontalCenter: parent.horizontalCenter }
                    }
                }

                // Card Bateria
                Rectangle {
                    width: 190; height: 120; radius: 12
                    color: "#13232a"; border.color: "#284450"
                    Column {
                        anchors.centerIn: parent
                        spacing: 8
                        Text { text: "TENSÃO BATERIA"; color: "#8a9ea8"; font.pixelSize: 11; font.bold: true; anchors.horizontalCenter: parent.horizontalCenter }
                        Text { text: telemetry.batteryVoltage + " V"; color: "#ffffff"; font.pixelSize: 26; font.bold: true; anchors.horizontalCenter: parent.horizontalCenter }
                        Text { text: "LiPo 3S Nominal"; color: "#8a9ea8"; font.pixelSize: 12; anchors.horizontalCenter: parent.horizontalCenter }
                    }
                }

                // Card Motores PWM
                Rectangle {
                    width: 220; height: 120; radius: 12
                    color: "#13232a"; border.color: "#284450"
                    Column {
                        anchors.centerIn: parent
                        spacing: 8
                        Text { text: "PWM MOTORES (ESQ / DIR)"; color: "#8a9ea8"; font.pixelSize: 11; font.bold: true; anchors.horizontalCenter: parent.horizontalCenter }
                        Text { text: telemetry.motorLeftPwm + " | " + telemetry.motorRightPwm; color: "#38e07b"; font.pixelSize: 24; font.bold: true; anchors.horizontalCenter: parent.horizontalCenter }
                        Text { text: telemetry.robotStatus; color: "#ffffff"; font.pixelSize: 11; anchors.horizontalCenter: parent.horizontalCenter }
                    }
                }
            }
        }
    }
}
EOF

# STREAMING_CHUNK:Writing QML Stats View (Image 2 style)
cat << 'EOF' > app/views/qml/pages/StatsView.qml
import QtQuick 2.15
import QtQuick.Layouts 1.15

Item {
    id: root

    Rectangle {
        anchors.fill: parent
        anchors.margins: 24
        radius: 16
        color: "#101d24"
        border.color: "#243a46"

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 20
            spacing: 12

            // Subcabeçalho estilo EFL LEAGUE TWO / Temporada
            RowLayout {
                Layout.fillWidth: true
                spacing: 12

                Rectangle {
                    width: 32; height: 32; radius: 6; color: "#182a32"
                    Text { anchors.centerIn: parent; text: "🏆"; font.pixelSize: 16 }
                }

                Text {
                    text: "EFL LEAGUE TWO  •  ESTATÍSTICAS DE ATLETAS (2026/27)"
                    color: "#d0dce4"
                    font.pixelSize: 16
                    font.bold: true
                }

                Item { Layout.fillWidth: true }

                Text {
                    text: "Artilheiros"
                    color: "#38e07b"
                    font.bold: true
                    font.pixelSize: 14
                }
            }

            // Tabela Header
            Rectangle {
                Layout.fillWidth: true
                height: 32
                color: "#15242d"
                radius: 4

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 16
                    anchors.rightMargin: 16

                    Text { text: "Atleta"; Layout.preferredWidth: 260; color: "#748894"; font.pixelSize: 12; font.bold: true }
                    Text { text: "Time atual"; Layout.fillWidth: true; color: "#748894"; font.pixelSize: 12; font.bold: true }
                    Text { text: "Gols"; Layout.preferredWidth: 80; color: "#ffffff"; font.pixelSize: 12; font.bold: true }
                    Text { text: "Partidas"; Layout.preferredWidth: 80; color: "#748894"; font.pixelSize: 12; font.bold: true }
                }
            }

            // Lista de Jogadores/Robôs
            ListView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                model: controller.athletesList
                spacing: 6

                delegate: Rectangle {
                    width: ListView.view.width
                    height: 54
                    radius: 6
                    color: index % 2 === 0 ? "#122028" : "#14242e"
                    border.color: mouseArea.containsMouse ? "#38e07b" : "transparent"
                    border.width: 1

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 16
                        anchors.rightMargin: 16
                        spacing: 12

                        // Avatar
                        Text { text: modelData.avatar; font.pixelSize: 22 }

                        // Nome + Bandeira
                        Row {
                            Layout.preferredWidth: 220
                            spacing: 8
                            Text { text: modelData.pais; font.pixelSize: 14; anchors.verticalCenter: parent.verticalCenter }
                            Text { 
                                text: modelData.nome
                                color: "#ffffff"
                                font.bold: true
                                font.pixelSize: 13
                                anchors.verticalCenter: parent.verticalCenter 
                            }
                        }

                        // Time
                        Text {
                            text: modelData.time
                            color: "#9db0bc"
                            font.pixelSize: 13
                            Layout.fillWidth: true
                        }

                        // Gols
                        Text {
                            text: modelData.gols.toString()
                            color: "#ffffff"
                            font.bold: true
                            font.pixelSize: 15
                            Layout.preferredWidth: 80
                        }

                        // Partidas
                        Text {
                            text: modelData.partidas.toString()
                            color: "#9db0bc"
                            font.pixelSize: 14
                            Layout.preferredWidth: 80
                        }
                    }

                    MouseArea {
                        id: mouseArea
                        anchors.fill: parent
                        hoverEnabled: true
                    }
                }
            }
        }
    }
}
EOF

# STREAMING_CHUNK:Writing Main QML shell
cat << 'EOF' > app/views/qml/main.qml
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import "components"
import "pages"

ApplicationWindow {
    id: window
    width: 1280
    height: 720
    minimumWidth: 960
    minimumHeight: 600
    visible: true
    title: "FC Mini-Sumô & Telemetria Hub"
    color: "#081014"

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // Barra superior estilo EA FC (Tabs)
        TopNavBar {
            id: navBar
            Layout.fillWidth: true
        }

        // Stack de Conteúdo alternável entre Início e Estatísticas
        StackLayout {
            id: stackLayout
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: controller.activeTab

            HomeView { id: homeTab }
            StatsView { id: statsTab }
        }

        // Barra inferior com atalhos de controle
        BottomBar {
            id: footerBar
            Layout.fillWidth: true
        }
    }
}
EOF

# STREAMING_CHUNK:Writing Python Application entry point and CLI
echo "[6/6] Criando arquivo principal e inicializador CLI (app/main.py)..."
cat << 'EOF' > app/main.py
import sys
import argparse
import os
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtQml import QQmlApplicationEngine
from app.models.telemetry_model import TelemetryModel
from app.controllers.app_controller import AppController

def main():
    parser = argparse.ArgumentParser(description="FC Robô Dashboard - Telemetria & Estatísticas")
    parser.add_argument("--mock", action="store_true", help="Executar com simulação (sem necessidade de Arduino conectado)")
    parser.add_argument("--host", default="192.168.4.1", help="Endereço IP do Arduino/ESP32 (Padrão: 192.168.4.1)")
    parser.add_argument("--port", type=int, default=8888, help="Porta UDP/TCP de telemetria (Padrão: 8888)")
    args = parser.parse_args()

    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()

    # Instanciação da arquitetura MVC
    model = TelemetryModel(use_mock=args.mock, host=args.host, port=args.port)
    controller = AppController(model)

    # Injeção de dependências no contexto QML
    engine.rootContext().setContextProperty("telemetry", model)
    engine.rootContext().setContextProperty("controller", controller)

    qml_file = os.path.join(os.path.dirname(__file__), "views/qml/main.qml")
    engine.load(qml_file)

    if not engine.rootObjects():
        print("[ERRO FATAL] Falha ao carregar a interface QML.")
        sys.exit(-1)

    print(f"[OK] Aplicação iniciada com sucesso. Modo: {'Simulação Mock' if args.mock else f'Rede ({args.host}:{args.port})'}")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
EOF

# STREAMING_CHUNK:Compiling the C++ shared library
echo ""
echo "Compilando biblioteca C++ nativa (libtelemetry.so)..."
make -C cpp

# STREAMING_CHUNK:Creating executable run script and Python virtual environment instructions
cat << 'EOF' > run.sh
#!/usr/bin/env bash
# Script de execução rápida
if [ ! -d "venv" ]; then
    echo "Criando ambiente virtual Python..."
    python3 -m venv venv
    ./venv/bin/pip install --upgrade pip
    ./venv/bin/pip install PyQt6
fi

source venv/bin/activate
export PYTHONPATH=.
python3 -m app.main "$@"
EOF

chmod +x run.sh

echo ""
echo "=========================================================="
echo " Projeto configurado com sucesso na pasta '${PROJECT_NAME}'!"
echo "=========================================================="
echo "Para executar o projeto:"
echo "  1. Entre na pasta:   cd ${PROJECT_NAME}"
echo "  2. Modo Simulação:   ./run.sh --mock"
echo "  3. Modo Arduino/IP:  ./run.sh --host 192.168.4.1 --port 8888"
echo "=========================================================="