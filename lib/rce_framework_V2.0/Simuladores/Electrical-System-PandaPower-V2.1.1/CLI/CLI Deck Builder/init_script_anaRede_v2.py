#!/usr/bin/env python3
"""
script_inicial_anaRede.py - Sistema Completo de Automação AnaREDE e Organon
Integrado com CLI Launcher usando Rich TUI

Autor: Pedro Victor
Versão: 2.0.0
Data: Janeiro 2026
"""

import sys
import os
import subprocess
import time
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict, Tuple
import pyautogui
import pygame

try:
    from gtts import gTTS
except ImportError:
    print("⚠️  gtts não instalado. Função de voz desabilitada.")
    gTTS = None

try:
    from win10toast import ToastNotifier
    WINDOWS = True
except ImportError:
    WINDOWS = False
    print("⚠️  win10toast não disponível (apenas Windows)")

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
    from rich.table import Table
    from rich.style import Style
    from rich import box
    from rich.tree import Tree
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.live import Live
except ImportError:
    raise ImportError(
        "A biblioteca 'rich' é necessária. Instale com: pip install rich"
    )

console = Console()

"""
Arquitetura da automação:
CLI (seleção)
   ↓
Memória explícita (casos_selecionados)
   ↓
run_automation()
   ↓
AnaRedeDeckBuilder
   ↓
PyAutoGUI (cliques e digitação com teclado e mouse)
"""


# ============================================================================
# CLASSE CONFIGURACOES (Original mantida)
# ============================================================================
class Configuracoes:
    """Configurações originais do sistema"""
    
    def __init__(self):
        # Caminhos originais
        caminho_sav: str = r"C:\Users\pedrovictor.veras\OneDrive - Operador Nacional do Sistema Eletrico\Documentos\ESTAGIO_ONS_PVRV_2025\Casos - Cenarios - ONS - Real\SIN\Sav\3Q2025_estudo_v1.SAV"
        caminho_spt: str = r"C:\Users\pedrovictor.veras\OneDrive - Operador Nacional do Sistema Eletrico\Documentos\ESTAGIO_ONS_PVRV_2025\Casos - Cenarios - ONS - Real\SIN\diagramas\SIN.lst"
        
        # NOVA VARIÁVEL - Caminho dos decks
        self.caminho_decks_anaRede: str = r"C:\Users\pedrovictor.veras\OneDrive - Operador Nacional do Sistema Eletrico\Documentos\ESTAGIO_ONS_PVRV_2025\ONS + SIN + Tarefas PLC 2026\SIN"
        
        self.PROGRAMAS: list[str] = ["Explorador de arquivos", "Anarede 12", "Organon.exe"]
        
        self.arquivos_anaRede: dict[str, str] = {
            "caminho_sav": caminho_sav,
            "caminho_spt": caminho_spt,
            "caminho_decks": self.caminho_decks_anaRede,
        }
        
        # Create a ToastNotifier object
        self.toaster: ToastNotifier = ToastNotifier() if WINDOWS else None
    
    def showToast(self, title: str, message: str, icon_path: str = None, 
                   duration: int = 5, threaded: bool = True):
        """Mostra uma notificação na tela (Original)"""
        if not self.toaster:
            console.print(Panel(f"[bold]{title}[/bold]\n{message}", border_style="blue"))
            return
        
        if icon_path is None:
            icon_path = os.path.join(os.getcwd(), "icon.ico")
        if not os.path.exists(icon_path):
            icon_path = None
        
        self.toaster.show_toast(title, message, icon_path, duration, threaded)


