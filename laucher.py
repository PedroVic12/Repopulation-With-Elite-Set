"""
Launcher Desktop App (PySide6)
--------------------------------
Este aplicativo desktop organiza a configuração e execução do framework RCE, e
exibe um dashboard/console. É construído com PySide6 (Qt para Python).

Como o PySide6 estrutura a UI neste app:
- QApplication: processo/loop de eventos da aplicação.
- QMainWindow (LauncherWindow): janela principal com barra de status e conteúdo central.
- QTabWidget: organiza abas para Configuração/Execução, Parâmetros AG e Dashboard/Logs.
- Widgets e layouts (QWidget, QGroupBox, QVBoxLayout, QGridLayout, etc.) compõem a tela.
- QScrollArea envolve o conteúdo principal para permitir rolagem quando a UI crescer.

Fluxo principal do app:
1) ConfigManager carrega/salva params.json e options.json e normaliza as opções variáveis.
2) ConfigTab permite ajustar parâmetros de AG e preparar execuções (gera combinações e chama ExecutionTab).
3) ParamsAGTab edita parâmetros base e arrays variáveis, e inclui um editor de código Python
   para a função de fitness (src/fitness_function_user.py).
4) ExecutionTab executa o script do framework em thread separada (QThread) e mostra logs e progresso.
5) LauncherWindow junta tudo em abas e aplica um tema via STYLESHEET.

Observação: este arquivo prioriza comentários explicativos para facilitar manutenção e onboarding.
"""
import sys
import os
import json
import subprocess
import threading
import time
from pathlib import Path
from functools import reduce
import operator
from itertools import product

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel,
    QHBoxLayout, QTextEdit, QProgressBar, QTabWidget, QGroupBox, QSpinBox,
    QLineEdit,  QMessageBox, QRadioButton,
    QButtonGroup, QGridLayout, QTableWidget, QTableWidgetItem, QPlainTextEdit,
    QScrollArea
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QIcon, QIntValidator, QDoubleValidator

# --- CONFIGURAÇÃO ---
# pasta raiz do projeto
BASE_DIR = Path(__file__).parent
SRC_DIR = BASE_DIR / "src"

# arquivos de configuração .json para AG
PARAMS_FILE = SRC_DIR / "params.json"
OPTIONS_FILE = SRC_DIR / "options.json"

# arquivos de execução do framework e dashboard
RUN_FRAMEWORK_SCRIPT = SRC_DIR /"run_framework_backup.py" 

#! Script refatorado da pasta lib
#RUN_FRAMEWORK_SCRIPT = BASE_DIR / "lib" / "rce_framework" / "main.py"
DASHBOARD_SCRIPT = SRC_DIR / "DashboardApp" / "dashboard_RCE_APP.py"

from style import STYLESHEET

# Parâmetros que podem variar via options.json (arrays)
VARYING_KEYS = {"MUTACAO", "CROSSOVER", "NUM_GENERATIONS", "POP_SIZE"}

class ConfigManager:
    """Gerencia leitura/escrita dos JSON de configuração e normalização de opções.

    Responsabilidades:
    - Carregar params.json e options.json ao iniciar.
    - Persistir alterações com json.dump (indent=4 para legibilidade).
    - clean_options(): manter somente chaves variáveis permitidas em options.json,
      deduplicar arrays e preservar 'repeticoes_por_config'.
    """
    def __init__(self):
        self.params = self.load_json(PARAMS_FILE)
        self.options = self.load_json(OPTIONS_FILE)
        # Normaliza options.json logo no início
        self.clean_options()

    def load_json(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar {file_path}: {e}")
            return {}

    def save_json(self, data, file_path):
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Erro ao salvar {file_path}: {e}")
            return False

    def clean_options(self):
        """Mantém apenas arrays para chaves em VARYING_KEYS + repeticoes_por_config; deduplica arrays."""
        try:
            current = self.options if isinstance(self.options, dict) else {}
            cleaned = {}
            if 'repeticoes_por_config' in current:
                cleaned['repeticoes_por_config'] = current['repeticoes_por_config']
            for k in VARYING_KEYS:
                v = current.get(k)
                if isinstance(v, list):
                    seen = set()
                    dedup = []
                    for x in v:
                        if x not in seen:
                            seen.add(x)
                            dedup.append(x)
                    cleaned[k] = dedup
            if cleaned != current:
                # persiste em disco e atualiza em memória
                if self.save_json(cleaned, OPTIONS_FILE):
                    self.options = cleaned
        except Exception as e:
            print(f"Erro ao normalizar options.json: {e}")

class ExecutionThread(QThread):
    """Executa o framework em subprocesso dentro de uma QThread.

    - Emite sinais de log (log_updated) conforme o stdout do processo é lido.
    - Emite execution_finished ao término, indicando sucesso/erro.
    - Permite interrupção graciosa via stop() (terminate do subprocesso).
    """
    log_updated = Signal(str)
    execution_finished = Signal(bool, str)

    def __init__(self, script_path, args=None):
        super().__init__()
        self.script_path = script_path
        self.args = args or []
        self.process = None

    def run(self):
        """Inicia o subprocesso do framework e encaminha logs para a UI."""
        try:
            cmd = [sys.executable, str(self.script_path)] + self.args
            self.log_updated.emit(f"Executando: {' '.join(cmd)}")
            self.process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                universal_newlines=True, cwd=SRC_DIR, encoding='utf-8'
            )
            for line in iter(self.process.stdout.readline, ''):
                if line:
                    self.log_updated.emit(line.strip())
            return_code = self.process.wait()
            success = return_code == 0
            self.execution_finished.emit(success, f"Código de retorno: {return_code}")
        except Exception as e:
            self.log_updated.emit(f"Erro na execução: {e}")
            self.execution_finished.emit(False, str(e))

    def stop(self):
        """Termina o subprocesso em execução e informa via log."""
        if self.process:
            self.process.terminate()
            self.log_updated.emit("Processo de execução terminado pelo usuário.")

