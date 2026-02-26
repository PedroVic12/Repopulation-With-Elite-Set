# launcher_window.ui

## Qt Designer UI file — Janela Principal do RCE Framework Launcher

### Como usar:

1. Editar visualmente: designer ui/launcher_window.ui
2. Gerar Python: pyside6-uic ui/launcher_window.ui -o ui/ui_launcher_window.py

3. Carregar em tempo de execução (forma usada neste projeto):

```python
   from PySide6.QtUiTools import QUiLoader

   loader = QUiLoader()

   ui = loader.load("ui/launcher_window.ui", self)
```

— ou —

```python
from PySide6.QtCore import QFile

ui_file = QFile("ui/launcher_window.ui")

loader.load(ui_file, self)
```

### Objetos importantes (acessíveis via self.ui.`<objectName>`):

- central_widget — QWidget central

- left_menu — QFrame menu lateral esquerdo (fixedWidth=240)

- toggle_button — QPushButton "☰" para expandir/recolher menu

- nav_menu_container— QWidget placeholder onde NavigationMenu é injetado

- tabs — QTabWidget área de conteúdo principal
