
# -*- coding: utf-8 -*-
"""
Ferramenta de Visualização de Fluxo de Potência para Análise de Sistemas Elétricos.

Este script é uma ferramenta de visualização para análise de sistemas de potência,
inspirado pela necessidade de apresentar resultados claros em trabalhos acadêmicos,
como a tese de doutorado sobre agendamento de intervenções que você compartilhou.

Ele é projetado para pegar os resultados de uma simulação de fluxo de potência,
que pode ser gerada por ferramentas como o Pandapower (visto no seu código do GitHub),
e criar visualizações vetoriais da potência ativa (P) e reativa (Q) em cada barra.

A ideia é transformar dados numéricos de uma simulação em uma "história" visual
para o seu artigo, mostrando de forma intuitiva onde estão as principais cargas e
geradores do seu sistema de teste.

"""

import os
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib

# Use backend sem interface gráfica em ambientes sem display (headless)
_HEADLESS = not os.environ.get("DISPLAY") and os.name != "nt"
if _HEADLESS:
    matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

# -----------------------------------------------------------------------------
# DADOS DO SISTEMA DE 16 BARRAS (POPULAÇÃO DO ALGORITMO GENÉTICO)
# -----------------------------------------------------------------------------
# Esta seção define o nosso sistema de teste.
# A nomeação das barras com aves brasileiras é uma forma criativa de
# identificar os "indivíduos" da população para um Algoritmo Genético (AG),
# tornando o estudo mais único para o seu artigo.

def criar_sistema_de_teste():
    """Cria um DataFrame do Pandas com dados fictícios para um sistema de 16 barras."""
    
    # Nomes de 16 aves brasileiras famosas
    nomes_barras = [
        "Arara-Azul", "Tucano", "Beija-Flor", "Canário-da-Terra",
        "Pato-Selvagem", "Garça", "Martim-Pescador", "Ema",
        "Falcão", "Coruja", "Andorinha", "Pica-Pau",
        "Sabiá-Laranjeira", "João-de-Barro", "Bem-te-vi", "Urubu-Rei"
    ]

    # Coordenadas (x, y) fictícias para a disposição geográfica das barras
    coordenadas = {
        "Arara-Azul": (1, 5), "Tucano": (2, 6), "Beija-Flor": (3, 5), "Canário-da-Terra": (2, 4),
        "Pato-Selvagem": (5, 7), "Garça": (6, 6), "Martim-Pescador": (7, 7), "Ema": (6, 5),
        "Falcão": (8, 4), "Coruja": (9, 5), "Andorinha": (8, 3), "Pica-Pau": (9, 3),
        "Sabiá-Laranjeira": (4, 2), "João-de-Barro": (5, 3), "Bem-te-vi": (6, 2), "Urubu-Rei": (7, 1)
    }

    # Potência ativa (P) e reativa (Q) fictícias (em MW e MVAr)
    # Sinal negativo indica carga, positivo indica geração.
    np.random.seed(42)  # Garante que os valores aleatórios sejam sempre os mesmos
    potencias = {
        nome: (np.random.uniform(-50, 20), np.random.uniform(-30, 15))
        for nome in nomes_barras
    }

    # Organizando tudo em um DataFrame do Pandas
    df_barras = pd.DataFrame(index=nomes_barras)
    df_barras['x'] = [coordenadas.get(nome)[0] for nome in nomes_barras]
    df_barras['y'] = [coordenadas.get(nome)[1] for nome in nomes_barras]
    df_barras['p_mw'] = [potencias.get(nome)[0] for nome in nomes_barras]
    df_barras['q_mvar'] = [potencias.get(nome)[1] for nome in nomes_barras]
    
    return df_barras

def criar_template_excel(caminho_excel: str, df_barras: pd.DataFrame, linhas: list[tuple]):
    """
    Cria um arquivo Excel (template) com múltiplas planilhas para entrada de dados.

    Sheets:
      - 'barras': colunas [nome, x, y, p_mw, q_mvar]
      - 'linhas': colunas [from, to] usando nomes das barras

    Args:
        caminho_excel: caminho .xlsx a ser criado.
        df_barras: DataFrame de barras com índice=nome e colunas x,y,p_mw,q_mvar.
        linhas: lista de tuplas de conexões (por nome) entre barras.
    """
    # Garante diretório
    Path(os.path.dirname(caminho_excel)).mkdir(parents=True, exist_ok=True)

    # Monta DF de barras com índice como coluna 'nome'
    df_b = df_barras.reset_index().rename(columns={df_barras.index.name or 'index': 'nome'})
    if 'nome' not in df_b.columns:
        df_b = df_b.rename(columns={df_b.columns[0]: 'nome'})
    df_b = df_b[['nome', 'x', 'y', 'p_mw', 'q_mvar']]

    # Monta DF de linhas
    df_l = pd.DataFrame(linhas, columns=['from', 'to'])

    with pd.ExcelWriter(caminho_excel, engine='openpyxl') as writer:
        df_b.to_excel(writer, sheet_name='barras', index=False)
        df_l.to_excel(writer, sheet_name='linhas', index=False)

