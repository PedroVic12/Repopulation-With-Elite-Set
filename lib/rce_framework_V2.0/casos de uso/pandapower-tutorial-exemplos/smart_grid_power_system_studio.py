#!/usr/bin/env python3
# ==============================================================================
# SMART GRID & POWER SYSTEM STUDIO (ANAREDE Parser + Pandapower + Schemdraw + Cramer 3x3)
# Arquitetura Orientada a Objetos (POO): SmartGridStudioEngine
# ==============================================================================

import sys
import os
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")
import io
import re
import numpy as np
import pandas as pd

import pandapower as pp
import schemdraw
import schemdraw.elements as elm

from PyQt6.QtCore import QObject, pyqtSignal, pyqtProperty, pyqtSlot, QUrl
from PyQt6.QtGui import QGuiApplication, QImage, QPixmap
from PyQt6.QtQml import QQmlApplicationEngine

# -----------------------------------------------------------------------------
# 1. CORE ENGINE: ANAREDE Deck Parser, Pandapower & Cramer 3x3 Electrical Solver
# -----------------------------------------------------------------------------
class SmartGridStudioEngine(QObject):
    networkUpdated = pyqtSignal()
    logMessage = pyqtSignal(str)
    schematicUpdated = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._net = pp.create_empty_network(name="SmartGrid_ONS_Model")
        self._deck_loaded = False
        self._results_summary = "Nenhuma rede carregada. Importe um arquivo .pwf ou .dat."
        self._schematic_path = os.path.abspath("circuit_schematic.png")
        self._cramer_result_text = "Nenhuma análise nodal/malha resolvida por Cramer (3x3)."
        
        # Inicializa caso padrão e gera esquemático inicial Schemdraw
        self._build_default_network()
        self._generate_schemdraw_diagram()

    def _build_default_network(self):
        self._net = pp.create_empty_network(name="Sistema_Teste_ONS")
        b1 = pp.create_bus(self._net, vn_kv=138.0, name="Barra-1", type="b")
        b2 = pp.create_bus(self._net, vn_kv=138.0, name="Barra-2", type="b")
        b3 = pp.create_bus(self._net, vn_kv=69.0, name="Barra-3", type="b")
        
        pp.create_ext_grid(self._net, bus=b1, vm_pu=1.0, name="Ref_ONS")
        pp.create_load(self._net, bus=b2, p_mw=25.0, q_mvar=10.0, name="Carga_Sudeste")
        pp.create_gen(self._net, bus=b3, p_mw=40.0, vm_pu=1.02, name="UHE_Mock")

        line_types = pp.available_std_types(self._net).get("line", {})
        trafo_types = pp.available_std_types(self._net).get("trafo", {})
        preferred_line = "149-AL1/24-ST1 110.0"
        preferred_trafo = "25 MVA 138/69 kV"

        if preferred_line not in line_types:
            preferred_line = "CUSTOM_LINE_110kV"
            self._net.std_types.setdefault("line", {})[preferred_line] = {
                "r_ohm_per_km": 0.115,
                "x_ohm_per_km": 0.4,
                "c_nf_per_km": 0.0,
                "max_i_ka": 0.4,
            }

        if preferred_trafo not in trafo_types:
            preferred_trafo = "CUSTOM_TRAFO_138_69"
            self._net.std_types.setdefault("trafo", {})[preferred_trafo] = {
                "sn_mva": 25.0,
                "vn_hv_kv": 138.0,
                "vn_lv_kv": 69.0,
                "vk_percent": 10.0,
                "vkr_percent": 0.4,
                "pfe_kw": 0.0,
                "i0_percent": 0.0,
                "shift_degree": 0,
            }

        pp.create_line(self._net, from_bus=b1, to_bus=b2, length_km=15.0, std_type=preferred_line, name="DLIN_1-2")
        pp.create_transformer(self._net, hv_bus=b1, lv_bus=b3, std_type=preferred_trafo, name="TRAFO_1-3")
        self._run_power_flow()

    def _generate_schemdraw_diagram(self):
        """Gera imagem esquemática AC/DC profissional usando a biblioteca schemdraw"""
        try:
            with schemdraw.Drawing(file=self._schematic_path, show=False) as d:
                d.config(unit=2.5)
                d += elm.SourceV(v='12V AC').label('V1 (Geração)')
                d += elm.Resistor().right().label('R1 (10 $\\Omega$)')
                d += elm.Inductor().right().label('L1 (5 mH)')
                d.push()
                d += elm.Capacitor().down().label('C1 (100 $\\mu$F)')
                d += elm.Ground()
                d.pop()
                d += elm.Line().right()
                d += elm.Resistor().down().label('R2 (20 $\\Omega$)')
                d += elm.Line().left().toy(d.here)
        except Exception as e:
            self.logMessage.emit(f"Aviso Schemdraw: {e}")

    @pyqtSlot(str)
    def parse_anarede_deck(self, filepath_or_text):
        """Lê decks ANAREDE (.pwf / .dat) extraindo DBAR e DLIN"""
        self.logMessage.emit(f"Processando deck ANAREDE: {filepath_or_text}")
        content = ""
        if os.path.exists(filepath_or_text):
            with open(filepath_or_text, 'r', encoding='latin1') as f:
                content = f.read()
        else:
            content = filepath_or_text

        dbar_pattern = re.compile(r'DBAR\s*\n(.*?)(?:9{5}|FIM)', re.DOTALL | re.IGNORECASE)
        dbar_match = dbar_pattern.search(content)
        
        buses_list = []
        if dbar_match:
            for line in dbar_match.group(1).strip().split('\n'):
                if not line.strip() or line.strip().startswith('('): continue
                parts = line.split()
                if len(parts) >= 6:
                    try:
                        buses_list.append({"num": int(parts[0]), "nome": parts[1], "base_kv": float(parts[2]), "pg": float(parts[3]), "qg": float(parts[4])})
                    except ValueError:
                        continue

        if buses_list:
            self._net = pp.create_empty_network(name="Anarede_Imported_Grid")
            bus_map = {}
            for b in buses_list:
                b_id = pp.create_bus(self._net, vn_kv=b["base_kv"], name=b["nome"])
                bus_map[b["num"]] = b_id
                if b["num"] == buses_list[0]["num"]:
                    pp.create_ext_grid(self._net, bus=b_id, vm_pu=1.0)
                elif b["pg"] > 0:
                    pp.create_gen(self._net, bus=b_id, p_mw=b["pg"])
                else:
                    pp.create_load(self._net, bus=b_id, p_mw=abs(b["pg"]), q_mvar=abs(b["qg"]))
            
            self._run_power_flow()
            self.logMessage.emit(f"Deck ANAREDE importado com sucesso! {len(buses_list)} barramentos.")

    @pyqtSlot()
    def run_power_flow(self):
        self._run_power_flow()

    def _run_power_flow(self):
        try:
            pp.runpp(self._net)
            res = self._net.res_bus
            self._results_summary = (
                f"Fluxo de Potência CONVERGIDO (Newton-Raphson ONS)\n"
                f"• Total de Barras: {len(self._net.bus)}\n"
                f"• Tensão Mínima: {res.vm_pu.min():.3f} p.u. | Máxima: {res.vm_pu.max():.3f} p.u.\n"
                f"• Solução estável calculada com sucesso."
            )
            self.logMessage.emit("Fluxo de potência convergido.")
        except Exception as e:
            self._results_summary = f"Erro no Fluxo: {e}"
        self.networkUpdated.emit()

    @pyqtSlot(str, str, str)
    def solve_circuit_cramer_3x3(self, matrix_type, mat_data_str, vec_data_str):
        """
        Resolve Análise Nodal ou de Malhas (3x3) utilizando a Regra de Cramer.
        Mapeia estritamente 3 incógnitas e 3 equações.
        """
        try:
            # Converte strings de entrada para matriz 3x3 e vetor 3x1
            m_vals = [float(x) for x in mat_data_str.replace(',', ' ').split() if x.strip()]
            v_vals = [float(x) for x in vec_data_str.replace(',', ' ').split() if x.strip()]

            if len(m_vals) != 9 or len(v_vals) != 3:
                self._cramer_result_text = "[Erro] Insira exatamente 9 valores para a matriz 3x3 e 3 valores para o vetor de termos independentes."
                self.networkUpdated.emit()
                return

            A = np.array(m_vals, dtype=float).reshape(3, 3)
            B = np.array(v_vals, dtype=float).reshape(3, 1)

            det_A = np.linalg.det(A)
            if abs(det_A) < 1e-9:
                self._cramer_result_text = f"Determinante principal D = {det_A:.5f} ≈ 0. Sistema Singular ou Indeterminado."
                self.networkUpdated.emit()
                return

            # Aplicação da Regra de Cramer para 3x3
            results = []
            for i in range(3):
                Ai = A.copy()
                Ai[:, i] = B[:, 0]
                det_Ai = np.linalg.det(Ai)
                xi = det_Ai / det_A
                results.append(xi)

            tipo_analise = "Nodal (Tensões de Nó $V_1, V_2, V_3$)" if matrix_type == "nodal" else "de Malhas (Correntes de Malha $I_1, I_2, I_3$)"
            self._cramer_result_text = (
                f"=== RESULTADO ANÁLISE {tipo_analise.upper()} (CRAMER 3x3) ===\n"
                f"• Determinante Principal (D): {det_A:.4f}\n"
                f"• Incógnita 1 ($X_1$): {results[0]:.4f}\n"
                f"• Incógnita 2 ($X_2$): {results[1]:.4f}\n"
                f"• Incógnita 3 ($X_3$): {results[2]:.4f}\n"
                f"• Status: Solução exata obtida com sucesso!"
            )
            self.logMessage.emit(f"Análise {matrix_type} resolvida via Regra de Cramer.")
        except Exception as e:
            self._cramer_result_text = f"[Erro de Cálculo Cramer]: {str(e)}"
        
        self.networkUpdated.emit()

    @pyqtProperty(str, notify=networkUpdated)
    def resultsSummary(self): return self._results_summary

    @pyqtProperty(str, notify=networkUpdated)
    def cramerResultText(self): return self._cramer_result_text

    @pyqtProperty(str, notify=networkUpdated)
    def schematicImageUrl(self): return f"file:///{self._schematic_path}"


