import sys
import sqlite3
import pyodbc
import webbrowser
import os
import re
from pathlib import Path
from datetime import datetime
from io import StringIO
import tempfile

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QComboBox, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QScrollArea, QFrame, QDialog, QTextBrowser, QTabWidget,
    QProgressBar, QStackedWidget, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QFont

try:
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    from PySide6.QtWebEngineWidgets import QWebEngineView
except ImportError:
    print("Dependências críticas (pandas, plotly, PySide6-WebEngine) não encontradas.")
    pd = px = go = QWebEngineView = None

try:
    from ansi2html import Ansi2HTMLConverter
    ansi_converter = Ansi2HTMLConverter(dark_bg=True, scheme="xterm")
except ImportError:
    ansi_converter = None

#! Importação PVRV do script de ETL e Classes Criadas
from ..ScrapperPDF.src.Palkia_GUI import PalkiaGUIWindowGUI
from Palkia_GUI import  PalkiaWindowGUI


# ==============================================================================
#! ESTILOS CSS
# Garante que o arquivo styles.py esteja na mesma pasta
# ==============================================================================

try:
    from styles import STYLESHEET, APP_STYLES
except ImportError:
    print("AVISO: 'styles.py' não encontrado. Usando estilos padrão.")
    STYLESHEET = "QWidget { background-color: #111827; color: white; }"
    APP_STYLES = STYLESHEET


# ==============================================================================
# MODELO DE DADOS (DATABASE)
# ==============================================================================