# ============================================================================
# CLASSE C3POGeminiAssistant (Original mantida)
# ============================================================================
class C3POGeminiAssistant:
    """Assistente original C3PO com Gemini"""
    
    def __init__(self):
        pygame.mixer.init()
        self.voice_enabled = True
    
    def generate_gemini_response(self, prompt: str):
        """Gera uma resposta usando o modelo Gemini"""
        console.print("[yellow]⚠️  Gemini API não configurada[/yellow]")
        pass
    
    def execute_sql_query(self, query: str):
        """Executa uma consulta SQL"""
        console.print("[yellow]⚠️  SQL não configurado[/yellow]")
        pass
    
    def display_data(self, data: list[dict]):
        """Exibe os dados em uma tabela"""
        if not data:
            console.print("[yellow]Sem dados para exibir[/yellow]")
            return
        
        table = Table(title="Dados", box=box.ROUNDED)
        if data:
            for key in data[0].keys():
                table.add_column(key, style="cyan")
            for row in data:
                table.add_row(*[str(v) for v in row.values()])
        console.print(table)
    
    def falar(self, texto: str):
        """Gera e executa um áudio em português (voz sintética) - ORIGINAL"""
        console.print(f"[blue]🔊 {texto}[/blue]")
        
        if not self.voice_enabled or not gTTS:
            return
        
        try:
            tts = gTTS(text=texto, lang='pt-br', slow=False)
            arquivo = os.path.join(os.getcwd(), "fala_temp.mp3")
            tts.save(arquivo)
            
            # Reproduzir com pygame
            pygame.mixer.music.load(arquivo)
            pygame.mixer.music.play()
            
            # Aguardar finalizar
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            
            os.remove(arquivo)
            
        except FileNotFoundError:
            console.print("[yellow]⚠️  Erro: 'mpg123' não encontrado[/yellow]")
        except Exception as e:
            console.print(f"[yellow]Erro ao gerar fala: {e}[/yellow]")
    
    def abrir_programa(self, nome_programa):
        """Abre o programa digitando no menu iniciar - ORIGINAL"""
        self.falar(f"Abrindo programa {nome_programa}")
        pyautogui.press('win')
        time.sleep(1)
        pyautogui.write(nome_programa)
        time.sleep(1)
        pyautogui.press('enter')
        time.sleep(5)
        console.print(f"[green]✅ {nome_programa} aberto.[/green]")