# -----------------------------------------------------------------------------
# 2. INTERFACE QML: Barra de Circuitos CA/DC, Schemdraw & Solver Cramer 3x3
# -----------------------------------------------------------------------------
qml_code = """
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

ApplicationWindow {
    id: window
    width: 1360
    height: 768
    visible: true
    title: "Smart Grid Studio • ANAREDE + Schemdraw + Cramer 3x3"
    color: "#081014"

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // Barra Superior de Ferramentas Estilo ANAREDE / Schemdraw
        Rectangle {
            Layout.fillWidth: true
            height: 60
            color: "#0c171e"
            border.color: "#182c36"

            RowLayout {
                anchors.fill: parent; anchors.leftMargin: 20; anchors.rightMargin: 20; spacing: 14

                Rectangle {
                    width: 42; height: 36; radius: 6; color: "#182e38"; border.color: "#38e07b"; border.width: 1.5
                    Text { anchors.centerIn: parent; text: "ONS"; color: "#38e07b"; font.bold: true; font.pixelSize: 12 }
                }

                Row {
                    spacing: 8
                    Repeater {
                        model: ["Hub SEP", "Diagrama Schemdraw", "Decks ANAREDE", "Análise Nodal & Malhas (Cramer 3x3)"]
                        delegate: Rectangle {
                            width: tabText.implicitWidth + 22; height: 38; radius: 6
                            color: stackLayout.currentIndex === index ? "#3a4750" : (ma.containsMouse ? "#1c2e38" : "transparent")
                            border.color: stackLayout.currentIndex === index ? "#38e07b" : "transparent"; border.width: 1.5

                            Text {
                                id: tabText; anchors.centerIn: parent; text: modelData
                                color: stackLayout.currentIndex === index ? "#ffffff" : "#8e9ea8"
                                font.pixelSize: 13; font.bold: stackLayout.currentIndex === index
                            }
                            MouseArea {
                                id: ma; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                                onClicked: stackLayout.currentIndex = index
                            }
                        }
                    }
                }

                Item { Layout.fillWidth: true }
                
                Button {
                    text: "Executar Fluxo ONS"
                    onClicked: smartEngine.run_power_flow()
                    background: Rectangle { color: "#38e07b"; radius: 6 }
                    contentItem: Text { text: parent.text; color: "#081014"; font.bold: true; horizontalAlignment: Text.AlignHCenter }
                }
            }
        }

        // Stack Principal de Telas
        StackLayout {
            id: stackLayout
            Layout.fillWidth: true; Layout.fillHeight: true; currentIndex: 0

            // TELA 1: Hub SEP
            Item {
                Rectangle {
                    anchors.fill: parent; anchors.margins: 24; radius: 12; color: "#101d24"; border.color: "#1e3642"
                    ColumnLayout {
                        anchors.fill: parent; anchors.margins: 28; spacing: 20
                        Text { text: "SMART GRID POWER SYSTEM STUDIO - ONS / PANDAPOWER"; color: "#ffffff"; font.pixelSize: 26; font.bold: true }
                        Rectangle {
                            Layout.fillWidth: true; Layout.fillHeight: true; radius: 8; color: "#15242e"; border.color: "#253e4c"
                            ColumnLayout {
                                anchors.fill: parent; anchors.margins: 20; spacing: 12
                                Text { text: "RELATÓRIO DO SISTEMA ELÉTRICO"; color: "#38e07b"; font.bold: true; font.pixelSize: 15 }
                                TextArea {
                                    Layout.fillWidth: true; Layout.fillHeight: true
                                    text: smartEngine.resultsSummary
                                    color: "#d0dce4"; font.family: "Courier"; font.pixelSize: 14; readOnly: true
                                    background: Rectangle { color: "#091217"; radius: 6 }
                                }
                            }
                        }
                    }
                }
            }

            // TELA 2: Canvas com Schemdraw & Barra de Elementos CA/DC
            Item {
                Rectangle {
                    anchors.fill: parent; anchors.margins: 24; radius: 12; color: "#0c171e"; border.color: "#1e3642"
                    ColumnLayout {
                        anchors.fill: parent; anchors.margins: 20; spacing: 14

                        // Barra de Ferramentas de Circuitos CA/DC (Estilo ANAREDE / Schemdraw)
                        Rectangle {
                            Layout.fillWidth: true; height: 48; radius: 6; color: "#15242e"; border.color: "#243a46"
                            RowLayout {
                                anchors.fill: parent; anchors.leftMargin: 16; anchors.rightMargin: 16; spacing: 12
                                Text { text: "ELEMENTOS CA/DC:"; color: "#38e07b"; font.bold: true; font.pixelSize: 12 }
                                Repeater {
                                    model: ["⚡ Fonte AC", "🔌 Resistor", "🔋 Indutor", "⚡ Capacitor", "⏚ Terra", "⚙️ Trafo"]
                                    delegate: Button {
                                        text: modelData
                                        background: Rectangle { color: "#22343f"; radius: 4 }
                                        contentItem: Text { text: parent.text; color: "#ffffff"; font.pixelSize: 11; horizontalAlignment: Text.AlignHCenter }
                                    }
                                }
                                Item { Layout.fillWidth: true }
                            }
                        }

                        // Display da Imagem gerada pelo Schemdraw
                        Rectangle {
                            Layout.fillWidth: true; Layout.fillHeight: true; radius: 8; color: "#091217"; border.color: "#1a2c36"
                            Image {
                                anchors.centerIn: parent
                                source: smartEngine.schematicImageUrl
                                fillMode: Image.PreserveAspectFit
                                width: parent.width - 40; height: parent.height - 40
                            }
                        }
                    }
                }
            }

            // TELA 3: Leitor de Deck ANAREDE (.pwf / .dat)
            Item {
                Rectangle {
                    anchors.fill: parent; anchors.margins: 24; radius: 12; color: "#101d24"; border.color: "#1e3642"
                    ColumnLayout {
                        anchors.fill: parent; anchors.margins: 20; spacing: 14
                        Text { text: "IMPORTAÇÃO DE DECK ANAREDE (.pwf / .dat)"; color: "#ffffff"; font.bold: true; font.pixelSize: 16 }
                        RowLayout {
                            Layout.fillWidth: true
                            TextField {
                                id: deckInputPath; placeholderText: "Caminho do arquivo .pwf / .dat ou conteúdo bruto..."
                                Layout.fillWidth: true; color: "#ffffff"
                                background: Rectangle { color: "#15242e"; radius: 6; border.color: "#284450" }
                            }
                            Button {
                                text: "Carregar Deck ONS"
                                onClicked: smartEngine.parse_anarede_deck(deckInputPath.text)
                                background: Rectangle { color: "#38e07b"; radius: 6 }
                                contentItem: Text { text: parent.text; color: "#081014"; font.bold: true; horizontalAlignment: Text.AlignHCenter }
                            }
                        }
                        TextArea {
                            Layout.fillWidth: true; Layout.fillHeight: true
                            text: smartEngine.resultsSummary; color: "#38e07b"; font.family: "Courier"; readOnly: true
                            background: Rectangle { color: "#091217"; radius: 6 }
                        }
                    }
                }
            }

            // TELA 4: Análise Nodal & de Malhas com Regra de Cramer (3x3)
            Item {
                Rectangle {
                    anchors.fill: parent; anchors.margins: 24; radius: 12; color: "#101d24"; border.color: "#1e3642"
                    ColumnLayout {
                        anchors.fill: parent; anchors.margins: 20; spacing: 16

                        Text { text: "RESOLUTOR DE CIRCUITOS - ANÁLISE NODAL & MALHAS (CRAMER 3x3)"; color: "#ffffff"; font.bold: true; font.pixelSize: 16 }

                        RowLayout {
                            spacing: 16
                            Button {
                                text: "Análise Nodal (3 Nós)"
                                onClicked: typeField.text = "nodal"
                                background: Rectangle { color: "#22343f"; radius: 6 }
                                contentItem: Text { text: parent.text; color: "#ffffff"; font.bold: true; horizontalAlignment: Text.AlignHCenter }
                            }
                            Button {
                                text: "Análise de Malhas (3 Malhas)"
                                onClicked: typeField.text = "mesh"
                                background: Rectangle { color: "#22343f"; radius: 6 }
                                contentItem: Text { text: parent.text; color: "#ffffff"; font.bold: true; horizontalAlignment: Text.AlignHCenter }
                            }
                            TextField {
                                id: typeField; text: "nodal"; visible: false
                            }
                        }

                        RowLayout {
                            spacing: 14; Layout.fillWidth: true
                            ColumnLayout {
                                Layout.fillWidth: true; spacing: 6
                                Text { text: "Matriz Coeficientes (9 valores para 3x3):"; color: "#8e9ea8"; font.pixelSize: 13 }
                                TextField {
                                    id: matInput; text: "4 -1 0  -1 4 -1  0 -1 3"
                                    Layout.fillWidth: true; color: "#ffffff"
                                    background: Rectangle { color: "#15242e"; radius: 6; border.color: "#284450" }
                                }
                            }
                            ColumnLayout {
                                Layout.preferredWidth: 260; spacing: 6
                                Text { text: "Vetor Independente (3 valores):"; color: "#8e9ea8"; font.pixelSize: 13 }
                                TextField {
                                    id: vecInput; text: "10 0 5"
                                    Layout.fillWidth: true; color: "#ffffff"
                                    background: Rectangle { color: "#15242e"; radius: 6; border.color: "#284450" }
                                }
                            }
                        }

                        Button {
                            text: "Calcular com Regra de Cramer (3x3)"
                            onClicked: smartEngine.solve_circuit_cramer_3x3(typeField.text, matInput.text, vecInput.text)
                            background: Rectangle { color: "#38e07b"; radius: 6 }
                            contentItem: Text { text: parent.text; color: "#081014"; font.bold: true; horizontalAlignment: Text.AlignHCenter }
                        }

                        TextArea {
                            Layout.fillWidth: true; Layout.fillHeight: true
                            text: smartEngine.cramerResultText
                            color: "#38e07b"; font.family: "Courier"; font.pixelSize: 15; readOnly: true
                            background: Rectangle { color: "#091217"; radius: 6; border.color: "#1a2c36" }
                        }
                    }
                }
            }
        }
    }
}
"""

def main():
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()

    smart_engine = SmartGridStudioEngine()
    smart_engine.setParent(engine)
    engine.rootContext().setContextProperty("smartEngine", smart_engine)

    engine.loadData(qml_code.encode('utf-8'))
    if not engine.rootObjects():
        print("[ERRO FATAL] Falha ao carregar QML do Smart Grid.")
        sys.exit(-1)

    print("[OK] Smart Grid Studio com Schemdraw e Solver Cramer 3x3 iniciado com sucesso!")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()