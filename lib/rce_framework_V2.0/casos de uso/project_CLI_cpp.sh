#!/usr/bin/env bash
set -e

BASE_DIR="serene_hybrid_core"
APP_TITLE="Serene & Performance Suite"

function banner() {
    echo "========================================================="
    echo "       SERENE HYBRID SYSTEM - CLI DE ARQUITETURA         "
    echo "  C++ (QML) | Python (UV) | Julia | Lua (Scripts/Data)  "
    echo "========================================================="
    echo " 🎯 Projeto Ativo Atual: ./${BASE_DIR}"
    echo " 📌 Título da Aplicação:  ${APP_TITLE}"
    echo "========================================================="
}

function print_tree() {
    local dir=$1
    local prefix=$2

    if [ ! -d "$dir" ]; then
        return
    fi

    shopt -s nullglob
    local entries=("$dir"/*)
    shopt -u nullglob
    local count=${#entries[@]}
    local i=0

    for entry in "${entries[@]}"; do
        i=$((i + 1))
        local name=$(basename "$entry")
        local pointer="├── "
        if [ $i -eq $count ]; then
            pointer="└── "
        fi

        if [ "$name" = "build" ]; then
            echo -e "${prefix}${pointer}📁 \e[1;30mbuild/\e[0m \e[36m(Objetos de Compilação CMake/C++)\e[0m"
            continue
        fi

        if [ -d "$entry" ]; then
            echo -e "${prefix}${pointer}📁 \e[1;34m${name}\e[0m/"
            local new_prefix="${prefix}│   "
            if [ $i -eq $count ]; then
                new_prefix="${prefix}    "
            fi
            print_tree "$entry" "$new_prefix"
        else
            echo -e "${prefix}${pointer}📄 ${name}"
        fi
    done
}

function show_project_tree() {
    if [ ! -d "${BASE_DIR}" ]; then
        echo "[-] Projeto ./${BASE_DIR} ainda não foi inicializado."
        return
    fi

    echo ""
    echo "========================================================="
    echo " 🌳 ESTRUTURA E TELAS DO PROJETO: ./${BASE_DIR}"
    echo "========================================================="
    echo -e "📂 \e[1;32m${BASE_DIR}\e[0m/"
    print_tree "${BASE_DIR}" "   "
    echo "========================================================="
    echo ""
}

function scan_projects() {
    PROJECTS=()
    shopt -s nullglob
    for d in */; do
        if [ -d "$d" ] && [ -f "${d}CMakeLists.txt" ]; then
            d_clean="${d%/}"
            PROJECTS+=("$d_clean")
        fi
    done
    shopt -u nullglob
}

function select_project_flow() {
    scan_projects
    echo ""
    echo "========================================================="
    echo " 🔄 SELECIONAR PROJETO ATIVO"
    echo "========================================================="
    if [ ${#PROJECTS[@]} -eq 0 ]; then
        echo "[-] Nenhum projeto encontrado no diretório atual."
        return
    fi

    echo "Projetos disponíveis:"
    local idx=1
    for p in "${PROJECTS[@]}"; do
        echo " ${idx}) ./${p}"
        idx=$((idx + 1))
    done

    read -p "Escolha o número do projeto > " P_NUM
    if [[ "$P_NUM" =~ ^[0-9]+$ ]] && [ "$P_NUM" -ge 1 ] && [ "$P_NUM" -le "${#PROJECTS[@]}" ]; then
        BASE_DIR="${PROJECTS[$((P_NUM - 1))]}"
        if [ -f "${BASE_DIR}/config/system.txt" ]; then
            TITLE_LINE=$(grep "^TITLE=" "${BASE_DIR}/config/system.txt" | cut -d'=' -f2 || true)
            if [ -n "$TITLE_LINE" ]; then
                APP_TITLE="$TITLE_LINE"
            fi
        fi
        echo "[✓] Projeto ativo alterado para: ./${BASE_DIR}"
    else
        echo "[-] Seleção inválida."
    fi
}

function init_project_structure() {
    local custom_dir=$1
    local custom_title=$2

    if [ -n "$custom_dir" ]; then
        BASE_DIR="$custom_dir"
    fi
    if [ -n "$custom_title" ]; then
        APP_TITLE="$custom_title"
    fi

    echo "[+] Inicializando arquitetura de pastas MVC para: ./${BASE_DIR}..."
    mkdir -p ${BASE_DIR}/{src/{views,controllers,models,engine,scripts,analytics},data,config,logs}
    
    # Arquivo de configuração base
    cat << EOF > ${BASE_DIR}/config/system.txt
APP_NAME=${BASE_DIR}
TITLE=${APP_TITLE}
VERSION=1.0.0
STORAGE_MODE=LOCAL_AND_CACHE
LOG_LEVEL=DEBUG
SAMPLE_RATE=44100
EOF

    # Arquivo de metadados
    cat << EOF > ${BASE_DIR}/data/app_state.json
{
  "user": "Pedro",
  "project_name": "${BASE_DIR}",
  "app_title": "${APP_TITLE}",
  "active_screens": ["Home"],
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
#include <QDir>
#include <QFileInfo>

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

    QString appDir = QCoreApplication::applicationDirPath();
    QString qmlPath = appDir + "/../src/views/MainApp.qml";
    if (!QFileInfo::exists(qmlPath)) {
        qmlPath = appDir + "/src/views/MainApp.qml";
    }
    if (!QFileInfo::exists(qmlPath)) {
        qmlPath = "src/views/MainApp.qml";
    }

    qDebug() << "[C++ Native Core] Carregando QML de:" << qmlPath;
    engine.load(QUrl::fromLocalFile(qmlPath));
    if (engine.rootObjects().isEmpty()) {
        qCritical() << "[Erro C++] Falha ao carregar componente QML!";
        return -1;
    }

    return app.exec();
}
#include "app.moc"
EOF

    # View Inicial padrão
    cat << 'EOF' > ${BASE_DIR}/src/views/HomeView.qml
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
EOF

    # Shell principal QML com Drawer e StackView Dinâmico
    cat << EOF > ${BASE_DIR}/src/views/MainApp.qml
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

ApplicationWindow {
    id: window
    visible: true
    width: 440
    height: 860
    title: "${APP_TITLE}"
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
                text: "${APP_TITLE}"
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
EOF

    # CMakeLists.txt para compilação Qt6 / C++
    cat << EOF > ${BASE_DIR}/CMakeLists.txt
cmake_minimum_required(VERSION 3.16)
project(${BASE_DIR} LANGUAGES CXX)

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

    # Script auxiliar de Build & Run
    cat << EOF > ${BASE_DIR}/build.sh
#!/usr/bin/env bash
set -e

SCRIPT_DIR="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")" && pwd)"
cd "\$SCRIPT_DIR"

echo "========================================================="
echo "   COMPILANDO E EXECUTANDO - ${APP_TITLE}    "
echo "========================================================="

mkdir -p build && cd build
cmake ..
make -j\$(nproc)

echo "[✓] Compilação concluída com sucesso! Iniciando aplicação..."
echo "---------------------------------------------------------"
./SereneHybridCore
EOF
    chmod +x ${BASE_DIR}/build.sh

    echo "[✓] Estrutura base criada com sucesso em: ./${BASE_DIR}"
}

function register_screen_in_main_qml() {
    local screen_name=$1
    local qml_file="${BASE_DIR}/src/views/MainApp.qml"

    if [ -f "$qml_file" ]; then
        if grep -q "${screen_name}View.qml" "$qml_file"; then
            echo "[!] Tela ${screen_name} já cadastrada no Menu principal."
        else
            echo "[+] Registrando ${screen_name} no menu principal do QML..."
            sed -i "/id: screenModel/a \        ListElement { title: \"${screen_name}\"; componentUrl: \"${screen_name}View.qml\" }" "$qml_file"
            echo "[✓] ${screen_name} cadastrada com sucesso no Drawer!"
        fi
    fi
}

function generate_screen_scaffold() {
    local screen_name=$1
    if [ -z "$screen_name" ]; then
        echo "[-] Erro: Nome da tela não fornecido."
        return
    fi

    if [ ! -d "${BASE_DIR}" ]; then
        echo "[!] Diretório ./${BASE_DIR} não encontrado. Criando estrutura inicial..."
        init_project_structure
    fi

    echo "[+] Gerando scaffold completo para a tela: ${screen_name} no projeto ./${BASE_DIR}"
    
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
                text: "${screen_name} Module"
                color: "#00e5ff"
                font.pointSize: 20
                font.bold: true
            }

            Text {
                text: "Tela gerada via CLI para ${APP_TITLE}"
                color: "#a0aec0"
                font.pointSize: 12
            }

            Button {
                text: "Executar Ação Native (C++)"
                onClicked: {
                    Bridge.logAction("${screen_name}View::execute");
                }
            }

            Item { Layout.fillHeight: true }
        }
    }
}
EOF

    # 2. Script de Regra em Lua
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

    # 3. Módulo de Análise em Python
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

    # 4. Registrar a tela no QML principal
    register_screen_in_main_qml "${screen_name}"

    echo "[✓] Módulos gerados e integrados: View (QML), Regras (Lua) e Processor (Python) para ${screen_name}."
}

