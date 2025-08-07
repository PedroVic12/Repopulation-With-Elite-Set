import sys
import traceback
import pandas as pd
import pandapower as pp
import pandapower.networks as pn
import pandapower.plotting as plot
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.collections import PatchCollection
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QListWidget, QListWidgetItem, QPushButton,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QSplitter, QTextEdit, QMessageBox, QFrame, QStackedLayout
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QColor

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
            else:
                self.net = pn.case14()
            
            if 'coords' not in self.net.bus_geodata.columns:
                 plot.create_generic_coordinates(self.net)

            self.net.name = network_name
            return self.net
        except Exception:
            return pp.create_empty_network()

    def reset_network_state(self):
        """Resets the network to its original state."""
        if self.net:
            self.net.line['in_service'] = True
            if 'in_service' in self.net.trafo:
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
            "total_gen_mw": self.net.res_gen.p_mw.sum(),
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

    def plot_network(self, net):
        """Plots the network, highlighting out-of-service elements and adding a legend."""
        self.ax.clear()
        self.ax.set_facecolor("#f0f2f6")
        try:
            title = f"Diagrama da Rede: {net.name.upper()}"
            
            # --- Bus Collections (Corrected Size) ---
            bc = plot.create_bus_collection(net, size=0.05, color="b", zorder=10)
            self.ax.add_collection(bc)
            
            # --- Line Collections ---
            line_vns = net.bus.loc[net.line.from_bus, 'vn_kv'].values
            vn_kv_unique = sorted(pd.unique(line_vns))
            cmap = plt.get_cmap('viridis', len(vn_kv_unique) + 1)
            colors = {v: cmap(i) for i, v in enumerate(vn_kv_unique)}
            
            legend_elements = []
            
            # In-service lines
            for v_kv, color in colors.items():
                lines_at_v = net.line.index[line_vns == v_kv]
                in_service_lines = net.line.index[net.line.in_service & (net.line.index.isin(lines_at_v))]
                if not in_service_lines.empty:
                    lc = plot.create_line_collection(net, lines=in_service_lines, color=color, use_bus_geodata=True, linewidths=1.5)
                    self.ax.add_collection(lc)
                legend_elements.append(Line2D([0], [0], color=color, lw=2, label=f'{v_kv:.1f} kV'))

            # Out-of-service lines
            oos_lines = net.line.index[~net.line.in_service]
            if not oos_lines.empty:
                lc_oos = plot.create_line_collection(net, lines=oos_lines, color="r", linestyle="--", linewidths=1.5)
                self.ax.add_collection(lc_oos)
                if not any(h.get_label() == 'Fora de Serviço' for h in legend_elements):
                     legend_elements.append(Line2D([0], [0], color='r', linestyle='--', lw=2, label='Fora de Serviço'))

            # --- Transformer Collections (Corrected Size) ---
            if not net.trafo.empty:
                in_service_trafos = net.trafo.index[net.trafo.in_service]
                oos_trafos = net.trafo.index[~net.trafo.in_service]

                if not in_service_trafos.empty:
                    tc = plot.create_trafo_collection(net, trafos=in_service_trafos, color='k', zorder=5,)
                    for collection in tc if isinstance(tc, (list, tuple)) else [tc]:
                        if collection: self.ax.add_collection(collection)
                
                if not oos_trafos.empty:
                    tc_oos = plot.create_trafo_collection(net, trafos=oos_trafos, color='r', linestyle="--", zorder=5, )
                    for collection in tc_oos if isinstance(tc_oos, (list, tuple)) else [tc_oos]:
                        if collection: self.ax.add_collection(collection)

                    if not any(h.get_label() == 'Fora de Serviço' for h in legend_elements):
                        legend_elements.append(Line2D([0], [0], color='r', linestyle='--', lw=2, label='Fora de Serviço'))

            self.ax.set_title(title, fontsize=14, weight='bold')
            self.ax.legend(handles=legend_elements, title="Legenda")
            self.ax.autoscale_view()
            self.ax.set_xticks([])
            self.ax.set_yticks([])
            self.ax.set_aspect('equal')


        except Exception as e:
            print("--- ERRO AO PLOTAR A REDE ---")
            traceback.print_exc()
            print("-----------------------------")
            self.ax.text(0.5, 0.5, f"Erro ao plotar a rede:\n{e}", ha='center', va='center')
        
        self.draw()
        plt.close('all')

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
        card.setStyleSheet("QGroupBox { background-color: white; border: 1px solid #ddd; border-radius: 8px; margin-top: 10px; font-size: 11px; font-weight: bold; color: #555; } QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 5px; left: 10px; }")
        layout = QVBoxLayout(card)
        value_label = QLabel(value)
        value_label.setStyleSheet("font-size: 22px; color: #000; font-weight: bold; padding-top: 5px;")
        value_label.setObjectName("value_label")
        layout.addWidget(value_label)
        layout.addStretch()
        return card

    def update_metrics(self, kpis):
        values = {"load": f"{kpis['total_load_mw']:.2f}", "gen": f"{kpis['total_gen_mw']:.2f}", "voltage": f"{kpis['voltage_violations']}", "overload": f"{kpis['overloads']}"}
        for key, value in values.items():
            value_label = self.metric_cards[key].findChild(QLabel, "value_label")
            if value_label: value_label.setText(str(value))

