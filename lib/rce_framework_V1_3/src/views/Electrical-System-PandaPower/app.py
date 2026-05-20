import sys
import traceback
import pandas as pd
import pandapower as pp
import pandapower.networks as pn
import pandapower.plotting as plot
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.figure import Figure
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QListWidget, QListWidgetItem, QPushButton,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QSplitter, QTextEdit, QMessageBox, QFrame, QStackedLayout,
    QFileDialog
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QColor
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from styles import AppStyles

# Desativa o modo interativo do Matplotlib para evitar pop-ups
plt.ioff()

# NOTE: QWebEngineView is required for Plotly charts. 
# You may need to install it separately:
# pip install PySide6-WebEngine
try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    import plotly.graph_objects as go
    import plotly.io as pio

    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# =========================== MODEL ===========================
class PowerSystemModel:
    """
    Model - Encapsulates the logic for power system analysis using Pandapower.
    Handles loading, simulating, and modifying the electrical network.
    """
    
    def __init__(self, network_name="case14"):
        """Initializes the model with a default network."""
        self.network_name = network_name
        self.net = self.load_network(network_name)

    def load_network(self, network_name):
        """Loads a standard test network from the pandapower library."""
        self.network_name = network_name
        try:
            if network_name == "case14":
                self.net = pn.case14()
            elif network_name == "case30":
                self.net = pn.case_ieee30()
            elif network_name == "case57":
                self.net = pn.case57()
            elif network_name == "case118":
                self.net = pn.case118()
            elif network_name == "New Network":
                self.net = pp.create_empty_network(name="New Network")
            else:
                self.net = pn.case14()
            
            if self.net and ('coords' not in self.net.bus_geodata.columns or self.net.bus_geodata.empty):
                 plot.create_generic_coordinates(self.net)

            if self.net:
                self.net.name = network_name
            return self.net
        except Exception:
            return pp.create_empty_network()

    def reset_network_state(self):
        """Resets the network to its original state."""
        if self.net:
            if not self.net.line.empty:
                self.net.line['in_service'] = True
            if not self.net.trafo.empty and 'in_service' in self.net.trafo:
                self.net.trafo['in_service'] = True

    def run_power_flow(self):
        """Executes the power flow calculation."""
        try:
            pp.runpp(self.net, algorithm="nr", numba=True)
            return True, "Fluxo de potência convergiu com sucesso."
        except pp.LoadflowNotConverged:
            return False, "Fluxo de Potência Não Convergiu."
        except Exception as e:
            return False, f"Ocorreu um erro inesperado: {e}"

    def apply_contingencies(self, contingencies):
        """Applies a list of contingencies to the network."""
        self.reset_network_state()
        for c_type, c_id in contingencies:
            if c_type == 'line' and c_id in self.net.line.index:
                self.net.line.loc[c_id, 'in_service'] = False
            elif c_type == 'trafo' and c_id in self.net.trafo.index:
                self.net.trafo.loc[c_id, 'in_service'] = False

class ResultsRepository:
    """Repository for fetching and formatting simulation results."""
    
    def __init__(self, net):
        if net is None or not hasattr(net, 'res_bus') or net.res_bus.empty:
            raise ValueError("A rede não foi simulada ou não contém resultados.")
        self.net = net

    def get_kpis(self):
        """Calculates and returns key performance indicators (KPIs)."""
        voltage_violations = ((self.net.res_bus.vm_pu > self.net.bus.max_vm_pu) | 
                              (self.net.res_bus.vm_pu < self.net.bus.min_vm_pu)).sum()
        line_overloads = (self.net.res_line.loading_percent > 100).sum()
        trafo_overloads = 0
        if hasattr(self.net, 'res_trafo') and not self.net.res_trafo.empty:
            trafo_overloads = (self.net.res_trafo.loading_percent > 100).sum()

        return {
            "total_load_mw": self.net.res_load.p_mw.sum(),
            "total_gen_mw": self.net.res_gen.p_mw.sum() + abs(self.net.res_bus.p_mw[self.net.ext_grid.bus[0]]),
            "voltage_violations": int(voltage_violations),
            "overloads": int(line_overloads + trafo_overloads)
        }

    def get_bus_voltage_data(self):
        df = self.net.res_bus[['vm_pu']].copy().round(4)
        return df.reset_index().rename(columns={'index': 'Barra', 'vm_pu': 'Tensão (p.u.)'})

    def get_line_loading_data(self):
        df = self.net.res_line[['loading_percent']].copy().round(2)
        return df.reset_index().rename(columns={'index': 'Linha', 'loading_percent': 'Carregamento (%)'})

    def get_trafo_loading_data(self):
        if not hasattr(self.net, 'res_trafo') or self.net.res_trafo.empty:
            return pd.DataFrame(columns=['Transformador', 'Carregamento (%)'])
        df = self.net.res_trafo[['loading_percent']].copy().round(2)
        return df.reset_index().rename(columns={'index': 'Transformador', 'loading_percent': 'Carregamento (%)'})

    def get_line_power_flow_data(self):
        """Returns active and reactive power flow for lines."""
        df = self.net.res_line[['p_from_mw', 'q_from_mvar']].copy().round(3)
        return df.reset_index().rename(columns={'index': 'Linha', 'p_from_mw': 'Potência Ativa (MW)', 'q_from_mvar': 'Potência Reativa (MVAr)'})

