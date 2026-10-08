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
import json
import numpy as np
import pandas as pd

import pandapower as pp
import schemdraw
import schemdraw.elements as elm

from PyQt6.QtCore import QObject, pyqtSignal, pyqtProperty, pyqtSlot, QUrl
from PyQt6.QtGui import QGuiApplication, QImage, QPixmap
from PyQt6.QtQml import QQmlApplicationEngine

from PyQt6.QtWidgets import QApplication
from PyQt6.QtWidgets import QFileDialog

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
        self._deck_text = ""
        
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
        example_path = os.path.join(os.path.dirname(__file__), "examples", "rede_3_barras.pwf")
        if os.path.isfile(example_path):
            self.load_example_deck("3")
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

    @staticmethod
    def _number(value, default=0.0):
        try:
            return float(value.strip().replace(",", "."))
        except (AttributeError, TypeError, ValueError):
            return default

    @staticmethod
    def _section_records(content):
        sections = {"DBAR": [], "DLIN": [], "DGBT": []}
        active_section = None
        for raw_line in content.splitlines():
            line = raw_line.strip()
            if not line or line.startswith(("(", "#")):
                continue
            if line.startswith("99999") or line.upper() == "FIM":
                active_section = None
                continue
            command = line.split()[0].upper()
            if command in sections and len(line.split()) == 1:
                active_section = command
                continue
            if active_section:
                sections[active_section].append(raw_line.rstrip())
        return sections

    def _parse_bus_record(self, line, voltage_groups):
        parts = line.split()
        kinds = {"REF", "SLACK", "SWING", "PV", "PQ"}
        if len(parts) >= 7 and parts[0].lstrip("+-").isdigit() and parts[1].upper() in kinds:
            values = parts[7:] + ["0"] * max(0, 10 - len(parts))
            return {
                "num": int(parts[0]),
                "kind": "REF" if parts[1].upper() in {"REF", "SLACK", "SWING"} else parts[1].upper(),
                "name": parts[2],
                "vn_kv": self._number(parts[3], 230.0),
                "vm_pu": self._number(parts[4], 1.0),
                "va_degree": self._number(parts[5]),
                "pg": self._number(parts[6]),
                "qg": self._number(values[0]),
                "pl": self._number(values[1]),
                "ql": self._number(values[2]),
            }

        if len(line) < 28:
            raise ValueError(f"Registro DBAR inválido: {line}")
        number = int(line[0:5])
        group = line[22:23].strip().upper()
        bus_code = line[7:8].strip()
        return {
            "num": number,
            "kind": "REF" if bus_code == "2" else "PV" if bus_code == "1" else "PQ",
            "name": line[10:22].strip() or f"BARRA_{number}",
            "vn_kv": voltage_groups.get(group, 230.0),
            "vm_pu": self._number(line[24:28], 1000.0) / 1000.0,
            "va_degree": self._number(line[28:32]),
            "pg": self._number(line[32:38]),
            "qg": self._number(line[38:44]),
            "pl": self._number(line[59:65]),
            "ql": self._number(line[65:71]),
        }

    def _parse_branch_record(self, line):
        parts = line.split()
        if len(line) >= 44:
            return {
                "from": int(line[0:5]),
                "to": int(line[11:16]),
                "circuit": line[16:17].strip() or "1",
                "r_pct": self._number(line[20:26]),
                "x_pct": self._number(line[26:32]),
                "b_mvar": self._number(line[32:38]),
                "tap": self._number(line[38:44], 1.0) or 1.0,
            }
        if len(parts) >= 6 and all(part.lstrip("+-").isdigit() for part in parts[:3]):
            numeric = parts[3:]
            if len(numeric) >= 3:
                parsed = [self._number(value, float("nan")) for value in numeric]
                if all(np.isfinite(parsed[:3])):
                    return {
                        "from": int(parts[0]), "to": int(parts[1]), "circuit": parts[2],
                        "r_pct": parsed[0], "x_pct": parsed[1], "b_mvar": parsed[2],
                        "tap": parsed[3] if len(parsed) > 3 and np.isfinite(parsed[3]) else 1.0,
                    }

        if len(line) < 38:
            raise ValueError(f"Registro DLIN inválido: {line}")
        return {
            "from": int(line[0:5]),
            "to": int(line[11:16]),
            "circuit": line[16:17].strip() or "1",
            "r_pct": self._number(line[20:26]),
            "x_pct": self._number(line[26:32]),
            "b_mvar": self._number(line[32:38]),
            "tap": self._number(line[38:44], 1.0) or 1.0,
        }

    def _build_network_from_pwf(self, content):
        sections = self._section_records(content)
        voltage_groups = {}
        for row in sections["DGBT"]:
            fields = row.split()
            if len(fields) >= 2:
                voltage_groups[fields[0].upper()] = self._number(fields[1])

        buses = [self._parse_bus_record(row, voltage_groups) for row in sections["DBAR"] if row.strip()]
        branches = [self._parse_branch_record(row) for row in sections["DLIN"] if row.strip()]
        if not buses:
            raise ValueError("O deck não contém registros DBAR válidos.")

        numbers = [bus["num"] for bus in buses]
        if len(numbers) != len(set(numbers)):
            raise ValueError("O deck contém números DBAR duplicados.")
        bus_numbers = set(numbers)
        missing = sorted({branch[key] for branch in branches for key in ("from", "to") if branch[key] not in bus_numbers})
        if missing:
            raise ValueError(f"DLIN referencia barras não cadastradas: {', '.join(map(str, missing))}.")

        net = pp.create_empty_network(name="ANAREDE_PWF", sn_mva=100.0, f_hz=60.0)
        for bus in buses:
            pp.create_bus(net, index=bus["num"], vn_kv=bus["vn_kv"], name=bus["name"], type="b")

        reference = next((bus for bus in buses if bus["kind"] == "REF"), buses[0])
        pp.create_ext_grid(net, bus=reference["num"], vm_pu=reference["vm_pu"], name=f"Referência {reference['num']}")
        for bus in buses:
            number = bus["num"]
            if number != reference["num"] and bus["kind"] == "PV":
                pp.create_gen(net, bus=number, p_mw=bus["pg"], vm_pu=bus["vm_pu"], name=f"Gerador {number}")
            if bus["pl"] > 0 or bus["ql"] > 0:
                pp.create_load(net, bus=number, p_mw=max(bus["pl"], 0.0), q_mvar=max(bus["ql"], 0.0), name=f"Carga {number}")

        for branch in branches:
            from_bus, to_bus = branch["from"], branch["to"]
            vn_from = float(net.bus.at[from_bus, "vn_kv"])
            vn_to = float(net.bus.at[to_bus, "vn_kv"])
            r_pct = abs(branch["r_pct"])
            x_pct = abs(branch["x_pct"])
            tap = branch["tap"]
            is_transformer = abs(vn_from - vn_to) > 1.0 or abs(tap - 1.0) > 0.01
            name = f"{from_bus}-{to_bus} circ. {branch['circuit']}"
            if is_transformer:
                hv_bus, lv_bus = (from_bus, to_bus) if vn_from >= vn_to else (to_bus, from_bus)
                vn_hv, vn_lv = max(vn_from, vn_to), min(vn_from, vn_to)
                transformer_args = {}
                if abs(tap - 1.0) > 0.01:
                    transformer_args = {
                        "tap_side": "hv", "tap_neutral": 0, "tap_step_percent": 1.0,
                        "tap_pos": round((tap - 1.0) * 100),
                    }
                pp.create_transformer_from_parameters(
                    net, hv_bus=hv_bus, lv_bus=lv_bus, sn_mva=100.0,
                    vn_hv_kv=vn_hv, vn_lv_kv=vn_lv,
                    vkr_percent=max(r_pct, 0.01),
                    vk_percent=max(float(np.hypot(r_pct, x_pct)), max(r_pct, 0.01) + 0.01),
                    pfe_kw=0.0, i0_percent=0.0, name=name, **transformer_args,
                )
            else:
                z_base = vn_from ** 2 / net.sn_mva
                pp.create_line_from_parameters(
                    net, from_bus=from_bus, to_bus=to_bus, length_km=1.0,
                    r_ohm_per_km=max(r_pct * z_base / 100.0, 1e-5),
                    x_ohm_per_km=max(x_pct * z_base / 100.0, 1e-5),
                    c_nf_per_km=0.0, max_i_ka=1.0, name=name,
                )
        return net, len(buses), len(branches)

    @pyqtSlot(str)
    def parse_anarede_deck(self, filepath_or_text):
        """Importa as seções DBAR, DLIN e DGBT de um deck PWF."""
        try:
            source = str(filepath_or_text)
            if "\n" not in source and os.path.isfile(source):
                with open(source, "r", encoding="latin1") as deck_file:
                    content = deck_file.read()
            else:
                content = source
            net, bus_count, branch_count = self._build_network_from_pwf(content)
            self._net = net
            self._deck_text = content
            self._results_summary = f"Deck ANAREDE carregado: {bus_count} barras | {branch_count} ramos."
            self._run_power_flow()
            self.logMessage.emit(f"PWF importado: {bus_count} barras e {branch_count} ramos.")
        except Exception as error:
            self.logMessage.emit(f"[Erro PWF]: {error}")
            self._results_summary = f"Falha ao importar PWF: {error}"
            self.networkUpdated.emit()

    @pyqtSlot(str)
    def set_deck_text(self, text):
        self._deck_text = text
        self.networkUpdated.emit()

    @pyqtSlot(str)
    def load_example_deck(self, bus_count):
        example_path = os.path.join(os.path.dirname(__file__), "examples", f"rede_{bus_count}_barras.pwf")
        try:
            with open(example_path, "r", encoding="latin1") as deck_file:
                self.parse_anarede_deck(deck_file.read())
        except OSError as error:
            self.logMessage.emit(f"[Erro exemplo]: {error}")

    @pyqtSlot()
    def open_deck_file(self):
        path, _ = QFileDialog.getOpenFileName(None, "Abrir deck ANAREDE", "", "Decks ANAREDE (*.pwf *.dat);;Todos os arquivos (*)")
        if path:
            self.parse_anarede_deck(path)

    @pyqtSlot()
    def save_deck_file(self):
        path, _ = QFileDialog.getSaveFileName(None, "Salvar deck ANAREDE", "rede.pwf", "Deck ANAREDE (*.pwf)")
        if path:
            if not path.lower().endswith(".pwf"):
                path += ".pwf"
            with open(path, "w", encoding="latin1", errors="replace") as deck_file:
                deck_file.write(self._deck_text)
            self.logMessage.emit(f"Deck salvo em {path}")

    @pyqtSlot(str)
    def append_anarede_record(self, command):
        fields = command.strip().split()
        if len(fields) < 2 or fields[0].upper() not in {"DBAR", "DLIN"}:
            self.logMessage.emit("Use DBAR para barra ou DLIN para ramo. Transformadores são DLIN com tap ou bases diferentes.")
            return

        section = fields[0].upper()
        record = " ".join(fields[1:])
        lines = self._deck_text.splitlines()
        section_index = next((index for index, line in enumerate(lines) if line.strip().upper() == section), None)
        if section_index is None:
            try:
                end_index = next(index for index, line in enumerate(lines) if line.strip().upper() == "FIM")
            except StopIteration:
                end_index = len(lines)
            lines[end_index:end_index] = [section, record, "99999"]
        else:
            end_index = next(
                (index for index in range(section_index + 1, len(lines)) if lines[index].strip().startswith("99999")),
                len(lines),
            )
            lines.insert(end_index, record)
        self.parse_anarede_deck("\n".join(lines))

    @pyqtProperty(str, notify=networkUpdated)
    def deckText(self):
        return self._deck_text

    @pyqtProperty(str, notify=networkUpdated)
    def networkTopology(self):
        bus_ids = list(self._net.bus.index)
        count = len(bus_ids)
        bus_positions = {}
        for index, bus_id in enumerate(bus_ids):
            angle = -np.pi / 2 + 2 * np.pi * index / max(count, 1)
            bus_positions[int(bus_id)] = (0.5 + 0.40 * np.cos(angle), 0.5 + 0.38 * np.sin(angle))

        reference_ids = set(self._net.ext_grid.bus.astype(int).tolist())
        generator_ids = set(self._net.gen.bus.astype(int).tolist())
        load_ids = set(self._net.load.bus.astype(int).tolist())
        buses = []
        for bus_id, bus in self._net.bus.iterrows():
            bus_id = int(bus_id)
            x, y = bus_positions[bus_id]
            kind = "reference" if bus_id in reference_ids else "generator" if bus_id in generator_ids else "load" if bus_id in load_ids else "bus"
            buses.append({"id": bus_id, "name": str(bus["name"] or f"Barra {bus_id}"), "kv": float(bus.vn_kv), "kind": kind, "x": float(x), "y": float(y)})

        lines = [{"from": int(row.from_bus), "to": int(row.to_bus)} for row in self._net.line.itertuples()]
        transformers = [{"from": int(row.hv_bus), "to": int(row.lv_bus)} for row in self._net.trafo.itertuples()]
        return json.dumps({"buses": buses, "lines": lines, "transformers": transformers}, ensure_ascii=True)

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
    width: 1480
    height: 900
    minimumWidth: 1120
    minimumHeight: 720
    visible: true
    title: "Smart Grid Studio | ANAREDE PWF"
    color: "#0b1419"
    property var topology: JSON.parse(smartEngine.networkTopology)

    Connections {
        target: smartEngine
        function onNetworkUpdated() {
            root.topology = JSON.parse(smartEngine.networkTopology)
            if (!deckEditor.activeFocus)
                deckEditor.text = smartEngine.deckText
            topologyCanvas.requestPaint()
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 76
            color: "#111e24"
            border.color: "#263841"

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 24
                anchors.rightMargin: 24

                ColumnLayout {
                    spacing: 3
                    Text { text: "SMART GRID / ANAREDE"; color: "#f0f5f2"; font.pixelSize: 21; font.bold: true }
                    Text { text: "PWF editor · Pandapower · topologia"; color: "#93a7a6"; font.pixelSize: 12 }
                }

                Item { Layout.fillWidth: true }

                Text {
                    text: root.topology.buses.length + " barras   /   " + root.topology.lines.length + " linhas   /   " + root.topology.transformers.length + " trafos"
                    color: "#67d9b2"
                    font.pixelSize: 14
                    font.bold: true
                }
            }
        }

        TabBar {
            id: tabs
            Layout.fillWidth: true
            background: Rectangle { color: "#0e191e" }
            TabButton { text: "Rede PWF" }
            TabButton { text: "Análise" }
        }

        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: tabs.currentIndex

            Item {
                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 18
                    spacing: 14

                    Rectangle {
                        Layout.preferredWidth: 610
                        Layout.fillHeight: true
                        color: "#111e24"
                        border.color: "#293b42"

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 14
                            spacing: 10

                            RowLayout {
                                Layout.fillWidth: true
                                Text { text: "DECK ANAREDE"; color: "#edf3ef"; font.bold: true; font.pixelSize: 14 }
                                Item { Layout.fillWidth: true }
                                ComboBox {
                                    id: examplePicker
                                    model: ["3 barras", "5 barras", "10 barras"]
                                    implicitWidth: 130
                                    onActivated: smartEngine.load_example_deck(["3", "5", "10"][currentIndex])
                                }
                            }

                            RowLayout {
                                Layout.fillWidth: true
                                Button { text: "Abrir PWF"; onClicked: smartEngine.open_deck_file() }
                                Button { text: "Salvar PWF"; onClicked: smartEngine.save_deck_file() }
                                Item { Layout.fillWidth: true }
                                Button {
                                    text: "Importar rede"
                                    onClicked: smartEngine.parse_anarede_deck(deckEditor.text)
                                    background: Rectangle { color: "#55d2a7"; radius: 4 }
                                    contentItem: Text { text: parent.text; color: "#0b1717"; font.bold: true; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                                }
                            }

                            TextArea {
                                id: deckEditor
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                Layout.minimumHeight: 280
                                color: "#d8e5e0"
                                selectionColor: "#286a5d"
                                selectedTextColor: "#ffffff"
                                font.family: "Consolas"
                                font.pixelSize: 12
                                wrapMode: TextEdit.NoWrap
                                selectByMouse: true
                                background: Rectangle { color: "#091216"; border.color: "#25363c" }
                                Component.onCompleted: text = smartEngine.deckText
                                onTextChanged: if (activeFocus) smartEngine.set_deck_text(text)
                            }

                            RowLayout {
                                Layout.fillWidth: true
                                TextField {
                                    id: commandInput
                                    Layout.fillWidth: true
                                    placeholderText: "DBAR 4 PQ BARRA_4 230 1 0 0 0 20 8  |  DLIN 1 4 1 0.6 8 0 1"
                                    onAccepted: {
                                        smartEngine.append_anarede_record(text)
                                        clear()
                                    }
                                }
                                Button {
                                    text: "Inserir registro"
                                    onClicked: {
                                        smartEngine.append_anarede_record(commandInput.text)
                                        commandInput.clear()
                                    }
                                }
                            }

                            Text {
                                Layout.fillWidth: true
                                text: "Trafo: DLIN entre níveis de tensão diferentes ou com tap diferente de 1.0."
                                color: "#8da19f"
                                font.pixelSize: 11
                                wrapMode: Text.WordWrap
                            }

                            Text {
                                Layout.fillWidth: true
                                text: smartEngine.resultsSummary
                                color: smartEngine.resultsSummary.indexOf("CONVERGIDO") >= 0 ? "#67d9b2" : "#f0bf69"
                                font.pixelSize: 12
                                wrapMode: Text.WordWrap
                            }
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        color: "#111e24"
                        border.color: "#293b42"

                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 14
                            spacing: 8

                            RowLayout {
                                Layout.fillWidth: true
                                Text { text: "TOPOLOGIA DA REDE"; color: "#edf3ef"; font.bold: true; font.pixelSize: 14 }
                                Item { Layout.fillWidth: true }
                                Text { text: "● referência"; color: "#f2c66d"; font.pixelSize: 11 }
                                Text { text: "● geração"; color: "#65d8b2"; font.pixelSize: 11 }
                                Text { text: "● carga"; color: "#79a9d2"; font.pixelSize: 11 }
                            }

                            Item {
                                Layout.fillWidth: true
                                Layout.fillHeight: true

                                Canvas {
                                    id: topologyCanvas
                                    anchors.fill: parent
                                    onPaint: {
                                        var ctx = getContext("2d")
                                        ctx.clearRect(0, 0, width, height)
                                        ctx.fillStyle = "#0b151a"
                                        ctx.fillRect(0, 0, width, height)
                                        var data = root.topology
                                        var positions = ({})
                                        var centerX = width / 2
                                        var centerY = height / 2
                                        var radiusX = Math.max(40, width * 0.36)
                                        var radiusY = Math.max(40, height * 0.36)

                                        for (var i = 0; i < data.buses.length; ++i) {
                                            var angle = -Math.PI / 2 + 2 * Math.PI * i / Math.max(1, data.buses.length)
                                            positions[data.buses[i].id] = {
                                                x: centerX + radiusX * Math.cos(angle),
                                                y: centerY + radiusY * Math.sin(angle)
                                            }
                                        }

                                        function drawEdges(edges, transformer) {
                                            for (var j = 0; j < edges.length; ++j) {
                                                var start = positions[edges[j].from]
                                                var end = positions[edges[j].to]
                                                if (!start || !end) continue
                                                ctx.beginPath()
                                                ctx.moveTo(start.x, start.y)
                                                ctx.lineTo(end.x, end.y)
                                                ctx.strokeStyle = transformer ? "#df9d57" : "#52747b"
                                                ctx.lineWidth = transformer ? 2.5 : 1.6
                                                ctx.stroke()
                                                if (transformer) {
                                                    var middleX = (start.x + end.x) / 2
                                                    var middleY = (start.y + end.y) / 2
                                                    ctx.fillStyle = "#0b151a"
                                                    ctx.beginPath(); ctx.arc(middleX - 5, middleY, 5, 0, 2 * Math.PI); ctx.fill()
                                                    ctx.beginPath(); ctx.arc(middleX + 5, middleY, 5, 0, 2 * Math.PI); ctx.fill()
                                                    ctx.strokeStyle = "#f0b36e"
                                                    ctx.lineWidth = 2
                                                    ctx.beginPath(); ctx.arc(middleX - 5, middleY, 5, 0, 2 * Math.PI); ctx.stroke()
                                                    ctx.beginPath(); ctx.arc(middleX + 5, middleY, 5, 0, 2 * Math.PI); ctx.stroke()
                                                }
                                            }
                                        }

                                        drawEdges(data.lines, false)
                                        drawEdges(data.transformers, true)

                                        for (var k = 0; k < data.buses.length; ++k) {
                                            var bus = data.buses[k]
                                            var point = positions[bus.id]
                                            var fill = bus.kind === "reference" ? "#f2c66d" : bus.kind === "generator" ? "#65d8b2" : bus.kind === "load" ? "#79a9d2" : "#d7e2dc"
                                            ctx.beginPath()
                                            ctx.arc(point.x, point.y, 17, 0, 2 * Math.PI)
                                            ctx.fillStyle = fill
                                            ctx.fill()
                                            ctx.strokeStyle = "#071114"
                                            ctx.lineWidth = 2
                                            ctx.stroke()
                                            ctx.fillStyle = "#102027"
                                            ctx.font = "bold 11px 'Segoe UI'"
                                            ctx.textAlign = "center"
                                            ctx.textBaseline = "middle"
                                            ctx.fillText(String(bus.id), point.x, point.y)
                                            ctx.fillStyle = "#d6e2dd"
                                            ctx.font = "11px 'Segoe UI'"
                                            ctx.textAlign = point.x < centerX ? "right" : "left"
                                            ctx.fillText(bus.name + " · " + bus.kv + " kV", point.x + (point.x < centerX ? -23 : 23), point.y + 1)
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            Item {
                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 18
                    spacing: 14

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        color: "#111e24"
                        border.color: "#293b42"
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 18
                            Text { text: "RELATÓRIO DO FLUXO DE POTÊNCIA"; color: "#edf3ef"; font.bold: true; font.pixelSize: 14 }
                            TextArea {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                text: smartEngine.resultsSummary
                                color: "#bfe7d7"
                                font.family: "Consolas"
                                readOnly: true
                                background: Rectangle { color: "#091216"; border.color: "#25363c" }
                            }
                            Button { text: "Executar fluxo Newton-Raphson"; onClicked: smartEngine.run_power_flow() }
                        }
                    }

                    Rectangle {
                        Layout.preferredWidth: 520
                        Layout.fillHeight: true
                        color: "#111e24"
                        border.color: "#293b42"
                        ColumnLayout {
                            anchors.fill: parent
                            anchors.margins: 18
                            Text { text: "CRAMER 3×3"; color: "#edf3ef"; font.bold: true; font.pixelSize: 14 }
                            TextField { id: matrixInput; Layout.fillWidth: true; text: "4 -1 0 -1 4 -1 0 -1 3"; placeholderText: "9 coeficientes da matriz" }
                            TextField { id: vectorInput; Layout.fillWidth: true; text: "10 0 5"; placeholderText: "3 valores independentes" }
                            RowLayout {
                                ComboBox { id: matrixType; model: ["nodal", "malhas"] }
                                Button { text: "Resolver"; onClicked: smartEngine.solve_circuit_cramer_3x3(matrixType.currentIndex === 0 ? "nodal" : "mesh", matrixInput.text, vectorInput.text) }
                            }
                            TextArea {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                text: smartEngine.cramerResultText
                                color: "#67d9b2"
                                font.family: "Consolas"
                                readOnly: true
                                background: Rectangle { color: "#091216"; border.color: "#25363c" }
                            }
                        }
                    }
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