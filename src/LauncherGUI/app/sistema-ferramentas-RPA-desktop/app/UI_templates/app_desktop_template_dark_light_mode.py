# -*- coding: utf-8 -*-

"""
Arquivo Principal da Aplicação de Configurações

Este script demonstra a criação de uma interface gráfica com PySide6,
seguindo os padrões de arquitetura MVC (Model-View-Controller) e os
princípios SOLID, tudo contido em um único arquivo.

A aplicação inclui:
- Navegação lateral para alternar entre "páginas".
- Suporte a temas Dark e Light.
- Widgets customizados para uma aparência moderna.
- Código limpo e comentado seguindo as diretrizes da PEP 8.
- Sistema de logs para rastrear interações do usuário.
- Comentários detalhados para futura integração com banco de dados SQLite3.
"""

import sys
import logging
import sqlite3
from pathlib import Path

from PySide6.QtCore import (
    Qt, QSize, QPoint, QRect, QRectF, Signal, QObject, Property,
    QPropertyAnimation, QEasingCurve
)
from PySide6.QtGui import QPainter, QColor, QFont, QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QPushButton, QStackedWidget, QComboBox,
    QAbstractButton, QListWidget, QListWidgetItem, QSizePolicy
)


# --- ESTILOS (QSS) PARA OS TEMAS ---
# Semelhante ao CSS, o QSS permite estilizar a aplicação.

DARK_STYLE = """
    QWidget {
        background-color: #202020;
        color: #FFFFFF;
        font-family: 'Segoe UI';
        font-size: 14px;
    }
    QMainWindow {
        background-color: #2D2D2D;
    }
    #Sidebar {
        background-color: #2D2D2D;
        border-right: 1px solid #404040;
    }
    #ContentFrame, #HeaderLabel {
        background-color: #202020;
    }
    QListWidget {
        border: none;
        padding-top: 10px;
    }
    QListWidget::item {
        padding: 12px 20px;
        border-radius: 5px;
    }
    QListWidget::item:hover {
        background-color: #353535;
    }
    QListWidget::item:selected {
        background-color: #0078D4;
        color: #FFFFFF;
    }
    QLabel#HeaderLabel {
        font-size: 28px;
        font-weight: 600;
        padding: 20px;
    }
    QLabel#SectionLabel {
        font-size: 18px;
        font-weight: 600;
        margin-top: 20px;
        margin-bottom: 10px;
    }
    QLabel#HintLabel {
        color: #A0A0A0;
    }
    QComboBox {
        background-color: #3C3C3C;
        border: 1px solid #505050;
        border-radius: 4px;
        padding: 5px 10px;
    }
    QComboBox:hover {
        border: 1px solid #606060;
    }
    QComboBox::drop-down {
        border: none;
    }
    QComboBox QAbstractItemView {
        background-color: #3C3C3C;
        border: 1px solid #505050;
        selection-background-color: #0078D4;
    }
    QPushButton#LinkButton {
        background-color: transparent;
        color: #0096FF;
        border: none;
        text-align: left;
        padding: 5px 0;
    }
    QPushButton#LinkButton:hover {
        text-decoration: underline;
    }
    QPushButton#ActionButton {
        background-color: #3C3C3C;
        border: 1px solid #505050;
        border-radius: 4px;
        padding: 8px 15px;
    }
    QPushButton#ActionButton:hover {
        background-color: #4A4A4A;
    }
"""

