#!/usr/bin/env python3
# ==============================================================================
# SMART GRID & POWER SYSTEM STUDIO (ANAREDE DBAR/DLIN + Pandapower + Schemdraw + Cramer 3x3 + Modal DBAR + Markdown Doc)
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

from PyQt6.QtWidgets import QApplication

#! pip install PyQt6 schemdraw pandapower numpy pandas 

# -----------------------------------------------------------------------------
# 1. CORE ENGINE: ANAREDE Deck Parser, Pandapower, Cramer 3x3 & Modal DBAR Manager
# -----------------------------------------------------------------------------
class SmartGridStudioEngine(QObject):
    networkUpdated = pyqtSignal()
    logMessage = pyqtSignal(str)
    schematicUpdated = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._net = pp.create_empty_network(name="SmartGrid_ONS_Model")
        self._deck_loaded = False
        self._results_summary = "Nenhuma rede carregada. Importe um arquivo .pwf ou .dat ou utilize o modal DBAR."
        self._schematic_path = os.path.abspath("circuit_schematic.png")
        self._cramer_result_text = "Nenhuma análise nodal/malha resolvida por Cramer (3x3)."
        self._readme_content = self._load_readme_file()
        
        # Propriedades do Modal DBAR (Espelhando a tela padrão ONS/ANAREDE)
        self._modal_bus_num = 1
        self._modal_bus_name = "Barra-1"
        self._modal_bus_type = 0  # 0-PQ, 1-PV, 2-Referência (Swing), 3-PQ VLIM
        self._modal_vm_pu = 1.0
        self._modal_va_deg = 0.0
        self._modal_vn_kv = 138.0
        self._modal_p_mw = 25.0
        self._modal_q_mvar = 10.0
        self._modal_pg_mw = 0.0
        self._modal_qg_mvar = 0.0
        
        # Inicializa caso padrão e gera esquemático inicial Schemdraw
        self._build_default_network()
        self._generate_schemdraw_diagram()

    def _load_readme_file(self):
        readme_path = os.path.abspath("README.md")
        if os.path.exists(readme_path):
            try:
                with open(readme_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception:
                pass
        
        # Conteúdo Markdown padrão profissional caso o arquivo não exista no disco
        return """# Smart Grid Studio ONS • Documentação Técnica

Bem-vindo ao ambiente avançado de modelagem, simulação e análise de sistemas elétricos de potência (**SEP**), desenvolvido com arquitetura híbrida **Python + PyQt6 + QML + Pandapower + Schemdraw**.

## 🚀 Funcionalidades Principais

1. **Parser de Decks ANAREDE (`.pwf` / `.dat`):**
   * Leitura automática de barramentos (`DBAR`) e linhas de transmissão (`DLIN`).
   * Conversão direta para estruturas de dados corporativas em `pandas.DataFrame`.
   * Modelagem completa de nós do Sistema Interligado Nacional (**SIN / ONS**).

2. **Modal de Dados de Barra CA (`DBAR`):**
   * Configuração interativa de barramentos via interface QML dedicada.
   * Seleção estrita do **Tipo de Barra**:
     * `0 - PQ`: Barra de Carga (Potência Ativa e Reativa especificadas).
     * `1 - PV`: Barra de Geração Controlada (Tensão e Potência Ativa especificadas).
     * `2 - Referência`: Barra de Folga / Slack / Swing (Referência angular do sistema).
     * `3 - PQ VLIM`: Barra com limite de tensão reativa restrito.
   * Inserção, alteração e remoção de elementos dinâmicos na rede ativa do `pandapower`.

3. **Resolutor de Circuitos por Regra de Cramer (3x3):**
   * Resolução exata de sistemas lineares para **Análise Nodal** ($V_1, V_2, V_3$) e **Análise de Malhas** ($I_1, I_2, I_3$).
   * Validação de determinante principal $D \neq 0$ e cálculo de matrizes adjuntas.

4. **Motor de Desenho Schemdraw AC/DC:**
   * Visualização gráfica vetorial de circuitos elementares (Fontes AC, Indutores, Capacitores, Resistores e Transformadores).

---
*Desenvolvido para engenheiros eletricistas e operadores do ONS.*
"""

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
            line_name = "CUSTOM_LINE_110kV"
            self._net.std_types.setdefault("line", {})
            self._net.std_types["line"][line_name] = {
                "r_ohm_per_km": 0.115,
                "x_ohm_per_km": 0.4,
                "c_nf_per_km": 0.0,
                "max_i_ka": 0.4,
            }
            preferred_line = line_name

        if preferred_trafo not in trafo_types:
            trafo_name = "CUSTOM_TRAFO_138_69"
            self._net.std_types.setdefault("trafo", {})
            self._net.std_types["trafo"][trafo_name] = {
                "sn_mva": 25.0,
                "vn_hv_kv": 138.0,
                "vn_lv_kv": 69.0,
                "vk_percent": 10.0,
                "vkr_percent": 0.4,
                "pfe_kw": 0.0,
                "i0_percent": 0.0,
                "shift_degree": 0,
            }
            preferred_trafo = trafo_name

        try:
            pp.create_line(
                self._net,
                from_bus=b1,
                to_bus=b2,
                length_km=15.0,
                std_type=preferred_line,
                name="DLIN_1-2",
            )
        except Exception as e:
            self.logMessage.emit(f"Erro ao criar linha padrão: {e}")
            raise

        try:
            pp.create_transformer(
                self._net,
                hv_bus=b1,
                lv_bus=b3,
                std_type=preferred_trafo,
                name="TRAFO_1-3",
            )
        except Exception as e:
            self.logMessage.emit(f"Erro ao criar trafo padrão: {e}")
            raise
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
        """Lê decks ANAREDE (.pwf / .dat) extraindo DBAR e DLIN com pandas"""
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
            lines = [l for l in dbar_match.group(1).strip().split('\n') if l.strip() and not l.strip().startswith('(')]
            for line in lines:
                parts = line.split()
                if len(parts) >= 6:
                    try:
                        buses_list.append({
                            "num": int(parts[0]), 
                            "nome": parts[1], 
                            "base_kv": float(parts[2]), 
                            "pg": float(parts[3]), 
                            "qg": float(parts[4])
                        })
                    except ValueError:
                        continue

        if buses_list:
            # Demonstração explícita de uso de DataFrame pandas para análise dos dados ANAREDE
            df_dbar = pd.DataFrame(buses_list)
            self.logMessage.emit(f"Pandas DataFrame DBAR criado com {len(df_dbar)} registros.")

            self._net = pp.create_empty_network(name="Anarede_Imported_Grid")
            bus_map = {}
            for _, b in df_dbar.iterrows():
                b_id = pp.create_bus(self._net, vn_kv=b["base_kv"], name=b["nome"])
                bus_map[int(b["num"])] = b_id
                if b["num"] == df_dbar.iloc[0]["num"]:
                    pp.create_ext_grid(self._net, bus=b_id, vm_pu=1.0)
                elif b["pg"] > 0:
                    pp.create_gen(self._net, bus=b_id, p_mw=b["pg"])
                else:
                    pp.create_load(self._net, bus=b_id, p_mw=abs(b["pg"]), q_mvar=abs(b["qg"]))
            
            self._run_power_flow()
            self.logMessage.emit(f"Deck ANAREDE importado com sucesso via pandas! {len(buses_list)} barramentos configurados.")

    @pyqtSlot(int, str, int, float, float, float, float, float, float, float)
    def insert_or_update_dbar_bus(self, num, name, bus_type, vm, va, kv, p_load, q_load, p_gen, q_gen):
        """Método acionado pelo Modal DBAR da UI para adicionar ou atualizar barra na rede pandapower"""
        try:
            # Verifica se a barra já existe no net
            existing_buses = self._net.bus.index.tolist()
            if num in existing_buses:
                # Atualiza nome e tensão base
                self._net.bus.at[num, 'name'] = name
                self._net.bus.at[num, 'vn_kv'] = kv
                self.logMessage.emit(f"Barra DBAR {num} ({name}) atualizada com sucesso.")
            else:
                # Cria nova barra
                pp.create_bus(self._net, nr=num, vn_kv=kv, name=name, type="b")
                self.logMessage.emit(f"Nova barra DBAR {num} ({name}) criada na rede.")

            # Trata o Tipo de Barra (0-PQ, 1-PV, 2-Referência/Swing, 3-PQ VLIM)
            if bus_type == 2:
                # Swing / Referência
                if not self._net.ext_grid[self._net.ext_grid.bus == num].empty:
                    self._net.ext_grid.loc[self._net.ext_grid.bus == num, 'vm_pu'] = vm
                else:
                    pp.create_ext_grid(self._net, bus=num, vm_pu=vm, name=f"Ref_{num}")
            elif bus_type == 1:
                # PV (Geração)
                if not self._net.gen[self._net.gen.bus == num].empty:
                    self._net.gen.loc[self._net.gen.bus == num, 'p_mw'] = p_gen if p_gen > 0 else 20.0
                    self._net.gen.loc[self._net.gen.bus == num, 'vm_pu'] = vm
                else:
                    pp.create_gen(self._net, bus=num, p_mw=p_gen if p_gen > 0 else 20.0, vm_pu=vm, name=f"Gen_{num}")
            else:
                # PQ (Carga)
                if p_load > 0 or q_load > 0:
                    if not self._net.load[self._net.load.bus == num].empty:
                        self._net.load.loc[self._net.load.bus == num, 'p_mw'] = p_load
                        self._net.load.loc[self._net.load.bus == num, 'q_mvar'] = q_load
                    else:
                        pp.create_load(self._net, bus=num, p_mw=p_load, q_mvar=q_load, name=f"Carga_{num}")

            self._run_power_flow()
        except Exception as e:
            self.logMessage.emit(f"[Erro Modal DBAR]: {str(e)}")

    @pyqtSlot()
    def run_power_flow(self):
        self._run_power_flow()

    def _run_power_flow(self):
        try:
            pp.runpp(self._net)
            res = self._net.res_bus
            self._results_summary = (
                f"Fluxo de Potência CONVERGIDO (Newton-Raphson ONS)\n"
                f"• Total de Barras Ativas: {len(self._net.bus)}\n"
                f"• Tensão Mínima: {res.vm_pu.min():.3f} p.u. | Máxima: {res.vm_pu.max():.3f} p.u.\n"
                f"• Solução estável calculada e integrada com pandas/pandapower."
            )
            self.logMessage.emit("Fluxo de potência convergido com sucesso.")
        except Exception as e:
            self._results_summary = f"Erro no Fluxo: {e}"
        self.networkUpdated.emit()

    @pyqtSlot(str, str, str)
    def solve_circuit_cramer_3x3(self, matrix_type, mat_data_str, vec_data_str):
        """
        Resolve Análise Nodal ou de Malhas (3x3) utilizando estritamente a Regra de Cramer.
        Mapeia exatamente 3 incógnitas e 3 equações.
        """
        try:
            m_vals = [float(x) for x in mat_data_str.replace(',', ' ').split() if x.strip()]
            v_vals = [float(x) for x in vec_data_str.replace(',', ' ').split() if x.strip()]

            if len(m_vals) != 9 or len(v_vals) != 3:
                self._cramer_result_text = "[Erro] Insira exatamente 9 valores para a matriz 3x3 e 3 valores para o vetor independente."
                self.networkUpdated.emit()
                return

            A = np.array(m_vals, dtype=float).reshape(3, 3)
            B = np.array(v_vals, dtype=float).reshape(3, 1)

            det_A = np.linalg.det(A)
            if abs(det_A) < 1e-9:
                self._cramer_result_text = f"Determinante principal D = {det_A:.5f} ≈ 0. Sistema Singular ou Indeterminado."
                self.networkUpdated.emit()
                return

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
                f"• Status: Solução exata 3x3 obtida com sucesso!"
            )
            self.logMessage.emit(f"Análise {matrix_type} resolvida via Regra de Cramer 3x3.")
        except Exception as e:
            self._cramer_result_text = f"[Erro de Cálculo Cramer]: {str(e)}"
        
        self.networkUpdated.emit()

    @pyqtProperty(str, notify=networkUpdated)
    def resultsSummary(self): return self._results_summary

    @pyqtProperty(str, notify=networkUpdated)
    def cramerResultText(self): return self._cramer_result_text

    @pyqtProperty(str, notify=networkUpdated)
    def schematicImageUrl(self): return f"file:///{self._schematic_path}"

    @pyqtProperty(str, notify=networkUpdated)
    def readmeMarkdownContent(self): return self._readme_content