# ============================================================================
# CLASSE AnaRedeDeckBuilder (Original mantida e expandida)
# ============================================================================
class AnaRedeDeckBuilder:
    """Classe original para automação do AnaREDE"""
    
    def __init__(self, assistant: C3POGeminiAssistant):
        self.assistant = assistant
        
        # Hash table de coordenadas (key: label_snake_case, value: (x, y))
        self.coordenadas = {
            # Menu principal AnaREDE
            'menu_caso': (50, 35),
            'menu_abrir_caso': (100, 70),
            'menu_salvar_caso': (100, 95),
            'menu_exibir': (106, 35),
            'menu_dados': (165, 35),
            'menu_analise': (248, 35),
            'menu_ferramentas': (350, 35),
            
            # Botões de ação
            'botao_executar_fluxo': (300, 100),
            'botao_calcular': (320, 120),
            
            # Campos de entrada
            'campo_caminho_arquivo': (400, 300),
            
            # Organon
            'organon_menu_arquivo': (100, 50),
            'organon_abrir_diagrama': (130, 180),
            
            # EditCepel
            'editcepel_centro_editor': (500, 400),
        }

    def carregar_caso_completo(self, casos: dict):
        """
        Abre o AnaREDE e carrega:
        - Caso .SAV
        - Diagrama .LST
        - Deck (.dat / .pdw / .txt)
        """
        self.carregar_save_case(casos['sav'])
        self.carregar_diagrama(casos['lst'])
        self.colar_deck_editcepel(casos['deck'])
        self.executar_fluxo()
        self.salvar_caso()
        self.salvar_diagrama()
        self.salvar_deck()
        self.salvar_caso_completo()
        self.salvar_diagrama_completo()
        self.salvar_deck_completo()

    
    def carregar_save_case(self, caminho_arquivo):
        """Carrega um arquivo .SAV no AnaREDE - ORIGINAL"""
        self.assistant.falar("Carregando caso do fluxo de potência.")
        time.sleep(2)
        
        # Clicar no menu Caso usando coordenadas da hash table
        console.print(f"[cyan]Clicando em Menu Caso: {self.coordenadas['menu_caso']}[/cyan]")
        pyautogui.click(*self.coordenadas['menu_caso'])
        time.sleep(1)
        
        # Clicar em Abrir Caso
        console.print(f"[cyan]Clicando em Abrir Caso: {self.coordenadas['menu_abrir_caso']}[/cyan]")
        pyautogui.click(*self.coordenadas['menu_abrir_caso'])
        time.sleep(2)
        
        # Digita o caminho do arquivo e pressiona Enter
        console.print(f"[cyan]Digitando caminho: {caminho_arquivo}[/cyan]")
        pyautogui.write(caminho_arquivo, interval=0.01)
        time.sleep(0.5)
        pyautogui.press('enter')
        time.sleep(3)
        
        console.print(f"[green]✅ Caso {os.path.basename(caminho_arquivo)} carregado no AnaREDE.[/green]")
    
    def abrir_editcepel_com_arquivo(self, caminho_arquivo: str):
        """Abre EditCepel e carrega arquivo"""
        self.assistant.falar("Abrindo EditCepel com arquivo")
        
        # Abrir EditCepel
        self.assistant.abrir_programa("EditCepel")
        time.sleep(3)
        
        # Ctrl+O para abrir arquivo
        pyautogui.hotkey('ctrl', 'o')
        time.sleep(2)
        
        # Digitar caminho
        pyautogui.write(caminho_arquivo, interval=0.01)
        pyautogui.press('enter')
        time.sleep(2)
        
        console.print(f"[green]✅ EditCepel aberto com {os.path.basename(caminho_arquivo)}[/green]")
    
    def inserir_regua_editcepel(self):
        """Insere régua de comandos no EditCepel - Atalho Ctrl+*"""
        pyautogui.hotkey('ctrl', 'shift', '8')  # ctrl+*
        time.sleep(0.5)
        console.print("[green]✓ Régua inserida[/green]")
    
    def colar_deck_editcepel(self, caminho_deck: str):
        """Lê deck e cola no EditCepel usando Ctrl+V"""
        try:
            # Ler arquivo
            with open(caminho_deck, 'r', encoding='utf-8') as f:
                conteudo = f.read()
            
            # Copiar para clipboard
            import pyperclip
            pyperclip.copy(conteudo)
            
            # Clicar no centro do editor
            pyautogui.click(*self.coordenadas['editcepel_centro_editor'])
            time.sleep(0.3)
            
            # Colar com Ctrl+V
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.5)
            
            console.print(f"[green]✓ Deck colado: {os.path.basename(caminho_deck)}[/green]")
        
        except Exception as e:
            console.print(f"[red]✗ Erro ao colar deck: {e}[/red]")
    
    def abrirEditCepel(self):
        """Abre o menu Edit -> Cepel - ORIGINAL"""
        self.assistant.abrir_programa("EditCepel")
    
    def carregar_diagrama(self, caminho_arquivo: str):
        """Carrega um arquivo de diagrama no Organon - ORIGINAL"""
        self.assistant.falar("Carregando diagrama elétrico no Organon.")
        time.sleep(2)
        
        # Clicar no menu Arquivo do Organon
        console.print(f"[cyan]Clicando em Menu Arquivo: {self.coordenadas['organon_menu_arquivo']}[/cyan]")
        pyautogui.click(*self.coordenadas['organon_menu_arquivo'])
        time.sleep(1)
        
        # Clicar em Abrir Diagrama
        console.print(f"[cyan]Clicando em Abrir Diagrama: {self.coordenadas['organon_abrir_diagrama']}[/cyan]")
        pyautogui.click(*self.coordenadas['organon_abrir_diagrama'])
        time.sleep(2)
        
        # Digitar caminho
        console.print(f"[cyan]Digitando caminho: {caminho_arquivo}[/cyan]")
        pyautogui.write(caminho_arquivo, interval=0.01)
        pyautogui.press('enter')
        time.sleep(3)
        
        console.print(f"[green]✅ Diagrama {os.path.basename(caminho_arquivo)} carregado no Organon.[/green]")
    
    def diagnosticar_posicao_mouse(self):
        """Mostra a posição atual do mouse e emite um alerta - ORIGINAL"""
        self.assistant.falar("Diagnóstico da posição do mouse ativado. Mova o mouse para o local desejado.")
        time.sleep(3)
        x, y = pyautogui.position()
        self.assistant.falar(f"Posição do mouse: X={x}, Y={y}")
        console.print(f"[green]Posição do mouse: X={x}, Y={y}[/green]")
        
        # Alerta visual (opcional)
        pyautogui.alert(text=f'Posição do mouse: X={x}, Y={y}', 
                       title='Diagnóstico de Posição', button='OK')
    
    def executar_fluxo(self):
        """Executa cálculo de fluxo de potência"""
        self.assistant.falar("Executando cálculo de fluxo")
        pyautogui.press('ctrl', 'f5')
        time.sleep(3)
        console.print("[green]✅ Fluxo executado[/green]")
    
    def adicionar_coordenada(self, label: str, x: int, y: int):
        """Adiciona nova coordenada à hash table"""
        self.coordenadas[label] = (x, y)
        console.print(f"[green]✓ Coordenada '{label}' adicionada: ({x}, {y})[/green]")
    
    def mostrar_coordenadas(self):
        """Mostra todas as coordenadas cadastradas"""
        table = Table(title="📍 Coordenadas Cadastradas", box=box.ROUNDED)
        table.add_column("Label", style="cyan")
        table.add_column("X", style="green", justify="right")
        table.add_column("Y", style="green", justify="right")
        
        for label, (x, y) in sorted(self.coordenadas.items()):
            table.add_row(label, str(x), str(y))
        
        console.print(table)
    
    def salvar_coordenadas(self, arquivo: str = "coordenadas.json"):
        """Salva coordenadas em arquivo JSON"""
        with open(arquivo, 'w', encoding='utf-8') as f:
            json.dump(self.coordenadas, f, indent=2, ensure_ascii=False)
        console.print(f"[green]✓ Coordenadas salvas em {arquivo}[/green]")
    
    def carregar_coordenadas(self, arquivo: str = "coordenadas.json"):
        """Carrega coordenadas de arquivo JSON"""
        try:
            with open(arquivo, 'r', encoding='utf-8') as f:
                coords = json.load(f)
                # Converter listas para tuplas
                self.coordenadas = {k: tuple(v) for k, v in coords.items()}
            console.print(f"[green]✓ Coordenadas carregadas de {arquivo}[/green]")
        except FileNotFoundError:
            console.print(f"[yellow]⚠️  Arquivo {arquivo} não encontrado[/yellow]")