class ConfigTab(QWidget):
    """Aba de Configuração e Execução rápida.

    Funções principais:
    - Ajustar execuções por configuração.
    - Configurar parâmetros AG base (MUTACAO, CROSSOVER, NUM_GENERATIONS, POP_SIZE).
    - Resumo de total de execuções.
    - Disparar a execução (gera combinações e sinaliza ExecutionTab).
    """
    execution_requested = Signal(list, int)

    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.param_widgets = {}
        self.init_ui()
        self.update_summary()

    def init_ui(self):
        """Monta a UI da aba com grupos de configurações e botão de execução."""
        self.setObjectName("ParamsAGTabRoot")
        self.setStyleSheet(
            """
            #ParamsAGTabRoot { background: #f0f2f5; }
            """
        )
        layout = QVBoxLayout(self)
        self.create_general_settings(layout)
        self.create_ag_params(layout)
        self.create_summary(layout)
        self.create_run_button(layout)
        layout.addStretch()

    def create_general_settings(self, layout):
        """Cria controles de configurações gerais (quantidade de execuções por config)."""
        general_group = QGroupBox("Configurações Gerais")
        general_layout = QVBoxLayout(general_group)
        self.runs_per_config_spin = QSpinBox()
        self.runs_per_config_spin.setRange(1, 100)
        self.runs_per_config_spin.setValue(self.config_manager.options.get('repeticoes_por_config', 1))
        self.runs_per_config_spin.valueChanged.connect(self.update_summary)
        general_layout.addWidget(QLabel("Execuções por Configuração:"))
        general_layout.addWidget(self.runs_per_config_spin)
        layout.addWidget(general_group)

    def create_ag_params(self, layout):
        """Cria widgets para parâmetros principais do AG em um grid responsivo."""
        ag_group = QGroupBox("Parâmetros do Algoritmo Genético")
        ag_layout = QGridLayout(ag_group)

        # espaçamento entre os widgets
        ag_layout.setHorizontalSpacing(16)
        ag_layout.setVerticalSpacing(16)

        # criação dos widgets dos parâmetros de configuração
        params_to_render = {
            "MUTAÇÃO (%)": self.config_manager.params.get("MUTACAO", 0.1),
            "CROSSOVER (%)": self.config_manager.params.get("CROSSOVER", 0.8),
            "NÚMERO DE GERAÇÕES (INT)": self.config_manager.params.get("NUM_GENERATIONS", 100),
            "TAMANHO DA POPULAÇÃO (INT)": self.config_manager.params.get("POP_SIZE", 50),
        }
        row, col = 0, 0
        for name, default_val in params_to_render.items():
            param_widget = self._create_param_widget(name, default_val)
            ag_layout.addWidget(param_widget, row, col)
            col += 1
            if col > 1:
                col, row = 0, row + 1
        layout.addWidget(ag_group)

    def create_summary(self, layout):
        """Mostra um resumo dinâmico: configs únicas e total de execuções."""
        summary_group = QGroupBox("Resumo da Execução")
        summary_layout = QHBoxLayout(summary_group)
        self.unique_configs_label = QLabel("Configurações Únicas: 1")
        self.total_runs_label = QLabel(f"Total de Execuções: {self.runs_per_config_spin.value()}")
        summary_layout.addWidget(self.unique_configs_label)
        summary_layout.addWidget(self.total_runs_label)
        layout.addWidget(summary_group)

    def create_run_button(self, layout):
        """Botão para salvar e executar o framework com os parâmetros atuais."""
        self.run_button = QPushButton("💾 Salvar e Executar")
        self.run_button.setObjectName("run_button")
        self.run_button.clicked.connect(self.prepare_and_run)
        layout.addWidget(self.run_button, alignment=Qt.AlignCenter)

    def _create_param_widget(self, name, default_value):
        widget_group = QGroupBox(name)
        layout = QVBoxLayout(widget_group)
        mode_group = QButtonGroup(self)
        fixed_radio = QRadioButton("Fixo")
        variable_radio = QRadioButton("Variável")
        fixed_radio.setChecked(True)
        mode_group.addButton(fixed_radio)
        mode_group.addButton(variable_radio)
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(fixed_radio)
        mode_layout.addWidget(variable_radio)
        layout.addLayout(mode_layout)

        # criação do widget fixo
        is_int = isinstance(default_value, int)
        fixed_input = QLineEdit()
        if is_int:
            fixed_input.setValidator(QIntValidator(1, 100000))
        else:
            fixed_input.setValidator(QDoubleValidator(0.0, 1.0, 5))
        fixed_input.setText(str(default_value))

        # aumentar tamanho das caixas
        fixed_font = fixed_input.font()
        fixed_font.setPointSize(max(fixed_font.pointSize(), 11))
        fixed_input.setFont(fixed_font)
        fixed_input.setMinimumWidth(140)
        fixed_input.setFixedHeight(34)

        # criação do widget variável
        variable_inputs_widget = QWidget()
        
        # layout 2x2 para as 4 entradas de variação
        from PySide6.QtWidgets import QGridLayout as _QGridLayout
        variable_layout = _QGridLayout(variable_inputs_widget)
        variable_layout.setContentsMargins(0, 0, 0, 0)
        variable_layout.setHorizontalSpacing(8)
        variable_layout.setVerticalSpacing(6)
        
        # criação das entradas de variação
        variable_inputs = []
        for i in range(4):
            input_field = QLineEdit()
            input_field.setPlaceholderText(f"V{i+1}")
            input_field.setText(str(default_value))  # Preenche com o valor padrão
            if is_int:
                input_field.setValidator(QIntValidator(1, 100000))
            else:
                input_field.setValidator(QDoubleValidator(0.0, 1.0, 5))
            
             # aumentar tamanho das caixas
            f = input_field.font()
            f.setPointSize(max(f.pointSize(), 11))
            input_field.setFont(f)
            input_field.setMinimumWidth(120)
            input_field.setFixedHeight(36)
            
            # posicionar em 2x2
            r = i // 2
            c = i % 2
            variable_layout.addWidget(input_field, r, c)
            variable_inputs.append(input_field)
        variable_inputs_widget.setVisible(False)

        layout.addWidget(fixed_input)
        layout.addWidget(variable_inputs_widget)

        fixed_radio.toggled.connect(fixed_input.setVisible)
        variable_radio.toggled.connect(variable_inputs_widget.setVisible)

        self.param_widgets[name] = {
            "mode": mode_group, "fixed": fixed_input,
            "variable": variable_inputs, "is_int": is_int
        }

        fixed_input.textChanged.connect(self.update_summary)
        for var_input in variable_inputs:
            var_input.textChanged.connect(self.update_summary)
        mode_group.buttonClicked.connect(self.update_summary)

        return widget_group

    def update_summary(self, _=None):
        # Garante options.json limpo e, então, lê arrays variáveis (exclui repeticoes_por_config)
        self.config_manager.options = self.config_manager.load_json(OPTIONS_FILE) or {}
        self.config_manager.clean_options()
        options = self.config_manager.options
        arrays = [v for k, v in options.items() if k in VARYING_KEYS and isinstance(v, list) and len(v) > 0]
        total_combinations = reduce(operator.mul, [len(v) for v in arrays], 1) if arrays else 1
        total_execucoes = total_combinations * self.runs_per_config_spin.value()

        self.unique_configs_label.setText(f"Configurações Únicas: {total_combinations}")
        self.total_runs_label.setText(f"Total de Execuções: {total_execucoes}")

    def prepare_and_run(self):
        try:
            # Lê base (params) e opções (arrays + repeticoes)
            base_params = self.config_manager.load_json(PARAMS_FILE) or {}
            options = self.config_manager.load_json(OPTIONS_FILE) or {}
            runs_per_config = self.runs_per_config_spin.value()

            # garante que repeticoes_por_config esteja salvo em options.json
            options['repeticoes_por_config'] = runs_per_config
            # filtra para apenas chaves permitidas e deduplica
            filtered = {'repeticoes_por_config': options['repeticoes_por_config']}
            for k in VARYING_KEYS:
                v = options.get(k)
                if isinstance(v, list):
                    seen = set()
                    dedup = []
                    for x in v:
                        if x not in seen:
                            seen.add(x)
                            dedup.append(x)
                    filtered[k] = dedup
            if not self.config_manager.save_json(filtered, OPTIONS_FILE):
                QMessageBox.critical(self, "Erro", f"Falha ao salvar {OPTIONS_FILE.name}")
                return

            varying = {k: v for k, v in filtered.items() if k != 'repeticoes_por_config' and isinstance(v, list) and len(v) > 0}
            keys = list(varying.keys())
            values_lists = list(varying.values())
            combinations = [dict(zip(keys, v)) for v in product(*values_lists)] if keys else [{}]

            configurations = []
            skeleton = {}
            for idx, combo in enumerate(combinations, start=1):
                cfg = dict(base_params)
                cfg.update(combo)
                cfg['repeticoes_por_config'] = runs_per_config
                cfg['key'] = True
                configurations.append(combo)
                skeleton[f"config {idx}"] = cfg

            # salva esqueleto em docs/config.json
            try:
                docs_dir = BASE_DIR / 'docs'
                docs_dir.mkdir(exist_ok=True)
                with open(docs_dir / 'config.json', 'w', encoding='utf-8') as f:
                    json.dump(skeleton, f, indent=4, ensure_ascii=False)
            except Exception as e:
                QMessageBox.warning(self, "Aviso", f"Não foi possível salvar docs/config.json: {e}")

            msg = f"{len(combinations)} configs únicas serão executadas {runs_per_config} vez(es) cada."
            QMessageBox.information(self, "Pronto para Iniciar", msg)
            self.execution_requested.emit([dict(base_params, **c) for c in configurations], runs_per_config)

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao preparar execução: {e}")