class DashboardDB:
    def __init__(self, db_path):
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Arquivo de banco de dados não encontrado: {self.db_path}")

        self.db_type = 'access' if self.db_path.suffix.lower() == '.accdb' else 'sqlite'
        
        if self.db_type == 'sqlite':
            self.tbl_empresas = 'empresas'
            self.tbl_anotacao = 'anotacao'
            self.tbl_valores = 'valores_must'
        else:
            self.tbl_empresas = 'tb_empresas'
            self.tbl_anotacao = 'tb_anotacao'
            self.tbl_valores = 'tb_valores_must'

        if self.db_type == 'sqlite':
            self._ensure_approval_columns_exist_sqlite()

        self.company_links = {
            'SUL SUDESTE': 'https://onsbr-my.sharepoint.com/:b:/g/personal/pedrovictor_veras_ons_org_br/EbWWq1r7MnxPvOejycbr82cB5a_rN_PCsDMDjp9r3bF3Ng?e=C7dxKN',
            'ELETROPAULO': 'https://onsbr-my.sharepoint.com/:b:/g/personal/pedrovictor_veras_ons_org_br/EXzdo_ClziVDrnOHTiGzoysBdqgci92tpuKYN2xKIjPQvw?e=kzrFho',
            'PIRATININGA': 'https://onsbr-my.sharepoint.com/:b:/g/personal/pedrovictor_veras_ons_org_br/EZGF1uzc1opGujAlp1fwNqcBoLnXsAt532XFPbNrNCwEvQ?e=nEOCn9',
            'NEOENERGIA ELEKTRO': 'https://onsbr-my.sharepoint.com/:b:/g/personal/pedrovictor_veras_ons_org_br/Eet4gEXFfDNEoPMejiLnMaQBVW1ubN1TxOIvMtLY0yUfPA?e=WruSdk',
            'JAGUARI': 'https://onsbr-my.sharepoint.com/:b:/g/personal/pedrovictor_veras_ons_org_br/EXzdo_ClziVDrnOHTiGzoysBdqgci92tpuKYN2xKIjPQvw?e=b2yXV2',
            'CPFL PAULISTA': 'https://onsbr-my.sharepoint.com/:b:/g/personal/pedrovictor_veras_ons_org_br/EbWWq1r7MnxPvOejycbr82cB5a_rN_PCsDMDjp9r3bF3Ng?e=C7dxKN'
        }

    def _get_connection(self):
        if self.db_type == 'sqlite':
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn
        else:
            conn_str = (r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};" fr"DBQ={self.db_path};")
            return pyodbc.connect(conn_str)

    def _execute_query(self, query, params=(), fetch_one=False):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                columns = [column[0] for column in cursor.description]
                if fetch_one:
                    result = cursor.fetchone()
                    return dict(zip(columns, result)) if result else None
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except (sqlite3.Error, pyodbc.Error) as e:
            print(f"Erro de banco de dados (leitura): {e}")
            return [] if not fetch_one else None

    def _execute_write_query(self, query, params=()):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
            return True
        except (sqlite3.Error, pyodbc.Error) as e:
            print(f"Erro de banco de dados (escrita): {e}")
            return False

    def _ensure_approval_columns_exist_sqlite(self):
        try:
            table_info = self._execute_query(f"PRAGMA table_info({self.tbl_anotacao})")
            column_names = [col['name'] for col in table_info]
            if 'aprovado_por' not in column_names:
                self._execute_write_query(f"ALTER TABLE {self.tbl_anotacao} ADD COLUMN aprovado_por TEXT;")
            if 'data_aprovacao' not in column_names:
                self._execute_write_query(f"ALTER TABLE {self.tbl_anotacao} ADD COLUMN data_aprovacao TEXT;")
        except Exception as e:
            print(f"Erro ao verificar tabela '{self.tbl_anotacao}': {e}")
            
    def get_kpi_summary(self):
        query_companies = f"SELECT COUNT(*) as count FROM {self.tbl_empresas};"
        query_points = f"SELECT COUNT(*) as count FROM {self.tbl_anotacao};"
        query_remarks = f"SELECT COUNT(*) as count FROM {self.tbl_anotacao} WHERE anotacao_geral IS NOT NULL AND anotacao_geral <> '' AND anotacao_geral <> 'nan';"
        try:
            total_companies = self._execute_query(query_companies, fetch_one=True)['count']
            total_points = self._execute_query(query_points, fetch_one=True)['count']
            points_with_remarks = self._execute_query(query_remarks, fetch_one=True)['count']
            percentage = (points_with_remarks / total_points * 100) if total_points > 0 else 0
            return {
                'unique_companies': total_companies,
                'total_points': total_points,
                'points_with_remarks': points_with_remarks,
                'percentage_with_remarks': f"{percentage:.1f}%"
            }
        except (TypeError, KeyError, ZeroDivisionError) as e:
            print(f"Erro ao calcular KPIs: {e}")
            return {'unique_companies': 0, 'total_points': 0, 'points_with_remarks': 0, 'percentage_with_remarks': '0.0%'}

    def get_company_analysis(self):
        query = f"""
            SELECT e.nome_empresa, COUNT(a.id_conexao) as total,
                   SUM(IIF(a.anotacao_geral IS NOT NULL AND a.anotacao_geral <> '' AND a.anotacao_geral <> 'nan', 1, 0)) as with_remarks
            FROM {self.tbl_empresas} AS e INNER JOIN {self.tbl_anotacao} AS a ON e.id_empresa = a.id_empresa
            GROUP BY e.nome_empresa ORDER BY e.nome_empresa;
        """
        return self._execute_query(query)
        
    def get_yearly_must_stats(self):
        query = f"SELECT ano, periodo, SUM(valor) as total_valor FROM {self.tbl_valores} GROUP BY ano, periodo ORDER BY ano, periodo;"
        return self._execute_query(query)

    def get_unique_companies(self):
        query = f"SELECT nome_empresa FROM {self.tbl_empresas} ORDER BY nome_empresa;"
        return [row['nome_empresa'] for row in self._execute_query(query)]

    def get_unique_tensions(self):
        query = f"SELECT DISTINCT tensao_kv FROM {self.tbl_anotacao} WHERE tensao_kv IS NOT NULL ORDER BY tensao_kv;"
        return [str(row['tensao_kv']) for row in self._execute_query(query)]

    def get_all_connection_points(self, filters=None):
        query = f"""
            SELECT emp.nome_empresa, a.cod_ons, a.tensao_kv, a.anotacao_geral, a.aprovado_por, a.data_aprovacao
            FROM ({self.tbl_empresas} AS emp
            INNER JOIN {self.tbl_anotacao} AS a ON emp.id_empresa = a.id_empresa)
        """
        conditions, params = [], []
        if filters:
            year_filter = filters.get("year")
            if year_filter and year_filter != "Todos":
                conditions.append(f"a.id_conexao IN (SELECT vm.id_conexao FROM {self.tbl_valores} vm WHERE vm.ano = ?)")
                params.append(int(year_filter))
            if filters.get("company") and filters["company"] != "Todas":
                conditions.append("emp.nome_empresa = ?")
                params.append(filters["company"])
            if filters.get("search"):
                search_term = f"%{filters['search']}%"
                conditions.append("(a.cod_ons LIKE ? OR a.anotacao_geral LIKE ?)")
                params.extend([search_term, search_term])
            if filters.get("tension") and filters["tension"] != "Todas":
                conditions.append("a.tensao_kv = ?")
                params.append(int(filters["tension"]))
            if filters.get("status") == "Com Ressalva":
                conditions.append("(a.anotacao_geral IS NOT NULL AND a.anotacao_geral <> '' AND a.anotacao_geral <> 'nan')")
            elif filters.get("status") == "Aprovado":
                conditions.append("(a.aprovado_por IS NOT NULL AND a.aprovado_por <> '')")
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY emp.nome_empresa, a.cod_ons;"
        
        results = self._execute_query(query, tuple(params))
        for row in results:
            normalized_empresa = str(row['nome_empresa']).strip().upper()
            row['arquivo_referencia'] = self.company_links.get(normalized_empresa, '')
        return results

    def get_must_history_for_point(self, cod_ons):
        query = f"""
            SELECT vm.ano, vm.periodo, vm.valor
            FROM {self.tbl_valores} AS vm
            INNER JOIN {self.tbl_anotacao} AS a ON vm.id_conexao = a.id_conexao
            WHERE a.cod_ons = ? ORDER BY vm.ano, vm.periodo;
        """
        return self._execute_query(query, (cod_ons,))

    def approve_point(self, cod_ons, approver_name):
        query = f"UPDATE {self.tbl_anotacao} SET aprovado_por = ?, data_aprovacao = ? WHERE cod_ons = ?;"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return self._execute_write_query(query, (approver_name, timestamp, cod_ons))
        
    def get_data_for_charts(self):
        points_per_company_query = f"SELECT e.nome_empresa, COUNT(a.id_conexao) as count FROM {self.tbl_empresas} AS e INNER JOIN {self.tbl_anotacao} AS a ON e.id_empresa = a.id_empresa GROUP BY e.nome_empresa"
        remarks_summary_query = f"SELECT SUM(IIF(anotacao_geral IS NOT NULL AND anotacao_geral <> '' AND anotacao_geral <> 'nan', 1, 0)) as with_remarks, COUNT(id_conexao) as total FROM {self.tbl_anotacao}"
        yearly_sum_query = f"SELECT ano, SUM(valor) as total_valor FROM {self.tbl_valores} GROUP BY ano ORDER BY ano"
        return {
            "points_per_company": self._execute_query(points_per_company_query),
            "remarks_summary": self._execute_query(remarks_summary_query, fetch_one=True),
            "yearly_sum": self._execute_query(yearly_sum_query),
        }


