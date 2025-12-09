# ///////////////////////////////////////////////////////////////
#
# BY: Pedro Victor Rodrigues Veras 
# PROJECT MADE WITH: Qt Designer and PySide6 for a app template Pyside6 with IFrames, Widgets, Dark/Light Mode, Settings and more!
# VERSÃO: 3.1.4
#
# ///////////////////////////////////////////////////////////////

# IMPORT MODULES
import sys
import webbrowser
from functools import partial

# IMPORT QT CORE
from qt_core import *

# IMPORT STYLES
from styles import DARK_STYLE, LIGHT_STYLE

# IMPORT MODEL
from app.models.settings_model import SettingsModel

# IMPORT UI
from gui.windows.main_window.ui_main_window import UI_MainWindow

# IMPORT IFRAME WIDGETS (pagina separadas para cada TAB)
from gui.iframes.dashboard_widget import DashboardWidget
from gui.iframes.checklist_widget import ChecklistWidget
from gui.iframes.settings_widget import SettingsWidget

# IMPORT IFRAME WIDGETS (pagina separadas para cada TAB)
from gui.iframes.perdas_duplas_widget import PerdasDuplasWidget 


# IMPORT SIDE MENU WIDGETS
from gui.side_menus.navigation_menu import NavigationMenu
from gui.side_menus.checklist_sidemenu import ChecklistSideMenu
from gui.side_menus.default_sidemenu import DefaultSideMenu

# IMPORT CUSTOM WIDGETS
from gui.widgets.py_text_button import PyTextButton