class PlotlyWidget(QWebEngineView if PLOTLY_AVAILABLE else QTextEdit):
    """Widget to display Plotly charts."""
    def __init__(self):
        super().__init__()
        if not PLOTLY_AVAILABLE:
            self.setReadOnly(True)
            self.setText("Plotly não disponível. Instale 'PySide6-WebEngine'.")
        else:
            self.setHtml("<html><body style='background-color:#f0f2f6;'></body></html>")

    def plot_chart(self, fig):
        if PLOTLY_AVAILABLE: self.setHtml(pio.to_html(fig, full_html=False, include_plotlyjs='cdn'))

    def clear(self):
        if PLOTLY_AVAILABLE: self.setHtml("<html><body style='background-color:#f0f2f6;'></body></html>")

class SidebarWidget(QWidget):
    """Sidebar widget with all simulation controls."""
    
    network_changed = Signal(str)
    contingencies_changed = Signal(list)
    run_simulation_requested = Signal()
    
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        title = QLabel("Parâmetros da Simulação")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        layout.addWidget(title)
        
        network_group = QGroupBox("Seleção da Rede Elétrica")
        network_layout = QVBoxLayout(network_group)
        self.network_combo = QComboBox()
        self.network_combo.addItems(["case14", "case30", "case57", "case118"])
        network_layout.addWidget(self.network_combo)
        layout.addWidget(network_group)
        
        contingency_group = QGroupBox("Análise de Contingência (N-k)")
        contingency_layout = QVBoxLayout(contingency_group)
        self.element_list = QListWidget()
        self.element_list.setSelectionMode(QListWidget.NoSelection)
        contingency_layout.addWidget(self.element_list)
        layout.addWidget(contingency_group)

        self.run_button = QPushButton("Executar Fluxo de Potência")
        self.run_button.setStyleSheet("QPushButton { background-color: #28a745; color: white; padding: 8px; border-radius: 5px; font-weight: bold; } QPushButton:disabled { background-color: #9E9E9E; }")
        layout.addWidget(self.run_button)
        
        layout.addStretch()
        
        self.network_combo.currentTextChanged.connect(self.network_changed.emit)
        self.element_list.itemClicked.connect(self._on_item_clicked)
        self.run_button.clicked.connect(self.run_simulation_requested.emit)

    def _on_item_clicked(self, item):
        # Manually toggle the checkbox state and update visual feedback
        new_state = Qt.Checked if item.checkState() == Qt.Unchecked else Qt.Unchecked
        item.setCheckState(new_state)
        
        if new_state == Qt.Checked:
            item.setBackground(QColor("#d4edda")) # Light green for selected
        else:
            item.setBackground(QColor("white")) # Default white
            
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
        if net and not net.trafo.empty:
            for idx, row in net.trafo.iterrows():
                item = QListWidgetItem(f"[T] Trafo {idx} ({row.hv_bus}↔{row.lv_bus})")
                item.setData(Qt.UserRole, ('trafo', idx))
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Unchecked)
                self.element_list.addItem(item)
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
        self.hide()