class JsonEditor(QWidget):
    def __init__(self, title, file_path, config_manager: 'ConfigManager'):
        super().__init__()
        self.title = title
        self.file_path = file_path
        self.config_manager = config_manager
        self.fields = {}  # key -> {widget, type, is_list, elem_type}
        self.init_ui()

    def init_ui(self):
        """Constroi a tabela, cartões e editor de código com layout e estilos."""
        layout = QVBoxLayout(self)
        group = QGroupBox(self.title)
        v = QVBoxLayout(group)

        self.info_label = QLabel(str(self.file_path))
        self.info_label.setStyleSheet("color: #666;")
        v.addWidget(self.info_label)

        self.fields_widget = QWidget()
        self.fields_layout = QGridLayout(self.fields_widget)
        self.fields_layout.setColumnStretch(1, 1)
        v.addWidget(self.fields_widget)

        buttons_layout = QHBoxLayout()
        self.reload_btn = QPushButton("🔄 Recarregar")
        self.save_btn = QPushButton("💾 Salvar")
        self.reload_btn.clicked.connect(self.reload)
        self.save_btn.clicked.connect(self.save)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.reload_btn)
        buttons_layout.addWidget(self.save_btn)
        v.addLayout(buttons_layout)

        layout.addWidget(group)
        self.reload()

    def detect_elem_type(self, lst):
        if not lst:
            return float
        types = {type(x) for x in lst}
        if int in types and float in types:
            return float
        if int in types and len(types) == 1:
            return int
        if float in types and len(types) == 1:
            return float
        return str

    def build_fields(self, data: dict):
        # clear previous
        while self.fields_layout.count():
            item = self.fields_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self.fields.clear()

        row = 0
        for key, value in data.items():
            label = QLabel(str(key))
            label.setMinimumWidth(180)
            self.fields_layout.addWidget(label, row, 0)

            if isinstance(value, list):
                editor = QLineEdit(", ".join(str(x) for x in value))
                elem_type = self.detect_elem_type(value)
                # Não usar validators aqui, pois a entrada é separada por vírgulas
                self.fields_layout.addWidget(editor, row, 1)
                self.fields[key] = {
                    "widget": editor, "is_list": True, "elem_type": elem_type, "orig_type": list
                }
            elif isinstance(value, int):
                editor = QLineEdit(str(value))
                editor.setValidator(QIntValidator())
                self.fields_layout.addWidget(editor, row, 1)
                self.fields[key] = {"widget": editor, "is_list": False, "orig_type": int}
            elif isinstance(value, float):
                editor = QLineEdit(str(value))
                editor.setValidator(QDoubleValidator())
                self.fields_layout.addWidget(editor, row, 1)
                self.fields[key] = {"widget": editor, "is_list": False, "orig_type": float}
            else:
                editor = QLineEdit(str(value))
                self.fields_layout.addWidget(editor, row, 1)
                self.fields[key] = {"widget": editor, "is_list": False, "orig_type": str}

            row += 1

    def reload(self):
        data = self.config_manager.load_json(self.file_path)
        if not isinstance(data, dict):
            QMessageBox.critical(self, "Erro", f"Arquivo inválido: {self.file_path}")
            data = {}
        self.build_fields(data)

    def parse_list(self, text, elem_type):
        items = [t.strip() for t in text.split(',') if t.strip() != ""]
        parsed = []
        for it in items:
            try:
                if elem_type is int:
                    parsed.append(int(it))
                elif elem_type is float:
                    parsed.append(float(it))
                else:
                    parsed.append(it)
            except ValueError:
                raise ValueError(f"Valor de lista inválido: '{it}'")
        return parsed

    def save(self):
        """Lê os valores da tabela e salva nos JSON correspondentes."""
        try:
            current = self.config_manager.load_json(self.file_path)
            if not isinstance(current, dict):
                current = {}
            for key, meta in self.fields.items():
                w: QLineEdit = meta["widget"]
                txt = w.text().strip()
                if meta["is_list"]:
                    lst = self.parse_list(txt, meta.get("elem_type", str))
                    current[key] = lst
                else:
                    orig = meta.get("orig_type", str)
                    if orig is int:
                        current[key] = int(txt) if txt else 0
                    elif orig is float:
                        current[key] = float(txt) if txt else 0.0
                    else:
                        current[key] = txt
            if not self.config_manager.save_json(current, self.file_path):
                QMessageBox.critical(self, "Erro", f"Falha ao salvar {self.file_path.name}")
                return
            QMessageBox.information(self, "Sucesso", f"Arquivo salvo: {self.file_path.name}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar: {e}")