# ==============================================================================
# DIÁLOGOS
# ==============================================================================

class DetailsDialog(QDialog):
    def __init__(self, annotation_content, history_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Detalhes do Ponto de Conexão")
        self.setMinimumSize(700, 500)
        self.setStyleSheet(STYLESHEET)
        
        layout = QVBoxLayout(self)
        tab_widget = QTabWidget()

        ressalva_widget = QWidget()
        ressalva_layout = QVBoxLayout(ressalva_widget)
        text_view = QTextBrowser()
        text_view.setPlainText(annotation_content if annotation_content else "Nenhuma ressalva.")
        ressalva_layout.addWidget(text_view)
        
        history_widget = QWidget()
        history_layout = QVBoxLayout(history_widget)
        history_table = QTableWidget()
        history_table.setColumnCount(3)
        history_table.setHorizontalHeaderLabels(["Ano", "Período", "Valor MUST"])
        history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        history_table.setRowCount(len(history_data))
        
        for i, row in enumerate(history_data):
            valor = row.get('valor')
            valor_str = f"{valor}" if valor is not None else "N/D"
            history_table.setItem(i, 0, QTableWidgetItem(str(row['ano'])))
            history_table.setItem(i, 1, QTableWidgetItem(str(row['periodo'])))
            history_table.setItem(i, 2, QTableWidgetItem(valor_str))
        
        history_layout.addWidget(history_table)
        
        tab_widget.addTab(ressalva_widget, "Ressalva")
        tab_widget.addTab(history_widget, "Histórico de Valores")
        
        close_button = QPushButton("Fechar")
        close_button.clicked.connect(self.accept)
        
        layout.addWidget(tab_widget)
        layout.addWidget(close_button, 0, Qt.AlignmentFlag.AlignRight)

class ApprovalDialog(QDialog):
    def __init__(self, cod_ons, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Aprovar Solicitação")
        self.setStyleSheet(STYLESHEET)
        self.setMinimumWidth(400)
        self.approver_name = ""
        
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"<b>Ponto de Conexão:</b> {cod_ons}"))
        layout.addWidget(QLabel("Digite seu nome para confirmar:"))
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nome do Responsável")
        layout.addWidget(self.name_input)
        
        button_layout = QHBoxLayout()
        self.confirm_button = QPushButton("Confirmar")
        self.confirm_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.confirm_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
    
    def accept(self):
        if self.name_input.text().strip():
            self.approver_name = self.name_input.text().strip()
            super().accept()
        else:
            self.name_input.setStyleSheet("border: 1px solid red;")