# ============================================================================
# CLASSE MouseTracker (Nova - para rastreamento avançado)
# ============================================================================
class MouseTracker:
    """Rastreador avançado de posição do mouse"""
    
    def __init__(self):
        self.tracking = False
        self.positions = []
    
    def start_tracking(self, duration: int = 10):
        """Inicia rastreamento por um período definido"""
        self.tracking = True
        console.print(f"\n[yellow]🖱️  Rastreamento ativado por {duration} segundos[/yellow]")
        console.print("[cyan]Pressione ESC para parar[/cyan]\n")
        
        start_time = time.time()
        
        try:
            while self.tracking and (time.time() - start_time) < duration:
   
                x, y = pyautogui.position()
                timestamp = time.time() - start_time
                
                console.print(f"\r[green]Posição: X={x:4d}, Y={y:4d}[/green] | Tempo: {timestamp:.1f}s", end="")
                
                self.positions.append((x, y, timestamp))
                time.sleep(0.1)
        
        except ImportError:
            console.print("[yellow]⚠️  keyboard não instalado, usando modo simples[/yellow]")
            # Modo simples sem keyboard
            while self.tracking and (time.time() - start_time) < duration:
                x, y = pyautogui.position()
                timestamp = time.time() - start_time
                console.print(f"\r[green]Posição: X={x:4d}, Y={y:4d}[/green] | Tempo: {timestamp:.1f}s", end="")
                self.positions.append((x, y, timestamp))
                time.sleep(0.1)
        
        except KeyboardInterrupt:
            pass
        finally:
            self.tracking = False
            console.print("\n\n[yellow]Rastreamento finalizado[/yellow]")
            self.show_summary()
    
    def show_summary(self):
        """Mostra resumo das posições capturadas"""
        if not self.positions:
            console.print("[red]Nenhuma posição capturada[/red]")
            return
        
        table = Table(title="📍 Posições Capturadas", box=box.ROUNDED)
        table.add_column("#", style="cyan", justify="right")
        table.add_column("X", style="green", justify="right")
        table.add_column("Y", style="green", justify="right")
        table.add_column("Tempo (s)", style="yellow", justify="right")
        
        for i, (x, y, t) in enumerate(self.positions[-10:], 1):
            table.add_row(str(i), str(x), str(y), f"{t:.2f}")
        
        console.print(table)
    
    def capture_position(self, label: str = ""):
        """Captura posição atual com label"""
        x, y = pyautogui.position()
        console.print(f"[green]✓[/green] {label}: X={x}, Y={y}")
        return (x, y)