function create_new_project_flow() {
    echo ""
    read -p "Digite o nome da pasta do NOVO projeto (ex: vbt_sport_app): " NEW_DIR
    read -p "Digite o TÍTULO central do aplicativo (ex: VBT Sport Metrics): " NEW_TITLE

    if [ -z "$NEW_DIR" ]; then
        NEW_DIR="meu_novo_projeto_qt6"
    fi
    if [ -z "$NEW_TITLE" ]; then
        NEW_TITLE="Meu Novo App Hybrid Core"
    fi

    BASE_DIR="$NEW_DIR"
    APP_TITLE="$NEW_TITLE"

    init_project_structure "$NEW_DIR" "$NEW_TITLE"
    echo "[✓] Projeto '${NEW_DIR}' inicializado com o título '${NEW_TITLE}'!"
}

function build_and_run_active_project() {
    if [ ! -d "${BASE_DIR}" ]; then
        echo "[-] O projeto ./${BASE_DIR} ainda não foi criado."
        return
    fi

    echo ""
    echo "========================================================="
    echo " 🚀 COMPILANDO E EXECUTANDO PROJETO ATIVO: ./${BASE_DIR}"
    echo "========================================================="
    (cd "${BASE_DIR}" && ./build.sh)
}

# Menu Interativo da CLI (Loop)
while true; do
    banner
    echo " OPERAÇÕES DE PROJETO:"
    echo " 1) 🏗️  Inicializar/Reconstruir projeto ativo (./${BASE_DIR})"
    echo " 2) ➕ Criar um NOVO projeto separado"
    echo " 3) 🔄 Alternar Projeto Ativo (Escolher entre os existentes)"
    echo " 4) 🌳 Ver Árvore de Arquivos & Telas do Projeto (Tree View)"
    echo " 5) 🚀 COMPILAR E RODAR o projeto ativo agora"
    echo "--------------------------------------------------------"
    echo " ADICIONAR TELAS AO PROJETO ATIVO (./${BASE_DIR}):"
    echo " 6) MoodVoice (Registro por Voz)"
    echo " 7) SentimentReview (Tags & Transcrição)"
    echo " 8) JournalTimeline (Diário)"
    echo " 9) PersonalityMatrix (Testes & Arquétipos)"
    echo " 10) MoodHeatmap (Calendário de Humor)"
    echo " 11) LearningTrack (Cursos & Aulas)"
    echo " 12) VbtSportMetrics (Performance e Curvas de Treino)"
    echo " 13) SoccerEngine (Visualizador 3D & Simulação)"
    echo " 14) ✨ Gerar Tela Customizada (Digitar o nome)"
    echo " 0) 🚪 Sair"
    echo "--------------------------------------------------------"
    read -p "Opção > " OPTION

    case $OPTION in
        1)
            init_project_structure
            ;;
        2)
            create_new_project_flow
            ;;
        3)
            select_project_flow
            ;;
        4)
            show_project_tree
            ;;
        5)
            build_and_run_active_project
            ;;
        6)
            generate_screen_scaffold "MoodVoice"
            ;;
        7)
            generate_screen_scaffold "SentimentReview"
            ;;
        8)
            generate_screen_scaffold "JournalTimeline"
            ;;
        9)
            generate_screen_scaffold "PersonalityMatrix"
            ;;
        10)
            generate_screen_scaffold "MoodHeatmap"
            ;;
        11)
            generate_screen_scaffold "LearningTrack"
            ;;
        12)
            generate_screen_scaffold "VbtSportMetrics"
            ;;
        13)
            generate_screen_scaffold "SoccerEngine"
            ;;
        14)
            read -p "Digite o nome da nova tela (ex: AnalyticsDashboard): " CUSTOM_SCREEN
            if [ -n "$CUSTOM_SCREEN" ]; then
                generate_screen_scaffold "$CUSTOM_SCREEN"
            fi
            ;;
        0)
            echo "Finalizado."
            exit 0
            ;;
        *)
            echo "Opção inválida."
            ;;
    esac
    echo ""
    read -p "Pressione [ENTER] para continuar..." dummy
    echo ""
done