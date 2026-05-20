# --- Imports do PySide6 ---
from PySide6.QtWidgets import (
    QPushButton,
    QVBoxLayout,
    QWidget,
    QLabel,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QListWidget,
    QListWidgetItem,
    QTabWidget,
    QSplitter,
)
from PySide6.QtCore import (
    Qt,
    Signal,
)


import pandapower.plotting as plot
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


# --- Checagem de dependências opcionais ---
try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    import plotly.graph_objects as go
    import plotly.io as pio

    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False


# Widgets
class AnalysisSelectionWidget(QWidget):
    analysis_selected = Signal(str)

    def __init__(self, cases):
        super().__init__()
        self.cases = cases
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        title = QLabel("Selecione o Caso de Análise de Contingência")
        title.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title, alignment=Qt.AlignCenter)
        self.list_widget = QListWidget()
        self.list_widget.setMaximumWidth(500)
        for case_id, case_data in self.cases.items():
            item = QListWidgetItem(case_data["name"])
            item.setData(Qt.UserRole, case_id)
            item.setTextAlignment(Qt.AlignCenter)
            self.list_widget.addItem(item)
        layout.addWidget(self.list_widget, alignment=Qt.AlignCenter)
        self.load_button = QPushButton("Carregar Análise")
        self.load_button.setStyleSheet("font-size: 16px; padding: 15px 30px;")
        self.load_button.clicked.connect(self.on_load_clicked)
        layout.addWidget(self.load_button, alignment=Qt.AlignCenter)

    def on_load_clicked(self):
        if self.list_widget.currentItem():
            self.analysis_selected.emit(
                self.list_widget.currentItem().data(Qt.UserRole)
            )


class NetworkCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(8, 8), dpi=100, tight_layout=True)
        super().__init__(self.fig)
        self.ax = self.fig.add_subplot(111)
        self.net = None
        plt.ioff()

    def plot_network(self, net):
        self.net = net
        self.ax.clear()
        self.fig.set_facecolor("#1e1e1e")
        self.ax.set_facecolor("#1e1e1e")
        if not net or net.bus.empty:
            self.ax.text(0.5, 0.5, "Rede Vazia.", ha="center", color="white")
            self.draw()
            return
        if not hasattr(net, "bus_geodata") or net.bus_geodata.empty:
            plot.create_generic_coordinates(net, respect_switches=True)
        bc = plot.create_bus_collection(
            net, buses=net.bus.index, size=0.05, color="blue", zorder=10
        )
        self.ax.add_collection(bc)
        if not net.line.empty:
            in_service = net.line[net.line.in_service].index
            oos = net.line[~net.line.in_service].index
            if not in_service.empty:
                self.ax.add_collection(
                    plot.create_line_collection(
                        net,
                        lines=in_service,
                        use_bus_geodata=True,
                        color="grey",
                        linewidths=1.5,
                    )
                )
            if not oos.empty:
                self.ax.add_collection(
                    plot.create_line_collection(
                        net,
                        lines=oos,
                        use_bus_geodata=True,
                        color="red",
                        linestyle="--",
                        linewidths=1.5,
                    )
                )
        if not net.trafo.empty:
            self.ax.add_collection(
                plot.create_trafo_collection(
                    net, trafos=net.trafo.index, color="purple"
                )
            )
        self.ax.set_title(f"Diagrama: {net.name}", color="white")
        self.ax.autoscale_view(True, True, True)
        self.draw()


class PlotlyWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.is_available = PLOTLY_AVAILABLE
        self.setLayout(QVBoxLayout())
        if self.is_available:
            self.browser = QWebEngineView()
            self.layout().addWidget(self.browser)
        else:
            self.label = QLabel(
                "Plotly indisponível.\nInstale 'PySide6-WebEngine' para ver gráficos interativos."
            )
            self.label.setAlignment(Qt.AlignCenter)
            self.layout().addWidget(self.label)

    def plot_chart(self, fig):
        if self.is_available:
            fig.update_layout(
                paper_bgcolor="#1e1e1e", plot_bgcolor="#2d2d2d", font_color="white"
            )
            self.browser.setHtml(
                pio.to_html(fig, full_html=False, include_plotlyjs="cdn")
            )

    def clear(self):
        if self.is_available:
            self.browser.setHtml("")


class PowerSystemAnalysisView(QWidget):
    run_simulation_requested = Signal()
    contingencies_changed = Signal(list)

    def __init__(self, case_name):
        super().__init__()
        self.case_name = case_name
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        self.sidebar = self._create_sidebar()
        main_layout.addWidget(self.sidebar)
        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        main_layout.addWidget(content_area)
        self.status_label = QLabel(f"Caso Carregado: {self.case_name}")
        content_layout.addWidget(self.status_label)
        self.tabs = QTabWidget()
        content_layout.addWidget(self.tabs)
        self._setup_tabs()

    def _create_sidebar(self):
        sidebar_widget = QWidget()
        sidebar_widget.setMaximumWidth(350)
        layout = QVBoxLayout(sidebar_widget)
        layout.addWidget(
            QLabel(
                f"Análise: {self.case_name}",
                styleSheet="font-weight: bold; font-size: 16px;",
            )
        )
        self.contingency_list = QListWidget()
        self.contingency_list.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.contingency_list)
        self.run_button = QPushButton("Executar Fluxo de Potência")
        self.run_button.clicked.connect(self.run_simulation_requested.emit)
        layout.addWidget(self.run_button)
        return sidebar_widget

    def _setup_tabs(self):
        self.network_canvas = NetworkCanvas(self)
        self.tabs.addTab(self.network_canvas, "Diagrama da Rede")
        self.voltage_plot = PlotlyWidget()
        self.voltage_table = QTableWidget()
        self.tabs.addTab(
            self._create_tab_layout(self.voltage_plot, self.voltage_table),
            "Tensão nas Barras",
        )
        self.line_loading_plot = PlotlyWidget()
        self.line_loading_table = QTableWidget()
        self.tabs.addTab(
            self._create_tab_layout(self.line_loading_plot, self.line_loading_table),
            "Carregamento de Linhas",
        )

    def _create_tab_layout(self, plot_widget, table_widget):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(plot_widget)
        splitter.addWidget(table_widget)
        splitter.setSizes([400, 200])
        layout.addWidget(splitter)
        return tab

    def _on_item_clicked(self, item):
        contingencies = [
            self.contingency_list.item(i).data(Qt.UserRole)
            for i in range(self.contingency_list.count())
            if self.contingency_list.item(i).checkState() == Qt.Checked
        ]
        self.contingencies_changed.emit(contingencies)

    def update_status(self, text, is_error=False):
        self.status_label.setText(text)
        self.status_label.setStyleSheet(
            "color: #e74c3c;" if is_error else "color: #2ecc71;"
        )

    def update_table(self, table, df):
        table.clearContents()
        if df.empty:
            table.setRowCount(0)
            return
        table.setRowCount(df.shape[0])
        table.setColumnCount(df.shape[1])
        table.setHorizontalHeaderLabels(df.columns)
        for i, row in enumerate(df.itertuples(index=False)):
            for j, val in enumerate(row):
                table.setItem(i, j, QTableWidgetItem(str(val)))