LIGHT_STYLE = """
    QWidget {
        background-color: #F3F3F3;
        color: #000000;
        font-family: 'Segoe UI';
        font-size: 14px;
    }
    QMainWindow {
        background-color: #E0E0E0;
    }
    #Sidebar {
        background-color: #E0E0E0;
        border-right: 1px solid #C0C0C0;
    }
    #ContentFrame, #HeaderLabel {
        background-color: #F3F3F3;
    }
    QListWidget {
        border: none;
        padding-top: 10px;
    }
    QListWidget::item {
        padding: 12px 20px;
        border-radius: 5px;
    }
    QListWidget::item:hover {
        background-color: #DCDCDC;
    }
    QListWidget::item:selected {
        background-color: #0078D4;
        color: #FFFFFF;
    }
    QLabel#HeaderLabel {
        font-size: 28px;
        font-weight: 600;
        padding: 20px;
    }
    QLabel#SectionLabel {
        font-size: 18px;
        font-weight: 600;
        margin-top: 20px;
        margin-bottom: 10px;
    }
    QLabel#HintLabel {
        color: #505050;
    }
    QComboBox {
        background-color: #FFFFFF;
        border: 1px solid #C0C0C0;
        border-radius: 4px;
        padding: 5px 10px;
    }
    QComboBox:hover {
        border: 1px solid #A0A0A0;
    }
    QComboBox::drop-down {
        border: none;
    }
    QComboBox QAbstractItemView {
        background-color: #FFFFFF;
        border: 1px solid #C0C0C0;
        selection-background-color: #0078D4;
    }
    QPushButton#LinkButton {
        background-color: transparent;
        color: #005B9F;
        border: none;
        text-align: left;
        padding: 5px 0;
    }
    QPushButton#LinkButton:hover {
        text-decoration: underline;
    }
    QPushButton#ActionButton {
        background-color: #FFFFFF;
        border: 1px solid #C0C0C0;
        border-radius: 4px;
        padding: 8px 15px;
    }
    QPushButton#ActionButton:hover {
        background-color: #F0F0F0;
    }
"""


# --- WIDGET CUSTOMIZADO (SWITCH) ---
# O Qt não tem um "toggle switch" moderno. Esta classe cria um.
# Isso demonstra o princípio da Responsabilidade Única (S de SOLID),
# pois esta classe cuida apenas da aparência e comportamento do switch.

class Switch(QAbstractButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(50, 28)
        self.setCursor(Qt.PointingHandCursor)

        self._thumb_position = 0
        self.animation = QPropertyAnimation(self, b"thumb_position", self)
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.InOutCubic)

        self.toggled.connect(self._handle_toggle)

    @Property(float)
    def thumb_position(self):
        return self._thumb_position

    @thumb_position.setter
    def thumb_position(self, pos):
        self._thumb_position = pos
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        is_dark_mode = self.palette().window().color().lightness() < 128
        track_color = QColor("#0078D4") if self.isChecked() \
            else QColor("#8E8E8E" if is_dark_mode else "#C0C0C0")
        thumb_color = QColor("#FFFFFF")
        track_radius = self.height() / 2

        painter.setBrush(track_color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), track_radius, track_radius)

        thumb_y = 2
        thumb_size = self.height() - 4
        thumb_x = self._thumb_position * (self.width() - thumb_size - 4) + 2

        painter.setBrush(thumb_color)
        painter.drawEllipse(int(thumb_x), thumb_y, thumb_size, thumb_size)

    def _handle_toggle(self, checked):
        self.animation.setStartValue(self.thumb_position)
        self.animation.setEndValue(1.0 if checked else 0.0)
        self.animation.start()


# --- MODELO (MVC) ---
# Responsável por armazenar e gerenciar os dados da aplicação.
# Não sabe nada sobre a interface gráfica. Emite sinais quando os dados mudam.
#
# --- INTEGRAÇÃO COM BANCO DE DADOS (Exemplo com SQLite3) ---
# Para tornar as configurações persistentes, podemos usar um banco de dados.
# Os métodos `_load_from_db` e `_save_to_db` abaixo são placeholders
# que mostram como essa integração pode ser feita.

DB_FILE = "settings.db"

