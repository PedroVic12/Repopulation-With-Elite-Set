# create_your_new_network.py

```python

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
import pandas as pd
import numpy as np
import matplotlib

# Use backend sem interface gráfica em ambientes sem display (headless)
_HEADLESS = not os.environ.get("DISPLAY") and os.name != "nt"
if _HEADLESS:
    matplotlib.use("Agg")

import matplotlib.pyplot as plt

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
    # IMPORTANTE: Estes dados devem ser substituídos pelos resultados da sua simulação no Pandapower.
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
    caminho_fig1 = os.path.join(saida_dir, "fluxo_pq_16barras.png")
    caminho_fig2 = os.path.join(saida_dir, "fluxo_s_16barras.png")
    fig1.savefig(caminho_fig1, dpi=200, bbox_inches="tight")
    fig2.savefig(caminho_fig2, dpi=200, bbox_inches="tight")
    print(f"Figuras salvas em:\n - {caminho_fig1}\n - {caminho_fig2}")

    # Exibir na tela apenas se houver display disponível
    if not _HEADLESS:
        plt.show()
    else:
        plt.close(fig1)
        plt.close(fig2)

```