# =========================== VIEW ===========================
class NetworkCanvas(FigureCanvas):
    """Matplotlib canvas for plotting the power grid."""
    
    def __init__(self, parent=None, width=8, height=8, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi, tight_layout=True)
        super().__init__(self.fig)
        self.ax = self.fig.add_subplot(111)
        self.current_theme = 'dark'
        self.net = None

    def plot_network(self, net):
        """Plots the network, highlighting out-of-service elements and adding a legend."""
        self.net = net
        self.ax.clear()
        self.fig.set_facecolor("#f0f2f6")
        self.ax.set_facecolor("#f0f2f6")
        title_color, legend_text_color = '#333', '#333'

        try:
            if not net or net.bus.empty:
                self.ax.text(0.5, 0.5, "Nenhuma rede carregada ou rede vazia.", ha='center', va='center', color=title_color)
                self.draw()
                return

            title = f"Diagrama da Rede: {net.name.upper()}"

            # --- Determine Bus Colors ---
            gen_buses = set(net.gen.bus) if not net.gen.empty else set()
            load_buses = set(net.load.bus) if not net.load.empty else set()

            bus_colors = []
            for bus_idx in net.bus.index:
                is_gen = bus_idx in gen_buses
                is_load = bus_idx in load_buses
                if is_gen and is_load: bus_colors.append("purple")
                elif is_gen: bus_colors.append("green")
                elif is_load: bus_colors.append("orange")
                else: bus_colors.append("blue")

            # --- Create Collections ---
            bc = plot.create_bus_collection(net, buses=net.bus.index, size=0.05, color=bus_colors, zorder=10)
            self.ax.add_collection(bc)

            if hasattr(net, 'bus_geodata') and not net.bus_geodata.empty:
                for i, bus in net.bus_geodata.iterrows():
                    self.ax.text(bus.x, bus.y + 0.02, str(i), fontsize=8, weight='bold', ha='center', va='bottom', color='navy', zorder=11)

            # --- Prepare Legend Handles ---
            bus_handles = [
                Line2D([0], [0], marker='o', color='w', label='Barra (Transfer)', markerfacecolor='blue', markersize=8),
                Line2D([0], [0], marker='o', color='w', label='Barra (Geração)', markerfacecolor='green', markersize=8),
                Line2D([0], [0], marker='o', color='w', label='Barra (Carga)', markerfacecolor='orange', markersize=8),
                Line2D([0], [0], marker='o', color='w', label='Barra (Geração/Carga)', markerfacecolor='purple', markersize=8)
            ]
            line_handles = []

            if not net.line.empty:
                line_vns = net.bus.loc[net.line.from_bus, 'vn_kv'].values
                vn_kv_unique = sorted(pd.unique(line_vns))
                cmap = plt.get_cmap('viridis', len(vn_kv_unique) + 1)
                colors = {v: cmap(i) for i, v in enumerate(vn_kv_unique)}

                for v_kv, color in colors.items():
                    lines_at_v = net.line.index[line_vns == v_kv]
                    in_service_lines = net.line.index[net.line.in_service & (net.line.index.isin(lines_at_v))]
                    if not in_service_lines.empty:
                        lc = plot.create_line_collection(net, lines=in_service_lines, color=color, use_bus_geodata=True, linewidths=1.5)
                        self.ax.add_collection(lc)
                    line_handles.append(Line2D([0], [0], color=color, lw=2, label=f'{v_kv:.1f} kV'))

                oos_lines = net.line.index[~net.line.in_service]
                if not oos_lines.empty:
                    lc_oos = plot.create_line_collection(net, lines=oos_lines, color="r", linestyle="--", linewidths=1.5)
                    self.ax.add_collection(lc_oos)
                    if not any(h.get_label() == 'Fora de Serviço' for h in line_handles):
                         line_handles.append(Line2D([0], [0], color='r', linestyle='--', lw=2, label='Fora de Serviço'))

            if not net.trafo.empty:
                in_service_trafos = net.trafo.index[net.trafo.in_service]
                oos_trafos = net.trafo.index[~net.trafo.in_service]
                if not in_service_trafos.empty:
                    tc = plot.create_trafo_collection(net, trafos=in_service_trafos, color='k', zorder=5)
                    for collection in tc if isinstance(tc, (list, tuple)) else [tc]:
                        if collection: self.ax.add_collection(collection)
                if not oos_trafos.empty:
                    tc_oos = plot.create_trafo_collection(net, trafos=oos_trafos, color='r', linestyle="--", zorder=5)
                    for collection in tc_oos if isinstance(tc_oos, (list, tuple)) else [tc_oos]:
                        if collection: self.ax.add_collection(collection)
                    if not any(h.get_label() == 'Fora de Serviço' for h in line_handles):
                        line_handles.append(Line2D([0], [0], color='r', linestyle='--', lw=2, label='Fora de Serviço'))

            self.ax.set_title(title, fontsize=14, weight='bold', color=title_color)
            
            # --- Create Organized Legend ---
            legend_elements = []
            if bus_handles:
                legend_elements.append(Line2D([0], [0], marker='None', color='None', label='Info Barras'))
                legend_elements.extend(bus_handles)
            
            if line_handles:
                if legend_elements: # Add a spacer
                    legend_elements.append(Line2D([0], [0], marker='None', color='None', label=''))
                legend_elements.append(Line2D([0], [0], marker='None', color='None', label='Info Linhas'))
                legend_elements.extend(line_handles)

            if legend_elements:
                legend = self.ax.legend(handles=legend_elements, title="Legenda", labelcolor=legend_text_color)
                legend.get_frame().set_facecolor('#ffffff')
                legend.get_frame().set_edgecolor('#cccccc')
                # Make titles bold
                for text in legend.get_texts():
                    if text.get_text() in ['Info Barras', 'Info Linhas']:
                        text.set_fontweight('bold')
            
            self.ax.autoscale_view()
            self.ax.set_xticks([])
            self.ax.set_yticks([])
            self.ax.set_aspect('auto')

        except Exception as e:
            print("--- ERRO AO PLOTAR A REDE ---")
            traceback.print_exc()
            print("-----------------------------")
            self.ax.text(0.5, 0.5, f"Erro ao plotar a rede:\n{e}", ha='center', va='center', color=title_color)
        
        self.draw()
        plt.close('all')

    def update_theme_colors(self, theme):
        self.current_theme = theme
        self.plot_network(self.net)