# ==============================================================================
# WIDGETS CUSTOMIZADOS
# ==============================================================================

class CompanyCard(QFrame):
    def __init__(self, company_name, stats, parent=None):
        super().__init__(parent)
        self.setObjectName("kpiCard")
        
        with_remarks = stats.get('with_remarks', 0)
        total = stats.get('total', 0)
        percentage = (with_remarks / total * 100) if total > 0 else 0
        
        layout = QVBoxLayout(self)
        name_label = QLabel(company_name)
        name_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        
        stats_label = QLabel(f"Com Ressalvas: {with_remarks} / {total}")
        stats_label.setObjectName("kpiTitle")
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(int(percentage))
        self.progress_bar.setFormat(f"{percentage:.1f}%")
        
        layout.addWidget(name_label)
        layout.addWidget(stats_label)
        layout.addWidget(self.progress_bar)

# ==============================================================================
# TELAS DA APLICAÇÃO (Widgets)
# ==============================================================================


class DashboardMainWidget(QWidget):
    def __init__(self, db_model, parent=None):
        super().__init__(parent)
        self.db = db_model
        self._setup_ui()
        self._load_initial_data()
    
    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(20)
        
        self._create_header()
        self.main_layout.addWidget(self._create_kpi_container())
        self.main_layout.addWidget(self._create_company_analysis_container())
        self.main_layout.addWidget(self._create_yearly_stats_container())
        self.main_layout.addWidget(self._create_filters_container())
        self.main_layout.addWidget(self._create_details_table_container())
        self.main_layout.addStretch()
    
    def _create_header(self):
        header_layout = QVBoxLayout()
        title = QLabel("Dashboard de Análise de Pontos MUST")
        title.setObjectName("headerTitle")
        subtitle = QLabel("Visão geral das solicitações e ressalvas por empresa e ponto de conexão")
        subtitle.setObjectName("headerSubtitle")
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        self.main_layout.addLayout(header_layout)
    
    def _create_kpi_container(self):
        container = QFrame()
        container.setObjectName("container")
        layout = QVBoxLayout(container)
        layout.addWidget(QLabel("Visão Geral das Solicitações", objectName="sectionTitle"))
        
        self.kpi_layout = QHBoxLayout()
        self.kpi_layout.setSpacing(20)
        self.kpi_cards = {
            "unique_companies": self._create_kpi_card("Total de Empresas", "0"),
            "total_points": self._create_kpi_card("Total de Pontos", "0"),
            "points_with_remarks": self._create_kpi_card("Pontos com Ressalvas", "0"),
            "percentage_with_remarks": self._create_kpi_card("% com Ressalvas", "0.0%"),
        }
        for card in self.kpi_cards.values():
            self.kpi_layout.addWidget(card)
        
        layout.addLayout(self.kpi_layout)
        return container
    
    def _create_kpi_card(self, title_text, value_text):
        card = QFrame()
        card.setObjectName("kpiCard")
        card_layout = QVBoxLayout(card)
        
        title = QLabel(title_text)
        value = QLabel(value_text)
        title.setObjectName("kpiTitle")
        value.setObjectName("kpiValue")
        
        card_layout.addWidget(title)
        card_layout.addWidget(value)
        return card
    
    def _create_company_analysis_container(self):
        container = QFrame()
        container.setObjectName("container")
        layout = QVBoxLayout(container)
        layout.addWidget(QLabel("Análise por Empresa", objectName="sectionTitle"))
        
        self.company_analysis_layout = QGridLayout()
        self.company_analysis_layout.setSpacing(20)
        layout.addLayout(self.company_analysis_layout)
        return container
    
    def _create_yearly_stats_container(self):
        container = QFrame()
        container.setObjectName("container")
        layout = QVBoxLayout(container)
        layout.addWidget(QLabel("Estatísticas Anuais MUST", objectName="sectionTitle"))
        
        self.yearly_stats_layout = QGridLayout()
        self.yearly_stats_layout.setSpacing(20)
        layout.addLayout(self.yearly_stats_layout)
        return container
    
    def _create_filters_container(self):
        container = QFrame()
        container.setObjectName("container")
        layout = QVBoxLayout(container)
        layout.addWidget(QLabel("Filtros", objectName="sectionTitle"))
        
        grid_layout = QGridLayout()
        grid_layout.setSpacing(15)
        
        grid_layout.addWidget(QLabel("Empresa"), 0, 0)
        grid_layout.addWidget(QLabel("Pesquisar"), 0, 1)
        grid_layout.addWidget(QLabel("Ano"), 0, 2)
        grid_layout.addWidget(QLabel("Tensão (kV)"), 0, 3)
        grid_layout.addWidget(QLabel("Status"), 0, 4)
        
        self.company_combo = QComboBox()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Cód ONS, Ressalva...")
        self.year_combo = QComboBox()
        self.tension_combo = QComboBox()
        self.status_combo = QComboBox()
        
        grid_layout.addWidget(self.company_combo, 1, 0)
        grid_layout.addWidget(self.search_input, 1, 1)
        grid_layout.addWidget(self.year_combo, 1, 2)
        grid_layout.addWidget(self.tension_combo, 1, 3)
        grid_layout.addWidget(self.status_combo, 1, 4)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.clear_button = QPushButton("Limpar")
        self.clear_button.setObjectName("clearButton")
        self.clear_button.clicked.connect(self._clear_filters)
        
        self.filter_button = QPushButton("Filtrar")
        self.filter_button.setObjectName("filterButton")
        self.filter_button.clicked.connect(self._apply_filters)
        
        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.filter_button)
        
        layout.addLayout(grid_layout)
        layout.addLayout(button_layout)
        return container
    
    def _create_details_table_container(self):
        container = QFrame()
        container.setObjectName("container")
        layout = QVBoxLayout(container)
        layout.addWidget(QLabel("Detalhes dos Pontos de Conexão", objectName="sectionTitle"))
        
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Empresa", "Cód ONS", "Tensão (kV)", "Ressalva?", "Ação/Aprovado Por", "Arquivo PDF"
        ])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)
        
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.cellClicked.connect(self._on_cell_clicked)
        self.table.setFixedHeight((self.fontMetrics().height() + 12) * 16)
        
        layout.addWidget(self.table)
        return container
    
    def _load_initial_data(self):
        self._update_kpis()
        self._populate_company_analysis()
        self._populate_yearly_stats()
        self._populate_filters()
        self._apply_filters()
    
    def _update_kpis(self):
        kpi_data = self.db.get_kpi_summary()
        self.kpi_cards["unique_companies"].findChild(QLabel, "kpiValue").setText(
            str(kpi_data.get('unique_companies', 0)))
        self.kpi_cards["total_points"].findChild(QLabel, "kpiValue").setText(
            str(kpi_data.get('total_points', 0)))
        self.kpi_cards["points_with_remarks"].findChild(QLabel, "kpiValue").setText(
            str(kpi_data.get('points_with_remarks', 0)))
        self.kpi_cards["percentage_with_remarks"].findChild(QLabel, "kpiValue").setText(
            str(kpi_data.get('percentage_with_remarks', '0.0%')))
    
    def _populate_company_analysis(self):
        analysis_data = self.db.get_company_analysis()
        for i in reversed(range(self.company_analysis_layout.count())):
            self.company_analysis_layout.itemAt(i).widget().setParent(None)
        
        row, col, MAX_COLS = 0, 0, 3
        for stats in analysis_data:
            card = CompanyCard(stats['nome_empresa'], stats)
            self.company_analysis_layout.addWidget(card, row, col)
            col += 1
            if col >= MAX_COLS:
                col, row = 0, row + 1
    
    def _populate_yearly_stats(self):
        stats_data = self.db.get_yearly_must_stats()
        for i in reversed(range(self.yearly_stats_layout.count())):
            self.yearly_stats_layout.itemAt(i).widget().setParent(None)
        
        yearly_totals = {}
        for row in stats_data:
            if row['ano'] not in yearly_totals:
                yearly_totals[row['ano']] = {}
            yearly_totals[row['ano']][row['periodo']] = row.get('total_valor', 0)
        
        row, col, MAX_COLS = 0, 0, 4
        for year in sorted(yearly_totals.keys()):
            card = QFrame()
            card.setObjectName("kpiCard")
            layout = QVBoxLayout(card)
            
            year_label = QLabel(f"Ano: {year}")
            year_label.setStyleSheet("font-weight: bold; font-size: 16px;")
            
            ponta_val = yearly_totals[year].get('ponta', 0)
            fora_ponta_val = yearly_totals[year].get('fora_ponta', 0)
            
            ponta_label = QLabel(f"Ponta: {ponta_val:,.2f}")
            fora_ponta_label = QLabel(f"Fora Ponta: {fora_ponta_val:,.2f}")
            ponta_label.setObjectName("kpiTitle")
            fora_ponta_label.setObjectName("kpiTitle")
            
            layout.addWidget(year_label)
            layout.addWidget(ponta_label)
            layout.addWidget(fora_ponta_label)
            
            self.yearly_stats_layout.addWidget(card, row, col)
            col += 1
            if col >= MAX_COLS:
                col, row = 0, row + 1
    
    def _populate_filters(self):
        self.company_combo.addItems(["Todas"] + self.db.get_unique_companies())
        self.year_combo.addItems(["Todos", "2025", "2026", "2027", "2028"])
        self.tension_combo.addItems(["Todas"] + self.db.get_unique_tensions())
        self.status_combo.addItems(["Todos", "Com Ressalva", "Aprovado"])
    
    def _populate_table(self, data):
        self.table.setRowCount(0)
        self.table.setRowCount(len(data))
        
        for r, row in enumerate(data):
            annotation = row.get('anotacao_geral')
            has_remark = annotation and str(annotation).strip().lower() not in ('', 'nan')
            
            self.table.setItem(r, 0, QTableWidgetItem(row['nome_empresa']))
            self.table.setItem(r, 1, QTableWidgetItem(row['cod_ons']))
            self.table.setItem(r, 2, QTableWidgetItem(str(row.get('tensao_kv', 'N/D'))))
            
            if has_remark:
                remark_button = QPushButton("Sim")
                remark_button.setStyleSheet(
                    "background-color: #FBBF24; color: #78350F; font-weight: bold;")
                remark_button.clicked.connect(lambda checked=False, r=r: self._show_details_modal(r))
                self.table.setCellWidget(r, 3, remark_button)
            else:
                item = QTableWidgetItem("Não")
                item.setForeground(Qt.GlobalColor.green)
                self.table.setItem(r, 3, item)
            
            if row.get('aprovado_por'):
                self.table.setCellWidget(r, 4, 
                    QLabel(f"{row['aprovado_por']} em {row['data_aprovacao']}"))
            else:
                approve_button = QPushButton("Aprovar")
                approve_button.setStyleSheet("font-size: 12px; padding: 5px;")
                approve_button.clicked.connect(lambda checked=False, r=r: self._open_approval_dialog(r))
                self.table.setCellWidget(r, 4, approve_button)
            
            pdf_link = row.get('arquivo_referencia', '')
            pdf_item = QTableWidgetItem("Abrir Link" if pdf_link else "N/D")
            if pdf_link:
                pdf_item.setForeground(Qt.GlobalColor.cyan)
                pdf_item.setData(Qt.ItemDataRole.UserRole, pdf_link)
            self.table.setItem(r, 5, pdf_item)
        
        self.table.resizeRowsToContents()
    
    def _apply_filters(self):
        filters = {
            "company": self.company_combo.currentText(),
            "search": self.search_input.text(),
            "year": self.year_combo.currentText(),
            "tension": self.tension_combo.currentText(),
            "status": self.status_combo.currentText()
        }
        data = self.db.get_all_connection_points(filters)
        self._populate_table(data)
    
    def _clear_filters(self):
        self.company_combo.setCurrentIndex(0)
        self.search_input.clear()
        self.year_combo.setCurrentIndex(0)
        self.tension_combo.setCurrentIndex(0)
        self.status_combo.setCurrentIndex(0)
        self._apply_filters()
    
    def _on_cell_clicked(self, row, column):
        if column == 5:
            item = self.table.item(row, column)
            if item and item.data(Qt.ItemDataRole.UserRole):
                webbrowser.open(item.data(Qt.ItemDataRole.UserRole))
    
    def _open_approval_dialog(self, row):
        cod_ons = self.table.item(row, 1).text()
        dialog = ApprovalDialog(cod_ons, self)
        if dialog.exec():
            approver = dialog.approver_name
            if self.db.approve_point(cod_ons, approver):
                self._apply_filters()
    
    def _show_details_modal(self, row):
        cod_ons_item = self.table.item(row, 1)
        if not cod_ons_item:
            return
        
        cod_ons = cod_ons_item.text()
        annotation_data = self.db._execute_query(
            f"SELECT anotacao_geral FROM {self.db.tbl_anotacao} WHERE cod_ons = ?",
            (cod_ons,), fetch_one=True)
        annotation = annotation_data.get('anotacao_geral') if annotation_data else "Não encontrada."
        history_data = self.db.get_must_history_for_point(cod_ons)
        
        dialog = DetailsDialog(str(annotation), history_data, self)
        dialog.exec()

