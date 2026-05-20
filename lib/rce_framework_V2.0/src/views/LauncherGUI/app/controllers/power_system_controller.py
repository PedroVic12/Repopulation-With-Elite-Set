# --- Imports do PySide6 ---
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QLabel,
    QHBoxLayout,
    QTextEdit,
    QProgressBar,
    QTabWidget,
    QGroupBox,
    QSpinBox,
    QLineEdit,
    QComboBox,
    QMessageBox,
    QRadioButton,
    QButtonGroup,
    QGridLayout,
    QTableWidget,
    QTableWidgetItem,
    QFrame,
    QHeaderView,
    QListWidget,
    QListWidgetItem,
    QStackedLayout,
    QSplitter,
    QFileDialog,
)
from PySide6.QtCore import (
    Qt,
    QThread,
    Signal,
    QTimer,
    Slot,
    QObject,
    QPropertyAnimation,
    QEasingCurve,
)
from PySide6.QtGui import (
    QIntValidator,
    QDoubleValidator,
    QFont,
    QColor,
    QTextCursor,
    QIcon,
)

class PowerSystemController(QObject):
    def __init__(self, view, network_name, contingencia_df):
        super().__init__()
        self.view, self.model = view, PowerSystemModel(network_name)
        self.contingencia_df = contingencia_df
        self.current_contingencies = []
        self._setup_connections()
        self._initial_load()

    def _setup_connections(self):
        self.view.run_simulation_requested.connect(self.run_simulation)
        self.view.contingencies_changed.connect(self.prepare_contingencies)

    def _initial_load(self):
        self.view.update_status("Pronto para simular.")
        self._update_contingency_list()
        self.view.network_canvas.plot_network(self.model.net)
        self.clear_results()

    def _update_contingency_list(self):
        self.view.contingency_list.clear()
        if self.contingencia_df is not None and not self.contingencia_df.empty:
            for idx, row in self.contingencia_df.iterrows():
                line = self.model.net.line[
                    (self.model.net.line.from_bus == row["from"])
                    & (self.model.net.line.to_bus == row["to"])
                ]
                line_index = line.index[0] if not line.empty else -1
                item = QListWidgetItem(f"[L] Ramo {row['from']} ↔ {row['to']}")
                item.setData(Qt.UserRole, ("line", line_index))
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Unchecked)
                self.view.contingency_list.addItem(item)

    @Slot(list)
    def prepare_contingencies(self, contingencies):
        self.current_contingencies = contingencies
        self.model.apply_contingencies(self.current_contingencies)
        self.clear_results()
        self.view.network_canvas.plot_network(self.model.net)

    @Slot()
    def run_simulation(self):
        try:
            self.model.apply_contingencies(self.current_contingencies)
            success, msg = self.model.run_power_flow()
            self.view.update_status(msg, not success)
            if success:
                self.update_results_display()
            else:
                self.clear_results()
        except Exception as e:
            self.view.update_status(f"Erro crítico: {e}", True)
            print(traceback.format_exc())

    def update_results_display(self):
        try:
            repo = ResultsRepository(self.model.net)
            voltage_df = repo.get_bus_voltage_data()
            line_df = repo.get_line_loading_data()
            self.view.update_table(self.view.voltage_table, voltage_df)
            self.view.update_table(self.view.line_loading_table, line_df)
            if PLOTLY_AVAILABLE:
                fig_v = go.Figure(
                    data=[
                        go.Bar(
                            x=voltage_df["Barra"],
                            y=voltage_df["Tensão (p.u.)"],
                            name="Tensão",
                        )
                    ]
                )
                fig_v.add_hline(y=1.05, line_dash="dash", line_color="red")
                fig_v.add_hline(y=0.95, line_dash="dash", line_color="red")
                fig_v.update_layout(title_text="Tensão (p.u.)")
                self.view.voltage_plot.plot_chart(fig_v)
                fig_l = go.Figure(
                    data=[
                        go.Bar(
                            x=line_df["Linha"],
                            y=line_df["Carreg. (%)"],
                            name="Carregamento",
                        )
                    ]
                )
                fig_l.add_hline(y=100, line_dash="dash", line_color="red")
                fig_l.update_layout(title_text="Carreg. (%)")
                self.view.line_loading_plot.plot_chart(fig_l)
        except Exception as e:
            self.view.update_status(f"Erro ao exibir resultados: {e}", True)
            print(traceback.format_exc())

    def clear_results(self):
        self.view.update_table(self.view.voltage_table, pd.DataFrame())
        self.view.update_table(self.view.line_loading_table, pd.DataFrame())
        self.view.voltage_plot.clear()
        self.view.line_loading_plot.clear()
