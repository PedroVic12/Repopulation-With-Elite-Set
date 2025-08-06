import sys
import pandas as pd
import pandapower as pp
import pandapower.networks as pn
import pandapower.plotting as plot
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QRadioButton, QButtonGroup, QPushButton,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QSplitter, QTextEdit, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

# Desativa o modo interativo do Matplotlib para evitar pop-ups
plt.ioff()

# NOTE: QWebEngineView is required for Plotly charts. 
# You may need to install it separately:
# pip install PySide6-WebEngine
try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    import plotly.graph_objects as go
    import plotly.io as pio
    import plotly.express as px
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
                # Fallback to a default case if the name is unrecognized
                self.net = pn.case14()
            
            # Store the original name in the network object for plotting
            self.net.name = network_name
            return self.net
        except Exception:
            # Return an empty network if loading fails
            return pp.create_empty_network()

    def reset_network_state(self):
        """
        Resets the network to its original operational state by putting all
        lines and transformers back in service.
        """
        if self.net:
            self.net.line['in_service'] = True
            if 'in_service' in self.net.trafo:
                self.net.trafo['in_service'] = True

    def run_power_flow(self):
        """
        Executes the power flow calculation using the Newton-Raphson method.
        Returns a status tuple (success, message).
        """
        try:
            pp.runpp(self.net, algorithm="nr", numba=True)
            return True, "Power flow converged successfully."
        except pp.LoadflowNotConverged:
            return False, "Power Flow Did Not Converge."
        except Exception as e:
            return False, f"An unexpected error occurred: {e}"

    def apply_contingency(self, element_type, element_id):
        """
        Applies a contingency by taking a specified element out of service.
        """
        if element_type == 'Linha' and element_id in self.net.line.index:
            self.net.line.loc[element_id, 'in_service'] = False
        elif element_type == 'Transformador' and element_id in self.net.trafo.index:
            self.net.trafo.loc[element_id, 'in_service'] = False

class ResultsRepository:
    """
    Repository - A class dedicated to fetching and formatting simulation results
    from a pandapower network object.
    """
    
    def __init__(self, net):
        """
        Initializes the repository with a simulated pandapower network.
        Raises ValueError if the network is not simulated or has no results.
        """
        if net is None or not hasattr(net, 'res_bus') or net.res_bus.empty:
            raise ValueError("The pandapower network has not been simulated or contains no results.")
        self.net = net

    def get_kpis(self):
        """Calculates and returns key performance indicators (KPIs) for the network."""
        voltage_violations = (
            (self.net.res_bus.vm_pu > self.net.bus.max_vm_pu) | 
            (self.net.res_bus.vm_pu < self.net.bus.min_vm_pu)
        ).sum()

        line_overloads = (self.net.res_line.loading_percent > 100).sum()
        trafo_overloads = 0
        if hasattr(self.net, 'res_trafo') and not self.net.res_trafo.empty:
            trafo_overloads = (self.net.res_trafo.loading_percent > 100).sum()

        kpis = {
            "total_load_mw": self.net.res_load.p_mw.sum(),
            "total_gen_mw": self.net.res_gen.p_mw.sum(),
            "voltage_violations": voltage_violations,
            "overloads": line_overloads + trafo_overloads
        }
        return kpis

    def get_bus_voltage_data(self):
        """Returns a DataFrame with bus voltage results."""
        df = self.net.res_bus[['vm_pu']].copy()
        df['vm_pu'] = df['vm_pu'].round(4)
        return df.reset_index().rename(columns={'index': 'Barra', 'vm_pu': 'Tensão (p.u.)'})

    def get_line_loading_data(self):
        """Returns a DataFrame with line loading results."""
        df = self.net.res_line[['loading_percent']].copy()
        df['loading_percent'] = df['loading_percent'].round(2)
        return df.reset_index().rename(columns={'index': 'Linha', 'loading_percent': 'Carregamento (%)'})

    def get_trafo_loading_data(self):
        """Returns a DataFrame with transformer loading results."""
        if not hasattr(self.net, 'res_trafo') or self.net.res_trafo.empty:
            return pd.DataFrame(columns=['Transformador', 'Carregamento (%)'])
        df = self.net.res_trafo[['loading_percent']].copy()
        df['loading_percent'] = df['loading_percent'].round(2)
        return df.reset_index().rename(columns={'index': 'Transformador', 'loading_percent': 'Carregamento (%)'})