# ============================================================================
# CLASSE FileExplorer (Nova - explorador de arquivos Rich)
# ============================================================================
class FileExplorer:
    """Explorador de arquivos com Rich"""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
    
    def listar_diretorio(self, caminho: Optional[Path] = None) -> List[Path]:
        """Lista arquivos de um diretório"""
        if caminho is None:
            caminho = self.base_path
        
        try:
            items = sorted(caminho.iterdir(), key=lambda x: (not x.is_dir(), x.name))
            return items
        except Exception as e:
            console.print(f"[red]Erro ao listar: {e}[/red]")
            return []
    
    def mostrar_tree(self, caminho: Optional[Path] = None, max_depth: int = 2):
        """Mostra árvore de diretórios"""
        if caminho is None:
            caminho = self.base_path
        
        tree = Tree(f"📁 [bold cyan]{caminho.name}[/bold cyan]")
        self._build_tree(tree, caminho, 0, max_depth)
        console.print(tree)
    
    def _build_tree(self, tree, path: Path, depth: int, max_depth: int):
        """Constrói árvore recursivamente"""
        if depth >= max_depth:
            return
        
        try:
            items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
            
            for item in items:
                if item.name.startswith('.'):
                    continue
                
                if item.is_dir():
                    branch = tree.add(f"📁 [cyan]{item.name}[/cyan]")
                    self._build_tree(branch, item, depth + 1, max_depth)
                else:
                    icon = self._get_file_icon(item.suffix)
                    tree.add(f"{icon} [green]{item.name}[/green]")
        except PermissionError:
            tree.add("[red]⛔ Acesso negado[/red]")
    
    def _get_file_icon(self, extensao: str) -> str:
        """Retorna ícone baseado na extensão"""
        icons = {
            '.py': '🐍',
            '.sav': '💾',
            '.lst': '📋',
            '.pwf': '⚡',
            '.dat': '📊',
            '.xlsx': '📈',
            '.csv': '📉'
        }
        return icons.get(extensao.lower(), '📄')
    
    def mostrar_tabela(self, caminho: Optional[Path] = None):
        """Mostra arquivos em tabela"""
        if caminho is None:
            caminho = self.base_path
        
        items = self.listar_diretorio(caminho)
        
        table = Table(title=f"📂 {caminho}", box=box.ROUNDED)
        table.add_column("#", style="cyan", justify="right")
        table.add_column("Tipo", style="blue")
        table.add_column("Nome", style="green")
        table.add_column("Tamanho", style="yellow", justify="right")
        
        for i, item in enumerate(items, 1):
            tipo = "📁 DIR" if item.is_dir() else self._get_file_icon(item.suffix) + " FILE"
            nome = item.name
            
            if item.is_file():
                tamanho = self._format_size(item.stat().st_size)
            else:
                tamanho = "-"
            
            table.add_row(str(i), tipo, nome, tamanho)
        
        console.print(table)
        return items
    
    def _format_size(self, size: int) -> str:
        """Formata tamanho de arquivo"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"


# ============================================================================
# CLASSE CLIMenu (Integração com CLI Launcher)
# ============================================================================
class CLIMenu:
    """Menu CLI integrado com launcher"""
    
    def __init__(self, config: Configuracoes, assistant: C3POGeminiAssistant):
        self.config = config
        self.assistant = assistant
        self.deck_builder = AnaRedeDeckBuilder(assistant)
        self.mouse_tracker = MouseTracker()
        
        # Explorador de arquivos
        self.explorer = FileExplorer(config.caminho_decks_anaRede)
        
        # Casos selecionados
        self.casos_selecionados = {
            'sav': None,
            'diagrama': None,
            'deck': None
        }
    
    def display_header(self):
        """Display welcome header"""
        console.clear()
        banner = """
        ╔═══════════════════════════════════════════════╗
        ║   ⚡ AUTOMAÇÃO SEP - AnaREDE & Organon      ║
        ║   Sistema Elétrico de Potência - ONS         ║
        ║   Integrado com CLI Launcher                 ║
        ╚═══════════════════════════════════════════════╝
        """
        console.print(Panel(banner, style="bold blue"))
    
    def display_menu(self) -> Optional[str]:
        """Display menu principal"""
        menu = Table(box=box.ROUNDED)
        menu.add_column("Opção", style="cyan", justify="center")
        menu.add_column("Descrição", style="white")
        
        opcoes = [
            ("1", "📂 Explorar arquivos (Tree)"),
            ("2", "📋 Selecionar casos/diagramas"),
            ("3", "▶️  Executar automação AnaREDE (anaRedeScript)"),
            ("4", "▶️  Executar automação Organon (OrganonScript)"),
            ("5", "🔄 Executar workflow completo (run_automation)"),
            ("6", "📍 Ver coordenadas cadastradas"),
            ("7", "➕ Adicionar nova coordenada"),
            ("8", "🖱️  Rastrear posição do mouse"),
            ("9", "📍 Diagnosticar posição do mouse (original)"),
            ("s", "💾 Salvar coordenadas"),
            ("l", "📂 Carregar coordenadas"),
            ("v", "🔊 Toggle voz"),
            ("0", "🚪 Sair")
        ]
        
        for num, desc in opcoes:
            menu.add_row(num, desc)
        
        console.print(menu)
        
        escolha = Prompt.ask(
            "\n[bold yellow]Escolha uma opção[/bold yellow]",
            choices=[o[0] for o in opcoes]
        )
        
        return escolha
    
    def explorar_arquivos(self):
        """Explora estrutura de arquivos - LIMPA TELA A CADA VEZ"""
        console.clear()
        console.print("[bold cyan]📂 Estrutura de Diretórios[/bold cyan]\n")
        
        self.explorer.mostrar_tree(max_depth=3)
        
        console.print()  # Espaço
        
        if Confirm.ask("\nMostrar detalhes em tabela?"):
            console.clear()  # Limpar antes da tabela
            console.print("[bold cyan]📂 Arquivos Detalhados[/bold cyan]\n")
            self.explorer.mostrar_tabela()
        
        Prompt.ask("\n[dim]Pressione Enter para voltar[/dim]")
    
    def _selecionar_arquivo_deck(self, current_path: Path) -> Optional[Path]:
        """Permite a seleção de arquivos .PWF ou .DAT dentro de um diretório, navegando por subdiretórios."""
        
        while True:
            console.print(f"\n[cyan]📂 Caminho atual: {current_path}[/cyan]")
            items = self.explorer.mostrar_tabela(current_path)

            if not items:
                console.print(f"[yellow]⚠️ Nenhum item encontrado em {current_path}[/yellow]")
                return None
            
            escolha = Prompt.ask("Selecione um item (número), '..' para voltar, ou Enter para pular", default="")

            if escolha == "..":
                if current_path == Path(self.config.caminho_decks_anaRede):
                    console.print("[yellow]Você já está no diretório raiz dos decks.[/yellow]")
                else:
                    return None # Isso sinaliza para a chamada anterior que deve voltar
            elif escolha.isdigit():
                idx = int(escolha) - 1
                if 0 <= idx < len(items):
                    item_selecionado = items[idx]
                    
                    if item_selecionado.is_dir():
                        # Entrar no subdiretório
                        selected_file = self._selecionar_arquivo_deck(item_selecionado)
                        if selected_file:
                            return selected_file # Retorna o arquivo se selecionado em subdiretório
                        # Se selected_file for None, significa que o usuário voltou do subdiretório, então continua no loop atual
                    elif item_selecionado.suffix.lower() in ['.pwf', '.dat']:
                        return item_selecionado
                    else:
                        console.print("[red]Tipo de arquivo inválido. Selecione um diretório ou um arquivo .PWF/.DAT.[/red]")
                else:
                    console.print("[red]Número inválido.[/red]")
            elif not escolha: # Usuário pulou a seleção
                return None
            else:
                console.print("[red]Opção inválida.[/red]")

    def selecionar_casos(self):
        """Seleção interativa de casos"""
        console.clear()
        console.print("[bold cyan]📋 Seleção de Casos/Diagramas[/bold cyan]\n")
        
        base = Path(self.config.caminho_decks_anaRede)
        
        dirs = {
            'sav': base / 'Sav',
            'diagrama': base / 'diagramas',
            'deck': base / 'decks'
        }
        
        for tipo, dir_path in dirs.items():
            if not dir_path.exists():
                console.print(f"[yellow]⚠️  Diretório {tipo} não encontrado: {dir_path}[/yellow]")
                continue
            
            console.print(f"\n[cyan]═══ {tipo.upper()} ═══[/cyan]")
            
            if tipo == 'deck':
                deck_file = self._selecionar_arquivo_deck(dir_path)
                if deck_file:
                    self.casos_selecionados['deck'] = deck_file
                    console.print(f"✓ Selecionado: [green]{deck_file.name}[/green]")
                else:
                    console.print("[yellow]Pular seleção de deck.[/yellow]")
            else:
                items = self.explorer.mostrar_tabela(dir_path)
                
                if items:
                    idx = Prompt.ask(
                        f"Selecione {tipo} (número) ou [dim]Enter para pular[/dim]",
                        default=""
                    )
                    
                    if idx.isdigit():
                        idx = int(idx) - 1
                        if 0 <= idx < len(items):
                            self.casos_selecionados[tipo] = items[idx]
                            console.print(f"[green]✓ Selecionado: {items[idx].name}[/green]")
        
        # Mostrar resumo
        console.print("\n[bold]📊 Casos Selecionados:[/bold]")
        for tipo, arquivo in self.casos_selecionados.items():
            if arquivo:
                console.print(f"  {tipo}: [green]{arquivo.name}[/green]")
            else:
                console.print(f"  {tipo}: [dim]não selecionado[/dim]")
        
        Prompt.ask("\n[dim]Pressione Enter para voltar[/dim]")
    
    def menu_loop(self):
        """Loop principal do menu"""
        while True:
            self.display_header()
            escolha = self.display_menu()
            
            if escolha == "1":
                self.explorar_arquivos()
            
            elif escolha == "2":
                self.selecionar_casos()
            
            elif escolha == "3":
                self.executar_anarede_script()
            
            elif escolha == "4":
                self.executar_organon_script()
            
            elif escolha == "5":
                self.run_automation()
            
            elif escolha == "6":
                console.clear()
                self.deck_builder.mostrar_coordenadas()
                Prompt.ask("\n[dim]Pressione Enter para continuar[/dim]")
            
            elif escolha == "7":
                self.adicionar_coordenada_interativa()
            
            elif escolha == "8":
                console.clear()
                duracao = int(Prompt.ask("Duração do rastreamento (segundos)", default="10"))
                self.mouse_tracker.start_tracking(duration=duracao)
                Prompt.ask("\n[dim]Pressione Enter para continuar[/dim]")
            
            elif escolha == "9":
                self.deck_builder.diagnosticar_posicao_mouse()
                Prompt.ask("\n[dim]Pressione Enter para continuar[/dim]")
            
            elif escolha == "s":
                console.clear()
                arquivo = Prompt.ask("Nome do arquivo", default="coordenadas.json")
                self.deck_builder.salvar_coordenadas(arquivo)
                Prompt.ask("\n[dim]Pressione Enter para continuar[/dim]")
            
            elif escolha == "l":
                console.clear()
                arquivo = Prompt.ask("Nome do arquivo", default="coordenadas.json")
                self.deck_builder.carregar_coordenadas(arquivo)
                Prompt.ask("\n[dim]Pressione Enter para continuar[/dim]")
            
            elif escolha == "v":
                self.assistant.voice_enabled = not self.assistant.voice_enabled
                status = "ativada" if self.assistant.voice_enabled else "desativada"
                console.print(f"[yellow]Voz {status}[/yellow]")
                time.sleep(1)
            
            elif escolha == "0":
                if Confirm.ask("Deseja realmente sair?"):
                    console.print("[yellow]Até logo! ⚡[/yellow]")
                    break
    
    def adicionar_coordenada_interativa(self):
        """Adiciona coordenada interativamente"""
        console.clear()
        console.print("[bold cyan]➕ Adicionar Nova Coordenada[/bold cyan]\n")
        
        label = Prompt.ask("Label (snake_case, ex: botao_salvar)")
        
        console.print(f"\n[yellow]Posicione o mouse e aguarde 3 segundos...[/yellow]")
        time.sleep(3)
        
        x, y = pyautogui.position()
        
        self.deck_builder.adicionar_coordenada(label, x, y)
        
        if Confirm.ask("\nSalvar coordenadas agora?", default=True):
            self.deck_builder.salvar_coordenadas()
        
        Prompt.ask("\n[dim]Pressione Enter para continuar[/dim]")
    
    def executar_anarede_script(self):
        """Executa anaRedeScript original"""
        console.clear()
        console.print("[bold cyan]⚡ Executando anaRedeScript[/bold cyan]\n")
        
        if not self.casos_selecionados['sav']:
            console.print("[red]❌ Nenhum arquivo .SAV selecionado![/red]")
            console.print("[yellow]Use a opção 2 para selecionar um caso[/yellow]")
            Prompt.ask("[dim]Pressione Enter[/dim]")
            return
        
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Iniciando...", total=3)
            
            progress.update(task, description="Abrindo AnaREDE...")
            anaRedeScript(self.assistant, self.deck_builder, self.casos_selecionados)
            progress.advance(task)
        
        console.print("\n[green]✅ anaRedeScript concluído![/green]")
        Prompt.ask("[dim]Pressione Enter[/dim]")
    
    def executar_organon_script(self):
        """Executa OrganonScript original"""
        console.clear()
        console.print("[bold cyan]📊 Executando OrganonScript[/bold cyan]\n")
        
        if not self.casos_selecionados['diagrama']:
            console.print("[red]❌ Nenhum diagrama selecionado![/red]")
            console.print("[yellow]Use a opção 2 para selecionar um diagrama[/yellow]")
            Prompt.ask("[dim]Pressione Enter[/dim]")
            return
        
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Iniciando...", total=2)
            
            progress.update(task, description="Abrindo Organon...")
            OrganonScript(self.assistant, self.deck_builder, self.casos_selecionados)
            progress.advance(task)
        
        console.print("\n[green]✅ OrganonScript concluído![/green]")
        Prompt.ask("[dim]Pressione Enter[/dim]")
    
    def run_automation(self):
        """Executa run_automation original completo"""
        console.clear()
        console.print("[bold cyan]🔄 Executando Workflow Completo[/bold cyan]\n")
        
        run_automation(self.assistant, self.deck_builder, self.casos_selecionados)
        
        console.print("\n[green]✅ Workflow completo finalizado![/green]")
        Prompt.ask("[dim]Pressione Enter[/dim]")


# ============================================================================
# FUNÇÕES ORIGINAIS (mantidas exatamente como estavam)
# ============================================================================

casos = {
  'sav': Path(''),
  'diagrama': Path(''),
  'deck': Path('')   # ainda é diretório, depois vira .dat/.pdw/.txt
}



def anaRedeScript(assistant: C3POGeminiAssistant, deck_builder: AnaRedeDeckBuilder, 
                  casos: dict):
    """Script original de automação AnaREDE
    
    Fluxo operacional (engenharia SEP)

    O workflow reflete a realidade do estudo elétrico:

    Seleciona caso (.SAV)

    Seleciona diagrama (.LST)

    Carrega simulador

    Executa ações determinísticas

    Repete para múltiplos cenários

    """
    console.print("[green]🟢 Iniciando script de automação AnaREDE...[/green]")
    
    assistant.abrir_programa("Anarede 12")
    
    if casos['sav']:
        deck_builder.carregar_save_case(str(casos['sav']))
    else:
        console.print("[yellow]⚠️  Nenhum caso .SAV selecionado[/yellow]")


def OrganonScript(assistant: C3POGeminiAssistant, deck_builder: AnaRedeDeckBuilder,
                  casos: dict):
    """Script original de automação Organon"""
    console.print("[green]🟢 Iniciando script de automação Organon...[/green]")
    
    assistant.abrir_programa("Organon")
    
    if casos['diagrama']:
        deck_builder.carregar_diagrama(str(casos['diagrama']))
    else:
        console.print("[yellow]⚠️  Nenhum diagrama selecionado[/yellow]")


def run_automation(assistant: C3POGeminiAssistant, deck_builder: AnaRedeDeckBuilder,
                   casos: dict):
    """Rotina principal original - workflow completo"""
    assistant.falar("Iniciando rotina automática AnaREDE e Organon para análise do caso RSE.")
    
    anaRedeScript(assistant, deck_builder, casos)
    
    # Opcional: adicionar OrganonScript aqui se necessário
    # OrganonScript(assistant, deck_builder, casos)
    
    assistant.falar("Rotina finalizada com sucesso.")
    console.print("[green]✅ Automação concluída.[/green]")



def run_automation_real(assistant: C3POGeminiAssistant,
                        deck_builder: AnaRedeDeckBuilder,
                        casos: dict):
    """
    Rotina REAL de automação AnaREDE
    Usa APENAS código que executa no mundo físico (GUI)
    """

    console.print("[bold green]🟢 Iniciando automação REAL AnaREDE[/bold green]")

    # ===============================
    # 1. Validação dura (sem mentira)
    # ===============================
    if not casos.get('sav'):
        console.print("[red]❌ Nenhum arquivo .SAV selecionado[/red]")
        console.print("[yellow]👉 Use a opção 2 do menu para selecionar o caso[/yellow]")
        return

    sav_path = str(casos['sav'])

    # ===============================
    # 2. Abrir AnaREDE DE VERDADE
    # ===============================
    assistant.falar("Abrindo o AnaREDE")
    assistant.abrir_programa("Anarede 12")

    # Tempo real de carga (SEP não é web app)
    time.sleep(8)

    # Forçar foco da janela
    pyautogui.click(200, 200)
    time.sleep(1)

    console.print("[green]✓ AnaREDE aberto e em foco[/green]")

    # ===============================
    # 3. Carregar caso .SAV
    # ===============================
    console.print(f"[cyan]📂 Carregando caso: {os.path.basename(sav_path)}[/cyan]")
    deck_builder.carregar_save_case(sav_path)

    # ===============================
    # 4. (Opcional) Executar fluxo
    # ===============================
    assistant.falar("Executando fluxo de potência")
    deck_builder.executar_fluxo()

    # ===============================
    # 5. Finalização honesta
    # ===============================
    assistant.falar("Automação concluída com sucesso")
    console.print("[bold green]✅ Automação REAL finalizada[/bold green]")


# ============================================================================
# FUNÇÃO MAIN
# ============================================================================

def main():
    """Função principal - inicialização do sistema"""
    try:
        # Banner inicial
        console.print("\n[bold green]Iniciando Sistema de Automação SEP...[/bold green]\n")
        
        # Inicializar componentes
        config = Configuracoes()
        assistant = C3POGeminiAssistant()
        
        # Verificar caminho base
        base_path = Path(config.caminho_decks_anaRede)
        if not base_path.exists():
            console.print(f"[red]❌ Caminho não encontrado: {base_path}[/red]")
            console.print("[yellow]Ajuste o caminho_decks_anaRede na classe Configuracoes[/yellow]")
            return
        
        console.print(f"[cyan]Caminho base: {base_path}[/cyan]")
        console.print("[green]✓ Sistema pronto![/green]\n")
        
        time.sleep(2)
        
        # Iniciar CLI
        cli = CLIMenu(config, assistant)
        cli.menu_loop()
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Programa interrompido pelo usuário[/yellow]")
    
    except Exception as e:
        console.print(f"\n[red]Erro fatal: {e}[/red]")
        import traceback
        console.print(traceback.format_exc())


if __name__ == "__main__":
    main()