class GraphicsWidget(QWidget):
    def __init__(self, db_model, parent=None):
        super().__init__(parent)
        self.db = db_model
        self._setup_ui()
    
    def _setup_ui(self):
        if not px or not QWebEngineView:
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel("Plotly ou WebEngine não instalados."))
            return
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("Análise Gráfica Interativa")
        title.setObjectName("headerTitle")
        layout.addWidget(title)
        
        chart_data = self.db.get_data_for_charts()
        
        grid_layout = QGridLayout()
        grid_layout.setSpacing(10)
        
        self.points_chart = self._create_plotly_chart(
            chart_data.get('points_per_company'), self._plot_points_by_company)
        self.remarks_chart = self._create_plotly_chart(
            chart_data.get('remarks_summary'), self._plot_remarks_pie)
        self.yearly_chart = self._create_plotly_chart(
            chart_data.get('yearly_sum'), self._plot_yearly_sum)
        
        grid_layout.addWidget(self.points_chart, 0, 0)
        grid_layout.addWidget(self.remarks_chart, 0, 1)
        grid_layout.addWidget(self.yearly_chart, 1, 0, 1, 2)
        
        layout.addLayout(grid_layout)
    
    def _create_plotly_chart(self, data, plot_function):
        browser = QWebEngineView()
        if not data:
            return browser
        
        fig = plot_function(data)
        temp_file = tempfile.NamedTemporaryFile(suffix=".html", delete=False, 
                                                mode='w', encoding='utf-8')
        fig.write_html(temp_file.name, config={'displayModeBar': False})
        temp_file.close()
        browser.setUrl(QUrl.fromLocalFile(os.path.abspath(temp_file.name)))
        return browser
    
    def _get_plotly_layout(self, title):
        return go.Layout(
            title={'text': title, 'x': 0.5, 'font': {'color': 'white', 'size': 16}},
            paper_bgcolor='#1F2937',
            plot_bgcolor='#1F2937',
            font={'color': '#E0E0E0'},
            xaxis={'gridcolor': '#374151'},
            yaxis={'gridcolor': '#374151'},
            legend={'font': {'color': 'white'}}
        )
    
    def _plot_points_by_company(self, data):
        df = pd.DataFrame(data)
        fig = px.bar(df, y='nome_empresa', x='count', orientation='h',
                    labels={'count': 'Nº de Pontos', 'nome_empresa': 'Empresa'},
                    color_discrete_sequence=['#EA580C'])
        fig.update_layout(self._get_plotly_layout("Pontos por Empresa"))
        return fig
    
    def _plot_remarks_pie(self, data):
        if not data:
            return go.Figure()
        with_remarks = data.get('with_remarks', 0)
        approved = data.get('total', 0) - with_remarks
        labels = ['Sem Ressalva', 'Com Ressalva']
        values = [approved, with_remarks]
        fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.4,
                                     marker_colors=['#22C55E', '#F97316'])])
        fig.update_layout(self._get_plotly_layout("Proporção de Ressalvas"))
        return fig
    
    def _plot_yearly_sum(self, data):
        df = pd.DataFrame(data)
        fig = px.bar(df, x='ano', y='total_valor',
                    labels={'ano': 'Ano', 'total_valor': 'Soma MUST'},
                    color_discrete_sequence=['#3B82F6'])
        fig.update_layout(self._get_plotly_layout("Soma MUST por Ano"),
                         xaxis={'type': 'category'})
        return fig

class ReportsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        title = QLabel("Página de Relatórios")
        title.setObjectName("headerTitle")
        subtitle = QLabel("Esta área será usada para a geração de relatórios customizados.")
        subtitle.setObjectName("headerSubtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addStretch()

# ==============================================================================
# JANELA PRINCIPAL
# ==============================================================================

class MainWindow(QMainWindow):
    def __init__(self, db_model):
        super().__init__()
        self.db = db_model
        self.setWindowTitle("Dashboard MUST - Sistema Integrado")
        self.setMinimumSize(1400, 950)
        self.setStyleSheet(STYLESHEET)
        
        self._setup_ui()
        self.nav_buttons["dashboard"].setChecked(True)
    
    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        self.nav_panel = self._create_nav_panel()
        main_layout.addWidget(self.nav_panel)
        
        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget, 1)
        
        self.dashboard_widget = self._create_scrollable_widget(DashboardMainWidget(self.db))
        self.graphics_widget = self._create_scrollable_widget(GraphicsWidget(self.db))
        self.extraction_widget = self._create_scrollable_widget(PalkiaWindowGUI())
        self.reports_widget = self._create_scrollable_widget(ReportsWidget())
        
        self.stacked_widget.addWidget(self.dashboard_widget)
        self.stacked_widget.addWidget(self.graphics_widget)
        self.stacked_widget.addWidget(self.extraction_widget)
        self.stacked_widget.addWidget(self.reports_widget)
    
    def _create_nav_panel(self):
        nav_panel = QFrame()
        nav_panel.setObjectName("navPanel")
        nav_panel.setFixedWidth(220)
        nav_layout = QVBoxLayout(nav_panel)
        
        nav_title = QLabel("Menu")
        nav_title.setObjectName("headerTitle")
        nav_layout.addWidget(nav_title)
        
        self.nav_buttons = {
            "dashboard": QPushButton("Dashboard Principal"),
            "graphics": QPushButton("Análise Gráfica"),
            "extraction": QPushButton("Extração de PDF"),
            "reports": QPushButton("Relatórios")
        }
        
        for name, button in self.nav_buttons.items():
            button.setObjectName("navButton")
            button.setCheckable(True)
            button.setAutoExclusive(True)
            nav_layout.addWidget(button)
        
        self.nav_buttons["dashboard"].clicked.connect(lambda: self._switch_view(0))
        self.nav_buttons["graphics"].clicked.connect(lambda: self._switch_view(1))
        self.nav_buttons["extraction"].clicked.connect(lambda: self._switch_view(2))
        self.nav_buttons["reports"].clicked.connect(lambda: self._switch_view(3))
        
        nav_layout.addStretch()
        
        info_label = QLabel("Sistema MUST Desktop v3.4.3")
        info_label.setStyleSheet("color: #6B7280; font-size: 11px; padding: 10px;")
        nav_layout.addWidget(info_label)
        
        return nav_panel
    
    def _create_scrollable_widget(self, widget):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(widget)
        scroll_area.setStyleSheet("border: none;")
        return scroll_area
    
    def _switch_view(self, index):
        self.stacked_widget.setCurrentIndex(index)