def carregar_sistema_de_excel(caminho_excel: str) -> tuple[pd.DataFrame, list[tuple]]:
    """
    Carrega os dados do sistema a partir de um Excel com múltiplas sheets.

    Espera-se:
      - Sheet 'barras' com colunas: nome, x, y, p_mw, q_mvar
      - Sheet 'linhas' com colunas: from, to (nomes das barras)

    Retorna:
      (df_barras, linhas)
        df_barras: índice=nome, colunas [x,y,p_mw,q_mvar]
        linhas: lista de tuplas (from_name, to_name)
    """
    try:
        sheets = pd.read_excel(caminho_excel, sheet_name=None, engine='openpyxl')
    except ImportError as e:
        raise ImportError("Pacote 'openpyxl' é necessário para ler o Excel. Instale com: pip install openpyxl") from e

    if 'barras' not in sheets:
        raise ValueError("Excel não contém a sheet obrigatória 'barras'.")
    if 'linhas' not in sheets:
        raise ValueError("Excel não contém a sheet obrigatória 'linhas'.")

    df_b = sheets['barras'].copy()
    obrig_b = {'nome', 'x', 'y', 'p_mw', 'q_mvar'}
    if not obrig_b.issubset(set(df_b.columns)):
        raise ValueError(f"Sheet 'barras' deve conter as colunas: {sorted(obrig_b)}")
    df_barras = df_b[['nome', 'x', 'y', 'p_mw', 'q_mvar']].copy()
    df_barras = df_barras.set_index('nome')

    df_l = sheets['linhas'].copy()
    obrig_l = {'from', 'to'}
    if not obrig_l.issubset(set(df_l.columns)):
        raise ValueError("Sheet 'linhas' deve conter as colunas: ['from','to']")
    linhas = list(df_l[['from', 'to']].itertuples(index=False, name=None))

    return df_barras, linhas

# -----------------------------------------------------------------------------
# CLASSE DE VISUALIZAÇÃO EM MATPLOTLIB
# -----------------------------------------------------------------------------
# Esta classe encapsula toda a lógica de plotagem. Ela recebe os dados do sistema
# e oferece métodos para criar os gráficos, tornando o código principal mais limpo.