# MAIN WINDOW
class MainWindow(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self.app = app 

        # --- DICTIONARIES TO MANAGE DYNAMIC WIDGETS ---
        self.open_tabs = {}
        self.side_menus = {}
        self.tab_to_side_menu_map = {}

        # --- SETUP MAIN WINDOW AND UI ---
        self.ui = UI_MainWindow()
        self.ui.setup_ui(self)

        # --- SETUP SETTINGS MODEL AND APPLY INITIAL SETTINGS ---
        self.settings_model = SettingsModel()
        self.settings_model.settings_changed.connect(self.apply_settings_from_model)
        self.apply_settings_from_model()

        # --- SETUP DYNAMIC UI MODULES ---
        self.navigation_menu = NavigationMenu()
        self.ui.left_menu_layout.insertWidget(0, self.navigation_menu)


        # import default widgets
        self.side_menu_stack = QStackedWidget()
        self.default_side_menu = DefaultSideMenu()
        self.side_menus['default'] = self.default_side_menu
        self.side_menu_stack.addWidget(self.default_side_menu)
        self.ui.left_menu_layout.insertWidget(1, self.side_menu_stack)

        self._setup_appbar_links()
        
        # --- CONNECT SIGNALS ---
        self.connect_signals()

        # --- OPEN INITIAL TAB ---
        self.open_dashboard_tab()

        # --- SHOW APP ---
        self.show()

    #! NAVIGATION HANDLERS TABS FUNCTIONS
    # ///////////////////////////////////////////////////////////////
    def open_dashboard_tab(self): self.open_or_focus_tab("Dashboard", DashboardWidget)
    #def open_pomodoro_tab(self): self.open_or_focus_tab("Pomodoro", PomodoroWidget)
    def open_checklist_tab(self): self.open_or_focus_tab("Checklist", ChecklistWidget, ChecklistSideMenu)
    def open_settings_tab(self): self.open_or_focus_tab("Configurações", SettingsWidget)
    def open_perdas_duplas_tab(self): """Abre a aba da ferramenta de Perdas Duplas ETL.""" ; self.open_or_focus_tab("Perdas Duplas ETL", PerdasDuplasWidget)

    #! CONNECT SIGNALS
    def connect_signals(self):
        # Main Navigation
        self.navigation_menu.dashboard_requested.connect(self.open_dashboard_tab)
        #self.navigation_menu.pomodoro_requested.connect(self.open_pomodoro_tab)
        self.navigation_menu.checklist_requested.connect(self.open_checklist_tab)
        self.navigation_menu.settings_requested.connect(self.open_settings_tab)
        self.navigation_menu.perdas_duplas_requested.connect(self.open_perdas_duplas_tab) # Conecta o sinal do NavigationMenu
        

        # Other UI
        self.ui.toggle_button.clicked.connect(self.toggle_button)
        self.ui.tabs.currentChanged.connect(self.on_tab_changed)
        self.ui.tabs.tabCloseRequested.connect(self.close_tab)



    # CORE UI LOGIC
    # ///////////////////////////////////////////////////////////////
    def _setup_appbar_links(self):
        links = {
            "🌍 GitHub": "https://github.com/PedroVic12",
            "Pyside6 web": "https://doc.qt.io/qtforpython-6/PySide6/QtWebEngineWidgets/QWebEngineView.html#PySide6.QtWebEngineWidgets.QWebEngineView",
            "PySide6 QtWidgets": "https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QApplication.html#PySide6.QtWidgets.QApplication",
            "📚 Dashboard Atividades SP": "https://dashboard-ons.onrender.com/",
            "📚 Habit Tracker": "https://gohann-treinamentos-web-app-one.vercel.app",
            "⚡ SEP para Leigos": "https://electrical-system-simulator.vercel.app/"
        }
        for text, url in links.items():
            btn = PyTextButton(text=text)
            btn.setToolTip(f"Abrir {url} no navegador")
            btn.clicked.connect(partial(webbrowser.open, url))
            self.ui.top_bar_layout.addWidget(btn)

    def open_or_focus_tab(self, tab_name, main_widget_class, side_menu_class=None):
        if tab_name in self.open_tabs:
            self.ui.tabs.setCurrentWidget(self.open_tabs[tab_name])
        else:
            side_menu_widget = None
            if side_menu_class:
                if side_menu_class.__name__ not in self.side_menus:
                    side_menu_widget = side_menu_class()
                    self.side_menus[side_menu_class.__name__] = side_menu_widget
                    self.side_menu_stack.addWidget(side_menu_widget)
                else:
                    side_menu_widget = self.side_menus[side_menu_class.__name__]
            
            main_widget = main_widget_class(side_menu=side_menu_widget)
            index = self.ui.tabs.addTab(main_widget, tab_name)
            self.ui.tabs.setCurrentIndex(index)
            self.open_tabs[tab_name] = main_widget
            if side_menu_widget:
                self.tab_to_side_menu_map[main_widget] = side_menu_widget
        
        self.navigation_menu.set_active_button(tab_name)

    #! SETTINGS FUNCTIONS
    # ///////////////////////////////////////////////////////////////
    @Slot(int)
    def on_tab_changed(self, index):
        current_tab_widget = self.ui.tabs.widget(index)
        side_menu = self.tab_to_side_menu_map.get(current_tab_widget)
        if side_menu:
            self.side_menu_stack.setCurrentWidget(side_menu)
        else:
            self.side_menu_stack.setCurrentWidget(self.default_side_menu)
        
        tab_name = self.ui.tabs.tabText(index)
        self.navigation_menu.set_active_button(tab_name)

    @Slot(int)
    def close_tab(self, index):
        widget = self.ui.tabs.widget(index)
        if widget:
            tab_name = self.ui.tabs.tabText(index)
            if tab_name in self.open_tabs:
                del self.open_tabs[tab_name]
            if widget in self.tab_to_side_menu_map:
                del self.tab_to_side_menu_map[widget]
            widget.deleteLater()
            self.ui.tabs.removeTab(index)

    @Slot()
    def apply_settings_from_model(self):
        theme = self.settings_model.get("theme")
        self.app.setStyleSheet(DARK_STYLE if theme == "dark" else LIGHT_STYLE)
        font = QFont(self.settings_model.get("font_family"), self.settings_model.get("font_size"))
        self.app.setFont(font)
        if "Configurações" in self.open_tabs:
            widget = self.open_tabs["Configurações"]
            widget.style().unpolish(widget)
            widget.style().polish(widget)
            widget.update()

    @Slot(dict)
    def handle_settings_saved(self, settings_dict):
        self.settings_model.set_and_save(settings_dict)

    # ANIMATION
    # ///////////////////////////////////////////////////////////////
    def toggle_button(self):
        menu_width = self.ui.left_menu.width()
        width = 0 if menu_width > 0 else 240
        self.animation = QPropertyAnimation(self.ui.left_menu, b"minimumWidth")
        self.animation.setStartValue(menu_width)
        self.animation.setEndValue(width)
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.animation.start()
        self.animation2 = QPropertyAnimation(self.ui.left_menu, b"maximumWidth")
        self.animation2.setStartValue(menu_width)
        self.animation2.setEndValue(width)
        self.animation2.setDuration(300)
        self.animation2.setEasingCurve(QEasingCurve.InOutCubic)
        self.animation2.start()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("icon.ico"))
    window = MainWindow(app)
    sys.exit(app.exec())