# ==============================================================================
# PONTO DE ENTRADA
# ==============================================================================

def main():
    """Ponto de entrada da aplicação."""
    app = QApplication(sys.argv)
    
    # --- Definição de Caminhos Dinâmicos ---
    # Constrói o caminho para a pasta 'database' de forma relativa ao local do script
    try:
        script_dir = Path(__file__).resolve().parent
        db_folder = script_dir / "database"
        
        if not db_folder.exists():
            raise FileNotFoundError(f"Pasta do banco de dados não encontrada em: {db_folder}")
            
    except Exception as e:
        QMessageBox.critical(None, "Erro de Configuração", f"Não foi possível determinar o caminho do banco de dados.\n\n{e}")
        sys.exit(1)

    access_db_path = db_folder / "Database_MUST.accdb"
    sqlite_db_path = db_folder / "database_consolidado.db"
    
    db_to_use = None
    
    print("\nTentando conectar ao banco de dados...")
    
    if access_db_path.exists():
        try:
            conn = pyodbc.connect(
                r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
                fr"DBQ={access_db_path};"
            )
            conn.close()
            print(f"Usando Access: {access_db_path}")
            db_to_use = access_db_path
        except pyodbc.Error as e:
            print(f"Falha ao conectar Access: {e}")
            print("Tentando SQLite...")
    
    if not db_to_use:
        if sqlite_db_path.exists():
            print(f"Usando SQLite: {sqlite_db_path}")
            db_to_use = sqlite_db_path
        else:
            print(f"ERRO: Nenhum banco encontrado em: {db_folder}")
            QMessageBox.critical(None, "Erro Crítico", 
                f"Nenhum banco de dados encontrado.\n\nVerifique a pasta:\n{db_folder}")
            sys.exit(1)
    
    try:
        db_model = DashboardDB(db_to_use)
        
        window = MainWindow(db_model)
        window.show()
        
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"Erro ao iniciar aplicação: {e}")
        import traceback
        traceback.print_exc()
        
        QMessageBox.critical(None, "Erro Crítico",
            f"Erro fatal ao iniciar:\n\n{e}\n\nConsulte o terminal para detalhes.")
        sys.exit(1)

if __name__ == '__main__':
    main()