class MetricsWidget(QWidget):
    """Widget to display KPIs in styled cards."""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(0,0,0,0)
        self.metric_cards = {}
        titles = {"load": "Carga Total (MW)", "gen": "Geração Total (MW)", "voltage": "Violações de Tensão", "overload": "Sobrecargas"}
        for key, title in titles.items():
            card = self._create_metric_card(title, "0.00")
            layout.addWidget(card)
            self.metric_cards[key] = card

    def _create_metric_card(self, title, value):
        card = QGroupBox(title)
        layout = QVBoxLayout(card)
        value_label = QLabel(value)
        value_label.setObjectName("value_label")
        layout.addWidget(value_label)
        layout.addStretch()
        return card

    def update_metrics(self, kpis):
        values = {"load": f"{kpis['total_load_mw']:.2f}", "gen": f"{kpis['total_gen_mw']:.2f}", "voltage": f"{kpis['voltage_violations']}", "overload": f"{kpis['overloads']}"}
        for key, value in values.items():
            value_label = self.metric_cards[key].findChild(QLabel, "value_label")
            if value_label: value_label.setText(str(value))

    def update_theme_colors(self, theme):
        for key, card in self.metric_cards.items():
            if theme == 'light':
                card.setStyleSheet("QGroupBox { background-color: white; border: 1px solid #ddd; border-radius: 8px; margin-top: 10px; font-size: 11px; font-weight: bold; color: #555; } QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 5px; left: 10px; } ")
                value_label = card.findChild(QLabel, "value_label")
                if value_label: value_label.setStyleSheet("font-size: 22px; color: #000; font-weight: bold; padding-top: 5px;")
            else:
                card.setStyleSheet("QGroupBox { background-color: #343a40; border: 1px solid #495057; border-radius: 8px; margin-top: 10px; font-size: 11px; font-weight: bold; color: #f8f9fa; } QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 5px; left: 10px; } ")
                value_label = card.findChild(QLabel, "value_label")
                if value_label: value_label.setStyleSheet("font-size: 22px; color: #f8f9fa; font-weight: bold; padding-top: 5px;")

class PlotlyWidget(QWebEngineView if PLOTLY_AVAILABLE else QTextEdit):
    """Widget to display Plotly charts."""
    def __init__(self):
        super().__init__()
        self.current_theme = 'dark' # Default theme
        if not PLOTLY_AVAILABLE:
            self.setReadOnly(True)
            self.setText("Plotly não disponível. Instale 'PySide6-WebEngine'.")
        else:
            self.setHtml(self._get_html_template())

    def _get_html_template(self):
        bg_color = "#f0f2f6" if self.current_theme == 'light' else "#343a40"
        return f"<html><body style='background-color:{bg_color};'></body></html>"

    def plot_chart(self, fig):
        if PLOTLY_AVAILABLE:
            if self.current_theme == 'dark':
                fig.update_layout(paper_bgcolor='#343a40', plot_bgcolor='#343a40', font=dict(color='#f8f9fa'), title_font_color='#f8f9fa', xaxis=dict(gridcolor='#495057', zerolinecolor='#495057'), yaxis=dict(gridcolor='#495057', zerolinecolor='#495057'))
            else:
                fig.update_layout(paper_bgcolor='#f0f2f6', plot_bgcolor='#f0f2f6', font=dict(color='#333'), title_font_color='#333', xaxis=dict(gridcolor='#d0d0d0', zerolinecolor='#d0d0d0'), yaxis=dict(gridcolor='#d0d0d0', zerolinecolor='#d0d0d0'))
            self.setHtml(pio.to_html(fig, full_html=False, include_plotlyjs='cdn'))

    def clear(self):
        if PLOTLY_AVAILABLE: self.setHtml(self._get_html_template())

    def update_theme_colors(self, theme):
        self.current_theme = theme
        if PLOTLY_AVAILABLE: self.setHtml(self._get_html_template())