# =========================== VIEW ===========================
class NetworkCanvas(FigureCanvas):
    """A Matplotlib canvas widget for plotting the power grid diagram."""
    
    def __init__(self, parent=None, width=8, height=8, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi, tight_layout=True)
        self.fig.patch.set_facecolor("#f0f2f6")
        super().__init__(self.fig)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor("#f0f2f6")

    def plot_network(self, net):
        """
        Plots the electrical network diagram, highlighting out-of-service elements.
        """
        self.ax.clear()
        try:
            title = f"Diagrama da Rede: {net.name.upper() if hasattr(net, 'name') and net.name else 'Desconhecida'}"
            
            # Plot the base network, ensuring it doesn't create a new window
            plot.simple_plot(net, ax=self.ax, bus_size=0.6, line_width=2.0, bus_color="b")
            
            # Identify and plot out-of-service lines
            oos_lines = net.line.index[~net.line.in_service]
            if len(oos_lines) > 0:
                lc = plot.create_line_collection(net, lines=oos_lines, color="r", linestyle="--", use_bus_geodata=True)
                self.ax.add_collection(lc)

            # Identify and plot out-of-service transformers
            if 'in_service' in net.trafo:
                oos_trafos = net.trafo.index[~net.trafo.in_service]
                if len(oos_trafos) > 0:
                    tc = plot.create_trafo_collection(net, trafos=oos_trafos, color="r", linestyle="--")
                    self.ax.add_collection(tc)

            self.ax.set_title(title, fontsize=14, weight='bold')
        except Exception as e:
            self.ax.text(0.5, 0.5, f"Erro ao plotar a rede:\n{e}", ha='center', va='center')
        self.draw()


class MetricsWidget(QWidget):
    """A widget to display key performance indicators (KPIs) in styled cards."""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(0,0,0,0)
        
        self.metric_cards = {}
        titles = {
            "load": "Carga Total (MW)",
            "gen": "Geração Total (MW)",
            "voltage": "Violações de Tensão",
            "overload": "Sobrecargas"
        }
        
        for key, title in titles.items():
            card = self._create_metric_card(title, "0.00")
            layout.addWidget(card)
            self.metric_cards[key] = card

    def _create_metric_card(self, title, value):
        """Creates a single styled card for a metric."""
        card = QGroupBox(title)
        card.setStyleSheet("""
            QGroupBox { 
                background-color: white; 
                border: 1px solid #ddd; 
                border-radius: 8px; 
                margin-top: 10px;
                font-size: 11px;
                font-weight: bold;
                color: #555;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                left: 10px;
            }
        """)
        
        layout = QVBoxLayout(card)
        value_label = QLabel(value)
        value_label.setStyleSheet("font-size: 22px; color: #000; font-weight: bold; padding-top: 5px;")
        value_label.setObjectName("value_label")
        layout.addWidget(value_label)
        layout.addStretch()
        return card

    def update_metrics(self, kpis):
        """Updates the values displayed on the metric cards."""
        values = {
            "load": f"{kpis['total_load_mw']:.2f}",
            "gen": f"{kpis['total_gen_mw']:.2f}",
            "voltage": f"{kpis['voltage_violations']}",
            "overload": f"{kpis['overloads']}"
        }
        
        for key, value in values.items():
            card = self.metric_cards[key]
            value_label = card.findChild(QLabel, "value_label")
            if value_label:
                value_label.setText(value)

