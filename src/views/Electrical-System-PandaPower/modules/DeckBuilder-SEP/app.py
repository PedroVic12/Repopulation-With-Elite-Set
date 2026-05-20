#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aplicação educacional para estudos de fluxo de potência e circuitos CA.
Interface com PySide6, banco SQLite, pandapower e schemdraw.
Arquivo único (self-contained) com todas as correções.
"""

import sys
import io
import sqlite3
import pandas as pd
import pandapower as pp
import networkx as nx
import plotly.graph_objects as go
import schemdraw
from schemdraw import elements as elm

# Imports do PySide6 organizados corretamente
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QMessageBox,
    QInputDialog, QTableView, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit
)
from PySide6.QtGui import QPixmap, QStandardItemModel, QStandardItem
from PySide6.QtCore import QFile, QIODevice, QByteArray, QBuffer
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWebEngineWidgets import QWebEngineView

# ----------------------------------------------------------------------
# 1. UI definida como string (frontend.ui) - SEM BOM e com quebra de linha normalizada
# ----------------------------------------------------------------------
FRONTEND_UI_XML = """<?xml version="1.0" encoding="UTF-8"?>
<ui version="4.0">
 <class>MainWindow</class>
 <widget class="QMainWindow" name="MainWindow">
  <property name="geometry">
   <rect>
    <x>0</x>
    <y>0</y>
    <width>1000</width>
    <height>700</height>
   </rect>
  </property>
  <property name="windowTitle">
   <string>Analisador de Redes Elétricas</string>
  </property>
  <widget class="QWidget" name="centralwidget">
   <layout class="QVBoxLayout" name="verticalLayout">
    <item>
     <widget class="QTabWidget" name="tabWidget">
      <property name="currentIndex">
       <number>0</number>
      </property>
      <!-- Aba: Barras -->
      <widget class="QWidget" name="tabBuses">
       <attribute name="title">
        <string>Barras</string>
       </attribute>
       <layout class="QVBoxLayout" name="verticalLayout_2">
        <item>
         <widget class="QTableView" name="tableViewBuses"/>
        </item>
        <item>
         <layout class="QHBoxLayout" name="horizontalLayout">
          <item>
           <widget class="QPushButton" name="btnAddBus">
            <property name="text">
             <string>Adicionar Barra</string>
            </property>
           </widget>
          </item>
          <item>
           <widget class="QPushButton" name="btnEditBus">
            <property name="text">
             <string>Editar Barra</string>
            </property>
           </widget>
          </item>
          <item>
           <widget class="QPushButton" name="btnDelBus">
            <property name="text">
             <string>Excluir Barra</string>
            </property>
           </widget>
          </item>
         </layout>
        </item>
       </layout>
      </widget>
      <!-- Aba: Linhas -->
      <widget class="QWidget" name="tabLines">
       <attribute name="title">
        <string>Linhas</string>
       </attribute>
       <layout class="QVBoxLayout" name="verticalLayout_3">
        <item>
         <widget class="QTableView" name="tableViewLines"/>
        </item>
        <item>
         <layout class="QHBoxLayout" name="horizontalLayout_2">
          <item>
           <widget class="QPushButton" name="btnAddLine">
            <property name="text">
             <string>Adicionar Linha</string>
            </property>
           </widget>
          </item>
          <item>
           <widget class="QPushButton" name="btnEditLine">
            <property name="text">
             <string>Editar Linha</string>
            </property>
           </widget>
          </item>
          <item>
           <widget class="QPushButton" name="btnDelLine">
            <property name="text">
             <string>Excluir Linha</string>
            </property>
           </widget>
          </item>
         </layout>
        </item>
       </layout>
      </widget>
      <!-- Aba: Transformadores -->
      <widget class="QWidget" name="tabTrafos">
       <attribute name="title">
        <string>Transformadores</string>
       </attribute>
       <layout class="QVBoxLayout" name="verticalLayout_4">
        <item>
         <widget class="QTableView" name="tableViewTrafos"/>
        </item>
        <item>
         <layout class="QHBoxLayout" name="horizontalLayout_3">
          <item>
           <widget class="QPushButton" name="btnAddTrafo">
            <property name="text">
             <string>Adicionar Transformador</string>
            </property>
           </widget>
          </item>
          <item>
           <widget class="QPushButton" name="btnEditTrafo">
            <property name="text">
             <string>Editar Transformador</string>
            </property>
           </widget>
          </item>
          <item>
           <widget class="QPushButton" name="btnDelTrafo">
            <property name="text">
             <string>Excluir Transformador</string>
            </property>
           </widget>
          </item>
         </layout>
        </item>
       </layout>
      </widget>
      <!-- Aba: Diagrama Unifilar (Plotly) -->
      <widget class="QWidget" name="tabDiagram">
       <attribute name="title">
        <string>Diagrama Unifilar</string>
       </attribute>
       <layout class="QVBoxLayout" name="verticalLayout_5">
        <item>
         <widget class="QWebEngineView" name="webEngineView" native="true"/>
        </item>
       </layout>
      </widget>
      <!-- Aba: Resultados do Fluxo -->
      <widget class="QWidget" name="tabResults">
       <attribute name="title">
        <string>Resultados</string>
       </attribute>
       <layout class="QVBoxLayout" name="verticalLayout_6">
        <item>
         <widget class="QTableView" name="tableViewResults"/>
        </item>
       </layout>
      </widget>
      <!-- Aba: Circuitos com String -->
      <widget class="QWidget" name="tabStringCircuit">
       <attribute name="title">
        <string>Circuitos (String)</string>
       </attribute>
       <layout class="QVBoxLayout" name="verticalLayout_7">
        <item>
         <layout class="QHBoxLayout" name="horizontalLayout_4">
          <item>
           <widget class="QLabel" name="label">
            <property name="text">
             <string>Notação do Circuito:</string>
            </property>
           </widget>
          </item>
          <item>
           <widget class="QLineEdit" name="lineEditCircuit">
            <property name="text">
             <string>R1-[C2,R3-[C4,R5]]</string>
            </property>
           </widget>
          </item>
          <item>
           <widget class="QPushButton" name="btnGenerateCircuit">
            <property name="text">
             <string>Gerar Diagrama</string>
            </property>
           </widget>
          </item>
         </layout>
        </item>
        <item>
         <widget class="QLabel" name="labelCircuitImage">
          <property name="text">
           <string>Diagrama será exibido aqui</string>
          </property>
          <property name="alignment">
           <set>Qt::AlignCenter</set>
          </property>
          <property name="styleSheet">
           <string>border: 1px solid gray;</string>
          </property>
          <property name="minimumSize">
           <size>
            <width>400</width>
            <height>300</height>
           </size>
          </property>
         </widget>
        </item>
        <item>
         <widget class="QPushButton" name="btnExamples">
          <property name="text">
           <string>Carregar Exemplo</string>
          </property>
         </widget>
        </item>
       </layout>
      </widget>
     </widget>
    </item>
   </layout>
  </widget>
  <widget class="QMenuBar" name="menubar">
   <property name="geometry">
    <rect>
     <x>0</x>
     <y>0</y>
     <width>1000</width>
     <height>22</height>
    </rect>
   </property>
   <widget class="QMenu" name="menuArquivo">
    <property name="title">
     <string>Arquivo</string>
    </property>
    <addaction name="actionImportar_Excel"/>
    <addaction name="actionImportar_Anarede"/>
    <addaction name="separator"/>
    <addaction name="actionExportar_Resultados"/>
    <addaction name="separator"/>
    <addaction name="actionSair"/>
   </widget>
   <widget class="QMenu" name="menuFerramentas">
    <property name="title">
     <string>Ferramentas</string>
    </property>
    <addaction name="actionCalcular_Ybus"/>
    <addaction name="actionExecutar_Fluxo"/>
    <addaction name="actionPlotar_Diagrama"/>
   </widget>
   <addaction name="menuArquivo"/>
   <addaction name="menuFerramentas"/>
  </widget>
  <widget class="QStatusBar" name="statusbar"/>
  <action name="actionImportar_Excel">
   <property name="text">
    <string>Importar Excel</string>
   </property>
  </action>
  <action name="actionImportar_Anarede">
   <property name="text">
    <string>Importar AnaREDE (.pwf)</string>
   </property>
  </action>
  <action name="actionExportar_Resultados">
   <property name="text">
    <string>Exportar Resultados para Excel</string>
   </property>
  </action>
  <action name="actionSair">
   <property name="text">
    <string>Sair</string>
   </property>
  </action>
  <action name="actionCalcular_Ybus">
   <property name="text">
    <string>Calcular Matriz Ybus</string>
   </property>
  </action>
  <action name="actionExecutar_Fluxo">
   <property name="text">
    <string>Executar Fluxo de Potência</string>
   </property>
  </action>
  <action name="actionPlotar_Diagrama">
   <property name="text">
    <string>Plotar Diagrama Unifilar</string>
   </property>
  </action>
 </widget>
 <customwidgets>
  <customwidget>
   <class>QWebEngineView</class>
   <extends>QWidget</extends>
   <header>PySide6.QtWebEngineWidgets</header>
  </customwidget>
 </customwidgets>
 <resources/>
 <connections/>
