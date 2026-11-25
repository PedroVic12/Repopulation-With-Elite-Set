#!/usr/bin/env python3
# ==============================================================================
# SMART GRID STUDIO (ANAREDE + Pandapower + QML single-line diagram)
# Arquitetura Orientada a Objetos (POO): SmartGridStudioEngine
# ==============================================================================

import sys
import os
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")
import re
import json
import numpy as np
import pandas as pd

import pandapower as pp

from PyQt6.QtCore import QObject, pyqtSignal, pyqtProperty, pyqtSlot, QUrl
from PyQt6.QtQml import QQmlApplicationEngine

from PyQt6.QtWidgets import QApplication
from PyQt6.QtWidgets import QFileDialog

#! pip install PyQt6 pandapower numpy pandas 

# -----------------------------------------------------------------------------
# 1. CORE ENGINE: ANAREDE Deck Parser, Pandapower, Cramer 3x3 & Modal DBAR Manager
# -----------------------------------------------------------------------------
class SmartGridStudioEngine(QObject):
    networkUpdated = pyqtSignal()
    logMessage = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._net = pp.create_empty_network(name="SmartGrid_ONS_Model")
        self._deck_loaded = False
        self._results_summary = "Nenhuma rede carregada. Importe um arquivo .pwf ou .dat ou utilize o modal DBAR."
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

        
        # Inicializa a rede padrão; o diagrama é renderizado no canvas QML.
        self._build_default_network()
        example_path = os.path.join(os.path.dirname(__file__), "examples", "rede_3_barras.pwf")
        if os.path.isfile(example_path):
            self.load_example_deck("3")

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

Bem-vindo ao ambiente de modelagem e análise de sistemas elétricos de potência (**SEP**), desenvolvido com **Python + PyQt6 + QML + Pandapower**.

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

4. **Diagrama unifilar QML:**
   * Barras, linhas e transformadores são renderizados a partir da topologia da rede Pandapower.

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
        name = line[9:21].strip() or f"BARRA_{number}"
        nominal_voltage = voltage_groups.get(group)
        if nominal_voltage is None:
            voltage_suffix = re.search(r"(\d{2,3})$", name)
            nominal_voltage = float(voltage_suffix.group(1)) if voltage_suffix else 230.0
        return {
            "num": number,
            "kind": "REF" if bus_code == "2" else "PV" if bus_code == "1" else "PQ",
            "name": name,
            "vn_kv": nominal_voltage,
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
        bus_ids = sorted(int(bus_id) for bus_id in self._net.bus.index)
        line_rows = list(self._net.line.itertuples())
        trafo_rows = list(self._net.trafo.itertuples())
        adjacency = {bus_id: set() for bus_id in bus_ids}
        for row in line_rows:
            adjacency[int(row.from_bus)].add(int(row.to_bus))
            adjacency[int(row.to_bus)].add(int(row.from_bus))
        for row in trafo_rows:
            adjacency[int(row.hv_bus)].add(int(row.lv_bus))
            adjacency[int(row.lv_bus)].add(int(row.hv_bus))

        reference_ids = set(int(bus_id) for bus_id in self._net.ext_grid.bus)
        components = []
        remaining = set(bus_ids)
        while remaining:
            preferred_roots = sorted(remaining & reference_ids)
            root = preferred_roots[0] if preferred_roots else min(remaining)
            depths = {root: 0}
            queue = [root]
            for bus_id in queue:
                for neighbor in sorted(adjacency[bus_id]):
                    if neighbor not in depths:
                        depths[neighbor] = depths[bus_id] + 1
                        queue.append(neighbor)
            remaining.difference_update(depths)
            components.append(depths)

        components.sort(key=lambda component: (not bool(set(component) & reference_ids), min(component)))
        bus_positions = {}
        column_offset = 0
        layout_width = 0
        layout_height = 0
        for depths in components:
            layers = {}
            for bus_id, depth in depths.items():
                layers.setdefault(depth, []).append(bus_id)
            component_height = max(map(len, layers.values()))
            max_depth = max(depths.values())
            for depth, layer_bus_ids in layers.items():
                for row_index, bus_id in enumerate(sorted(layer_bus_ids)):
                    row = round((row_index + 0.5) * component_height / len(layer_bus_ids) - 0.5)
                    bus_positions[bus_id] = (column_offset + depth, max(row, 0))
            component_width = max_depth + 1
            column_offset += component_width + 1
            layout_width = column_offset - 1
            layout_height = max(layout_height, component_height)

        generator_ids = set(int(bus_id) for bus_id in self._net.gen.bus)
        load_ids = set(int(bus_id) for bus_id in self._net.load.bus)
        buses = []
        for bus_id, bus in self._net.bus.iterrows():
            bus_id = int(bus_id)
            x, y = bus_positions[bus_id]
            kind = "reference" if bus_id in reference_ids else "generator" if bus_id in generator_ids else "load" if bus_id in load_ids else "bus"
            name = bus["name"]
            buses.append({
                "id": bus_id,
                "name": str(name) if pd.notna(name) and str(name).strip() else f"Barra {bus_id}",
                "kv": float(bus.vn_kv),
                "kind": kind,
                "x": x,
                "y": y,
            })

        lines = [{
            "from": int(row.from_bus),
            "to": int(row.to_bus),
            "name": str(row.name or f"Linha {row.Index}"),
        } for row in line_rows]
        transformers = [{
            "from": int(row.hv_bus),
            "to": int(row.lv_bus),
            "name": str(row.name or f"Trafo {row.Index}"),
        } for row in trafo_rows]
        return json.dumps({
            "buses": buses,
            "lines": lines,
            "transformers": transformers,
            "layoutWidth": max(layout_width, 1),
            "layoutHeight": max(layout_height, 1),
        }, ensure_ascii=True)

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
    def readmeMarkdownContent(self): return self._readme_content


# -----------------------------------------------------------------------------
# 2. INTERFACE QML: smart_grid_power_system_unifilar.qml

def main():
    app = QApplication(sys.argv)
    engine = QQmlApplicationEngine()

    smart_engine = SmartGridStudioEngine()
    smart_engine.setParent(engine)
    engine.rootContext().setContextProperty("smartEngine", smart_engine)

    qml_path = os.path.join(os.path.dirname(__file__), "smart_grid_power_system_unifilar.qml")
    engine.load(QUrl.fromLocalFile(qml_path))
    if not engine.rootObjects():
        print(f"[ERRO FATAL] Falha ao carregar a interface QML: {qml_path}")
        sys.exit(-1)

    print("[OK] Smart Grid Studio ANAREDE/Pandapower com diagrama unifilar iniciado.")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()