class PlotlyWidget(QWebEngineView if PLOTLY_AVAILABLE else QTextEdit):
    """
    A widget to display Plotly charts. It uses QWebEngineView if available,
    otherwise it falls back to a simple QTextEdit with an error message.
    """
    def __init__(self):
        super().__init__()
        if not PLOTLY_AVAILABLE:
            self.setReadOnly(True)
            self.setText("Plotly não está disponível. Por favor, instale 'PySide6-WebEngine' para ver os gráficos.")
        else:
            self.setHtml("<html><body style='background-color:#f0f2f6;'></body></html>")

    def plot_chart(self, fig):
        """Renders a Plotly figure object into the web view."""
        if not PLOTLY_AVAILABLE:
            return
        html = pio.to_html(fig, full_html=False, include_plotlyjs='cdn')
        self.setHtml(html)

    def clear(self):
        """Clears the plot view."""
        if PLOTLY_AVAILABLE:
            self.setHtml("<html><body style='background-color:#f0f2f6;'></body></html>")

class SidebarWidget(QWidget):
    """The sidebar widget containing all simulation controls."""
    
    network_changed = Signal(str)
    contingency_changed = Signal(str, object)
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
        
        # Network Selection
        network_group = QGroupBox("Seleção da Rede Elétrica")
        network_layout = QVBoxLayout(network_group)
        self.network_combo = QComboBox()
        self.network_combo.addItems(["case14", "case30", "case57", "case118"])
        self.network_combo.currentTextChanged.connect(self.network_changed.emit)
        network_layout.addWidget(self.network_combo)
        layout.addWidget(network_group)
        
        # Contingency Analysis
        contingency_group = QGroupBox("Análise de Contingência (N-1)")
        contingency_layout = QVBoxLayout(contingency_group)
        
        contingency_layout.addWidget(QLabel("Elemento para Desligar:"))
        self.radio_group = QButtonGroup(self)
        self.radio_none = QRadioButton("Nenhum (Caso Base)")
        self.radio_line = QRadioButton("Linha")
        self.radio_trafo = QRadioButton("Transformador")
        self.radio_none.setChecked(True)
        
        self.radio_group.addButton(self.radio_none)
        self.radio_group.addButton(self.radio_line)
        self.radio_group.addButton(self.radio_trafo)
        
        radio_layout = QVBoxLayout()
        radio_layout.addWidget(self.radio_none)
        radio_layout.addWidget(self.radio_line)
        radio_layout.addWidget(self.radio_trafo)
        contingency_layout.addLayout(radio_layout)
        
        self.element_combo = QComboBox()
        self.element_combo.setEnabled(False)
        contingency_layout.addWidget(self.element_combo)
        layout.addWidget(contingency_group)

        # Run Button
        self.run_button = QPushButton("Executar Fluxo de Potência")
        self.run_button.setStyleSheet("QPushButton { background-color: #28a745; color: white; padding: 8px; border-radius: 5px; font-weight: bold; }")
        layout.addWidget(self.run_button)
        
        layout.addStretch()
        
        # Connect signals
        self.radio_group.buttonClicked.connect(self._on_radio_changed)
        self.element_combo.currentIndexChanged.connect(self._on_element_changed)
        self.run_button.clicked.connect(self.run_simulation_requested.emit)

    def _on_radio_changed(self):
        """Handles changes in the contingency type radio buttons."""
        self.element_combo.setEnabled(not self.radio_none.isChecked())
        self._on_element_changed() # Trigger an update

    def _on_element_changed(self):
        """Emits a signal when the selected contingency changes."""
        if self.radio_none.isChecked():
            self.contingency_changed.emit("Nenhum", None)
        elif self.radio_line.isChecked():
            self.contingency_changed.emit("Linha", self.element_combo.currentData())
        elif self.radio_trafo.isChecked():
            self.contingency_changed.emit("Transformador", self.element_combo.currentData())

    def update_element_combo(self, net):
        """Populates the element combo box based on the selected network and type."""
        self.element_combo.clear()
        if self.radio_line.isChecked():
            if net and not net.line.empty:
                for idx, row in net.line.iterrows():
                    label = f"Linha {idx} (Barra {row.from_bus} ↔ {row.to_bus})"
                    self.element_combo.addItem(label, idx)
        elif self.radio_trafo.isChecked():
            if net and not net.trafo.empty:
                for idx, row in net.trafo.iterrows():
                    label = f"Trafo {idx} (Barra {row.hv_bus} ↔ {row.lv_bus})"
                    self.element_combo.addItem(label, idx)

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
        
        # Sidebar
        self.sidebar = SidebarWidget()
        self.sidebar.setMaximumWidth(320)
        
        # Main Area
        main_area = QWidget()
        main_area_layout = QVBoxLayout(main_area)
        
        # Status Label
        self.status_label = QLabel("Carregando rede inicial...")
        main_area_layout.addWidget(self.status_label)
        
        # Metrics
        self.metrics_widget = MetricsWidget()
        main_area_layout.addWidget(self.metrics_widget)
        
        # Content Splitter
        content_splitter = QSplitter(Qt.Horizontal)
        
        # Left Panel (Network Diagram)
        left_panel = QGroupBox("Diagrama Topológico da Rede")
        left_layout = QVBoxLayout(left_panel)
        self.network_canvas = NetworkCanvas(self)
        left_layout.addWidget(self.network_canvas)
        
        # Right Panel (Tabs with detailed results)
        right_panel = QGroupBox("Resultados Detalhados da Simulação")
        right_layout = QVBoxLayout(right_panel)
        self.tabs = QTabWidget()
        self.setup_tabs()
        right_layout.addWidget(self.tabs)
        
        content_splitter.addWidget(left_panel)
        content_splitter.addWidget(right_panel)
        content_splitter.setSizes([600, 800])
        main_area_layout.addWidget(content_splitter)
        
        # Add to main splitter
        splitter.addWidget(self.sidebar)
        splitter.addWidget(main_area)
        splitter.setSizes([300, 1300])
        main_layout.addWidget(splitter)

    def setup_tabs(self):
        """Configures the tabs for detailed analysis."""
        self.voltage_plot = PlotlyWidget()
        self.line_plot = PlotlyWidget()
        self.trafo_plot = PlotlyWidget()
        self.voltage_table = QTableWidget()
        self.line_table = QTableWidget()
        self.trafo_table = QTableWidget()

        self.tabs.addTab(self.create_tab("📊 Tensões nas Barras", self.voltage_plot, self.voltage_table), "Tensões")
        self.tabs.addTab(self.create_tab("📈 Carregamento das Linhas", self.line_plot, self.line_table), "Linhas")
        self.tabs.addTab(self.create_tab("📈 Carregamento dos Trafos", self.trafo_plot, self.trafo_table), "Transformadores")

    def create_tab(self, title, plot_widget, table_widget):
        """Helper function to create a consistent tab layout."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(plot_widget)
        splitter.addWidget(table_widget)
        splitter.setSizes([400, 200])
        layout.addWidget(splitter)
        return tab

    def apply_styles(self):
        """Applies a global stylesheet (QSS) to the application."""
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #f0f2f6;
            }
            QLabel {
                font-family: 'Segoe UI', Arial, sans-serif;
                color: #333;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #d0d0d0;
                border-radius: 8px;
                margin-top: 10px;
                background-color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
                left: 10px;
                color: #333;
            }
            QComboBox, QRadioButton {
                font-family: 'Segoe UI', Arial, sans-serif;
                padding: 5px;
            }
            QTabWidget::pane {
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: white;
            }
            QTabBar::tab {
                background: #e1e1e1;
                border: 1px solid #cccccc;
                border-bottom-color: #c2c7d5;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: white;
                border-bottom-color: white;
            }
            QSplitter::handle {
                background: #d0d0d0;
            }
            QSplitter::handle:horizontal {
                width: 5px;
            }
            QSplitter::handle:vertical {
                height: 5px;
            }
            QHeaderView::section {
                background-color: #f0f2f6;
                padding: 4px;
                border: 1px solid #d0d0d0;
                font-weight: bold;
            }
        """)

    def update_status(self, text, style_type='info'):
        """Updates the simulation status label with appropriate styling."""
        base_style = "padding: 10px; border-radius: 5px; font-weight: bold;"
        if style_type == 'success':
            self.status_label.setText(f"✅ {text}")
            self.status_label.setStyleSheet(f"QLabel {{ {base_style} background-color: #d4edda; border: 1px solid #c3e6cb; color: #155724; }}")
        elif style_type == 'error':
            self.status_label.setText(f"❌ {text}")
            self.status_label.setStyleSheet(f"QLabel {{ {base_style} background-color: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }}")
        else: # info
            self.status_label.setText(f"ℹ️ {text}")
            self.status_label.setStyleSheet(f"QLabel {{ {base_style} background-color: #e2e3e5; border: 1px solid #d6d8db; color: #383d41; }}")


    def update_table(self, table_widget, df):
        """Populates a QTableWidget with data from a pandas DataFrame."""
        table_widget.clear()
        if df.empty:
            table_widget.setRowCount(0)
            table_widget.setColumnCount(0)
            return
        table_widget.setRowCount(len(df))
        table_widget.setColumnCount(len(df.columns))
        table_widget.setHorizontalHeaderLabels(df.columns.tolist())
        
        for i, row in enumerate(df.itertuples(index=False)):
            for j, value in enumerate(row):
                table_widget.setItem(i, j, QTableWidgetItem(str(value)))
        
        table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

