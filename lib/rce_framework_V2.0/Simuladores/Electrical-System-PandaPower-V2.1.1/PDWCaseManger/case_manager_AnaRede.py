import numpy as np
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QWidget, QHBoxLayout, QTextEdit
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
import matplotlib.pyplot as plt
import pandas as pd
from pyspark.sql import SparkSession
import pandapower as pp
import pandapower.converter as pc
import pandapower.plotting as plot
import os

def apply_layout(self, net):
    """Gera coordenadas geográficas artificiais para plotagem se estiverem vazias"""
    if net.bus_geodata.empty:
        n_buses = len(net.bus)
        # Distribui as barras em um círculo para visualização clara
        angles = np.linspace(0, 2*np.pi, n_buses, endpoint=False)
        for i, angle in enumerate(angles):
            net.bus_geodata.loc[i] = [np.cos(angle), np.sin(angle)]
    return net


class PWFManager:
    def __init__(self):
        self.spark = SparkSession.builder.appName("ANA_REDE_SPARK").getOrCreate()
        self.net = None
        self.current_file = None

    def load_system(self, pwf_path):
        """Carrega o arquivo PWF e sincroniza com Spark SQL e Pandapower"""
        self.current_file = pwf_path
        # Converte PWF para objeto Pandapower (POO)
        self.net = pc.from_ppc(pc.pwf_to_ppc(pwf_path))
        
        # Sincroniza Tabelas para SQL via Spark
        df_lines = self.spark.createDataFrame(self.net.line[['from_bus', 'to_bus', 'r_pu', 'x_pu', 'length_km']])
        df_lines.createOrReplaceTempView("linhas")
        
        df_buses = self.spark.createDataFrame(self.net.bus[['vn_kv', 'type']])
        df_buses.createOrReplaceTempView("barras")
        
        return self.net

    def query_data(self, sql_query):
        """Executa SQL via Spark nos dados do sistema elétrico"""
        return self.spark.sql(sql_query).toPandas()

    def run_power_flow(self):
        """Executa o Fluxo de Potência (Newton-Raphson)"""
        if self.net:
            pp.runpp(self.net)
            return self.net

    def export_pwf(self, path):
        """Exporta o estado atual para .pwf (via conversão PPC)"""
        # Pandapower salva em .mat/PPC que o AnaRede lê via importação
        pc.to_ppc(self.net, path.replace(".pwf", ".mat"))
        print(f"Dados exportados para compatibilidade AnaRede: {path}")


class PWFView(QMainWindow):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.setWindowTitle("Sistema Elétrico: 3, 14 e 30 Barras")
        self.resize(1200, 800)

        # Layout Principal
        self.main_widget = QWidget()
        self.main_layout = QHBoxLayout(self.main_widget)
        self.setCentralWidget(self.main_widget)

        # Painel Esquerdo (Controles e SQL)
        self.controls = QVBoxLayout()
        self.init_controls()
        self.main_layout.addLayout(self.controls, 1)

        # Painel Direito (Gráfico)
        self.canvas_layout = QVBoxLayout()
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas_layout.addWidget(self.canvas)
        self.main_layout.addLayout(self.canvas_layout, 2)

    def init_controls(self):
        for caso in ["3_barras.pwf", "ieee14.pwf", "ieee30.pwf"]:
            btn = QPushButton(f"Carregar {caso}")
            btn.clicked.connect(lambda chk, c=caso: self.load_case(c))
            self.controls.addWidget(btn)

        self.sql_output = QTextEdit()
        self.sql_output.setPlaceholderText("Resultados SQL Spark...")
        self.sql_output.setReadOnly(True)
        self.controls.addWidget(self.sql_output)

        btn_export = QPushButton("Exportar .PWF")
        btn_export.setStyleSheet("background-color: #4CAF50; color: white;")
        btn_export.clicked.connect(lambda: self.manager.export_pwf("saida_sistema.pwf"))
        self.controls.addWidget(btn_export)

    def load_case(self, filename):
        if not os.path.exists(filename):
            self.sql_output.setText(f"Erro: Arquivo {filename} não encontrado.")
            return

        # 1. Backend processa
        net = self.manager.load_system(filename)
        self.manager.run_power_flow()

        # 2. Spark Query (Exemplo: Top 5 linhas com maior reatância)
        df_res = self.manager.query_data("SELECT * FROM linhas ORDER BY x_pu DESC LIMIT 5")
        self.sql_output.setText(f"Query Spark SQL (Linhas Críticas):\n{df_res.to_string()}")

        # 3. Atualiza Plot
        self.ax.clear()
        plot.simple_plot(net, ax=self.ax, show_plot=False)
        self.canvas.draw()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Instancia as Classes Únicas
    manager = PWFManager()
    view = PWFView(manager)
    
    view.show()
    sys.exit(app.exec())