class SettingsModel(QObject):
    theme_changed = Signal(str)
    word_wrap_changed = Signal(bool)
    formatting_changed = Signal(bool)

    def __init__(self):
        super().__init__()
        # Valores padrão que serão usados se o BD não existir ou estiver vazio.
        self._theme = "dark"
        self._word_wrap = True
        self._formatting = True

        # Tenta carregar as configurações do banco de dados na inicialização.
        self._db_conn = self._create_db_connection()
        self._load_from_db()

    def _create_db_connection(self):
        """Cria a conexão com o banco de dados e a tabela se não existir."""
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            # Cria a tabela de configurações. O uso de 'key' como PRIMARY KEY
            # garante que cada configuração exista apenas uma vez.
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)
            conn.commit()
            logging.info(f"Conexão com o banco de dados '{DB_FILE}' estabelecida.")
            return conn
        except sqlite3.Error as e:
            logging.error(f"Erro ao conectar ou criar tabela no banco de dados: {e}")
            return None

    def _load_from_db(self):
        """Carrega as configurações do banco de dados para o modelo."""
        if not self._db_conn:
            return

        try:
            cursor = self._db_conn.cursor()
            cursor.execute("SELECT key, value FROM settings")
            settings = dict(cursor.fetchall())

            # Atualiza os atributos do modelo com os valores do BD.
            # O `settings.get(key, default)` é usado para manter o valor padrão
            # caso a chave não seja encontrada no BD.
            self._theme = settings.get("theme", self._theme)
            self._word_wrap = settings.get("word_wrap", "1") == "1"
            self._formatting = settings.get("formatting", "1") == "1"

            logging.info("Configurações carregadas do banco de dados.")

        except sqlite3.Error as e:
            logging.error(f"Erro ao carregar configurações do banco de dados: {e}")

    def _save_to_db(self, key, value):
        """Salva um par chave-valor no banco de dados."""
        if not self._db_conn:
            return

        try:
            cursor = self._db_conn.cursor()
            # "INSERT OR REPLACE" (UPSERT) insere uma nova linha ou
            # substitui a existente se a chave (PRIMARY KEY) já existir.
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
            self._db_conn.commit()
            logging.info(f"Configuração salva no BD: {key} = {value}")
        except sqlite3.Error as e:
            logging.error(f"Erro ao salvar configuração '{key}' no banco de dados: {e}")


    @property
    def theme(self):
        return self._theme

    @theme.setter
    def theme(self, value):
        self._theme = value
        self._save_to_db("theme", value) # Salva a mudança no BD
        self.theme_changed.emit(value)

    @property
    def word_wrap(self):
        return self._word_wrap

    @word_wrap.setter
    def word_wrap(self, value):
        self._word_wrap = value
        self._save_to_db("word_wrap", "1" if value else "0") # Salva bool como string "1" ou "0"
        self.word_wrap_changed.emit(value)

    @property
    def formatting(self):
        return self._formatting

    @formatting.setter
    def formatting(self, value):
        self._formatting = value
        self._save_to_db("formatting", "1" if value else "0") # Salva bool como string "1" ou "0"
        self.formatting_changed.emit(value)


# --- VIEW (MVC) ---
# Responsável pela interface gráfica (GUI).
# Exibe os dados do modelo e envia sinais de interação do usuário
# para o Controller.