class VisualizadorFluxoPotencia:
    """
    Classe para criar visualizações de fluxo de potência a partir de dados de barras.
    """
    def __init__(self, df_barras):
        """
        Inicializa o visualizador com os dados das barras.

        Args:
            df_barras (pd.DataFrame): DataFrame com colunas 'x', 'y', 'p_mw', 'q_mvar' 
                                      e o índice sendo o nome da barra.
        """
        if not all(col in df_barras.columns for col in ['x', 'y', 'p_mw', 'q_mvar']):
            raise ValueError("O DataFrame precisa conter as colunas 'x', 'y', 'p_mw', 'q_mvar'.")
        self.df = df_barras

    def plotar_rede_collections(self, linhas, ax=None, titulo="Rede Elétrica (Collections)",
                                largura_linha=2.0):
        """
        Plota a rede (barras e linhas) usando matplotlib.collections.

        Args:
            linhas (list[tuple]): lista de tuplas representando conexões entre barras.
                Cada tupla pode conter índices do DataFrame ou nomes das barras.
                Ex.: [("Arara-Azul", "Tucano"), (0, 1), ("Tucano", "Beija-Flor")]
            ax (matplotlib.axes.Axes, optional): Eixos alvo.
            titulo (str): Título do gráfico.
            largura_linha (float): largura das linhas da rede.
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=(12, 10))

        ax.set_title(titulo, fontsize=16)
        ax.set_xlabel("Coordenada Geográfica X", fontsize=12)
        ax.set_ylabel("Coordenada Geográfica Y", fontsize=12)

        # Dados base
        x = self.df['x'].to_numpy()
        y = self.df['y'].to_numpy()
        nomes = list(self.df.index)
        nome_para_idx = {n: i for i, n in enumerate(nomes)}

        # Determina cores das barras: geração (P>0) verde, carga (P<0) laranja, neutro azul
        p = self.df['p_mw'].to_numpy()
        cores_barras = [
            ('green' if val > 0 else ('orange' if val < 0 else 'blue'))
            for val in p
        ]

        # Monta segmentos das linhas a partir das conexões
        segmentos = []
        for a, b in linhas:
            ia = nome_para_idx.get(a, a) if isinstance(a, str) else a
            ib = nome_para_idx.get(b, b) if isinstance(b, str) else b
            if 0 <= ia < len(x) and 0 <= ib < len(x):
                segmentos.append([(x[ia], y[ia]), (x[ib], y[ib])])

        # Cor única para linhas por simplicidade; pode evoluir para mapa por tensão/carga
        lc = LineCollection(segmentos, colors='steelblue', linewidths=largura_linha, zorder=5)
        ax.add_collection(lc)

        # Desenha barras
        ax.scatter(x, y, s=80, c=cores_barras, edgecolors='k', zorder=10, label='Barras')
        for i, nome in enumerate(nomes):
            ax.text(x[i] + 0.08, y[i] + 0.08, nome, fontsize=9, ha='left', zorder=12)

        # Legenda customizada simples
        from matplotlib.lines import Line2D
        legenda_elems = [
            Line2D([0], [0], color='steelblue', lw=2, label='Linhas'),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='green', markeredgecolor='k', label='Barra com Geração (P>0)', markersize=8),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='orange', markeredgecolor='k', label='Barra com Carga (P<0)', markersize=8),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='blue', markeredgecolor='k', label='Barra Neutra (P≈0)', markersize=8),
        ]
        ax.legend(handles=legenda_elems)

        ax.grid(True, linestyle='--', alpha=0.6)
        ax.set_aspect('equal', adjustable='box')
        return ax

    def plotar_vetores_pq(self, ax=None, escala=0.05, titulo="Fluxo de Potência (P e Q)"):
        """
        Plota vetores separados para potência ativa (P) e reativa (Q) em 2D.

        Args:
            ax (matplotlib.axes.Axes, optional): Eixos para plotar. Se None, cria uma nova figura.
            escala (float): Fator de escala para o tamanho dos vetores.
            titulo (str): Título do gráfico.
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=(12, 10))
        
        ax.set_title(titulo, fontsize=16)
        ax.set_xlabel("Coordenada Geográfica X", fontsize=12)
        ax.set_ylabel("Coordenada Geográfica Y", fontsize=12)

        # Dados (como arrays numpy para garantir dimensões compatíveis no quiver)
        x = self.df['x'].to_numpy()
        y = self.df['y'].to_numpy()
        p = self.df['p_mw'].to_numpy()
        q = self.df['q_mvar'].to_numpy()
        nomes = self.df.index

        # Componentes de vetores separados para P e Q
        u_p = p
        v_p = np.zeros_like(p)
        u_q = np.zeros_like(q)
        v_q = q

        # Plotando os vetores (setas)
        ax.quiver(x, y, u_p, v_p, color='red', angles='xy', scale_units='xy', scale=1/escala, label='Potência Ativa (P)')
        ax.quiver(x, y, u_q, v_q, color='blue', angles='xy', scale_units='xy', scale=1/escala, label='Potência Reativa (Q)')

        # Plotando as barras e seus nomes
        ax.plot(x, y, 'ko', markersize=8, label='Barras do Sistema')
        for i, nome in enumerate(nomes):
            ax.text(x[i] + 0.1, y[i] + 0.1, nome, fontsize=9, ha='left')

        ax.legend()
        ax.grid(True, linestyle='--', alpha=0.6)
        ax.set_aspect('equal', adjustable='box')
        return ax

    def plotar_vetores_s(self, ax=None, escala=0.02, titulo="Vetor da Potência Aparente (S)"):
        """
        Plota um único vetor para a potência aparente (S) em cada barra.

        Args:
            ax (matplotlib.axes.Axes, optional): Eixos para plotar. Se None, cria uma nova figura.
            escala (float): Fator de escala para o tamanho dos vetores.
            titulo (str): Título do gráfico.
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=(12, 10))

        ax.set_title(titulo, fontsize=16)
        ax.set_xlabel("Coordenada Geográfica X", fontsize=12)
        ax.set_ylabel("Coordenada Geográfica Y", fontsize=12)

        # Dados (como arrays numpy para garantir dimensões compatíveis no quiver)
        x = self.df['x'].to_numpy()
        y = self.df['y'].to_numpy()
        p = self.df['p_mw'].to_numpy()
        q = self.df['q_mvar'].to_numpy()
        nomes = self.df.index

        # Plotando os vetores (setas) da potência aparente S = P + jQ
        ax.quiver(x, y, p, q, color='green', angles='xy', scale_units='xy', scale=1/escala, label='Potência Aparente (S)')
        
        # Plotando as barras e seus nomes
        ax.plot(x, y, 'ko', markersize=8, label='Barras do Sistema')
        for i, nome in enumerate(nomes):
            ax.text(x[i] + 0.1, y[i] + 0.1, nome, fontsize=9, ha='left')

        ax.legend()
        ax.grid(True, linestyle='--', alpha=0.6)
        ax.set_aspect('equal', adjustable='box')
        return ax

# -----------------------------------------------------------------------------
# EXECUÇÃO PRINCIPAL DO SCRIPT
# -----------------------------------------------------------------------------
# Esta é a parte "executável" do nosso código.
# É aqui que criamos os dados, instanciamos a classe e chamamos os métodos de plotagem.

if __name__ == "__main__":
    # 1. Gerar os dados do nosso sistema de teste
    dados_sistema_16_barras = criar_sistema_de_teste()
    print("--- Dados do Sistema de Teste (16 Barras) ---")
    print(dados_sistema_16_barras)
    print("-" * 50)
    
    # 2. Criar uma instância da nossa classe de visualização
    visualizador = VisualizadorFluxoPotencia(dados_sistema_16_barras)
    
    # 3. Gerar e exibir os gráficos

    # 3.1. Carregar dados de Excel (se existir), senão criar template com exemplos
    pasta_input = os.path.join(os.path.dirname(__file__), "input")
    os.makedirs(pasta_input, exist_ok=True)
    caminho_excel = os.path.join(pasta_input, "sistema_16barras.xlsx")

    linhas_exemplo = None
    if os.path.exists(caminho_excel):
        try:
            dados_sistema_16_barras, linhas_exemplo = carregar_sistema_de_excel(caminho_excel)
            print(f"Dados carregados de: {caminho_excel}")
        except Exception as e:
            print(f"Falha ao carregar Excel: {e}. Usando dados fictícios e gerando template novo.")
    
    if linhas_exemplo is None:
        # Topologia exemplo caso não exista Excel válido
        linhas_exemplo = [
            ("Arara-Azul", "Tucano"), ("Tucano", "Beija-Flor"), ("Beija-Flor", "Canário-da-Terra"),
            ("Canário-da-Terra", "João-de-Barro"), ("João-de-Barro", "Sabiá-Laranjeira"), ("Sabiá-Laranjeira", "Pato-Selvagem"),
            ("Pato-Selvagem", "Garça"), ("Garça", "Martim-Pescador"), ("Martim-Pescador", "Ema"),
            ("Ema", "Falcão"), ("Falcão", "Coruja"), ("Coruja", "Pica-Pau"),
            ("Pica-Pau", "Andorinha"), ("Andorinha", "Bem-te-vi"), ("Bem-te-vi", "Urubu-Rei"),
            ("Urubu-Rei", "Falcão")
        ]
        # Gerar template a partir dos dados atuais
        try:
            criar_template_excel(caminho_excel, dados_sistema_16_barras, linhas_exemplo)
            print(f"Template Excel criado em: {caminho_excel}")
        except Exception as e:
            print(f"Falha ao criar template Excel: {e}")

    # Figura da rede com collections
    fig0, ax0 = plt.subplots(figsize=(14, 12))
    visualizador.plotar_rede_collections(linhas_exemplo, ax=ax0)
    plt.tight_layout()
    
    # Gráfico 1: Vetores de P e Q separados
    fig1, ax1 = plt.subplots(figsize=(14, 12))
    visualizador.plotar_vetores_pq(ax=ax1)
    plt.tight_layout()
    
    # Gráfico 2: Vetor único para a Potência Aparente S
    fig2, ax2 = plt.subplots(figsize=(14, 12))
    visualizador.plotar_vetores_s(ax=ax2)
    plt.tight_layout()

    # Salvar sempre as figuras em arquivo para garantir funcionamento em qualquer ambiente
    saida_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(saida_dir, exist_ok=True)
    caminho_fig0 = os.path.join(saida_dir, "rede_collections_16barras.png")
    caminho_fig1 = os.path.join(saida_dir, "fluxo_pq_16barras.png")
    caminho_fig2 = os.path.join(saida_dir, "fluxo_s_16barras.png")
    fig0.savefig(caminho_fig0, dpi=200, bbox_inches="tight")
    fig1.savefig(caminho_fig1, dpi=200, bbox_inches="tight")
    fig2.savefig(caminho_fig2, dpi=200, bbox_inches="tight")
    print(f"Figuras salvas em:\n - {caminho_fig0}\n - {caminho_fig1}\n - {caminho_fig2}")

    # Exibir na tela apenas se houver display disponível
    if not _HEADLESS:
        plt.show()
    else:
        plt.close(fig0)
        plt.close(fig1)
        plt.close(fig2)
