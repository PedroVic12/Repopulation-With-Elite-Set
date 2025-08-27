# -*- coding: utf-8 -*-
"""
Ferramenta de Análise e Visualização para Redes Elétricas Inteligentes (Smart Grids)

Este script consolida a simulação de redes elétricas usando Pandapower e a 
geração de uma sequência de 7 visualizações para compor o capítulo de resultados
de um artigo científico.

A narrativa visual segue a estrutura de "início, meio e fim":
1.  **Início:** Apresentação do estado base da rede.
2.  **Meio:** Introdução de uma contingência (problema) e seus impactos.
3.  **Fim:** Comparação dos resultados e demonstração da análise.

Autor: Pedro Victor 
Data: 17/08/2025
"""

#----
# Métodos de ML para rede elétrica com dados de entrada em .xlsx ter 2 váriaveis alvo para treinamento do modelo para uma Rede Autônoma
#----




# --- Importações Essenciais ---
import pandapower as pp
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# --- Classe Principal da SmartGrid ---
class SmartGrid:
    """
    Classe que encapsula a lógica de simulação e visualização de uma rede elétrica.
    """
    def __init__(self, network_name="canarinho"):
        """
        Inicializa a classe, carregando ou criando a rede elétrica desejada.
        """
        self.net = self._carregar_rede(network_name)
        self.nome_rede = network_name
        self.resultados_base = None
        self.resultados_contingencia = None

    def _carregar_rede(self, network_name):
        """
        Método interno para carregar redes do pandapower ou criar a rede customizada.
        """
        if network_name == "canarinho":
            print("Criando a rede customizada 'Canarinho' de 16 barras...")
            return self._criar_rede_canarinho()
        elif network_name == "case14":
            print("Carregando a rede 'case14' do pandapower...")
            return pp.networks.case14()
        else:
            print(f"Rede '{network_name}' não reconhecida. Carregando 'case14' por padrão.")
            return pp.networks.case14()

    def _criar_rede_canarinho(self):
        """
        Cria a rede fictícia "Canarinho" de 16 barras para o artigo.
        """
        net = pp.create_empty_network()

        # Nomes das barras (aves brasileiras)
        nomes_barras = [
            "Arara-Azul", "Tucano", "Beija-Flor", "Canário", "Pato-Selvagem", "Garça",
            "Martim-Pescador", "Ema", "Falcão", "Coruja", "Andorinha", "Pica-Pau",
            "Sabiá", "João-de-Barro", "Bem-te-vi", "Urubu-Rei"
        ]
        
        # Coordenadas geográficas para plotagem
        coords = [(1,5),(2,6),(3,5),(2,4),(5,7),(6,6),(7,7),(6,5),(8,4),(9,5),(8,3),(9,3),(4,2),(5,3),(6,2),(7,1)]

        # Criando os barramentos
        for i, nome in enumerate(nomes_barras):
            pp.create_bus(net, vn_kv=20., name=nome)

        # Assign geodata after all buses are created
        net.bus_geodata = pd.DataFrame(coords, index=net.bus.index, columns=['x', 'y'])

        # Criando linhas (exemplo de topologia)
        pp.create_line(net, from_bus=0, to_bus=1, length_km=1., std_type="NA2XS2Y 1x240 RM/25 12/20 kV")
        pp.create_line(net, from_bus=1, to_bus=2, length_km=1., std_type="NA2XS2Y 1x240 RM/25 12/20 kV")
        pp.create_line(net, from_bus=2, to_bus=3, length_km=1., std_type="NA2XS2Y 1x240 RM/25 12/20 kV")
        pp.create_line(net, from_bus=3, to_bus=0, length_km=1., std_type="NA2XS2Y 1x240 RM/25 12/20 kV")
        pp.create_line(net, from_bus=4, to_bus=5, length_km=1., std_type="NA2XS2Y 1x240 RM/25 12/20 kV")
        pp.create_line(net, from_bus=5, to_bus=6, length_km=1., std_type="NA2XS2Y 1x240 RM/25 12/20 kV")
        pp.create_line(net, from_bus=6, to_bus=7, length_km=1., std_type="NA2XS2Y 1x240 RM/25 12/20 kV")
        pp.create_line(net, from_bus=1, to_bus=4, length_km=2., std_type="NA2XS2Y 1x240 RM/25 12/20 kV")
        # ... adicionar mais linhas para conectar a rede

        # Criando cargas (exemplo)
        pp.create_load(net, bus=3, p_mw=0.1, q_mvar=0.05, name="Carga Canário")
        pp.create_load(net, bus=7, p_mw=0.15, q_mvar=0.08, name="Carga Ema")
        pp.create_load(net, bus=10, p_mw=0.2, q_mvar=0.1, name="Carga Andorinha")

        # Criando geradores (exemplo)
        pp.create_gen(net, bus=0, p_mw=0.5, vm_pu=1.02, name="Gerador Arara-Azul")
        pp.create_ext_grid(net, bus=15, vm_pu=1.03, name="Conexão SIN")
        
        return net

    def rodar_fluxo_de_potencia(self):
        """
        Executa o cálculo de fluxo de potência na rede.
        """
        try:
            pp.runpp(self.net)
            print("Cálculo de fluxo de potência executado com sucesso.")
            return True
        except Exception as e:
            print(f"Erro ao executar o fluxo de potência: {e}")
            return False

    def salvar_resultados(self, nome_cenario):
        """
        Salva uma cópia dos resultados da simulação para um cenário específico.
        """
        resultados = {
            'bus': self.net.res_bus.copy(),
            'line': self.net.res_line.copy(),
            'gen': self.net.res_gen.copy(),
            'load': self.net.res_load.copy()
        }
        if nome_cenario == 'base':
            self.resultados_base = resultados
        elif nome_cenario == 'contingencia':
            self.resultados_contingencia = resultados
        else:
            print(f"Nome de cenário '{nome_cenario}' não reconhecido.")

    def aplicar_contingencia(self, id_linha):
        """
        Simula uma contingência desligando uma linha específica.
        """
        if id_linha in self.net.line.index:
            self.net.line.loc[id_linha, 'in_service'] = False
            print(f"Contingência aplicada: Linha {id_linha} foi desligada.")
        else:
            print(f"Erro: ID de linha {id_linha} não encontrado.")

    def resetar_rede(self):
        """
        Restaura a rede para o estado original, religando todos os elementos.
        """
        self.net.line['in_service'] = True
        print("Rede resetada para o estado original.")

    # --- MÉTODOS DE PLOTAGEM PARA O ARTIGO (7 GRÁFICOS) ---

    def plotar_grafico_1_topologia_rede(self, ax=None):
        """GRÁFICO 1: Mostra a topologia da rede, identificando barras, cargas e geradores."""
        if ax is None:
            fig, ax = plt.subplots(figsize=(12, 10))
        
        ax.set_title("Gráfico 1: Topologia da Rede 'Canarinho' (16 Barras)", fontsize=16)
        
        # Coordenadas
        x = self.net.bus_geodata.x
        y = self.net.bus_geodata.y

        # Plotar linhas
        for _, line in self.net.line.iterrows():
            from_bus = self.net.bus.index[line.from_bus]
            to_bus = self.net.bus.index[line.to_bus]
            ax.plot([x[from_bus], x[to_bus]], [y[from_bus], y[to_bus]], 'b-', alpha=0.7, linewidth=1.5)

        # Plotar barras, cargas e geradores
        ax.plot(x, y, 'ko', markersize=8, label='Barra')
        ax.plot(x[self.net.load.bus], y[self.net.load.bus], 'r^', markersize=10, label='Carga')
        ax.plot(x[self.net.gen.bus], y[self.net.gen.bus], 'gs', markersize=10, label='Gerador')
        ax.plot(x[self.net.ext_grid.bus], y[self.net.ext_grid.bus], 'mP', markersize=12, label='Conexão Externa (SIN)')

        # Nomes das barras
        for i, name in self.net.bus.iterrows():
            ax.text(x.iloc[i] + 0.1, y.iloc[i] + 0.1, name['name'], fontsize=9)
            
        ax.legend()
        ax.grid(True, linestyle='--', alpha=0.5)
        ax.set_xlabel("Coordenada X")
        ax.set_ylabel("Coordenada Y")
        return ax

    def _plotar_vetores_potencia(self, ax, resultados, titulo, cor_p='red', cor_q='blue'):
        """Função auxiliar para plotar vetores de potência."""
        ax.set_title(titulo, fontsize=16)
        
        bus_geodata = self.net.bus_geodata
        res_bus = resultados['bus']
        
        # Potência líquida em cada barra (Geração - Carga)
        p_net = res_bus['p_mw']
        q_net = res_bus['q_mvar']
        
        # Create arrays of zeros with the same size as p_net and q_net
        zeros_array = np.zeros_like(p_net)
        
        ax.quiver(bus_geodata.x, bus_geodata.y, p_net, zeros_array, color=cor_p, angles='xy', scale_units='xy', scale=None, label='Potência Ativa (P)')
        ax.quiver(bus_geodata.x, bus_geodata.y, zeros_array, q_net, color=cor_q, angles='xy', scale_units='xy', scale=None, label='Potência Reativa (Q)')
        
        ax.plot(bus_geodata.x, bus_geodata.y, 'ko', markersize=5)
        ax.legend()
        ax.grid(True, linestyle='--', alpha=0.5)
        ax.set_xlabel("Coordenada X")
        ax.set_ylabel("Coordenada Y")

    def plotar_grafico_2_fluxo_base(self, ax=None):
        """GRÁFICO 2: Vetores de fluxo de potência (P e Q) no caso base."""
        if ax is None:
            fig, ax = plt.subplots(figsize=(12, 10))
        self._plotar_vetores_potencia(ax, self.resultados_base, "Gráfico 2: Fluxo de Potência - Caso Base")
        return ax

    def plotar_grafico_3_tensoes_base(self, ax=None):
        """GRÁFICO 3: Perfil de tensão em todas as barras no caso base."""
        if ax is None:
            fig, ax = plt.subplots(figsize=(12, 8))
        
        res_bus = self.resultados_base['bus']
        barras = self.net.bus.name
        tensoes = res_bus['vm_pu']
        
        colors = ['green' if 0.95 <= v <= 1.05 else 'red' for v in tensoes]
        
        ax.bar(barras, tensoes, color=colors)
        ax.axhline(y=1.05, color='r', linestyle='--', label='Limite Superior (1.05 pu)')
        ax.axhline(y=0.95, color='r', linestyle='--', label='Limite Inferior (0.95 pu)')
        
        ax.set_title("Gráfico 3: Perfil de Tensão - Caso Base", fontsize=16)
        ax.set_ylabel("Tensão (pu)")
        ax.set_xlabel("Barramentos")
        ax.tick_params(axis='x', rotation=90)
        ax.legend()
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        return ax

    def plotar_grafico_4_fluxo_contingencia(self, ax=None):
        """GRÁFICO 4: Vetores de fluxo de potência (P e Q) durante a contingência."""
        if ax is None:
            fig, ax = plt.subplots(figsize=(12, 10))
        self._plotar_vetores_potencia(ax, self.resultados_contingencia, "Gráfico 4: Fluxo de Potência - Contingência", cor_p='darkorange', cor_q='cyan')
        return ax

    def plotar_grafico_5_tensoes_contingencia(self, ax=None):
        """GRÁFICO 5: Perfil de tensão em todas as barras durante a contingência."""
        if ax is None:
            fig, ax = plt.subplots(figsize=(12, 8))
        
        res_bus = self.resultados_contingencia['bus']
        barras = self.net.bus.name
        tensoes = res_bus['vm_pu']
        
        colors = ['green' if 0.95 <= v <= 1.05 else 'red' for v in tensoes]
        
        ax.bar(barras, tensoes, color=colors)
        ax.axhline(y=1.05, color='r', linestyle='--', label='Limite Superior (1.05 pu)')
        ax.axhline(y=0.95, color='r', linestyle='--', label='Limite Inferior (0.95 pu)')
        
        ax.set_title("Gráfico 5: Perfil de Tensão - Contingência", fontsize=16)
        ax.set_ylabel("Tensão (pu)")
        ax.set_xlabel("Barramentos")
        ax.tick_params(axis='x', rotation=90)
        ax.legend()
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        return ax

    def plotar_grafico_6_comparativo_tensoes(self, ax=None):
        """GRÁFICO 6: Comparativo do perfil de tensão (Base vs. Contingência)."""
        if ax is None:
            fig, ax = plt.subplots(figsize=(14, 8))
            
        barras = self.net.bus.name
        tensoes_base = self.resultados_base['bus']['vm_pu']
        tensoes_cont = self.resultados_contingencia['bus']['vm_pu']
        
        x = np.arange(len(barras))
        width = 0.35
        
        ax.bar(x - width/2, tensoes_base, width, label='Caso Base', color='cornflowerblue')
        ax.bar(x + width/2, tensoes_cont, width, label='Contingência', color='salmon')
        
        ax.set_title("Gráfico 6: Comparativo de Perfil de Tensão", fontsize=16)
        ax.set_ylabel("Tensão (pu)")
        ax.set_xlabel("Barramentos")
        ax.set_xticks(x)
        ax.set_xticklabels(barras, rotation=90)
        ax.legend()
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        return ax

    def plotar_grafico_7_comparativo_carregamento(self, ax=None):
        """GRÁFICO 7: Comparativo do carregamento das linhas (Base vs. Contingência)."""
        if ax is None:
            fig, ax = plt.subplots(figsize=(14, 8))

        linhas = self.net.line.index
        load_base = self.resultados_base['line']['loading_percent']
        load_cont = self.resultados_contingencia['line']['loading_percent']

        x = np.arange(len(linhas))
        width = 0.35

        ax.bar(x - width/2, load_base, width, label='Caso Base', color='seagreen')
        ax.bar(x + width/2, load_cont, width, label='Contingência', color='goldenrod')
        
        ax.axhline(y=100, color='r', linestyle='--', label='Limite de Carregamento (100%)')

        ax.set_title("Gráfico 7: Comparativo de Carregamento das Linhas", fontsize=16)
        ax.set_ylabel("Carregamento (%)")
        ax.set_xlabel("Índice da Linha")
        ax.set_xticks(x)
        ax.set_xticklabels(linhas)
        ax.legend()
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        return ax