class MainWindow(QMainWindow):
    # Sinais para o Controller
    theme_selection_changed = Signal(str)
    word_wrap_toggled = Signal(bool)
    formatting_toggled = Signal(bool)
    link_button_clicked = Signal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bloco de Notas - Configurações")
        self.resize(900, 600)

        self._create_widgets()
        self._setup_layout()
        self._connect_signals()

    def _create_widgets(self):
        """Cria todos os widgets da interface."""
        self.central_widget = QWidget()
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Barra lateral de navegação
        self.sidebar = QWidget()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(250)
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(5, 0, 5, 0)
        self.sidebar_layout.setAlignment(Qt.AlignTop)

        self.nav_list = QListWidget()
        self.nav_list.addItem("Configurações")
        self.nav_list.addItem("Sobre") # Placeholder para outra página
        self.sidebar_layout.addWidget(self.nav_list)
        self.nav_list.setCurrentRow(0)

        # Conteúdo principal com QStackedWidget para as páginas
        self.content_frame = QFrame()
        self.content_frame.setObjectName("ContentFrame")
        self.content_layout = QVBoxLayout(self.content_frame)
        self.content_layout.setContentsMargins(0, 0, 0, 0)

        self.stacked_widget = QStackedWidget()
        self.settings_page = self._create_settings_page()
        self.about_page = self._create_about_page() # Página placeholder
        self.stacked_widget.addWidget(self.settings_page)
        self.stacked_widget.addWidget(self.about_page)

        self.header_label = QLabel("Configurações")
        self.header_label.setObjectName("HeaderLabel")
        self.content_layout.addWidget(self.header_label)
        self.content_layout.addWidget(self.stacked_widget)

    def _setup_layout(self):
        """Monta o layout principal."""
        self.main_layout.addWidget(self.sidebar)
        self.main_layout.addWidget(self.content_frame, 1) # O '1' faz expandir
        self.setCentralWidget(self.central_widget)

    def _create_settings_page(self):
        """Cria a página de configurações, replicando a imagem."""
        page = QWidget()
        main_layout = QHBoxLayout(page)
        main_layout.setContentsMargins(20, 0, 20, 20)

        # Coluna da Esquerda (Configurações)
        left_column = QWidget()
        left_layout = QVBoxLayout(left_column)
        left_layout.setAlignment(Qt.AlignTop)

        # --- Seção Aparência ---
        appearance_label = QLabel("Aparência")
        appearance_label.setObjectName("SectionLabel")
        left_layout.addWidget(appearance_label)

        theme_layout = self._create_setting_option(
            "Tema do aplicativo",
            "Selecionar o tema do aplicativo a ser exibido"
        )
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Escuro", "dark")
        self.theme_combo.addItem("Claro", "light")
        theme_layout.addWidget(self.theme_combo)
        left_layout.addLayout(theme_layout)

        # --- Seção Formatação de Texto ---
        format_label = QLabel("Formatação de Texto")
        format_label.setObjectName("SectionLabel")
        left_layout.addWidget(format_label)

        ww_layout = self._create_setting_option(
            "Quebra automática de linha",
            "Ajustar o texto na janela por padrão"
        )
        self.word_wrap_switch = Switch()
        ww_layout.addWidget(self.word_wrap_switch)
        left_layout.addLayout(ww_layout)

        format_switch_layout = self._create_setting_option(
            "Formatando",
            "Ativar opções de formatação de texto"
        )
        self.formatting_switch = Switch()
        format_switch_layout.addWidget(self.formatting_switch)
        left_layout.addLayout(format_switch_layout)

        left_layout.addStretch()

        # Coluna da Direita (Sobre)
        right_column = QWidget()
        right_layout = QVBoxLayout(right_column)
        right_layout.setAlignment(Qt.AlignTop)
        right_layout.setContentsMargins(40, 0, 0, 0)

        about_label = QLabel("Sobre este aplicativo")
        about_label.setObjectName("SectionLabel")
        right_layout.addWidget(about_label)

        version_label = QLabel("Projeto Clone de Bloco de notas moderno 11.2507.26.0 usando PySide6 dark/light mode")
        copyright_label = QLabel("© 2025 Microsoft, ONS. Todos os direitos reservados por Pedro Victor Veras, 27 anos.")
        copyright_label.setObjectName("HintLabel")

        right_layout.addWidget(version_label)
        right_layout.addWidget(copyright_label)
        right_layout.addSpacing(20)

        self.terms_button = QPushButton("Termos de Licença", objectName="LinkButton")
        self.privacy_button = QPushButton("Política de Privacidade", objectName="LinkButton")
        right_layout.addWidget(self.terms_button)
        right_layout.addWidget(self.privacy_button)
        right_layout.addSpacing(20)

        self.feedback_button = QPushButton("Enviar comentários", objectName="ActionButton")
        self.help_button = QPushButton("Ajuda", objectName="ActionButton")
        right_layout.addWidget(self.feedback_button)
        right_layout.addWidget(self.help_button)

        right_layout.addStretch()

        main_layout.addWidget(left_column, 2) # 2/3 do espaço
        main_layout.addWidget(right_column, 1) # 1/3 do espaço
        return page

    def _create_about_page(self):
        """Cria uma página 'Sobre' simples como placeholder."""
        page = QWidget()
        layout = QVBoxLayout(page)
        label = QLabel("Página 'Sobre'")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        return page

    def _create_setting_option(self, title, subtitle):
        """Helper para criar uma linha de configuração padrão."""
        layout = QHBoxLayout()
        text_layout = QVBoxLayout()
        text_layout.setSpacing(0)
        title_label = QLabel(title)
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("HintLabel")
        text_layout.addWidget(title_label)
        text_layout.addWidget(subtitle_label)
        layout.addLayout(text_layout, 1)
        return layout

    def _connect_signals(self):
        """Conecta os sinais dos widgets às emissões de sinais da View."""
        self.nav_list.currentRowChanged.connect(self._on_nav_changed)
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        self.word_wrap_switch.toggled.connect(self.word_wrap_toggled)
        self.formatting_switch.toggled.connect(self.formatting_toggled)

        # Conecta os botões a um handler genérico para logging
        self.terms_button.clicked.connect(lambda: self._on_link_button_clicked("Termos de Licença"))
        self.privacy_button.clicked.connect(lambda: self._on_link_button_clicked("Política de Privacidade"))
        self.feedback_button.clicked.connect(lambda: self._on_link_button_clicked("Enviar Comentários"))
        self.help_button.clicked.connect(lambda: self._on_link_button_clicked("Ajuda"))

    def _on_nav_changed(self, index):
        """Lida com a mudança de página na navegação e loga a ação."""
        page_name = self.nav_list.item(index).text()
        logging.info(f"Navegando para a página: '{page_name}'")
        self.stacked_widget.setCurrentIndex(index)

    def _on_theme_changed(self, index):
        """Emite o sinal com o nome do tema (dark/light)."""
        theme_name = self.theme_combo.itemData(index)
        self.theme_selection_changed.emit(theme_name)

    def _on_link_button_clicked(self, button_name):
        """Emite um sinal quando um botão de ação/link é clicado."""
        self.link_button_clicked.emit(button_name)


    # --- MÉTODOS PÚBLICOS (Slots para o Controller) ---

    def update_view(self, model):
        """Atualiza a UI com base no estado atual do modelo."""
        theme_index = self.theme_combo.findData(model.theme)
        self.theme_combo.setCurrentIndex(theme_index)

        self.word_wrap_switch.setChecked(model.word_wrap)
        self.formatting_switch.setChecked(model.formatting)

        self.apply_theme(model.theme)

    def apply_theme(self, theme_name):
        """Aplica o estilo QSS à aplicação."""
        style = DARK_STYLE if theme_name == "dark" else LIGHT_STYLE
        self.setStyleSheet(style)