class ParamsAGTab(QWidget):
    """Aba para editar todos os parâmetros em tabela e o código da função de fitness.

    Recursos:
    - Tabela única de parâmetros base (params.json) com estilos de destaque.
    - Salvamento inteligente que separa base (params.json) e variações (options.json).
    - Editor de código Python (QPlainTextEdit) com tema escuro para editar
      src/fitness_function_user.py (carregar/salvar com botões dedicados).
    """
    def __init__(self, config_manager: 'ConfigManager'):
        super().__init__()
        self.config_manager = config_manager
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        header = QLabel("Tabela única para edição de parâmetros base (params.json) e variações (options.json).\nAs variações são salvas em options.json e o valor base em params.json.")
        header.setWordWrap(True)
        layout.addWidget(header)
        
        self.table = QTableWidget()
        # Visual moderno e centrado
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Parâmetro AG", "Valor"])
        from PySide6.QtWidgets import QAbstractItemView, QFrame, QGraphicsDropShadowEffect, QSizePolicy
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QHeaderView

        # Aparência limpa: sem borda da tabela e sem grid
        self.table.setFrameShape(QFrame.Shape.NoFrame)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setHighlightSections(False)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.verticalHeader().setDefaultSectionSize(48)
        table_font = self.table.font()
        table_font.setPointSize(max(table_font.pointSize(), 12))
        self.table.setFont(table_font)
        self.table.setMinimumHeight(520)
        self.table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        header_font = self.table.horizontalHeader().font()
        header_font.setPointSize(max(header_font.pointSize(), 12))
        self.table.horizontalHeader().setFont(header_font)
        self.table.setStyleSheet("""
        QTableWidget {
            background-color: #7a7a7a;
            alternate-background-color: #2d2d2e;
            gridline-color: #c9d1dc;
            font-size: 12pt;
            selection-background-color: #adb9cc;
            selection-color: #111;
        }

        QHeaderView::section {
            background-color: #0e22b5;
            color: #ffffff;
            padding: 4px 8px;
            border: none;
            font-size: 12pt;
        }

        QTableWidget::item {
            padding: 4px 8px;
            border: none;
        }

        /* Editar célula (QLineEdit interno) */
        QTableWidget QLineEdit {
            background-color: #f9f9f9;  /* Fundo visível */
            color: #111;                /* Texto escuro para contraste */
            border: none;
            border-bottom: 2px solid #c9d1dc;
            padding: 4px 8px;
            font-size: 12pt;
        }

        QTableWidget QLineEdit:focus {
            border-bottom: 2px solid #4a90e2;
            background-color: #6087e0;
            color: #111;
        }

        QTableWidget QLineEdit:hover {
            background-color: #6087e0;
        }
        """)

        # Card wrapper centralizado com sombra
        card = QFrame(self)
        card.setObjectName("paramsCard")
        card.setStyleSheet(
            """
            #paramsCard { background: #ffffff; border: 1px solid #e6e6e6; border-radius: 12px; }
            """
        )
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.addWidget(self.table)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(22)
        shadow.setOffset(0, 6)
        from PySide6.QtGui import QColor
        shadow.setColor(QColor(0, 0, 0, 60))
        card.setGraphicsEffect(shadow)

        # Container para centralizar horizontalmente e limitar largura
        # Centralização horizontal
        container = QHBoxLayout()
        container.setContentsMargins(0, 0, 0, 0)
        container.addStretch(1)
        card.setMinimumWidth(900)
        card.setMaximumWidth(1200)
        container.addWidget(card)
        container.addStretch(1)

        # Centralização vertical com stretches
        layout.addStretch(1)
        layout.addLayout(container)
        layout.addStretch(1)

        # ==========================
        # Editor de Código (Python)
        # ==========================
        code_title = QLabel("Função de Fitness (Python)")
        code_title.setStyleSheet("font-weight: 600; font-size: 14pt;")
        layout.addWidget(code_title)

        code_card = QFrame(self)
        code_card.setObjectName("codeCard")
        code_card.setStyleSheet(
            """
            #codeCard { background: #ffffff; border: 1px solid #e6e6e6; border-radius: 12px; }
            """
        )
        code_layout = QVBoxLayout(code_card)
        code_layout.setContentsMargins(16, 16, 16, 16)

        self.code_editor = QPlainTextEdit()
        # Aparência do editor
        editor_font = QFont("Courier New")
        editor_font.setStyleHint(QFont.Monospace)
        editor_font.setPointSize(11)
        self.code_editor.setFont(editor_font)
        self.code_editor.setTabStopDistance(4 * self.code_editor.fontMetrics().horizontalAdvance(' '))
        self.code_editor.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.code_editor.setMinimumHeight(340)
        # Tema escuro para melhor contraste
        self.code_editor.setStyleSheet(
            """
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #eaeaea;
                border: 1px solid #3a3a3a;
                selection-background-color: #264f78;
                selection-color: #ffffff;
            }
            """
        )

        code_layout.addWidget(self.code_editor)

        code_shadow = QGraphicsDropShadowEffect(self)
        code_shadow.setBlurRadius(22)
        code_shadow.setOffset(0, 6)
        from PySide6.QtGui import QColor
        code_shadow.setColor(QColor(0, 0, 0, 60))
        code_card.setGraphicsEffect(code_shadow)

        # Centralizar code_card
        code_container = QHBoxLayout()
        code_container.setContentsMargins(0, 0, 0, 0)
        code_container.addStretch(1)
        code_card.setMinimumWidth(800)
        code_card.setMaximumWidth(1200)
        code_container.addWidget(code_card)
        code_container.addStretch(1)
        layout.addLayout(code_container)

        # Ações do editor de código
        code_actions = QHBoxLayout()
        self.code_reload_btn = QPushButton("🔄 Recarregar Código")
        self.code_save_btn = QPushButton("💾 Salvar Código")
        self.code_reload_btn.clicked.connect(self.reload_code)
        self.code_save_btn.clicked.connect(self.save_code)
        code_actions.addStretch()
        code_actions.addWidget(self.code_reload_btn)
        code_actions.addWidget(self.code_save_btn)
        layout.addLayout(code_actions)

        actions = QHBoxLayout()
        self.reload_btn = QPushButton("🔄 Recarregar")
        self.save_btn = QPushButton("💾 Salvar")
        self.reload_btn.clicked.connect(self.reload)
        self.save_btn.clicked.connect(self.save)
        actions.addStretch()
        actions.addWidget(self.reload_btn)
        actions.addWidget(self.save_btn)
        layout.addLayout(actions)

        self.reload()
        self.reload_code()

    def reload(self):
        """Recarrega params.json e options.json e repopula a tabela."""
        self.params = self.config_manager.load_json(PARAMS_FILE) or {}
        self.options = self.config_manager.load_json(OPTIONS_FILE) or {}
        self.types = {k: type(v) for k, v in self.params.items()}
        # somente arrays de variação válidos (somente chaves permitidas) e excluir repeticoes_por_config
        arrays = {k: v for k, v in self.options.items() if k in VARYING_KEYS and isinstance(v, list)}

        # remover duplicados preservando ordem
        def unique(seq):
            seen = set()
            out = []
            for x in seq:
                if x not in seen:
                    seen.add(x)
                    out.append(x)
            return out
        arrays = {k: unique(v) for k, v in arrays.items()}

        # Persistir options.json já limpo (apenas chaves permitidas e sem duplicatas)
        cleaned_options = {}
        if 'repeticoes_por_config' in self.options:
            cleaned_options['repeticoes_por_config'] = self.options['repeticoes_por_config']
        cleaned_options.update(arrays)
        # salva apenas se mudou algo
        if cleaned_options != {k: v for k, v in self.options.items() if (k in arrays or k == 'repeticoes_por_config')}:
            self.config_manager.save_json(cleaned_options, OPTIONS_FILE)

        # Mostrar apenas parâmetros que NÃO estão variando
        keys = [k for k in self.params.keys() if k not in arrays]

        self.table.setRowCount(len(keys))
        for r, key in enumerate(keys):
            # coluna 0: nome
            name_item = QTableWidgetItem(key)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(r, 0, name_item)

            # coluna 1: valor base
            base_val = self.params.get(key, "")
            self.table.setItem(r, 1, QTableWidgetItem(str(base_val)))

    def _cast_value(self, key, text):
        t = self.types.get(key, str)
        if t is int:
            return int(text) if text != '' else 0
        if t is float:
            return float(text) if text != '' else 0.0
        if t is bool:
            low = text.strip().lower()
            return low in ('1','true','yes','sim')
        return text

    def _parse_list(self, text, elem_type):
        if text.strip() == "":
            return []
        parts = [p.strip() for p in text.split(',') if p.strip() != '']
        out = []
        for p in parts:
            if elem_type is int:
                out.append(int(p))
            elif elem_type is float:
                out.append(float(p))
            elif elem_type is bool:
                out.append(p.lower() in ('1','true','yes','sim'))
            else:
                out.append(p)
        return out

    def save(self):
        try:
            # reconstruir params e arrays
            new_params = {}
            new_arrays = {}
            rows = self.table.rowCount()
            for r in range(rows):
                key = self.table.item(r, 0).text()
                base_text = self.table.item(r, 1).text() if self.table.item(r,1) else ''

                # tipo do valor base: usar tipo conhecido de params.json, senão inferir float->int->str
                try:
                    if key in self.types:
                        new_params[key] = self._cast_value(key, base_text)
                    else:
                        # inferência simples
                        if base_text.strip() == "":
                            new_params[key] = ""
                        else:
                            try:
                                new_params[key] = int(base_text)
                            except ValueError:
                                try:
                                    new_params[key] = float(base_text)
                                except ValueError:
                                    new_params[key] = base_text
                except Exception as e:
                    QMessageBox.warning(self, "Valor inválido", f"Parâmetro '{key}': {e}")
                    return

                # listas: somente para chaves permitidas variáveis
                if key in VARYING_KEYS:
                    elem_type = type(self.params.get(key, 0.0)) if key in self.params else float
                    try:
                        parsed_list = self._parse_list(list_text, elem_type)
                    except Exception as e:
                        QMessageBox.warning(self, "Lista inválida", f"Parâmetro '{key}' lista: {e}")
                        return
                    if parsed_list:
                        # remover duplicados preservando ordem
                        seen = set()
                        dedup = []
                        for x in parsed_list:
                            if x not in seen:
                                seen.add(x)
                                dedup.append(x)
                        new_arrays[key] = dedup

            # salvar params.json
            if not self.config_manager.save_json(new_params, PARAMS_FILE):
                QMessageBox.critical(self, "Erro", f"Falha ao salvar {PARAMS_FILE.name}")
                return

            # salvar options.json: somente arrays PERMITIDOS + manter repeticoes_por_config se existir
            out_options = {}
            if 'repeticoes_por_config' in self.options:
                out_options['repeticoes_por_config'] = self.options['repeticoes_por_config']
            # Apenas chaves em VARYING_KEYS
            out_options.update({k: v for k, v in new_arrays.items() if k in VARYING_KEYS})
            if not self.config_manager.save_json(out_options, OPTIONS_FILE):
                QMessageBox.critical(self, "Erro", f"Falha ao salvar {OPTIONS_FILE.name}")
                return

            QMessageBox.information(self, "Sucesso", "Parâmetros salvos com sucesso.")
            # atualiza cópias do config_manager
            self.config_manager.params = new_params
            self.config_manager.options = out_options
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar parâmetros: {e}")

    # ------------------------------
    # Editor de Código: load/save
    # ------------------------------
    def _fitness_file_path(self) -> Path:
        return SRC_DIR / "fitness_function_user.py"

    def reload_code(self):
        """Carrega (ou inicializa com template) o arquivo de função de fitness."""
        try:
            path = self._fitness_file_path()
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    self.code_editor.setPlainText(f.read())
            else:
                # Template inicial
                template = (
                    "\"\"\"\n"
                    "Arquivo de função de fitness do usuário.\n"
                    "Implemente a função evaluate(individual, data) -> float\n"
                    "\"\"\"\n\n"
                    "def evaluate(individual, data=None):\n"
                    "    \"\"\"\n"
                    "    individual: sequência de variáveis de decisão\n"
                    "    data: dados auxiliares (opcional)\n"
                    "    retorne um float com o fitness (quanto menor/melhor ou maior/melhor, conforme seu problema).\n"
                    "    \"\"\"\n"
                    "    # TODO: implemente sua lógica aqui\n"
                    "    return 0.0\n"
                )
                self.code_editor.setPlainText(template)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar código: {e}")

    def save_code(self):
        """Salva o conteúdo do editor no arquivo de função de fitness do usuário."""
        try:
            path = self._fitness_file_path()
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(self.code_editor.toPlainText())
            QMessageBox.information(self, "Sucesso", f"Código salvo em: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar código: {e}")