# =========================== CONTROLLER ===========================
class PowerSystemController:
    """
    Controller - Manages the interaction between the Model and the View.
    """
    
    def __init__(self):
        self.view = MainWindow()
        self.model = PowerSystemModel()
        self.setup_connections()
        self.load_network(self.view.sidebar.network_combo.currentText())

    def setup_connections(self):
        """Connects signals from the view to the controller's methods."""
        self.view.sidebar.network_changed.connect(self.load_network)
        self.view.sidebar.contingency_changed.connect(self.prepare_contingency)
        self.view.sidebar.radio_group.buttonClicked.connect(self._on_contingency_type_change)
        self.view.sidebar.run_simulation_requested.connect(self.run_simulation)

    def show(self):
        """Displays the main application window."""
        self.view.show()

    def load_network(self, network_name):
        """Loads a new network, updates controls, and clears previous results."""
        self.model.load_network(network_name)
        self._on_contingency_type_change() 
        self.clear_results()
        self.view.network_canvas.plot_network(self.model.net)


    def _on_contingency_type_change(self):
        """Updates the contingency element combo box when the type changes."""
        self.view.sidebar.update_element_combo(self.model.net)
        self.prepare_contingency(
            self.view.sidebar.radio_group.checkedButton().text(),
            self.view.sidebar.element_combo.currentData()
        )

    def prepare_contingency(self, element_type, element_id):
        """Applies a contingency to the model without running the simulation yet."""
        self.model.reset_network_state()
        if element_type != "Nenhum (Caso Base)" and element_id is not None:
            # Determine the correct type string for the model
            model_element_type = "Linha" if "Linha" in element_type else "Transformador"
            self.model.apply_contingency(model_element_type, int(element_id))
        
        self.clear_results()
        self.view.network_canvas.plot_network(self.model.net)

    def clear_results(self):
        """Clears all result displays in the UI."""
        self.view.update_status("Pronto para simular. Pressione o botão para executar.", 'info')
        self.view.metrics_widget.update_metrics({
            "total_load_mw": 0, "total_gen_mw": 0, 
            "voltage_violations": 'N/A', "overloads": 'N/A'
        })
        self.view.update_table(self.view.voltage_table, pd.DataFrame())
        self.view.update_table(self.view.line_table, pd.DataFrame())
        self.view.update_table(self.view.trafo_table, pd.DataFrame())
        if PLOTLY_AVAILABLE:
            self.view.voltage_plot.clear()
            self.view.line_plot.clear()
            self.view.trafo_plot.clear()

    def run_simulation(self):
        """
        The main simulation workflow. Executes power flow and updates all
        UI components with the new results.
        """
        success, msg = self.model.run_power_flow()
        
        if success:
            self.view.update_status(msg, 'success')
            try:
                repo = ResultsRepository(self.model.net)
                
                # Update KPIs
                self.view.metrics_widget.update_metrics(repo.get_kpis())
                
                # Get data
                voltage_df = repo.get_bus_voltage_data()
                line_df = repo.get_line_loading_data()
                trafo_df = repo.get_trafo_loading_data()
                
                # Update tables
                self.view.update_table(self.view.voltage_table, voltage_df)
                self.view.update_table(self.view.line_table, line_df)
                self.view.update_table(self.view.trafo_table, trafo_df)

                # Update plots if Plotly is available
                if PLOTLY_AVAILABLE:
                    self._update_plots(voltage_df, line_df, trafo_df)

            except Exception as e:
                self.view.update_status(f"Erro ao processar resultados: {e}", 'error')
        else:
            self.view.update_status(msg, 'error')
            self.clear_results() # Clear results but keep the network plot
            self.view.network_canvas.plot_network(self.model.net)


    def _update_plots(self, voltage_df, line_df, trafo_df):
        """Helper function to create and display all Plotly charts."""
        # Voltage Plot
        fig_v = go.Figure(data=[go.Bar(
            x=voltage_df['Barra'], 
            y=voltage_df['Tensão (p.u.)'],
            marker_color='#1f77b4'
        )])
        fig_v.add_hline(y=1.05, line_dash="dash", line_color="red")
        fig_v.add_hline(y=0.95, line_dash="dash", line_color="red")
        fig_v.update_layout(title_text='Tensão nas Barras', yaxis_range=[0.9, 1.1])
        self.view.voltage_plot.plot_chart(fig_v)

        # Line Loading Plot
        fig_l = go.Figure(data=[go.Bar(
            x=line_df['Linha'], 
            y=line_df['Carregamento (%)'],
            marker_color='#ff7f0e'
        )])
        fig_l.add_hline(y=100, line_dash="dash", line_color="red")
        fig_l.update_layout(title_text='Carregamento das Linhas', yaxis_range=[0, max(110, line_df['Carregamento (%)'].max() * 1.1 if not line_df.empty else 110)])
        self.view.line_plot.plot_chart(fig_l)

        # Transformer Loading Plot
        if not trafo_df.empty:
            fig_t = go.Figure(data=[go.Bar(
                x=trafo_df['Transformador'], 
                y=trafo_df['Carregamento (%)'],
                marker_color='#2ca02c'
            )])
            fig_t.add_hline(y=100, line_dash="dash", line_color="red")
            fig_t.update_layout(title_text='Carregamento dos Transformadores', yaxis_range=[0, max(110, trafo_df['Carregamento (%)'].max() * 1.1 if not trafo_df.empty else 110)])
            self.view.trafo_plot.plot_chart(fig_t)
        else:
            self.view.trafo_plot.clear()


# =========================== MAIN ===========================
def main():
    """The main entry point for the application."""
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 9))
    
    if not PLOTLY_AVAILABLE:
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setText("Dependência Faltando")
        msg_box.setInformativeText(
            "O módulo 'PySide6-WebEngine' não foi encontrado. "
            "Os gráficos interativos não serão exibidos.\n\n"
            "Por favor, instale-o com: pip install PySide6-WebEngine"
        )
        msg_box.setWindowTitle("Aviso")
        msg_box.exec()

    controller = PowerSystemController()
    controller.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