# --- CONTROLLER (MVC) ---
# Conecta a View e o Model.
# Ouve os sinais da View, processa a lógica de negócio e atualiza o Model.
# Ouve os sinais do Model para atualizar a View.

class AppController:
    def __init__(self, model: SettingsModel, view: MainWindow):
        self._model = model
        self._view = view
        self._connect_signals()
        self._view.update_view(self._model)

    def _connect_signals(self):
        """Conecta os sinais e slots entre M, V e C."""
        # View -> Controller
        self._view.theme_selection_changed.connect(self.change_theme)
        self._view.word_wrap_toggled.connect(self.toggle_word_wrap)
        self._view.formatting_toggled.connect(self.toggle_formatting)
        self._view.link_button_clicked.connect(self.log_button_click)

        # Model -> View
        # Neste caso simples, o controller atualiza a view diretamente.
        # Em apps maiores, poderíamos usar sinais do modelo.
        # ex: self._model.theme_changed.connect(self._view.apply_theme)

    # --- SLOTS (para sinais da View) ---

    def change_theme(self, theme_name):
        logging.info(f"Ação do usuário: Mudar tema para '{theme_name}'")
        self._model.theme = theme_name
        self._view.apply_theme(theme_name) # Atualiza a UI

    def toggle_word_wrap(self, is_checked):
        logging.info(f"Ação do usuário: Mudar 'Quebra automática de linha' para {is_checked}")
        self._model.word_wrap = is_checked

    def toggle_formatting(self, is_checked):
        logging.info(f"Ação do usuário: Mudar 'Formatando' para {is_checked}")
        self._model.formatting = is_checked

    def log_button_click(self, button_name):
        logging.info(f"Ação do usuário: Clique no botão '{button_name}'")


# --- PONTO DE ENTRADA DA APLICAÇÃO ---

def setup_logging():
    """Configura o sistema de logs para salvar em arquivo e mostrar no console."""
    log_file = Path(__file__).parent / "app.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] - %(message)s",
        handlers=[
            logging.FileHandler(log_file, mode='w'), # 'w' para sobrescrever o log a cada execução
            logging.StreamHandler(sys.stdout)
        ]
    )
    logging.info("Aplicação iniciada. Sistema de logs configurado.")


def main():
    """Função principal que inicia a aplicação."""
    setup_logging()
    app = QApplication(sys.argv)

    # 1. Cria as instâncias de Model, View e Controller
    # O modelo agora se conecta e carrega os dados do BD na sua inicialização.
    model = SettingsModel()
    view = MainWindow()
    controller = AppController(model=model, view=view)

    # 2. Exibe a janela principal
    view.show()

    # 3. Inicia o loop de eventos da aplicação
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