class ExecutionTab(QWidget):
    """Aba de execução e logs do framework.

    - Exibe barra de progresso, logs em tempo real e estado da execução.
    - Recebe lotes de configurações e executa sequencialmente via ExecutionThread.
    - Permite interromper a bateria de testes.
    """
    def __init__(self, config_manager):
        super().__init__()
        self.config_manager = config_manager
        self.execution_thread = None
        self.configurations = []
        self.runs_per_config = 0
        self.current_run_number = 0
        self.total_runs = 0
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.create_control_buttons(layout)
        self.create_status_panel(layout)
        self.create_progress_bar(layout)
        self.create_log_area(layout)

    def create_control_buttons(self, layout):
        control_layout = QHBoxLayout()
        self.run_dashboard_btn = QPushButton("📊 Abrir Dashboard")
        self.run_dashboard_btn.clicked.connect(self.run_dashboard)
        control_layout.addWidget(self.run_dashboard_btn)
        self.stop_btn = QPushButton("⏹️ Parar Execução")
        self.stop_btn.clicked.connect(self.stop_execution)
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.stop_btn)
        layout.addLayout(control_layout)

    def create_status_panel(self, layout):
        self.current_config_group = QGroupBox("Configuração da Execução Atual")
        current_config_layout = QVBoxLayout(self.current_config_group)
        self.current_config_label = QLabel("Aguardando início...")
        self.current_config_label.setAlignment(Qt.AlignCenter)
        current_config_layout.addWidget(self.current_config_label)
        layout.addWidget(self.current_config_group)

    def create_progress_bar(self, layout):
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

    def create_log_area(self, layout):
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(QLabel("Log de Execução:"))
        layout.addWidget(self.log_text)

    def start_executions(self, configs, runs_per_config):
        """Prepara e inicia a bateria de execuções, atualizando a UI."""
        try:
            # Verifica existência do script do framework
            if not RUN_FRAMEWORK_SCRIPT.exists():
                QMessageBox.critical(self, "Erro", f"Script não encontrado: {RUN_FRAMEWORK_SCRIPT}")
                return

            # Inicializa estado de execução
            self.configurations = configs
            self.runs_per_config = runs_per_config
            self.total_runs = len(self.configurations) * self.runs_per_config
            self.current_run_number = 0

            # Limpa e informa log inicial
            self.log_text.clear()
            self.append_log(
                f"Iniciando bateria de testes com {len(self.configurations)} configs e {self.runs_per_config} repetições."
            )
            self.append_log(f"Total de execuções: {self.total_runs}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao preparar execuções: {e}")
            return

        self.stop_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, self.total_runs)
        self.progress_bar.setValue(0)
        
        self.run_next_configuration()

    def run_next_configuration(self):
        if self.current_run_number >= self.total_runs:
            self.on_all_executions_finished(True, "Todas as execuções foram concluídas.")
            return

        config_index = self.current_run_number // self.runs_per_config
        repetition = (self.current_run_number % self.runs_per_config) + 1
        current_config = self.configurations[config_index]
        
        config_str = ", ".join([f"{k}: {v}" for k, v in current_config.items()])
        self.current_config_label.setText(f"Execução {self.current_run_number + 1}/{self.total_runs} (Rep. {repetition}) | {config_str}")
        self.append_log("-" * 20)
        self.append_log(f"Iniciando Config {config_index + 1}, Execução {repetition}: {config_str}")

        base_params = self.config_manager.load_json(PARAMS_FILE)
        base_params.update(current_config)
        
        # Salva uma cópia do params.json para cada configuração
        config_params_path = SRC_DIR / f"output/params_config{config_index + 1}.json"
        if not self.config_manager.save_json(base_params, config_params_path):
             self.append_log(f"❌ Erro ao salvar o arquivo de parâmetros de configuração {config_params_path}")
             # Decide se quer parar ou continuar

        if not self.config_manager.save_json(base_params, PARAMS_FILE):
             self.append_log(f"❌ Erro ao salvar o arquivo de parâmetros {PARAMS_FILE}")
             self.on_all_executions_finished(False, "Erro de arquivo.")
             return

        args = ["--config_num", str(config_index + 1), "--exec_num", str(repetition)]
        self.execution_thread = ExecutionThread(RUN_FRAMEWORK_SCRIPT, args)
        self.execution_thread.log_updated.connect(self.append_log)
        self.execution_thread.execution_finished.connect(self.on_single_execution_finished)
        self.execution_thread.start()

    def on_single_execution_finished(self, success, message):
        self.append_log(f"Finalizada execução {self.current_run_number + 1}. Sucesso: {success}. {message}")
        if not success:
            self.append_log(f"❌ Erro na execução, pulando para a próxima.")
        
        self.current_run_number += 1
        self.progress_bar.setValue(self.current_run_number)
        
        QTimer.singleShot(100, self.run_next_configuration)

    def run_dashboard(self):
        if not DASHBOARD_SCRIPT.exists():
            QMessageBox.critical(self, "Erro", f"Dashboard não encontrado: {DASHBOARD_SCRIPT}")
            return
        try:
            subprocess.Popen(["streamlit", "run", str(DASHBOARD_SCRIPT), "--server.port", "8501"], cwd=BASE_DIR)
            self.append_log("Dashboard iniciado em http://localhost:8501")
        except Exception as e:
            self.append_log(f"Erro ao iniciar dashboard: {e}")

    def stop_execution(self):
        self.current_run_number = self.total_runs # Prevent next run
        if self.execution_thread and self.execution_thread.isRunning():
            self.execution_thread.stop()
        self.on_all_executions_finished(False, "Interrompido pelo usuário.")

    def append_log(self, message):
        self.log_text.append(f"[{time.strftime('%H:%M:%S')}] {message}")
        self.log_text.ensureCursorVisible()

    def on_all_executions_finished(self, success, message):
        """Feedback final após concluir/interromper a bateria de execuções."""
        self.stop_btn.setEnabled(False)
        self.progress_bar.setValue(self.progress_bar.maximum())
        self.current_config_label.setText(f"Finalizado. {message}")
        if success:
            self.append_log(f"✅ {message}")
            QMessageBox.information(self, "Sucesso", "Bateria de testes concluída com sucesso!")
        else:
            self.append_log(f"❌ {message}")
            if "Interrompido" not in message:
                QMessageBox.critical(self, "Erro", f"A bateria de testes terminou com erro: {message}")