class SidebarWidget(QWidget):
    """Sidebar widget with all simulation controls."""
    
    network_changed = Signal(str)
    contingencies_changed = Signal(list)
    run_simulation_requested = Signal()
    theme_toggle_requested = Signal()
    
    def __init__(self):
        super().__init__()
        self.current_theme = 'dark'
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        title = QLabel("Parâmetros da Simulação")
        title.setObjectName("SidebarTitle")
        layout.addWidget(title)
        
        network_group = QGroupBox("Seleção da Rede Elétrica")
        network_layout = QVBoxLayout(network_group)
        self.network_combo = QComboBox()
        self.network_combo.addItems(["case14", "case30", "case57", "case118", "New Network"])
        network_layout.addWidget(self.network_combo)
        layout.addWidget(network_group)
        
        self.contingency_group = QGroupBox("Análise de Contingência (N-k)")
        contingency_layout = QVBoxLayout(self.contingency_group)
        self.element_list = QListWidget()
        self.element_list.setSelectionMode(QListWidget.NoSelection)
        contingency_layout.addWidget(self.element_list)
        layout.addWidget(self.contingency_group)

        self.run_button = QPushButton("Executar Fluxo de Potência")
        self.run_button.setStyleSheet("QPushButton { background-color: #28a745; color: white; padding: 8px; border-radius: 5px; font-weight: bold; } QPushButton:disabled { background-color: #9E9E9E; }")
        layout.addWidget(self.run_button)

        self.theme_toggle_button = QPushButton("Alternar Tema")
        self.theme_toggle_button.setObjectName("ThemeToggle")
        layout.addWidget(self.theme_toggle_button)
        
        layout.addStretch()
        
        self.network_combo.currentTextChanged.connect(self.network_changed.emit)
        self.element_list.itemClicked.connect(self._on_item_clicked)
        self.run_button.clicked.connect(self.run_simulation_requested.emit)
        self.theme_toggle_button.clicked.connect(self.theme_toggle_requested.emit)
        self.update_theme_colors(self.current_theme)

    def update_theme_colors(self, theme):
        self.current_theme = theme
        title = self.findChild(QLabel, "SidebarTitle")
        if title:
            title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {{'#f8f9fa' if theme == 'dark' else '#333'}}; ")

        for i in range(self.element_list.count()):
            item = self.element_list.item(i)
            self._update_item_visuals(item, item.checkState() == Qt.Checked)

    def _update_item_visuals(self, item, is_checked):
        if self.current_theme == 'light':
            bg_color = QColor("#d4edda") if is_checked else QColor("white")
            text_color = QColor("black")
        else: # dark
            bg_color = QColor("#2a9d8f") if is_checked else QColor("#495057")
            text_color = QColor("white")
        item.setBackground(bg_color)
        item.setForeground(text_color)

    def _on_item_clicked(self, item):
        new_state = Qt.Checked if item.checkState() == Qt.Unchecked else Qt.Unchecked
        item.setCheckState(new_state)
        self._update_item_visuals(item, new_state == Qt.Checked)
        self._emit_contingencies()

    def _emit_contingencies(self):
        contingencies = []
        for i in range(self.element_list.count()):
            item = self.element_list.item(i)
            if item.checkState() == Qt.Checked:
                contingencies.append(item.data(Qt.UserRole))
        self.contingencies_changed.emit(contingencies)

    def update_element_list(self, net):
        self.element_list.itemClicked.disconnect(self._on_item_clicked)
        self.element_list.clear()
        if net and not net.line.empty:
            for idx, row in net.line.iterrows():
                item = QListWidgetItem(f"[L] Linha {idx} ({row.from_bus}↔{row.to_bus})")
                item.setData(Qt.UserRole, ('line', idx))
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Unchecked)
                self.element_list.addItem(item)
                self._update_item_visuals(item, False)
        if net and not net.trafo.empty:
            for idx, row in net.trafo.iterrows():
                item = QListWidgetItem(f"[T] Trafo {idx} ({row.hv_bus}↔{row.lv_bus})")
                item.setData(Qt.UserRole, ('trafo', idx))
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Unchecked)
                self.element_list.addItem(item)
                self._update_item_visuals(item, False)
        self.element_list.itemClicked.connect(self._on_item_clicked)

    def set_run_button_loading(self, is_loading):
        if is_loading:
            self.run_button.setText("Calculando...")
            self.run_button.setEnabled(False)
        else:
            self.run_button.setText("Executar Fluxo de Potência")
            self.run_button.setEnabled(True)

