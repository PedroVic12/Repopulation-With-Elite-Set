"""
Objetivo
Permitir a inserção de dados de barras, linhas e transformadores por meio de um formulário passo a passo ou importação de Excel.

Armazenar os dados em um banco SQLite (apenas operações de criação e exclusão, sem edição).

Calcular a matriz Ybus e exibi-la em formato tabular.

Gerar o diagrama unifilar interativo usando plotly (ou matplotlib via pandapower).

Servir como base para futuros estudos de fluxo de potência.

2. Estrutura de Arquivos
Criaremos três arquivos:

frontend.ui – interface gráfica desenhada no Qt Designer.

backend.py – classes do modelo (banco de dados) e controlador (lógica de negócio).

main.py – ponto de entrada que carrega a UI e instancia o controlador.

"""

import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QIODevice
from backend import Database, NetworkController
import pandas as pd
import plotly.offline as py_offline
from PySide6.QtWebEngineWidgets import QWebEngineView

#! pip install pyside6 pandas pandapower plotly rich openpyxl networkx

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Carrega UI
        ui_file = QFile("frontend.ui")
        ui_file.open(QFile.ReadOnly)
        loader = QUiLoader()
        self.ui = loader.load(ui_file, self)
        ui_file.close()
        self.setCentralWidget(self.ui)

        # Inicializa banco e controlador
        self.db = Database()
        self.controller = NetworkController(self.db)

        # Conecta ações
        self.ui.actionImportar_Excel.triggered.connect(self.import_excel)
        self.ui.actionCalcular_Ybus.triggered.connect(self.calcular_ybus)
        self.ui.actionPlotar_Diagrama.triggered.connect(self.plotar_diagrama)
        
        self.ui.actionImportar_Anarede.triggered.connect(self.import_anarede)
        self.ui.actionExecutar_Fluxo.triggered.connect(self.executar_fluxo)
        self.ui.actionExportar_Resultados.triggered.connect(self.exportar_resultados)
        self.ui.btnEditBus.clicked.connect(self.edit_bus_dialog)
        
        # Botões de adicionar (simplificado: abre diálogo próprio)
        self.ui.btnAddBus.clicked.connect(self.add_bus_dialog)
        self.ui.btnAddLine.clicked.connect(self.add_line_dialog)
        self.ui.btnAddTrafo.clicked.connect(self.add_trafo_dialog)

        # Botões de excluir
        self.ui.btnDelBus.clicked.connect(self.del_bus)
        self.ui.btnDelLine.clicked.connect(self.del_line)
        self.ui.btnDelTrafo.clicked.connect(self.del_trafo)

        # Atualiza tabelas
        self.refresh_tables()

    def import_excel(self):
        # Abre diálogo para selecionar arquivo
        from PySide6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(self, "Importar Excel", "", "Excel (*.xlsx *.xls)")
        if file_path:
            self.controller.import_from_excel(file_path)
            self.refresh_tables()

    def calcular_ybus(self):
        net = self.controller.build_pandapower_net()
        # Força a criação do Ybus (necessário rodar fluxo de potência ou chamar pp.runpp?)
        # Na verdade, o Ybus é criado quando se chama pp.runpp, mas podemos acessar net._ppc depois.
        # Para apenas Ybus, podemos fazer pp.runpp(net) se houver pelo menos uma carga/geração.
        # Se não houver, adicionamos uma carga fictícia para poder rodar? Ou usamos net._ppc diretamente?
        # Alternativa: usar pp.create_ybus(net) que é interno. Vamos chamar pp.runpp(net) com tolerância.
        try:
            pp.runpp(net)
        except:
            # Se não convergir, mesmo assim o Ybus pode estar disponível
            pass
        self.controller.show_ybus(net)  # Exibe no console rich
        # Também mostrar na UI (aba Ybus)
        ybus_str = str(net._ppc["Ybus"].todense())
        self.ui.textYbus.setPlainText(ybus_str)

    def plotar_diagrama(self):
        net = self.controller.build_pandapower_net()
        fig = self.controller.plot_diagram(net)
        # Salva HTML temporário e carrega no QWebEngineView
        html = py_offline.plot(fig, output_type='div', include_plotlyjs='cdn')
        self.ui.webEngineView.setHtml(html)

    def add_bus_dialog(self):
        # Diálogo simples (pode ser implementado com QDialog)
        # Aqui apenas exemplo didático: usar inputs fixos
        from PySide6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "Nova Barra", "Nome:")
        if ok and name:
            vnom, ok = QInputDialog.getDouble(self, "Nova Barra", "Tensão nominal (kV):")
            if ok:
                tipo, ok = QInputDialog.getItem(self, "Nova Barra", "Tipo:", ["PQ", "PV", "ref"], 0, False)
                if ok:
                    self.db.insert_bus(name, vnom, tipo)
                    self.refresh_tables()

    def import_anarede(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Importar AnaREDE", "", "Arquivos PWF (*.pwf)")
        if file_path:
            self.controller.import_from_anarede(file_path)
            self.refresh_tables()

    def executar_fluxo(self):
        sucesso, resultado = self.controller.run_power_flow()
        if sucesso:
            QMessageBox.information(self, "Fluxo de Potência", "Cálculo convergiu com sucesso!")
            self.mostrar_resultados(resultado)  # Método para popular abas de resultado
        else:
            QMessageBox.warning(self, "Fluxo de Potência", f"Não convergiu: {resultado}")

    def exportar_resultados(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Exportar Resultados", "", "Excel (*.xlsx)")
        if file_path:
            try:
                self.controller.export_results_to_excel(file_path)
                QMessageBox.information(self, "Exportar", "Resultados exportados com sucesso!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", str(e))

    def edit_bus_dialog(self):
        # Lógica similar ao add_bus_dialog, mas carregando os dados existentes
        # e chamando self.db.update_bus() ao invés de insert
        pass

    def mostrar_resultados(self, net):
        # Exemplo: popular uma QTableView com net.res_bus
        model = self.ui.tableViewResultados.model()
        if model is None:
            from PySide6.QtGui import QStandardItemModel
            model = QStandardItemModel()
            self.ui.tableViewResultados.setModel(model)
        model.clear()
        # Copia os dados do DataFrame para o modelo
        df = net.res_bus
        model.setHorizontalHeaderLabels(df.columns)
        for i, row in df.iterrows():
            for j, value in enumerate(row):
                item = QStandardItem(str(value))
                model.setItem(i, j, item)
    def add_trafo_dialog(self):
        pass

    def del_bus(self):
        # Pega ID selecionado na tabela
        index = self.ui.tableViewBuses.currentIndex()
        if index.isValid():
            bus_id = int(index.sibling(index.row(), 0).data())
            self.db.delete_bus(bus_id)
            self.refresh_tables()

    def del_line(self):
        pass

    def del_trafo(self):
        pass

    def refresh_tables(self):
        # Atualiza modelos das tabelas
        # Exemplo para buses
        buses = self.db.get_all_buses()
        model = self.ui.tableViewBuses.model()
        if model is None:
            from PySide6.QtGui import QStandardItemModel
            model = QStandardItemModel()
            self.ui.tableViewBuses.setModel(model)
        model.clear()
        model.setHorizontalHeaderLabels(["ID", "Nome", "Vnom", "Tipo"])
        for row, bus in enumerate(buses):
            for col, val in enumerate(bus):
                item = QStandardItem(str(val))
                model.setItem(row, col, item)

        # Repetir para linhas e trafos...

    def closeEvent(self, event):
        self.db.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())