class LauncherWindow(QMainWindow):
    """Janela principal da aplicação com abas e rolagem.

    - Envolve o conteúdo em QScrollArea para suportar telas menores.
    - Cria as abas: Configuração/Execução, Parâmetros AG e Dashboard/Logs.
    - Aplica estilos via STYLESHEET e mostra status bar.
    """
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.init_ui()

    def init_ui(self):
        """Configura janela, scroll e chama construtores de header e tabs."""
        self.setWindowTitle("RCE Framework Launcher - Otimizado")
        #self.setMinimumSize(1200, 700)
        
        # Usa QScrollArea para permitir scroll vertical em telas menores
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        main_layout = QVBoxLayout(content)
        scroll.setWidget(content)
        self.setCentralWidget(scroll)
        
        self.create_header(main_layout)
        self.create_tabs(main_layout)
        
        self.statusBar().showMessage("Pronto.")

    def create_header(self, layout):
        """Cria títulos principais do app (nome e subtítulo)."""
        title = QLabel("Repopulation-With-Elite-Set Framework")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        subtitle = QLabel("Configuração e Execução em Tempo Real usando PySide6")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

    def create_tabs(self, layout):
        """Instancia as abas e conecta sinais entre ConfigTab e ExecutionTab."""
        tab_widget = QTabWidget()

        # Componentes
        self.config_tab = ConfigTab(self.config_manager)
        self.execution_tab = ExecutionTab(self.config_manager)
        self.params_ag_tab = ParamsAGTab(self.config_manager)
        
        # Configurações e Execução em TABS
        tab_widget.addTab(self.config_tab, "⚙️ Configuração e Execução")
        tab_widget.addTab(self.params_ag_tab, "Parametros AG")
        tab_widget.addTab(self.execution_tab, "📊 Dashboard e Logs")
        
        layout.addWidget(tab_widget)

        # Connect signals
        self.config_tab.execution_requested.connect(self.execution_tab.start_executions)
        self.config_tab.execution_requested.connect(lambda: tab_widget.setCurrentWidget(self.execution_tab))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Aplica estilos globais em arquivo separado
    app.setStyleSheet(STYLESHEET)
    
    # Cria a janela principal
    window = LauncherWindow()

    # Abre sempre maximizado
    window.showMaximized()
    
    # Executa a aplicação
    sys.exit(app.exec())