class LoadingWidget(QFrame):
    """A semi-transparent overlay widget to indicate loading."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 0.6); border-radius: 10px;")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        self.label = QLabel("Calculando Fluxo de Potência...", self)
        self.label.setStyleSheet("color: white; font-size: 20px; font-weight: bold; background: transparent;")
        layout.addWidget(self.label)

class NewNetworkEditor(QWidget):
    """Widget for creating and editing a new network."""
    build_network_requested = Signal()
    import_requested = Signal()
    export_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # --- Action Buttons ---
        button_layout = QHBoxLayout()
        self.import_button = QPushButton("📥 Importar de Excel")
        self.export_button = QPushButton("📤 Exportar para Excel")
        self.build_button = QPushButton("🛠️ Construir Rede a partir das Tabelas")
        self.build_button.setStyleSheet("background-color: #007bff; color: white; font-weight: bold; padding: 8px; border-radius: 5px;")
        button_layout.addWidget(self.import_button)
        button_layout.addWidget(self.export_button)
        button_layout.addStretch()
        button_layout.addWidget(self.build_button)
        main_layout.addLayout(button_layout)

        # --- Tables in Tabs ---
        self.editor_tabs = QTabWidget()
        self.tables = {}

        headers = {
            "bus": ["name", "vn_kv", "type", "zone", "in_service"],
            "line": ["name", "from_bus", "to_bus", "length_km", "std_type", "in_service"],
            "trafo": ["name", "hv_bus", "lv_bus", "std_type", "in_service"],
            "gen": ["name", "bus", "p_mw", "vm_pu", "in_service"],
            "load": ["name", "bus", "p_mw", "q_mvar", "in_service"],
        }

        for name, header_list in headers.items():
            table = QTableWidget()
            table.setColumnCount(len(header_list))
            table.setHorizontalHeaderLabels(header_list)
            table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            table.setRowCount(5) # Start with 5 empty rows
            self.tables[name] = table
            self.editor_tabs.addTab(table, name.capitalize())

        main_layout.addWidget(self.editor_tabs)

        self.import_button.clicked.connect(self.import_requested.emit)
        self.export_button.clicked.connect(self.export_requested.emit)
        self.build_button.clicked.connect(self.build_network_requested.emit)

    def get_dataframes(self):
        dfs = {}
        for name, table in self.tables.items():
            df = pd.DataFrame(columns=self.get_table_headers(table))
            for row in range(table.rowCount()):
                if all(table.item(row, col) is None or table.item(row, col).text().strip() == '' for col in range(table.columnCount())):
                    continue
                row_data = [table.item(row, col).text() if table.item(row, col) else '' for col in range(table.columnCount())]
                df.loc[len(df)] = row_data
            dfs[name] = df
        return dfs

    def load_dataframes(self, dfs):
        for name, df in dfs.items():
            if name in self.tables:
                table = self.tables[name]
                table.clearContents()
                table.setRowCount(0)
                table.setRowCount(len(df))
                table.setColumnCount(len(df.columns))
                table.setHorizontalHeaderLabels(df.columns.tolist())
                for i, row in enumerate(df.itertuples(index=False)):
                    for j, value in enumerate(row):
                        table.setItem(i, j, QTableWidgetItem(str(value)))
                table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def get_table_headers(self, table):
        return [table.horizontalHeaderItem(i).text() for i in range(table.columnCount())]

class MainWindow(QMainWindow):
    """The main application window."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("⚡ Dashboard de Análise de Contingências Elétricas")
        self.setGeometry(100, 100, 1600, 900)
        self.current_theme = 'dark'
        self.network_canvas = NetworkCanvas(self)
        self.setup_ui()
        self.apply_theme()

    def apply_theme(self):
        stylesheet = AppStyles.DARK_MODE_STYLESHEET if self.current_theme == 'dark' else AppStyles.LIGHT_MODE_STYLESHEET
        self.setStyleSheet(stylesheet)
        self.sidebar.update_theme_colors(self.current_theme)
        self.metrics_widget.update_theme_colors(self.current_theme)
        self.network_canvas.update_theme_colors(self.current_theme)
        if PLOTLY_AVAILABLE:
            self.voltage_plot.update_theme_colors(self.current_theme)
            self.line_loading_plot.update_theme_colors(self.current_theme)
            self.trafo_loading_plot.update_theme_colors(self.current_theme)
            self.line_p_flow_plot.update_theme_colors(self.current_theme)
            self.line_q_flow_plot.update_theme_colors(self.current_theme)
        self.update_status(self.status_label.text().strip('✅❌ℹ️ '), self.status_label.property("style_type"))

    def toggle_theme(self):
        self.current_theme = 'light' if self.current_theme == 'dark' else 'dark'
        self.apply_theme()

    def create_tab(self, plot_widget, table_widget):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(plot_widget)
        splitter.addWidget(table_widget)
        splitter.setSizes([400, 200])
        layout.addWidget(splitter)
        return tab

    def setup_tabs(self):
        """Configures the tabs for detailed analysis."""
        diagram_tab = QWidget()
        diagram_layout = QVBoxLayout(diagram_tab)
        diagram_layout.addWidget(self.network_canvas)
        self.tabs.addTab(diagram_tab, "🗺️ Diagrama da Rede")

        self.voltage_plot = PlotlyWidget()
        self.line_loading_plot = PlotlyWidget()
        self.trafo_loading_plot = PlotlyWidget()
        self.line_p_flow_plot = PlotlyWidget()
        self.line_q_flow_plot = PlotlyWidget()

        self.voltage_table = QTableWidget()
        self.line_loading_table = QTableWidget()
        self.trafo_loading_table = QTableWidget()
        self.power_flow_table = QTableWidget()

        self.tabs.addTab(self.create_tab(self.voltage_plot, self.voltage_table), "📊 Tensões nas Barras")
        self.tabs.addTab(self.create_tab(self.line_loading_plot, self.line_loading_table), "📈 Carreg. Linhas")
        self.tabs.addTab(self.create_tab(self.trafo_loading_plot, self.trafo_loading_table), "📈 Carreg. Trafos")
        
        power_flow_tab = QWidget()
        pf_layout = QVBoxLayout(power_flow_tab)
        pf_splitter_plots = QSplitter(Qt.Horizontal)
        pf_splitter_plots.addWidget(self.line_p_flow_plot)
        pf_splitter_plots.addWidget(self.line_q_flow_plot)
        pf_splitter_main = QSplitter(Qt.Vertical)
        pf_splitter_main.addWidget(pf_splitter_plots)
        pf_splitter_main.addWidget(self.power_flow_table)
        pf_splitter_main.setSizes([400, 200])
        pf_layout.addWidget(pf_splitter_main)
        self.tabs.addTab(power_flow_tab, "⚡ Fluxo de Potência")

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Root layout for stacking UI and loading screen
        self.root_stack = QStackedLayout(central_widget)

        # Main UI container
        main_ui_widget = QWidget()
        main_layout = QHBoxLayout(main_ui_widget)
        
        self.sidebar = SidebarWidget()
        self.sidebar.setMaximumWidth(350)
        main_layout.addWidget(self.sidebar)

        main_content_area = QWidget()
        main_content_layout = QVBoxLayout(main_content_area)
        main_layout.addWidget(main_content_area)

        self.status_label = QLabel("Carregando rede inicial...")
        self.status_label.setProperty("style_type", "info")
        main_content_layout.addWidget(self.status_label)
        self.metrics_widget = MetricsWidget()
        main_content_layout.addWidget(self.metrics_widget)

        main_vertical_splitter = QSplitter(Qt.Vertical)
        main_content_layout.addWidget(main_vertical_splitter)

        # --- View Stack for Results vs. Editor ---
        self.view_stack = QStackedLayout()
        view_container = QWidget()
        view_container.setLayout(self.view_stack)
        main_vertical_splitter.addWidget(view_container)

        # View 1: Detailed Results (Tabs)
        detailed_results_group = QGroupBox("Resultados Detalhados da Simulação")
        detailed_results_layout = QVBoxLayout(detailed_results_group)
        self.tabs = QTabWidget()
        self.setup_tabs()
        detailed_results_layout.addWidget(self.tabs)
        self.view_stack.addWidget(detailed_results_group)

        # View 2: New Network Editor
        self.new_network_editor = NewNetworkEditor()
        self.view_stack.addWidget(self.new_network_editor)

        # Network Description Area
        network_description_group = QGroupBox("Descrição da Rede e Componentes")
        network_description_layout = QVBoxLayout(network_description_group)
        self.network_description_text = QTextEdit()
        self.network_description_text.setReadOnly(True)
        network_description_layout.addWidget(self.network_description_text)
        main_vertical_splitter.addWidget(network_description_group)
        main_vertical_splitter.setSizes([700, 300])

        # Add main UI and loading widget to the root stack
        self.root_stack.addWidget(main_ui_widget)
        self.loading_widget = LoadingWidget()
        self.root_stack.addWidget(self.loading_widget)

        self.sidebar.theme_toggle_requested.connect(self.toggle_theme)

    def show_loading_overlay(self, show):
        self.root_stack.setCurrentIndex(1 if show else 0)

    def show_view(self, name):
        self.view_stack.setCurrentIndex(1 if name == "new_network" else 0)
        self.sidebar.contingency_group.setVisible(name != "new_network")

    def update_status(self, text, style_type='info'):
        base_style = "padding: 10px; border-radius: 5px; font-weight: bold;"
        self.status_label.setProperty("style_type", style_type)
        if style_type == 'success':
            self.status_label.setText(f"✅ {text}")
            self.status_label.setStyleSheet(f"QLabel {{ {base_style} background-color: #d4edda; border: 1px solid #c3e6cb; color: #155724; }}")
        elif style_type == 'error':
            self.status_label.setText(f"❌ {text}")
            self.status_label.setStyleSheet(f"QLabel {{ {base_style} background-color: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }}")
        else:
            self.status_label.setText(f"ℹ️ {text}")
            self.status_label.setStyleSheet(f"QLabel {{ {base_style} background-color: #e2e3e5; border: 1px solid #d6d8db; color: #383d41; }}")

    def update_table(self, table_widget, df):
        table_widget.clearContents()
        table_widget.setRowCount(0)
        if df.empty: return
        table_widget.setRowCount(len(df))
        table_widget.setColumnCount(len(df.columns))
        table_widget.setHorizontalHeaderLabels(df.columns.tolist())
        for i, row in enumerate(df.itertuples(index=False)):
            for j, value in enumerate(row):
                table_widget.setItem(i, j, QTableWidgetItem(str(value)))
        table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def update_network_description(self, net):
        if not net:
            self.network_description_text.setHtml("<h3>Nenhuma rede carregada.</h3>")
            return

        description = f"<h3>Detalhes da Rede: {net.name.upper()}</h3>"
        description += "<p>Esta seção fornece uma visão geral dos componentes da rede.</p>"
        def create_html_list(title, count, items):
            s = f"<h4>{title} ({count}):</h4>"
            if not items: return s + "<p>Nenhum componente definido.</p>"
            s += "<ul>" + "".join([f"<li>{item}</li>" for item in items]) + "</ul>"
            return s

        bus_items = [f"<b>Barra {idx}:</b> Tensão Nominal = {bus.vn_kv} kV" for idx, bus in net.bus.iterrows()]
        line_items = [f"<b>Linha {idx}:</b> De Barra {line.from_bus} para Barra {line.to_bus}, Comp. = {line.length_km:.2f} km, Tipo = {line.std_type}" for idx, line in net.line.iterrows()]
        trafo_items = [f"<b>Trafo {idx}:</b> HV {trafo.hv_bus} ↔ LV {trafo.lv_bus}, Tipo = {trafo.std_type}" for idx, trafo in net.trafo.iterrows()]
        load_items = [f"<b>Carga {idx}</b> @ Barra {load.bus}: P={load.p_mw:.2f} MW, Q={load.q_mvar:.2f} MVAr" for idx, load in net.load.iterrows()]
        gen_items = [f"<b>Gerador {idx}</b> @ Barra {gen.bus}: P={gen.p_mw:.2f} MW" for idx, gen in net.gen.iterrows()]
        ext_grid_items = [f"<b>Grid Externo {idx}</b> @ Barra {ext_grid.bus}: Max P={ext_grid.max_p_mw:.2f} MW, Min P={ext_grid.min_p_mw:.2f} MW" for idx, ext_grid in net.ext_grid.iterrows()]

        description += create_html_list("Barras", len(net.bus), bus_items)
        description += create_html_list("Linhas", len(net.line), line_items)
        description += create_html_list("Transformadores", len(net.trafo), trafo_items)
        description += create_html_list("Cargas", len(net.load), load_items)
        description += create_html_list("Geradores", len(net.gen), gen_items)
        description += create_html_list("Grid Externo", len(net.ext_grid), ext_grid_items)
        self.network_description_text.setHtml(description)