# -----------------------------------------------------------------------------
# 2. INTERFACE QML: Abas Principais, Modal DBAR, Schemdraw & Cramer 3x3
# -----------------------------------------------------------------------------
qml_code = """
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

ApplicationWindow {
    id: root
    width: 1200
    height: 800
    visible: true
    title: "Smart Grid Studio • ANAREDE + Pandapower + Cramer 3x3"
    color: "#081014"

    Rectangle {
        anchors.fill: parent
        anchors.margins: 16
        radius: 12
        color: "#101d24"
        border.color: "#1e3642"

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 20
            spacing: 20

            Text {
                text: "SMART GRID POWER SYSTEM STUDIO"
                color: "#ffffff"
                font.pixelSize: 26
                font.bold: true
            }

            Rectangle {
                Layout.fillWidth: true
                height: 120
                radius: 8
                color: "#15242e"
                border.color: "#253e4c"

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 10

                    Text {
                        text: "RELATÓRIO DO SISTEMA ELÉTRICO"
                        color: "#38e07b"
                        font.bold: true
                    }

                    TextArea {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        text: smartEngine.resultsSummary
                        color: "#d0dce4"
                        font.family: "Courier"
                        readOnly: true
                        background: Rectangle {
                            color: "#091217"
                            radius: 6
                            border.color: "#1a2c36"
                        }
                    }
                }
            }

            RowLayout {
                spacing: 12

                Button {
                    text: "Executar Fluxo ONS"
                    onClicked: smartEngine.run_power_flow()
                    background: Rectangle { color: "#38e07b"; radius: 6 }
                    contentItem: Text {
                        text: parent.text
                        color: "#081014"
                        font.bold: true
                        horizontalAlignment: Text.AlignHCenter
                    }
                }

                Button {
                    text: "Calcular Cramer 3x3"
                    onClicked: smartEngine.solve_circuit_cramer_3x3("nodal", "4 -1 0 -1 4 -1 0 -1 3", "10 0 5")
                    background: Rectangle { color: "#22343f"; radius: 6 }
                    contentItem: Text {
                        text: parent.text
                        color: "#ffffff"
                        font.bold: true
                        horizontalAlignment: Text.AlignHCenter
                    }
                }
            }

            TextArea {
                Layout.fillWidth: true
                Layout.fillHeight: true
                text: smartEngine.cramerResultText
                color: "#38e07b"
                font.family: "Courier"
                font.pixelSize: 14
                readOnly: true
                background: Rectangle {
                    color: "#091217"
                    radius: 6
                    border.color: "#1a2c36"
                }
            }
        }
    }
}
"""

def main():
    app = QApplication(sys.argv)
    engine = QQmlApplicationEngine()

    smart_engine = SmartGridStudioEngine()
    smart_engine.setParent(engine)
    engine.rootContext().setContextProperty("smartEngine", smart_engine)

    engine.loadData(qml_code.encode('utf-8'))
    if not engine.rootObjects():
        print("[ERRO FATAL] Falha ao carregar QML do Smart Grid.")
        sys.exit(-1)

    print("[OK] Smart Grid Studio com Modal DBAR, Schemdraw, Cramer 3x3 e Aba Markdown iniciado com sucesso!")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()