# --- Execução Principal do Script ---
if __name__ == "__main__":
    
    # 1. Inicializar a SmartGrid com a rede "Canarinho"
    rede_inteligente = SmartGrid(network_name="canarinho")
    
    # --- INÍCIO DA HISTÓRIA: CENÁRIO BASE ---
    print("\n--- ANÁLISE DO CENÁRIO BASE ---")
    if rede_inteligente.rodar_fluxo_de_potencia():
        rede_inteligente.salvar_resultados('base')

    # --- MEIO DA HISTÓRIA: CENÁRIO DE CONTINGÊNCIA ---
    print("\n--- ANÁLISE DO CENÁRIO DE CONTINGÊNCIA ---")
    rede_inteligente.aplicar_contingencia(id_linha=4) # Desligando a linha de índice 4
    if rede_inteligente.rodar_fluxo_de_potencia():
        rede_inteligente.salvar_resultados('contingencia')

    # --- FIM DA HISTÓRIA: GERAÇÃO DOS 7 GRÁFICOS ---
    print("\n--- GERANDO GRÁFICOS PARA O ARTIGO ---")
    
    # Plotando cada gráfico separadamente
    fig1 = plt.figure(figsize=(12, 10))
    ax1 = fig1.add_subplot(111)
    rede_inteligente.plotar_grafico_1_topologia_rede(ax=ax1)
    plt.tight_layout()
    plt.savefig("grafico_1_topologia_rede.png")
    plt.close(fig1)

    fig2 = plt.figure(figsize=(12, 10))
    ax2 = fig2.add_subplot(111)
    rede_inteligente.plotar_grafico_2_fluxo_base(ax=ax2)
    plt.tight_layout()
    plt.savefig("grafico_2_fluxo_base.png")
    plt.close(fig2)

    fig3 = plt.figure(figsize=(12, 8))
    ax3 = fig3.add_subplot(111)
    rede_inteligente.plotar_grafico_3_tensoes_base(ax=ax3)
    plt.tight_layout()
    plt.savefig("grafico_3_tensoes_base.png")
    plt.close(fig3)

    fig4 = plt.figure(figsize=(12, 10))
    ax4 = fig4.add_subplot(111)
    rede_inteligente.plotar_grafico_4_fluxo_contingencia(ax=ax4)
    plt.tight_layout()
    plt.savefig("grafico_4_fluxo_contingencia.png")
    plt.close(fig4)

    fig5 = plt.figure(figsize=(12, 8))
    ax5 = fig5.add_subplot(111)
    rede_inteligente.plotar_grafico_5_tensoes_contingencia(ax=ax5)
    plt.tight_layout()
    plt.savefig("grafico_5_tensoes_contingencia.png")
    plt.close(fig5)

    fig6 = plt.figure(figsize=(14, 8))
    ax6 = fig6.add_subplot(111)
    rede_inteligente.plotar_grafico_6_comparativo_tensoes(ax=ax6)
    plt.tight_layout()
    plt.savefig("grafico_6_comparativo_tensoes.png")
    plt.close(fig6)

    fig7 = plt.figure(figsize=(14, 8))
    ax7 = fig7.add_subplot(111)
    rede_inteligente.plotar_grafico_7_comparativo_carregamento(ax=ax7)
    plt.tight_layout()
    plt.savefig("grafico_7_comparativo_carregamento.png")
    plt.close(fig7)

    # Resetar a rede para o estado original para futuras simulações
    rede_inteligente.resetar_rede()
