import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

class PlotFluxoPotencia:
    def __init__(self, df_barras):
        """
        Inicializa a classe com os dados das barras.

        Args:
            df_barras (pd.DataFrame): DataFrame com colunas 'x', 'y', 'p_mw', 'q_mvar' e o índice sendo o nome da barra.
        """
        self.df = df_barras

    def plotar_2d(self, ax=None, escala_p=0.1, escala_q=0.1):
        """
        Plota os vetores de potência ativa (P) e reativa (Q) em 2D.

        Args:
            ax (matplotlib.axes.Axes, optional): Eixos para plotar. Se None, cria novos eixos.
            escala_p (float): Fator de escala para os vetores de potência ativa.
            escala_q (float): Fator de escala para os vetores de potência reativa.
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 8))
            ax.set_title("Fluxo de Potência (P e Q)")
            ax.set_xlabel("Coordenada X")
            ax.set_ylabel("Coordenada Y")

        x = self.df['x']
        y = self.df['y']
        p = self.df['p_mw']
        q = self.df['q_mvar']
        nomes = self.df.index

        ax.quiver(x, y, p * escala_p, np.zeros_like(q), color='r', angles='xy', scale_units='xy', scale=1, label='Potência Ativa (P)')
        ax.quiver(x, y, np.zeros_like(p), q * escala_q, color='b', angles='xy', scale_units='xy', scale=1, label='Potência Reativa (Q)')

        for i, nome in enumerate(nomes):
            ax.annotate(nome, (x.iloc[i], y.iloc[i]), textcoords="offset points", xytext=(5,5), ha='left')

        ax.scatter(x, y, color='k', marker='o', label='Barras')
        ax.legend()
        ax.grid(True)
        return ax

    def plotar_magnitude(self, ax=None, escala=0.1):
        """
        Plota vetores cuja magnitude representa a potência aparente (S).

        Args:
            ax (matplotlib.axes.Axes, optional): Eixos para plotar. Se None, cria novos eixos.
            escala (float): Fator de escala para os vetores de potência aparente.
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 8))
            ax.set_title("Magnitude da Potência Aparente (S)")
            ax.set_xlabel("Coordenada X")
            ax.set_ylabel("Coordenada Y")

        x = self.df['x']
        y = self.df['y']
        p = self.df['p_mw']
        q = self.df['q_mvar']
        s_complexo = p + 1j * q
        magnitudes_s = np.abs(s_complexo)
        angulos_s = np.angle(s_complexo)
        nomes = self.df.index

        ax.quiver(x, y, magnitudes_s * np.cos(angulos_s) * escala, magnitudes_s * np.sin(angulos_s) * escala,
                  angles='xy', scale_units='xy', scale=1, label='Potência Aparente (S)', color='g')

        for i, nome in enumerate(nomes):
            ax.annotate(nome, (x.iloc[i], y.iloc[i]), textcoords="offset points", xytext=(5,5), ha='left')

        ax.scatter(x, y, color='k', marker='o', label='Barras')
        ax.legend()
        ax.grid(True)
        return ax

# Criando um DataFrame com índice nomeado
barras_data = {
    "x": [1, 2, 3, 4, 5],
    "y": [1, 2, 3, 4, 5],
    "p_mw": [10, 20, 30, 40, 50],  # Valores mais altos para melhor visualização
    "q_mvar": [5, 10, 15, 20, 25]   # Valores mais altos para melhor visualização
}
df_barras = pd.DataFrame(
    barras_data,
    index=["barra1", "barra2", "barra3", "barra4", "barra5"]
)

# Exemplo de uso:
plotador = PlotFluxoPotencia(df_barras.copy()) # Passe uma cópia para não modificar o original

# Plotando em 2D (vetores de P e Q separados)
fig_2d, ax_2d = plt.subplots(figsize=(12, 10))
plotador.plotar_2d(ax=ax_2d, escala_p=0.05, escala_q=0.05)
plt.show()

# Plotando a magnitude da potência aparente (S)
fig_mag, ax_mag = plt.subplots(figsize=(12, 10))
plotador.plotar_magnitude(ax=ax_mag, escala=0.02)
plt.show()