class MainWindow(QMainWindow):
    """The main application window."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("⚡ Dashboard de Análise de Contingências Elétricas")
        self.setGeometry(100, 100, 1600, 900)
        self.setup_ui()
        self.apply_styles()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        splitter = QSplitter(Qt.Horizontal)
        self.sidebar = SidebarWidget()
        self.sidebar.setMaximumWidth(350)
        
        main_area_container = QWidget()
        self.stacked_layout = QStackedLayout(main_area_container)
        
        self.main_area_widget = QWidget()
        main_area_layout = QVBoxLayout(self.main_area_widget)
        
        self.status_label = QLabel("Carregando rede inicial...")
        main_area_layout.addWidget(self.status_label)
        self.metrics_widget = MetricsWidget()
        main_area_layout.addWidget(self.metrics_widget)
        content_splitter = QSplitter(Qt.Horizontal)
        left_panel = QGroupBox("Diagrama Topológico da Rede")
        left_layout = QVBoxLayout(left_panel)
        self.network_canvas = NetworkCanvas(self)
        left_layout.addWidget(self.network_canvas)
        right_panel = QGroupBox("Resultados Detalhados da Simulação")
        right_layout = QVBoxLayout(right_panel)
        self.tabs = QTabWidget()
        self.setup_tabs()
        right_layout.addWidget(self.tabs)
        content_splitter.addWidget(left_panel)
        content_splitter.addWidget(right_panel)
        content_splitter.setSizes([600, 800])
        main_area_layout.addWidget(content_splitter)
        
        self.loading_widget = LoadingWidget()
        self.stacked_layout.addWidget(self.main_area_widget)
        self.stacked_layout.addWidget(self.loading_widget)

        splitter.addWidget(self.sidebar)
        splitter.addWidget(main_area_container)
        splitter.setSizes([320, 1280])
        main_layout.addWidget(splitter)

    def show_loading_overlay(self, show):
        if show:
            self.stacked_layout.setCurrentWidget(self.loading_widget)
        else:
            self.stacked_layout.setCurrentWidget(self.main_area_widget)

    def setup_tabs(self):
        """Configures the tabs for detailed analysis."""
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

    def create_tab(self, plot_widget, table_widget):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(plot_widget)
        splitter.addWidget(table_widget)
        splitter.setSizes([400, 200])
        layout.addWidget(splitter)
        return tab

    def apply_styles(self):
        self.setStyleSheet("QMainWindow, QWidget { background-color: #f0f2f6; } QLabel { font-family: 'Segoe UI', Arial, sans-serif; color: #333; } QGroupBox { font-weight: bold; border: 1px solid #d0d0d0; border-radius: 8px; margin-top: 10px; background-color: #ffffff; } QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 8px; left: 10px; color: #333; } QComboBox, QListWidget { font-family: 'Segoe UI', Arial, sans-serif; padding: 5px; } QTabWidget::pane { border: 1px solid #cccccc; border-radius: 4px; background-color: white; } QTabBar::tab { background: #e1e1e1; border: 1px solid #cccccc; border-bottom-color: #c2c7d5; padding: 8px 16px; margin-right: 2px; border-top-left-radius: 4px; border-top-right-radius: 4px; } QTabBar::tab:selected { background: white; border-bottom-color: white; } QSplitter::handle { background: #d0d0d0; } QSplitter::handle:horizontal { width: 5px; } QSplitter::handle:vertical { height: 5px; } QHeaderView::section { background-color: #f0f2f6; padding: 4px; border: 1px solid #d0d0d0; font-weight: bold; }")

    def update_status(self, text, style_type='info'):
        base_style = "padding: 10px; border-radius: 5px; font-weight: bold;"
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
        for i, row in enumerate(df.itertuples()):
            for j, value in enumerate(row[1:]):
                table_widget.setItem(i, j, QTableWidgetItem(str(value)))
        table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

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

    def show(self):
        self.view.show()

    def load_network(self, network_name):
        self.model.load_network(network_name)
        self.view.sidebar.update_element_list(self.model.net)
        self.prepare_contingencies([])

    def prepare_contingencies(self, contingencies):
        self.current_contingencies = contingencies
        self.model.apply_contingencies(self.current_contingencies)
        self.clear_results()
        self.view.network_canvas.plot_network(self.model.net)

    def clear_results(self):
        self.view.update_status("Pronto para simular. Pressione o botão para executar.", 'info')
        self.view.metrics_widget.update_metrics({"total_load_mw": 0, "total_gen_mw": 0, "voltage_violations": 'N/A', "overloads": 'N/A'})
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
        """Shows loading screen and runs simulation after a short delay to ensure UI updates."""
        self.view.sidebar.set_run_button_loading(True)
        self.view.show_loading_overlay(True)
        # Use a QTimer to allow the UI to refresh and show the loading screen before blocking
        QTimer.singleShot(50, self.run_simulation)

    def run_simulation(self):
        try:
            success, msg = self.model.run_power_flow()
            if success:
                self.view.update_status(msg, 'success')
                self.update_results_display()
            else:
                self.view.update_status(msg, 'error')
                self.clear_results()
                self.view.network_canvas.plot_network(self.model.net)
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

    def _update_plots(self, voltage_df, line_df, trafo_df, power_flow_df):
        fig_v = go.Figure(data=[go.Bar(x=voltage_df['Barra'], y=voltage_df['Tensão (p.u.)'], marker_color='#1f77b4')])
        fig_v.add_hline(y=1.05, line_dash="dash", line_color="red"); fig_v.add_hline(y=0.95, line_dash="dash", line_color="red")
        fig_v.update_layout(title_text='Tensão nas Barras', yaxis_range=[0.9, 1.1])
        self.view.voltage_plot.plot_chart(fig_v)

        fig_l = go.Figure(data=[go.Bar(x=line_df['Linha'], y=line_df['Carregamento (%)'], marker_color='#ff7f0e')])
        fig_l.add_hline(y=100, line_dash="dash", line_color="red")
        fig_l.update_layout(title_text='Carregamento das Linhas', yaxis_range=[0, max(110, line_df['Carregamento (%)'].max() * 1.1 if not line_df.empty else 110)])
        self.view.line_loading_plot.plot_chart(fig_l)

        if not trafo_df.empty:
            fig_t = go.Figure(data=[go.Bar(x=trafo_df['Transformador'], y=trafo_df['Carregamento (%)'], marker_color='#2ca02c')])
            fig_t.add_hline(y=100, line_dash="dash", line_color="red")
            fig_t.update_layout(title_text='Carregamento dos Transformadores', yaxis_range=[0, max(110, trafo_df['Carregamento (%)'].max() * 1.1 if not trafo_df.empty else 110)])
            self.view.trafo_loading_plot.plot_chart(fig_t)
        else:
            self.view.trafo_loading_plot.clear()

        fig_p = go.Figure(data=[go.Bar(x=power_flow_df['Linha'], y=power_flow_df['Potência Ativa (MW)'], name='P (MW)', marker_color='#d62728')])
        fig_p.update_layout(title_text='Fluxo de Potência Ativa (MW)')
        self.view.line_p_flow_plot.plot_chart(fig_p)
        
        fig_q = go.Figure(data=[go.Bar(x=power_flow_df['Linha'], y=power_flow_df['Potência Reativa (MVAr)'], name='Q (MVAr)', marker_color='#9467bd')])
        fig_q.update_layout(title_text='Fluxo de Potência Reativa (MVAr)')
        self.view.line_q_flow_plot.plot_chart(fig_q)

# =========================== MAIN ===========================
def main():
    """Main entry point for the application."""
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 9))
    
    # Aplica o estilo claro por padrão
    app.setStyleSheet(AppStyles.DARK_MODE_STYLESHEET)

    if not PLOTLY_AVAILABLE:
        QMessageBox.warning(None, "Dependência Faltando", "O módulo 'PySide6-WebEngine' não foi encontrado. Os gráficos interativos não serão exibidos.\n\nPor favor, instale-o com: pip install PySide6-WebEngine")

    controller = PowerSystemController()
    controller.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
