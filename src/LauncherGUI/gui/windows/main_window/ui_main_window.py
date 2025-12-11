# IMPORT QT CORE
from qt_core import *

# IMPORT CUSTOM WIDGETS
from gui.widgets.py_push_button import PyPushButton
from gui.widgets.py_text_button import PyTextButton

# MAIN WINDOW
class UI_MainWindow(object):
    def setup_ui(self, parent):
        if not parent.objectName():
            parent.setObjectName("MainWindow")

        # SET INITIAL PARAMETERS
        # ///////////////////////////////////////////////////////////////
        parent.resize(1200, 720)
        parent.setMinimumSize(960, 540)

        # CREATE CENTRAL WIDGET
        # ///////////////////////////////////////////////////////////////
        self.central_frame = QFrame()

        # CREATE MAIN LAYOUT
        self.main_layout = QHBoxLayout(self.central_frame)
        self.main_layout.setContentsMargins(0,0,0,0)
        self.main_layout.setSpacing(0)

        # LEFT MENU (A DYNAMIC CONTAINER)
        # ///////////////////////////////////////////////////////////////
        self.left_menu = QFrame()
        self.left_menu.setObjectName("left_menu")
        self.left_menu.setMinimumWidth(240)
        self.left_menu.setMaximumWidth(240)

        # LEFT MENU LAYOUT
        self.left_menu_layout = QVBoxLayout(self.left_menu)
        self.left_menu_layout.setContentsMargins(5,5,5,5)
        self.left_menu_layout.setSpacing(10)
        
        # The layout will be populated dynamically by main.py
        
        # LABEL VERSION
        # ///////////////////////////////////////////////////////////////
        self.left_menu_label_version = QLabel("v4.1.3")
        self.left_menu_label_version.setAlignment(Qt.AlignCenter)
        self.left_menu_label_version.setMinimumHeight(30)
        self.left_menu_label_version.setMaximumHeight(30)
        self.left_menu_label_version.setStyleSheet("color: #c3ccdf")

        # ADD TO LAYOUT
        # ///////////////////////////////////////////////////////////////
        self.left_menu_layout.addWidget(self.left_menu_label_version)

        # CONTENT
        # ///////////////////////////////////////////////////////////////
        self.content = QFrame()
        self.content.setObjectName("content")

        # Content Layout
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0,0,0,0)
        self.content_layout.setSpacing(0)

        # TOP BAR (AppBar)
        # ///////////////////////////////////////////////////////////////
        self.top_bar = QFrame()
        self.top_bar.setMinimumHeight(40)
        self.top_bar.setMaximumHeight(40)
        self.top_bar.setObjectName("top_bar")
        self.top_bar_layout = QHBoxLayout(self.top_bar)
        self.top_bar_layout.setContentsMargins(10,0,10,0)

        # Left side of AppBar
        self.toggle_button = PyPushButton(text="Menu", icon_path="icon_menu.svg")
        self.toggle_button.setToolTip("Ocultar/Mostrar Menu Lateral")
        
        # Spacer
        self.top_spacer = QSpacerItem(20,20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        # Add to AppBar layout
        self.top_bar_layout.addWidget(self.toggle_button)
        self.top_bar_layout.addItem(self.top_spacer)
        # TextButtons for links will be added dynamically by main.py

        # Application Tabs
        self.tabs = QTabWidget()
        self.tabs.setObjectName("tabs")
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)

        # BOTTOM BAR
        # ///////////////////////////////////////////////////////////////
        self.bottom_bar = QFrame()
        self.bottom_bar.setMinimumHeight(30)
        self.bottom_bar.setMaximumHeight(30)
        self.bottom_bar.setObjectName("bottom_bar")

        self.bottom_bar_layout = QHBoxLayout(self.bottom_bar)
        self.bottom_bar_layout.setContentsMargins(10,0,10,0)

        # Left label
        self.bottom_label_left = QLabel("Criado por: Pedro Veras")
        self.bottom_bar_layout.addWidget(self.bottom_label_left)

        # ADD TO CONTENT LAYOUT
        self.content_layout.addWidget(self.top_bar)
        self.content_layout.addWidget(self.tabs)
        self.content_layout.addWidget(self.bottom_bar)

        # ADD WIDGETS TO APP
        # ///////////////////////////////////////////////////////////////
        self.main_layout.addWidget(self.left_menu)
        self.main_layout.addWidget(self.content)

        # SET CENTRAL WIDGET
        parent.setCentralWidget(self.central_frame)

