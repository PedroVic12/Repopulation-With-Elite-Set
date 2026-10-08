#!/usr/bin/env bash
set -e

BASE_DIR="serene_hybrid_core"

function banner() {
    echo "========================================================="
    echo "       SERENE HYBRID SYSTEM - CLI DE ARQUITETURA         "
    echo "  C++ (QML) | Python (UV) | Julia | Lua (Scripts/Data)  "
    echo "========================================================="
}

function init_project_structure() {
    echo "[+] Inicializando arquitetura de pastas MVC..."
    mkdir -p ${BASE_DIR}/{src/{views,controllers,models,engine,scripts,analytics},data,config,logs}
    
    # Arquivo de configuração base
    cat << 'EOF' > ${BASE_DIR}/config/system.txt
APP_NAME=SereneHybridCore
VERSION=1.0.0
STORAGE_MODE=LOCAL_AND_CACHE
LOG_LEVEL=DEBUG
SAMPLE_RATE=44100
EOF

    # Arquivo de metadados
    cat << 'EOF' > ${BASE_DIR}/data/app_state.json
{
  "user": "Pedro",
  "active_screens": [],
  "metrics": {
    "total_records": 0,
    "current_streak": 1
  }
}
EOF

    # Engine nativa C++ que hospeda o QML
    cat << 'EOF' > ${BASE_DIR}/src/engine/app.cpp
#include <QGuiApplication>
#include <QQmlApplicationEngine>
#include <QQmlContext>
#include <QObject>
#include <QDebug>

class SystemBridge : public QObject {
    Q_OBJECT
    Q_PROPERTY(QString currentUser READ currentUser CONSTANT)

public:
    explicit SystemBridge(QObject *parent = nullptr) : QObject(parent) {}
    QString currentUser() const { return "Pedro"; }

    Q_INVOKABLE void logAction(const QString &actionName) {
        qDebug() << "[C++ Native Core] Ação registrada na tela:" << actionName;
    }
};

int main(int argc, char *argv[]) {
    QGuiApplication app(argc, argv);
    QQmlApplicationEngine engine;

    SystemBridge bridge;
    engine.rootContext()->setContextProperty("Bridge", &bridge);

    engine.load(QUrl::fromLocalFile("src/views/MainApp.qml"));
    if (engine.rootObjects().isEmpty())
        return -1;

    return app.exec();
}
#include "app.moc"
EOF

    # Shell principal QML
    cat << 'EOF' > ${BASE_DIR}/src/views/MainApp.qml
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
EOF

    # CMakeLists.txt para compilação Qt6 / C++
    cat << 'EOF' > ${BASE_DIR}/CMakeLists.txt
cmake_minimum_required(VERSION 3.16)
project(SereneHybridCore LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)
set(CMAKE_AUTOUIC ON)

find_package(Qt6 REQUIRED COMPONENTS Gui Qml Quick)

add_executable(SereneHybridCore
    src/engine/app.cpp
)

target_link_libraries(SereneHybridCore PRIVATE Qt6::Gui Qt6::Qml Qt6::Quick)
EOF

    # Script auxiliar de Build
    cat << 'EOF' > ${BASE_DIR}/build.sh
#!/usr/bin/env bash
set -e
echo "[+] Compilando Serene Hybrid Core..."
mkdir -p build && cd build
cmake ..
make -j$(nproc)
echo "[✓] Compilação concluída com sucesso! Para rodar: ./build/SereneHybridCore"
EOF
    chmod +x ${BASE_DIR}/build.sh

    echo "[✓] Estrutura base criada com sucesso em: ./${BASE_DIR}"
}

function generate_screen_scaffold() {
    local screen_name=$1
    if [ -z "$screen_name" ]; then
        echo "[-] Erro: Nome da tela não fornecido."
        return
    fi

    echo "[+] Gerando scaffold completo para a tela: ${screen_name}"
    
    # 1. View em QML
    cat << EOF > ${BASE_DIR}/src/views/${screen_name}View.qml
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Item {
    id: ${screen_name,,}Root
    anchors.fill: parent

    Rectangle {
        anchors.fill: parent
        color: "#0f141c"

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 20
            spacing: 15

            Text {
                text: "${screen_name} Screen"
                color: "#ffffff"
                font.pointSize: 18
                font.bold: true
            }

            Button {
                text: "Executar Ação da Tela"
                onClicked: {
                    Bridge.logAction("${screen_name}View::execute");
                }
            }

            Item { Layout.fillHeight: true }
        }
    }
}
EOF

    # 2. Script de Regra em Lua (Data Driven & Hashing)
    cat << EOF > ${BASE_DIR}/src/scripts/${screen_name,,}_rules.lua
-- Regras de Domínio e Hash para ${screen_name}
local Rules = {}
Rules.__index = Rules

function Rules:new()
    return setmetatable({ screen = "${screen_name}" }, Rules)
end

function Rules:process_event(param)
    local raw = string.format("%s_%s_%d", self.screen, param, os.time())
    print("[Lua Rule Engine] Evento processado para: " .. raw)
    return raw
end

return Rules
EOF

    # 3. Módulo de Análise em Python / UV
    cat << EOF > ${BASE_DIR}/src/analytics/${screen_name,,}_processor.py
"""Processador de dados e rotinas para ${screen_name}."""
import sys
import json

def run_pipeline(payload: dict):
    print(f"[Python Pipeline] Processando dados para ${screen_name}: {payload}")

if __name__ == "__main__":
    sample_data = {"screen": "${screen_name}", "status": "active"}
    run_pipeline(sample_data)
EOF

    echo "[✓] Módulos gerados: View (QML), Regras (Lua) e Processor (Python) para ${screen_name}."
}

# Menu Interativo da CLI
banner
echo "Escolha uma operação:"
echo "1) Criar infraestrutura inicial do projeto"
echo "2) Gerar tela: Home (Plano Diário)"
echo "3) Gerar tela: MoodVoice (Registro por Voz)"
echo "4) Gerar tela: SentimentReview (Tags & Transcrição)"
echo "5) Gerar tela: JournalTimeline (Diário)"
echo "6) Gerar tela: PersonalityMatrix (Testes & Arquétipos)"
echo "7) Gerar tela: MoodHeatmap (Calendário de Humor)"
echo "8) Gerar tela: LearningTrack (Cursos & Aulas)"
echo "9) Gerar tela: VbtSportMetrics (Performance e Curvas de Treino)"
echo "10) Gerar tela: SoccerEngine (Visualizador 3D & Simulação)"
echo "0) Sair"
read -p "Opção > " OPTION

case $OPTION in
    1)
        init_project_structure
        ;;
    2)
        generate_screen_scaffold "Home"
        ;;
    3)
        generate_screen_scaffold "MoodVoice"
        ;;
    4)
        generate_screen_scaffold "SentimentReview"
        ;;
    5)
        generate_screen_scaffold "JournalTimeline"
        ;;
    6)
        generate_screen_scaffold "PersonalityMatrix"
        ;;
    7)
        generate_screen_scaffold "MoodHeatmap"
        ;;
    8)
        generate_screen_scaffold "LearningTrack"
        ;;
    9)
        generate_screen_scaffold "VbtSportMetrics"
        ;;
    10)
        generate_screen_scaffold "SoccerEngine"
        ;;
    0)
        echo "Finalizado."
        exit 0
        ;;
    *)
        echo "Opção inválida."
        exit 1
        ;;
esac