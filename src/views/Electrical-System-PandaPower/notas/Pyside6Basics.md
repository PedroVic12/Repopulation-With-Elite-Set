# Conceitos Básicos de PySide6 (Qt for Python)

Este documento explica os principais conceitos do PySide6 usados na construção do `main_launcher.py`.

## 1. Janela Principal (QMainWindow)

A `QMainWindow` é a base de uma aplicação desktop. Ela funciona como a janela principal que contém todos os outros elementos, como menus, barras de ferramentas e os widgets centrais da sua aplicação.

- **No seu código:** A classe `LauncherWindow(QMainWindow)` é a sua janela principal.

## 2. Widgets

Widgets são os "tijolos" de uma interface gráfica. Tudo que você vê na tela é um widget ou parte de um.

- **`QPushButton`**: Um botão que pode ser clicado.
- **`QLabel`**: Um rótulo para exibir texto ou imagens.
- **`QLineEdit`**: Uma caixa para o usuário digitar uma única linha de texto.
- **`QTextEdit`**: Uma área para exibir ou editar múltiplas linhas de texto (como o seu log).
- **`QComboBox`**: Uma lista de opções que o usuário pode selecionar (dropdown).
- **`QProgressBar`**: Uma barra de progresso.
- **`QSpinBox`**: Uma caixa para selecionar números inteiros.
- **`QGroupBox`**: Uma caixa com uma borda e um título, usada para agrupar outros widgets.

## 3. Layouts

Layouts são responsáveis por organizar os widgets dentro de uma janela ou de outro widget. Eles gerenciam o tamanho e a posição dos elementos, garantindo que a interface se ajuste bem quando a janela é redimensionada.

- **`QVBoxLayout`**: Organiza os widgets verticalmente (um abaixo do outro).
- **`QHBoxLayout`**: Organiza os widgets horizontalmente (um ao lado do outro).
- **`QGridLayout`**: Organiza os widgets em uma grade (linhas e colunas).

## 4. Abas (QTabWidget)

O `QTabWidget` é um container que permite criar uma interface com múltiplas "páginas" ou abas. O usuário pode alternar entre as abas clicando no título de cada uma.

- **No seu código:** O `self.tabs = QTabWidget()` no `LauncherWindow` é o que permite ter as abas "Configurar AG", "Executar AG", "Console", etc.

## 5. Sinais e Slots (Signals & Slots)

Este é o coração do Qt e a forma como os objetos se comunicam.

- **Sinal (Signal):** É uma notificação que um objeto emite quando algo acontece. Ex: um `QPushButton` emite o sinal `clicked()` quando é clicado.
- **Slot:** É uma função que é executada em resposta a um sinal.

A conexão `sinal.connect(slot)` é o que liga o evento à ação.

- **No seu código:** `self.run_button.clicked.connect(self.prepare_and_run)` conecta o sinal `clicked` do botão a uma função `prepare_and_run`, que será executada quando o botão for clicado.

## 6. Threads (QThread & Worker)

Uma aplicação GUI tem uma thread principal que desenha a interface e responde ao usuário. Se você rodar uma tarefa longa (como o seu algoritmo genético) nessa thread, a interface irá congelar.

- **`QThread`**: É uma classe que gerencia uma thread separada do sistema operacional.
- **Padrão Worker:** A forma correta de usar `QThread` é criar uma classe "Worker" (que herda de `QObject`) com a sua lógica demorada. Você move esse worker para a nova thread. O worker emite sinais para comunicar o progresso (`log_updated`) ou o término (`finished`) para a thread principal, que pode então atualizar a interface gráfica sem congelar.

- **No seu código:** As classes `ScriptWorker` e `ExecutionModel` usam `QThread` para rodar o `run.py` em segundo plano, permitindo que a interface continue responsiva e exibindo os logs em tempo real.

## 7. IFrames (QWebEngineView)

O termo "IFrame" é do mundo web e se refere a uma página embutida em outra. O equivalente no PySide6 para exibir conteúdo web é o `QWebEngineView`. Ele é basicamente um navegador Chromium completo embutido na sua aplicação.

- **No seu código:** A classe `PlotlyWidget` usa `QWebEngineView` para renderizar os gráficos interativos da biblioteca Plotly. O Plotly gera o gráfico como um arquivo HTML, e o `QWebengineView` exibe esse HTML.