</ui>
"""

# ----------------------------------------------------------------------
# 2. Modelo (Database)
# ----------------------------------------------------------------------
class Database:
    def __init__(self, db_path="network.db"):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.executescript("""
            CREATE TABLE IF NOT EXISTS buses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                vnom REAL,
                type TEXT
            );
            CREATE TABLE IF NOT EXISTS lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                from_bus INTEGER,
                to_bus INTEGER,
                r REAL,
                x REAL,
                b REAL,
                FOREIGN KEY(from_bus) REFERENCES buses(id) ON DELETE CASCADE,
                FOREIGN KEY(to_bus) REFERENCES buses(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS transformers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                from_bus INTEGER,
                to_bus INTEGER,
                r REAL,
                x REAL,
                tap_ratio REAL,
                FOREIGN KEY(from_bus) REFERENCES buses(id) ON DELETE CASCADE,
                FOREIGN KEY(to_bus) REFERENCES buses(id) ON DELETE CASCADE
            );
        """)
        self.conn.commit()

    def insert_bus(self, name, vnom, type_):
        self.cursor.execute("INSERT INTO buses (name, vnom, type) VALUES (?,?,?)", (name, vnom, type_))
        self.conn.commit()
        return self.cursor.lastrowid

    def insert_line(self, name, from_bus, to_bus, r, x, b):
        self.cursor.execute("INSERT INTO lines (name, from_bus, to_bus, r, x, b) VALUES (?,?,?,?,?,?)",
                            (name, from_bus, to_bus, r, x, b))
        self.conn.commit()

    def insert_transformer(self, name, from_bus, to_bus, r, x, tap_ratio):
        self.cursor.execute("INSERT INTO transformers (name, from_bus, to_bus, r, x, tap_ratio) VALUES (?,?,?,?,?,?)",
                            (name, from_bus, to_bus, r, x, tap_ratio))
        self.conn.commit()

    def update_bus(self, bus_id, name, vnom, type_):
        self.cursor.execute("UPDATE buses SET name=?, vnom=?, type=? WHERE id=?", 
                            (name, vnom, type_, bus_id))
        self.conn.commit()

    def update_line(self, line_id, name, from_bus, to_bus, r, x, b):
        self.cursor.execute("""UPDATE lines SET name=?, from_bus=?, to_bus=?, r=?, x=?, b=?
                             WHERE id=?""", (name, from_bus, to_bus, r, x, b, line_id))
        self.conn.commit()

    def update_transformer(self, tf_id, name, from_bus, to_bus, r, x, tap_ratio):
        self.cursor.execute("""UPDATE transformers SET name=?, from_bus=?, to_bus=?, r=?, x=?, tap_ratio=?
                             WHERE id=?""", (name, from_bus, to_bus, r, x, tap_ratio, tf_id))
        self.conn.commit()

    def delete_bus(self, bus_id):
        self.cursor.execute("DELETE FROM buses WHERE id=?", (bus_id,))
        self.conn.commit()

    def delete_line(self, line_id):
        self.cursor.execute("DELETE FROM lines WHERE id=?", (line_id,))
        self.conn.commit()

    def delete_transformer(self, tf_id):
        self.cursor.execute("DELETE FROM transformers WHERE id=?", (tf_id,))
        self.conn.commit()

    def get_all_buses(self):
        return self.cursor.execute("SELECT * FROM buses").fetchall()

    def get_all_lines(self):
        return self.cursor.execute("SELECT * FROM lines").fetchall()

    def get_all_transformers(self):
        return self.cursor.execute("SELECT * FROM transformers").fetchall()

    def close(self):
        self.conn.close()


# ----------------------------------------------------------------------
# 3. Controlador (NetworkController)
# ----------------------------------------------------------------------
class NetworkController:
    def __init__(self, db: Database):
        self.db = db
        self.current_net = None

    def import_from_excel(self, file_path):
        """Lê planilhas com nomes definidos: 'barras', 'linhas', 'transformadores'"""
        df_buses = pd.read_excel(file_path, sheet_name='barras')
        df_lines = pd.read_excel(file_path, sheet_name='linhas')
        df_trafos = pd.read_excel(file_path, sheet_name='transformadores')

        for _, row in df_buses.iterrows():
            self.db.insert_bus(row['nome'], row['vnom'], row['tipo'])
        for _, row in df_lines.iterrows():
            self.db.insert_line(row['nome'], row['de'], row['para'], row['r'], row['x'], row['b'])
        for _, row in df_trafos.iterrows():
            self.db.insert_transformer(row['nome'], row['de'], row['para'], row['r'], row['x'], row['tap'])

    def import_from_anarede(self, file_path):
        """Esboço de importação de arquivo .pwf (AnaREDE)"""
        QMessageBox.information(None, "Info", f"Importação de {file_path} não implementada completamente. Simulação de inserção manual.")
        # Implementação real depende do formato específico

    def build_pandapower_net(self):
        """Cria uma rede pandapower a partir do banco SQLite"""
        net = pp.create_empty_network()
        bus_map = {}

        for bus in self.db.get_all_buses():
            bid = bus[0]
            name = bus[1]
            vnom = bus[2]
            bus_type = bus[3]
            idx = pp.create_bus(net, name=name, vn_kv=vnom, type=bus_type)
            bus_map[bid] = idx

        for line in self.db.get_all_lines():
            _, name, from_b, to_b, r, x, b = line
            pp.create_line_from_parameters(
                net, from_bus=bus_map[from_b], to_bus=bus_map[to_b],
                length_km=1.0, r_ohm_per_km=r, x_ohm_per_km=x, c_nf_per_km=b*1e9,
                max_i_ka=1.0, name=name
            )

        for tf in self.db.get_all_transformers():
            _, name, from_b, to_b, r, x, tap = tf
            pp.create_transformer_from_parameters(
                net, hv_bus=bus_map[from_b], lv_bus=bus_map[to_b],
                sn_mva=100, vn_hv_kv=100, vn_lv_kv=100, vkr_percent=r*100,
                vk_percent=x*100, pfe_kw=0, i0_percent=0, tap_side="hv",
                tap_neutral=1.0, tap_step_percent=tap, name=name
            )
        return net

    def run_power_flow(self):
        """Executa o fluxo de potência e armazena a rede em current_net"""
        self.current_net = self.build_pandapower_net()
        try:
            pp.runpp(self.current_net)
            return True, self.current_net
        except pp.LoadflowNotConverged as e:
            return False, str(e)

    def plot_diagram(self, net):
        """Gera diagrama unifilar interativo com plotly"""
        from pandapower.plotting.plotly import simple_plotly
        fig = simple_plotly(net, bus_size=10, line_width=2, trafo=True, plot_line_names=True, plot_bus_names=True)
        return fig

    def export_results_to_excel(self, file_path):
        """Exporta as tabelas de resultado para Excel"""
        if self.current_net is None:
            raise ValueError("Nenhum resultado de fluxo disponível.")
        with pd.ExcelWriter(file_path) as writer:
            self.current_net.res_bus.to_excel(writer, sheet_name='Resultados_Barras')
            self.current_net.res_line.to_excel(writer, sheet_name='Resultados_Linhas')
            self.current_net.res_trafo.to_excel(writer, sheet_name='Resultados_Trafos')
            self.current_net.res_ext_grid.to_excel(writer, sheet_name='Resultados_RedeExterna')
            self.current_net.bus.to_excel(writer, sheet_name='Barras')
            self.current_net.line.to_excel(writer, sheet_name='Linhas')
            self.current_net.trafo.to_excel(writer, sheet_name='Transformadores')


# ----------------------------------------------------------------------
# 4. Gerador de Circuitos com String (StringCircuitGenerator)
# ----------------------------------------------------------------------
class StringCircuitGenerator:
    """
    Gera diagramas de circuitos a partir de uma notação em string.
    Atualmente mapeia palavras-chave para cinco circuitos predefinidos:
      - 'RC'          : Circuito RC série
      - 'RLC'         : Circuito RLC série
      - 'RLC paralelo': Circuito RLC paralelo
      - 'CA simples'  : Circuito CA com fonte senoidal, resistor e indutor
      - 'duas malhas' : Circuito com duas malhas acopladas
    Se a string não for reconhecida, retorna o circuito RC série.
    """

    def __init__(self):
        self.drawing = None

    def _generate_rc_series(self):
        d = schemdraw.Drawing()
        d += elm.Resistor().label('R1')
        d += elm.Capacitor().label('C1')
        d += elm.Line().dot()
        return d

    def _generate_rlc_series(self):
        d = schemdraw.Drawing()
        d += elm.Resistor().label('R')
        d += elm.Inductor().label('L')
        d += elm.Capacitor().label('C')
        d += elm.Line().dot()
        return d

    def _generate_rlc_parallel(self):
        d = schemdraw.Drawing()
        d += elm.Dot()
        d += elm.Resistor().down().label('R')
        d += elm.Dot()
        d += elm.Line().up().color('white')
        d += elm.Dot()
        d += elm.Inductor().down().label('L')
        d += elm.Dot()
        d += elm.Line().up().color('white')
        d += elm.Dot()
        d += elm.Capacitor().down().label('C')
        d += elm.Dot()
        d += elm.Line().left()
        return d

    def _generate_ac_simple(self):
        d = schemdraw.Drawing()
        d += elm.SourceSin().label('V_{AC}')
        d += elm.Resistor().right().label('R')
        d += elm.Inductor().down().label('L')
        d += elm.Line().left().tox(d.here[0]-4)
        d += elm.Line().up().toy(d.here[1]+2)
        d += elm.Line().right().color('white')
        d += elm.CurrentLabel(top=False, ofst=0.5).at(d.here).label('I')
        return d

    def _generate_two_mesh(self):
        d = schemdraw.Drawing()
        V = elm.SourceV().label('V1')
        d += V
        d += elm.Resistor().right().label('R1')
        d += elm.Dot()
        R2 = elm.Resistor().down().label('R2')
        d += R2
        d += elm.Line().left().tox(V.start)
        d += elm.Line().up().toy(V.start)
        d += elm.Dot().at(R2.end)
        d += elm.Resistor().right().label('R3')
        d += elm.Dot()
        d += elm.Line().down().toy(d.here[1]-2)
        d += elm.Line().left().tox(R2.end)
        d += elm.CurrentLabel(top=False, ofst=0.3).at(V).label('I_1')
        d += elm.CurrentLabel(top=False, ofst=0.3).at(R3).label('I_2')
        return d

    def generate_from_notation(self, notation):
        examples = {
            'RC': self._generate_rc_series,
            'RLC': self._generate_rlc_series,
            'RLC paralelo': self._generate_rlc_parallel,
            'CA simples': self._generate_ac_simple,
            'duas malhas': self._generate_two_mesh,
        }
        key = notation.strip()
        if key in examples:
            return examples[key]()
        else:
            return self._generate_rc_series()

    def draw_to_pixmap(self, notation, width=400, height=300):
        drawing = self.generate_from_notation(notation)
        img_buffer = io.BytesIO()
        drawing.save(img_buffer, format='png', dpi=100)
        img_buffer.seek(0)
        pixmap = QPixmap()
        pixmap.loadFromData(img_buffer.getvalue(), 'PNG')
        return pixmap.scaled(width, height)


# ----------------------------------------------------------------------
# 5. Janela Principal (MainWindow)
# ----------------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Carrega UI a partir da string XML - removendo qualquer BOM
        loader = QUiLoader()
        ui_bytes = FRONTEND_UI_XML.encode('utf-8')
        ui_buffer = QBuffer()
        ui_buffer.setData(ui_bytes)
        ui_buffer.open(QIODevice.ReadOnly)

        self.ui = loader.load(ui_buffer, self)
        ui_buffer.close()

        if self.ui is None:
            # Falha no carregamento - mostra erro e cria um fallback
            error = loader.errorString()
            print(f"Erro ao carregar UI: {error}")
            # Cria um widget simples para não deixar a tela branca
            from PySide6.QtWidgets import QLabel, QVBoxLayout
            fallback = QWidget()
            layout = QVBoxLayout(fallback)
            layout.addWidget(QLabel(f"Falha ao carregar UI: {error}"))
            layout.addWidget(QLabel("Verifique o formato do arquivo .ui"))
            self.setCentralWidget(fallback)
        else:
            self.setCentralWidget(self.ui)
            print("UI carregada com sucesso!")
            # Opcional: lista os widgets filhos para depuração
            print("Widgets na UI:", [child.objectName() for child in self.ui.findChildren(QWidget)])
        self.setCentralWidget(self.ui)

        # Inicializa banco e controlador
        self.db = Database()
        self.controller = NetworkController(self.db)

        # Inicializa gerador de circuitos
        self.circuit_gen = StringCircuitGenerator()
        self.example_index = 0
        self.examples_list = ['RC', 'RLC', 'RLC paralelo', 'CA simples', 'duas malhas']

        # Conecta ações da barra de menus
        self.ui.actionImportar_Excel.triggered.connect(self.import_excel)
        self.ui.actionImportar_Anarede.triggered.connect(self.import_anarede)
        self.ui.actionExportar_Resultados.triggered.connect(self.export_results)
        self.ui.actionSair.triggered.connect(self.close)
        self.ui.actionCalcular_Ybus.triggered.connect(self.calcular_ybus)
        self.ui.actionExecutar_Fluxo.triggered.connect(self.executar_fluxo)
        self.ui.actionPlotar_Diagrama.triggered.connect(self.plotar_diagrama)

        # Conecta botões de adicionar/editar/excluir
        self.ui.btnAddBus.clicked.connect(self.add_bus_dialog)
        self.ui.btnEditBus.clicked.connect(self.edit_bus_dialog)
        self.ui.btnDelBus.clicked.connect(self.del_bus)
        self.ui.btnAddLine.clicked.connect(self.add_line_dialog)
        self.ui.btnEditLine.clicked.connect(self.edit_line_dialog)
        self.ui.btnDelLine.clicked.connect(self.del_line)
        self.ui.btnAddTrafo.clicked.connect(self.add_trafo_dialog)
        self.ui.btnEditTrafo.clicked.connect(self.edit_trafo_dialog)
        self.ui.btnDelTrafo.clicked.connect(self.del_trafo)

        # Conecta botões da aba de circuitos string
        self.ui.btnGenerateCircuit.clicked.connect(self.generate_circuit)
        self.ui.btnExamples.clicked.connect(self.load_circuit_example)

        # Atualiza as tabelas
        self.refresh_tables()

    # ------------------------------------------------------------------
    # Métodos para importação/exportação
    # ------------------------------------------------------------------
    def import_excel(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Importar Excel", "", "Excel (*.xlsx *.xls)")
        if file_path:
            try:
                self.controller.import_from_excel(file_path)
                self.refresh_tables()
                QMessageBox.information(self, "Sucesso", "Dados importados com sucesso!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Falha na importação: {e}")

    def import_anarede(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Importar AnaREDE", "", "Arquivos PWF (*.pwf)")
        if file_path:
            self.controller.import_from_anarede(file_path)
            self.refresh_tables()

    def export_results(self):
        if self.controller.current_net is None:
            QMessageBox.warning(self, "Aviso", "Nenhum resultado disponível. Execute o fluxo primeiro.")
            return
        file_path, _ = QFileDialog.getSaveFileName(self, "Exportar Resultados", "", "Excel (*.xlsx)")
        if file_path:
            try:
                self.controller.export_results_to_excel(file_path)
                QMessageBox.information(self, "Sucesso", "Resultados exportados!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", str(e))

    # ------------------------------------------------------------------
    # Métodos de cálculo e plotagem
    # ------------------------------------------------------------------
    def calcular_ybus(self):
        net = self.controller.build_pandapower_net()
        try:
            pp.runpp(net)
        except:
            pass  # Ybus pode estar disponível mesmo sem convergência
        ybus = net._ppc["Ybus"].todense()
        ybus_str = str(ybus)
        QMessageBox.information(self, "Matriz Ybus", ybus_str[:1000] + "..." if len(ybus_str)>1000 else ybus_str)

    def executar_fluxo(self):
        sucesso, resultado = self.controller.run_power_flow()
        if sucesso:
            QMessageBox.information(self, "Fluxo de Potência", "Cálculo convergiu!")
            self.mostrar_resultados(self.controller.current_net)
        else:
            QMessageBox.warning(self, "Fluxo de Potência", f"Não convergiu: {resultado}")

    def plotar_diagrama(self):
        if self.controller.current_net is None:
            QMessageBox.warning(self, "Aviso", "Execute o fluxo de potência primeiro.")
            return
        fig = self.controller.plot_diagram(self.controller.current_net)
        from plotly.offline import plot
        html = plot(fig, output_type='div', include_plotlyjs='cdn')
        self.ui.webEngineView.setHtml(html)

    # ------------------------------------------------------------------
    # CRUD de Barras (diálogos simplificados)
    # ------------------------------------------------------------------
    def add_bus_dialog(self):
        name, ok = QInputDialog.getText(self, "Nova Barra", "Nome:")
        if not ok or not name:
            return
        vnom, ok = QInputDialog.getDouble(self, "Nova Barra", "Tensão nominal (kV):")
        if not ok:
            return
        tipo, ok = QInputDialog.getItem(self, "Nova Barra", "Tipo:", ["PQ", "PV", "ref"], 0, False)
        if ok:
            self.db.insert_bus(name, vnom, tipo)
            self.refresh_tables()

    def edit_bus_dialog(self):
        index = self.ui.tableViewBuses.currentIndex()
        if not index.isValid():
            QMessageBox.warning(self, "Editar", "Selecione uma barra para editar.")
            return
        bus_id = int(index.sibling(index.row(), 0).data())
        name = index.sibling(index.row(), 1).data()
        vnom = float(index.sibling(index.row(), 2).data())
        tipo = index.sibling(index.row(), 3).data()
        new_name, ok = QInputDialog.getText(self, "Editar Barra", "Nome:", text=name)
        if not ok:
            return
        new_vnom, ok = QInputDialog.getDouble(self, "Editar Barra", "Tensão nominal (kV):", value=vnom)
        if not ok:
            return
        new_tipo, ok = QInputDialog.getItem(self, "Editar Barra", "Tipo:", ["PQ", "PV", "ref"], 
                                            current=["PQ","PV","ref"].index(tipo), editable=False)
        if ok:
            self.db.update_bus(bus_id, new_name, new_vnom, new_tipo)
            self.refresh_tables()

    def del_bus(self):
        index = self.ui.tableViewBuses.currentIndex()
        if index.isValid():
            bus_id = int(index.sibling(index.row(), 0).data())
            self.db.delete_bus(bus_id)
            self.refresh_tables()

    def add_line_dialog(self):
        name, ok = QInputDialog.getText(self, "Nova Linha", "Nome:")
        if not ok:
            return
        from_bus, ok = QInputDialog.getInt(self, "Nova Linha", "ID da barra de origem:")
        if not ok:
            return
        to_bus, ok = QInputDialog.getInt(self, "Nova Linha", "ID da barra de destino:")
        if not ok:
            return
        r, ok = QInputDialog.getDouble(self, "Nova Linha", "Resistência (pu):")
        if not ok:
            return
        x, ok = QInputDialog.getDouble(self, "Nova Linha", "Reatância (pu):")
        if not ok:
            return
        b, ok = QInputDialog.getDouble(self, "Nova Linha", "Susceptância (pu):")
        if ok:
            self.db.insert_line(name, from_bus, to_bus, r, x, b)
            self.refresh_tables()

    def edit_line_dialog(self):
        index = self.ui.tableViewLines.currentIndex()
        if not index.isValid():
            return
        line_id = int(index.sibling(index.row(), 0).data())
        # Para simplificar, não implementaremos a edição completa aqui
        QMessageBox.information(self, "Editar", "Implementação de edição de linha similar à barra (pendente).")

    def del_line(self):
        index = self.ui.tableViewLines.currentIndex()
        if index.isValid():
            line_id = int(index.sibling(index.row(), 0).data())
            self.db.delete_line(line_id)
            self.refresh_tables()

    def add_trafo_dialog(self):
        name, ok = QInputDialog.getText(self, "Novo Transformador", "Nome:")
        if not ok:
            return
        from_bus, ok = QInputDialog.getInt(self, "Novo Transformador", "ID da barra de origem (HV):")
        if not ok:
            return
        to_bus, ok = QInputDialog.getInt(self, "Novo Transformador", "ID da barra de destino (LV):")
        if not ok:
            return
        r, ok = QInputDialog.getDouble(self, "Novo Transformador", "Resistência (pu):")
        if not ok:
            return
        x, ok = QInputDialog.getDouble(self, "Novo Transformador", "Reatância (pu):")
        if not ok:
            return
        tap, ok = QInputDialog.getDouble(self, "Novo Transformador", "Tap ratio (pu):")
        if ok:
            self.db.insert_transformer(name, from_bus, to_bus, r, x, tap)
            self.refresh_tables()

    def edit_trafo_dialog(self):
        index = self.ui.tableViewTrafos.currentIndex()
        if not index.isValid():
            return
        QMessageBox.information(self, "Editar", "Implementação de edição de transformador pendente.")

    def del_trafo(self):
        index = self.ui.tableViewTrafos.currentIndex()
        if index.isValid():
            tf_id = int(index.sibling(index.row(), 0).data())
            self.db.delete_transformer(tf_id)
            self.refresh_tables()

    # ------------------------------------------------------------------
    # Atualização das tabelas na interface
    # ------------------------------------------------------------------
    def refresh_tables(self):
        # Barras
        buses = self.db.get_all_buses()
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(["ID", "Nome", "Vnom", "Tipo"])
        for row, bus in enumerate(buses):
            for col, val in enumerate(bus):
                item = QStandardItem(str(val))
                model.setItem(row, col, item)
        self.ui.tableViewBuses.setModel(model)

        # Linhas
        lines = self.db.get_all_lines()
        model_lines = QStandardItemModel()
        model_lines.setHorizontalHeaderLabels(["ID", "Nome", "De", "Para", "R", "X", "B"])
        for row, line in enumerate(lines):
            for col, val in enumerate(line):
                item = QStandardItem(str(val))
                model_lines.setItem(row, col, item)
        self.ui.tableViewLines.setModel(model_lines)

        # Transformadores
        trafos = self.db.get_all_transformers()
        model_trafos = QStandardItemModel()
        model_trafos.setHorizontalHeaderLabels(["ID", "Nome", "De", "Para", "R", "X", "Tap"])
        for row, tf in enumerate(trafos):
            for col, val in enumerate(tf):
                item = QStandardItem(str(val))
                model_trafos.setItem(row, col, item)
        self.ui.tableViewTrafos.setModel(model_trafos)

    def mostrar_resultados(self, net):
        model = QStandardItemModel()
        if net.res_bus.empty:
            model.setHorizontalHeaderLabels(["Sem resultados"])
        else:
            model.setHorizontalHeaderLabels(net.res_bus.columns)
            for i, row in net.res_bus.iterrows():
                for j, val in enumerate(row):
                    item = QStandardItem(str(val))
                    model.setItem(i, j, item)
        self.ui.tableViewResults.setModel(model)

    # ------------------------------------------------------------------
    # Métodos para a aba de circuitos string
    # ------------------------------------------------------------------
    def generate_circuit(self):
        notation = self.ui.lineEditCircuit.text()
        pixmap = self.circuit_gen.draw_to_pixmap(notation)
        self.ui.labelCircuitImage.setPixmap(pixmap)
        self.ui.labelCircuitImage.setScaledContents(True)

    def load_circuit_example(self):
        notation = self.examples_list[self.example_index % len(self.examples_list)]
        self.ui.lineEditCircuit.setText(notation)
        self.generate_circuit()
        self.example_index += 1

    # ------------------------------------------------------------------
    # Finalização
    # ------------------------------------------------------------------
    def closeEvent(self, event):
        self.db.close()
        event.accept()


# ----------------------------------------------------------------------
# 6. Ponto de entrada
# ----------------------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    print("Aplicação iniciada. Interface gráfica carregada com sucesso.")
    window.show()
    sys.exit(app.exec())