# =========================== CONTROLLER ===========================
class PowerSystemController:
    """Controller - Manages interaction between Model and View."""
    
    def __init__(self):
        self.view = MainWindow()
        self.model = PowerSystemModel()
        self.current_contingencies = []
        self.setup_connections()
        self.load_network(self.view.sidebar.network_combo.currentText())

    def setup_connections(self):
        self.view.sidebar.network_changed.connect(self.load_network)
        self.view.sidebar.contingencies_changed.connect(self.prepare_contingencies)
        self.view.sidebar.run_simulation_requested.connect(self.run_simulation_with_delay)
        self.view.sidebar.theme_toggle_requested.connect(self.handle_theme_toggle)
        self.view.new_network_editor.import_requested.connect(self.import_network_from_excel)
        self.view.new_network_editor.export_requested.connect(self.export_network_to_excel)
        self.view.new_network_editor.build_network_requested.connect(self.build_network_from_editor)

    def handle_theme_toggle(self):
        self.view.toggle_theme()

    def show(self):
        self.view.show()

    def load_network(self, network_name):
        self.model.load_network(network_name)
        self.view.show_view("new_network" if network_name == "New Network" else "results")
        self.clear_results()
        self.view.sidebar.update_element_list(self.model.net)
        self.view.update_network_description(self.model.net)
        self.view.network_canvas.plot_network(self.model.net)
        if network_name == "New Network":
            self.view.update_status("Editor de Rede pronto. Importe ou preencha os dados.", 'info')
        else:
            self.prepare_contingencies([])

    def prepare_contingencies(self, contingencies):
        self.current_contingencies = contingencies
        self.model.apply_contingencies(self.current_contingencies)
        self.clear_results()
        self.view.network_canvas.plot_network(self.model.net)

    def clear_results(self):
        self.view.update_status("Pronto para simular. Pressione o botão para executar.", 'info')
        self.view.metrics_widget.update_metrics({"total_load_mw": 0, "total_gen_mw": 0, "voltage_violations": 0, "overloads": 0})
        self.view.update_table(self.view.voltage_table, pd.DataFrame())
        self.view.update_table(self.view.line_loading_table, pd.DataFrame())
        self.view.update_table(self.view.trafo_loading_table, pd.DataFrame())
        self.view.update_table(self.view.power_flow_table, pd.DataFrame())
        if PLOTLY_AVAILABLE:
            self.view.voltage_plot.clear()
            self.view.line_loading_plot.clear()
            self.view.trafo_loading_plot.clear()
            self.view.line_p_flow_plot.clear()
            self.view.line_q_flow_plot.clear()

    def run_simulation_with_delay(self):
        self.view.sidebar.set_run_button_loading(True)
        self.view.show_loading_overlay(True)
        QTimer.singleShot(50, self.run_simulation)

    def run_simulation(self):
        try:
            if not self.model.net or self.model.net.bus.empty:
                self.view.update_status("Rede vazia. Carregue uma rede ou construa uma nova.", 'error')
                return

            self.model.apply_contingencies(self.current_contingencies)
            success, msg = self.model.run_power_flow()
            if success:
                self.view.update_status(msg, 'success')
                self.update_results_display()
            else:
                self.view.update_status(msg, 'error')
                self.clear_results()
                self.view.network_canvas.plot_network(self.model.net)
        except Exception as e:
            self.view.update_status(f"Erro crítico na simulação: {e}", 'error')
            traceback.print_exc()
        finally:
            self.view.sidebar.set_run_button_loading(False)
            self.view.show_loading_overlay(False)

    def update_results_display(self):
        try:
            repo = ResultsRepository(self.model.net)
            self.view.metrics_widget.update_metrics(repo.get_kpis())
            voltage_df = repo.get_bus_voltage_data()
            line_loading_df = repo.get_line_loading_data()
            trafo_loading_df = repo.get_trafo_loading_data()
            power_flow_df = repo.get_line_power_flow_data()

            self.view.update_table(self.view.voltage_table, voltage_df)
            self.view.update_table(self.view.line_loading_table, line_loading_df)
            self.view.update_table(self.view.trafo_loading_table, trafo_loading_df)
            self.view.update_table(self.view.power_flow_table, power_flow_df)

            if PLOTLY_AVAILABLE:
                self._update_plots(voltage_df, line_loading_df, trafo_loading_df, power_flow_df)
        except Exception as e:
            self.view.update_status(f"Erro ao processar resultados: {e}", 'error')
            traceback.print_exc()

    def _update_plots(self, voltage_df, line_df, trafo_df, power_flow_df):

        # Gráfico de Tensão nas barras
        if not voltage_df.empty:
            fig_v = go.Figure(data=[go.Bar(x=voltage_df['Barra'], y=voltage_df['Tensão (p.u.)'], marker_color='#1f77b4')])
            fig_v.add_hline(y=1.05, line_dash="dash", line_color="red"); fig_v.add_hline(y=0.95, line_dash="dash", line_color="red")
            fig_v.update_layout(title_text='Tensão nas Barras', yaxis_range=[0.7, 1.2])
            self.view.voltage_plot.plot_chart(fig_v)
        else:
            self.view.voltage_plot.clear()

        # Gráfico de Carregamento das Linhas
        if not line_df.empty:

            fig_l = go.Figure(data=[go.Bar(x=line_df['Linha'], y=line_df['Carregamento (%)'], marker_color='#ff7f0e')])

            fig_l.add_hline(y=1, line_dash="dash", line_color="red")
            
            #! Colocando limites de porcentagem corretamente
            fig_l.update_layout(title_text='Carregamento das Linhas (%) ', yaxis_range=[0, 2.5])
            #fig_l.update_layout(title_text='Carregamento das Linhas', yaxis_range=[0, max(50, line_df['Carregamento (%)'].max() * 1.1 if not line_df.empty else 50)])

            self.view.line_loading_plot.plot_chart(fig_l)

        else:
            self.view.line_loading_plot.clear()


        # Gráfico Carregamento de Trafos
        if not trafo_df.empty:
            fig_t = go.Figure(data=[go.Bar(x=trafo_df['Transformador'], y=trafo_df['Carregamento (%)'], marker_color='#2ca02c')])
            fig_t.add_hline(y=1, line_dash="dash", line_color="red")
            fig_l.update_layout(title_text='Carregamento dos Transformadores (%)', yaxis_range=[0, 2.0])
            #fig_t.update_layout(title_text='Carregamento dos Transformadores (%)', yaxis_range=[0, max(80, trafo_df['Carregamento (%)'].max() * 1.1 if not trafo_df.empty else 50)])
            self.view.trafo_loading_plot.plot_chart(fig_t)
        else:
            self.view.trafo_loading_plot.clear()

        # Gráfico de Fluxo de potencai
        if not power_flow_df.empty:
            fig_p = go.Figure(data=[go.Bar(x=power_flow_df['Linha'], y=power_flow_df['Potência Ativa (MW)'], name='P (MW)', marker_color='#d62728')])
            fig_p.update_layout(title_text='Fluxo de Potência Ativa (MW)')
            self.view.line_p_flow_plot.plot_chart(fig_p)
            fig_q = go.Figure(data=[go.Bar(x=power_flow_df['Linha'], y=power_flow_df['Potência Reativa (MVAr)'], name='Q (MVAr)', marker_color='#9467bd')])
            fig_q.update_layout(title_text='Fluxo de Potência Reativa (MVAr)')
            self.view.line_q_flow_plot.plot_chart(fig_q)
        else:
            self.view.line_p_flow_plot.clear()
            self.view.line_q_flow_plot.clear()

    def import_network_from_excel(self):
        path, _ = QFileDialog.getOpenFileName(self.view, "Importar Rede de Arquivo Excel", "", "Excel Files (*.xlsx)")
        if not path: return
        try:
            xls = pd.ExcelFile(path)
            dfs = {sheet_name: xls.parse(sheet_name, dtype=str) for sheet_name in xls.sheet_names}
            self.view.new_network_editor.load_dataframes(dfs)
            self.view.update_status(f"Dados importados de {path}", 'success')
        except Exception as e:
            self.view.update_status(f"Falha ao importar arquivo: {e}", 'error')
            traceback.print_exc()

    def export_network_to_excel(self):
        path, _ = QFileDialog.getSaveFileName(self.view, "Exportar Rede para Arquivo Excel", "minha_rede.xlsx", "Excel Files (*.xlsx)")
        if not path: return
        try:
            dfs = self.view.new_network_editor.get_dataframes()
            with pd.ExcelWriter(path) as writer:
                for name, df in dfs.items():
                    if not df.empty:
                        df.to_excel(writer, sheet_name=name, index=False)
            self.view.update_status(f"Rede exportada para {path}", 'success')
        except Exception as e:
            self.view.update_status(f"Falha ao exportar arquivo: {e}", 'error')
            traceback.print_exc()

    def build_network_from_editor(self):
        self.view.show_loading_overlay(True)
        QTimer.singleShot(50, self._build_network_task)

    def _build_network_task(self):
        try:
            self.view.update_status("Construindo rede a partir dos dados...", 'info')
            dfs = self.view.new_network_editor.get_dataframes()
            net = pp.create_empty_network(name="New Network")

            bus_df = dfs.get('bus')
            if bus_df is None or bus_df.empty:
                raise ValueError("A tabela 'bus' está vazia. Pelo menos uma barra é necessária.")

            bus_map = {name: i for i, name in enumerate(bus_df['name'])}
            for i, row in bus_df.iterrows():
                pp.create_bus(net, name=row['name'], vn_kv=float(row['vn_kv']), index=bus_map[row['name']], type=row.get('type', 'b'))

            def safe_cast(val, cast_fn, default=0):
                return cast_fn(val) if val and str(val).strip() else default

            for df_name, create_func, param_map in self._get_element_mappers(bus_map):
                df = dfs.get(df_name)
                if df is not None and not df.empty:
                    for _, row in df.iterrows():
                        params = {pp_key: safe_cast(row[df_key], type_fn) for pp_key, df_key, type_fn in param_map if df_key in row and pd.notna(row[df_key])}
                        params['name'] = row['name']
                        create_func(net, **params)

            self.model.net = net
            plot.create_generic_coordinates(self.model.net)
            self.view.sidebar.update_element_list(self.model.net)
            self.view.network_canvas.plot_network(self.model.net)
            self.view.update_network_description(self.model.net)
            self.view.update_status("Rede construída com sucesso! Pronta para simulação.", 'success')

        except Exception as e:
            self.view.update_status(f"Erro ao construir a rede: {e}", 'error')
            traceback.print_exc()
        finally:
            self.view.show_loading_overlay(False)

    def _get_element_mappers(self, bus_map):
        return [
            ('line', pp.create_line_from_parameters, [
                ('from_bus', 'from_bus', lambda x: bus_map[x]), ('to_bus', 'to_bus', lambda x: bus_map[x]),
                ('length_km', 'length_km', float), ('r_ohm_per_km', 'r_ohm_per_km', float),
                ('x_ohm_per_km', 'x_ohm_per_km', float), ('c_nf_per_km', 'c_nf_per_km', float),
                ('max_i_ka', 'max_i_ka', float), ('std_type', 'std_type', str)
            ]),
            ('gen', pp.create_gen, [
                ('bus', 'bus', lambda x: bus_map[x]), ('p_mw', 'p_mw', float), ('vm_pu', 'vm_pu', float)
            ]),
            ('load', pp.create_load, [
                ('bus', 'bus', lambda x: bus_map[x]), ('p_mw', 'p_mw', float), ('q_mvar', 'q_mvar', float)
            ]),
            ('trafo', pp.create_transformer_from_parameters, [
                ('hv_bus', 'hv_bus', lambda x: bus_map[x]), ('lv_bus', 'lv_bus', lambda x: bus_map[x]),
                ('sn_mva', 'sn_mva', float), ('vn_hv_kv', 'vn_hv_kv', float), ('vn_lv_kv', 'vn_lv_kv', float),
                ('vkr_percent', 'vkr_percent', float), ('vk_percent', 'vk_percent', float),
                ('pfe_kw', 'pfe_kw', float), ('i0_percent', 'i0_percent', float)
            ])
        ]

# =========================== MAIN ===========================
def main():
    """Main entry point for the application."""
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 9))

    if not PLOTLY_AVAILABLE:
        QMessageBox.warning(None, "Dependência Faltando", "O módulo 'PySide6-WebEngine' não foi encontrado. Os gráficos interativos não serão exibidos.\n\nPor favor, instale-o com: pip install PySide6-WebEngine")

    controller = PowerSystemController()
    controller.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
